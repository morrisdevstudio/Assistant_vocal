import json

import pytest
from fastapi.testclient import TestClient

from alfred.app import create_app
from alfred.config import Settings
from alfred.intent_context import CURRENT_TURN


class Speech:
    def status(self):
        return {"stt_available": True, "tts_available": True}

    def speak(self, text):
        return b"audio", 1


class Model:
    def __init__(self):
        self.received = []

    def status(self):
        return {"configured": True, "access_verified": True}

    def stream(self, text, session, cancelled):
        self.received.append((text, CURRENT_TURN.get().floor))
        yield {"type": "answer", "text": "Interprétation par le modèle.", "llm_ms": 1}


@pytest.mark.parametrize("text", [
    "mets un minuteur de deux minutes", "quel temps reste-t-il sur le minuteur",
    "annule le minuteur", "allume la lumière du bureau et mets de la musique", "mets de la musique",
    "ajoute du lait aux courses",
])
def test_configured_model_receives_even_simple_commands(tmp_path, monkeypatch, text):
    model = Model()
    app = create_app(Settings(tmp_path), voice_service=Speech(), conversation_service=model)

    def forbidden(*args, **kwargs):
        raise AssertionError("Le raccourci local ne doit pas interpréter la demande")

    monkeypatch.setattr(app.state.intents, "handle_local", forbidden)
    monkeypatch.setattr(app.state.intents.timers, "handle", forbidden)
    with TestClient(app) as client:
        response = client.post("/api/conversation/text", json={
            "text": text, "session_id": "model-routing-session", "floor_id": "rdc"})
        rows = [json.loads(line) for line in response.text.splitlines()]
        assert rows[-1]["type"] == "done", rows
        assert model.received == [(text, "rdc")]
        assert client.get("/api/schedules").json()["items"] == []


def test_bell_stop_bypasses_model(tmp_path):
    model = Model()
    app = create_app(Settings(tmp_path), voice_service=Speech(), conversation_service=model)
    with TestClient(app) as client:
        response = client.post("/api/conversation/text", json={
            "text": "arrête la sonnerie", "session_id": "model-emergency-session", "floor_id": "rdc"})
        rows = [json.loads(line) for line in response.text.splitlines()]
        assert rows[-1]["type"] == "done", rows
        assert rows[-1]["mode"] == "timer"
        assert rows[-1]["timings"]["llm_ms"] == 0
        assert model.received == []


def test_final_tool_answer_without_deltas_is_synthesized(tmp_path):
    import io
    import wave

    class EarlySpeech(Speech):
        supports_early_speech = True
        spoken = []

        def speak(self, text):
            self.spoken.append(text)
            output = io.BytesIO()
            with wave.open(output, "wb") as wav:
                wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(16000)
                wav.writeframes(bytes(3200))
            return output.getvalue(), 1

    speech = EarlySpeech()
    app = create_app(Settings(tmp_path), voice_service=speech, conversation_service=Model())
    with TestClient(app) as client:
        response = client.post("/api/conversation/text", json={
            "text": "temps restant", "session_id": "final-tool-answer-session", "floor_id": "rdc"})
        rows = [json.loads(line) for line in response.text.splitlines()]
        assert rows[-1]["type"] == "done", rows
        assert rows[-1]["progressive_audio"] is True
        assert speech.spoken == ["Interprétation par le modèle."]
