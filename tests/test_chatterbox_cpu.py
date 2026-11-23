import base64
import io
import json
from pathlib import Path
import sys
import wave

import pytest

from alfred.chatterbox_cpu import ChatterboxCPU, ChatterboxCPUError, MODEL_FILES
from alfred.voice import VoiceService, VoiceUnavailable


def config(tmp_path):
    site = tmp_path / "site"
    (site / "chatterbox").mkdir(parents=True)
    (site / "chatterbox/mtl_tts.py").write_text("")
    models = tmp_path / "models"
    models.mkdir()
    for name in MODEL_FILES:
        (models / name).write_bytes(b"model")
    reference = tmp_path / "reference.wav"
    reference.write_bytes(b"reference")
    path = tmp_path / "chatterbox.json"
    path.write_text(json.dumps({"python": sys.executable, "site_packages": str(site),
                                "model_dir": str(models), "reference": str(reference)}))
    return path


def wav():
    output = io.BytesIO()
    with wave.open(output, "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(24000)
        stream.writeframes(bytes(2400))
    return output.getvalue()


def test_configuration_requires_all_assets_and_never_downloads(tmp_path):
    client = ChatterboxCPU(tmp_path / "absent.json")
    assert not client.available()
    client = ChatterboxCPU(config(tmp_path))
    assert client.available()
    (tmp_path / "models/s3gen.pt").unlink()
    assert not client.available()
    with pytest.raises(ChatterboxCPUError):
        client.start()


def test_persistent_worker_reused_and_terminated_on_close(tmp_path, monkeypatch):
    import subprocess
    original_popen = subprocess.Popen
    script = tmp_path / "fake_worker.py"
    encoded = base64.b64encode(wav()).decode()
    script.write_text(
        "import sys,json\nprint(json.dumps({'ready':True}),flush=True)\n"
        "for line in sys.stdin:\n json.loads(line)\n print(json.dumps({'audio':"
        + repr(encoded) + "}),flush=True)\n")
    calls = []
    def popen(command, **kwargs):
        calls.append((command, kwargs))
        return original_popen([sys.executable, "-u", str(script)], **kwargs)
    monkeypatch.setattr(subprocess, "Popen", popen)
    client = ChatterboxCPU(config(tmp_path), timeout=5)
    try:
        assert client.synthesize("Bonjour") == wav()
        process = client.process
        assert client.synthesize("Une autre réponse") == wav()
        assert client.ready and client.process is process and len(calls) == 1
        assert calls[0][1]["env"]["CUDA_VISIBLE_DEVICES"] == ""
        assert calls[0][1]["env"]["HF_HUB_OFFLINE"] == "1"
        assert not (tmp_path / "saved.wav").exists()
    finally:
        client.close()
    assert process.poll() is not None and not client.ready


def test_worker_timeout_terminates_process_and_can_be_retried(tmp_path, monkeypatch):
    import subprocess
    original_popen = subprocess.Popen
    script = tmp_path / "stalled_worker.py"
    script.write_text("import time\ntime.sleep(30)\n")
    processes = []
    def popen(command, **kwargs):
        process = original_popen([sys.executable, "-u", str(script)], **kwargs)
        processes.append(process)
        return process
    monkeypatch.setattr(subprocess, "Popen", popen)
    client = ChatterboxCPU(config(tmp_path), timeout=.1)
    for _ in range(2):
        with pytest.raises(ChatterboxCPUError, match="délai"):
            client.start()
        assert not client.ready and processes[-1].poll() is not None


def test_chatterbox_is_not_a_voice_service_engine(tmp_path):
    voice=VoiceService(tmp_path)
    with pytest.raises(ValueError):voice.set_voice("chatterbox-cpu")
    assert not hasattr(voice,"_chatterbox")
