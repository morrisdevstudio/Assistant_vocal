"""Alias locaux attribués aux entités Home Assistant."""
import json
import os
import re
import tempfile


class AliasError(ValueError):
    pass


class HomeAliases:
    def __init__(self, directory):
        self.path = directory / "home-aliases.json"

    def validate(self, value):
        if not isinstance(value, dict) or len(value) > 10000:
            raise AliasError("Liste d'alias invalide.")
        result = {}
        for entity, names in value.items():
            if not isinstance(entity, str) or not re.fullmatch(r"[a-z_]+\.[a-z0-9_]+", entity) or not isinstance(names, list) or len(names) > 20:
                raise AliasError("Entité ou liste d'alias invalide.")
            if any(not isinstance(name, str) or not name.strip() or len(name) > 80 or any(ord(c) < 32 for c in name) or ',' in name for name in names):
                raise AliasError("Chaque alias doit contenir entre 1 et 80 caractères, sans virgule.")
            cleaned = list(dict.fromkeys(name.strip() for name in names))
            if cleaned:
                result[entity] = cleaned
        return result

    def load(self):
        if not self.path.exists(): return {}
        try:
            return self.validate(json.loads(self.path.read_text(encoding="utf-8")))
        except (ValueError, OSError, TypeError) as error:
            raise AliasError("Impossible de lire les alias domotiques.") from error

    def save(self, value):
        values = self.validate(value)
        write_names(self.path, values)
        return values


def write_names(path, values):
    path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        fd, name = tempfile.mkstemp(prefix=path.stem + "-", suffix=".tmp", dir=path.parent)
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            json.dump(values, output, ensure_ascii=False)
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


class HomeLabels:
    def __init__(self, directory, filename):
        self.path = directory / filename

    @staticmethod
    def validate_name(name):
        if not isinstance(name, str) or any(ord(char) < 32 for char in name) or len(name.strip()) > 80:
            raise ValueError("Indiquez un nom sur une seule ligne, de 80 caractères maximum.")
        return name.strip()

    def load(self):
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return self.validate_labels(data)
        except FileNotFoundError:
            return {}
        except (OSError, ValueError) as error:
            raise ValueError("Impossible de lire les réglages personnalisés des appareils.") from error

    @classmethod
    def validate_labels(cls, data):
        if not isinstance(data, dict):
            raise ValueError("Format invalide.")
        return {entity: cls.validate_name(name) for entity, name in data.items()}

    def set_label(self, entity, name):
        name = self.validate_name(name)
        names = self.load()
        if name:
            names[entity] = name
        else:
            names.pop(entity, None)
        write_names(self.path, names)
        return name


def entity_target_names(item):
    return tuple(dict.fromkeys(name for name in (
        item.get("name"), item.get("ha_name"), item["entity_id"],
        *item.get("aliases", []), *item.get("ha_aliases", []),
    ) if name))
