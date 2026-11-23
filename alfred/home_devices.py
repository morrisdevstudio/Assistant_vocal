"""Commandes natives bornées pour lecteurs multimédias et aspirateurs."""

import math
import re
from decimal import Decimal

from alfred.home_assistant import HomeError, normalize
from alfred.tts_text import prepare_tts_text


FAN_NAMES = {"quiet": "silencieux", "balanced": "équilibré", "turbo": "turbo",
             "max": "maximum", "max_plus": "maximum plus", "off": "désactivé", "custom": "personnalisé"}
DEVICE_READS = {"read_volume", "read_source", "sources", "fan_speeds", "cleaning_areas"}


def parse_device(phrase):
    patterns = [
        ("device_pause", r"mets? (.+?) en pause"),
        ("device_pause", r"(?:mets? en pause|pause) (.+)"),
        ("device_resume", r"(?:reprends|reprend|reprendre|relance) (?:la lecture (?:de |du |sur )?)?(.+)"),
        ("device_stop", r"(?:arrete|arreter|stoppe|stop) (.+)"),
        ("device_start", r"(?:demarre|demarrer|lance|lancer) (.+)"),
        ("return_to_base", r"(?:renvoie|ramene) (.+?) a (?:sa|la) (?:base|station)"),
        ("return_to_base", r"(?:retour a (?:la|sa) (?:base|station) (?:de |du |pour )?)(.+)"),
        ("locate", r"(?:localise|localiser|fais sonner) (.+)"),
        ("mute", r"(?:coupe|couper|desactive) le son (?:de |du |de la |de l'|sur )(.+)"),
        ("unmute", r"(?:remets|remet|reactive|retablis) le son (?:de |du |de la |de l'|sur )(.+)"),
        ("volume_up", r"(?:augmente|monte) le volume (?:de |du |de la |de l'|sur )(.+)"),
        ("volume_down", r"(?:diminue|baisse) le volume (?:de |du |de la |de l'|sur )(.+)"),
        ("media_next_track", r"(?:piste|morceau|titre) suivant(?:e)? (?:sur |de |du )(.+)"),
        ("media_next_track", r"passe (.+?) (?:au morceau|a la piste|au titre) suivant(?:e)?"),
        ("media_previous_track", r"(?:piste|morceau|titre) precedent(?:e)? (?:sur |de |du )(.+)"),
        ("media_previous_track", r"passe (.+?) (?:au morceau|a la piste|au titre) precedent(?:e)?"),
        ("read_volume", r"(?:quel est|donne-moi|lis) le volume (?:de |du |de la |de l')(.+)"),
        ("read_source", r"(?:quelle est|donne-moi|lis) la source (?:de |du |de la |de l')(.+)"),
        ("sources", r"(?:liste|quelles sont) les sources (?:de |du |de la |de l'|pour )(.+)"),
        ("fan_speeds", r"(?:liste|quelles sont) les puissances (?:de |du |de la |de l'|pour )(.+)"),
        ("cleaning_areas", r"(?:liste|quelles sont) les pieces (?:nettoyables (?:par |avec )|de |du )(.+)"),
    ]
    for action, pattern in patterns:
        match = re.fullmatch(pattern, phrase)
        if match:
            return action, match[1], None
    for action, subject in (("volume_set", "le volume"), ("select_source", "la source"), ("set_fan_speed", "la puissance")):
        match = re.fullmatch(r"(?:mets?|regle|fixe|change) " + subject + r" (?:de |du |de la |de l')(.+?) (?:a|sur) (.+)", phrase)
        if match:
            return action, match[1], match[2]
    match = re.fullmatch(r"(?:mets?|regle|fixe) le volume a (.+?) sur (.+)", phrase)
    if match:
        return "volume_set", match[2], match[1]
    match = re.fullmatch(r"nettoie (.+?) avec (.+)", phrase)
    if match:
        return "clean_area", match[2], match[1]
    match = re.fullmatch(r"nettoie (.+)", phrase)
    if match:
        return "clean_area", "aspirateur", match[1]
    return None


def generic_target(item, target):
    """Noms de catégorie explicites uniquement ; aucun rapprochement flou."""
    if item.get("domain") == "vacuum" and target in {"aspirateur", "robot", "robot aspirateur"}:
        return True
    if item.get("domain") == "media_player":
        if target in {"lecteur", "lecteur multimedia"}:
            return True
        kind = item.get("attributes", {}).get("device_class")
        return (target in {"tele", "television", "televiseur"} and kind == "tv"
                or target in {"ampli", "amplificateur"} and kind == "receiver")
    return False


def choose(value, options, label, translate=False):
    if not isinstance(options, list) or not options or any(not isinstance(x, str) for x in options):
        raise HomeError(f"Les {label} de cet appareil sont indisponibles.")
    target = normalize(value).strip(" .!?")
    found = [x for x in options if normalize(x) == target or translate and normalize(FAN_NAMES.get(x, x)) == target]
    if len(found) != 1:
        raise HomeError(f"Choix inconnu ou ambigu. Demandez les {label} disponibles.")
    return found[0]


def volume(attrs):
    value = attrs.get("volume_level")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
        raise HomeError("Le volume de cet appareil est indisponible.")
    return value


def read_device(action, item, state):
    attrs = state.get("attributes") or {}
    if state.get("state") in {None, "unknown", "unavailable"}:
        raise HomeError("Cet appareil est actuellement indisponible.")
    name = item.get("name") or "Cet appareil"
    if action == "read_volume":
        value = f"volume à {round(volume(attrs) * 100, 2):g} pour cent"
    elif action == "read_source":
        value = "source « " + attrs["source"] + " »" if isinstance(attrs.get("source"), str) else "source inconnue"
    elif action in {"sources", "fan_speeds", "cleaning_areas"}:
        choices = (attrs.get("source_list") if action == "sources" else attrs.get("fan_speed_list") if action == "fan_speeds"
                   else [x["name"] for x in item.get("cleaning_areas", [])])
        if not isinstance(choices, list) or not choices or any(not isinstance(x, str) for x in choices):
            raise HomeError("Aucun choix disponible ; vérifiez la configuration Home Assistant de cet appareil.")
        value = ", ".join(FAN_NAMES.get(x, x) if action == "fan_speeds" else x for x in choices)
    else:
        value = {"off": "éteint", "on": "allumé", "idle": "au repos", "playing": "en lecture", "paused": "en pause",
                 "buffering": "prépare la lecture", "cleaning": "en cours de nettoyage", "docked": "à sa base",
                 "returning": "retourne à sa base", "error": "en erreur"}.get(state.get("state"), "état non reconnu")
    return prepare_tts_text(f"{name} : {value}.")


def prepare_device(action, value, domain, attrs, state, item):
    """Renvoie service, données et preuve attendue ; aucune action arbitraire."""
    if domain == "media_player":
        mapped = {"device_pause": "media_pause", "device_resume": "media_play", "device_start": "media_play", "device_stop": "media_stop"}
        service = mapped.get(action, action)
        expected_states = {"turn_on": ["on", "idle", "playing", "paused", "buffering"], "turn_off": ["off"],
                           "media_pause": ["paused"], "media_play": ["playing"], "media_stop": ["idle", "off"]}
        if service in expected_states:
            return service, {}, {"states": expected_states[service]}
        if service in {"media_next_track", "media_previous_track"}:
            return service, {}, {"dispatch_only": "Passage à la piste " + ("suivante" if service == "media_next_track" else "précédente") + " demandé."}
        if action in {"mute", "unmute"}:
            muted = action == "mute"
            return "volume_mute", {"is_volume_muted": muted}, {"attributes": {"is_volume_muted": muted}}
        if action == "volume_set":
            from alfred.home_commands import numeric
            amount = numeric(re.sub(r"\s*(?:%|pour cent|pourcent)$", "", value).strip())
            if not amount.is_finite() or not 0 <= amount <= 100:
                raise HomeError("Le volume doit être compris entre zéro et cent pour cent.")
            target = float(amount / 100)
            return action, {"volume_level": target}, {"volume": target}
        if action in {"volume_up", "volume_down"}:
            return action, {}, {"volume_direction": 1 if action == "volume_up" else -1, "before": volume(attrs)}
        if action in {"select_source", "set"}:
            choice = choose(value, attrs.get("source_list"), "sources")
            return "select_source", {"source": choice}, {"attributes": {"source": choice}}
    if domain == "vacuum":
        service = {"device_start": "start", "device_resume": "start", "device_pause": "pause", "device_stop": "stop"}.get(action, action)
        expected_states = {"start": ["cleaning"], "pause": ["paused"], "stop": ["idle", "paused", "docked"],
                           "return_to_base": ["returning", "docked"]}
        if service in expected_states:
            return service, {}, {"states": expected_states[service]}
        if action == "locate":
            return action, {}, {"dispatch_only": "Signal de localisation demandé."}
        if action in {"set_fan_speed", "set"}:
            choice = choose(value, attrs.get("fan_speed_list"), "puissances", translate=True)
            return "set_fan_speed", {"fan_speed": choice}, {"attributes": {"fan_speed": choice}}
        if action == "clean_area":
            room = re.sub(r"^(?:le |la |les |l')", "", value)
            found = [x for x in item.get("cleaning_areas", []) if normalize(x["name"]) == room]
            if len(found) != 1:
                raise HomeError("Pièce inconnue ou non associée à la carte de cet aspirateur dans Home Assistant. Aucun nettoyage lancé.")
            # Le service natif vérifie le mapping ; jamais de repli sur un nettoyage global.
            return action, {"cleaning_area_id": [found[0]["id"]]}, {"dispatch_only": "Nettoyage de « " + found[0]["name"] + " » demandé."}
    raise HomeError("Cette action n'est pas disponible pour cet appareil.")


def confirmed_device(after, expected):
    attrs = after.get("attributes") or {}
    if "dispatch_only" in expected:
        return False
    if "states" in expected:
        return after["state"] in expected["states"]
    if "attributes" in expected:
        return all(attrs.get(key) == value for key, value in expected["attributes"].items())
    if "volume" in expected:
        return abs(volume(attrs) - expected["volume"]) <= .005
    if "volume_direction" in expected:
        return (volume(attrs) - expected["before"]) * expected["volume_direction"] > 0
    return None


def confirmed_reply(item, after, expected):
    attrs = after.get("attributes") or {}
    if "volume" in expected or "volume_direction" in expected:
        return read_device("read_volume", item, after)
    if "is_volume_muted" in expected.get("attributes", {}):
        return (item.get("name") or "Cet appareil") + (" : son coupé." if attrs["is_volume_muted"] else " : son rétabli.")
    if "source" in expected.get("attributes", {}):
        return read_device("read_source", item, after)
    if "fan_speed" in expected.get("attributes", {}):
        return prepare_tts_text((item.get("name") or "Cet appareil") + " : puissance « " + FAN_NAMES.get(attrs["fan_speed"], attrs["fan_speed"]) + " ».")
    return read_device("read", item, after)
