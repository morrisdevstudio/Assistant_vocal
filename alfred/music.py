"""Lecture musicale Music Assistant sur le lecteur configuré ou choisi dans la PWA."""

import hashlib
import json
import os
import re
import tempfile
import threading
import time
from pathlib import Path

from alfred.home_assistant import HomeError, normalize


PLAYER_PATTERN = r"media_player\.[a-z0-9_]+"
MEDIA_TYPES = ("artist", "album", "track", "playlist", "radio")
DUCK_DEFAULT_PERCENT = 25
DUCK_MIN_VOLUME = 0.03
DUCK_TIMEOUT_SECONDS = 90
CONTROL_SERVICES = {
    "pause": ("media_pause", "pause"),
    "resume": ("media_play", "reprise"),
    "stop": ("media_stop", "arrêt"),
    "next": ("media_next_track", "morceau suivant"),
    "previous": ("media_previous_track", "morceau précédent"),
    "volume_up": ("volume_up", "volume augmenté"),
    "volume_down": ("volume_down", "volume baissé"),
}
CONTROL_MESSAGES = {
    "pause": "Pause demandée",
    "resume": "Reprise demandée",
    "stop": "Arrêt demandé",
    "next": "Morceau suivant demandé",
    "previous": "Morceau précédent demandé",
    "volume_up": "Hausse du volume demandée",
    "volume_down": "Baisse du volume demandée",
}

POLITE = re.compile(r"(?:\s*,?\s*(?:s'il te plaît|s'il vous plaît|stp|svp|merci))?\s*$", re.I)
WAKE_PREFIX = re.compile(r"^(?:(?:hey|he|eh|euh|et|alors)\s*,?\s*)?(?:alfred|alexa|jarvis(?:se)?)\s*,?\s*", re.I)
PLAY = re.compile(
    r"^(?:(?:hey|he|hé|eh|euh|et|alors)\s*,?\s*)?(?:(?:alfred|alexa|jarvis(?:se)?)[,\s]+)?(?:mets(?:-moi)?|joue|lance|écoute)\s+"
    r"(?:(l'album|la chanson|le morceau|le titre|l'artiste)\s+)?"
    r"(?:de la musique\s+(?:de\s+|d'))?"
    r"(?P<query>.+?)\s+sur\s+(?:l'ampli|ampli|le salon|la chaîne|la chaine|music assistant)"
    r"(?:\s+du\s+salon)?\s*$", re.I)
TYPE_WORDS = {
    "l'album": "album", "la chanson": "track", "le morceau": "track",
    "le titre": "track", "l'artiste": "artist",
}


class MusicCommand:
    def __init__(self, action, query=None, media_type=None):
        self.action = action
        self.query = query
        self.media_type = media_type


def parse_music_command(text):
    """Reconnaît une commande musicale complète et simple."""
    if not isinstance(text, str):
        return None
    value = POLITE.sub("", text.strip()).strip(" ,.!?")
    if not value or len(value) > 180:
        return None
    match = PLAY.fullmatch(value)
    if match:
        query = match.group("query").strip(" ,.!?")
        # Les réglages ciblés relèvent de la domotique, pas d'une recherche d'artiste.
        from alfred.home_devices import parse_device
        targeted = parse_device(WAKE_PREFIX.sub("", normalize(value)))
        if targeted and targeted[0] in {"volume_set", "select_source", "set_fan_speed", "device_pause"}:
            return None
        qualifier = match.group(1)
        if (not 1 <= len(query) <= 160 or any(ord(char) < 32 for char in query)
                or normalize(query) == "de la musique"):
            return None
        media_type = TYPE_WORDS.get(qualifier.lower(), "artist") if qualifier else "artist"
        return MusicCommand("play", query, media_type)

    compact = normalize(value)
    compact = WAKE_PREFIX.sub("", compact).strip(" ,.!?")
    controls = [
        (r"(?:mets?|mettre)?\s*(?:la musique\s+)?en pause|pause(?: la musique)?", "pause"),
        (r"(?:reprends|reprend|relance|remets|resume)(?: la musique)?", "resume"),
        (r"(?:arrete|arreter|coupe|couper|stop) (?:la musique|la lecture)", "stop"),
        (r"(?:passe au |joue le |mets le )?(?:morceau|titre|musique) suivante?", "next"),
        (r"(?:reviens au |passe au |joue le |mets le )?(?:morceau|titre|musique) precedent", "previous"),
    ]
    for pattern, action in controls:
        if re.fullmatch(pattern, compact):
            return MusicCommand(action)
    return None


class Music:
    """Sélection locale et commandes vers Music Assistant via Home Assistant."""

    def __init__(self, home, directory: Path):
        self.home = home
        self.path = directory / "music.json"
        self._lock = threading.Lock()
        self._duck_lock = threading.Lock()
        self._active_duck = None
        self._normal_volumes = {}

    def default_playlist(self):
        return self._config().get("default_playlist")

    def normal_volume(self, player, observed=None):
        """Le volume manuel de référence, jamais le volume temporairement atténué."""
        with self._duck_lock:
            current = self._active_duck
            if current and current.get("player") == player:
                return float(current["original_volume"])
        if observed is not None:
            self._normal_volumes[player] = float(observed)
        return self._normal_volumes.get(player, float(observed))

    def note_normal_volume(self, player, value):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            self._normal_volumes[player] = float(value)

    def update_duck_reference(self, player, volume):
        """Un réglage demandé pendant l'atténuation devient la valeur à restaurer."""
        with self._duck_lock:
            if self._active_duck and self._active_duck.get("player") == player:
                self._active_duck["original_volume"] = float(volume)
        self.note_normal_volume(player, volume)

    def _config(self):
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ValueError()
            player = value.get("player_entity_id")
            if not isinstance(player, str) or not re.fullmatch(PLAYER_PATTERN, player):
                raise ValueError()
            percent = value.get("duck_percent", DUCK_DEFAULT_PERCENT)
            if not isinstance(percent, (int, float)) or isinstance(percent, bool) or not 5 <= percent <= 80:
                raise ValueError()
            playlist = value.get("default_playlist")
            if playlist is not None:
                if not isinstance(playlist, dict) or set(playlist) != {"uri", "name", "provider"}:
                    raise ValueError()
                if not all(isinstance(playlist[k], str) and 1 <= len(playlist[k]) <= 500 for k in playlist):
                    raise ValueError()
                playlist = dict(playlist)
            return {"player_entity_id": player, "duck_percent": int(percent),
                    "default_playlist": playlist}
        except FileNotFoundError:
            return {}
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
            raise HomeError("La configuration musicale locale est illisible.") from error

    def _read(self):
        return self._config().get("player_entity_id")

    def player(self):
        player = self._read()
        if not player:
            raise HomeError("Aucun lecteur musical n'est sélectionné dans Alfred.")
        return player

    def configured(self):
        return bool(self._read())

    def configure(self, entity_id, duck_percent=None, default_playlist=None, clear_playlist=False):
        entity_id = entity_id.strip() if isinstance(entity_id, str) else ""
        if not re.fullmatch(PLAYER_PATTERN, entity_id):
            raise HomeError("Identifiant de lecteur musical invalide.")
        state = self.home.get_state(entity_id)
        if not isinstance(state, dict) or state.get("entity_id") != entity_id:
            raise HomeError("Ce lecteur musical est introuvable dans Home Assistant.")
        previous_config = self._config()
        previous = previous_config.get("duck_percent", DUCK_DEFAULT_PERCENT)
        percent = previous if duck_percent is None else duck_percent
        if not isinstance(percent, int) or isinstance(percent, bool) or not 5 <= percent <= 80:
            raise HomeError("Le volume réduit doit être compris entre 5 et 80 %.")
        playlist = None if clear_playlist else previous_config.get("default_playlist") if default_playlist is None else default_playlist
        if playlist is not None:
            if not isinstance(playlist, dict) or set(playlist) != {"uri", "name", "provider"}:
                raise HomeError("Playlist par défaut invalide.")
            if not all(isinstance(playlist[k], str) and 1 <= len(playlist[k]) <= 500 for k in playlist):
                raise HomeError("Playlist par défaut invalide.")
            if not re.match(r"^[a-z][a-z0-9+.-]*://", playlist["uri"]):
                raise HomeError("Référence de playlist Music Assistant invalide.")
        raw = json.dumps({"player_entity_id": entity_id, "duck_percent": percent,
                          "default_playlist": playlist},
                         ensure_ascii=False).encode("utf-8")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        name = None
        try:
            fd, name = tempfile.mkstemp(prefix="music-", suffix=".tmp", dir=self.path.parent)
            with os.fdopen(fd, "wb") as output:
                output.write(raw)
                os.fsync(output.fileno())
            os.replace(name, self.path)
        except OSError as error:
            raise HomeError("Impossible d'enregistrer le lecteur musical.") from error
        finally:
            if name and os.path.exists(name):
                os.unlink(name)
        return self.status()

    def players(self, music_assistant_only=False):
        result = []
        for state in self.home.states("media_player"):
            if not isinstance(state, dict):
                continue
            entity_id = state.get("entity_id")
            if not isinstance(entity_id, str) or not re.fullmatch(PLAYER_PATTERN, entity_id):
                continue
            attributes = state.get("attributes") if isinstance(state.get("attributes"), dict) else {}
            if music_assistant_only and not attributes.get("mass_player_type"):
                continue
            result.append({"entity_id": entity_id,
                           "name": attributes.get("friendly_name") or entity_id,
                           "state": state.get("state")})
        return result

    def _target_state(self, entity_id, default_player):
        if not re.fullmatch(PLAYER_PATTERN, entity_id):
            raise HomeError("Identifiant de lecteur musical invalide.")
        state = self.home.get_state(entity_id)
        if entity_id != default_player and not (state.get("attributes") or {}).get("mass_player_type"):
            raise HomeError("Ce lecteur n'est pas disponible dans Music Assistant.")
        return state

    def _command_player(self, entity_id):
        if entity_id is None:
            return self.player()
        state = self._target_state(entity_id, self._read())
        if state.get("state") in {"unavailable", "unknown"}:
            raise HomeError("Ce lecteur est indisponible.")
        return entity_id

    def status(self, entity_id=None):
        try:
            config = self._config()
        except HomeError as error:
            return {"configured": False, "player_entity_id": None,
                    "configured_player": None, "error": str(error)}
        default_player = config.get("player_entity_id")
        player = entity_id or default_player
        player_name = player
        current = None
        if player:
            try:
                state = self._target_state(player, default_player)
                if isinstance(state, dict):
                    attrs = state.get("attributes") or {}
                    player_name = attrs.get("friendly_name") or player
                    current = {"state": state.get("state"), **{name: attrs.get(name) for name in (
                        "media_title", "media_album_name", "media_artist", "media_duration",
                        "media_position", "media_position_updated_at", "volume_level", "supported_features")}}
                    picture = attrs.get("entity_picture") or attrs.get("entity_picture_local")
                    if isinstance(picture, str) and picture:
                        revision = hashlib.sha256(picture.encode()).hexdigest()[:16]
                        current["artwork_url"] = f"/api/music/artwork?entity_id={player}&v={revision}"
            except Exception:
                current = None
        return {"configured": bool(player), "player_entity_id": player,
                "configured_player": player_name, "current": current,
                "duck_percent": config.get("duck_percent", DUCK_DEFAULT_PERCENT),
                "default_playlist": config.get("default_playlist")}

    def artwork(self, entity_id):
        state = self._target_state(entity_id, self._read())
        attrs = state.get("attributes") or {}
        if attrs.get("entity_picture") or attrs.get("entity_picture_local"):
            return self.home.media_player_image(entity_id)
        return None

    def _config_entry(self):
        """Retrouve l'installation Music Assistant associée au lecteur retenu."""
        player = self.player()
        return self.home.config_entry_id(), player

    def library(self, media_type, query=""):
        entry = self.home.config_entry_id()
        if query:
            result = self.home.call_service_response("music_assistant", "search", {
                "config_entry_id": entry, "media_type": [media_type], "name": query, "limit": 20})
            key = media_type + "s"
        else:
            result = self.home.call_service_response("music_assistant", "get_library", {
                "config_entry_id": entry, "media_type": media_type, "favorite": True, "limit": 50})
            key = "items"
        if isinstance(result, dict) and isinstance(result.get("service_response"), dict):
            result = result["service_response"]
        rows = result.get(key) if isinstance(result, dict) else None
        if not isinstance(rows, list):
            raise HomeError("Réponse de la bibliothèque Music Assistant illisible.")
        items = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            uri, name = row.get("uri"), row.get("name")
            if (isinstance(uri, str) and len(uri) <= 160 and re.match(r"^[a-z][a-z0-9+.-]*://", uri)
                    and isinstance(name, str) and name.strip()):
                items.append({"uri": uri, "name": name})
        return items

    def playlists(self):
        entry, _ = self._config_entry()
        result = self.home.call_service_response("music_assistant", "get_library", {
            "config_entry_id": entry, "media_type": "playlist"})
        if isinstance(result, dict) and isinstance(result.get("service_response"), dict):
            result = result["service_response"]
        rows = result if isinstance(result, list) else result.get("items", result.get("playlists", [])) if isinstance(result, dict) else []
        items = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            uri = row.get("uri")
            name = row.get("name")
            metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
            # Les playlists locales de Music Assistant n'annoncent pas de
            # fournisseur dans get_library ; « Bibliothèque » est explicite et
            # évite de confondre leurs homonymes Qobuz.
            provider = row.get("provider") or row.get("provider_name") or metadata.get("provider")
            if not isinstance(provider, str):
                provider = "Qobuz" if "qobuz" in uri.lower() or "qobuz" in str(row).lower() else "Bibliothèque Music Assistant"
            if isinstance(uri, str) and isinstance(name, str) and isinstance(provider, str):
                items.append({"uri": uri, "name": name, "provider": provider})
        return sorted(items, key=lambda x: (normalize(x["name"]), normalize(x["provider"])))

    def duck(self, session_id):
        """Réduit le volume pendant une interaction navigateur, une seule fois par session."""
        if not isinstance(session_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{16,80}", session_id):
            raise HomeError("Session musicale invalide.")
        with self._duck_lock:
            current = self._active_duck
            if current:
                if current["session_id"] == session_id:
                    return self._duck_result(current, owned=True)
                if time.monotonic() < current["expires_at"]:
                    return {"ducked": True, "owned": False, "reason": "interaction_in_progress"}
                self._restore_active(current, force=False)
            player = self.player()
            state = self.home.get_state(player)
            attributes = state.get("attributes") if isinstance(state, dict) else None
            volume = attributes.get("volume_level") if isinstance(attributes, dict) else None
            if state.get("state") != "playing" or not isinstance(volume, (int, float)) or isinstance(volume, bool):
                return {"ducked": False, "owned": False, "reason": "not_playing"}
            if attributes.get("is_volume_muted"):
                return {"ducked": False, "owned": False, "reason": "muted"}
            percent = self._config().get("duck_percent", DUCK_DEFAULT_PERCENT)
            target = max(DUCK_MIN_VOLUME, min(1.0, float(volume) * percent / 100))
            if target >= float(volume) - 0.005:
                return {"ducked": False, "owned": False, "reason": "already_low"}
            self.note_normal_volume(player, volume)
            self.home.call_service("media_player", "volume_set", {
                "entity_id": player, "volume_level": round(target, 3)})
            confirmed = self._confirm_volume(player, target)
            current = {"session_id": session_id, "player": player,
                       "original_volume": float(volume), "duck_volume": round(target, 3),
                       "expires_at": time.monotonic() + DUCK_TIMEOUT_SECONDS}
            self._active_duck = current
            return self._duck_result(current, owned=True, confirmed=confirmed)

    def restore(self, session_id):
        """Rétablit le volume initial si personne ne l'a modifié entre-temps."""
        if not isinstance(session_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{16,80}", session_id):
            raise HomeError("Session musicale invalide.")
        with self._duck_lock:
            current = self._active_duck
            if not current:
                return {"ducked": False, "restored": False, "reason": "not_active"}
            if current["session_id"] != session_id:
                return {"ducked": True, "restored": False, "reason": "other_interaction"}
            return self._restore_active(current, force=False)

    def expire_duck(self):
        """Filet de sécurité lorsqu'un onglet disparaît avant de demander la restitution."""
        with self._duck_lock:
            current = self._active_duck
            if not current or time.monotonic() < current["expires_at"]:
                return None
            try:
                return self._restore_active(current, force=False)
            except HomeError:
                return {"ducked": True, "restored": False, "reason": "home_assistant_unavailable"}

    def _restore_active(self, current, force):
        state = self.home.get_state(current["player"])
        attributes = state.get("attributes") if isinstance(state, dict) else {}
        volume = attributes.get("volume_level")
        muted = bool(attributes.get("is_volume_muted"))
        changed = (not isinstance(volume, (int, float)) or isinstance(volume, bool)
                   or abs(float(volume) - current["duck_volume"]) > 0.015)
        if not force and (changed or muted):
            self._active_duck = None
            return {"ducked": False, "restored": False, "reason": "manual_change"}
        self.home.call_service("media_player", "volume_set", {
            "entity_id": current["player"], "volume_level": current["original_volume"]})
        confirmed = self._confirm_volume(current["player"], current["original_volume"])
        if not confirmed:
            return {"ducked": True, "restored": False, "reason": "unconfirmed"}
        self._active_duck = None
        return {"ducked": False, "restored": True,
                "volume_level": current["original_volume"], "confirmed": True}

    @staticmethod
    def _duck_result(current, owned, confirmed=True):
        return {"ducked": True, "owned": owned,
                "volume_level": current["duck_volume"], "confirmed": confirmed}

    def _confirm_volume(self, player, expected):
        deadline = time.monotonic() + 1.5
        while True:
            state = self.home.get_state(player)
            volume = (state.get("attributes") or {}).get("volume_level")
            if (isinstance(volume, (int, float)) and not isinstance(volume, bool)
                    and abs(float(volume) - expected) <= 0.015):
                return True
            if time.monotonic() >= deadline:
                return False
            time.sleep(0.08)

    def play(self, query, media_type="artist", artist=None, entity_id=None):
        if not isinstance(query, str) or not 1 <= len(query.strip()) <= 160 or any(ord(c) < 32 for c in query):
            raise HomeError("Précisez un artiste, un album ou un titre valide.")
        if media_type not in MEDIA_TYPES:
            raise HomeError("Type de musique non pris en charge.")
        if artist is not None and (not isinstance(artist, str) or not 1 <= len(artist.strip()) <= 80):
            raise HomeError("Nom d'artiste invalide.")
        player = self._command_player(entity_id)
        if not self._lock.acquire(blocking=False):
            raise HomeError("Une commande musicale est déjà en cours.")
        try:
            payload = {"entity_id": player, "media_id": query.strip(),
                       "media_type": media_type, "enqueue": "play"}
            if artist:
                payload["artist"] = artist.strip()
            self.home.call_service("music_assistant", "play_media", payload)
        finally:
            self._lock.release()
        return {"message": f"Lecture de « {query.strip()} » demandée sur {self._player_name(player)}.",
                "player_entity_id": player, "media_query": query.strip(), "media_type": media_type}

    def control(self, action, entity_id=None):
        if action not in CONTROL_SERVICES:
            raise HomeError("Commande musicale non reconnue.")
        player = self._command_player(entity_id)
        service, _ = CONTROL_SERVICES[action]
        if not self._lock.acquire(blocking=False):
            raise HomeError("Une commande musicale est déjà en cours.")
        try:
            self.home.call_service("media_player", service, {"entity_id": player})
        finally:
            self._lock.release()
        return {"message": f"{CONTROL_MESSAGES[action]} à {self._player_name(player)}.",
                "player_entity_id": player, "control": action}

    def seek(self, action, position, entity_id=None):
        if action != "seek" or position is None:
            raise HomeError("Précisez une position valide.")
        player = self._command_player(entity_id)
        if not self._lock.acquire(blocking=False):
            raise HomeError("Une commande musicale est déjà en cours.")
        try:
            self.home.call_service("media_player", "media_seek", {"entity_id": player, "seek_position": position})
        finally:
            self._lock.release()
        return {"message": "Déplacement demandé.", "player_entity_id": player, "control": action}

    def _player_name(self, player):
        try:
            state = self.home.get_state(player)
            return (state.get("attributes") or {}).get("friendly_name") or player
        except Exception:
            return player

    def handle(self, text):
        command = parse_music_command(text)
        if command is None:
            return None
        try:
            if command.action == "play":
                result = self.play(command.query, command.media_type)
            else:
                result = self.control(command.action)
            return {"matched": True, **result}
        except HomeError as error:
            return {"matched": True, "reply": None, "error": str(error), "action": command.action}


def music_reply(result):
    return result.get("message") or result.get("error") or "La commande musicale n'a pas pu être exécutée."
