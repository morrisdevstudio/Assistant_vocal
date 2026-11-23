import io
import json
import wave
import pytest

from fastapi.testclient import TestClient

from alfred.app import create_app
from alfred.config import Settings


class FakeSpeech:
    def status(self):
        return {"stt_available": True, "tts_available": True}

    def speak(self, text):
        return b"test-audio", 5

    def transcribe(self, audio):
        return "mets un minuteur de huit minutes", 1.0, 10


class NoAI:
    def status(self):
        return {"configured": False, "access_verified": False}

    def stream(self, *args):
        raise AssertionError("Une commande de minuteur ne doit jamais appeler l'IA")


class NoHome:
    def handle(self, text):
        raise AssertionError("Une commande de minuteur ne doit pas solliciter HA")


def events(response):
    assert response.status_code == 200
    result = [json.loads(line) for line in response.text.splitlines()]
    assert result[-1]["type"] == "done", result
    assert result[-1]["mode"] == "timer"
    assert result[-1]["timings"]["llm_ms"] == 0
    return result[-1]


def test_text_create_list_cancel_and_missing_floor_without_any_ai_or_ha(tmp_path):
    app = create_app(Settings(tmp_path), voice_service=FakeSpeech(),
                     conversation_service=NoAI(), home_service=NoHome())
    with TestClient(app) as client:
        def send(text, floor="rdc"):
            return events(client.post("/api/conversation/text", json={
                "text": text, "session_id": "timer-test-session-001", "floor_id": floor}))
        assert "Choisissez" in send("mets un minuteur de huit minutes", None)["text"]
        assert client.get("/api/schedules").json()["items"] == []
        assert "lancé" in send("mets un minuteur de huit minutes")["text"]
        records = client.get("/api/schedules").json()["items"]
        assert len(records) == 1 and records[0]["floor_id"] == "rdc"
        remaining = send("quel temps reste-t-il sur le minuteur ?")
        assert "Il reste huit minutes" in remaining["text"]
        assert "Précisez une durée" not in remaining["text"]
        assert "huit minutes" in send("liste les minuteurs")["text"]
        assert "Aucun" in send("liste les minuteurs", "etage1")["text"]
        assert "annulé" in send("annule le minuteur")["text"]
        assert client.get("/api/schedules").json()["items"][0]["status"] == "cancelled"


def test_named_web_timer_can_be_read_and_cancelled_in_conversation(tmp_path):
    app = create_app(Settings(tmp_path), voice_service=FakeSpeech(),
                     conversation_service=NoAI(), home_service=NoHome())
    with TestClient(app) as client:
        def send(text):
            return events(client.post("/api/conversation/text", json={
                "text": text, "session_id": "named-timer-test-session", "floor_id": "rdc"}))["text"]

        timer = client.post("/api/timers", json={
            "title": "Œuf à la coque", "duration_seconds": 180, "floor_id": "rdc"}).json()
        send("mets un minuteur de huit minutes")
        assert send("il reste combien sur le minuteur oeuf à la coque ?") == "Pour « Œuf à la coque », il reste trois minutes."
        assert "Aucun minuteur actif" in send("annule le minuteur thé")
        assert "Il reste huit minutes" in send("il reste combien sur le minuteur ?")
        assert send("annule le minuteur oeuf à la coque") == "Minuteur « Œuf à la coque » annulé."
        remaining = client.get("/api/timers?floor_id=rdc").json()["items"]
        assert len(remaining) == 1 and remaining[0]["id"] != timer["id"]


@pytest.mark.parametrize("question", [
    "Il reste combien de temps sur le minuteur ?",
    "Combien de temps il reste sur le minuteur ?",
    "Quel temps reste-t-il sur le minuteur ?",
    "Il reste combien sur mon minuteur ?",
])
def test_spoken_timer_variants_preserve_current_context(tmp_path, question):
    class Speech(FakeSpeech):
        transcript = ""

        def transcribe(self, audio):
            return self.transcript, 1.0, 10

    speech = Speech()
    app = create_app(Settings(tmp_path), voice_service=speech,
                     conversation_service=NoAI(), home_service=NoHome())
    audio = io.BytesIO()
    with wave.open(audio, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(bytes(32000))
    with TestClient(app) as client:
        def say(text):
            speech.transcript = text
            return events(client.post("/api/conversation/voice", content=audio.getvalue(), headers={
                "Content-Type": "audio/wav", "X-Alfred-Session": "timer-variants-session",
                "X-Alfred-Floor": "rdc"}))["text"]

        assert "lancé" in say("Mets un minuteur de huit minutes.")
        assert "lancé" in say("On met un minuteur de deux minutes.")
        reply = say(question)
        assert "Il reste deux minutes" in reply
        listing = say("liste les minuteurs")
        assert "huit minutes" in listing and "deux minutes" in listing
        assert "annulé" in say("annule le minuteur")
        records = client.get("/api/schedules").json()["items"]
        assert sorted(x["status"] for x in records) == ["cancelled", "pending"]


def test_voice_uses_transcript_and_floor_header_without_llm(tmp_path):
    app = create_app(Settings(tmp_path), voice_service=FakeSpeech(),
                     conversation_service=NoAI(), home_service=NoHome())
    audio = io.BytesIO()
    with wave.open(audio, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(bytes(32000))
    with TestClient(app) as client:
        result = client.post("/api/conversation/voice", content=audio.getvalue(), headers={
            "Content-Type": "audio/wav", "X-Alfred-Session": "timer-test-session-002",
            "X-Alfred-Floor": "etage1"})
        assert events(result)["timings"]["stt_ms"] == 10
        assert client.get("/api/schedules").json()["items"][0]["floor_id"] == "etage1"
        invalid = client.post("/api/conversation/voice", content=audio.getvalue(), headers={
            "Content-Type": "audio/wav", "X-Alfred-Session": "timer-test-session-002",
            "X-Alfred-Floor": "inconnu"})
        assert invalid.status_code == 422


def test_tts_failure_reports_recorded_action_without_retry(tmp_path):
    class BrokenSpeech(FakeSpeech):
        def speak(self, text):
            raise RuntimeError("détail interne à ne pas exposer")
    app = create_app(Settings(tmp_path), voice_service=BrokenSpeech(),
                     conversation_service=NoAI(), home_service=NoHome())
    with TestClient(app) as client:
        result = client.post("/api/conversation/text", json={"text": "mets un minuteur de huit minutes",
                            "session_id": "timer-test-session-003", "floor_id": "rdc"})
        stream = [json.loads(line) for line in result.text.splitlines()]
        assert stream[-1]["type"] == "error"
        assert "lancé" in stream[-1]["message"]
        assert "interne" not in result.text
        assert len(client.get("/api/schedules").json()["items"]) == 1


def test_web_text_reply_can_skip_synthesis(tmp_path):
    class TextOnly(FakeSpeech):
        def speak(self, text):
            raise AssertionError("La PWA a demandé une réponse écrite")
    with TestClient(create_app(Settings(tmp_path), voice_service=TextOnly(),
                               conversation_service=NoAI(), home_service=NoHome())) as client:
        result = client.post("/api/conversation/text", json={
            "text": "liste les minuteurs", "floor_id": "rdc",
            "session_id": "pwa-text-only-001", "speak": False, "allow_internet": False,
        })
        assert "Aucun" in events(result)["text"]
        assert events(result)["audio_base64"] == ""
