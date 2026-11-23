"""Empreintes vocales locales ECAPA-TDNN, chargées à la demande et sans réseau."""

import importlib.util
import threading
from pathlib import Path

MODEL_REPOSITORY = "speechbrain/spkrec-ecapa-voxceleb"
MODEL_LABEL = "ECAPA-TDNN VoxCeleb · 192 valeurs"
REQUIRED_FILES = ("hyperparams.yaml", "embedding_model.ckpt", "mean_var_norm_emb.ckpt",
                  "label_encoder.ckpt")


class SpeakerUnavailable(RuntimeError):
    pass


class SpeakerBusy(RuntimeError):
    pass


class SpeakerService:
    def __init__(self, directory: Path):
        self.model_path = Path(directory) / "speechbrain/spkrec-ecapa-voxceleb"
        self._model = None
        self._lock = threading.Lock()

    def status(self):
        installed = importlib.util.find_spec("speechbrain") is not None
        present = installed and all((self.model_path / name).exists() for name in REQUIRED_FILES)
        return {"available": present, "model": MODEL_LABEL, "busy": self._lock.locked()}

    def _engine(self):
        if importlib.util.find_spec("speechbrain") is None:
            raise SpeakerUnavailable("Le moteur d'empreinte vocale n'est pas installé.")
        if not all((self.model_path / name).exists() for name in REQUIRED_FILES):
            raise SpeakerUnavailable("Le modèle d'empreinte vocale n'est pas préparé.")
        if self._model is None:
            from speechbrain.inference.speaker import EncoderClassifier
            self._model = EncoderClassifier.from_hparams(
                source=MODEL_REPOSITORY,
                savedir=str(self.model_path),
                run_opts={"device": "cpu"},
            )
        return self._model

    def embed_pcm(self, pcm):
        """PCM mono 16 kHz en float32 -> vecteur de 192 valeurs."""
        if not self._lock.acquire(blocking=False):
            raise SpeakerBusy("Un calcul d'empreinte est déjà en cours.")
        try:
            import numpy as np
            import torch
            values = np.asarray(pcm, dtype="float32").reshape(-1)
            if values.size < 8000:
                raise ValueError("Trop court pour une empreinte vocale : une seconde au minimum.")
            with torch.no_grad():
                vector = self._engine().encode_batch(torch.from_numpy(values).unsqueeze(0))
            return [float(value) for value in vector.squeeze().reshape(-1).tolist()]
        finally:
            self._lock.release()

    def embed_wav(self, data):
        from alfred.voice import pcm_16khz, validate_wav
        validate_wav(data)
        return self.embed_pcm(pcm_16khz(data))

