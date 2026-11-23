from datetime import timedelta
import json
import time
import httpx
from fastapi.testclient import TestClient
from alfred.app import create_app
from alfred.config import Settings
from alfred.home_assistant import HomeService, HomeStore
from alfred.reminder_dispatch import ReminderDispatcher
from alfred.storage import Store, utc_now


def fixture(tmp_path, terminal="assist_satellite.bureau"):
    store=Store(tmp_path);store.initialize(); now=utc_now()
    reminder=store.create_reminder(title="Essai fictif",due_at=now+timedelta(seconds=1),floor_id="rdc",
        terminal_id=terminal,target_room="Bureau",audience="family",now=now)
    store.tick(now+timedelta(seconds=2))
    return store, reminder


def test_dispatch_is_attempted_once_and_never_claims_heard(tmp_path):
    store,reminder=fixture(tmp_path)
    class Announcements:
        def __init__(self): self.calls=[]
        def select(self,scope,target): return [{"entity_id":"assist_satellite.bureau"}]
        def send(self,*args): self.calls.append(args); return {"accepted":["Bureau"],"incomplete":False}
    transport=Announcements(); dispatcher=ReminderDispatcher(store,transport)
    dispatcher.sync(); dispatcher.sync()
    assert len(transport.calls)==1
    result=store.get(reminder["id"])
    assert result["status"]=="awaiting_delivery" and result["dispatch_phase"]=="sent"


def test_uncertain_failure_is_not_retried(tmp_path):
    store,reminder=fixture(tmp_path)
    class Announcements:
        def __init__(self): self.calls=0
        def select(self,*args): return [{"entity_id":"assist_satellite.bureau"}]
        def send(self,*args): self.calls+=1; raise TimeoutError()
    transport=Announcements(); dispatcher=ReminderDispatcher(store,transport)
    dispatcher.sync(); dispatcher.sync()
    assert transport.calls==1 and store.get(reminder["id"])["dispatch_phase"]=="failed"


def test_wrong_terminal_never_falls_back_to_another_room(tmp_path):
    store,reminder=fixture(tmp_path,terminal="assist_satellite.autre")
    class Announcements:
        def select(self,*args): return [{"entity_id":"assist_satellite.bureau"}]
        def send(self,*args): raise AssertionError("mauvaise destination")
    ReminderDispatcher(store,Announcements()).sync()
    assert store.get(reminder["id"])["dispatch_phase"]=="failed"


def test_scheduler_dispatches_reminder_only_to_requested_room(tmp_path):
    calls=[]
    def handler(request):
        calls.append(json.loads(request.content))
        return httpx.Response(200,json=[])
    config=HomeStore(tmp_path)
    config.save("http://192.168.77.21:8123", "faux-jeton-test-0123456789", "Bureau")
    home=HomeService(config,lambda:httpx.Client(transport=httpx.MockTransport(handler)))
    (tmp_path / "announcement-targets.json").write_text(json.dumps({"delivery_mode":"ha_pipeline","targets":[
        {"entity_id":"assist_satellite.bureau", "room":"Bureau", "floor":"rdc"},
        {"entity_id":"assist_satellite.chambre", "room":"Chambre", "floor":"etage1"}]}))
    with TestClient(create_app(Settings(tmp_path,poll_seconds=0.1,legacy_reminders=True),home_service=home)) as client:
        due=(utc_now()+timedelta(seconds=1)).isoformat()
        result=client.post("/api/reminders",json={"title":"Essai fictif","due_at":due,"floor_id":"rdc",
            "target_room":"Bureau","audience":"family"})
        assert result.status_code==201
        deadline=time.monotonic()+5
        while not calls and time.monotonic()<deadline: time.sleep(0.05)
        assert len(calls)==1 and calls[0]["entity_id"]=="assist_satellite.bureau"
        assert calls[0]["message"]=="Rappel : Essai fictif"
        deadline=time.monotonic()+2
        while time.monotonic()<deadline:
            item=next(x for x in client.get("/api/schedules").json()["items"] if x["id"]==result.json()["id"])
            if item["dispatch_phase"]=="sent": break
            time.sleep(0.05)
        assert item["dispatch_phase"]=="sent" and item["status"]=="awaiting_delivery"
