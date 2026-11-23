"""Diffusion explicite vers les satellites Alfred déclarés dans la configuration."""
import json
import re
from pathlib import Path

import httpx

from alfred.home_assistant import HomeError, normalize


class Announcements:
    def __init__(self, home, directory: Path):
        self.home = home
        self.path = directory / "announcement-targets.json"

    def targets(self):
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            targets = data["targets"]
            if not isinstance(targets, list) or len(targets) > 32:
                raise ValueError()
            seen = set()
            for target in targets:
                if not isinstance(target, dict) or set(target) != {"entity_id", "room", "floor"}:
                    raise ValueError()
                entity, room, floor = target["entity_id"], target["room"], target["floor"]
                if not isinstance(entity, str) or not re.fullmatch(r"assist_satellite\.[a-z0-9_]+", entity) or entity in seen:
                    raise ValueError()
                if not isinstance(room, str) or not room.strip() or len(room) > 80 or floor not in ("rdc", "etage1"):
                    raise ValueError()
                seen.add(entity)
            return targets
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise HomeError("Aucun terminal d'annonce Alfred configuré correctement.") from error

    def select(self, scope, target=None):
        targets = self.targets()
        if scope == "house":
            chosen = targets
        elif scope == "floor" and target in ("rdc", "etage1"):
            chosen = [item for item in targets if item["floor"] == target]
        elif scope == "room" and isinstance(target, str) and target.strip():
            chosen = [item for item in targets if normalize(item["room"]) == normalize(target)]
        else:
            raise HomeError("Précisez une destination d'annonce valide.")
        if not chosen:
            raise HomeError("Aucun terminal Alfred configuré pour cette destination.")
        return chosen

    def send(self, message, scope="house", target=None, cancelled=None):
        if not isinstance(message, str) or not 1 <= len(message.strip()) <= 300 or any(ord(c) < 32 for c in message):
            raise HomeError("Précisez un message d'annonce valide.")
        chosen = self.select(scope, target)
        try:
            mode = json.loads(self.path.read_text(encoding="utf-8")).get("delivery_mode", "disabled")
        except (OSError, ValueError, AttributeError) as error:
            raise HomeError("Configuration des annonces illisible.") from error
        if mode != "ha_pipeline":
            raise HomeError("La diffusion n'est pas encore activée : choisissez d'abord la voix du terminal.")
        base, token = self.home._endpoint()
        sent = []
        try:
            with self.home.client_factory() as client:
                for item in chosen:
                    if cancelled is not None and cancelled.is_set():
                        return {"accepted": sent, "incomplete": True}
                    try:
                        self.home._request(client, token, "POST", base + "/services/assist_satellite/announce",
                                           {"entity_id": item["entity_id"], "message": message.strip(), "preannounce": False})
                    except (HomeError, httpx.HTTPError):
                        return {"accepted": sent, "incomplete": True}
                    sent.append(item["room"])
        except httpx.HTTPError as error:
            raise HomeError("Connexion à Home Assistant impossible.") from error
        return {"accepted": sent, "incomplete": False}


def announce_reply(result):
    count = len(result["accepted"])
    if result["incomplete"]:
        return f"Annonce non confirmée pour tous les terminaux ; {count} demande(s) acceptée(s)."
    return f"Annonce demandée sur {count} terminal{'s' if count != 1 else ''}."
