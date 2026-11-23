"""Essai réel optionnel avec les modèles locaux, sans microphone ni fichier audio."""

import os

import pytest
from fastapi.testclient import TestClient

from alfred.app import create_app
from alfred.config import Settings
from alfred.voice import VoiceService, validate_wav


@pytest.mark.skipif(os.environ.get("ALFRED_TEST_VOICE") != "1", reason="Modèles locaux : activer ALFRED_TEST_VOICE=1")
def test_real_local_tts_to_stt_routes(tmp_path):
    configured = Settings.from_env()
    models = configured.models_dir
    voice = VoiceService(models, voice_file=configured.data_dir / "voice.json")
    with TestClient(create_app(Settings(tmp_path, models_dir=models), voice_service=voice)) as client:
        audio = client.post("/api/voice/speak", json={"text":"Bonsoir, je suis Alfred. Que puis-je faire pour vous ?"})
        assert audio.status_code == 200
        assert validate_wav(audio.content) > 0
        result = client.post("/api/voice/turn", content=audio.content, headers={"Content-Type":"audio/wav"})
        assert result.status_code == 200
        record = result.json()
        assert "alfred" in record["text"].lower()
        assert record["audio_base64"]
        assert record["mode"] == "audio-test"
        assert client.get("/api/schedules").json()["items"] == []
        assert not list(tmp_path.rglob("*.wav"))
