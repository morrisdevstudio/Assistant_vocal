"""Outils locaux de mesure et de transcription pour la recette acoustique."""

import argparse
import json
import math
from pathlib import Path
import time

import numpy as np
from scipy.fft import irfft, next_fast_len, rfft
from scipy.io import wavfile
from scipy.signal import butter, chirp, sosfilt, windows

from alfred.parakeet_stt import MODEL_DIRECTORY, ParakeetSTT
from alfred.voice import pcm_16khz, validate_wav


RATE = 16_000
SWEEP_SECONDS = 2
TAIL_SECONDS = 1


def test_signal():
    times = np.arange(RATE * SWEEP_SECONDS) / RATE
    sweep = chirp(times, f0=350, t1=SWEEP_SECONDS, f1=6000, method="logarithmic")
    sweep *= windows.tukey(len(sweep), alpha=0.04) * 0.25
    return np.rint(sweep * 32768).astype(np.int16)


def write_signal(path):
    sweep = test_signal()
    samples = np.pad(sweep, (RATE, RATE * 2))
    with path.open("xb") as file:
        wavfile.write(file, RATE, samples)


def load_samples(path):
    wav = path.read_bytes()
    validate_wav(wav)
    return pcm_16khz(wav)


def measure(samples):
    sweep = test_signal().astype(np.float64) / 32768
    tail = RATE * TAIL_SECONDS
    if len(samples) < len(sweep) + tail:
        raise ValueError("L'enregistrement doit inclure le balayage et sa queue sonore.")
    size = next_fast_len(len(samples) + len(sweep), real=True)
    emitted = rfft(sweep, size)
    received = rfft(samples, size)
    power = np.abs(emitted) ** 2
    response = irfft(received * emitted.conj() / (power + power.max() * 1e-3), size)
    latest_start = len(samples) - len(sweep) - tail
    valid = np.abs(response[:latest_start + 1])
    peak = int(valid.argmax())
    if valid[peak] < 1e-5:
        raise ValueError("Balayage trop faible ou absent.")
    # Recul borné pour retenir une arrivée antérieure au pic dominant.
    left = max(0, peak - int(0.04 * RATE))
    arrival = left + int(np.flatnonzero(valid[left:peak + 1] >= valid[peak] * 0.2)[0])
    window = response[arrival:arrival + tail]
    early = float(np.sum(window[:RATE // 20] ** 2))
    late = float(np.sum(window[RATE // 20:] ** 2))
    return {
        "debut_estime_s": round(arrival / RATE, 3),
        "rapport_0_50_sur_50_1000_ms_db": round(10 * math.log10(early / max(late, 1e-30)), 2),
        "crete_dbfs": round(20 * math.log10(max(float(np.abs(samples).max()), 1e-9)), 2),
        "fraction_proche_saturation": round(float(np.mean(np.abs(samples) >= 32760 / 32768)), 6),
    }


def transcribe(paths, local, compare=False):
    engine = ParakeetSTT(local / "models" / MODEL_DIRECTORY, local / "data" / "stt-murmure.json")
    try:
        engine.preload()
        highpass = butter(2, 120, btype="highpass", fs=RATE, output="sos") if compare else None
        for path in paths:
            samples = load_samples(path)
            variants = {"temoin": samples}
            if compare:
                variants["passe-haut-120-hz"] = sosfilt(highpass, samples)
            for name, signal in variants.items():
                start = time.perf_counter()
                result = {"fichier": path.name, "reglage": name,
                          "texte": engine.transcribe(signal),
                          "stt_ms": round(1000 * (time.perf_counter() - start))}
                print(json.dumps(result, ensure_ascii=False))
    finally:
        engine.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("signal", help="Créer le WAV à lire sur le téléphone").add_argument("wav", type=Path)
    commands.add_parser("mesure", help="Analyser des prises du balayage").add_argument("wav", type=Path, nargs="+")
    speech = commands.add_parser("transcrire", help="Comparer les prises avec le Parakeet d'Alfred")
    speech.add_argument("wav", type=Path, nargs="+")
    speech.add_argument("--local", type=Path, default=Path(".local"))
    speech.add_argument("--comparer", action="store_true",
                        help="Rejouer chaque prise avec et sans un passe-haut à 120 Hz")
    options = parser.parse_args()
    if options.command == "signal":
        write_signal(options.wav)
    elif options.command == "mesure":
        for path in options.wav:
            print(json.dumps({"fichier": path.name, **measure(load_samples(path))}, ensure_ascii=False))
    else:
        transcribe(options.wav, options.local, options.comparer)


if __name__ == "__main__":
    main()
