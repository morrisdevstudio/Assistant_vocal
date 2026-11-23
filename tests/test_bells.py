import json
import time
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from fastapi.testclient import TestClient

from alfred.app import create_app
from alfred.bells import BellController, MAX_RING_SECONDS, read_targets
from alfred.config import Settings
from alfred.home_assistant import HomeError, HomeService, HomeStore
from alfred.storage import Store

START = "waveshare_voice_eb05fc_start_ringing"
STOP = "waveshare_voice_eb05fc_stop_ringing"
TARGET = {"floor_id": "rdc", "start_service": START, "stop_service": STOP}
NOW = datetime(2026, 10, 27, 12, tzinfo=timezone.utc)


class FakeHome:
    def __init__(self):
        self.calls = []
        self.fail_start = False
        self.fail_stop = False

    def status(self):
        return {"configured": True}

    def ring_action(self, service):
        self.calls.append(service)
        if (service == START and self.fail_start) or (service == STOP and self.fail_stop):
            raise HomeError("Service indisponible")


@pytest.fixture
def setup_bells(tmp_path):
    store = Store(tmp_path)
    store.initialize()
    home = FakeHome()
    clock = [NOW.timestamp()]
    bell = BellController(store, home, [TARGET], clock=lambda: clock[0])
    bell.initialize()
    return store, home, bell, clock


def make_timer(store, floor="rdc", due=NOW):
    return store.create(kind="timer", title="Test", due_at=due, floor_id=floor,
                        terminal_id="browser-test", now=NOW - timedelta(seconds=2))


def test_ring_once_per_floor_and_stop_only_after_last_active_timer(setup_bells):
    store, home, bell, clock = setup_bells
    first, second = make_timer(store), make_timer(store)
    other = make_timer(store, "etage1")
    store.tick(NOW)
    bell.sync(); bell.sync()
    assert home.calls == [START]
    store.cancel(first["id"], NOW)
    bell.sync()
    assert home.calls == [START]
    store.cancel(second["id"], NOW)
    bell.sync(); bell.sync()
    assert home.calls == [START, STOP]
    assert store.get(other["id"])["status"] == "ringing"
    assert bell.status()["targets"][0]["phase"] is None


def test_recovery_stops_previous_output_but_never_replays_expired_timer(setup_bells):
    store, home, bell, clock = setup_bells
    timer = make_timer(store)
    store.tick(NOW); bell.sync()
    assert home.calls == [START]
    store.recover(NOW + timedelta(seconds=1))
    restarted = BellController(store, home, [TARGET], clock=lambda: clock[0] + 1)
    restarted.initialize(); restarted.sync(); restarted.sync()
    assert home.calls == [START, STOP]
    assert store.get(timer["id"])["status"] == "completed"


def test_lost_start_reply_is_not_retried_and_stop_is_attempted(setup_bells):
    store, home, bell, clock = setup_bells
    home.fail_start = True
    timer = make_timer(store)
    store.tick(NOW); bell.sync(); bell.sync()
    assert home.calls == [START]
    assert "non confirmé" in bell.status()["targets"][0]["error"]
    store.cancel(timer["id"], NOW)
    bell.sync()
    assert home.calls == [START, STOP]


def test_failed_stop_retried_with_backoff_and_not_after_hardware_timeout(setup_bells):
    store, home, bell, clock = setup_bells
    timer = make_timer(store)
    store.tick(NOW); bell.sync()
    store.cancel(timer["id"], NOW)
    home.fail_stop = True
    bell.sync(); bell.sync()
    assert home.calls == [START, STOP]
    assert "Arrêt" in bell.status()["targets"][0]["error"]
    clock[0] += 6
    home.fail_stop = False
    bell.sync()
    assert home.calls == [START, STOP, STOP]
    assert bell._journal() == []
    other = make_timer(store)
    store.tick(NOW); bell.sync()
    store.cancel(other["id"], NOW)
    clock[0] += MAX_RING_SECONDS + 1
    calls = home.calls.copy()
    bell.sync()
    assert home.calls == calls and bell._journal() == []


def test_shutdown_stops_owned_sound_even_if_timer_is_still_ringing(setup_bells):
    store, home, bell, clock = setup_bells
    make_timer(store); store.tick(NOW); bell.sync()
    bell.sync(stop_all=True)
    assert home.calls == [START, STOP]


def test_new_due_timer_after_firmware_cutoff_can_ring_without_replaying_old_one(setup_bells):
    store, home, bell, clock = setup_bells
    make_timer(store); store.tick(NOW); bell.sync()
    clock[0] += MAX_RING_SECONDS + 1
    bell.sync(); bell.sync()
    assert home.calls == [START]
    assert bell.status()["targets"][0]["phase"] == "expired"
    later = NOW + timedelta(seconds=MAX_RING_SECONDS + 2)
    make_timer(store, due=later)
    clock[0] += 1
    store.tick(later); bell.sync(); bell.sync()
    assert home.calls == [START, START]


def test_ha_action_uses_existing_token_and_no_implicit_target(tmp_path):
    calls = []
    store = HomeStore(tmp_path, base_url="http://home.invalid", token="fake-token")
    client = HomeService(store, lambda: httpx.Client(transport=httpx.MockTransport(
        lambda request: (calls.append(request), httpx.Response(200, json=[]))[1])))
    client.ring_action(START)
    assert calls[0].url.path == "/api/services/esphome/" + START
    assert json.loads(calls[0].content) == {}
    assert calls[0].headers["authorization"] == "Bearer fake-token"
    with pytest.raises(HomeError):
        client.ring_action("../invalid")
    assert len(calls) == 1


def test_config_is_explicit_and_rejects_unsafe_service_and_duplicate(tmp_path):
    path = tmp_path / "bell-targets.json"
    assert read_targets(path) == []
    path.write_text(json.dumps({"targets": [{"floor_id": "rdc", "start_service": START}]}))
    assert read_targets(path) == [TARGET]
    for targets in ([{"floor_id": "rdc", "start_service": "../start_ringing"}],
                    [{"floor_id": "unknown", "start_service": START}],
                    [{"floor_id": "rdc", "start_service": START}] * 2):
        path.write_text(json.dumps({"targets": targets}))
        with pytest.raises(ValueError):
            read_targets(path)


def test_real_scheduler_triggers_and_stops_once_via_simulated_ha(tmp_path):
    (tmp_path / "bell-targets.json").write_text(json.dumps({"targets": [
        {"floor_id": "rdc", "start_service": START}]}))
    home = FakeHome()
    with TestClient(create_app(Settings(tmp_path, poll_seconds=0.05), home_service=home)) as client:
        response = client.post("/api/schedules", json={"kind": "timer", "title": "Test",
                               "duration_seconds": 1, "floor_id": "rdc", "terminal_id": "browser-test"})
        assert response.status_code == 201
        deadline = time.monotonic() + 4
        # L'appel simulé est visible avant que le worker ait validé son journal.
        # Attendre l'état publié, pas seulement l'entrée dans le faux client HA.
        while time.monotonic() < deadline:
            status = client.get("/api/status").json()["bells"]["targets"][0]
            if START in home.calls and status["phase"] == "sent":
                break
            time.sleep(0.05)
        assert home.calls == [START]
        assert client.get("/api/status").json()["bells"]["targets"][0]["phase"] == "sent"
        client.post("/api/stop", json={"floor_id": "rdc"})
        deadline = time.monotonic() + 3
        while STOP not in home.calls and time.monotonic() < deadline:
            time.sleep(0.05)
        assert home.calls == [START, STOP]
