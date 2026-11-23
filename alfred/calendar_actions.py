"""Consultation ciblée des calendriers HA, sans divulgation inter-profils implicite."""
import re
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from alfred.home_assistant import HomeError, normalize
from alfred.intent_context import ask_for_reply
from alfred.reminder_actions import HOUR
from alfred.timers import number

PARIS=ZoneInfo("Europe/Paris")
TITLE_STOPWORDS={"le","la","les","un","une","de","du","des","d","l","a","au","aux","et","mon","ma","mes","rappel","evenement","rendez","vous"}
MONTHS={"janvier":1,"fevrier":2,"mars":3,"avril":4,"mai":5,"juin":6,"juillet":7,"aout":8,"septembre":9,"octobre":10,"novembre":11,"decembre":12}


def title_words(value):
    return [word for word in re.findall(r"[a-z0-9]+", normalize(value)) if word not in TITLE_STOPWORDS]


def explicit_dates(context):
    dates=[]
    for year,month,day in re.findall(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b",context):
        dates.append((int(day),int(month),int(year)))
    for day,month,year in re.findall(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{4}))?\b",context):
        dates.append((int(day),int(month),int(year) if year else None))
    for day,month,year in re.findall(r"\b(\d{1,2})\s+(janvier|fevrier|mars|avril|mai|juin|juillet|aout|septembre|octobre|novembre|decembre)(?:\s+(\d{4}))?\b",context):
        dates.append((int(day),MONTHS[month],int(year) if year else None))
    return dates


def matches_date(value, descriptor):
    day,month,year=descriptor
    return value.day==day and value.month==month and (year is None or value.year==year)


class CalendarActions:
    def __init__(self, calendars, bindings, profiles):
        self.calendars, self.bindings, self.profiles = calendars, bindings, profiles

    def _entity(self,args,context,speaker_id=None):
        audience=args.get("audience", "personal")
        if audience=="family":
            if not re.search(r"\b(?:famille|familial|familiale|commun)\b",context):
                return None, ask_for_reply("Souhaitez-vous utiliser le calendrier familial ?")
            return self.bindings.family(), None
        if audience=="personal":
            name=args.get("profile_name")
            if isinstance(name,str) and name.strip() and re.search(r"(?<!\w)"+re.escape(normalize(name))+r"(?!\w)",context):
                profiles=[p for p in self.profiles.list() if normalize(p["name"])==normalize(name)]
                if len(profiles)!=1:
                    return None, "Je ne trouve pas un profil familial unique pour ce calendrier."
                return self.bindings.personal(profiles[0]["id"]), None
            if speaker_id and self.profiles.get(speaker_id):
                return self.bindings.personal(speaker_id), None
            return None, ask_for_reply("De quel profil familial souhaitez-vous utiliser le calendrier ?")
        return None, ask_for_reply("Précisez si vous souhaitez le calendrier personnel ou familial.")

    def read(self, args, user_text, history, speaker_id=None):
        if not isinstance(args, dict) or set(args)-{"audience","profile_name","start_date","end_date"}:
            return "Précisez le calendrier et la période à consulter."
        texts=[x["content"] for x in history[-6:] if x.get("role")=="user" and isinstance(x.get("content"),str)] + [user_text]
        context=normalize(" ".join(texts))
        entity,error=self._entity(args,context,speaker_id)
        if error: return error
        try:
            start=date.fromisoformat(args["start_date"])
            end=date.fromisoformat(args["end_date"])
            if not 0 <= (end-start).days <= 30:
                raise ValueError()
        except (KeyError,ValueError,TypeError):
            return ask_for_reply("Précisez une période de consultation de 31 jours maximum.")
        begin=datetime.combine(start,time.min,tzinfo=PARIS)
        finish=datetime.combine(end+timedelta(days=1),time.min,tzinfo=PARIS)
        events=self.calendars.events(entity,begin,finish)
        if not events:
            return "Aucun événement trouvé pour cette période."
        lines=[]
        for event in events[:10]:
            title=event.get("summary")
            raw=event.get("start")
            if not isinstance(title,str) or not title.strip() or len(title)>160 or any(ord(c)<32 for c in title):
                continue
            if isinstance(raw,dict): raw=raw.get("dateTime") or raw.get("date")
            try:
                if not isinstance(raw,str): raise ValueError()
                if len(raw)==10:
                    when="le " + date.fromisoformat(raw).strftime("%d/%m")
                else:
                    instant=datetime.fromisoformat(raw.replace("Z","+00:00"))
                    if instant.utcoffset() is None: raise ValueError()
                    when="le " + instant.astimezone(PARIS).strftime("%d/%m à %H h %M")
            except ValueError:
                raise HomeError("La date d'un événement est illisible.")
            lines.append(when + " : " + title.strip())
        if not lines:
            return "Les événements retournés ne sont pas lisibles."
        return ". ".join(lines) + (f". {len(events)-10} autre(s) événement(s)." if len(events)>10 else ".")

    def mutate(self,args,user_text,history,now=None,speaker_id=None):
        allowed={"audience","profile_name","title","operation","scope","new_title","new_datetime"}
        if not isinstance(args,dict) or set(args)-allowed:
            return "Précisez l'événement et la modification souhaitée."
        current=normalize(user_text)
        turns=[x["content"] for x in history[-6:] if x.get("role")=="user" and isinstance(x.get("content"),str)]+[user_text]
        operation=args.get("operation")
        verbs={"delete":r"\b(?:annule|annuler|supprime|supprimer|efface|effacer)\b",
               "update":r"\b(?:modifie|modifier|change|changer|decale|decaler|repousse|reporter|reporte|renomme|renommer)\b"}
        followup=r"\b(?:prochaine|prochain|une seule|cette fois|cette occurrence|uniquement|seulement|toute la serie|serie entiere|toutes les occurrences)\b"
        if operation not in verbs: return "Précisez si vous souhaitez modifier ou supprimer cet événement. Aucune action effectuée."
        start=0
        for index in range(len(turns)-1,-1,-1):
            if re.search(verbs[operation],normalize(turns[index])):
                start=index;break
        context=normalize(" ".join(turns[start:]))
        if not re.search(verbs[operation],context) or not (re.search(verbs[operation],current) or re.search(followup,current)) or re.search(r"\b(?:non|jamais|pas)\b",current):
            return "Précisez si vous souhaitez modifier ou supprimer cet événement. Aucune action effectuée."
        entity,error=self._entity(args,context,speaker_id)
        if error: return error
        title=args.get("title")
        if not isinstance(title,str) or not 1<=len(title.strip())<=160:
            return ask_for_reply("Quel événement souhaitez-vous modifier ?")
        words=title_words(title)
        context_words=set(re.findall(r"[a-z0-9]+",context))
        if not words or any(word not in context_words for word in words):
            return ask_for_reply("Précisez le nom de l'événement. Aucune action effectuée.")
        now=now or datetime.now(timezone.utc)
        candidates=self.calendars.detailed_events(entity,now-timedelta(days=1),now+timedelta(days=365))
        matches=[]
        for event in candidates:
            summary=event.get("summary")
            if not isinstance(summary,str) or not all(word in set(title_words(summary)) for word in words): continue
            raw=event.get("start",{})
            raw=raw.get("dateTime") if isinstance(raw,dict) else raw
            try:
                instant=datetime.fromisoformat(raw.replace("Z","+00:00"))
                if instant.utcoffset() is None or instant.astimezone(timezone.utc)<now: continue
            except (ValueError,AttributeError,TypeError): continue
            if isinstance(event.get("uid"),str) and event["uid"]:
                matches.append((instant.astimezone(timezone.utc),event))
        if not matches: return "Je ne trouve pas cet événement à venir dans ce calendrier."
        if operation=="delete":
            dates=explicit_dates(context)
            if len(set(dates))>1: return "Plusieurs dates sont mentionnées ; précisez l'événement. Aucune action effectuée."
            if dates:
                matches=[pair for pair in matches if matches_date(pair[0].astimezone(PARIS).date(),dates[0])]
                if not matches: return "Je ne trouve pas cet événement à cette date. Aucune action effectuée."
        if len({event["uid"] for _,event in matches})!=1:
            return "Plusieurs événements correspondent. Précisez leur titre dans Home Assistant."
        matches.sort(key=lambda pair:pair[0]); chosen=matches[0][1]
        chosen_local=matches[0][0].astimezone(PARIS)
        if operation=="delete":
            if "demain" in context and chosen_local.date() != (now.astimezone(PARIS).date()+timedelta(days=1)):
                return "La date de l'événement ne correspond pas à demain. Aucune action effectuée."
            from alfred.reminder_actions import WEEKDAYS
            days={value for name,value in WEEKDAYS.items() if re.search(r"\b"+name+r"\b",context)}
            if days and (len(days)!=1 or chosen_local.weekday() not in days):
                return "Je ne peux pas confirmer la date de cet événement. Aucune action effectuée."
        recurring=bool(chosen.get("rrule") or chosen.get("recurrence_id"))
        scope=args.get("scope")
        if recurring:
            if scope not in ("one","series"):
                return ask_for_reply("Voulez-vous modifier seulement la prochaine occurrence ou toute la série ? Aucune action effectuée.")
            if scope=="one" and not re.search(r"\b(?:prochaine|prochain|une seule|cette fois|cette occurrence|uniquement|seulement)\b",context):
                return ask_for_reply("Voulez-vous modifier seulement la prochaine occurrence ou toute la série ? Aucune action effectuée.")
            if scope=="series" and not re.search(r"\b(?:toute la serie|tous les rappels|toutes les occurrences|la serie entiere|toute la recurrence)\b",context):
                return ask_for_reply("Voulez-vous modifier seulement la prochaine occurrence ou toute la série ? Aucune action effectuée.")
            if scope=="one" and not isinstance(chosen.get("recurrence_id"),str):
                return "Impossible d'identifier cette occurrence. Aucune action effectuée."
        recurrence_id=chosen.get("recurrence_id") if recurring and scope=="one" else None
        if operation=="delete":
            self.calendars._event_command(entity,"delete",chosen["uid"],recurrence_id=recurrence_id)
            return "Événement supprimé dans Home Assistant." if not recurring or scope=="one" else "Série supprimée dans Home Assistant."
        if recurring and scope=="series":
            return "La modification de toute une série n'est pas encore disponible ; vous pouvez modifier la prochaine occurrence ou utiliser Home Assistant."
        if chosen.get("status") is not None:
            return "Cet événement contient un état que je ne peux pas préserver. Modifiez-le dans Home Assistant."
        event={"summary":chosen.get("summary"), "dtstart":chosen.get("start",{}).get("dateTime"), "dtend":chosen.get("end",{}).get("dateTime")}
        if not all(isinstance(event[k],str) and event[k] for k in ("summary","dtstart","dtend")):
            return "Cet événement ne peut pas être modifié sans perdre ses informations. Utilisez Home Assistant."
        for key_name in ("description","location"):
            value=chosen.get(key_name)
            if value is not None:
                if not isinstance(value,str): return "Les informations de cet événement ne sont pas lisibles."
                event[key_name]=value
        changed=False
        new_title=args.get("new_title")
        if new_title is not None:
            if not isinstance(new_title,str) or not 1<=len(new_title.strip())<=160 or normalize(new_title) not in context:
                return ask_for_reply("Précisez le nouveau nom exact. Aucune action effectuée.")
            event["summary"]=new_title.strip();changed=True
        new_time=args.get("new_datetime")
        if new_time is not None:
            if not isinstance(new_time,str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}",new_time):
                return ask_for_reply("Précisez une date et une heure exactes. Aucune action effectuée.")
            hours=list(HOUR.finditer(context))
            if not hours: return ask_for_reply("À quelle heure souhaitez-vous déplacer cet événement ?")
            try:
                wall=datetime.fromisoformat(new_time)
                spoken=hours[-1].group().strip()
                if spoken in ("midi","minuit"):
                    hh,mm=(12 if spoken=="midi" else 0),0
                else:
                    parts=re.fullmatch(r"(.+?)\s*(?:h(?:eures?)?|:)\s*(\d{0,2})",spoken)
                    hh=number(parts[1].strip()) if parts else None
                    mm=int(parts[2]) if parts and parts[2] else 0
                choices=[wall.replace(tzinfo=PARIS,fold=f) for f in (0,1)]
                valid=[x for x in choices if x.astimezone(timezone.utc).astimezone(PARIS).replace(tzinfo=None)==wall]
                if hh!=wall.hour or mm!=wall.minute or not valid or len({x.utcoffset() for x in valid})!=1: raise ValueError()
                if valid[0].astimezone(timezone.utc)<=now: raise ValueError()
                if "demain" in context:
                    if wall.date() != now.astimezone(PARIS).date()+timedelta(days=1): raise ValueError()
                elif "aujourd'hui" in context:
                    if wall.date() != now.astimezone(PARIS).date(): raise ValueError()
                elif wall.date()!=chosen_local.date():
                    # Ne pas laisser le modèle inventer une date implicite.
                    dates=explicit_dates(context)
                    if len(set(dates))!=1 or not matches_date(wall.date(),dates[0]):
                        raise ValueError()
                original_start=datetime.fromisoformat(event["dtstart"]);original_end=datetime.fromisoformat(event["dtend"])
                event["dtstart"]=valid[0].isoformat();event["dtend"]=(valid[0]+(original_end-original_start)).isoformat()
            except (ValueError,TypeError,OverflowError):
                return "Je n'ai pas pu confirmer la nouvelle date et l'heure. Aucune action effectuée."
            changed=True
        if not changed: return ask_for_reply("Que souhaitez-vous modifier dans cet événement ?")
        self.calendars._event_command(entity,"update",chosen["uid"],event=event,recurrence_id=recurrence_id)
        return "Événement modifié dans Home Assistant."
