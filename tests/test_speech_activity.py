import io
import os
from types import SimpleNamespace
import wave

import numpy as np
import pytest

from alfred.speech_activity import SpeechActivity
from alfred.terminal import Capture


def test_detector_preserves_context_state_and_packet_fragments(monkeypatch):
    calls = []
    probabilities = iter([.9, .4, .1, .9])
    class Session:
        def run(self, outputs, inputs):
            calls.append({k: v.copy() for k, v in inputs.items()})
            return np.array([next(probabilities)]), inputs["h"]+1, inputs["c"]+2
    monkeypatch.setattr("alfred.speech_activity.vad_session", lambda path: Session())
    detector = SpeechActivity()
    half = np.full(256, 1000, dtype="<i2").tobytes()
    assert detector.feed(half) is False
    assert not calls
    assert detector.feed(half) is True
    assert detector.feed(half*2) is True  # Hystérésis, probabilité 0,4.
    assert detector.feed(half*2) is False
    assert all(item["input"].shape == (1,576) for item in calls)
    assert np.all(calls[0]["input"][:,:64] == 0)
    assert np.all(calls[1]["h"] == 1)
    assert np.allclose(calls[1]["input"][:,:64], 1000/32768)
    other = SpeechActivity()
    assert other.feed(half*2)
    assert np.all(calls[-1]["h"] == 0)  # Pas de contexte partagé entre prises.


def test_loud_background_cannot_prevent_end_when_classifier_says_no_speech():
    class Activity:
        count = 0
        def feed(self, data):
            self.count += 1
            return self.count <= 20
    capture = Capture(Activity())
    background = np.full(320, 2000, dtype="<i2").tobytes()
    for _ in range(70):
        _, done = capture.feed(background)
        if done:
            break
    assert done and capture.end_reason == "speech_pause"
    assert capture.silence >= .9
    # Aucun filtrage ni modification des échantillons envoyés au STT.
    with wave.open(io.BytesIO(capture.wav()), "rb") as wav:
        assert np.all(np.frombuffer(wav.readframes(wav.getnframes()),dtype="<i2") == 2000)


def test_real_vad_rejects_loud_instrumental_proxy():
    pytest.importorskip("onnxruntime")
    from alfred.config import Settings
    if not (Settings.from_env().models_dir / "silero-v6/silero_vad_v6.onnx").is_file():
        pytest.skip("Préparer le modèle local avec python -m alfred.setup_vad")
    t = np.arange(16000*3) / 16000
    music = .03*np.sin(2*np.pi*220*t)+.03*np.sin(2*np.pi*330*t)+.03*np.sin(2*np.pi*440*t)
    pcm = (music*32767).astype("<i2").tobytes()
    capture = Capture(SpeechActivity())
    for i in range(0,len(pcm),640):capture.feed(pcm[i:i+640])
    assert not capture.speaking


@pytest.mark.skipif(os.environ.get("ALFRED_TEST_SPEECH_VAD") != "1",
                    reason="Banc VAD réel avec la synthèse locale : ALFRED_TEST_SPEECH_VAD=1")
def test_real_vad_finishes_with_music_still_present_and_keeps_whole_phrase():
    from alfred.config import Settings
    from alfred.voice import VoiceService, pcm_16khz
    from alfred.runtime import prefer_interactive_cpu
    prefer_interactive_cpu()
    settings = Settings.from_env()
    voice = VoiceService(settings.models_dir, voice_file=settings.data_dir / "voice.json")
    audio, _ = voice.speak("Alfred, allume la lumière du bureau.")
    speech = pcm_16khz(audio)
    t = np.arange(len(speech)+16000*4) / 16000
    track = .025*np.sin(2*np.pi*220*t)+.025*np.sin(2*np.pi*330*t)+.025*np.sin(2*np.pi*440*t)
    track[16000:16000+len(speech)] += speech
    pcm = (np.clip(track,-1,1)*32767).astype("<i2").tobytes()
    capture = Capture(SpeechActivity())
    for i in range(0,len(pcm)-640,640):
        _, done = capture.feed(pcm[i:i+640])
        if done:
            break
    assert done and capture.end_reason == "speech_pause"
    captured_end = capture.received/32000
    assert captured_end < 1 + len(speech)/16000 + 1.5
    assert captured_end < len(pcm)/32000 - 1  # Le fond continue après l'envoi.
    first_spoken = 1 + int(np.flatnonzero(np.abs(speech)>.005)[0])/16000
    buffer_start = (capture.received-len(capture.data))/32000
    assert buffer_start <= first_spoken
