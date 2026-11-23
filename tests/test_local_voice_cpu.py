import base64
import io
import json
import sys
import wave

import pytest

from alfred.local_voice_cpu import ASSETS, LocalVoiceCPU
from alfred.chatterbox_cpu import ChatterboxCPUError
from alfred.voice import VoiceService, VoiceUnavailable


def wav():
    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(24000)
        audio.writeframes(bytes(2400))
    return output.getvalue()


def prepare(tmp_path, engine):
    models = tmp_path / "models"
    for name in ASSETS[engine]:
        path = models / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fake model")
    site = tmp_path / "site"
    site.mkdir()
    package = site / ({"phonon":"ptts/__init__.py", "sopro":"sopro/model.py", "melo-openvoice":"alfred-local-sources.pth"}[engine])
    package.parent.mkdir(exist_ok=True)
    package.write_text("")
    reference = tmp_path / "reference.wav"
    reference.write_bytes(wav())
    config = tmp_path / "voice.json"
    config.write_text(json.dumps({"engine": engine, "python": sys.executable,
        "site_packages": str(site), "model_dir": str(models), ("voice_file" if engine == "phonon" else "reference"): str(reference)}))
    return config


@pytest.mark.parametrize("engine", ["phonon"])
def test_local_models_need_explicit_configuration_assets_and_runtime(tmp_path, engine):
    config = prepare(tmp_path, engine)
    voice = LocalVoiceCPU(config, engine)
    assert voice.available()
    (tmp_path / "models" / ASSETS[engine][0]).unlink()
    assert not voice.available()
    with pytest.raises(ChatterboxCPUError):
        voice.start()


@pytest.mark.parametrize("engine", ["phonon"])
def test_local_worker_is_persistent_cpu_offline_and_closed(tmp_path, monkeypatch, engine):
    import subprocess
    original = subprocess.Popen
    fake = tmp_path / "fake.py"
    fake.write_text("import sys,json\nprint(json.dumps({'ready':True}),flush=True)\n"
                    "for line in sys.stdin:\n print(json.dumps({'audio':"
                    + repr(base64.b64encode(wav()).decode()) + "}),flush=True)\n")
    calls = []
    def launch(command, **kwargs):
        calls.append((command, kwargs))
        return original([sys.executable, "-u", str(fake)], **kwargs)
    monkeypatch.setattr(subprocess, "Popen", launch)
    voice = LocalVoiceCPU(prepare(tmp_path, engine), engine)
    try:
        assert voice.synthesize("Bonjour") == wav()
        process = voice.process
        assert voice.synthesize("Deuxième phrase") == wav()
        assert voice.process is process and len(calls) == 1
        assert "alfred.local_voice_worker" in calls[0][0]
        assert calls[0][1]["env"]["CUDA_VISIBLE_DEVICES"] == ""
        assert calls[0][1]["env"]["HF_HUB_OFFLINE"] == "1"
    finally:
        voice.close()
    assert process.poll() is not None and not voice.ready


@pytest.mark.parametrize("voice_id,engine", [("phonon-arnaud-cpu", "phonon"), ("phonon-lucien-cpu", "phonon"), ("phonon-alfred-cpu", "phonon"), ("phonon-dumby-cpu", "phonon")])
def test_voice_selection_synthesis_stream_and_error_keep_selected_engine(tmp_path, monkeypatch, voice_id, engine):
    from alfred.app import VoiceConfigInput
    assert VoiceConfigInput(voice=voice_id).voice == voice_id
    voice = VoiceService(tmp_path / "models", voice_file=tmp_path / "data/voice.json")
    runtime = voice._local_voices[voice_id]
    monkeypatch.setattr(runtime, "available", lambda: True)
    monkeypatch.setattr(runtime, "start", lambda: None)
    received = []
    monkeypatch.setattr(runtime, "synthesize", lambda text: received.append(text) or wav())
    voice.set_voice(voice_id)
    assert VoiceService(tmp_path / "models", voice_file=voice.voice_file).status()["tts_voice_id"] == voice_id
    voice.speak("Il est 20h43. Il n'y a plus de pâtes.")
    assert received == ["Il est vingt heures quarante-trois. Il n'y a plus de pâtes."]
    assert voice.metadata()["voice_engine"] == engine
    assert list(voice.speak_blocks(["Une phrase.", "Autre phrase."]))
    def fail(text):
        raise ChatterboxCPUError("échec local")
    monkeypatch.setattr(runtime, "synthesize", fail)
    with pytest.raises(VoiceUnavailable):
        voice.speak("Bonjour")
    assert voice.status()["tts_voice_id"] == voice_id and not voice.last_fallback


@pytest.mark.parametrize("engine", ["sopro", "melo-openvoice", "chatterbox"])
def test_non_phonon_workers_are_not_available(tmp_path,engine):
    with pytest.raises(ValueError,match="Phonon"):
        LocalVoiceCPU(tmp_path / "voice.json",engine)
