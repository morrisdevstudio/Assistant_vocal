"""Intentions domotiques françaises bornées, sans outil générique ni appel IA."""

import re
import math
from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from alfred.home_assistant import HomeError, HomeBusy, normalize, clean_home_request
from alfred.home_catalog import HomeCatalog, CatalogError, capabilities
from alfred.home_aliases import entity_target_names
from alfred.credentials import ConfigurationError
from alfred.timers import number
from alfred.tts_text import numbers_to_words, prepare_tts_text
from alfred.home_devices import (DEVICE_READS, parse_device, generic_target, prepare_device,
                                 read_device, confirmed_device, confirmed_reply)
from alfred.home_confirmations import confirmation_question


MONTHS = "janvier fevrier mars avril mai juin juillet aout septembre octobre novembre decembre".split()
SPOKEN_MONTHS = "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split()
SUPPORTED = {"light", "switch", "sensor", "input_boolean", "input_number", "input_select",
             "input_datetime", "input_text", "input_button", "media_player", "vacuum"}
READ_ONLY_ACTIONS = {"read", "temperature", "options"} | DEVICE_READS


class ReadingClarification(HomeError):
    """Une lecture ne peut pas aboutir, sans panne technique du terminal."""


def bare(text):
    return re.sub(r"^(?:(?:le|la|les|un|une)\s+|l')", "", normalize(text)).strip()


def integer(text):
    text = text.strip().replace("-", " ")
    direct = number(text)
    if direct is not None:
        return direct
    # Cent et mille complètent le parseur partagé des minuteurs.
    for word, scale in (("mille", 1000), ("cent", 100)):
        match = re.fullmatch(r"(?:(.+?) )?" + word + r"s?(?: (.+))?", text)
        if match:
            high = integer(match[1]) if match[1] else 1
            low = integer(match[2]) if match[2] else 0
            if high is not None and low is not None and 0 < high < scale and 0 <= low < scale:
                return high * scale + low
    return None


def numeric(text):
    text = normalize(text)
    if re.fullmatch(r"[+-]?\d+(?:[,.]\d+)?", text):
        return Decimal(text.replace(",", "."))
    sign = -1 if text.startswith("moins ") else 1
    text = text.removeprefix("moins ").removeprefix("plus ")
    parts = text.split(" virgule ")
    whole = integer(parts[0])
    if whole is None or len(parts) > 2:
        raise HomeError("Précisez une valeur numérique valide.")
    value = Decimal(whole)
    if len(parts) == 2:
        fraction = integer(parts[1])
        if fraction is None:
            # « zéro cinq » conserve les zéros initiaux.
            digits = [number(word) for word in parts[1].split()]
            if not digits or any(x is None or x > 9 for x in digits):
                raise HomeError("Précisez les décimales.")
            raw = "".join(str(x) for x in digits)
        else:
            raw = str(fraction)
        value += Decimal("0." + raw)
    return sign * value


def parse_temperature(phrase):
    """Reconnaitre une question de temperature de piece, sans confondre un reglage."""
    patterns = (
        r"(?:quel(?:le)?(?: est)?(?: la)?\s+|la\s+)?temperature(?: (?:fait[- ]il|fait[- ]on|il fait))?(?:\s+(.*))?",
        r"(?:combien (?:fait[- ]il|fait il|il fait)|combien de degres(?: (?:fait[- ]il|fait il|il fait))?)(?:\s+(.*))?",
        r"il fait (?:quelle temperature|combien)(?:\s+(.*))?",
    )
    for pattern in patterns:
        match = re.fullmatch(pattern, phrase)
        if match:
            target = next((value for value in match.groups() if value), "")
            target = target.strip(" .!?")
            # Un reglage de blanc chaud n'est pas une lecture de sonde.
            if re.search(r"\b(?:kelvin|k|couleur|lampes?|lumiere|eclairage)\b", target):
                return None
            return target or "ici"
    return None


def temperature_room(target):
    """Retirer les formules de lieu pour comparer le nom de piece du catalogue."""
    value = normalize(target).strip(" .!?")
    value = re.sub(r"^(?:il fait|fait[- ]il|fait[- ]on|c'est|est-ce)\s+", "", value)
    previous = None
    while value != previous:
        previous = value
        value = re.sub(r"^(?:dans|au|aux|a|de|du|des|sur|pour|chez)\s+", "", value)
        value = re.sub(r"^(?:la|le|les|l')\s*", "", value)
    return value.strip(" .!?")


def parse(text):
    # Les captures de valeur utilisent le texte original : casse et accents préservés.
    raw = clean_home_request(text, preserve_punctuation=True)
    phrase = normalize(raw).strip(" .!?")
    device = parse_device(phrase)
    if device is not None:
        return device
    target = parse_temperature(phrase)
    if target is not None:
        return "temperature", target, None
    patterns = [
        ("turn_on", r"(?:allume|allumer|rallume|active|activer)\s+(.+)"),
        ("turn_off", r"(?:eteins|eteindre|coupe|couper|desactive|desactiver)\s+(.+)"),
        ("read", r"(?:lis|consulte)\s+(?:l'etat de |la valeur de |le choix de |l'heure de |la date de )?(.+)"),
        ("read", r"(?:donne(?:-moi)?|quel est|quelle est)\s+(?:l'etat|la valeur|le choix|l'heure|la date)\s+(?:de l'|de la |du |des |de )(.+)"),
        ("options", r"(?:liste|enumere|quelles sont)\s+(?:les )?(?:options|possibilites)(?: de| du| pour)\s+(.+)"),
        ("increment", r"(?:augmente|incremente)\s+(.+?)(?: d'un pas)?"),
        ("decrement", r"(?:diminue|decremente|baisse)\s+(.+?)(?: d'un pas)?"),
        ("select_next", r"(?:option suivante (?:de|pour)|passe (.+?) a l'option suivante)\s*(.*)"),
        ("select_previous", r"(?:option precedente (?:de|pour)|passe (.+?) a l'option precedente)\s*(.*)"),
        ("press", r"(?:appuie sur|presse|declenche)\s+(.+)"),
    ]
    for action, pattern in patterns:
        match = re.fullmatch(pattern, phrase)
        if match:
            return action, next((x for x in match.groups() if x), ""), None
    match = re.fullmatch(r"(?:mets?|r[eè]gle|fixe|d[eé]finis|modifie|change|[eé]cris)\s+(.+?)\s+(?:à|a|sur|avec)\s+(.+)", raw, re.I)
    if match:
        return "set", normalize(match[1]), match[2]
    # Question fermée : « est-ce que le mode vacances est activé ? »
    match = re.fullmatch(r"(?:est-ce que |est ce que )?(.+?) est (?:active|activee|allume|allumee|desactive|desactivee|eteint|eteinte)", phrase)
    if match:
        return "read", match[1], None
    return None


def matches(item, target):
    candidates = {bare(target)}
    candidates.add(re.sub(r"^(?:lumiere|lampe|eclairage|switch|interrupteur|booleen|selecteur|bouton|aspirateur|robot|lecteur)\s+(?:de |du |d')?", "", bare(target)))
    return generic_target(item, bare(target)) or any(bare(name) in candidates for name in entity_target_names(item))


def resolve(items, target, current_room, temperature=False):
    eligible = items
    if temperature:
        eligible = [item for item in eligible if item.get("domain") == "sensor"
                    and item.get("attributes", {}).get("device_class") == "temperature" and item.get("allowed")]
        room = temperature_room(target)
        room = current_room if room in {"ici", "", "piece", "dans cette piece", "cette piece", "ici meme", "la piece"} else room
        found = [item for item in eligible if normalize(item.get("area")) == normalize(room)]
        if not found:
            # Une piece partielle (« chambre ») doit etre reconnue : plusieurs
            # correspondances declenchent une precision au lieu d'un faux refus.
            found = [item for item in eligible if room and normalize(item.get("area"))
                     and (room in normalize(item.get("area")) or normalize(item.get("area")) in room)]
        if not found:
            found = [item for item in eligible if matches(item, target)]
        if not found and room != normalize(target):
            found = [item for item in eligible if matches(item, room)]
    else:
        found = [item for item in eligible if matches(item, target)]
        if not found:
            # N'enlever une pièce qu'après essai du nom complet (ex. « prise du salon »).
            for item in eligible:
                area = normalize(item.get("area"))
                if not area:
                    continue
                for separator in (" dans le ", " dans la ", " dans l'", " du ", " de la ", " de l'", " au "):
                    suffix = separator + area
                    if target.endswith(suffix) and matches(item, target[:-len(suffix)]):
                        found.append(item)
                        break
    if len(found) > 1:
        if temperature:
            raise ReadingClarification("Plusieurs capteurs correspondent : précisez le nom ou la pièce.")
        raise HomeError("Plusieurs entités correspondent : précisez le nom ou la pièce.")
    return found[0] if found else None


def safe_target(item, entries, seen=None):
    seen = set() if seen is None else seen
    entity = item["entity_id"]
    if entity in seen or not item.get("allowed"):
        return False
    members = item.get("members")
    if members is None:
        return True
    seen = seen | {entity}
    return isinstance(members, list) and bool(members) and all(
        isinstance(member, str) and member in entries and safe_target(entries[member], entries, seen)
        for member in members)


def safe_device_group(item, entries, seen=None):
    """Les groupes multimédias se mentionnent eux-mêmes et peuvent être réciproques."""
    if not safe_target(item, entries):
        return False
    if item.get("domain") != "media_player":
        return True
    seen = set() if seen is None else seen
    if item["entity_id"] in seen:
        return True
    seen = seen | {item["entity_id"]}
    members = item.get("attributes", {}).get("group_members", [])
    return isinstance(members, list) and all(isinstance(member, str) and member in entries
        and safe_device_group(entries[member], entries, seen) for member in members + (item.get("members") or []))


def clock_value(value):
    if value in {"midi", "minuit"}:
        return time(12 if value == "midi" else 0)
    match = re.fullmatch(r"(\d{1,2}):([0-9]{2})(?::([0-9]{2}))?", value)
    if match:
        return time(int(match[1]), int(match[2]), int(match[3] or 0))
    match = re.fullmatch(r"(.+?)\s*(?:heures?|h)(?:\s*(.+))?", value)
    if match:
        hour = integer(match[1])
        tail = match[2] or "zero"
        minute = {"et demie": 30, "et demi": 30, "et quart": 15, "moins le quart": 45}.get(tail)
        if minute is None:
            minute = integer(tail.removesuffix(" minutes").removesuffix(" minute"))
        if hour is not None and minute is not None:
            if tail == "moins le quart":
                hour = (hour - 1) % 24
            return time(hour, minute)
    raise HomeError("Précisez une heure valide, par exemple sept heures trente.")


def date_value(value, today):
    value = value.removeprefix("le ")
    if value in {"aujourd'hui", "demain"}:
        return today + timedelta(days=value == "demain")
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return date.fromisoformat(value)
    match = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", value)
    if match:
        return date(int(match[3]), int(match[2]), int(match[1]))
    match = re.fullmatch(r"(.+?) (" + "|".join(MONTHS) + r")(?: (.+))?", value)
    if match:
        day = 1 if match[1] in {"premier", "1er"} else integer(match[1])
        year = integer(match[3]) if match[3] else today.year
        if day is not None and year is not None:
            return date(year, MONTHS.index(match[2]) + 1, day)
    raise HomeError("Précisez une date valide, par exemple demain ou le quinze novembre.")


def datetime_payload(value, attrs, zone):
    value = normalize(value).strip(" .!?")
    today = datetime.now(zone).date()
    # Le champ demandé peut n'être qu'une moitié d'un helper date et heure.
    parts = re.split(r"\s+a\s+", value, maxsplit=1)
    if len(parts) == 2:
        payload = {"date": date_value(parts[0], today).isoformat(), "time": clock_value(parts[1]).isoformat()}
    else:
        try:
            payload = {"time": clock_value(value).isoformat()}
        except HomeError:
            payload = {"date": date_value(value, today).isoformat()}
    if ("date" in payload and not attrs.get("has_date")) or ("time" in payload and not attrs.get("has_time")):
        raise HomeError("Ce réglage ne possède pas le champ date ou heure demandé.")
    return payload


def numeric_payload(value, attrs):
    unit = normalize(attrs.get("unit_of_measurement", ""))
    raw = normalize(value).strip(" .!?")
    # Une unité n'est acceptée que si elle correspond à celle du helper.
    units = {unit} if unit else set()
    if unit == "°c":
        units |= {"degre", "degres", "degre celsius", "degres celsius"}
    units |= {"min": {"minute", "minutes"}, "s": {"seconde", "secondes"},
              "h": {"heure", "heures"}, "%": {"pour cent", "pourcent"},
              "°f": {"degre fahrenheit", "degres fahrenheit"}}.get(unit, set())
    for suffix in sorted(units, key=len, reverse=True):
        if suffix and raw.endswith(" " + suffix):
            raw = raw[:-len(suffix)].strip()
            break
    amount = numeric(raw)
    try:
        minimum, maximum = Decimal(str(attrs["min"])), Decimal(str(attrs["max"]))
        if not amount.is_finite() or not minimum <= amount <= maximum:
            raise HomeError("Cette valeur dépasse les limites autorisées.")
    except (KeyError, InvalidOperation, TypeError) as error:
        raise HomeError("Les limites de ce réglage sont indisponibles.") from error
    converted = float(amount)
    if not math.isfinite(converted):
        raise HomeError("Cette valeur dépasse les limites autorisées.")
    return {"value": converted}


def spoken_state(item, state, temperature_target=None):
    attrs = state.get("attributes") or {}
    domain = item["domain"]
    if domain in {"media_player", "vacuum"}:
        return read_device("read", item, state)
    value = state.get("state")
    if domain == "input_text" and attrs.get("mode") == "password":
        raise HomeError("Ce champ est confidentiel ; je ne peux pas le lire.")
    if value is None or value in {"unknown", "unavailable"}:
        if domain == "sensor":
            if temperature_target is not None:
                raise ReadingClarification("La température demandée est indisponible pour le moment.")
            raise ReadingClarification("La mesure de ce capteur est actuellement indisponible.")
        raise HomeError("Cette valeur est actuellement indisponible.")
    if domain in {"switch", "input_boolean"}:
        value = {"on": "activé", "off": "désactivé"}.get(value, "indisponible")
    elif domain in {"sensor", "input_number"}:
        amount = Decimal(str(value))
        if not amount.is_finite():
            raise HomeError("Cette valeur est actuellement indisponible.")
        value = str(amount).replace("-", "moins ").replace(".", ",")
        unit = attrs.get("unit_of_measurement", "")
        value += " " + {"°C": "degrés Celsius", "°F": "degrés Fahrenheit"}.get(unit, unit)
        if temperature_target is not None:
            area = item.get("area")
            location = temperature_room(temperature_target)
            if item.get("name") and location != normalize(area) and matches(item, location):
                return prepare_tts_text(f"Le capteur « {item['name']} » indique {value.strip()}.")
            if area:
                return prepare_tts_text(f"Il fait {value.strip()} dans la pièce « {area} ».")
            return prepare_tts_text(f"Il fait {value.strip()} d’après le capteur.")
    elif domain == "input_datetime":
        pieces = []
        if attrs.get("has_date"):
            day = date.fromisoformat(str(value)[:10])
            pieces.append(f"{day.day} {SPOKEN_MONTHS[day.month - 1]} {day.year}")
        if attrs.get("has_time"):
            hour = time.fromisoformat(str(value).split()[-1])
            pieces.append(f"{hour.hour} h {hour.minute:02d}" + (f" {hour.second} secondes" if hour.second else ""))
        value = " à ".join(pieces)
    return prepare_tts_text(f"{item.get('name') or 'Ce réglage'} : {value}.")


class HomeCommands:
    def __init__(self, home):
        self.home = home

    def handle(self, text):
        """Résultat éventuel et catalogue réutilisable par le traitement des lumières."""
        command = parse(text) if len(text) <= 4000 else None
        return self.handle_command(command)

    def handle_command(self, command, approved=False):
        """Entrée typée réutilisée par le relais IA, mêmes contrôles que la voie locale."""
        if command is None:
            return None, None
        action, target, value = command
        catalog = None
        locked = False
        try:
            source = getattr(self.home, "catalog", None)
            catalog = (source() if callable(source) else HomeCatalog(self.home)).snapshot()
            items = catalog["entities"]
            item = resolve(items, target, self.home.room(), action == "temperature")
            if item is None:
                if action == "temperature":
                    raise ReadingClarification("Je ne trouve pas de mesure de température pour cette pièce ou ce capteur.")
                if action in {"turn_on", "turn_off"}:
                    return None, catalog  # La grammaire lumière par pièce/maison reste inchangée.
                # Les commandes génériques sans cible connue restent conversationnelles.
                return None, catalog
            if item["domain"] == "light":
                return None, catalog
            if item["domain"] not in SUPPORTED:
                raise HomeError("Le pilotage des thermostats est différé jusqu'à votre retour à domicile." if item["domain"] == "climate" else "Ce type d'entité n'est pas encore pris en charge.")
            entries = {x["entity_id"]: x for x in items}
            if not safe_device_group(item, entries):
                raise HomeError("Cette entité ou un membre de son groupe n'est pas autorisé.")
            self.home._acquire()
            locked = True
            domain, entity = item["domain"], item["entity_id"]
            state = self.home.get_state(entity)
            if not isinstance(state, dict) or state.get("entity_id") != entity:
                raise HomeError("Réponse Home Assistant inattendue.")
            attrs = state.get("attributes") or {}
            live_item = {**item, "attributes": attrs, "members": attrs.get("entity_id", item.get("members"))}
            if not safe_device_group(live_item, {**entries, entity: live_item}):
                raise HomeError("Cette entité ou un membre de son groupe n'est pas autorisé.")
            available = capabilities(domain, attrs)
            temperature_target = target if action == "temperature" else None
            if action == "temperature":
                action = "read"
            if action == "read":
                if "read" not in available:
                    raise HomeError("La lecture de ce réglage n'est pas disponible.")
                reply = spoken_state(item, state, temperature_target)
            elif action == "options":
                if "options" not in available:
                    raise HomeError("Ce réglage ne possède pas d'options.")
                reply = numbers_to_words("Choix possibles : " + ", ".join(attrs.get("options", [])) + ".")
            elif action in DEVICE_READS:
                if domain not in {"media_player", "vacuum"}:
                    raise HomeError("Cette lecture n'est pas disponible pour ce réglage.")
                required_domain = "vacuum" if action in {"fan_speeds", "cleaning_areas"} else "media_player"
                if domain != required_domain:
                    raise HomeError("Cette lecture n'est pas disponible pour cet appareil.")
                reply = read_device(action, item, state)
            else:
                service, payload, expected = self.prepare(action, value, domain, attrs, state, item)
                if service not in available:
                    raise HomeError("Cette action n'est pas disponible pour ce réglage.")
                if state.get("state") in {"unknown", "unavailable"} and domain != "input_button":
                    raise HomeError("Ce réglage est actuellement indisponible.")
                if not approved and action not in READ_ONLY_ACTIONS:
                    names = self.sensitive_names(live_item, {**entries, entity: live_item})
                    action_name = action if not isinstance(live_item.get("members"), list) else None
                    question = confirmation_question(action_name, names)
                    if question:
                        self.home.pending.propose(
                            self.home.confirmation_key(),
                            {"kind": "device", "operation": action, "target": entity,
                             "value": value},
                            question)
                        return {"matched": True, "reply": question, "status": "confirmation",
                                "confirmation": True, "action": action, "scope": "entity",
                                "room": item.get("area")}, catalog
                self.home.call_service(domain, service, {"entity_id": entity, **payload})
                # Aucun retry : un bouton peut déclencher une automatisation non répétable.
                reply = prepare_tts_text(expected.get("dispatch_only") or "Commande envoyée à Home Assistant ; résultat non confirmé.")
                try:
                    after = self.home.get_state(entity)
                    if service != "press" and isinstance(after, dict) and after.get("entity_id") == entity and self.confirmed(after, expected):
                        if domain in {"media_player", "vacuum"}:
                            reply = confirmed_reply(item, after, expected)
                        else:
                            reply = spoken_state(item, after) if domain != "input_text" or attrs.get("mode") != "password" else "Champ confidentiel mis à jour."
                    elif service == "press":
                        reply = "Appui envoyé à Home Assistant."
                except (HomeError, InvalidOperation, ValueError, TypeError):
                    pass
            return {"matched": True, "reply": reply, "action": action, "scope": "entity", "room": item.get("area")}, catalog
        except (HomeError, HomeBusy, CatalogError, ConfigurationError, ValueError, InvalidOperation, ZoneInfoNotFoundError, KeyError, TypeError) as error:
            message = str(error) if isinstance(error, (HomeError, HomeBusy, CatalogError, ConfigurationError)) else "La valeur ou la configuration de ce réglage est invalide."
            return {"matched": True, "reply": None, "error": message,
                    "clarification": isinstance(error, ReadingClarification)}, catalog
        finally:
            if locked:
                self.home._lock.release()

    @staticmethod
    def sensitive_names(item, entries):
        """Un groupe est sensible dès qu'un membre effectivement piloté l'est."""
        names, seen = [], set()

        def walk(current):
            entity = current.get("entity_id")
            if not entity or entity in seen:
                return
            seen.add(entity)
            if current.get("confirmation_required"):
                names.append(current.get("name") or entity)
            members = current.get("members")
            if isinstance(members, list):
                for member in members:
                    if isinstance(member, str) and member in entries:
                        walk(entries[member])

        walk(item)
        return list(dict.fromkeys(names))

    def prepare(self, action, value, domain, attrs, state, item=None):
        if domain in {"media_player", "vacuum"}:
            return prepare_device(action, value, domain, attrs, state, item or {})
        if action in {"turn_on", "turn_off"}:
            return action, {}, {"state": "on" if action == "turn_on" else "off"}
        if domain == "input_number":
            if action == "set":
                payload = numeric_payload(value, attrs)
                return "set_value", payload, {"number": Decimal(str(payload["value"]))}
            if action in {"increment", "decrement"}:
                current, step = Decimal(str(state["state"])), Decimal(str(attrs["step"]))
                if not step.is_finite() or step <= 0:
                    raise HomeError("Le pas de ce réglage est invalide.")
                # Les incréments natifs gèrent les unités propres du helper.
                if attrs.get("device_class"):
                    limit = Decimal(str(attrs["max" if action == "increment" else "min"]))
                    if (action == "increment" and current >= limit) or (action == "decrement" and current <= limit):
                        raise HomeError("Cette valeur dépasse les limites autorisées.")
                    return action, {}, {"direction": 1 if action == "increment" else -1, "before": current}
                expected = current + step * (1 if action == "increment" else -1)
                numeric_payload(str(expected), attrs)
                return action, {}, {"number": expected}
        if domain == "input_select":
            options = attrs.get("options", [])
            if action == "set":
                choices = [x for x in options if normalize(x) == normalize(value)]
                if not choices:
                    choices = [x for x in options if normalize(x) == normalize(value).strip(" .!?")]
                if len(choices) != 1:
                    raise HomeError("Option inconnue ou ambiguë. Demandez les options disponibles.")
                return "select_option", {"option": choices[0]}, {"state": choices[0]}
            if action in {"select_next", "select_previous"} and state["state"] in options:
                index = (options.index(state["state"]) + (1 if action == "select_next" else -1)) % len(options)
                return action, {"cycle": True}, {"state": options[index]}
        if domain == "input_datetime" and action == "set":
            config = self.home.config()
            zone = ZoneInfo(config["time_zone"])
            payload = datetime_payload(value, attrs, zone)
            return "set_datetime", payload, payload
        if domain == "input_text" and action == "set":
            if not attrs.get("min", 0) <= len(value) <= attrs.get("max", 255):
                raise HomeError("Ce texte dépasse les limites de longueur autorisées.")
            return "set_value", {"value": value}, {"state": value}
        if domain == "input_button" and action == "press":
            return "press", {}, {}
        raise HomeError("Cette action n'est pas disponible pour ce réglage.")

    @staticmethod
    def confirmed(after, expected):
        if not isinstance(after, dict) or after.get("state") in {None, "unknown", "unavailable"}:
            return False
        value = after["state"]
        device_result = confirmed_device(after, expected)
        if device_result is not None:
            return device_result
        if "state" in expected:
            return value == expected["state"]
        if "number" in expected:
            return Decimal(value) == expected["number"]
        if "direction" in expected:
            return (Decimal(value) - expected["before"]) * expected["direction"] > 0
        return all((value[:10] == val if key == "date" else value.split()[-1] == val) for key, val in expected.items())
