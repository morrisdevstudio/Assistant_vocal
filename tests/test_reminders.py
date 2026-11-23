from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import pytest
from fastapi.testclient import TestClient
from alfred.app import create_app
from alfred.config import Settings
from alfred.storage import Store, utc_now
from alfred.recurrence import next_weekly


def test_personal_and_family_reminders_are_persisted_with_scope(tmp_path):
    with TestClient(create_app(Settings(tmp_path, legacy_reminders=True))) as client:
        profile = client.post("/api/profiles", json={"name":"Profil test", "role":"adult"}).json()
        due = (utc_now() + timedelta(hours=1)).isoformat()
        body = {"title":"Rappel fictif", "due_at":due, "floor_id":"rdc", "target_room":"Bureau", "audience":"personal", "owner_id":profile["id"]}
        response = client.post("/api/reminders", json=body)
        assert response.status_code == 201
        personal = response.json()
        assert personal["owner_id"] == profile["id"] and personal["audience"] == "personal"
        assert personal["owner_name"] == "Profil test" and personal["status"] == "pending"
        assert client.delete("/api/profiles/" + profile["id"]).status_code == 422
        family = client.post("/api/reminders", json={**body, "audience":"family", "owner_id":None}).json()
        assert family["audience"] == "family" and family["owner_id"] is None
        assert len([x for x in client.get("/api/schedules").json()["items"] if x["audience"] in ("family", "personal")]) == 2
        assert client.post("/api/schedules/" + personal["id"] + "/cancel", json={}).json()["status"] == "cancelled"
        assert client.delete("/api/profiles/" + profile["id"]).status_code == 200
    with TestClient(create_app(Settings(tmp_path, legacy_reminders=True))) as restarted:
        items = restarted.get("/api/schedules").json()["items"]
        assert any(item["id"] == family["id"] and item["status"] == "pending" for item in items)


def test_reminder_requires_real_profile_and_explicit_room(tmp_path):
    with TestClient(create_app(Settings(tmp_path, legacy_reminders=True))) as client:
        body={"title":"Essai", "due_at":(utc_now()+timedelta(hours=1)).isoformat(),
              "floor_id":"rdc", "target_room":"Bureau", "audience":"personal", "owner_id":"inconnu"}
        assert client.post("/api/reminders", json=body).status_code == 422
        assert client.post("/api/reminders", json={**body, "target_room":""}).status_code == 422
        assert client.post("/api/reminders", json={**body, "audience":"family"}).status_code == 422
        assert client.get("/api/schedules").json()["items"] == []


def test_missed_personal_reminder_can_be_cancelled_before_profile_deletion(tmp_path):
    with TestClient(create_app(Settings(tmp_path, legacy_reminders=True))) as client:
        profile = client.post("/api/profiles", json={"name":"Profil test", "role":"adult"}).json()
        body={"title":"Essai", "due_at":(utc_now()+timedelta(hours=1)).isoformat(),
              "floor_id":"rdc", "target_room":"Bureau", "audience":"personal", "owner_id":profile["id"]}
        reminder = client.post("/api/reminders", json=body).json()
        Store(tmp_path).recover(utc_now()+timedelta(hours=2))
        assert client.delete("/api/profiles/"+profile["id"]).status_code == 422
        assert client.post("/api/schedules/"+reminder["id"]+"/cancel", json={}).json()["status"] == "cancelled"
        assert client.delete("/api/profiles/"+profile["id"]).status_code == 200


def test_weekly_next_occurrence_preserves_paris_wall_time_across_dst():
    paris = ZoneInfo("Europe/Paris")
    anchor = datetime(2026, 10, 22, 19, 0, tzinfo=paris)
    result = next_weekly(anchor, datetime(2026, 10, 22, 20, tzinfo=paris))
    assert result.astimezone(paris) == datetime(2026, 10, 29, 19, 0, tzinfo=paris)
    assert result.hour == 18  # passage UTC+2 vers UTC+1


def test_weekly_spring_gap_moves_to_first_valid_minute():
    paris = ZoneInfo("Europe/Paris")
    anchor = datetime(2027, 3, 21, 2, 30, tzinfo=paris)
    result = next_weekly(anchor, datetime(2027, 3, 21, 3, 0, tzinfo=paris))
    assert result.astimezone(paris).strftime("%Y-%m-%d %H:%M") == "2027-03-28 03:00"


def test_weekly_reminder_recovers_missed_and_schedules_next_without_replay(tmp_path):
    store = Store(tmp_path)
    store.initialize()
    due = datetime(2026, 10, 22, 17, 0, tzinfo=timezone.utc)
    reminder = store.create_reminder(title="Essai", due_at=due, floor_id="rdc", terminal_id="test",
                                     target_room="Bureau", audience="family", recurrence="weekly", now=due-timedelta(hours=1))
    assert store.recover(due+timedelta(days=2)) == 1
    assert store.get(reminder["id"])["status"] == "missed"
    items = store.list()
    upcoming = [item for item in items if item["status"] == "pending"]
    assert len(upcoming) == 1 and upcoming[0]["series_id"] == reminder["series_id"]
    assert datetime.fromisoformat(upcoming[0]["due_at"]) == datetime(2026,10,29,18,0,tzinfo=timezone.utc)
    assert store.recover(due+timedelta(days=2)) == 0
    assert len(store.list()) == 2
    store.cancel(upcoming[0]["id"], due+timedelta(days=2))
    store.tick(due+timedelta(days=30))
    assert not any(item["status"] == "pending" for item in store.list())


def test_weekly_running_scheduler_advances_once_and_keeps_missed_visible(tmp_path):
    store = Store(tmp_path)
    store.initialize()
    due = datetime(2026,10,22,17,0,tzinfo=timezone.utc)
    reminder = store.create_reminder(title="Essai", due_at=due, floor_id="rdc", terminal_id="test",
                                     target_room="Bureau", audience="family", recurrence="weekly", now=due-timedelta(hours=1))
    assert store.tick(due) == 1
    assert store.get(reminder["id"])["status"] == "awaiting_delivery"
    assert store.tick(due) == 0
    assert len([item for item in store.list() if item["status"] == "pending"]) == 1
    store.recover(due+timedelta(minutes=1))
    assert store.get(reminder["id"])["status"] == "missed"
    assert len([item for item in store.list() if item["status"] == "pending"]) == 1


def test_legacy_reminders_remain_preserved_and_inactive_by_default(tmp_path):
    store = Store(tmp_path)
    store.initialize()
    now = utc_now()
    old = store.create_reminder(title="Ancien test", due_at=now-timedelta(minutes=5), floor_id="rdc",
        terminal_id="web-admin", target_room="Bureau", audience="family", recurrence="weekly", now=now-timedelta(days=1))
    with TestClient(create_app(Settings(tmp_path,poll_seconds=0.05))) as client:
        item=next(item for item in client.get("/api/schedules").json()["items"] if item["id"]==old["id"])
        assert item["status"]=="pending"
        assert len(client.get("/api/schedules").json()["items"])==1
        body={"title":"Nouveau test", "due_at":(now+timedelta(hours=1)).isoformat(),
              "floor_id":"rdc", "target_room":"Bureau", "audience":"family"}
        assert client.post("/api/reminders",json=body).status_code==409
        legacy={"kind":"reminder","title":"Test","due_at":(now+timedelta(hours=1)).isoformat(),
                "floor_id":"rdc","terminal_id":"browser-test"}
        assert client.post("/api/schedules",json=legacy).status_code==409
        timer={"kind":"timer","title":"Test","duration_seconds":10,"floor_id":"rdc","terminal_id":"browser-test"}
        assert client.post("/api/schedules",json=timer).status_code==201
