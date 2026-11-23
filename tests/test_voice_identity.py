import io
import math
import struct
import wave
import pytest
from alfred.profiles import Profiles
from alfred.speaker import MODEL_REPOSITORY
from alfred.storage import Store
from alfred.voice_identity import VoiceIdentity
from alfred.app import create_app
from alfred.config import Settings
from fastapi.testclient import TestClient


def wav():
    out=io.BytesIO()
    with wave.open(out,"wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000)
        w.writeframes(b"".join(struct.pack("<h",int(5000*math.sin(2*math.pi*200*i/16000))) for i in range(32000)))
    return out.getvalue()


def setup(tmp_path,number=2):
    store=Store(tmp_path);store.initialize(); profiles=Profiles(store)
    people=[profiles.create("Profil "+str(i)) for i in range(number)]
    for i,person in enumerate(people):
        for _ in range(6): profiles.add_voiceprint(person["id"], [1.0,0.0] if i==0 else [0.0,1.0],MODEL_REPOSITORY,3)
    class Speaker:
        vector=[1.0,0.0]
        def embed_wav(self,data): return self.vector
    speaker=Speaker();return VoiceIdentity(profiles,speaker,tmp_path),profiles,people,speaker


def test_one_voice_is_not_enough_to_calibrate(tmp_path):
    identity,_,_,_=setup(tmp_path,1)
    with pytest.raises(ValueError,match="deux personnes"): identity.calibrate()
    assert identity.status()["state"]=="not_calibrated"


def test_independent_probes_required_and_changes_invalidate(tmp_path):
    identity,profiles,people,speaker=setup(tmp_path)
    identity.calibrate()
    assert identity.classify([1.0,0.0]) is None
    for i,person in enumerate(people):
        speaker.vector=[1.0,0.0] if i==0 else [0.0,1.0]
        identity.probe(person["id"],wav()); identity.probe(person["id"],wav())
    assert identity.status()["state"]=="ready"
    assert identity.classify([1.0,0.0])==people[0]["id"]
    assert identity.classify([0.7,0.7]) is None
    profiles.add_voiceprint(people[0]["id"],[1.0,0.0],MODEL_REPOSITORY,3)
    assert identity.status()["state"]=="not_calibrated" and identity.classify([1.0,0.0]) is None


def test_overlapping_voices_are_refused(tmp_path):
    identity,profiles,people,_=setup(tmp_path)
    profiles.reset(people[1]["id"])
    for _ in range(6): profiles.add_voiceprint(people[1]["id"],[1.0,0.0],MODEL_REPOSITORY,3)
    with pytest.raises(ValueError,match="pas assez séparées"): identity.calibrate()


def test_api_explains_need_for_second_person(tmp_path):
    with TestClient(create_app(Settings(tmp_path))) as client:
        client.post("/api/profiles",json={"name":"Profil fictif","role":"adult"})
        assert client.get("/api/voice-identity/status").json()["state"]=="not_calibrated"
        result=client.post("/api/voice-identity/calibrate",json={})
        assert result.status_code==422 and "deux personnes" in result.json()["detail"]
