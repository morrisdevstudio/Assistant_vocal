"""Réglages de confirmation des entités et demandes en attente."""

import json
import os
import re
import tempfile
import threading
import time
from pathlib import Path


class ConfirmationError(ValueError):
    pass


class HomeConfirmations:
    """Entités pour lesquelles toute commande modificatrice exige un accord."""

    def __init__(self, directory: Path):
        self.path = directory / "home-confirmations.json"

    @staticmethod
    def validate(entities):
        if not isinstance(entities, list) or len(entities) > 10000:
            raise ConfirmationError("Liste de confirmations invalide.")
        if any(not isinstance(item, str) or not re.fullmatch(r"[a-z_]+\.[a-z0-9_]+", item)
               for item in entities):
            raise ConfirmationError("Identifiant d'entité invalide.")
        return sorted(set(entities))

    def load(self):
        if not self.path.exists():
            return []
        try:
            return self.validate(json.loads(self.path.read_text(encoding="utf-8")))
        except (OSError, ValueError, TypeError) as error:
            raise ConfirmationError("Impossible de lire les confirmations domotiques.") from error

    def save(self, entities):
        values = self.validate(entities)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        name = None
        try:
            fd, name = tempfile.mkstemp(prefix="home-confirmations-", suffix=".tmp",
                                        dir=self.path.parent)
            with os.fdopen(fd, "w", encoding="utf-8") as output:
                json.dump(values, output, ensure_ascii=False)
                output.flush()
                os.fsync(output.fileno())
            os.replace(name, self.path)
        finally:
            if name and os.path.exists(name):
                os.unlink(name)
        return values


class PendingConfirmations:
    """Une confirmation en mémoire par source et session, pendant trente secondes."""

    def __init__(self, clock=time.monotonic, ttl=30):
        self.clock = clock
        self.ttl = ttl
        self._lock = threading.Lock()
        self._items = {}

    def propose(self, key, payload, question):
        record = {"expires": self.clock() + self.ttl, "payload": payload,
                  "question": question}
        with self._lock:
            now = self.clock()
            for old_key, old in list(self._items.items()):
                if old["expires"] <= now:
                    self._items.pop(old_key, None)
            if key not in self._items and len(self._items) >= 128:
                self._items.pop(next(iter(self._items)), None)
            self._items[key] = record
        return record

    def peek(self, key):
        with self._lock:
            record = self._items.get(key)
            if record is None:
                return None
            if record["expires"] <= self.clock():
                self._items.pop(key, None)
                return None
            return record

    def discard(self, key):
        with self._lock:
            self._items.pop(key, None)

    def clear_session(self, session_id):
        with self._lock:
            for key in list(self._items):
                if isinstance(key, tuple) and len(key) > 1 and key[1] == session_id:
                    self._items.pop(key, None)


YES_WORDS = {"oui", "ouais", "oui merci", "oui vas-y", "vas-y", "d'accord", "ok",
             "confirme", "je confirme", "oui je confirme", "valide"}
NO_WORDS = {"non", "non merci", "annule", "annuler", "laisse tomber", "oublie"}


def confirmation_question(action, names):
    """Question courte et déterministe, sans identifiant technique."""
    values = []
    for name in names or []:
        if not isinstance(name, str):
            continue
        value = name.strip()[:80]
        if value and value not in values:
            values.append(value)
    if not values:
        return ""
    if action in {"turn_on", "turn_off"} and len(values) == 1:
        verb = "allumer" if action == "turn_on" else "éteindre"
        return f"Voulez-vous vraiment {verb} {values[0]} ?"
    if len(values) == 1:
        return f"Voulez-vous vraiment appliquer cette commande à {values[0]} ?"
    shown = ", ".join(values[:3])
    if len(values) > 3:
        shown += f" et {len(values) - 3} autres"
    return f"Voulez-vous vraiment appliquer cette commande ? Elle touche {shown}."
