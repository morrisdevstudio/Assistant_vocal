"""Intentions de lumière bornées ; préparation complète avant tout envoi."""
from dataclasses import dataclass
from typing import Literal
import math
import threading
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from alfred.home_assistant import HomeError, normalize
from alfred.home_catalog import HomeCatalog
from alfred.home_aliases import entity_target_names
from alfred.home_confirmations import confirmation_question
from alfred.home_settings import effective_light_types
from alfred.light_trace import mark, measure
from alfred.tts_text import prepare_tts_text


class LightAction(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    operation: Literal["turn_on", "turn_off", "read", "brightness", "brightness_delta", "color", "temperature"]
    scope: Literal["current", "room", "entity", "all", "reference"] = Field(
        default_factory=lambda data: "all" if data["operation"] == "read" else "current")
    target: str = Field(default="", max_length=160)
    value: int | str | None = None
    exclude_rooms: list[str] = Field(default_factory=list, max_length=30)
    exclude_entities: list[str] = Field(default_factory=list, max_length=50)
    category: Literal["main", "ambient", "all"] | None = None


class LightPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    actions: list[LightAction] = Field(min_length=1, max_length=4)
    # Une proposition prépare les cibles mais n'envoie aucune commande.
    propose: bool = False
    question: str = Field(default="", max_length=240)


COLORS = {"rouge": [255, 0, 0], "vert": [0, 255, 0], "verte": [0, 255, 0],
          "bleu": [0, 0, 255], "bleue": [0, 0, 255], "jaune": [255, 255, 0],
          "orange": [255, 165, 0], "violet": [128, 0, 255], "violette": [128, 0, 255],
          "rose": [255, 80, 160], "blanc": [255, 255, 255], "blanche": [255, 255, 255]}


def light_capabilities(attrs):
    modes = set(attrs.get("supported_color_modes") or [])
    actions = ["turn_on", "turn_off", "read"]
    if modes - {"onoff", "unknown"}:
        actions += ["brightness", "brightness_delta"]
    if modes & {"hs", "xy", "rgb", "rgbw", "rgbww"}:
        actions += ["color"]
    if "color_temp" in modes:
        actions += ["temperature"]
    return actions


def bare(value):
    import re
    return re.sub(r"^(?:la |le |les |l')", "", normalize(value)).strip()


@dataclass
class Prepared:
    action: LightAction
    targets: list[str]
    states: dict
    payloads: list[tuple[str, dict]]
    confirmation_names: list[str]


class LightActions:
    def __init__(self, home):
        self.home = home

    def catalog(self):
        catalog = getattr(self.home, "catalog", None)
        source = catalog() if callable(catalog) else HomeCatalog(self.home)
        return source.control_snapshot()

    def resolve(self, action, catalog):
        entries = {x["entity_id"]: x for x in catalog["entities"] if x["entity_id"].startswith("light.")}
        # Résoudre les racines dans les seules entités exposées. Les membres
        # masqués ne sont consultés qu'en descendant depuis l'une de ces racines.
        descendants = {**catalog.get("light_group_members", {}), **entries}
        excluded = set(catalog.get("excluded", []))
        room = None
        if action.scope == "reference":
            raise HomeError("Précisez la lumière à reprendre.")
        if action.scope in {"current", "room"}:
            room = self.home.room() if action.scope == "current" else action.target
            if not room:
                raise HomeError("Dans quelle pièce ?")
            roots = [e for e, x in entries.items() if bare(x.get("area")) == bare(room)]
            # Compatibilité des anciens catalogues ne portant pas encore les pièces.
            if not roots and entries and all("area" not in x for x in entries.values()):
                base, token = self.home._endpoint()
                with self.home.client_factory() as client:
                    roots = self.home._area_lights(client, token, base, room)
        elif action.scope == "all":
            roots = list(entries)
        else:
            wanted = bare(action.target)
            roots = [e for e, x in entries.items() if any(bare(n) == wanted for n in entity_target_names(x))]
            if len(roots) > 1:
                raise HomeError("Plusieurs lumières correspondent. Précisez le nom ou la pièce.")
        def leaves(entity, seen, room):
            item = descendants.get(entity)
            if entity in seen or entity in excluded or not item or not item.get("allowed"):
                raise HomeError("Cette lumière ou un membre de son groupe n'est pas autorisé.")
            members = item.get("members")
            if members is not None and (not isinstance(members, list) or not members):
                raise HomeError("Les membres de ce groupe sont indisponibles.")
            targets = [entity] if members is None else [
                leaf for member in members for leaf in leaves(member, seen | {entity}, room)]
            if room and item.get("alfred_area") and bare(item["area"]) != bare(room):
                return []
            return targets
        targets = []
        for root in roots:
            try:
                targets.extend(leaves(root, set(), room))
            except HomeError:
                if action.scope == "entity":
                    raise
                # Ne jamais adresser un groupe qui contourne une exclusion.
                continue
        targets = sorted(set(targets))
        if not targets:
            raise HomeError("Aucune lumière autorisée ne correspond à cette demande.")
        # Retirer les feuilles, y compris celles atteintes par un groupe situé
        # ailleurs. Ne jamais envoyer une commande globale au groupe HA.
        protected = set()
        for excluded_room in action.exclude_rooms:
            matches = [e for e, item in descendants.items() if bare(item.get("area")) == bare(excluded_room)]
            if not excluded_room.strip() or not matches:
                raise HomeError("Une pièce à préserver est inconnue. Précisez son nom ; aucune commande envoyée.")
            for entity in matches:
                protected.add(entity)
                protected.update(leaves(entity, set(), excluded_room))
        for entity in action.exclude_entities:
            # Les exclusions utilisent les mêmes noms et alias que les cibles.
            protected.update(self.resolve(LightAction(operation="read", scope="entity", target=entity), catalog))
        targets = [entity for entity in targets if entity not in protected]
        category = action.category
        if category is None and action.operation == "turn_on" and action.scope in {"current", "room", "all"}:
            category = "main"
        if category in {"main", "ambient"}:
            desired = "secondary" if category == "ambient" else "main"
            types = effective_light_types(targets, descendants)
            targets = [entity for entity in targets if types[entity] == desired]
            if not targets:
                label = "principale" if category == "main" else "d’ambiance"
                raise HomeError(f"Aucune lumière {label} autorisée ne correspond à cette demande.")
        return targets

    def state(self, entity, *, reading=False):
        with measure("state_read"):
            value = self.home.get_state(entity)
        if (not isinstance(value, dict) or value.get("entity_id") != entity
                or not isinstance(value.get("state"), str)
                or (not reading and value["state"] not in {"on", "off"})):
            raise HomeError("L'état d'une lumière est indisponible ; aucune commande envoyée.")
        # Les feuilles ne doivent pas être devenues des groupes depuis le catalogue.
        if value.get("attributes", {}).get("entity_id"):
            raise HomeError("Ce groupe a changé ; précisez à nouveau les lumières.")
        return value

    def prepare(self, action, catalog):
        targets = self.resolve(action, catalog)
        states = {e: self.state(e, reading=action.operation == "read") for e in targets}
        entries = {x["entity_id"]: x for x in catalog["entities"]}
        labels = {**catalog.get("light_group_members", {}), **entries}
        confirmation_names = []
        for entity in targets:
            if (labels.get(entity) or {}).get("confirmation_required"):
                confirmation_names.append((labels.get(entity) or {}).get("name")
                                          or (states[entity].get("attributes") or {}).get("friendly_name")
                                          or entity)
        payloads = []
        for e, state in states.items():
            attrs = state.get("attributes") or {}
            if action.operation not in light_capabilities(attrs):
                raise HomeError("Toutes les lampes visées ne permettent pas ce réglage. Précisez les lampes compatibles.")
            value, op = action.value, action.operation
            data = {"entity_id": [e]}
            service = "turn_on"
            if op in {"turn_on", "turn_off", "read"}:
                if value is not None:
                    raise HomeError("Ce réglage ne nécessite pas de valeur.")
                service = op
                if op == "read" or state["state"] == ("on" if op == "turn_on" else "off"):
                    continue
            elif op in {"brightness", "brightness_delta", "temperature"}:
                if isinstance(value, bool) or not isinstance(value, int):
                    raise HomeError("Précisez une valeur entière.")
                if op == "temperature":
                    low, high = attrs.get("min_color_temp_kelvin"), attrs.get("max_color_temp_kelvin")
                    if not isinstance(low, (int, float)) or not isinstance(high, (int, float)) or not low <= value <= high:
                        raise HomeError("Cette température de blanc dépasse les limites de la lampe.")
                    data["color_temp_kelvin"] = value
                else:
                    if op == "brightness_delta":
                        if not -100 <= value <= 100 or not value:
                            raise HomeError("Précisez une variation entre moins cent et cent points.")
                        if state["state"] == "off" and value < 0:
                            continue
                        brightness = attrs.get("brightness")
                        if not isinstance(brightness, (int, float)) or not math.isfinite(brightness):
                            raise HomeError("La luminosité actuelle est inconnue.")
                        value = max(1, min(100, round(brightness * 100 / 255) + value))
                    elif not 0 <= value <= 100:
                        raise HomeError("La luminosité doit être comprise entre zéro et cent pour cent.")
                    if value == 0:
                        service = "turn_off"
                    else:
                        data["brightness_pct"] = value
            elif op == "color":
                color = COLORS.get(normalize(value)) if isinstance(value, str) else None
                if color is None:
                    raise HomeError("Précisez une couleur usuelle, par exemple rouge, bleu ou blanc.")
                data["rgb_color"] = color
            payloads.append((service, data))
        return Prepared(action, targets, states, payloads,
                        list(dict.fromkeys(confirmation_names)))

    @staticmethod
    def read_reply(states, catalog):
        if not states:
            return "Il ne reste aucune lumière à vérifier dans ce périmètre."
        labels = {**catalog.get("light_group_members", {}),
                  **{item["entity_id"]: item for item in catalog["entities"]}}
        names = [(labels.get(entity) or {}).get("name")
                 or (state.get("attributes") or {}).get("friendly_name")
                 or entity.split(".", 1)[1].replace("_", " ")
                 for entity, state in states.items() if state["state"] == "on"]
        unknown = any(state["state"] not in {"on", "off"} for state in states.values())
        if names:
            lights = ", ".join(names[:-1]) + " et " + names[-1] if len(names) > 1 else names[0]
            reply = (f"Les lumières encore allumées sont {lights}." if len(names) > 1
                     else f"Il reste une lumière allumée, {lights}.")
            if unknown:
                reply += " L'état de certaines lumières reste indisponible."
            return reply
        if unknown:
            return "Je ne peux pas confirmer que toutes les lumières sont éteintes. Certains états sont indisponibles."
        return "Toutes les lumières sont éteintes."

    @staticmethod
    def confirmed(state, service, data):
        if state.get("state") != ("off" if service == "turn_off" else "on"):
            return False
        attrs = state.get("attributes") or {}
        if "brightness_pct" in data:
            v = attrs.get("brightness")
            if not isinstance(v, (int, float)) or not math.isfinite(v) or abs(v * 100 / 255 - data["brightness_pct"]) > 3:
                return False
        if "color_temp_kelvin" in data:
            v = attrs.get("color_temp_kelvin")
            if not isinstance(v, (int, float)) or not math.isfinite(v) or abs(v - data["color_temp_kelvin"]) > 100:
                return False
        if "rgb_color" in data:
            actual = attrs.get("rgb_color")
            if not isinstance(actual, (list, tuple)) or len(actual) != 3 or any(not isinstance(a, (int, float)) or not math.isfinite(a) or abs(a-b) > 10 for a, b in zip(actual, data["rgb_color"])):
                return False
        return True

    def execute(self, actions, cancelled=None, expected_targets=None, approved=False):
        cancelled = cancelled or threading.Event()
        results = []
        with measure("home_lock"):
            self.home._acquire()
        try:
            catalog = self.catalog()
            plans = [self.prepare(action, catalog) for action in actions]
            if expected_targets is not None and [p.targets for p in plans] != expected_targets:
                raise HomeError("Les cibles ont changé depuis la proposition. Précisez à nouveau la demande.")
            if not approved:
                names = list(dict.fromkeys(name for plan in plans if plan.payloads
                                           for name in plan.confirmation_names))
                action_name = (actions[0].operation
                               if len(actions) == 1 and len(plans[0].targets) == 1
                               and actions[0].operation in {"turn_on", "turn_off"}
                               else None)
                question = confirmation_question(action_name, names)
                if question:
                    self.home.pending.propose(
                        self.home.confirmation_key(),
                        {"kind": "lights", "actions": [a.model_dump() for a in actions],
                         "expected_targets": [p.targets for p in plans]},
                        question)
                    return {**self.result("confirmation", [], question),
                            "confirmation": True}
            for index, plan in enumerate(plans):
                if cancelled.is_set():
                    return self.result("partial" if results else "cancelled", results, "Demande interrompue. Les commandes déjà envoyées ne sont pas annulées.")
                # Revérification des droits, groupes et états juste avant chaque action.
                live_catalog = self.catalog()
                live = self.prepare(plan.action, live_catalog)
                if live.targets != plan.targets:
                    raise HomeError("Les cibles ont changé ; suite interrompue.")
                sent, confirmed = 0, True
                try:
                    for service, data in live.payloads:
                        if cancelled.is_set():
                            return self.result("partial" if results or sent else "cancelled", results, "Demande interrompue ; vérifiez les commandes déjà envoyées.")
                        sent += 1  # Même un timeout peut avoir suivi l'application réelle.
                        self.home.call_service("light", service, data)
                        observed = False
                        # Certaines intégrations publient l'état après la réponse
                        # au service. Attendre brièvement l'état, jamais renvoyer
                        # la commande, notamment au milieu d'un groupe.
                        for delay in (0, .1, .2, .4, .6, .7):
                            if cancelled.is_set() or delay and cancelled.wait(delay):
                                break
                            try:
                                with measure("confirmation_read"):
                                    after = self.home.get_state(data["entity_id"][0])
                                observed = isinstance(after, dict) and self.confirmed(after, service, data)
                            except Exception:
                                observed = False
                            if observed:
                                mark("state_confirmed", target=data["entity_id"][0], state=after["state"])
                                break
                        confirmed &= observed
                        if not confirmed:
                            break
                except Exception:
                    results.append({"action_id": uuid4().hex, "intent": plan.action.model_dump(), "targets": live.targets, "status": "unconfirmed", "sent": sent})
                    return self.result("partial" if index else "unconfirmed", results, "Commande envoyée ou possiblement appliquée ; résultat non confirmé. La suite est arrêtée, sans répétition.")
                results.append({"action_id": uuid4().hex, "intent": plan.action.model_dump(), "targets": live.targets, "status": "confirmed" if confirmed else "unconfirmed", "sent": sent})
                if not confirmed:
                    return self.result("partial" if index or cancelled.is_set() else "unconfirmed", results, "Commande envoyée ; résultat non confirmé. La suite est arrêtée, sans répétition.")
                if plan.action.operation == "read":
                    reply = self.read_reply(live.states, live_catalog)
                elif not live.payloads:
                    reply = "Les lumières sont déjà dans l'état demandé."
                else:
                    label = f"dans la pièce « {plan.action.target} »" if plan.action.scope == "room" else ""
                    word = {"turn_on": "allumée", "turn_off": "éteinte"}.get(plan.action.operation, "réglée")
                    n = len(live.payloads)
                    reply = f"{n} lumière{'s' if n > 1 else ''} {word}{'s' if n > 1 else ''} {label}."
                results[-1]["reply"] = reply
            return self.result("confirmed", results, " ".join(r["reply"] for r in results))
        except Exception as error:
            from alfred.home_catalog import CatalogError
            detail = str(error) if isinstance(error, (HomeError, CatalogError)) else "Vérification des lumières impossible."
            if results:
                detail += " La suite est arrêtée ; les commandes déjà envoyées ne sont pas répétées."
            return self.result("partial" if results else "refused", results, detail)
        finally:
            self.home._lock.release()

    @staticmethod
    def result(status, actions, reply):
        return {"status": status, "actions": actions, "reply": prepare_tts_text(reply)}
