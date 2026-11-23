from types import SimpleNamespace
import sys

import numpy as np
import pytest

from alfred.local_voice_models import load_engine


def test_phonon_loads_explicit_local_french_cpu_weights_and_voice(tmp_path, monkeypatch):
    calls = []
    class TTS:
        languages = ["fr"]
        sample_rate = 24000
        def __init__(self, model, **kwargs):
            calls.append((model, kwargs))
        def add_voice(self, name, path):
            calls.append((name, path))
        def synth(self, text, **kwargs):
            calls.append((text, kwargs))
            return np.zeros(2400, dtype=np.float32)
    monkeypatch.setitem(sys.modules, "ptts", SimpleNamespace(TTS=TTS, set_num_threads=lambda n: calls.append(n)))
    config = {"engine": "phonon", "model_dir": str(tmp_path),
              "voice_name": "Lucien", "voice_file": str(tmp_path / "Lucien.safetensors")}
    voice = load_engine(config)
    audio, rate = voice.synthesize("Il n'y a plus de pâtes.")
    assert rate == 24000 and len(audio) == 2400
    assert calls[0] == 4
    assert calls[1] == (str(tmp_path), {"lang": "fr", "device": "cpu", "quant": "q8",
        "temperature": .3, "seed": 42, "voice_catalog": str(tmp_path / "voices.jsonl")})
    assert calls[2] == ("Lucien", config["voice_file"])
    assert calls[3] == ("Il n'y a plus de pâtes.", {"voice": "Lucien", "seed": 42})


def test_english_default_model_cannot_replace_the_french_checkpoint(tmp_path, monkeypatch):
    class TTS:
        languages = ["en"]
        def __init__(self, *args, **kwargs):
            pass
    monkeypatch.setitem(sys.modules, "ptts", SimpleNamespace(TTS=TTS, set_num_threads=lambda n: None))
    with pytest.raises(ValueError, match="français"):
        load_engine({"engine": "phonon", "model_dir": str(tmp_path),
                     "voice_name": "Lucien", "voice_file": str(tmp_path / "voice.safetensors")})
