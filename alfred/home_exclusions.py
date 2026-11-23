"""Exclusions locales de la domotique, indépendantes du jeton HA."""

import json
import os
import re
import tempfile
from pathlib import Path


class ExclusionError(ValueError):
    pass


class HomeExclusions:
    def __init__(self, directory: Path):
        self.path = directory / "home-exclusions.json"

    @staticmethod
    def validate(entities):
        if not isinstance(entities, list) or len(entities) > 10000:
            raise ExclusionError("Liste d'exclusions invalide.")
        if any(not isinstance(item, str) or not re.fullmatch(r"[a-z_]+\.[a-z0-9_]+", item) for item in entities):
            raise ExclusionError("Identifiant d'entité invalide.")
        return sorted(set(entities))

    def load(self):
        if not self.path.exists():
            return []
        try:
            return self.validate(json.loads(self.path.read_text(encoding="utf-8")))
        except (OSError, ValueError, TypeError) as error:
            raise ExclusionError("Impossible de lire les exclusions domotiques.") from error

    def save(self, entities):
        values = self.validate(entities)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        name = None
        try:
            fd, name = tempfile.mkstemp(prefix="home-exclusions-", suffix=".tmp", dir=self.path.parent)
            with os.fdopen(fd, "w", encoding="utf-8") as output:
                json.dump(values, output, ensure_ascii=False)
                output.flush()
                os.fsync(output.fileno())
            os.replace(name, self.path)
        finally:
            if name and os.path.exists(name):
                os.unlink(name)
        return values
