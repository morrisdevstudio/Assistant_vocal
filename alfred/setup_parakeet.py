"""Préparation explicite de la stack Murmure autonome, sans capture audio."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from alfred.config import Settings
from alfred.parakeet_stt import MODEL_DIRECTORY, MODEL_FILES, ParakeetSTT
from alfred.setup_vad import prepare_vad


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--murmure-install", type=Path, default=Path("C:/Program Files/murmure"))
    parser.add_argument("--assets", type=Path, help="Dossier contenant les trois ONNX, vocab.txt et tokenizer.json")
    parser.add_argument("--murmure-settings", type=Path, help="Dossier de réglages à importer localement")
    parser.add_argument("--ort-lib-location", type=Path, help="Bibliothèque ORT 1.22.0 préchargée (sinon téléchargement Cargo explicite)")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    settings = Settings.from_env()
    prepare_vad(settings.models_dir)
    models = settings.models_dir / MODEL_DIRECTORY
    config = settings.data_dir / "stt-murmure.json"
    assets = args.assets or args.murmure_install / "_up_" / "resources" / "parakeet-tdt-0.6b-v3-int8"
    tokenizer = assets / "tokenizer.json"
    if not tokenizer.exists():
        tokenizer = assets.parent / "tokenizer.json"
    sources = {name: (tokenizer if name == "tokenizer.json" else assets / name)
               for name in MODEL_FILES if name != "source.json"}
    if not all(path.is_file() for path in sources.values()):
        parser.error("Ressources Parakeet introuvables. Indiquer --assets ou --murmure-install.")
    if not shutil.which("cargo"):
        parser.error("Rust/Cargo est requis à la préparation, pas pendant l'écoute.")
    build_env = os.environ.copy()
    ort_location = args.ort_lib_location
    cached_ort = settings.models_dir.parent / "ort-1.22.0/onnxruntime"
    if ort_location is None and cached_ort.is_dir():
        ort_location = cached_ort
    if ort_location:
        build_env["ORT_LIB_LOCATION"] = str(ort_location.resolve())
    subprocess.run(["cargo", "build", "--release", "--locked", "--manifest-path",
                    str(root / "native/murmure-stt/Cargo.toml"), "--target-dir",
                    str(settings.models_dir.parent / "native-build/murmure-stt")], check=True, env=build_env)
    models.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name, source in sources.items():
        destination = models / name
        if source.resolve() != destination.resolve():
            shutil.copyfile(source, destination)
        with destination.open("rb") as stream:
            hashes[name] = hashlib.file_digest(stream, "sha256").hexdigest()
    upstream = json.loads((root / "native/murmure-stt/UPSTREAM.json").read_text(encoding="utf-8"))
    (models / "source.json").write_text(json.dumps({
        "model": "Parakeet TDT 0.6B v3 INT8 (assets Murmure 1.11.3)",
        "model_reference": "https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3",
        "model_license": "CC-BY-4.0", "upstream": upstream, "sha256": hashes,
    }, indent=2), encoding="utf-8")
    worker = ParakeetSTT(models, config)
    worker.binary.parent.mkdir(parents=True, exist_ok=True)
    built = settings.models_dir.parent / "native-build/murmure-stt/release" / worker.binary.name
    shutil.copyfile(built, worker.binary)
    if os.name != "nt":
        worker.binary.chmod(worker.binary.stat().st_mode | 0o111)
    # Le paquet ORT Windows d'amont fournit cette dépendance même en mode CPU.
    directml = ort_location / "lib/DirectML.dll" if ort_location else built.parent / "DirectML.dll"
    if directml.is_file():
        shutil.copyfile(directml, worker.binary.parent / directml.name)
    # Snapshot local séparé : aucun lien vivant à l'application Murmure.
    if args.murmure_settings:
        dictionary = json.loads((args.murmure_settings / "dictionary.json").read_text(encoding="utf-8"))
        formatting = json.loads((args.murmure_settings / "formatting_rules.json").read_text(encoding="utf-8"))["settings"]
        value = {"dictionary": list(dictionary), "formatting": formatting,
                 "upstream_version": "1.11.3", "imported": True}
        if not all(isinstance(word, str) for word in value["dictionary"]):
            parser.error("Dictionnaire Murmure invalide")
    elif config.exists():
        value = json.loads(config.read_text(encoding="utf-8"))
    else:
        value = {"dictionary": [], "formatting": {"rules": [], "built_in": {
            "short_text_correction": 3, "space_before_punctuation": True,
            "trailing_space": True, "convert_text_numbers": False,
            "text_numbers_language": "fr", "text_numbers_threshold": 0.0}},
            "upstream_version": "1.11.3", "imported": False}
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        import numpy as np
        worker.preload()
        if worker.transcribe(np.zeros(32000, dtype=np.float32)):
            raise RuntimeError("Le contrôle du silence Parakeet n'a pas réussi")
    finally:
        worker.close()
    print("Stack Murmure 1.11.3 préparée : fichiers copiés, worker compilé et silence vérifié.")
    print("Parakeet est le moteur unique d'Alfred. Relancer après préparation.")


if __name__ == "__main__":
    main()
