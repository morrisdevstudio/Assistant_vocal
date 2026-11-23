"""Préférences locales et catalogue des mots d'appel (sans audio ni secrets)."""
import copy
import json
import re
import unicodedata
from pathlib import Path

BUILTINS = {
    "alfred-he.onnx": ("Hé Alfred", "Hé Alfred", ["Eh Alfred", "Hey Alfred"]),
    "jarvisse_20260916_004415.onnx": ("Jarvis", "Jarvis", ["Jarvisse"]),
    "alexa_v0.1.onnx": ("Alexa", "Alexa", []),
}


def words(text):
    text = unicodedata.normalize("NFKD", text.casefold())
    return re.findall(r"[^\W_]+", "".join(c for c in text if not unicodedata.combining(c)), re.UNICODE)


def phrase(value):
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= 40:
        raise ValueError("Le mot d'appel doit contenir de un à quarante caractères.")
    value = value.strip()
    if not 1 <= len(words(value)) <= 4 or any(not (c.isalpha() or c in " '-’") for c in value):
        raise ValueError("Choisissez un mot d'appel de un à quatre mots.")
    return value


def strip_prefix(text, phrases):
    """Retire seulement une séquence initiale de mots entiers, jamais une mention."""
    tokens = list(re.finditer(r"[^\W_]+", text, re.UNICODE))
    for candidate in sorted(phrases, key=lambda p: len(words(p)), reverse=True):
        expected = words(candidate)
        if expected and [words(m.group())[0] for m in tokens[:len(expected)]] == expected:
            end = tokens[len(expected)-1].end()
            return text[end:].lstrip(" ,;:.!?-–—\t\n"), True
    return text, False


class WakeSettings:
    def __init__(self, data_dir, models, terminal=None):
        self.path = Path(data_dir) / "wake-settings.json"
        self.folder = Path(models) / "wake-word"
        self.custom_path = self.folder / "catalog.json"
        self.custom = json.loads(self.custom_path.read_text(encoding="utf-8")) if self.custom_path.exists() else {}
        initial = {"engine": "openwakeword", "model": "jarvisse_20260916_004415.onnx",
                   "threshold": .5, "phrase": "Alfy", "variants": ["Alfi"]}
        self.values = {"browser": copy.deepcopy(initial), "esp32": copy.deepcopy(initial)}
        self.values["browser"]["engine"] = "stt"
        self.resume_esp32 = False
        if terminal:
            self.values["esp32"].update(model=terminal.wake_model, threshold=terminal.wake_threshold)
        if self.path.exists():
            saved = json.loads(self.path.read_text(encoding="utf-8"))
            self.resume_esp32 = saved.get("resume_esp32") is True
            for source in self.values:
                self.values[source] = self.validate(saved[source])

    def validate(self, value):
        if not isinstance(value, dict) or set(value) != {"engine", "model", "threshold", "phrase", "variants"}:
            raise ValueError("Réglages de réveil invalides.")
        if value["engine"] not in ("stt", "openwakeword"):
            raise ValueError("Moteur de réveil inconnu.")
        model = value["model"]
        if not isinstance(model, str) or not re.fullmatch(r"[A-Za-z0-9_-]+\.onnx", model):
            raise ValueError("Modèle de réveil invalide.")
        threshold = value["threshold"]
        if isinstance(threshold, bool) or not isinstance(threshold, (float, int)) or not 0 < threshold < 1:
            raise ValueError("Sensibilité invalide.")
        variants = value["variants"]
        if not isinstance(variants, list) or len(variants) > 8:
            raise ValueError("Huit variantes au maximum.")
        return {**value, "phrase": phrase(value["phrase"]), "variants": [phrase(v) for v in variants]}

    def catalogue(self):
        result = []
        for filename, (label, wake, variants) in {**BUILTINS, **self.custom}.items():
            if (self.folder / filename).is_file():
                result.append({"id": filename, "label": label, "phrase": wake, "variants": variants})
        return result

    def phrases(self, source):
        value = self.values[source]
        if value["engine"] == "stt":
            return [value["phrase"], *value["variants"]]
        entry = next((v for v in self.catalogue() if v["id"] == value["model"]), None)
        return [entry["phrase"], *entry["variants"]] if entry else []

    def save(self, source, value):
        updated = {**self.values, source: self.validate(value)}
        self._write(updated, self.resume_esp32)
        self.values = updated

    def save_resume(self, enabled):
        self._write(self.values, bool(enabled))
        self.resume_esp32 = bool(enabled)

    def _write(self, values, resume):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps({**values, "resume_esp32": resume}, ensure_ascii=False), encoding="utf-8")
        temp.replace(self.path)
