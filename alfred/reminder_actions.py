"""Création vocale prudente : identité et heure doivent être explicites."""
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from alfred.home_assistant import normalize
from alfred.intent_context import ask_for_reply
from alfred.storage import utc_now
from alfred.timers import number

PARIS = ZoneInfo("Europe/Paris")
HOUR = re.compile(r"\b(?:\d{1,2}\s*(?:h(?:eures?)?|:)\s*\d{0,2}|\d{1,2}\s+heures?|midi|minuit|(?:un|une|deux|trois|quatre|cinq|six|sept|huit|neuf|dix|onze|douze|treize|quatorze|quinze|seize|vingt)(?:[- ](?:et[- ]un|un|deux|trois))?\s+heures?)\b")
WEEKDAYS = {"lundi":0, "mardi":1, "mercredi":2, "jeudi":3, "vendredi":4, "samedi":5, "dimanche":6}


class ReminderActions:
    def __init__(self, store, profiles, announcements, clock=utc_now, calendars=None, bindings=None):
        self.store, self.profiles, self.announcements, self.clock = store, profiles, announcements, clock
        self.calendars, self.bindings = calendars, bindings

    def create(self, args, user_text, history, speaker_id=None):
        allowed = {"title", "datetime_local", "recurrence", "audience", "profile_name", "room"}
        if not isinstance(args, dict) or set(args) - allowed:
            return "Je n'ai pas compris le rappel. Aucun rappel n'a été créé."
        turns = [message["content"] for message in history[-6:]
                 if message.get("role") == "user" and isinstance(message.get("content"), str)] + [user_text]
        start = 0
        for index in range(len(turns)-1, -1, -1):
            if re.search(r"\b(?:rappel\w*|rappell\w*|pense\w*|souviens\w*)\b", normalize(turns[index])):
                start = index
                break
        context = normalize(" ".join(turns[start:]))
        hour_matches = list(HOUR.finditer(context))
        if not hour_matches:
            return ask_for_reply("À quelle heure souhaitez-vous ce rappel ? Aucun rappel n'a encore été créé.")
        title, local_text = args.get("title"), args.get("datetime_local")
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 160 or not isinstance(local_text, str):
            return ask_for_reply("Précisez le contenu et la date du rappel. Aucun rappel n'a été créé.")
        if any(ord(ch) < 32 for ch in title) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", local_text):
            return "La date du rappel n'est pas assez précise. Aucun rappel n'a été créé."
        try:
            wall = datetime.fromisoformat(local_text)
            candidates = [wall.replace(tzinfo=PARIS, fold=fold) for fold in (0, 1)]
            valid = [d for d in candidates if d.astimezone(timezone.utc).astimezone(PARIS).replace(tzinfo=None) == wall]
            if not valid or len({d.utcoffset() for d in valid}) != 1:
                return ask_for_reply("Cette heure est ambiguë ou n'existe pas au changement d'heure. Précisez une autre heure.")
            due = valid[0].astimezone(timezone.utc)
        except (ValueError, OverflowError):
            return "La date du rappel est invalide. Aucun rappel n'a été créé."
        spoken = hour_matches[-1].group().strip()
        if spoken in ("midi", "minuit"):
            expected_hour, expected_minute = (12 if spoken == "midi" else 0), 0
        else:
            parsed = re.fullmatch(r"(.+?)\s*(?:h(?:eures?)?|:)\s*(\d{0,2})", spoken)
            expected_hour = number(parsed[1].strip()) if parsed else None
            expected_minute = int(parsed[2]) if parsed and parsed[2] else 0
        if expected_hour is None or expected_hour != wall.hour or expected_minute != wall.minute:
            return "Je n'ai pas pu confirmer l'heure demandée. Aucun rappel n'a été créé."
        now = self.clock()
        if not now < due <= now + timedelta(days=366):
            return ask_for_reply("Choisissez une date future dans les 366 prochains jours. Aucun rappel n'a été créé.")
        if re.search(r"\bdemain\b", context) and wall.date() != (now.astimezone(PARIS).date() + timedelta(days=1)):
            return "Je n'ai pas pu confirmer la date de demain. Aucun rappel n'a été créé."
        recurrence = args.get("recurrence", "once")
        if recurrence not in ("once", "weekly"):
            return "Je sais seulement programmer un rappel ponctuel ou hebdomadaire pour l'instant."
        if re.search(r"\b(?:tous les jours|chaque jour|quotidien|tous les mois|chaque mois)\b", context):
            return "Cette récurrence n'est pas encore disponible. Aucun rappel n'a été créé."
        days = [n for name, n in WEEKDAYS.items() if re.search(r"\b" + name + r"\b", context)]
        if days and (len(set(days)) != 1 or wall.weekday() != days[0]):
            return "Je n'ai pas pu confirmer le jour demandé. Aucun rappel n'a été créé."
        if re.search(r"\b(?:tous les|chaque|toutes les)\b", context) and days and recurrence != "weekly":
            return "Je n'ai pas pu confirmer la répétition. Aucun rappel n'a été créé."
        audience = args.get("audience", "personal")
        if audience not in ("personal", "family"):
            return ask_for_reply("Ce rappel est-il personnel ou pour toute la famille ?")
        if audience == "family" and not re.search(r"\b(?:famille|familial|familiale|tout le monde|rappelle[- ]nous|rappel collectif|rappel commun)\b", context):
            return ask_for_reply("Ce rappel est-il pour toute la famille ? Aucun rappel n'a été créé.")
        owner_id = None
        if audience == "personal":
            name = args.get("profile_name")
            if isinstance(name,str) and name.strip() and re.search(r"(?<!\w)" + re.escape(normalize(name)) + r"(?!\w)", context):
                matches = [p for p in self.profiles.list() if normalize(p["name"]) == normalize(name)]
                if len(matches) != 1:
                    return "Je ne trouve pas un profil familial unique pour ce rappel. Aucun rappel n'a été créé."
                owner_id = matches[0]["id"]
            elif speaker_id and self.profiles.get(speaker_id):
                owner_id = speaker_id
            else:
                return ask_for_reply("Pour quel profil familial est ce rappel ? Aucun rappel n'a été créé.")
        room = args.get("room")
        if not isinstance(room, str) or not room.strip():
            return ask_for_reply("Dans quelle pièce souhaitez-vous ce rappel ? Aucun rappel n'a encore été créé.")
        if not re.search(r"(?<!\w)" + re.escape(normalize(room)) + r"(?!\w)", context):
            return ask_for_reply("Dans quelle pièce souhaitez-vous ce rappel ? Aucun rappel n'a encore été créé.")
        try:
            targets = self.announcements.select("room", room)
        except Exception:
            return "Je ne trouve pas de terminal Alfred configuré dans cette pièce. Aucun rappel n'a été créé."
        if not targets:
            return "Je ne trouve pas de terminal Alfred configuré dans cette pièce. Aucun rappel n'a été créé."
        if len(targets) != 1:
            return "Plusieurs terminaux correspondent à cette pièce. Aucun rappel n'a été créé."
        target = targets[0]
        if self.calendars is not None and self.bindings is not None:
            entity = self.bindings.personal(owner_id) if audience == "personal" else self.bindings.family()
            self.calendars.create_reminder(entity, title.strip(), due.astimezone(PARIS), target["room"], recurrence=recurrence)
        else:
            self.store.create_reminder(title=title.strip(), due_at=due, floor_id=target["floor"],
                terminal_id=target["entity_id"], target_room=target["room"], audience=audience,
                owner_id=owner_id, recurrence=recurrence, now=now)
        formatted = due.astimezone(PARIS).strftime("%d/%m à %H h %M")
        return f"Rappel enregistré {'dans Home Assistant ' if self.calendars is not None else ''}pour le {formatted}, pièce {target['room']}. L'annonce sera demandée à l'échéance."
