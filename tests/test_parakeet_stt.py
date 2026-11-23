import io
import json
import queue
import struct
import subprocess
import sys
import time

import numpy as np
import pytest

from alfred import parakeet_stt
from alfred.parakeet_stt import ParakeetError, ParakeetSTT
from alfred.voice import VoiceService, VoiceUnavailable


def test_framed_reader_rejects_truncation_and_oversized_output():
    for stream in (io.BytesIO(b"x"), io.BytesIO(struct.pack("<I", 2_000_000)),
                   io.BytesIO(struct.pack("<I", 3) + b"[] ")):
        responses = queue.Queue()
        ParakeetSTT._read_responses(stream, responses)
        assert responses.get_nowait() is None


@pytest.fixture
def fake_worker(tmp_path, monkeypatch):
    script = tmp_path / "worker.py"
    script.write_text('''import sys,struct,json,time
def send(value):
 b=json.dumps(value).encode();sys.stdout.buffer.write(struct.pack('<I',len(b))+b);sys.stdout.buffer.flush()
send({'ready':True})
if sys.argv[1]=='blocked_write':time.sleep(10);sys.exit()
while True:
 header=sys.stdin.buffer.read(4)
 if not header:break
 count=struct.unpack('<I',header)[0];body=sys.stdin.buffer.read(count)
 if sys.argv[1]=='crash':sys.exit(1)
 if sys.argv[1]=='stall':time.sleep(10)
 if sys.argv[1]=='invalid':send({'text':123});continue
 if sys.argv[1]=='error':send({'error':'private'});continue
 send({'text':'Bonjour Alfred.'})
''', encoding="utf-8")
    real_popen = subprocess.Popen
    mode = ["ok"]
    def spawn(args, **kwargs):
        return real_popen([sys.executable, "-u", str(script), mode[0]], **kwargs)
    monkeypatch.setattr(parakeet_stt.subprocess, "Popen", spawn)
    monkeypatch.setattr(parakeet_stt, "INFERENCE_TIMEOUT", .2)
    monkeypatch.setattr(parakeet_stt, "WRITE_TIMEOUT", .2)
    engine = ParakeetSTT(tmp_path / "models", tmp_path / "config.json")
    monkeypatch.setattr(engine, "available", lambda: True)
    try:
        yield engine, mode
    finally:
        engine.close()


def test_worker_is_persistent_closes_and_starts_again(fake_worker):
    engine, _ = fake_worker
    assert engine.transcribe(np.zeros(16000)) == "Bonjour Alfred."
    process = engine._process
    assert engine.transcribe(np.zeros(16000)) == "Bonjour Alfred."
    assert engine._process is process
    engine.close()
    assert process.poll() is not None and not engine.ready
    assert engine.transcribe(np.zeros(16000)) == "Bonjour Alfred."
    assert engine._process is not process


@pytest.mark.parametrize("failure", ["crash", "stall", "blocked_write", "invalid", "error"])
def test_worker_failure_kills_child_and_next_call_can_recover(fake_worker, failure):
    engine, mode = fake_worker
    mode[0] = failure
    engine.preload()
    process = engine._process
    started = time.monotonic()
    with pytest.raises(ParakeetError) as caught:
        engine.transcribe(np.zeros(30 * 16000))
    assert "private" not in str(caught.value)
    assert time.monotonic() - started < 5
    assert process.poll() is not None and not engine.ready
    mode[0] = "ok"
    assert engine.transcribe(np.zeros(16000)) == "Bonjour Alfred."


@pytest.mark.parametrize("samples", [[], [float("nan")], [float("inf")], [[0]], np.zeros(480001)])
def test_invalid_pcm_never_starts_worker(tmp_path, monkeypatch, samples):
    engine = ParakeetSTT(tmp_path / "models", tmp_path / "config.json")
    monkeypatch.setattr(engine, "preload", lambda: pytest.fail("Audio invalide : aucun worker"))
    with pytest.raises(ParakeetError):
        engine.transcribe(samples)


def test_parakeet_is_only_backend_and_failure_is_explicit(tmp_path, monkeypatch):
    data = tmp_path / "data"
    data.mkdir()
    voice = VoiceService(tmp_path / "models", voice_file=data / "voice.json")
    assert voice.stt_model == "parakeet"
    assert voice.status()["stt_engine"] == "murmure-native"
    assert voice.status()["stt_available"] is False
    monkeypatch.setattr("alfred.voice.pcm_16khz", lambda data: np.zeros(16000))
    monkeypatch.setattr(voice._parakeet, "transcribe", lambda samples: "Est-ce que tu peux me raconter une histoire ?")
    assert voice._recognize(b"wav").startswith("Est-ce que")
    def failed(samples):
        raise ParakeetError("Moteur indisponible")
    monkeypatch.setattr(voice._parakeet, "transcribe", failed)
    with pytest.raises(VoiceUnavailable):
        voice._recognize(b"wav")
