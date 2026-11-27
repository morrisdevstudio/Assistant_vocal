"""Interface sans privilèges vers les mises à jour du paquet Debian."""

from contextlib import contextmanager
import hmac
import json
from pathlib import Path

try:
    import fcntl
except ImportError:
    fcntl = None


STATE = Path("/var/lib/alfred-updater")
OPERATIONS = ("check", "install", "auto-on", "auto-off")


class UpdatesBusy(Exception):
    pass


class UpdateQueue:
    def __init__(self, directory=STATE):
        self.directory = directory
        self.requests = directory / "requests"
        self.key = directory / "admin.key"
        self.result = directory / "status.json"

    @property
    def available(self):
        return (fcntl is not None and self.key.is_file() and self.requests.is_dir()
                and Path("/usr/lib/systemd/system/alfred-home-update.path").is_file())

    @contextmanager
    def lock(self, *, blocking=False):
        with (self.directory / "operation.lock").open("rb") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
            except BlockingIOError as error:
                raise UpdatesBusy from error
            yield

    def authorized(self, supplied):
        if not 24 <= len(supplied) <= 128:
            return False
        try:
            expected = self.key.read_bytes().strip()
        except OSError:
            return False
        return hmac.compare_digest(expected, supplied.encode("utf-8"))

    def pending(self):
        return next((operation for operation in OPERATIONS if (self.requests / operation).exists()), None)

    def enqueue(self, operation):
        if operation not in OPERATIONS:
            raise ValueError("Opération de mise à jour inconnue")
        with self.lock():
            if self.pending():
                raise UpdatesBusy
            (self.requests / operation).touch(exist_ok=False)

    def read_result(self):
        try:
            result = json.loads(self.result.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return result if isinstance(result, dict) else {}

    def status(self):
        if not self.available:
            return {"available": False}
        try:
            with self.lock():
                result = self.read_result()
                if self.pending():
                    result.update(phase="queued", message="Opération demandée.")
                elif result.get("phase") == "running":
                    result.update(phase="failed", message="L’opération a été interrompue.")
        except UpdatesBusy:
            result = self.read_result()
            result.update(phase="running", message="Opération en cours…")
        except OSError:
            return {"available": False}
        return {**result, "available": True, "auto_enabled": (self.directory / "auto.enabled").exists()}
