"""Chaîne Murmure 1.11.3 autonome : worker Rust/ONNX sur CPU, PCM en mémoire."""
import base64
import json
import os
from pathlib import Path
import queue
import struct
import subprocess
import threading


MODEL_DIRECTORY = "parakeet-murmure-1.11.3"
MODEL_FILES = ("encoder-model.int8.onnx", "decoder_joint-model.int8.onnx",
               "nemo128.onnx", "vocab.txt", "tokenizer.json", "source.json")
STARTUP_TIMEOUT = 45
INFERENCE_TIMEOUT = 45
WRITE_TIMEOUT = 10


class ParakeetError(RuntimeError):
    pass


class ParakeetSTT:
    def __init__(self, models: Path, config: Path):
        self.models = models
        self.config = config
        binary_name = "alfred-murmure-stt.exe" if os.name == "nt" else "alfred-murmure-stt"
        default_binary = models.parent.parent / "bin" / binary_name
        self.binary = Path(os.environ.get("ALFRED_PARAKEET_BIN") or default_binary)
        self._process = None
        self._responses = None
        self._reader = None
        self._writer = None
        self._lock = threading.RLock()

    def available(self):
        return self.binary.is_file() and self.config.is_file() and all(
            (self.models / name).is_file() for name in MODEL_FILES)

    @property
    def ready(self):
        return self._process is not None and self._process.poll() is None

    @staticmethod
    def _read_responses(pipe, responses):
        def exact(count):
            result = bytearray()
            while len(result) < count:
                part = pipe.read(count - len(result))
                if not part:
                    raise EOFError()
                result.extend(part)
            return result
        try:
            while True:
                length, = struct.unpack("<I", exact(4))
                if not 0 < length <= 1_400_000:
                    raise ValueError()
                value = json.loads(exact(length))
                if not isinstance(value, dict):
                    raise ValueError()
                responses.put(value)
        except (OSError, EOFError, ValueError):
            responses.put(None)

    def _response(self, timeout):
        try:
            value = self._responses.get(timeout=timeout)
            if value is None or "error" in value:
                raise ParakeetError("Le moteur Parakeet n'a pas terminé la transcription.")
            return value
        except queue.Empty as error:
            raise ParakeetError("Délai maximal du moteur Parakeet dépassé.") from error

    def preload(self):
        with self._lock:
            if self.ready:
                return
            self.close()
            if not self.available():
                raise ParakeetError("Moteur Parakeet absent : préparer les ressources locales.")
            try:
                self._process = subprocess.Popen(
                    [str(self.binary), str(self.models), str(self.models / "tokenizer.json"), str(self.config)],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                    bufsize=0,
                )
                self._responses = queue.Queue()
                self._reader = threading.Thread(target=self._read_responses,
                    args=(self._process.stdout, self._responses), daemon=True)
                self._reader.start()
                if self._response(STARTUP_TIMEOUT).get("ready") is not True:
                    raise ParakeetError("Initialisation Parakeet non confirmée.")
            except Exception as error:
                self.close()
                if isinstance(error, ParakeetError):
                    raise
                raise ParakeetError("Impossible de démarrer le moteur Parakeet local.") from error

    def transcribe(self, samples):
        import numpy as np
        samples = np.asarray(samples, dtype=np.float32)
        if samples.ndim != 1 or not 0 < len(samples) <= 30 * 16000 or not np.isfinite(samples).all():
            raise ParakeetError("Audio Parakeet invalide.")
        pcm = np.clip(np.rint(samples * 32768), -32768, 32767).astype("<i2").tobytes()
        body = json.dumps({"pcm_base64": base64.b64encode(pcm).decode("ascii")}).encode("utf-8")
        with self._lock:
            self.preload()
            try:
                # Isolate writes too: a hung child must not block a full Windows pipe.
                frame = struct.pack("<I", len(body)) + body
                sent = queue.Queue()
                pipe = self._process.stdin
                def write_frame():
                    try:
                        offset = 0
                        while offset < len(frame):
                            written = pipe.write(frame[offset:])
                            if not written:
                                raise OSError()
                            offset += written
                        pipe.flush()
                        sent.put(True)
                    except (OSError, ValueError):
                        sent.put(False)
                self._writer = threading.Thread(target=write_frame, daemon=True)
                self._writer.start()
                if not sent.get(timeout=WRITE_TIMEOUT):
                    raise ParakeetError("Le moteur Parakeet n'a pas reçu l'audio.")
                result = self._response(INFERENCE_TIMEOUT)
                text = result.get("text")
                if not isinstance(text, str) or len(text) > 10000:
                    raise ParakeetError("Réponse Parakeet invalide.")
                return text
            except Exception as error:
                self.close()
                if isinstance(error, ParakeetError):
                    raise
                raise ParakeetError("La transcription Parakeet locale a échoué.") from error

    def close(self):
        with self._lock:
            process, self._process = self._process, None
            if process is not None:
                # No pending request survives close, timeout or a failed worker.
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=5)
                if process.stdin:
                    process.stdin.close()
                if self._reader:
                    self._reader.join(timeout=2)
                if self._writer:
                    self._writer.join(timeout=2)
                if process.stdout:
                    process.stdout.close()
            self._reader = None
            self._writer = None
            self._responses = None
