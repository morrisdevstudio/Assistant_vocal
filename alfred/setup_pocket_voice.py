"""Prépare le profil Pocket TTS local ; aucun secret n'est écrit dans le projet."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np
import soundfile as sf
import yaml
from huggingface_hub import hf_hub_download
from scipy.signal import resample_poly


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / ".local" / "data" / "voice-references" / "alfred"
MODELS = ROOT / ".local" / "models" / "pocket-tts"
SOURCE_WAV = DATA / "source.wav"
SOURCE_CLEAN_WAV = DATA / "source-clean.wav"
SOURCE_CLEAN_TEXT = DATA / "source-clean.txt"
REFERENCE_WAV = MODELS / "reference-24k.wav"
REFERENCE_TEXT = MODELS / "reference.txt"
LOCAL_CONFIG = MODELS / "french-local.yaml"
VOICE_STATE = MODELS / "alfred.safetensors"
MANIFEST = MODELS / "manifest.json"
MODEL_REPO = "kyutai/pocket-tts"
MODEL_REVISION = "3e82814a68665eec246ff649b14c71331f955c06"
TOKENIZER_REPO = "kyutai/pocket-tts-without-voice-cloning"
TOKENIZER_REVISION = "8843db76457a91db32077edf8dfcd1c0e3e755fd"


def sha256(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def trim_silence(samples: np.ndarray, rate: int):
    frame = max(1, int(rate * 0.02))
    frames = samples[: len(samples) // frame * frame].reshape(-1, frame)
    energy = np.sqrt(np.mean(frames * frames, axis=1))
    active = np.flatnonzero(energy >= max(0.005, float(energy.max()) * 0.04))
    if not len(active):
        return samples
    margin = int(rate * 0.10)
    start = max(0, int(active[0]) * frame - margin)
    end = min(len(samples), (int(active[-1]) + 1) * frame + margin)
    return samples[start:end]


def prepare_reference():
    source_wav = SOURCE_CLEAN_WAV if SOURCE_CLEAN_WAV.is_file() else SOURCE_WAV
    source_text = SOURCE_CLEAN_TEXT if SOURCE_CLEAN_TEXT.is_file() else DATA / "source.txt"
    if not source_wav.is_file():
        raise FileNotFoundError(f"Échantillon source absent : {source_wav}")
    MODELS.mkdir(parents=True, exist_ok=True)
    audio, rate = sf.read(source_wav)
    mono = np.asarray(audio.mean(axis=1) if audio.ndim > 1 else audio, dtype=np.float32)
    # L'échantillon complet donne une meilleure similarité de timbre que
    # l'extrait court, tout en restant assez court pour l'extraction initiale.
    excerpt = mono
    divisor = math.gcd(24000, rate)
    excerpt = resample_poly(excerpt, 24000 // divisor, rate // divisor).astype(np.float32)
    excerpt = trim_silence(excerpt, 24000)
    peak = float(np.max(np.abs(excerpt)))
    if not peak:
        raise RuntimeError("L'extrait vocal est silencieux.")
    excerpt = excerpt / peak * 0.90
    sf.write(REFERENCE_WAV, excerpt, 24000, subtype="PCM_16")
    REFERENCE_TEXT.write_text(
        source_text.read_text(encoding="utf-8").strip() if source_text.is_file() else "",
        encoding="utf-8",
    )
    return round(len(excerpt) / 24000, 3), source_wav


def download_models():
    MODELS.mkdir(parents=True, exist_ok=True)
    weights = Path(hf_hub_download(
        MODEL_REPO, "languages/french/model.safetensors", revision=MODEL_REVISION,
        local_dir=MODELS / "source", token=os.environ.get("HF_TOKEN"),
    ))
    tokenizer = Path(hf_hub_download(
        TOKENIZER_REPO, "languages/french/tokenizer.json", revision=TOKENIZER_REVISION,
        local_dir=MODELS / "source", token=os.environ.get("HF_TOKEN"),
    ))
    return weights, tokenizer


def write_local_config(weights: Path, tokenizer: Path):
    import pocket_tts

    source_config = Path(pocket_tts.__file__).parent / "config" / "french.yaml"
    config = yaml.safe_load(source_config.read_text(encoding="utf-8"))
    local_weights = str(weights.resolve()).replace("\\", "/")
    config["weights_path"] = local_weights
    config["weights_path_without_voice_cloning"] = local_weights
    config["flow_lm"]["lookup_table"]["tokenizer_path"] = str(tokenizer.resolve()).replace("\\", "/")
    LOCAL_CONFIG.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")


def export_voice():
    from pocket_tts import TTSModel, export_model_state

    model = TTSModel.load_model(config=LOCAL_CONFIG, quantize=False)
    state = model.get_state_for_audio_prompt(REFERENCE_WAV)
    export_model_state(state, VOICE_STATE)
    return model


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-only", action="store_true")
    args = parser.parse_args()
    seconds, source_wav = prepare_reference()
    print(f"Référence Pocket TTS prête : {seconds:.2f} s, 24 kHz mono.", flush=True)
    if args.reference_only:
        return
    try:
        weights, tokenizer = download_models()
    except Exception as error:
        raise SystemExit(
            "Téléchargement Pocket TTS impossible. Accepter les conditions sur "
            "https://huggingface.co/kyutai/pocket-tts puis lancer « .\\.venv\\Scripts\\hf.exe auth login » "
            "dans un terminal, sans coller le jeton dans le chat."
        ) from error
    write_local_config(weights, tokenizer)
    export_voice()
    MANIFEST.write_text(json.dumps({
        "engine": "pocket-tts", "engine_version": "4.0.1",
        "model_repository": MODEL_REPO, "model_revision": MODEL_REVISION,
        "tokenizer_repository": TOKENIZER_REPO, "tokenizer_revision": TOKENIZER_REVISION,
        "source_file": str(source_wav.relative_to(ROOT)).replace("\\", "/"),
        "source_sha256": sha256(source_wav), "reference_sha256": sha256(REFERENCE_WAV),
        "reference_start_seconds": 0.0, "reference_end_seconds": seconds,
        "reference_seconds": seconds,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Profil Pocket TTS exporté localement. Aucun accès réseau ne sera nécessaire à l'inférence.")


if __name__ == "__main__":
    main()
