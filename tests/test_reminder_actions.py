from datetime import datetime, timedelta, timezone
from alfred.profiles import Profiles
from alfred.reminder_actions import ReminderActions
from alfred.storage import Store

NOW = datetime(2026,10,29,10,0,tzinfo=timezone.utc)


def setup(tmp_path):
    store=Store(tmp_path); store.initialize()
    profiles=Profiles(store); profile=profiles.create("Alex")
    class Terminals:
        def select(self,scope,room):
            return [{"room":"Bureau", "floor":"rdc", "entity_id":"assist_satellite.bureau"}] if room.lower()=="bureau" else []
    return ReminderActions(store,profiles,Terminals(),clock=lambda:NOW), store, profile


def args(**overrides):
    return {"title":"sortir les poubelles", "datetime_local":"2026-10-29T19:00", "recurrence":"weekly",
            "audience":"personal", "profile_name":"Alex", "room":"Bureau", **overrides}


def test_weekly_voice_reminder_is_persisted_without_claiming_delivery(tmp_path):
    actions,store,profile=setup(tmp_path)
    reply=actions.create(args(),"rappelle moi de sortir les poubelles tous les jeudis à 19h pour Alex dans le bureau",[])
    assert "enregistré" in reply and "demandée à l'échéance" in reply
    items=store.list()
    assert len(items)==1 and items[0]["owner_id"]==profile["id"] and items[0]["series_id"]
    assert items[0]["terminal_id"]=="assist_satellite.bureau"


def test_missing_or_invented_hour_and_name_never_create(tmp_path):
    actions,store,_=setup(tmp_path)
    assert "quelle heure" in actions.create(args(),"rappelle-moi de payer la facture demain",[]).lower()
    assert "confirmer l'heure" in actions.create(args(),"rappelle moi jeudi à 18h",[]).lower()
    assert "profil" in actions.create(args(profile_name=""),"rappelle moi jeudi à 19h",[]).lower()
    assert not store.list()


def test_family_requires_explicit_request_and_invalid_room_is_rejected(tmp_path):
    actions,store,_=setup(tmp_path)
    assert "famille" in actions.create(args(audience="family"),"rappelle moi jeudi à 19h",[]).lower()
    assert "terminal" in actions.create(args(room="Cuisine"),"rappelle Alex jeudi à 19h dans la cuisine",[]).lower()
    assert not store.list()


def test_followup_hour_can_be_used_without_inventing_date(tmp_path):
    actions,store,_=setup(tmp_path)
    result=actions.create(args(),"à 19h",[{"role":"user","content":"rappelle Alex tous les jeudis dans le bureau"}])
    assert "enregistré" in result and len(store.list())==1


def test_followup_does_not_mix_previous_reminder_date(tmp_path):
    actions,store,_=setup(tmp_path)
    prior = [{"role":"user","content":"rappelle Alex jeudi à 19h dans le bureau"},
             {"role":"assistant","content":"Rappel enregistré."},
             {"role":"user","content":"rappelle Alex de payer la facture demain dans le bureau"},
             {"role":"assistant","content":"À quelle heure ?"}]
    result=actions.create(args(title="payer la facture",datetime_local="2026-10-30T18:00",recurrence="once"),"à 18h",prior)
    assert "enregistré" in result and len(store.list())==1


def test_voice_creation_uses_bound_ha_calendar_not_local_store(tmp_path):
    actions,store,profile=setup(tmp_path)
    class Calendars:
        def __init__(self): self.calls=[]
        def create_reminder(self,*args,**kwargs): self.calls.append((args,kwargs))
    class Bindings:
        def personal(self,identifier):
            assert identifier==profile["id"]
            return "calendar.personnel"
        def family(self): return "calendar.familial"
    calendar=Calendars(); actions.calendars=calendar; actions.bindings=Bindings()
    reply=actions.create(args(),"rappelle Alex tous les jeudis à 19h dans le bureau",[])
    assert "Home Assistant" in reply
    assert calendar.calls[0][0][0]=="calendar.personnel" and calendar.calls[0][1]["recurrence"]=="weekly"
    assert store.list()==[]
