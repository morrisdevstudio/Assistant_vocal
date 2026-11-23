"""Téléchargement explicite des modèles publics ; jamais depuis une requête audio."""

import json
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download

ROOT = Path(__file__).resolve().parents[1] / ".local" / "models"


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    api = HfApi(token=False)
    tts_repo = "Supertone/supertonic-3"
    tts_revision = api.model_info(tts_repo, token=False).sha
    from alfred.setup_vad import prepare_vad
    prepare_vad(ROOT)
    speaker_repo = "speechbrain/spkrec-ecapa-voxceleb"
    speaker_revision = api.model_info(speaker_repo, token=False).sha
    print("Téléchargement du modèle d'empreinte vocale ECAPA…", flush=True)
    snapshot_download(speaker_repo, revision=speaker_revision, token=False,
                      local_dir=ROOT / "speechbrain" / "spkrec-ecapa-voxceleb", allow_patterns=[
                          "hyperparams.yaml", "*.ckpt", "label_encoder.txt",
                      ])
    print("Téléchargement du moteur vocal Supertonic 3 et des voix françaises…", flush=True)
    snapshot_download(tts_repo, revision=tts_revision, token=False,
                      local_dir=ROOT / "supertonic-3", allow_patterns=[
                          "config.json", "LICENSE", "onnx/*", "voice_styles/M?.json",
                      ])
    (ROOT / "sources.json").write_text(json.dumps({
        "tts": {"repository": tts_repo, "revision": tts_revision,
                "voices": [f"M{number}" for number in range(1, 6)], "default": "M3"},
        "speaker": {"repository": speaker_repo, "revision": speaker_revision},
    }, indent=2), encoding="utf-8")
    print("Modèles disponibles localement. Le service ne téléchargera rien à l'écoute.")


if __name__ == "__main__":
    main()
