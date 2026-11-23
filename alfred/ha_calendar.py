"""Accès ciblé aux calendriers HA ; aucun calendrier local de substitution."""
import json
import logging
import re
from datetime import datetime, timedelta
from urllib.parse import urlencode, urlsplit, urlunsplit
from uuid import uuid4

import httpx
from alfred.home_assistant import HomeError
from websockets.sync.client import connect
from websockets.uri import parse_uri

REMINDER_PREFIX = "ALFRED_RAPPEL_V1:"
_ws_logger = logging.getLogger("alfred.calendar.websocket")
_ws_logger.setLevel(logging.WARNING)


def reminder_marker(room):
    if not isinstance(room, str) or not 1 <= len(room.strip()) <= 80 or any(ord(c)<32 for c in room):
        raise HomeError("Précisez une pièce pour ce rappel.")
    return REMINDER_PREFIX + json.dumps({"id":uuid4().hex, "room":room.strip()},ensure_ascii=False,separators=(",", ":"))


def parse_reminder_marker(description):
    if not isinstance(description, str) or not description.startswith(REMINDER_PREFIX):
        return None
    try:
        data = json.loads(description[len(REMINDER_PREFIX):])
        if not isinstance(data, dict) or set(data)!={"id", "room"}:
            return None
        if not isinstance(data["id"], str) or not re.fullmatch(r"[0-9a-f]{32}", data["id"]):
            return None
        if not isinstance(data["room"], str) or not 1 <= len(data["room"].strip()) <= 80 or any(ord(c)<32 for c in data["room"]):
            return None
        return data
    except (ValueError, TypeError):
        return None


class CalendarBindings:
    """Association locale des profils à leurs calendriers, sans inférer l'identité."""
    def __init__(self, directory):
        self.path = directory / "calendar-targets.json"

    def load(self):
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or set(data) != {"personal", "family"} or not isinstance(data["personal"], dict):
                raise ValueError()
            for owner, entity in data["personal"].items():
                if not isinstance(owner, str) or not re.fullmatch(r"[0-9a-f]{32}", owner):
                    raise ValueError()
                if not isinstance(entity, str) or not re.fullmatch(r"calendar\.[a-z0-9_]+", entity):
                    raise ValueError()
            if data["family"] is not None and (not isinstance(data["family"], str) or not re.fullmatch(r"calendar\.[a-z0-9_]+", data["family"])):
                raise ValueError()
            return data
        except (OSError, ValueError, TypeError) as error:
            raise HomeError("Configuration des calendriers Home Assistant indisponible.") from error

    def personal(self, profile_id):
        entity = self.load()["personal"].get(profile_id)
        if not entity:
            raise HomeError("Aucun calendrier personnel associé à ce profil.")
        return entity

    def family(self):
        entity = self.load()["family"]
        if not entity:
            raise HomeError("Le calendrier familial n'est pas encore configuré.")
        return entity


class CalendarClient:
    def __init__(self, home, allowed_entities, websocket_factory=connect):
        if not isinstance(allowed_entities, (set, list, tuple)) or any(
            not isinstance(entity, str) or not re.fullmatch(r"calendar\.[a-z0-9_]+", entity)
            for entity in allowed_entities
        ):
            raise ValueError("Liste de calendriers invalide.")
        self.home = home
        self.allowed = frozenset(allowed_entities)
        self.websocket_factory = websocket_factory

    def _check(self, entity, start, end):
        if entity not in self.allowed:
            raise HomeError("Ce calendrier n'est pas configuré pour cette opération.")
        if not isinstance(start, datetime) or not isinstance(end, datetime) or start.utcoffset() is None or end.utcoffset() is None or not start < end:
            raise HomeError("Précisez des dates valides avec fuseau horaire.")
        if end - start > timedelta(days=366):
            raise HomeError("La période demandée est trop longue.")

    def events(self, entity, start, end):
        self._check(entity, start, end)
        base, token = self.home._endpoint()
        try:
            with self.home.client_factory() as client:
                result = self.home._request(client, token, "POST", base + "/services/calendar/get_events?return_response",
                    {"entity_id": entity, "start_date_time":start.isoformat(), "end_date_time":end.isoformat()})
        except httpx.HTTPError as error:
            raise HomeError("Lecture du calendrier Home Assistant impossible.") from error
        try:
            items = result["service_response"][entity]["events"]
            if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
                raise ValueError()
            return items
        except (KeyError, TypeError, ValueError) as error:
            raise HomeError("Réponse du calendrier Home Assistant illisible.") from error

    def detailed_events(self, entity, start, end):
        """La route calendrier inclut UID et identifiant de récurrence pour cibler une modification."""
        self._check(entity, start, end)
        base, token = self.home._endpoint()
        query = urlencode({"start":start.isoformat(), "end":end.isoformat()})
        try:
            with self.home.client_factory() as client:
                result = self.home._request(client, token, "GET", base + "/calendars/" + entity + "?" + query)
        except httpx.HTTPError as error:
            raise HomeError("Lecture du calendrier Home Assistant impossible.") from error
        if not isinstance(result,list) or any(not isinstance(item,dict) for item in result):
            raise HomeError("Réponse du calendrier Home Assistant illisible.")
        return result

    def _event_command(self, entity, operation, uid, *, event=None, recurrence_id=None):
        if entity not in self.allowed or operation not in ("delete", "update"):
            raise HomeError("Opération ou calendrier non autorisé.")
        if not isinstance(uid,str) or not 1 <= len(uid) <= 512:
            raise HomeError("Identifiant d'événement indisponible.")
        if recurrence_id is not None and (not isinstance(recurrence_id,str) or not 1 <= len(recurrence_id) <= 200):
            raise HomeError("Identifiant de récurrence invalide.")
        if operation == "update" and not isinstance(event,dict):
            raise HomeError("Modification invalide.")
        base, token = self.home._endpoint()
        parsed=urlsplit(base)
        uri=urlunsplit(("wss" if parsed.scheme=="https" else "ws",parsed.netloc,parsed.path.rstrip("/")+"/websocket","",""))
        command={"id":1,"type":"calendar/event/"+operation,"entity_id":entity,"uid":uid}
        if recurrence_id is not None: command["recurrence_id"]=recurrence_id
        if event is not None: command["event"]=event
        sent=False
        try:
            with self.websocket_factory(uri,open_timeout=5,close_timeout=2,proxy=None,max_size=262144,logger=_ws_logger) as ws:
                if ws.protocol.uri != parse_uri(uri): raise HomeError("Redirection Home Assistant refusée.")
                if json.loads(ws.recv(timeout=10)).get("type") != "auth_required": raise HomeError("Authentification Home Assistant inattendue.")
                ws.send(json.dumps({"type":"auth","access_token":token}))
                if json.loads(ws.recv(timeout=10)).get("type") != "auth_ok": raise HomeError("Jeton Home Assistant refusé ou sans droit suffisant.")
                sent=True
                ws.send(json.dumps(command,ensure_ascii=False))
                response=json.loads(ws.recv(timeout=10))
                if response.get("id")!=1 or response.get("type")!="result": raise ValueError()
                if response.get("success") is not True: raise HomeError("Home Assistant a refusé la modification de l'événement.")
        except HomeError:
            raise
        except Exception as error:
            if sent: raise HomeError("Modification non confirmée : vérifiez le calendrier avant de réessayer.") from error
            raise HomeError("Connexion au calendrier Home Assistant impossible.") from error

    def create(self, entity, title, start, end, *, recurrence=None):
        self._check(entity, start, end)
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 160 or any(ord(c)<32 for c in title):
            raise HomeError("Précisez un intitulé valide.")
        if recurrence is not None:
            raise HomeError("La création d'événements récurrents dans ce calendrier reste à raccorder.")
        base, token = self.home._endpoint()
        try:
            with self.home.client_factory() as client:
                self.home._request(client, token, "POST", base + "/services/calendar/create_event",
                    {"entity_id":entity, "summary":title.strip(), "start_date_time":start.isoformat(), "end_date_time":end.isoformat()})
        except httpx.HTTPError as error:
            raise HomeError("Création non confirmée : consultez le calendrier avant de réessayer.") from error
        return "Création demandée à Home Assistant."

    def create_reminder(self, entity, title, start, room, *, recurrence="once"):
        if not isinstance(start, datetime) or start.utcoffset() is None:
            raise HomeError("Précisez une date et une heure avec fuseau horaire.")
        end = start + timedelta(minutes=1)
        self._check(entity, start, end)
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 160 or any(ord(c)<32 for c in title):
            raise HomeError("Précisez un intitulé valide.")
        if recurrence not in ("once", "weekly"):
            raise HomeError("Cette récurrence n'est pas prise en charge.")
        marker = reminder_marker(room)
        base, token = self.home._endpoint()
        parsed = urlsplit(base)
        uri = urlunsplit(("wss" if parsed.scheme == "https" else "ws", parsed.netloc,
                          parsed.path.rstrip("/") + "/websocket", "", ""))
        event = {"summary":title.strip(), "dtstart":start.isoformat(), "dtend":end.isoformat(), "description":marker}
        if recurrence == "weekly":
            event["rrule"] = "FREQ=WEEKLY"
        sent = False
        try:
            with self.websocket_factory(uri, open_timeout=5, close_timeout=2, proxy=None,
                                        max_size=262144, logger=_ws_logger) as ws:
                if ws.protocol.uri != parse_uri(uri):
                    raise HomeError("Redirection Home Assistant refusée.")
                hello = json.loads(ws.recv(timeout=10))
                if hello.get("type") != "auth_required":
                    raise HomeError("Authentification Home Assistant inattendue.")
                ws.send(json.dumps({"type":"auth", "access_token":token}))
                auth = json.loads(ws.recv(timeout=10))
                if auth.get("type") != "auth_ok":
                    raise HomeError("Jeton Home Assistant refusé ou sans droit suffisant.")
                sent = True
                ws.send(json.dumps({"id":1,"type":"calendar/event/create","entity_id":entity,"event":event},ensure_ascii=False))
                result = json.loads(ws.recv(timeout=10))
                if result.get("id") != 1 or result.get("type") != "result":
                    raise ValueError()
                if result.get("success") is not True:
                    raise HomeError("Home Assistant a refusé la création du rappel.")
        except HomeError:
            raise
        except Exception as error:
            if sent:
                raise HomeError("Création non confirmée : consultez le calendrier avant de réessayer.") from error
            raise HomeError("Connexion au calendrier Home Assistant impossible.") from error
        return "Rappel enregistré dans le calendrier Home Assistant."
