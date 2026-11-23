"""Sonneries de minuteur sur des satellites ESPHome configurés explicitement.

Un journal local précède l'appel réseau : une réponse perdue n'entraîne jamais
de second démarrage, et une sonnerie peut être arrêtée après un redémarrage.
"""

import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path

from alfred.credentials import ConfigurationError
from alfred.home_assistant import HomeBusy, HomeError

logger = logging.getLogger("alfred")
SERVICE = re.compile(r"^[a-z0-9_]+_start_ringing$")
MAX_RING_SECONDS = 15 * 60  # délai de sécurité du firmware v2.0.0
STOP_RETRY_SECONDS = 5


def read_targets(path: Path):
    if not path.exists():
        return []
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(config, dict) or set(config) != {"targets"} or not isinstance(config["targets"], list):
            raise ValueError()
        if len(config["targets"]) > 32:
            raise ValueError()
        targets, names = [], set()
        for item in config["targets"]:
            if not isinstance(item, dict) or set(item) != {"floor_id", "start_service"}:
                raise ValueError()
            floor, name = item["floor_id"], item["start_service"]
            if floor not in ("rdc", "etage1") or not isinstance(name, str) or not SERVICE.fullmatch(name) or name in names:
                raise ValueError()
            names.add(name)
            targets.append({"floor_id": floor, "start_service": name,
                            "stop_service": name.removesuffix("_start_ringing") + "_stop_ringing"})
        return targets
    except (ValueError, OSError, TypeError) as error:
        raise ValueError("Configuration des sonneries invalide.") from error


class BellController:
    def __init__(self, store, home, targets, clock=time.time):
        self.store, self.home, self.targets, self.clock = store, home, targets, clock
        self.errors = {}
        self.next_stop_attempt = {}

    def initialize(self):
        with self.store.connection() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS bell_dispatch (
                start_service TEXT PRIMARY KEY, floor_id TEXT NOT NULL,
                stop_service TEXT NOT NULL, phase TEXT NOT NULL, started_at REAL NOT NULL
            )""")

    def _journal(self):
        with self.store.connection() as db:
            return [dict(row) for row in db.execute("SELECT * FROM bell_dispatch").fetchall()]

    def _clear(self, service):
        with self.store.connection() as db:
            db.execute("DELETE FROM bell_dispatch WHERE start_service=?", (service,))
        self.errors.pop(service, None)
        self.next_stop_attempt.pop(service, None)

    def _stop(self, entry, now):
        service = entry["start_service"]
        if now - entry["started_at"] >= MAX_RING_SECONDS:
            # Le firmware coupe lui-même sa sonnerie après 15 minutes. Ne pas
            # interrompre une sonnerie HA ultérieure après une longue panne.
            self._clear(service)
            return
        if now < self.next_stop_attempt.get(service, 0):
            return
        try:
            self.home.ring_action(entry["stop_service"])
        except (HomeError, HomeBusy, ConfigurationError):
            self.errors[service] = "Arrêt de la sonnerie non confirmé par Home Assistant."
            self.next_stop_attempt[service] = now + STOP_RETRY_SECONDS
        else:
            self._clear(service)

    def sync(self, stop_all=False):
        """Appelé par un seul worker ; aucun appel réseau sur le thread de l'ordonnanceur."""
        now = self.clock()
        existing = {entry["start_service"]: entry for entry in self._journal()}
        configured = {target["start_service"]: target for target in self.targets}
        ringing_items = {floor: [item for item in self.store.active_timers(floor) if item["status"] == "ringing"]
                         for floor in ("rdc", "etage1")}
        ringing = {floor: bool(items) for floor, items in ringing_items.items()}
        for service, entry in list(existing.items()):
            if stop_all or service not in configured or not ringing.get(entry["floor_id"], False):
                self._stop(entry, now)
            elif (now - entry["started_at"] >= MAX_RING_SECONDS and any(
                    datetime.fromisoformat(item["due_at"]).timestamp() > entry["started_at"] + MAX_RING_SECONDS
                    for item in ringing_items[entry["floor_id"]])):
                # Une nouvelle échéance après la coupure automatique de la carte
                # doit sonner, sans redéclencher l'ancienne en boucle.
                self._clear(service)
                del existing[service]
        if stop_all:
            return
        for service, target in configured.items():
            if service in existing or not ringing[target["floor_id"]]:
                continue
            # Écrire AVANT l'action pour pouvoir la terminer même après un crash.
            with self.store.connection() as db:
                db.execute("INSERT INTO bell_dispatch VALUES (?, ?, ?, 'attempted', ?)",
                           (service, target["floor_id"], target["stop_service"], now))
            try:
                self.home.ring_action(service)
            except (HomeError, HomeBusy, ConfigurationError):
                # Un délai réseau peut masquer un succès : ne jamais relancer.
                self.errors[service] = "Démarrage de la sonnerie non confirmé par Home Assistant."
                logger.warning("Démarrage de sonnerie non confirmé pour %s", service)
            else:
                with self.store.connection() as db:
                    db.execute("UPDATE bell_dispatch SET phase='sent' WHERE start_service=?", (service,))
                self.errors.pop(service, None)

    def status(self):
        entries = {item["start_service"]: item for item in self._journal()}
        return {"targets": [{"floor_id": target["floor_id"], "error": self.errors.get(target["start_service"])}
                            | {"phase": ("expired" if target["start_service"] in entries and
                                          self.clock() - entries[target["start_service"]]["started_at"] >= MAX_RING_SECONDS
                                          else entries.get(target["start_service"], {}).get("phase"))}
                            for target in self.targets]}


class TerminalBellController:
    """Sonnerie native d'un terminal direct, sans passer par Home Assistant."""

    def __init__(self, store, terminal, floor_id, clock=time.monotonic):
        self.store, self.terminal, self.floor_id, self.clock = store, terminal, floor_id, clock
        self.error = None
        self.next_retry = 0.

    async def sync(self, stop_all=False):
        """Une seule commande par changement d'état ; nouvel essai après échec."""
        if getattr(self.terminal, "bell_test", False):
            return
        desired = (not stop_all and any(item["status"] == "ringing"
                   for item in self.store.active_timers(self.floor_id)))
        if desired == bool(getattr(self.terminal, "bell_active", False)):
            self.error = None
            return
        if self.clock() < self.next_retry:
            return
        try:
            await self.terminal.set_bell(desired)
        except Exception:
            # La commande peut avoir abouti malgré une réponse perdue ; la
            # reprise est sans danger car les deux actions sont idempotentes.
            self.error = "Sonnerie non confirmée par le terminal."
            self.next_retry = self.clock() + 2
        else:
            self.error = None
            self.next_retry = 0.

    def status(self):
        return {"active": bool(getattr(self.terminal, "bell_active", False)),
                "floor_id": self.floor_id, "error": self.error}
