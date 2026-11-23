"""Silero VAD local en continu ; état indépendant pour chaque prise micro."""
from functools import lru_cache
from alfred.config import Settings


@lru_cache(maxsize=4)
def vad_session(path):
    import onnxruntime
    if not path.is_file():
        raise RuntimeError("Modèle Silero absent : exécuter python -m alfred.setup_vad.")
    options = onnxruntime.SessionOptions()
    options.inter_op_num_threads = 1
    options.intra_op_num_threads = 1
    options.enable_cpu_mem_arena = False
    options.log_severity_level = 4
    return onnxruntime.InferenceSession(str(path), providers=["CPUExecutionProvider"], sess_options=options)


class SpeechActivity:
    name = "silero-v6"

    def __init__(self):
        import numpy as np
        # Même modèle et mêmes options ONNX ; ressource autonome, sans moteur STT tiers.
        self.session = vad_session(Settings.from_env().models_dir / "silero-v6/silero_vad_v6.onnx")
        self.pending = bytearray()
        self.h = np.zeros((1, 1, 128), dtype="float32")
        self.c = np.zeros((1, 1, 128), dtype="float32")
        self.context = np.zeros((1, 64), dtype="float32")
        self.probability = 0.
        self.active = False

    def feed(self, data):
        import numpy as np
        self.pending.extend(data)
        # 512 échantillons à 16 kHz, soit 32 ms. Les paquets réseau peuvent
        # avoir une autre taille ; conserver seulement la fraction non analysée.
        while len(self.pending) >= 1024:
            pcm = np.frombuffer(bytes(self.pending[:1024]), dtype="<i2").astype("float32") / 32768
            del self.pending[:1024]
            frame = pcm.reshape(1, -1)
            output, self.h, self.c = self.session.run(
                None, {"input": np.concatenate([self.context, frame], axis=1),
                       "h": self.h, "c": self.c})
            self.context = frame[:, -64:].copy()
            self.probability = float(np.asarray(output).reshape(-1)[0])
            if self.probability >= .5:
                self.active = True
            elif self.probability < .35:
                self.active = False
        return self.active
