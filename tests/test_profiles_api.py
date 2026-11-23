import io
import math
import struct
import wave

import pytest
from fastapi.testclient import TestClient

from alfred.app import create_app
from alfred.config import Settings
from alfred.profiles import Profiles
from alfred.speaker import SpeakerUnavailable
from alfred.storage import Store
from alfred.voice import validate_wav


def wav_bytes(seconds=2.0, rate=16000, frequency=220.0):
    frames = int(seconds * rate)
    payload = b"".join(struct.pack("<h", int(12000 * math.sin(2 * math.pi * frequency * i / rate)))
                       for i in range(frames))
    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        audio.writeframes(payload)
    return output.getvalue()


class FakeSpeaker:
    def __init__(self, available=True):
        self.available = available

    def status(self):
        return {"available": self.available, "model": "faux", "busy": False}

    def embed_wav(self, data):
        if not self.available:
            raise SpeakerUnavailable("Le modèle d'empreinte vocale n'est pas préparé.")
        validate_wav(data)
        return [1.0, 2.0, 3.0]


def build(tmp_path, speaker=None):
    settings = Settings(tmp_path, poll_seconds=0.02)
    return TestClient(create_app(settings, speaker_service=speaker or FakeSpeaker()))


def test_profile_lifecycle_with_audio(tmp_path):
    with build(tmp_path) as client:
        created = client.post("/api/profiles", json={"name": "Camille", "role": "adult"})
        assert created.status_code == 201
        identifier = created.json()["id"]
        assert created.json()["samples"] == 0

        enrolled = client.post(f"/api/profiles/{identifier}/enroll", content=wav_bytes(),
                               headers={"Content-Type": "audio/wav"})
        assert enrolled.status_code == 201
        assert enrolled.json()["samples"] == 1
        assert enrolled.json()["duration_seconds"] == pytest.approx(2.0, abs=0.05)

        items = client.get("/api/profiles").json()["items"]
        assert [item["samples"] for item in items] == [1]
        assert client.get("/api/profiles").json()["speaker"]["available"] is True

        samples = client.get(f"/api/profiles/{identifier}/samples").json()["items"]
        assert len(samples) == 1
        audio = client.get(f"/api/profiles/{identifier}/samples/{samples[0]['audio_file']}")
        assert audio.status_code == 200
        assert audio.headers["content-type"] == "audio/wav"
        assert audio.content == wav_bytes()

        stored = tmp_path / "profiles" / identifier / samples[0]["audio_file"]
        assert stored.is_file()

        scores = client.post("/api/profiles/identify", content=wav_bytes(),
                             headers={"Content-Type": "audio/wav"}).json()["scores"]
        assert scores[0]["name"] == "Camille"
        assert scores[0]["score"] == pytest.approx(1.0, abs=1e-4)

        reset = client.post(f"/api/profiles/{identifier}/reset", json={})
        assert reset.json()["cleared"] == 1
        assert client.get("/api/profiles").json()["items"][0]["samples"] == 0
        assert not stored.exists()

        assert client.delete(f"/api/profiles/{identifier}").json() == {"deleted": True}
        assert client.get("/api/profiles").json()["items"] == []
        assert not stored.parent.exists()


def test_profiles_are_checked_and_absent_speaker_is_explicit(tmp_path):
    with build(tmp_path) as client:
        assert client.post("/api/profiles", json={"name": "   "}).status_code == 422
        assert client.post("/api/profiles", json={"name": "Zoé", "role": "guest"}).status_code == 422
        assert client.get("/api/profiles/inconnu/samples").status_code == 404
        assert client.delete("/api/profiles/inconnu").status_code == 404
        assert client.patch("/api/profiles/inconnu", json={"name": "X"}).status_code == 404
        identifier = client.post("/api/profiles", json={"name": "Zoé"}).json()["id"]
        assert client.post("/api/profiles", json={"name": "Zoé"}).status_code == 422
        assert client.post(f"/api/profiles/{identifier}/enroll", content=b"pas un wav",
                           headers={"Content-Type": "application/wav"}).status_code == 415
        assert client.post(f"/api/profiles/{identifier}/enroll", content=b"pas un wav",
                           headers={"Content-Type": "audio/wav"}).status_code == 422
        assert client.post("/api/profiles/inconnu/enroll", content=wav_bytes(),
                           headers={"Content-Type": "audio/wav"}).status_code == 404

    with build(tmp_path, FakeSpeaker(available=False)) as client:
        identifier = client.post("/api/profiles", json={"name": "Léa"}).json()["id"]
        response = client.post(f"/api/profiles/{identifier}/enroll", content=wav_bytes(),
                               headers={"Content-Type": "audio/wav"})
        assert response.status_code == 503
        assert "préparé" in response.json()["detail"]
        assert client.get("/api/profiles").json()["items"][0]["samples"] == 0


def test_cross_origin_write_is_refused(tmp_path):
    with build(tmp_path) as client:
        response = client.post("/api/profiles", json={"name": "Camille"},
                               headers={"Origin": "https://other.example"})
        assert response.status_code == 403


def test_audio_files_live_outside_the_database_folder_name(tmp_path):
    store = Store(tmp_path)
    store.initialize()
    profiles = Profiles(store)
    profile = profiles.create("Hugo")
    name = profiles.save_audio(profile["id"], b"RIFF")
    assert (tmp_path / "profiles" / profile["id"] / name).read_bytes() == b"RIFF"
    assert profiles.audio_path(profile["id"], name) is not None
    assert profiles.audio_path(profile["id"], "../evil.wav") is None
    profiles.clear_voiceprints(profile["id"])
    assert profiles.audio_path(profile["id"], name) is not None

