import json
import threading
from datetime import datetime, timezone
import httpx
from alfred.calendar_actions import CalendarActions
from alfred.conversation import ConversationService
from alfred.credentials import CredentialStore
from alfred.profiles import Profiles
from alfred.storage import Store


def test_calendar_read_requires_named_profile_and_uses_selected_calendar(tmp_path):
    store=Store(tmp_path);store.initialize();profiles=Profiles(store); profile=profiles.create("Alex")
    class Bindings:
        def personal(self,identifier): assert identifier==profile["id"]; return "calendar.personnel"
        def family(self): return "calendar.familial"
    class Calendars:
        def __init__(self): self.calls=[]
        def events(self,entity,start,end):
            self.calls.append((entity,start,end))
            return [{"summary":"Événement fictif","start":"2026-10-30T19:00:00+01:00"}]
    calendars=Calendars();actions=CalendarActions(calendars,Bindings(),profiles)
    args={"audience":"personal","profile_name":"Alex","start_date":"2026-10-30","end_date":"2026-10-30"}
    assert "quel profil" in actions.read(args,"Que prévoit mon calendrier demain ?",[]).lower()
    result=actions.read(args,"Que prévoit le calendrier d'Alex demain ?",[])
    assert "Événement fictif" in result and calendars.calls[0][0]=="calendar.personnel"


def test_private_calendar_answer_is_not_sent_back_to_provider(tmp_path):
    requests=[]
    def handler(request):
        requests.append(json.loads(request.content))
        if len(requests)==1:
            event={"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"name":"consulter_calendrier","arguments":'{"audience":"family","start_date":"2026-10-30","end_date":"2026-10-30"}'}}]},"finish_reason":"tool_calls"}]}
        else:
            event={"choices":[{"delta":{"content":"Bonjour"},"finish_reason":"stop"}]}
        return httpx.Response(200,headers={"content-type":"text/event-stream"},text="data: "+json.dumps(event)+"\n\ndata: [DONE]\n\n")
    class CalendarAction:
        def read(self,args,text,history): return "Événement privé fictif."
    engine=ConversationService(CredentialStore(tmp_path,api_key="jeton-fictif-test-0123456789"),lambda:httpx.Client(transport=httpx.MockTransport(handler)))
    engine.shopping=object();engine.calendar_actions=CalendarAction()
    first=list(engine.stream("Lis le calendrier familial", "session-fictive-0001",threading.Event()))
    assert "Événement privé fictif" in first[-1]["text"]
    list(engine.stream("Merci", "session-fictive-0001",threading.Event()))
    assert "Événement privé fictif" not in json.dumps(requests[-1],ensure_ascii=False)
    assert "Résultat du calendrier affiché localement" in json.dumps(requests[-1],ensure_ascii=False)


def mutation_setup(tmp_path, events):
    store=Store(tmp_path);store.initialize(); profiles=Profiles(store)
    class Bindings:
        def family(self): return "calendar.familial"
    class Calendar:
        def __init__(self): self.calls=[]
        def detailed_events(self,entity,start,end): return events
        def _event_command(self,*args,**kwargs): self.calls.append((args,kwargs))
    calendar=Calendar()
    return CalendarActions(calendar,Bindings(),profiles),calendar


def calendar_event(uid="a",title="Sortir les poubelles",recurring=False):
    return {"uid":uid,"summary":title,"start":{"dateTime":"2026-11-05T19:00:00+01:00"},
            "end":{"dateTime":"2026-11-05T19:01:00+01:00"},"description":"description fictive", "location":"Bureau",
            "rrule":"FREQ=WEEKLY" if recurring else None,"recurrence_id":"20261105T190000" if recurring else None,"status":None}


def test_ambiguous_recurrence_asks_without_action_then_uses_requested_scope(tmp_path):
    actions,calendar=mutation_setup(tmp_path,[calendar_event(recurring=True)])
    args={"audience":"family","title":"rappel des poubelles","operation":"delete"}
    now=datetime(2026,10,29,12,0,tzinfo=timezone.utc)
    text="annule le rappel poubelles du calendrier familial"
    assert "prochaine occurrence" in actions.mutate(args,text,[],now=now)
    assert not calendar.calls
    history=[{"role":"user","content":text}]
    assert "supprimée" in actions.mutate({**args,"scope":"series"},"toute la série",history,now=now)
    assert calendar.calls[-1][0][1:]==("delete","a") and calendar.calls[-1][1]["recurrence_id"] is None


def test_single_recurrence_deletion_and_duplicate_titles(tmp_path):
    now=datetime(2026,10,29,12,0,tzinfo=timezone.utc)
    text="annule seulement la prochaine occurrence des poubelles du calendrier familial"
    args={"audience":"family","title":"poubelles","operation":"delete","scope":"one"}
    actions,calendar=mutation_setup(tmp_path,[calendar_event(recurring=True)])
    assert "supprimé" in actions.mutate(args,text,[],now=now)
    assert calendar.calls[-1][1]["recurrence_id"]=="20261105T190000"
    actions,calendar=mutation_setup(tmp_path,[calendar_event(uid="a"),calendar_event(uid="b")])
    assert "Plusieurs" in actions.mutate(args,text,[],now=now)
    assert not calendar.calls


def test_rename_preserves_description_and_rejects_fabricated_name(tmp_path):
    now=datetime(2026,10,29,12,0,tzinfo=timezone.utc)
    actions,calendar=mutation_setup(tmp_path,[calendar_event()])
    args={"audience":"family","title":"poubelles","operation":"update","new_title":"Sortir les bacs"}
    assert "nouveau nom" in actions.mutate(args,"modifie poubelles dans le calendrier familial",[],now=now)
    assert not calendar.calls
    result=actions.mutate(args,"modifie poubelles en Sortir les bacs dans le calendrier familial",[],now=now)
    assert "modifié" in result
    changed=calendar.calls[-1][1]["event"]
    assert changed["summary"]=="Sortir les bacs" and changed["description"]=="description fictive" and changed["location"]=="Bureau"


def test_negated_and_wrong_day_never_delete(tmp_path):
    now=datetime(2026,10,29,12,0,tzinfo=timezone.utc)
    actions,calendar=mutation_setup(tmp_path,[calendar_event()])
    args={"audience":"family","title":"poubelles","operation":"delete"}
    assert "Aucune action" in actions.mutate(args,"ne supprime pas les poubelles du calendrier familial",[],now=now)
    assert "date" in actions.mutate(args,"annule demain les poubelles du calendrier familial",[],now=now)
    assert not calendar.calls


def test_negative_followup_cannot_reuse_old_authorization(tmp_path):
    now=datetime(2026,10,29,12,0,tzinfo=timezone.utc)
    actions,calendar=mutation_setup(tmp_path,[calendar_event()])
    args={"audience":"family","title":"poubelles","operation":"delete"}
    history=[{"role":"user","content":"annule les poubelles du calendrier familial"}]
    assert "Aucune action" in actions.mutate(args,"non, laisse tomber",history,now=now)
    assert not calendar.calls


def test_delete_named_date_targets_correct_recurrence(tmp_path):
    now=datetime(2026,10,29,12,0,tzinfo=timezone.utc)
    first=calendar_event(recurring=True)
    second=calendar_event(recurring=True)
    second["start"]={"dateTime":"2026-11-12T19:00:00+01:00"}
    second["end"]={"dateTime":"2026-11-12T19:01:00+01:00"}
    second["recurrence_id"]="20261112T190000"
    actions,calendar=mutation_setup(tmp_path,[first,second])
    args={"audience":"family","title":"poubelles","operation":"delete","scope":"one"}
    reply=actions.mutate(args,"annule seulement les poubelles du 12 novembre dans le calendrier familial",[],now=now)
    assert "supprimé" in reply and calendar.calls[-1][1]["recurrence_id"]=="20261112T190000"
