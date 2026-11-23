"""Commandes de lumière Home Assistant, jeton local et intentions françaises bornées."""

import json
import os
import re
import tempfile
import threading
import time
import unicodedata
from contextlib import contextmanager, nullcontext
from contextvars import ContextVar
from http.cookiejar import CookieJar, DefaultCookiePolicy
from pathlib import Path
from alfred.tts_text import numbers_to_words
from alfred.home_aliases import entity_target_names
from alfred.light_trace import mark

import httpx

from alfred.credentials import ConfigurationError, windows_crypt
from alfred.home_confirmations import (PendingConfirmations, confirmation_question,
                                       YES_WORDS, NO_WORDS)

ACTION_WORDS = {"eteint": False, "eteins": False, "eteindre": False, "coupe": False, "couper": False,
                "allume": True, "allumer": True, "rallume": True}
LIGHT_WORDS = ("lumiere", "lumieres", "lampe", "lampes")
ALL_WORDS = ("toutes", "tous", "toute", "partout")
HOME_ROOM = ContextVar("alfred_home_room", default=None)
# Préfixe parlé du mot d'appel, appliqué à un texte déjà normalisé (sans accents).
# La transcription française peut écrire « hé » ou « et » : accepter les
# variantes évite qu'une commande « Hé Alfred allume la lumière » parte vers l'IA.
WAKE_PREFIX = re.compile(r"^(?:(?:h[ée]y?|hey|eh|euh|et|alors)\s*,?\s*)?(?:alfred|alexa|jarvis(?:se)?)\s*,?\s*", re.I)
ROOM_PATTERN = re.compile(r"(?:du|de la|de l|des|dans le|dans la|dans les|au|aux)\s+([a-z0-9][a-z0-9 '-]{0,60})$")


class HomeError(RuntimeError):
    pass


class HomeBusy(RuntimeError):
    pass


class HomeConfirmationRequired(HomeError):
    """Une écriture attend un accord explicite."""


def normalize(text):
    text = unicodedata.normalize("NFD", text or "")
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return " ".join(text.lower().replace("’", "'").split())


class LightCommand:
    def __init__(self, turn_on, scope, room=None, category=None):
        self.turn_on, self.scope, self.room = turn_on, scope, room
        self.category = category

    def __repr__(self):
        return f"LightCommand(turn_on={self.turn_on}, scope={self.scope}, room={self.room!r})"


# Courtoisie orale : séparateurs souples et confusions STT limitées à cette formule.
COURTESY = r"(?:s[' ’-]?il\s+(?:te|vous|de|le)\s+pl(?:a[iî]t|ais|ai|a[iî]s|ait|a[iî]e)|s\.?t\.?p\.?|s\.?v\.?p\.?|merci(?:\s+beaucoup)?)"
POLITE = re.compile(rf"(?:\s*[,;:]?\s+|^){COURTESY}$", re.I)
REQUEST_PREFIX = (
    r"(?:(?:est[- ]ce que\s+)?(?:peux[- ]tu|pouvez[- ]vous|pourrais[- ]tu|pourriez[- ]vous|"
    r"tu peux|tu pourrais|vous pouvez|vous pourriez|tu veux bien|vous voulez bien)\s+(?:bien\s+)?(?:m'|me\s+)?|"
    r"(?:merci de|je voudrais(?: que tu)?|j'aimerais(?: que tu)?|je veux que tu)\s+)"
)


def clean_home_request(text, preserve_punctuation=False):
    """Nettoie l'enrobage oral ; conserve valeurs, noms et négations sans les deviner."""
    value = text.strip().replace("’", "'")
    value = WAKE_PREFIX.sub("", value)
    tail = re.search(r"[\s,;:.!?…]+$", value)
    tail = tail.group() if tail else ""
    value = value.strip(" ,;:.!?…")
    removed_suffix = False
    # Retirer la ponctuation AVANT la courtoisie, y compris si elle est répétée.
    for _ in range(3):
        previous = value
        trimmed = POLITE.sub("", value)
        removed_suffix |= trimmed != value
        value = trimmed.strip(" ,;:.!?…")
        value = re.sub(rf"^{COURTESY}\s*[,;:]?\s+(?!\s*de\b)", "", value, flags=re.I)
        if value == previous:
            break
    value = WAKE_PREFIX.sub("", value)
    value = re.sub(r"^" + REQUEST_PREFIX, "", value, flags=re.I)
    # « allume-moi la lampe » et « éteins moi la lampe ».
    value = re.sub(r"^(allume|allumer|rallume|eteins|eteint|eteindre|éteins|éteint|éteindre|coupe|couper)[- ]moi\s+",
                   r"\1 ", value, flags=re.I)
    return value.strip(" ,;:.!?…") + (tail if preserve_punctuation and not removed_suffix else "")


INCLUDE_AMBIENT = re.compile(r"\b(?:y compris|incluant|en incluant)\s+(?:les (?:lumieres|lampes) d'|l[' ])?ambiance\b")
ORDER = re.compile(
    rf"(?:{REQUEST_PREFIX}|on\s+)?"
    r"(eteins|eteint|eteindre|coupe|couper|allume|allumer|rallume)\s+"
    r"(tout|toutes(?:\s+les)?|tous(?:\s+les)?|la|le|les|l'|une|un)?\s*"
    r"(lumiere|lumieres|lampe|lampes|eclairage)"
    r"(?:\s+(d'ambiance|secondaires?|principales?))?"
    r"(?:\s+(partout|ici|dans cette piece))?"
    r"(?:\s+(?:du|de la|de l'|des|dans le|dans la|dans les|au|aux)\s+([a-z0-9][a-z0-9 '-]*))?")

ALL_SCOPES = ("tout", "toutes", "toutes les", "tous", "tous les", "partout")


def parse_light_command(text):
    """Accepte uniquement une phrase de lumière complète et simple.

    Une demande plus longue (« et raconte une blague ») n'est pas exécutée ici :
    elle part vers la conversation, qui n'a aucun outil de maison.
    """
    normalized = normalize(clean_home_request(text))
    if not normalized or len(normalized) > 160:
        return None
    include = INCLUDE_AMBIENT.search(normalized)
    include_ambient = include is not None and include.end() == len(normalized)
    if include_ambient:
        normalized = normalized[:include.start()].rstrip(" ,")
    match = ORDER.fullmatch(normalized)
    if not match:
        return None
    action, quantifier, _, kind, place, room = match.groups()
    if include_ambient and kind:
        return None
    category = ("all" if include_ambient else
                "main" if kind and kind.startswith("principale") else
                "ambient" if kind else None)
    if room and re.search(r"\b(?:et|puis|ensuite|mais|sinon|quand)\b", room):
        return None  # Une demande composée doit être comprise avant toute action.
    turn_on = ACTION_WORDS[action]
    if room and room.strip(" '-") in ("maison", "partout"):
        return LightCommand(turn_on, "all", category=category) if not place else None
    if place and room:
        return None  # Ne pas élargir une cible contradictoire à toute la maison.
    if room:
        room = room.strip(" '-")
        if room and "'" not in room and '"' not in room:
            return LightCommand(turn_on, "room", room, category)
        return None
    if place in ("ici", "dans cette piece"):
        return LightCommand(turn_on, "current", category=category)
    if quantifier in ALL_SCOPES or place == "partout":
        return LightCommand(turn_on, "all", category=category)
    return LightCommand(turn_on, "current", category=category)


class HomeStore:
    """Jeton Home Assistant séparé de celui de Command Code, jamais renvoyé à l'interface."""

    def __init__(self, directory: Path, base_url="", token="", room=None):
        self.path = directory / "homeassistant.secret"
        self._env = {"base_url": base_url, "token": token, "room": room}
        self._lock = threading.Lock()

    def _read(self):
        if not self.path.exists():
            return {}
        try:
            raw = self.path.read_bytes()
            if raw.startswith(b"DPAPI\n"):
                if os.name != "nt":
                    raise ConfigurationError("Ce jeton est lié au compte Windows. Reconfigurez-le ici.")
                raw = windows_crypt(raw[6:], decrypt=True)
            elif os.name == "nt":
                raise ConfigurationError("Configuration Home Assistant non protégée.")
            elif self.path.stat().st_mode & 0o077:
                raise ConfigurationError("La configuration Home Assistant doit avoir les permissions 0600.")
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise ValueError()
            return value
        except ConfigurationError:
            raise
        except Exception as error:
            raise ConfigurationError("Impossible de lire la configuration Home Assistant.") from error

    def values(self):
        with self._lock:
            saved = self._read()
        return (self._env["base_url"] or saved.get("base_url", ""),
                self._env["token"] or saved.get("token", ""),
                self._env["room"] or saved.get("room") or "Bureau")

    def public(self):
        base_url, token, room = self.values()
        return {"configured": bool(base_url and token), "base_url": base_url,
                "room": room, "from_environment": bool(self._env["token"]),
                "storage": "Windows DPAPI" if os.name == "nt" else "fichier privé 0600"}

    def save(self, base_url, token, room):
        if self._env["token"]:
            raise ConfigurationError("Le jeton provient de l'environnement. Modifiez-le au lancement.")
        with self._lock:
            previous = self._read() if token is None else {}
            token = token if token is not None else previous.get("token", "")
            if not token:
                raise ConfigurationError("Saisissez un jeton d'accès Home Assistant.")
            raw = json.dumps({"base_url": base_url, "token": token, "room": room}).encode()
            if os.name == "nt":
                raw = b"DPAPI\n" + windows_crypt(raw)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            name = None
            try:
                fd, name = tempfile.mkstemp(prefix="ha-", suffix=".tmp", dir=self.path.parent)
                with os.fdopen(fd, "wb") as output:
                    if os.name != "nt":
                        os.fchmod(output.fileno(), 0o600)
                    output.write(raw)
                    os.fsync(output.fileno())
                os.replace(name, self.path)
            except OSError as error:
                raise ConfigurationError("Impossible d'enregistrer la configuration Home Assistant.") from error
            finally:
                if name and os.path.exists(name):
                    os.unlink(name)
        return self.public()


class HomeService:
    def __init__(self, store: HomeStore, client_factory=None):
        self.store = store
        self.client_factory = client_factory or (lambda: httpx.Client(
            timeout=httpx.Timeout(10, connect=5), trust_env=False, follow_redirects=False))
        self._lock = threading.Lock()
        self._music_entry_lock = threading.Lock()
        self._music_entry = None
        self.verified = False
        self._catalog = None
        self._catalog_lock = threading.Lock()
        self.pending = PendingConfirmations()

    @contextmanager
    def connection_pool(self):
        """Réutilise les connexions pendant la vie du serveur, avec le jeton de chaque requête."""
        standalone_factory = self.client_factory
        cookies = CookieJar(policy=DefaultCookiePolicy(allowed_domains=()))
        with httpx.Client(timeout=httpx.Timeout(10, connect=5), trust_env=False,
                          follow_redirects=False, cookies=cookies,
                          limits=httpx.Limits(max_connections=40, max_keepalive_connections=10,
                                             keepalive_expiry=30)) as client:
            self.client_factory = lambda: nullcontext(client)
            try:
                yield
            finally:
                self.client_factory = standalone_factory

    def confirmation_key(self):
        from alfred.intent_context import CURRENT_TURN
        turn = CURRENT_TURN.get()
        return tuple(turn.key[:2]) if turn is not None else ("direct", "default")

    def confirmation_request(self, text):
        phrase = normalize(clean_home_request(text)).strip(" .!?")
        if not phrase:
            return None
        key = self.confirmation_key()
        record = self.pending.peek(key)
        if record is None:
            return None
        if phrase in YES_WORDS:
            self.pending.discard(key)
            return self._confirmation_turn(self._execute_confirmation(record))
        if phrase in NO_WORDS:
            self.pending.discard(key)
            return self._confirmation_turn({"matched": True, "reply": "D'accord, commande annulée.",
                                            "status": "cancelled", "mode": "home"})
        self.pending.discard(key)
        return None

    @staticmethod
    def _confirmation_turn(result):
        from alfred.intent_context import CURRENT_TURN
        turn = CURRENT_TURN.get()
        if turn is not None:
            turn.result = result
            turn.route = "local"
        return result

    def _execute_confirmation(self, record):
        from alfred.intent_context import CURRENT_TURN
        payload = record.get("payload") or {}
        try:
            if payload.get("kind") == "lights":
                controller = getattr(self, "intent_service", None)
                if controller is None:
                    return {"matched": True, "reply": None, "mode": "home",
                            "error": "Le contrôle des lumières n'est pas disponible."}
                from alfred.light_actions import LightAction
                actions = [LightAction.model_validate(value) for value in payload.get("actions", [])]
                result = controller.execute(actions, turn=CURRENT_TURN.get(),
                                            expected_targets=payload.get("expected_targets"),
                                            approved=True)
                if result.get("status") == "refused":
                    return {"matched": True, "reply": result.get("reply"),
                            "error": result.get("reply"), "status": "refused",
                            "mode": "home"}
                return {"matched": True, "status": result.get("status"),
                        "reply": result.get("reply"), "actions": result.get("actions", []),
                        "mode": "home"}
            if payload.get("kind") == "device":
                from alfred.home_commands import HomeCommands
                result, _ = HomeCommands(self).handle_command(
                    (payload.get("operation"), payload.get("target"), payload.get("value")),
                    approved=True)
                if result is None:
                    return {"matched": True, "reply": None, "mode": "home",
                            "error": "Cette commande n'est plus disponible."}
                return {**result, "mode": "home"}
            if payload.get("kind") == "legacy_light":
                reply = self.execute(LightCommand(payload.get("turn_on"), payload.get("scope"),
                                                  payload.get("room"), payload.get("category")), approved=True)
                return {"matched": True, "reply": reply, "status": "confirmed",
                        "action": "turn_on" if payload.get("turn_on") else "turn_off",
                        "scope": payload.get("scope"), "room": payload.get("room"),
                        "mode": "home"}
        except (HomeError, HomeBusy) as error:
            return {"matched": True, "reply": None, "error": str(error), "mode": "home"}
        return {"matched": True, "reply": None, "mode": "home",
                "error": "Cette confirmation n'est plus valable."}

    def room(self):
        return HOME_ROOM.get() or self.store.values()[2]

    def status(self):
        try:
            public = self.store.public()
        except ConfigurationError:
            return {"configured": False, "configuration_error": True,
                    "verified": False, "room": None, "base_url": None}
        result = {**public, "verified": self.verified}
        if self._catalog is not None:
            result["catalog"] = self._catalog.stats()
        return result

    def _endpoint(self):
        base_url, token, _ = self.store.values()
        if not (base_url and token):
            raise HomeError("Home Assistant n'est pas configuré dans Alfred.")
        return base_url.rstrip("/") + "/api", token

    def catalog(self):
        """Catalogue partagé par les commandes successives de ce service."""
        with self._catalog_lock:
            if self._catalog is None:
                from alfred.home_catalog import HomeCatalog
                self._catalog = HomeCatalog(self)
            return self._catalog

    def _request(self, client, token, method, path, payload=None):
        response = client.request(method, path, json=payload,
                                  headers={"Authorization": "Bearer " + token})
        if response.status_code in (401, 403):
            raise HomeError("Jeton Home Assistant refusé ou sans droit suffisant.")
        if response.status_code == 404:
            raise HomeError("Adresse Home Assistant ou ressource introuvable.")
        if response.status_code >= 400:
            raise HomeError("Home Assistant a refusé la demande.")
        try:
            return response.json()
        except ValueError as error:
            raise HomeError("Réponse Home Assistant illisible.") from error

    def states(self, domain=None):
        """États utiles aux sélecteurs explicites ; aucun secret n'est renvoyé côté client."""
        if domain is not None and not re.fullmatch(r"[a-z_]+", domain):
            raise HomeError("Domaine Home Assistant invalide.")
        base, token = self._endpoint()
        try:
            with self.client_factory() as client:
                states = self._request(client, token, "GET", base + "/states")
        except httpx.HTTPError as error:
            raise HomeError("Connexion à Home Assistant impossible.") from error
        if not isinstance(states, list):
            raise HomeError("Réponse Home Assistant inattendue.")
        if domain is None:
            return states
        return [item for item in states if isinstance(item, dict)
                and str(item.get("entity_id", "")).startswith(domain + ".")]

    def get_state(self, entity_id):
        if not isinstance(entity_id, str) or not re.fullmatch(r"[a-z_]+\.[a-z0-9_]+", entity_id):
            raise HomeError("Identifiant d'entité Home Assistant invalide.")
        base, token = self._endpoint()
        try:
            with self.client_factory() as client:
                return self._request(client, token, "GET", base + "/states/" + entity_id)
        except httpx.HTTPError as error:
            raise HomeError("Connexion à Home Assistant impossible.") from error

    def media_player_image(self, entity_id):
        if not re.fullmatch(r"media_player\.[a-z0-9_]+", entity_id):
            raise HomeError("Identifiant de lecteur musical invalide.")
        base, token = self._endpoint()
        formats = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/avif"}
        try:
            with self.client_factory() as client, client.stream(
                "GET", base + "/media_player_proxy/" + entity_id,
                headers={"Authorization": "Bearer " + token}, follow_redirects=False,
            ) as response:
                content_type = response.headers.get("content-type", "").split(";", 1)[0]
                if response.status_code != 200 or content_type not in formats:
                    return None
                image = bytearray()
                for chunk in response.iter_bytes(chunk_size=65536):
                    image.extend(chunk)
                    if len(image) > 5 * 1024 * 1024:
                        return None
                return (bytes(image), content_type) if image else None
        except httpx.HTTPError as error:
            raise HomeError("Pochette Home Assistant indisponible.") from error

    def config(self):
        base, token = self._endpoint()
        try:
            with self.client_factory() as client:
                value = self._request(client, token, "GET", base + "/config")
        except httpx.HTTPError as error:
            raise HomeError("Connexion à Home Assistant impossible.") from error
        if not isinstance(value, dict) or not isinstance(value.get("time_zone"), str):
            raise HomeError("Le fuseau horaire Home Assistant est indisponible.")
        return value

    def config_entries(self):
        base, token = self._endpoint()
        try:
            with self.client_factory() as client:
                value = self._request(client, token, "GET", base + "/config_entries")
        except httpx.HTTPError as error:
            raise HomeError("Connexion à Home Assistant impossible.") from error
        if not isinstance(value, list):
            raise HomeError("Liste des intégrations Home Assistant illisible.")
        return value

    def integrations(self):
        """Instantané borné des intégrations chargées, sans données d'identifiants."""
        base, token = self._endpoint()
        try:
            with self.client_factory() as client:
                value = self._request(client, token, "GET", base + "/config/core")
        except httpx.HTTPError as error:
            raise HomeError("Connexion à Home Assistant impossible.") from error
        if not isinstance(value, dict) or not isinstance(value.get("integration"), list):
            raise HomeError("Intégrations Home Assistant illisibles.")
        return [x for x in value["integration"] if isinstance(x, dict) and x.get("integration") == "music_assistant"]

    def config_entry_id(self):
        """Réutilise une découverte récente pour le même serveur et le même jeton."""
        with self._music_entry_lock:
            endpoint = self._endpoint()
            cached = self._music_entry
            if cached and cached[0] == endpoint and time.monotonic() < cached[2]:
                return cached[1]
            self._music_entry = None
            entry = self._discover_music_entry(*endpoint)
            self._music_entry = (endpoint, entry, time.monotonic() + 60)
            return entry

    def _discover_music_entry(self, base, token):
        """Installation Music Assistant chargée, lue par WebSocket en lecture seule."""
        import json
        from urllib.parse import urlsplit, urlunsplit
        from websockets.sync.client import connect
        parsed = urlsplit(base)
        uri = urlunsplit(("wss" if parsed.scheme == "https" else "ws", parsed.netloc,
                          parsed.path.rstrip("/") + "/websocket", "", ""))
        try:
            with connect(uri, open_timeout=5, close_timeout=2, proxy=None) as ws:
                if json.loads(ws.recv(timeout=10)).get("type") != "auth_required":
                    raise ValueError()
                ws.send(json.dumps({"type": "auth", "access_token": token}))
                if json.loads(ws.recv(timeout=10)).get("type") != "auth_ok":
                    raise ValueError()
                ws.send(json.dumps({"id": 1, "type": "config_entries/get"}))
                result = json.loads(ws.recv(timeout=20))
        except Exception as error:
            raise HomeError("Installations Home Assistant indisponibles.") from error
        rows = result.get("result") if isinstance(result, dict) and result.get("success") else None
        entries = [x for x in rows if isinstance(x, dict) and x.get("domain") == "music_assistant"
                   and x.get("state") == "loaded" and isinstance(x.get("entry_id"), str)] if isinstance(rows, list) else []
        if len(entries) != 1:
            raise HomeError("Une seule installation Music Assistant chargée est nécessaire.")
        return entries[0]["entry_id"]

    def call_service(self, domain, service, payload):
        if not re.fullmatch(r"[a-z_]+", domain or "") or not re.fullmatch(r"[a-z_]+", service or ""):
            raise HomeError("Action Home Assistant invalide.")
        if not isinstance(payload, dict):
            raise HomeError("Paramètres de l'action Home Assistant invalides.")
        base, token = self._endpoint()
        try:
            with self.client_factory() as client:
                if domain == "light":
                    mark("service_sent", service=service, targets=payload.get("entity_id"))
                result = self._request(client, token, "POST", base + "/services/" + domain + "/" + service, payload)
                if domain == "light":
                    mark("service_acknowledged", service=service, targets=payload.get("entity_id"))
                return result
        except httpx.HTTPError as error:
            raise HomeError("Connexion à Home Assistant impossible.") from error

    def call_service_response(self, domain, service, payload):
        """Lit une réponse native bornée ; l'appelant valide le service."""
        if not re.fullmatch(r"[a-z_]+", domain or "") or not re.fullmatch(r"[a-z_]+", service or ""):
            raise HomeError("Action Home Assistant invalide.")
        if not isinstance(payload, dict):
            raise HomeError("Paramètres de l'action Home Assistant invalides.")
        base, token = self._endpoint()
        try:
            with self.client_factory() as client:
                response = client.post(base + "/services/" + domain + "/" + service + "?return_response", json=payload,
                                       headers={"Authorization": "Bearer " + token})
                if response.status_code in (401, 403):
                    raise HomeError("Jeton Home Assistant refusé ou sans droit suffisant.")
                if response.status_code >= 400:
                    detail = ""
                    try:
                        body = response.json()
                        detail = body.get("message", "") if isinstance(body, dict) else ""
                    except ValueError:
                        pass
                    raise HomeError("Home Assistant a refusé la demande" + (f" : {detail}" if detail else "."))
                return response.json() if response.content else None
        except (HomeError, httpx.HTTPError, ValueError) as error:
            if domain == "music_assistant":
                with self._music_entry_lock:
                    cached = self._music_entry
                    if cached and cached[:2] == ((base, token), payload.get("config_entry_id")):
                        self._music_entry = None
            if isinstance(error, HomeError):
                raise
            if isinstance(error, ValueError):
                raise HomeError("Réponse Home Assistant illisible.") from error
            raise HomeError("Connexion à Home Assistant impossible.") from error

    def _acquire(self):
        if not self._lock.acquire(blocking=False):
            raise HomeBusy("Une commande de maison est déjà en cours.")

    def ring_action(self, service):
        """Action native ESPHome, isolée des commandes de lumière ; sans relecture de jeton."""
        if not re.fullmatch(r"[a-z0-9_]+_(?:start|stop)_ringing", service):
            raise HomeError("Action de sonnerie invalide.")
        base, token = self._endpoint()
        try:
            with self.client_factory() as client:
                self._request(client, token, "POST", base + "/services/esphome/" + service, {})
        except httpx.HTTPError as error:
            raise HomeError("Connexion à Home Assistant impossible.") from error

    def check(self):
        self._acquire()
        try:
            base, token = self._endpoint()
            try:
                with self.client_factory() as client:
                    config = self._request(client, token, "GET", base + "/config")
                    states = self._request(client, token, "GET", base + "/states")
            except httpx.HTTPError as error:
                raise HomeError("Connexion à Home Assistant impossible.") from error
            if not isinstance(config, dict) or not isinstance(states, list):
                raise HomeError("Réponse Home Assistant inattendue.")
            lights = self._only_lights(states)
            self.verified = True
            return {"location_name": config.get("location_name"),
                    "version": config.get("version"), "lights": len(lights),
                    "lights_on": sum(item.get("state") == "on" for item in lights)}
        finally:
            self._lock.release()

    @staticmethod
    def _only_lights(states):
        return [item for item in states if isinstance(item, dict)
                and str(item.get("entity_id", "")).startswith("light.")]

    def _area_lights(self, client, token, base, room):
        safe = re.sub(r"[^\w '-]", "", room, flags=re.UNICODE).strip()
        if not safe or "'" in safe or '"' in safe:
            raise HomeError("Nom de pièce invalide.")
        template = ("{{ area_entities('" + safe + "') | select('match', '^light') "
                    "| list | tojson }}")
        result = self._request(client, token, "POST", base + "/template", {"template": template})
        if not isinstance(result, list):
            raise HomeError("Réponse Home Assistant inattendue pour cette pièce.")
        return [entity for entity in result
                if isinstance(entity, str) and entity.startswith("light.")]

    def execute(self, command, catalog=None, approved=False):
        controller = getattr(self, "intent_service", None)
        if controller is not None:
            return controller.from_legacy(command, catalog, approved=approved)
        self._acquire()
        try:
            from alfred.home_catalog import HomeCatalog, CatalogError
            try:
                catalog = catalog if catalog is not None else self.catalog().snapshot()
            except CatalogError as error:
                raise HomeError(str(error)) from error
            entries = {item["entity_id"]: item for item in catalog["entities"]}
            allowed = {entity for entity, item in entries.items() if item["allowed"]}
            def safe_target(entity, seen=None):
                seen = set() if seen is None else seen
                if entity in seen or entity not in allowed:
                    return False
                seen.add(entity)
                members = entries[entity].get("members")
                if members is None:
                    return True
                return isinstance(members, list) and bool(members) and all(isinstance(m, str) and safe_target(m, seen.copy()) for m in members)
            base, token = self._endpoint()
            try:
                with self.client_factory() as client:
                    classified = any(item.get("light_type") == "secondary" for item in entries.values())
                    if command.category is not None or (classified and command.turn_on and command.scope != "entity"):
                        from alfred.light_actions import LightAction, LightActions
                        targets = LightActions(self).resolve(
                            LightAction(operation="turn_on" if command.turn_on else "turn_off",
                                        scope=command.scope, target=command.room or "", category=command.category), catalog)
                        label = "dans toute la maison" if command.scope == "all" else f"pour « {command.room or self.room()} »"
                    elif command.scope == "entity":
                        matches = [entity for entity, item in entries.items() if item.get("domain") == "light"
                                   and any(normalize(name) == command.room for name in entity_target_names(item))]
                        if len(matches) > 1:
                            raise HomeError("Plusieurs lumières portent cet alias. Précisez un nom distinct dans Domotique.")
                        if not matches:
                            raise HomeError("Cette lumière n'est pas disponible dans le catalogue Assist.")
                        targets = matches
                        label = "pour « " + (entries[matches[0]].get("alfred_name") or command.room) + " »"
                    elif command.scope == "all":
                        lights = self._only_lights(self._request(client, token, "GET", base + "/states"))
                        targets = [item["entity_id"] for item in lights
                                   if command.turn_on or item.get("state") == "on"]
                        label = "dans toute la maison"
                    else:
                        room = command.room if command.scope == "room" else self.room()
                        if any("area" in item for item in entries.values()):
                            from alfred.light_actions import LightAction, LightActions
                            targets = LightActions(self).resolve(
                                LightAction(operation="turn_on" if command.turn_on else "turn_off",
                                            scope="room", target=room), catalog)
                        else:
                            targets = self._area_lights(client, token, base, room)
                        label = "dans la pièce « " + room + " »"
                    targets = [entity for entity in targets if safe_target(entity)]
                    if not targets:
                        if not command.turn_on:
                            return "Aucune lumière autorisée à éteindre."
                        raise HomeError("Aucune lumière trouvée pour " + label + ".")
                    if not approved:
                        names = list(dict.fromkeys(
                            entries.get(entity, {}).get("name") or entity
                            for entity in targets
                            if entries.get(entity, {}).get("confirmation_required")))
                        action_name = (("turn_on" if command.turn_on else "turn_off")
                                       if len(targets) == 1 else None)
                        question = confirmation_question(action_name, names)
                        if question:
                            self.pending.propose(
                                self.confirmation_key(),
                                {"kind": "legacy_light", "turn_on": command.turn_on,
                                 "scope": command.scope, "room": command.room, "category": command.category},
                                question)
                            raise HomeConfirmationRequired(question)
                    service = "turn_on" if command.turn_on else "turn_off"
                    self._request(client, token, "POST", base + "/services/light/" + service,
                                  {"entity_id": targets})
            except httpx.HTTPError as error:
                raise HomeError("Connexion à Home Assistant impossible.") from error
        finally:
            self._lock.release()
        self.verified = True
        count = len(targets)
        noun = "lumière" if count == 1 else "lumières"
        verb = ("allumée" if command.turn_on else "éteinte") + ("s" if count > 1 else "")
        return numbers_to_words(f"{count} {noun} {verb} {label}.")

    def handle(self, text):
        """Commandes directes communes au texte, au navigateur et au terminal ESP32."""
        confirmation = self.confirmation_request(text)
        if confirmation is not None:
            return confirmation
        from alfred.home_commands import HomeCommands
        result, catalog = HomeCommands(self).handle(text)
        if result is not None:
            return result
        command = None
        phrase = normalize(clean_home_request(text))
        match = re.fullmatch(rf"(?:{REQUEST_PREFIX}|on\s+)?(eteins|eteint|eteindre|coupe|couper|allume|allumer|rallume)\s+(.+)", phrase)
        target = match.group(2).strip() if match else ""
        candidates = {target, re.sub(r"^(?:le|la|les|un|une)\s+|^l'", "", target)}
        candidates.update(re.sub(r"^(?:lumiere|lampe|eclairage)\s+(?:de\s+|du\s+|des\s+|d')?", "", value) for value in list(candidates))
        try:
            aliases = self.catalog().settings.load()["aliases"]
        except ValueError as error:
            return {"matched": True, "reply": None, "error": str(error)}
        matches = {normalize(name) for entity, names in aliases.items() if entity.startswith("light.") for name in names if normalize(name) in candidates}
        if match:
            from alfred.home_catalog import HomeCatalog, CatalogError
            try:
                catalog = catalog if catalog is not None else self.catalog().snapshot()
                matches.update(normalize(name) for item in catalog["entities"] if item.get("domain") == "light"
                               for name in entity_target_names(item) if normalize(name) in candidates)
            except (CatalogError, HomeError, ConfigurationError) as error:
                return {"matched": True, "reply": None, "error": str(error)}
        if len(matches) > 1:
            return {"matched": True, "reply": None, "error": "Plusieurs alias correspondent : précisez le nom."}
        if matches and match:
            command = LightCommand(ACTION_WORDS[match.group(1)], "entity", next(iter(matches)))
        if command is None:
            command = parse_light_command(text)
        if command is None:
            return None
        try:
            reply = self.execute(command, catalog)
            result = {"matched": True, "reply": reply,
                      "action": "turn_on" if command.turn_on else "turn_off",
                      "scope": command.scope, "room": command.room}
            if self.pending.peek(self.confirmation_key()) is not None:
                result.update(status="confirmation", confirmation=True)
            return result
        except HomeConfirmationRequired as error:
            return {"matched": True, "reply": str(error), "status": "confirmation",
                    "confirmation": True, "mode": "home",
                    "action": "turn_on" if command.turn_on else "turn_off",
                    "scope": command.scope, "room": command.room}
        except (HomeError, HomeBusy) as error:
            return {"matched": True, "reply": None, "error": str(error),
                    "action": "turn_on" if command.turn_on else "turn_off",
                    "scope": command.scope, "room": command.room}


def command_reply(result):
    """Phrase courte à dire, sans exposer de détail technique."""
    if result.get("reply"):
        return result["reply"]
    return result.get("error") or "La commande n'a pas pu être exécutée."
