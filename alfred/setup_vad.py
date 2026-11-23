"""Préparation explicite du seul détecteur de parole Silero utilisé par Alfred."""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

from alfred.config import Settings

VAD_URL = "https://raw.githubusercontent.com/SYSTRAN/faster-whisper/v1.2.1/faster_whisper/assets/silero_vad_v6.onnx"
VAD_SHA256 = "4cbf549b8326f60f80f2536d9eefeb450a9abe83365a098031c89719f1be17d2"


def prepare_vad(models_dir: Path, source: Path | None = None):
    folder = models_dir / "silero-v6"
    target = folder / "silero_vad_v6.onnx"
    if target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest() == VAD_SHA256:
        return target
    if source:
        content = source.read_bytes()
    else:
        with urlopen(VAD_URL, timeout=60) as response:
            content = response.read(4 * 1024 * 1024)
    if hashlib.sha256(content).hexdigest() != VAD_SHA256:
        raise ValueError("Empreinte du modèle Silero incorrecte ; aucune ressource remplacée.")
    folder.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_bytes(content)
    temporary.replace(target)
    (folder / "source.json").write_text(json.dumps({
        "model": "Silero VAD v6", "url": VAD_URL, "sha256": VAD_SHA256,
        "license": "MIT", "authors": "Silero Team",
        "license_reference": "https://github.com/snakers4/silero-vad/blob/master/LICENSE",
    }, indent=2), encoding="utf-8")
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="Copie locale vérifiée, sans téléchargement")
    args = parser.parse_args()
    prepare_vad(Settings.from_env().models_dir, args.source)
    print("Silero VAD v6 autonome préparé et empreinte vérifiée.")


if __name__ == "__main__":
    main()
