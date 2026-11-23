import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from alfred.bells import TerminalBellController
from alfred.storage import Store
from alfred.terminal import DirectTerminal, TerminalConfig


NOW = datetime(2026, 11, 11, 12, tzinfo=timezone.utc)


class FakeTerminal:
    def __init__(self):
        self.bell_active = False
        self.bell_test = False
        self.calls = []
        self.fail = False

    async def set_bell(self, active):
        if self.fail:
            raise RuntimeError("réponse perdue")
        self.calls.append(active)
        self.bell_active = active


def make_store(tmp_path):
    store = Store(tmp_path)
    store.initialize()
    return store


def timer(store, floor="rdc"):
    return store.create(kind="timer", title="Test", due_at=NOW, floor_id=floor,
                        terminal_id="browser-test", now=NOW - timedelta(seconds=2))


def test_direct_bell_rings_once_and_stops_after_last_timer(tmp_path):
    store = make_store(tmp_path)
    terminal = FakeTerminal()
    bell = TerminalBellController(store, terminal, "rdc", clock=lambda: NOW.timestamp())
    first, second = timer(store), timer(store)
    other = timer(store, "etage1")
    store.tick(NOW)

    async def scenario():
        await bell.sync()
        await bell.sync()
        assert terminal.calls == [True]
        store.cancel(first["id"], NOW)
        await bell.sync()
        assert terminal.calls == [True]
        store.cancel(second["id"], NOW)
        await bell.sync()
        assert terminal.calls == [True, False]
        assert store.get(other["id"])["status"] == "ringing"
        assert bell.status() == {"active": False, "floor_id": "rdc", "error": None}

    asyncio.run(scenario())


def test_direct_bell_stops_on_shutdown_and_retries_a_lost_reply(tmp_path):
    store = make_store(tmp_path)
    terminal = FakeTerminal()
    now = [NOW.timestamp()]
    bell = TerminalBellController(store, terminal, "rdc", clock=lambda: now[0])
    timer(store)
    store.tick(NOW)
    terminal.fail = True

    async def scenario():
        await bell.sync()
        assert terminal.calls == [] and "non confirmée" in bell.status()["error"]
        now[0] += 2.1
        terminal.fail = False
        await bell.sync()
        assert terminal.calls == [True]
        await bell.sync(True)
        assert terminal.calls == [True, False]

    asyncio.run(scenario())


def test_direct_bell_ignores_a_manual_sound_test(tmp_path):
    store = make_store(tmp_path)
    terminal = FakeTerminal()
    terminal.bell_test = True
    bell = TerminalBellController(store, terminal, "rdc", clock=lambda: NOW.timestamp())
    timer(store)
    store.tick(NOW)

    asyncio.run(bell.sync())
    assert terminal.calls == []


def test_terminal_test_bell_uses_native_services_and_always_stops():
    async def scenario():
        calls = []

        async def execute(service, data):
            calls.append((service, data))

        terminal = DirectTerminal(
            TerminalConfig("board.local", "00:11:22:33:44:55", "192.168.77.24"),
            None, None)
        terminal.connected = True
        terminal.services = {"start_ringing": "start", "stop_ringing": "stop"}
        terminal.client = SimpleNamespace(execute_service=execute)
        await terminal.test_bell(seconds=0)
        assert calls == [("start", {}), ("stop", {})]
        assert terminal.bell_active is False and terminal.bell_test is False
        assert terminal.status()["bell"] == {"active": False, "test": False, "error": None}

    asyncio.run(scenario())




def test_terminal_bell_refuses_missing_firmware_service():
    async def scenario():
        terminal = DirectTerminal(
            TerminalConfig("board.local", "00:11:22:33:44:55", "192.168.77.24"),
            None, None)
        terminal.connected = True
        terminal.services = {}
        terminal.client = SimpleNamespace(execute_service=None)
        with pytest.raises(ValueError, match="absente|absent"):
            await terminal.set_bell(True)
        assert terminal.bell_active is False

    asyncio.run(scenario())
