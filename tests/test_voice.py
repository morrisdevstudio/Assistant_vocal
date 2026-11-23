import io
import json
import wave
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from alfred.app import create_app, VoiceConfigInput
from alfred.config import Settings
from alfred.voice import (MAX_AUDIO_BYTES, DEFAULT_VOICE, VOICES, InvalidAudio,
    VoiceBusy, VoiceService, VoiceUnavailable, pcm_16khz, validate_wav)

def wav_bytes(rate=16000, seconds=0.25, channels=1, width=2):
    output=io.BytesIO()
    with wave.open(output,"wb") as wav:
        wav.setnchannels(channels);wav.setsampwidth(width);wav.setframerate(rate)
        wav.writeframes(bytes(int(rate*seconds)*channels*width))
    return output.getvalue()



def test_wav_limits_before_inference():
    assert validate_wav(wav_bytes()) == 0.25
    for data in (b"", b"invalid", wav_bytes(channels=2), wav_bytes(width=1),
                 wav_bytes(seconds=31), wav_bytes(rate=1000), wav_bytes()[:-100],
                 b"x"*(MAX_AUDIO_BYTES+1)):
        with pytest.raises(InvalidAudio):
            validate_wav(data)



@pytest.mark.parametrize("rate", [16000,22050,48000,96000])
def test_resampling_is_mono_float32_and_retains_duration(rate):
    pytest.importorskip("av")
    pytest.importorskip("numpy")
    samples=pcm_16khz(wav_bytes(rate=rate,seconds=0.5))
    assert samples.dtype.name == "float32"
    assert samples.ndim == 1
    assert abs(len(samples)-8000) <= 2
    assert not samples.any()



def test_missing_models_never_download_or_load(tmp_path, monkeypatch):
    engine=VoiceService(tmp_path)
    monkeypatch.setattr(engine,"_synthesize",lambda _:pytest.fail("Ne doit pas charger"))
    assert not engine.status()["tts_available"]
    with pytest.raises(VoiceUnavailable):
        engine.speak("Bonjour")
    assert list(tmp_path.iterdir()) == []









def test_voice_lock_is_released_after_error(tmp_path,monkeypatch):
    engine=VoiceService(tmp_path)
    monkeypatch.setattr(engine,"_check",lambda **_:None)
    def fail(_):
        raise RuntimeError("test")
    monkeypatch.setattr(engine,"_synthesize",fail)
    with pytest.raises(RuntimeError):engine.speak("Bonjour")
    assert not engine.status()["busy"]
    engine._lock.acquire()
    try:
        with pytest.raises(VoiceBusy):engine.speak("Bonjour")
    finally:engine._lock.release()



def test_blocked_speech_keeps_voice_exclusive_until_closed(tmp_path, monkeypatch):
    engine = VoiceService(tmp_path)
    monkeypatch.setattr(engine, "_check", lambda **kwargs: None)
    calls = []
    def synthesize(text):
        calls.append(text)
        return b"audio"
    monkeypatch.setattr(engine, "_synthesize", synthesize)
    blocks = engine.speak_blocks(["Première phrase.", "Deuxième phrase."])
    assert next(blocks)[0] == b"audio"
    with pytest.raises(VoiceBusy):
        engine.speak("Autre voix concurrente")
    blocks.close()
    assert calls == ["Première phrase."]
    assert engine.speak("Nouvelle demande")[0] == b"audio"



def test_silence_returns_no_synthetic_transcript_or_audio(tmp_path,monkeypatch):
    engine=VoiceService(tmp_path)
    monkeypatch.setattr(engine,"_check",lambda **_:None)
    monkeypatch.setattr(engine,"_recognize",lambda _:"")
    monkeypatch.setattr(engine,"_synthesize",lambda _:pytest.fail("Silence ne doit pas produire une réponse inventée"))
    result=engine.turn(wav_bytes())
    assert result["text"] == ""
    assert result["audio_base64"] is None
    assert not engine.status()["busy"]



class FakeVoice:
    """Double explicite pour tester l'API, pas une preuve de qualité vocale."""
    def __init__(self):self.voice="phonon-dumby-cpu";self.last_fallback=False
    def status(self):return {"stt_available":True,"tts_available":True,"tts_voice_id":self.voice}
    def set_voice(self,voice):self.voice=voice
    def metadata(self):return {"voice_id":self.voice,"voice_engine":"phonon","voice_fallback":False}
    def speak(self,text):return wav_bytes(),12
    def turn(self,data):
        duration=validate_wav(data)
        return {"text":"Texte de test","input_seconds":duration,"audio_base64":None}



@pytest.fixture
def voice_client(tmp_path):
    with TestClient(create_app(Settings(tmp_path),voice_service=FakeVoice())) as client:
        yield client



def test_voice_routes_and_no_audio_file_created(voice_client,tmp_path):
    assert voice_client.get("/api/status").json()["capabilities"]["stt"]
    response=voice_client.post("/api/voice/speak",json={"text":"Bonjour"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.headers["x-tts-ms"] == "12"
    assert validate_wav(response.content) == 0.25
    result=voice_client.post("/api/voice/turn",content=wav_bytes(),headers={"Content-Type":"audio/wav"})
    assert result.status_code == 200
    assert result.json()["text"] == "Texte de test"
    assert not list(tmp_path.rglob("*.wav"))
    assert voice_client.get("/api/schedules").json()["items"] == []



def test_voice_validation_and_origin(voice_client):
    assert voice_client.post("/api/voice/speak",json={"text":"  "}).status_code == 422
    assert voice_client.post("/api/voice/speak",json={"text":"x"*501}).status_code == 422
    assert voice_client.post("/api/voice/turn",json={}).status_code == 415
    assert voice_client.post("/api/voice/turn",content=b"bad",headers={"Content-Type":"audio/wav"}).status_code == 422
    assert voice_client.post("/api/voice/turn",content=wav_bytes(),headers={"Content-Type":"audio/wav","Origin":"https://other.example"}).status_code == 403
    assert voice_client.post("/api/voice/turn",content=b"x"*(MAX_AUDIO_BYTES+1),headers={"Content-Type":"audio/wav"}).status_code == 413



@pytest.mark.parametrize("voice", list(VOICES))
def test_voice_config_route_changes_active_voice(voice_client, voice):
    response=voice_client.post("/api/voice/config",json={"voice":voice})
    assert response.status_code == 200
    assert response.json()["tts_voice_id"] == voice
    assert voice_client.get("/api/voice/status").json()["tts_voice_id"] == voice



@pytest.mark.parametrize("error,code",[(VoiceBusy("Occupé"),409),(VoiceUnavailable("Absent"),503),(RuntimeError("secret"),503)])
def test_engine_failures_are_honest_and_sanitized(tmp_path,error,code):
    class Failing(FakeVoice):
        def speak(self,text):raise error
    with TestClient(create_app(Settings(tmp_path),voice_service=Failing())) as client:
        result=client.post("/api/voice/speak",json={"text":"Bonjour"})
        assert result.status_code == code
        assert "secret" not in result.text



REMOVED_VOICES = ["pocket-alfred", "alfred-reference", "supertonic-m1", "supertonic-m2",
    "supertonic-m3", "supertonic-m4", "supertonic-m5", "chatterbox-cpu",
    "ha-cloud-henri", "sopro-cpu", "melo-openvoice-cpu"]


def test_only_phonon_is_available_in_registry(tmp_path):
    engine = VoiceService(tmp_path)
    assert engine.status()["tts_voice_id"] == "phonon-dumby-cpu"
    assert set(VOICES) == {"phonon-dumby-cpu", "phonon-alfred-cpu", "phonon-arnaud-cpu", "phonon-lucien-cpu"}
    assert all(v["engine"] == "phonon" for v in engine.status()["voices"])
    assert not any(key in engine.status() for key in ("pocket_clone_ready", "chatterbox_cpu_ready"))


@pytest.mark.parametrize("voice", REMOVED_VOICES)
def test_removed_voices_rejected_by_api_and_service(tmp_path, voice_client, voice):
    assert voice_client.post("/api/voice/config", json={"voice": voice}).status_code == 422
    with pytest.raises(ValidationError):
        VoiceConfigInput(voice=voice)
    engine = VoiceService(tmp_path)
    with pytest.raises(ValueError):
        engine.set_voice(voice)
    with pytest.raises(ValueError):
        VoiceService(tmp_path, initial_voice=voice)


@pytest.mark.parametrize("voice", REMOVED_VOICES)
def test_saved_legacy_preference_migrates_to_dumby(tmp_path, voice):
    preference=tmp_path / "voice.json"
    preference.write_text(json.dumps({"voice":voice,"version":2}))
    engine=VoiceService(tmp_path / "models",voice_file=preference)
    assert engine.status()["tts_voice_id"]==DEFAULT_VOICE
    assert engine.status()["tts_engine"]=="phonon"


def test_phonon_choice_persists_without_any_fallback(tmp_path, monkeypatch):
    from alfred.chatterbox_cpu import ChatterboxCPUError
    from alfred.local_voice_cpu import LocalVoiceCPU
    monkeypatch.setattr(LocalVoiceCPU,"available",lambda _:True)
    monkeypatch.setattr(LocalVoiceCPU,"start",lambda _:None)
    preference=tmp_path / "data/voice.json"
    engine=VoiceService(tmp_path / "models",voice_file=preference)
    engine.set_voice("phonon-lucien-cpu")
    assert VoiceService(tmp_path / "models",voice_file=preference).status()["tts_voice_id"]=="phonon-lucien-cpu"
    def fail(text):
        raise ChatterboxCPUError("Échec simulé")
    monkeypatch.setattr(engine._local_voices["phonon-lucien-cpu"],"synthesize",fail)
    with pytest.raises(VoiceUnavailable):engine.speak("Bonjour")
    assert engine.status()["tts_voice_id"]=="phonon-lucien-cpu"
    assert not engine.last_fallback
