from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest

from alfred.storage import ProcessLock, Store


NOW = datetime(2026, 10, 26, 18, 0, tzinfo=timezone.utc)


@pytest.fixture
def store(tmp_path):
    instance = Store(tmp_path)
    instance.initialize()
    return instance


def add(store, kind="timer", delay=30, floor="rdc"):
    return store.create(kind=kind, title="Échéance de test", due_at=NOW+timedelta(seconds=delay),
                        floor_id=floor, terminal_id="browser-test", now=NOW)


def test_restart_keeps_future_and_suppresses_late_delivery(store, tmp_path):
    expired_timer = add(store, delay=5)
    expired_reminder = add(store, kind="reminder", delay=5)
    future = add(store, delay=120)
    restarted = Store(tmp_path)
    restarted.initialize()
    assert restarted.recover(NOW+timedelta(seconds=60)) == 2
    assert restarted.get(expired_timer["id"])["status"] == "completed"
    assert restarted.get(expired_reminder["id"])["status"] == "missed"
    assert restarted.get(future["id"])["status"] == "pending"
    assert restarted.get(future["id"])["due_at"] == future["due_at"]
    assert restarted.recover(NOW+timedelta(seconds=60)) == 0


def test_restart_does_not_replay_existing_ringing_or_waiting(store):
    timer, reminder = add(store), add(store, kind="reminder")
    assert store.tick(NOW+timedelta(seconds=31)) == 2
    assert store.get(timer["id"])["status"] == "ringing"
    assert store.get(reminder["id"])["status"] == "awaiting_delivery"
    store.recover(NOW+timedelta(seconds=32))
    assert store.get(timer["id"])["status"] == "completed"
    assert store.get(reminder["id"])["status"] == "missed"


def test_stop_only_current_floor_ringing_timers(store):
    ground = add(store, floor="rdc")
    upstairs = add(store, floor="etage1")
    reminder = add(store, kind="reminder")
    future = add(store, delay=120)
    store.tick(NOW+timedelta(seconds=31))
    assert store.stop_floor("rdc", NOW+timedelta(seconds=32)) == 1
    assert store.get(ground["id"])["status"] == "completed"
    assert store.get(upstairs["id"])["status"] == "ringing"
    assert store.get(reminder["id"])["status"] == "awaiting_delivery"
    assert store.get(future["id"])["status"] == "pending"
    assert store.stop_floor("rdc") == 0


def test_concurrent_ticks_claim_each_due_item_once(store):
    add(store)
    with ThreadPoolExecutor(max_workers=4) as workers:
        counts = list(workers.map(lambda _: store.tick(NOW+timedelta(seconds=31)), range(4)))
    assert sum(counts) == 1


def test_cancellation_is_idempotent_and_survives_recovery(store):
    item = add(store)
    assert store.cancel(item["id"])["status"] == "cancelled"
    assert store.cancel(item["id"])["status"] == "cancelled"
    store.recover(NOW+timedelta(days=1))
    assert store.tick(NOW+timedelta(days=1)) == 0
    assert store.get(item["id"])["status"] == "cancelled"


def test_timezone_offsets_refer_to_same_instant(store):
    due = datetime(2026, 10, 26, 19, 0, tzinfo=timezone(timedelta(hours=1)))
    item = store.create(kind="timer", title="Fuseau", due_at=due, floor_id="rdc",
                        terminal_id="test", now=NOW-timedelta(seconds=2))
    assert store.tick(NOW-timedelta(seconds=1)) == 0
    assert store.tick(NOW) == 1
    assert store.get(item["id"])["status"] == "ringing"


def test_data_directory_cannot_have_two_schedulers(tmp_path):
    first, second = ProcessLock(tmp_path), ProcessLock(tmp_path)
    first.acquire()
    try:
        with pytest.raises(RuntimeError, match="déjà"):
            second.acquire()
    finally:
        first.release()
    second.acquire()
    second.release()


def test_unknown_schema_version_fails_without_rewriting(store):
    with store.connection() as db:
        db.execute("PRAGMA user_version=99")
    with pytest.raises(RuntimeError, match="Version"):
        store.initialize()
    with store.connection() as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 99
