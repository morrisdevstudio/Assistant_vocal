from datetime import datetime, timedelta, timezone
import json
import time
import httpx
from fastapi.testclient import TestClient
from alfred.app import create_app
from alfred.config import Settings
from alfred.calendar_reminder_monitor import CalendarReminderMonitor
from alfred.ha_calendar import reminder_marker
from alfred.home_assistant import HomeStore, HomeService
from alfred.profiles import Profiles
from alfred.storage import Store, utc_now

NOW=datetime(2026,10,29,12,0,tzinfo=timezone.utc)


def setup(tmp_path, events):
    store=Store(tmp_path);store.initialize()
    with store.connection() as db:
        db.execute("INSERT INTO profiles VALUES (?, ?, ?, ?, ?)", ("person","Profil test","adult",NOW.timestamp(),NOW.timestamp()))
    class Bindings:
        def load(self): return {"personal":{"person":"calendar.personnel"},"family":"calendar.familial"}
    class Calendar:
        def events(self, entity, start, end): return events.get(entity,[])
    class Announcements:
        def __init__(self): self.calls=[]
        def select(self, scope, room): return [{"entity_id":"assist_satellite.bureau"}] if room=="Bureau" else []
        def send(self, message, scope, room): self.calls.append((message,room)); return {"accepted":[room],"incomplete":False}
    transport=Announcements()
    monitor=CalendarReminderMonitor(store,Calendar(),Bindings(),transport,clock=lambda:NOW)
    return store,monitor,transport


def event(start, description):
    return {"summary":"Essai fictif", "start":start.isoformat(), "description":description}


def test_only_marked_events_are_announced_once(tmp_path):
    marker=reminder_marker("Bureau")
    events={"calendar.personnel":[event(NOW+timedelta(seconds=3), marker),event(NOW+timedelta(seconds=4),"Rendez-vous ordinaire")]}
    store,monitor,transport=setup(tmp_path,events)
    monitor.sync(startup=True)
    monitor.clock=lambda:NOW+timedelta(seconds=6)
    monitor.sync();monitor.sync()
    assert transport.calls==[("Rappel : Essai fictif","Bureau")]
    with store.connection() as db:
        rows=db.execute("SELECT phase FROM calendar_reminder_journal").fetchall()
    assert [r["phase"] for r in rows]==["sent"]


def test_restart_records_missed_without_late_announcement(tmp_path):
    events={"calendar.familial":[event(NOW+timedelta(seconds=3),reminder_marker("Bureau"))]}
    store,monitor,transport=setup(tmp_path,events)
    monitor.sync(startup=True)
    monitor.clock=lambda:NOW+timedelta(days=1)
    monitor.sync(startup=True);monitor.sync()
    assert transport.calls==[] and monitor.status()["missed"]==1


def test_failed_or_ambiguous_destination_is_not_retried(tmp_path):
    events={"calendar.familial":[event(NOW+timedelta(seconds=3),reminder_marker("Salon"))]}
    store,monitor,transport=setup(tmp_path,events)
    monitor.sync(startup=True)
    monitor.clock=lambda:NOW+timedelta(seconds=6)
    monitor.sync();monitor.sync()
    assert transport.calls==[] and monitor.status()["unconfirmed"]==1


def test_marker_cannot_leak_into_another_calendar(tmp_path):
    marker=reminder_marker("Bureau")
    events={"calendar.non_configure":[event(NOW+timedelta(seconds=3),marker)]}
    _,monitor,transport=setup(tmp_path,events)
    monitor.sync(startup=True);monitor.clock=lambda:NOW+timedelta(seconds=5);monitor.sync()
    assert not transport.calls


def test_failed_startup_read_still_treats_old_event_as_missed(tmp_path):
    events={"calendar.personnel":[event(NOW+timedelta(seconds=3),reminder_marker("Bureau"))]}
    store,monitor,transport=setup(tmp_path,events)
    monitor.sync(startup=True)
    original=monitor.calendar.events
    def unavailable(entity,start,end): raise ConnectionError("indisponible")
    monitor.calendar.events=unavailable
    monitor.clock=lambda:NOW+timedelta(seconds=5)
    monitor.sync(startup=True)
    monitor.calendar.events=original
    monitor.clock=lambda:NOW+timedelta(seconds=8)
    monitor.sync()
    assert not transport.calls and monitor.status()["missed"]==1


def test_lost_announcement_response_is_never_retried(tmp_path):
    events={"calendar.familial":[event(NOW+timedelta(seconds=3),reminder_marker("Bureau"))]}
    store,monitor,transport=setup(tmp_path,events)
    def failing_send(message,scope,room):
        transport.calls.append((message,room))
        raise TimeoutError("réponse perdue")
    transport.send=failing_send
    monitor.sync(startup=True); monitor.clock=lambda:NOW+timedelta(seconds=5)
    monitor.sync(); monitor.clock=lambda:NOW+timedelta(seconds=9); monitor.sync()
    assert len(transport.calls)==1 and monitor.status()["unconfirmed"]==1


def test_api_creates_in_ha_and_scheduler_announces_only_marked_event(tmp_path):
    store=Store(tmp_path);store.initialize(); owner=Profiles(store).create("Profil fictif")
    (tmp_path/"calendar-targets.json").write_text(json.dumps({"personal":{owner["id"]:"calendar.personnel"},"family":"calendar.familial"}))
    (tmp_path/"announcement-targets.json").write_text(json.dumps({"delivery_mode":"ha_pipeline","targets":[
        {"entity_id":"assist_satellite.bureau","room":"Bureau","floor":"rdc"}]}))
    calls=[]
    def handler(request):
        calls.append(json.loads(request.content))
        return httpx.Response(200,json=[])
    home_store=HomeStore(tmp_path);home_store.save("http://192.168.77.21:8123","jeton-fictif-0123456789","Bureau")
    home=HomeService(home_store,lambda:httpx.Client(transport=httpx.MockTransport(handler)))
    class FakeCalendar:
        def __init__(self): self.records=[]
        def create_reminder(self, entity, title, start, room, *, recurrence):
            self.records.append((entity,{"summary":title,"start":start.isoformat(),"description":reminder_marker(room)}))
        def events(self, entity, start, end): return [r for e,r in self.records if e==entity]
    calendar=FakeCalendar()
    with TestClient(create_app(Settings(tmp_path,poll_seconds=0.05),home_service=home,calendar_service=calendar)) as client:
        due=(utc_now()+timedelta(seconds=2)).isoformat()
        result=client.post("/api/calendar-reminders",json={"title":"Essai fictif", "due_at":due, "floor_id":"rdc",
            "target_room":"Bureau", "audience":"personal", "owner_id":owner["id"], "recurrence":"weekly"})
        assert result.status_code==201 and calendar.records[0][0]=="calendar.personnel"
        assert client.get("/api/schedules").json()["items"]==[]
        deadline=time.monotonic()+7
        while not calls and time.monotonic()<deadline: time.sleep(0.05)
        assert len(calls)==1 and calls[0]["entity_id"]=="assist_satellite.bureau"
        assert calls[0]["message"]=="Rappel : Essai fictif"

        family = {"title": "Rappel familial fictif", "floor_id": "rdc", "target_room": "Bureau",
                  "due_at": (utc_now() + timedelta(minutes=15)).isoformat()}
        assert client.post("/api/calendar-reminders/family", json={**family, "owner_id": owner["id"]}).status_code == 422
        assert client.post("/api/calendar-reminders/family", json=family).status_code == 201
        assert calendar.records[-1][0] == "calendar.familial"
        calendar.records.append(("calendar.familial", {"summary": "Événement ordinaire", "start": family["due_at"]}))
        visible = client.get("/api/calendar-reminders/family").json()
        assert [item["title"] for item in visible["items"]] == [family["title"]]
        assert visible["targets"] == [{"room": "Bureau", "floor_id": "rdc"}]
