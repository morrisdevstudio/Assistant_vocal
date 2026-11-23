"""Commandes françaises explicites de minuteurs, sans interprétation par le LLM."""

import math
import re
import unicodedata
from datetime import datetime, timedelta

from alfred.home_assistant import normalize as normalize_name
from alfred.storage import utc_now

WAKE_PREFIX = re.compile(r"^(?:(?:hey|he|eh|euh|et|alors)\s*,?\s*)?(?:alfred|alexa|jarvis(?:se)?)\s*,?\s*")


def normalize(text):
    text = unicodedata.normalize("NFD", text.lower().replace("’", "'"))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[.!?,;]+$", "", text.strip())
    text = WAKE_PREFIX.sub("", text)
    text = re.sub(r"\s*[,]?\s+s'il te plait$", "", text)
    text = re.sub(r"\bminuteries\b", "minuteurs", text)
    text = re.sub(r"\bminuterie\b", "minuteur", text)
    return " ".join(text.split())


SMALL = dict(zip(
    "zero un deux trois quatre cinq six sept huit neuf dix onze douze treize quatorze quinze seize".split(),
    range(17)))
TENS = {"vingt": 20, "trente": 30, "quarante": 40, "cinquante": 50, "soixante": 60}


def number(text):
    if text.isdigit():
        return int(text) if len(text) <= 6 else None
    text = text.replace("-", " ")
    if text in SMALL:
        return SMALL[text]
    if text == "une":
        return 1
    if text == "quatre vingts":
        return 80
    for prefix, value in [("quatre vingt", 80), *TENS.items()]:
        if text == prefix:
            return value
        if text.startswith(prefix + " "):
            tail = text[len(prefix) + 1:].removeprefix("et ")
            remainder = number(tail)
            if remainder is not None and 0 < remainder < (20 if value in (60, 80) else 10):
                return value + remainder
    if text.startswith("dix ") and text[4:] in SMALL and 7 <= SMALL[text[4:]] <= 9:
        return 10 + SMALL[text[4:]]
    return None


def duration(text):
    if text in ("une demi heure", "une demi-heure"):
        return 1800
    # Les durées longues restent bornées à sept jours pour les minuteurs.
    day = re.fullmatch(r"(?:un|une|1) jours?", text.strip())
    if day:
        return 86400
    compact = re.fullmatch(r"(.+?)\s*(?:minutes?|min)\s*(\d{1,2}|[a-z -]+)", text)
    if compact:
        minutes = number(compact[1].strip())
        seconds = number(compact[2].strip())
        if minutes is not None and seconds is not None and 0 <= seconds < 60:
            return minutes * 60 + seconds
    # Consommer toute la durée : aucune action sur une phrase mêlant deux demandes.
    parts = re.fullmatch(
        r"(.+?) (heures?|minutes?|secondes?)(?: et (demie?))?"
        r"(?: (?:et )?(.+?) (minutes?|secondes?))?", text)
    if not parts:
        return None
    first, unit, half, second, second_unit = parts.groups()
    amount = number(first)
    if amount is None:
        return None
    factors = {"heure": 3600, "minute": 60, "seconde": 1}
    factor = factors[unit.rstrip("s")]
    total = amount * factor
    if half:
        if factor == 1:
            return None
        total += factor // 2
    if second is not None:
        extra = number(second)
        other = factors[second_unit.rstrip("s")]
        if extra is None or other >= factor or half:
            return None
        total += extra * other
    return total


def spoken_duration(seconds):
    seconds = max(0, math.ceil(seconds))
    parts = []
    for factor, unit in ((3600, "heure"), (60, "minute"), (1, "seconde")):
        value, seconds = divmod(seconds, factor)
        if value:
            if value == 1:
                parts.append("une " + unit)
            else:
                parts.append(f"{value} {unit}s" if value > 1 else f"{value} {unit}")
    return " et ".join(parts) or "0 seconde"


CURRENT_TIMER_QUERIES = frozenset({
    "combien de temps reste-t-il",
    "combien de temps reste t il", "combien de temps reste-t-il au minuteur",
    "combien de temps reste t il au minuteur", "combien de temps il reste",
    "combien de temps reste sur le minuteur", "combien reste-t-il sur le minuteur",
    "combien de temps reste au minuteur", "combien de temps reste il au minuteur",
    "quel temps reste-t-il sur le minuteur",
    "quel temps reste t il sur le minuteur",
    "combien de temps reste-t-il sur le minuteur en cours",
    "quel temps reste sur le minuteur en cours",
})


def is_current_timer_query(prompt):
    """Reconnaître la question du minuteur courant sur tous les chemins locaux."""
    prompt = normalize(prompt)
    return prompt in CURRENT_TIMER_QUERIES or bool(re.fullmatch(
        r"(?:il reste (?:combien(?: de temps)?|quel temps)|"
        r"(?:combien(?: de temps)?|quel temps) (?:il reste|reste(?:-t-il| t il)?))"
        r"(?: (?:sur|pour) (?:le|mon) minuteur| au minuteur)?(?: en cours)?", prompt))


def timer_name(item):
    title = item["title"]
    duration_title = title.removeprefix("Minuteur de ")
    if title == "Minuteur" or (duration_title != title and duration(duration_title) is not None):
        return ""
    return title


def timer_remaining(item, now, include_label=False):
    name = timer_name(item)
    label = f"« {name} »" if name else f"le {item['title'].lower()}"
    if item["status"] == "ringing":
        return f"Le minuteur {label} sonne." if name else (
            f"{label.capitalize()} sonne." if include_label else "Le minuteur sonne.")
    left = spoken_duration((datetime.fromisoformat(item["due_at"]) - now).total_seconds())
    return f"Pour {label}, il reste {left}." if name or include_label else f"Il reste {left}."


class TimerService:
    def __init__(self, store):
        self.store = store

    def handle(self, text, floor_id, terminal_id="browser-test", now=None, name=None):
        prompt = normalize(text)
        creation = re.fullmatch(
            r"(?:on met|mets|met|lance|demarre|cree|programme) (?:moi )?(?:un|une|le|la) minuteur"
            r" (?:de|pour) (.+)", prompt)
        all_listing = prompt in {
            "quels sont les minuteurs", "quels sont les minuteurs en cours",
            "liste les minuteurs", "liste mes minuteurs",
        }
        current_listing = is_current_timer_query(prompt)
        listing = all_listing or current_listing
        cancellation = re.fullmatch(r"(?:annule|arrete) (?:le minuteur|mon minuteur)(?: (.+))?", prompt)
        cancel_number = number(cancellation[1]) if cancellation and cancellation[1] else None
        if cancellation and cancellation[1] and cancel_number is None:
            name = cancellation[1]
        stop = prompt in {"stop", "arrete la sonnerie", "arrete les sonneries"}
        seconds = duration(creation[1]) if creation else None
        if not (listing or cancellation or stop or seconds is not None):
            # Une demande de minuteur mal comprise ne doit pas produire une fausse
            # confirmation d'exécution par le modèle de conversation.
            if "minuteur" in prompt:
                return {"text": "Précisez une commande, par exemple : mets un minuteur de huit minutes. "
                        "Je n'ai modifié aucun minuteur.", "action": "clarify"}
            return None
        if floor_id not in ("rdc", "etage1"):
            return {"text": "Choisissez d'abord l'étage de ce terminal dans le formulaire des échéances.",
                    "action": "clarify"}
        now = now or utc_now()
        if seconds is not None:
            if not 1 <= seconds <= 604800:
                return {"text": "La durée doit être comprise entre une seconde et sept jours.", "action": "clarify"}
            label = spoken_duration(seconds)
            record = self.store.create(kind="timer", title=name or f"Minuteur de {label}",
                                       due_at=now + timedelta(seconds=seconds),
                                       floor_id=floor_id, terminal_id=terminal_id, now=now)
            reply = f"Minuteur « {name} » lancé pour {label}." if name else f"Minuteur de {label} lancé."
            return {"text": reply, "action": "create", "item": record}
        # Actualiser les échéances même entre deux passages de l'ordonnanceur.
        self.store.tick(now)
        if stop:
            count = self.store.stop_floor(floor_id, now)
            return {"text": "Sonnerie arrêtée." if count else "Aucun minuteur ne sonne à cet étage.", "action": "stop"}
        named = None
        if name:
            key = normalize_name(name).replace("œ", "oe")
            matches = [item for item in self.store.active_timers(floor_id)
                       if normalize_name(timer_name(item)).replace("œ", "oe") == key]
            if len(matches) != 1:
                return {"text": (f"Plusieurs minuteurs s’appellent « {name} ». Choisissez-le dans Minuteries."
                                 if matches else f"Aucun minuteur actif ne s’appelle « {name} » à cet étage."),
                        "action": "clarify"}
            named = matches[0]
        if cancellation:
            current = named or (self.store.current_timer(floor_id) if cancel_number is None else None)
            identifier = str(cancel_number) if cancel_number is not None else (
                str(current["number"]) if current else None)
            result = self.store.cancel_timer(floor_id, identifier, now) if identifier is not None else False
            if result == "ambiguous":
                return {"text": "Plusieurs minuteurs sont actifs. Donnez le nom de celui à annuler ou choisissez-le dans Minuteries.", "action": "clarify"}
            reply = "Minuteur annulé." if result else "Aucun minuteur correspondant à cet étage."
            if result and current and timer_name(current):
                reply = f"Minuteur « {timer_name(current)} » annulé."
            return {"text": reply,
                    "action": "cancel"}
        items = self.store.active_timers(floor_id)
        if not items:
            return {"text": "Aucun minuteur actif à cet étage.", "action": "list"}
        if current_listing:
            item = named or self.store.current_timer(floor_id)
            if item is None:
                return {"text": "Aucun minuteur actif à cet étage.", "action": "list"}
            return {"text": timer_remaining(item, now), "action": "list", "items": [item]}
        replies = [timer_remaining(item, now, include_label=True) for item in items[:10]]
        if len(items) > 10:
            replies.append(f"Il y a {len(items)} minuteurs actifs ; seuls les dix premiers sont lus.")
        return {"text": " ".join(replies), "action": "list", "items": items}
