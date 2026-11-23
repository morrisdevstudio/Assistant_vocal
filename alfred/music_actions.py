"""Intentions musicales bornées et vérifiées sur le lecteur explicitement choisi."""
import math
import threading
import time
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from alfred.home_assistant import HomeError, normalize
from alfred.home_catalog import HomeCatalog, capabilities
from alfred.tts_text import prepare_tts_text


VOLUME_STEP = 5


class MusicAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation: Literal["play_default", "play", "resume", "pause", "stop", "next", "previous", "read", "volume", "volume_delta", "mute", "unmute"]
    query: str = Field(default="", max_length=160)
    media_type: Literal["artist", "album", "track", "playlist", "radio"] = "artist"
    artist: str = Field(default="", max_length=80)
    value: int | None = None
    scope: Literal["target", "reference"] = "target"

    @model_validator(mode="after")
    def valid_payload(self):
        if self.operation == "volume" and self.value is not None and not 0 <= self.value <= 100:
            raise ValueError("Volume hors limites")
        if self.operation == "volume_delta" and self.value is not None and (not -100 <= self.value <= 100 or not self.value):
            raise ValueError("Variation hors limites")
        if self.operation == "play" and not self.query.strip():
            raise ValueError("Recherche musicale vide")
        return self


class MusicPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    actions: list[MusicAction] = Field(min_length=1, max_length=4)


class MusicActions:
    def __init__(self, home, music):
        self.home, self.music = home, music

    def player(self):
        player = self.music.player()
        if player != "media_player.amp_salon_2":
            raise HomeError("Le lecteur musical sélectionné n'est pas l'ampli du salon. Aucune autre cible ne sera substituée.")
        try:
            source = getattr(self.home, "catalog", None)
            catalog = (source() if callable(source) else HomeCatalog(self.home)).snapshot()
            item = next((x for x in catalog["entities"] if x["entity_id"] == player), None)
            excluded = set(catalog.get("excluded", []))
        except Exception as error:
            raise HomeError("Impossible de vérifier le lecteur musical autorisé.") from error
        if item is None or not item.get("allowed") or player in excluded:
            raise HomeError("L'ampli du salon n'est pas autorisé dans Alfred. Aucune commande musicale envoyée.")
        state = self.home.get_state(player)
        if not isinstance(state, dict) or state.get("entity_id") != player:
            raise HomeError("L'état de l'ampli du salon est indisponible.")
        available = capabilities("media_player", state.get("attributes") or {})
        return player, state, available

    def prepare(self, actions):
        player, state, available = self.player()
        attributes = state.get("attributes") or {}
        volume = attributes.get("volume_level")
        self.music.note_normal_volume(player, volume)
        active_duck = getattr(self.music, "_active_duck", None)
        ducking = bool(active_duck and active_duck.get("player") == player)
        payloads = []
        for action in actions:
            if action.scope == "reference":
                raise HomeError("Précisez la commande musicale à reprendre.")
            service, payload, required = "music_assistant", {"entity_id": player}, "media_play"
            op = action.operation
            if op == "play_default":
                default = self.music.default_playlist()
                if not default:
                    raise HomeError("Aucune playlist par défaut n'est définie dans le panneau Musique.")
                payload.update({"media_id": default["uri"], "media_type": "playlist", "enqueue": "play"})
            elif op == "play":
                query = action.query.strip()
                if not 1 <= len(query) <= 160 or any(ord(c) < 32 for c in query):
                    raise HomeError("Précisez un artiste, album, titre, radio ou playlist.")
                payload.update({"media_id": query, "media_type": action.media_type, "enqueue": "play"})
                if action.artist:
                    payload["artist"] = action.artist
            elif op in {"resume", "pause", "stop", "next", "previous", "read"}:
                service = "media_player"
                service_name = {"resume": "media_play", "pause": "media_pause", "stop": "media_stop",
                                "next": "media_next_track", "previous": "media_previous_track", "read": "read"}[op]
                required = {"resume": "media_play", "pause": "media_pause", "stop": "media_stop",
                            "next": "media_next_track", "previous": "media_previous_track", "read": "read"}[op]
                if service_name != "read":
                    payloads.append((service, service_name, payload, required))
                else:
                    payloads.append((service, "read", payload, "read"))
                continue
            elif op in {"volume", "volume_delta", "mute", "unmute"}:
                service = "media_player"
                if op in {"mute", "unmute"}:
                    payloads.append((service, "volume_mute", {"entity_id": player, "is_volume_muted": op == "mute"}, "volume_mute"))
                    continue
                if isinstance(action.value, bool) or not isinstance(action.value, int):
                    raise HomeError("Précisez un volume entier.")
                if not isinstance(volume, (int, float)) or isinstance(volume, bool) or not math.isfinite(volume):
                    raise HomeError("Le volume actuel de l'ampli est indisponible.")
                # Ne jamais démarrer la lecture ni modifier le son d'un lecteur arrêté ou muet.
                if op == "volume_delta" and state.get("state") in {"off", "idle", "standby"} and not ducking:
                    raise HomeError("L'ampli du salon est arrêté. Allumez une lecture avant de régler le volume.")
                if op == "volume_delta" and attributes.get("is_volume_muted") and not ducking:
                    raise HomeError("Le son est coupé. Rétablissez-le avant de régler le volume.")
                normal_volume = self.music.normal_volume(player, volume)
                if op == "volume_delta":
                    if not -100 <= action.value <= 100 or not action.value:
                        raise HomeError("Précisez une variation de volume valide.")
                    target = max(0, min(100, round(normal_volume * 100) + action.value))
                else:
                    if not 0 <= action.value <= 100:
                        raise HomeError("Le volume doit être compris entre zéro et cent pour cent.")
                    target = action.value
                payloads.append((service, "volume_set", {"entity_id": player, "volume_level": target / 100}, "volume_set"))
                payload.setdefault("volume_pct", target)
                continue
            payloads.append((service, "play_media", payload, required))
        return player, state, available, payloads

    def execute(self, actions, cancelled=None):
        cancelled = cancelled or threading.Event()
        results = []
        try:
            player, state, available, payloads = self.prepare(actions)
            for domain, service, payload, required in payloads:
                if required != "read" and required not in available:
                    raise HomeError("Cette commande n'est pas disponible sur l'ampli du salon.")
            for domain, service, payload, required in payloads:
                if cancelled.is_set():
                    return self.result("partial" if results else "cancelled", results, "Demande interrompue ; les commandes déjà envoyées ne sont pas annulées.")
                if service == "volume_set":
                    self.music.update_duck_reference(player, payload["volume_level"])
                if domain == "music_assistant" and service == "play_media":
                    default = self.music.default_playlist() or {}
                    dispatch_only = payload.get("media_id") != default.get("uri")
                    if dispatch_only:
                        self.home.call_service(domain, service, payload)
                        results.append({"action_id": uuid4().hex, "intent": actions[len(results)].model_dump(),
                                        "targets": [player], "status": "unconfirmed", "sent": 1})
                        return self.result("unconfirmed", results, "Commande musicale envoyée ; résultat non encore confirmé.")
                sent = 0
                try:
                    if service == "read":
                        if results:
                            state = self.home.get_state(player)
                            if not isinstance(state, dict) or state.get("entity_id") != player:
                                raise HomeError("Je n’ai pas pu vérifier ce qui passe en ce moment.")
                        confirmed = True
                    else:
                        sent = 1
                        self.home.call_service(domain, service, payload)
                        confirmed = self.confirm(player, service, payload)
                except Exception:
                    results.append({"action_id": uuid4().hex, "intent": actions[len(results)].model_dump(), "targets": [player], "status": "unconfirmed", "sent": sent})
                    return self.result("unconfirmed", results, "Commande envoyée ou possiblement appliquée ; résultat non confirmé. La suite est arrêtée, sans répétition.")
                results.append({"action_id": uuid4().hex, "intent": actions[len(results)].model_dump(), "targets": [player], "status": "confirmed" if confirmed else "unconfirmed", "sent": sent})
                if service == "volume_set":
                    self.music.note_normal_volume(player, payload["volume_level"])
                if not confirmed:
                    return self.result("partial" if len(results) > 1 else "unconfirmed", results, "Commande envoyée ; le résultat n'est pas encore confirmé. La suite est arrêtée.")
            return self.result("confirmed", results, self.reply(actions[-1].operation, state))
        except HomeError as error:
            return self.result("partial" if results else "refused", results, str(error))
        except Exception:
            return self.result("partial" if results else "refused", results,
                               "Vérification musicale impossible ; aucune nouvelle commande envoyée.")

    def confirm(self, player, service, payload):
        if service == "play_media":
            # Pour une playlist par défaut, l'état playing prouve qu'elle a été
            # reçue ; une recherche de piste reste seulement envoyée.
            default = self.music.default_playlist() or {}
            if payload.get("media_id") != default.get("uri"):
                return False
            expected = {"playing"}
        elif service == "read":
            return True
        else:
            expected = {"media_play": {"playing"}, "media_pause": {"paused"}, "media_stop": {"idle", "off"}}.get(service)
        deadline = time.monotonic() + 1.5
        while True:
            try:
                state = self.home.get_state(player)
                attrs = state.get("attributes") or {}
                if service == "volume_set" and isinstance(attrs.get("volume_level"), (int, float)) and abs(float(attrs["volume_level"]) - payload["volume_level"]) <= .015:
                    return True
                if service == "volume_mute" and attrs.get("is_volume_muted") == payload["is_volume_muted"]:
                    return True
                if expected and state.get("state") in expected:
                    return True
            except Exception:
                pass
            if time.monotonic() >= deadline:
                return False
            time.sleep(.08)

    @staticmethod
    def reply(operation, state):
        if operation == "read":
            playback = state.get("state")
            if playback in {"off", "idle", "standby", "on"}:
                return "Aucun morceau n’est en cours de lecture."
            if playback not in {"playing", "paused"}:
                return "Je n’ai pas pu vérifier ce qui passe en ce moment."
            attrs = state.get("attributes") or {}
            title, artist = (value.strip() if isinstance(value, str) else ""
                             for value in (attrs.get("media_title"), attrs.get("media_artist")))
            if not title:
                return "Le titre du morceau est indisponible."
            song = f"« {title} »" + (f", de {artist}" if artist else "")
            return f"{song} est en pause." if playback == "paused" else f"Tu écoutes {song}."
        labels = {"play_default": "Playlist par défaut lancée.", "play": "Lecture demandée.", "resume": "Lecture reprise.",
                  "pause": "Musique en pause.", "stop": "Musique arrêtée.", "next": "Passage au morceau suivant demandé.",
                  "previous": "Passage au morceau précédent demandé.", "read": "État musical lu.", "volume": "Volume réglé.",
                  "volume_delta": "Volume ajusté.", "mute": "Son coupé.", "unmute": "Son rétabli."}
        return labels[operation]

    @staticmethod
    def result(status, actions, reply):
        return {"status": status, "actions": actions, "reply": prepare_tts_text(reply)}
