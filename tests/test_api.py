import json
import time
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from alfred.app import create_app
from alfred.config import Settings
from alfred.storage import utc_now


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(Settings(tmp_path, poll_seconds=0.02, legacy_reminders=True))) as instance:
        yield instance


def timer(**overrides):
    return {"kind":"timer", "title":"Pâtes", "duration_seconds":30,
            "floor_id":"rdc", "terminal_id":"browser-test", **overrides}


def test_api_lifecycle_and_truthful_capabilities(client):
    assert client.get("/health").json()["status"] == "ok"
    status = client.get("/api/status").json()
    assert status["capabilities"]["schedules"]
    assert not status["capabilities"]["home_assistant"]
    assert not status["capabilities"]["stt"]
    response = client.post("/api/schedules", json=timer())
    assert response.status_code == 201
    item = response.json()
    assert client.get("/api/schedules").json()["items"][0]["id"] == item["id"]
    assert client.post(f"/api/schedules/{item['id']}/cancel", json={}).json()["status"] == "cancelled"
    assert client.post("/api/schedules/missing/cancel", json={}).status_code == 404


def test_web_timers_are_shared_by_floor_and_cannot_cancel_reminders(client):
    body = {"title": "Cuisson", "duration_seconds": 60, "floor_id": "etage1"}
    created = client.post("/api/timers", json=body)
    assert created.status_code == 201
    timer_id = created.json()["id"]
    reminder = client.post("/api/schedules", json={
        "kind": "reminder", "title": "Rappel fictif", "terminal_id": "test",
        "due_at": (utc_now() + timedelta(minutes=10)).isoformat(), "floor_id": "etage1",
    }).json()
    assert client.get("/api/timers?floor_id=rdc").json()["items"] == []
    assert [item["id"] for item in client.get("/api/timers?floor_id=etage1").json()["items"]] == [timer_id]
    assert client.post(f"/api/timers/{reminder['id']}/cancel", json={}).status_code == 404
    assert client.post(f"/api/timers/{timer_id}/cancel", json={}).json()["status"] == "cancelled"
    assert client.get("/api/timers?floor_id=etage1").json()["items"] == []


@pytest.mark.parametrize("override", [
    {"duration_seconds":0}, {"duration_seconds":True}, {"duration_seconds":1.2},
    {"duration_seconds":604801}, {"duration_seconds":None}, {"title":"   "},
    {"floor_id":"inconnu"}, {"terminal_id":""}, {"terminal_id":"../test"},
    {"kind":"reminder"}, {"unexpected":"value"}, {"due_at":"2026-10-26T18:00:00Z"},
])
def test_invalid_timer_never_persists(client, override):
    assert client.post("/api/schedules", json=timer(**override)).status_code == 422
    assert client.get("/api/schedules").json()["items"] == []


@pytest.mark.parametrize("due", ["2026-10-26T20:00:00", "not-a-date", "2000-01-01T00:00:00Z"])
def test_reminder_rejects_naive_invalid_and_past_dates(client, due):
    body = {"kind":"reminder", "title":"Test", "floor_id":"rdc", "terminal_id":"browser-test", "due_at":due}
    assert client.post("/api/schedules", json=body).status_code == 422


def test_reminder_keeps_explicit_destination_and_awaits_real_delivery(client):
    due = utc_now()+timedelta(seconds=1)
    body = {"kind":"reminder", "title":"Test", "floor_id":"rdc", "terminal_id":"browser-test",
            "due_at":due.isoformat(), "target_room":"Salon"}
    response = client.post("/api/schedules", json=body)
    assert response.status_code == 201
    assert response.json()["target_room"] == "Salon"
    deadline = time.monotonic()+3
    while time.monotonic() < deadline:
        item = client.get("/api/schedules").json()["items"][0]
        if item["status"] == "awaiting_delivery":
            break
        time.sleep(0.03)
    assert item["status"] == "awaiting_delivery"


def test_future_timer_survives_app_restart(tmp_path):
    settings = Settings(tmp_path)
    with TestClient(create_app(settings)) as first:
        item = first.post("/api/schedules", json=timer()).json()
    with TestClient(create_app(settings)) as second:
        saved = second.get("/api/schedules").json()["items"][0]
        assert saved["id"] == item["id"]
        assert saved["due_at"] == item["due_at"]
        assert saved["status"] == "pending"


def test_rejects_cross_origin_forms_and_unknown_host(client):
    assert client.post("/api/schedules", json=timer(), headers={"Origin":"https://other.example"}).status_code == 403
    assert client.post("/api/stop", data={"floor_id":"rdc"}).status_code == 415
    assert client.get("/", headers={"Host":"other.example"}).status_code == 400
    assert client.post("/api/stop", json={"floor_id":"rdc"}, headers={"Origin":"http://testserver"}).status_code == 200


def test_lan_development_host_is_explicit_and_cross_origin_still_rejected(tmp_path):
    with TestClient(create_app(Settings(tmp_path, listen_host="192.168.77.24")),
                    base_url="http://192.168.77.24:8765") as client:
        assert client.get("/").status_code == 200
        assert client.get("/health").json()["status"] == "ok"
        assert client.post("/api/schedules", json=timer(),
                           headers={"Origin": "http://192.168.77.24:8765"}).status_code == 201
        assert client.post("/api/stop", json={"floor_id": "rdc"},
                           headers={"Origin": "http://other.example"}).status_code == 403
        assert client.get("/", headers={"Host": "other.example"}).status_code == 400


def test_local_page_assets_and_degraded_health(client):
    page = client.get("/")
    assert page.status_code == 200
    assert "<title>Alfred" in page.text and 'id="chat-form"' in page.text
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/music-panel.js").status_code == 200
    assert client.get("/static/style.css").status_code == 200
    assert client.get("/static/app.js?versioned-test").headers["cache-control"] == "public, max-age=3600"
    assert client.get("/static/app.js").headers["cache-control"] == "no-store"
    assert client.get("/api/status").headers["cache-control"] == "no-store"
    client.app.state.scheduler_ok = False
    assert client.get("/health").status_code == 503


def test_terminal_status_separates_supervision_from_private_exchange(client):
    terminal = client.app.state.terminal
    terminal.connected = True
    terminal.phase = "idle"
    payload = client.get("/api/terminal/status").json()
    assert payload["health"]["status"] == "ok"
    assert payload["health"]["components"]["transport"] == "ok"
    assert "Texte privé" not in json.dumps(payload)
