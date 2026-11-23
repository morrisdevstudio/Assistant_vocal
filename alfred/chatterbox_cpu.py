"""Client d'un processus TTS CPU persistant, isolé des dépendances d'Alfred."""
import base64
import json
import os
from pathlib import Path
import queue
import subprocess
import threading

MAX_MESSAGE = 9 * 1024 * 1024
MODEL_FILES = ("ve.pt", "t3_mtl23ls_v2.safetensors", "s3gen.pt",
               "grapheme_mtl_merged_expanded_v1.json")


class ChatterboxCPUError(RuntimeError):
    pass


class ChatterboxCPU:
    worker_module = "alfred.chatterbox_worker"
    config_path_fields = ("python", "site_packages", "model_dir", "reference")
    def __init__(self, config_path, timeout=60):
        self.config_path = Path(config_path)
        self.timeout = timeout
        self.process = None
        self.messages = None
        self.reader = None
        self._ready = False
        self._lock = threading.RLock()

    def configuration(self):
        value = json.loads(self.config_path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("Configuration Chatterbox CPU invalide")
        for key in self.config_path_fields:
            if not isinstance(value.get(key), str) or not Path(value[key]).is_absolute():
                raise ValueError("Configuration Chatterbox CPU invalide")
        return value

    def available(self):
        try:
            config = self.configuration()
            return (Path(config["python"]).is_file() and Path(config["reference"]).is_file()
                    and (Path(config["site_packages"]) / "chatterbox/mtl_tts.py").is_file()
                    and all((Path(config["model_dir"]) / name).is_file() for name in MODEL_FILES))
        except (OSError, ValueError, TypeError):
            return False

    @property
    def ready(self):
        return self._ready and self.process is not None and self.process.poll() is None

    def _receive(self):
        try:
            value = self.messages.get(timeout=self.timeout)
            if value is None or value.get("error"):
                raise ChatterboxCPUError("Le moteur Chatterbox CPU est indisponible.")
            return value
        except queue.Empty as error:
            raise ChatterboxCPUError("Le délai de génération Chatterbox CPU est dépassé.") from error

    def start(self):
        with self._lock:
            if self.ready:
                return
            if not self.available():
                raise ChatterboxCPUError("Chatterbox CPU n'est pas préparé localement.")
            config = self.configuration()
            environment = dict(os.environ)
            root = Path(__file__).resolve().parents[1]
            environment.update(PYTHONPATH=os.pathsep.join((config["site_packages"], str(root))),
                               HF_HUB_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1",
                               CUDA_VISIBLE_DEVICES="", TQDM_DISABLE="1")
            self.messages = messages = queue.Queue()
            self.process = process = subprocess.Popen(
                [config["python"], "-u", "-m", self.worker_module,
                 "--config", str(self.config_path.resolve())],
                cwd=root, env=environment, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

            def read():
                try:
                    while line := process.stdout.readline(MAX_MESSAGE + 1):
                        if len(line) > MAX_MESSAGE:
                            break
                        messages.put(json.loads(line))
                except (OSError, ValueError):
                    pass
                finally:
                    messages.put(None)

            self.reader = threading.Thread(target=read, daemon=True, name="chatterbox-cpu-output")
            self.reader.start()
            try:
                if self._receive().get("ready") is not True:
                    raise ChatterboxCPUError("Chargement Chatterbox CPU non confirmé.")
                self._ready = True
            except Exception:
                self.close()
                raise

    def synthesize(self, text):
        with self._lock:
            self.start()
            try:
                self.process.stdin.write((json.dumps({"text": text}, ensure_ascii=True) + "\n").encode())
                self.process.stdin.flush()
                result = self._receive()
                return base64.b64decode(result["audio"], validate=True)
            except Exception as error:
                self.close()
                if isinstance(error, ChatterboxCPUError):
                    raise
                raise ChatterboxCPUError("La génération Chatterbox CPU a échoué.") from error

    def close(self):
        with self._lock:
            process, self.process = self.process, None
            self._ready = False
            if process is None:
                return
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            for pipe in (process.stdin, process.stdout):
                if pipe:
                    pipe.close()
            if self.reader:
                self.reader.join(timeout=1)
                self.reader = None
