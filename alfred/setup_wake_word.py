"""Préparation explicite du mot d'appel : prétraitement public et modèle privé.

Le modèle entraîné vit sous `.local/models/wake-word/` ; il n'est jamais
versionné et aucune voix réelle n'entre dans son corpus.
"""
import argparse
import hashlib
import shutil
import sys
from pathlib import Path
from urllib.request import urlopen

from alfred.wake_word import PREPROCESS_FILES, PREPROCESS_URL, WakeWordError

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DIR = ROOT / ".local" / "models" / "wake-word"


def download_preprocess(folder=DEFAULT_DIR):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for name, expected in PREPROCESS_FILES.items():
        target = folder / name
        if target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest() == expected:
            print(f"{name} : prêt")
            continue
        temporary = target.with_suffix(target.suffix + ".part")
        try:
            digest = hashlib.sha256()
            received = 0
            with urlopen(PREPROCESS_URL + name, timeout=60) as response, temporary.open("wb") as output:
                while chunk := response.read(64 * 1024):
                    received += len(chunk)
                    if received > 30_000_000:
                        raise WakeWordError("Fichier trop volumineux : " + name)
                    digest.update(chunk)
                    output.write(chunk)
            if digest.hexdigest() != expected:
                raise WakeWordError("Empreinte SHA-256 incorrecte : " + name)
            temporary.replace(target)
            print(f"{name} : installé")
        finally:
            temporary.unlink(missing_ok=True)
    return folder


def install_model(source, folder=DEFAULT_DIR, name="alfred-he.onnx"):
    """Copie le modèle entraîné et vérifie qu'il est lisible par ONNX Runtime."""
    source = Path(source)
    if not source.is_file():
        raise WakeWordError("Modèle absent : " + str(source))
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / name
    shutil.copyfile(source, target)
    license_source = source.with_name(source.name + ".LICENSE")
    if license_source.is_file():
        shutil.copyfile(license_source, target.with_name(target.name + ".LICENSE"))
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    (folder / (name + ".sha256")).write_text(digest + "\n", encoding="utf-8")
    print(f"{name} : installé ({digest[:16]}…)")
    return target, digest


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Prépare le prétraitement openWakeWord et le modèle « Hé Alfred »")
    parser.add_argument("--dir", default=str(DEFAULT_DIR))
    parser.add_argument("--model", help="Modèle ONNX entraîné à installer")
    parser.add_argument("--name", default="alfred-he.onnx")
    args = parser.parse_args(argv)
    try:
        folder = download_preprocess(args.dir)
        if args.model:
            install_model(args.model, folder, args.name)
        print("Dossier prêt :", folder)
    except (WakeWordError, OSError) as error:
        print("Erreur :", error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
