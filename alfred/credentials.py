"""Clé propre à Alfred : jamais renvoyée par l'API ou lue dans une autre app."""

import ctypes
import json
import os
import tempfile
import threading
from pathlib import Path

DEFAULT_MODEL = "deepseek/deepseek-v4-flash"


class ConfigurationError(RuntimeError):
    pass


def windows_crypt(data: bytes, decrypt=False):
    from ctypes import wintypes

    class Blob(ctypes.Structure):
        _fields_ = [("size", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_ubyte))]

    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    target = Blob()
    crypt = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    if decrypt:
        operation = crypt.CryptUnprotectData
        operation.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p,
                              ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
        description = None
    else:
        operation = crypt.CryptProtectData
        operation.argtypes = [ctypes.POINTER(Blob), wintypes.LPCWSTR, ctypes.c_void_p,
                              ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
        description = "Alfred Command Code"
    operation.restype = wintypes.BOOL
    if not operation(ctypes.byref(source), description, None, None, None, 1, ctypes.byref(target)):
        raise ConfigurationError("Impossible de protéger ou relire la configuration locale.")
    try:
        return ctypes.string_at(target.data, target.size)
    finally:
        kernel.LocalFree(ctypes.cast(target.data, ctypes.c_void_p))


class CredentialStore:
    def __init__(self, directory: Path, api_key="", model=None):
        self.path = directory / "commandcode.secret"
        self._env_key = api_key
        self._env_model = model
        self._lock = threading.Lock()

    def _read(self):
        if not self.path.exists():
            return {}
        try:
            raw = self.path.read_bytes()
            if raw.startswith(b"DPAPI\n"):
                if os.name != "nt":
                    raise ConfigurationError("Cette clé est liée au compte Windows. Reconfigurez-la sur ce système.")
                raw = windows_crypt(raw[6:], decrypt=True)
            elif os.name == "nt":
                raise ConfigurationError("Format de configuration locale non protégé.")
            elif self.path.stat().st_mode & 0o077:
                raise ConfigurationError("La configuration locale doit avoir les permissions 0600.")
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise ValueError()
            return result
        except ConfigurationError:
            raise
        except Exception as error:
            raise ConfigurationError("Impossible de lire la configuration Command Code.") from error

    def _values(self, saved):
        key = self._env_key or saved.get("api_key", "")
        model = self._env_model or saved.get("model", DEFAULT_MODEL)
        if not isinstance(key, str) or not isinstance(model, str):
            raise ConfigurationError("Configuration Command Code invalide.")
        return key, model

    def values(self):
        with self._lock:
            return self._values(self._read())

    @staticmethod
    def _models(saved, model):
        models = saved.get("models", [])
        if not isinstance(models, list) or any(not isinstance(item, str) for item in models):
            raise ConfigurationError("Liste de modèles Command Code invalide.")
        return list(dict.fromkeys([*models, model]))

    def public(self):
        with self._lock:
            saved = self._read()
            key, model = self._values(saved)
            return {"configured": bool(key), "model": model, "models": self._models(saved, model),
                    "key_from_environment": bool(self._env_key), "model_from_environment": bool(self._env_model),
                    "storage": "Windows DPAPI" if os.name == "nt" else "fichier privé 0600"}

    def save(self, key: str | None, model: str):
        if self._env_key or self._env_model:
            raise ConfigurationError("La configuration provient de l'environnement. Modifiez-la au lancement du service.")
        with self._lock:
            # Une nouvelle clé permet aussi de remplacer un fichier devenu illisible.
            try:
                previous = self._read()
            except ConfigurationError:
                if key is None:
                    raise
                previous = {}
            effective_key = key if key is not None else previous.get("api_key", "")
            if not effective_key:
                raise ConfigurationError("Saisissez une clé API pour configurer Alfred.")
            models = self._models(previous, previous.get("model", model))
            self._write({"api_key": effective_key, "model": model, "models": self._models({"models": models}, model)})
        return self.public()

    def update_model(self, model, *, activate=False):
        with self._lock:
            saved = self._read()
            key, active = self._values(saved)
            if not key:
                raise ConfigurationError("Configurez d’abord votre clé Command Code dans Alfred.")
            if activate and self._env_model:
                raise ConfigurationError("Le modèle actif est imposé au lancement du service.")
            models = self._models(saved, active)
            if model not in models:
                if activate:
                    raise ConfigurationError("Ajoutez ce modèle avant de le sélectionner.")
                models.append(model)
            if activate:
                saved["model"] = model
            self._write({**saved, "models": models})

    def _write(self, saved):
        raw = json.dumps(saved).encode("utf-8")
        if os.name == "nt":
            raw = b"DPAPI\n" + windows_crypt(raw)
        name = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, name = tempfile.mkstemp(prefix="commandcode-", suffix=".tmp", dir=self.path.parent)
            with os.fdopen(fd, "wb") as output:
                if os.name != "nt":
                    os.fchmod(output.fileno(), 0o600)
                output.write(raw)
                output.flush()
                os.fsync(output.fileno())
            os.replace(name, self.path)
        except OSError as error:
            raise ConfigurationError("Impossible d'enregistrer la configuration locale.") from error
        finally:
            if name and os.path.exists(name):
                os.unlink(name)
