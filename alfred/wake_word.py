"""Détection locale du mot d'appel « Hé Alfred » sur les trames du terminal.

Le modèle openWakeWord (ONNX) et ses deux modèles de prétraitement vivent dans
un dossier privé. Aucune trame n'est écrite, aucun texte n'est produit : seul un
score est calculé, et un déclenchement n'ouvre aucune action à lui seul.
"""
import hashlib
import threading
import time
from pathlib import Path

RATE = 16000
FRAME_SAMPLES = 1280          # 80 ms, la trame attendue par openWakeWord
FRAME_BYTES = FRAME_SAMPLES * 2
# Mesuré le 6 novembre sur cinq voix Supertonic jamais vues à l'entraînement :
# positifs médians 0,963, maximum des négatifs 0,117 sur 39 phrases. Un seuil de
# 0,25 gagne deux détections par rapport à 0,5 sans aucun faux réveil ; les scores
# positifs ratés restent sous 0,01 et ne sont pas récupérables par le seuil.
DEFAULT_THRESHOLD = .25
DEFAULT_COOLDOWN = 2.

PREPROCESS_FILES = {
    "melspectrogram.onnx": "ba2b0e0f8b7b875369a2c89cb13360ff53bac436f2895cced9f479fa65eb176f",
    "embedding_model.onnx": "70d164290c1d095d1d4ee149bc5e00543250a7316b59f31d056cff7bd3075c1f",
}
PREPROCESS_URL = "https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/"


class WakeWordError(RuntimeError):
    pass


def verify_preprocess(folder):
    """Les deux modèles partagés doivent être présents et intacts."""
    folder = Path(folder)
    for name, expected in PREPROCESS_FILES.items():
        path = folder / name
        if not path.is_file():
            raise WakeWordError("Prétraitement absent : lancez alfred.setup_wake_word")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != expected:
            raise WakeWordError("Prétraitement altéré : " + name)
    return folder


class WakeWordDetector:
    """Score glissant par trame ; le dernier mot n'est jamais conservé."""

    name = "openwakeword"

    def __init__(self, model, preprocess, threshold=DEFAULT_THRESHOLD,
                 cooldown=DEFAULT_COOLDOWN, clock=time.monotonic):
        from openwakeword.model import Model
        self.threshold = float(threshold)
        self.cooldown = float(cooldown)
        self.clock = clock
        self.model = Model(
            wakeword_models=[str(model)],
            inference_framework="onnx",
            melspec_model_path=str(Path(preprocess) / "melspectrogram.onnx"),
            embedding_model_path=str(Path(preprocess) / "embedding_model.onnx"),
        )
        self.key = next(iter(self.model.models))
        self.pending = bytearray()
        self.score = 0.
        self.detections = 0
        self.last_detection = 0.
        self.last_score_at = 0.
        self.inferences = 0
        self._lock = threading.Lock()

    def feed(self, pcm):
        """Consomme un multiple de trames ; renvoie True sur un déclenchement."""
        import numpy as np
        if not pcm:
            return False
        with self._lock:
            self.pending.extend(pcm)
            detected = False
            while len(self.pending) >= FRAME_BYTES:
                frame = bytes(self.pending[:FRAME_BYTES])
                del self.pending[:FRAME_BYTES]
                score = float(self.model.predict(
                    np.frombuffer(frame, dtype="<i2"))[self.key])
                self.score = score
                self.inferences += 1
                self.last_score_at = self.clock()
                if score >= self.threshold and self.last_score_at - self.last_detection >= self.cooldown:
                    self.last_detection = self.last_score_at
                    self.detections += 1
                    detected = True
            return detected

    def status(self):
        return {"detections": self.detections, "score": round(self.score, 3),
                "last_detection": round(self.last_detection, 3),
                "threshold": self.threshold, "inferences": self.inferences}

    def reset_audio(self):
        """Oublie l'audio précédent sans effacer les compteurs ni l'anti-rebond."""
        with self._lock:
            self.pending.clear()
            self.model.reset()
