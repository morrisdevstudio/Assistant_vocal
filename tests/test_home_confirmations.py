"""Confirmations locales : aucune écriture avant un oui explicite."""

import json
import threading

import httpx
import pytest
from fastapi.testclient import TestClient

from alfred.app import create_app
from alfred.config import Settings
from alfred.home_assistant import HomeService, HomeStore
from alfred.home_catalog import HomeCatalog
from alfred.home_confirmations import (ConfirmationError, HomeConfirmations,
                                       PendingConfirmations)
from alfred.intent_context import CURRENT_TURN, Turn
from alfred.intents import IntentService


class Speech:
    def status(self):
        return {"stt_available": True, "tts_available": True}

    def speak(self, text):
        return b"audio", 1


class Model:
    def __init__(self):
        self.received = []

    def status(self):
        return {"configured": True, "access_verified": True}

    def stream(self, text, session, cancelled):
        self.received.append(text)
        yield {"type": "answer", "text": "Réponse du modèle.", "llm_ms": 1}


def setup_home(tmp_path, monkeypatch, domain="switch", name="Imprimante", state="off", sensitive=True, attrs=None):
    entity = domain + ".test"
    attrs = dict(attrs or {})
    item = {"entity_id": entity, "domain": domain, "name": name, "allowed": True,
            "area": "Bureau", "members": None, "aliases": ["mon appareil"],
            "ha_aliases": [], "attributes": attrs,
            "confirmation_required": sensitive}
    items = [item]
    current = {"entity_id": entity, "state": state, "attributes": attrs.copy()}
    calls = []

    def respond(request):
        calls.append(request)
        if request.method == "GET":
            return httpx.Response(200, json=current)
        data = json.loads(request.content or b"{}")
        action = request.url.path.rsplit("/", 1)[-1]
        if action in {"turn_on", "turn_off"}:
            current["state"] = "on" if action == "turn_on" else "off"
        return httpx.Response(200, json=[])

    home = HomeService(HomeStore(tmp_path, base_url="http://ha.test:8123", token="fake", room="Bureau"),
                       lambda: httpx.Client(transport=httpx.MockTransport(respond)))
    cat = {"entities": items, "excluded": [], "aliases": {},
           "confirmations": [entity] if sensitive else []}
    monkeypatch.setattr(HomeCatalog, "snapshot", lambda self: cat)
    return home, calls, current


def writes(calls):
    return [request for request in calls if request.method == "POST"]


def in_session(home, text, session="session-confirm-001"):
    turn = Turn(("browser", session, "guest"), text, threading.Event())
    token = CURRENT_TURN.set(turn)
    try:
        return home.handle(text)
    finally:
        CURRENT_TURN.reset(token)


def test_store_validation_and_pending_expiry(tmp_path):
    store = HomeConfirmations(tmp_path)
    assert store.save(["switch.a", "switch.a"]) == ["switch.a"]
    with pytest.raises(ConfirmationError):
        store.save(["../invalid"])
    (tmp_path / "home-confirmations.json").write_text("not-json", encoding="utf-8")
    with pytest.raises(ConfirmationError):
        HomeConfirmations(tmp_path).load()

    now = [0]
    pending = PendingConfirmations(clock=lambda: now[0], ttl=30)
    pending.propose(("browser", "s"), {"kind": "device"}, "question")
    assert pending.peek(("browser", "s")) is not None
    now[0] = 31
    assert pending.peek(("browser", "s")) is None


def test_sensitive_switch_requires_one_explicit_yes(tmp_path, monkeypatch):
    home, calls, current = setup_home(tmp_path, monkeypatch)
    result = in_session(home, "allume l'imprimante")
    assert result["status"] == "confirmation"
    assert result["reply"] == "Voulez-vous vraiment allumer Imprimante ?"
    assert not writes(calls) and current["state"] == "off"

    result = in_session(home, "oui")
    assert "activé" in result["reply"]
    assert [request.url.path for request in writes(calls)] == ["/api/services/switch/turn_on"]
    assert current["state"] == "on"


def test_no_and_unrelated_phrase_never_write(tmp_path, monkeypatch):
    home, calls, current = setup_home(tmp_path, monkeypatch)
    assert in_session(home, "éteins imprimante")["status"] == "confirmation"
    assert in_session(home, "non")["status"] == "cancelled"
    assert not writes(calls) and current["state"] == "off"

    assert in_session(home, "allume imprimante")["status"] == "confirmation"
    assert in_session(home, "quelle heure est-il") is None
    assert in_session(home, "oui") is None
    assert not writes(calls)


def test_pending_is_isolated_by_session_and_expires(tmp_path, monkeypatch):
    home, calls, _ = setup_home(tmp_path, monkeypatch)
    assert in_session(home, "allume imprimante", "session-a-0000001")["status"] == "confirmation"
    assert in_session(home, "oui", "session-b-0000002") is None
    assert not writes(calls)
    assert "activé" in in_session(home, "oui", "session-a-0000001")["reply"]
    assert len(writes(calls)) == 1

    now = [0]
    home.pending = PendingConfirmations(clock=lambda: now[0], ttl=30)
    assert in_session(home, "éteins imprimante", "session-c-0000003")["status"] == "confirmation"
    now[0] = 31
    assert in_session(home, "oui", "session-c-0000003") is None
    assert len(writes(calls)) == 1


def test_reads_are_direct_and_button_needs_confirmation(tmp_path, monkeypatch):
    home, calls, _ = setup_home(tmp_path, monkeypatch, domain="input_button", name="Routine", state="unknown")
    result = in_session(home, "appuie sur routine")
    assert result["status"] == "confirmation" and not writes(calls)
    assert in_session(home, "oui")["reply"] == "Appui envoyé à Home Assistant."
    assert [request.url.path for request in writes(calls)] == ["/api/services/input_button/press"]

    home, calls, _ = setup_home(tmp_path, monkeypatch, domain="switch", name="Imprimante", state="on")
    result = in_session(home, "quel est l'état de imprimante")
    assert result["reply"] and not writes(calls)


def test_numeric_helper_requires_confirmation_too(tmp_path, monkeypatch):
    home, calls, _ = setup_home(tmp_path, monkeypatch, domain="input_number", name="Seuil",
                               state="20", attrs={"min": 0, "max": 100, "step": 1})
    result = in_session(home, "règle seuil à vingt et un")
    assert result["status"] == "confirmation" and not writes(calls)
    assert in_session(home, "oui")["reply"]
    assert [request.url.path for request in writes(calls)] == ["/api/services/input_number/set_value"]


def test_catalog_api_round_trip(tmp_path, monkeypatch):
    home = HomeService(HomeStore(tmp_path, base_url="http://ha.test:8123", token="fake", room="Bureau"))

    def snapshot(self):
        return {"entities": [], "excluded": [], "aliases": {},
                "confirmations": self.settings.load()["confirmations"], "synchronized": True}

    monkeypatch.setattr(HomeCatalog, "snapshot", snapshot)
    app = create_app(Settings(tmp_path), home_service=home, voice_service=Speech())
    with TestClient(app) as client:
        response = client.put("/api/home/confirmations", json=["switch.imprimante"])
        assert response.status_code == 200
        assert response.json()["confirmations"] == ["switch.imprimante"]
        catalog = client.get("/api/home/catalog").json()
        assert catalog["confirmations"] == ["switch.imprimante"]
        assert client.put("/api/home/confirmations", json=["bad"]).status_code == 422


def test_ai_device_tool_returns_question_then_local_yes_executes(tmp_path, monkeypatch):
    home, calls, current = setup_home(tmp_path, monkeypatch)
    service = IntentService(home, tmp_path)
    home.intent_service = service
    service.enabled = lambda family="lights": True
    turn = Turn(("browser", "session-ai-000001", "guest"), "allume imprimante", threading.Event())
    token = CURRENT_TURN.set(turn)
    try:
        reply = service.run_tools([("controler_appareil", {
            "operation": "turn_on", "target": "imprimante"})], threading.Event())
        assert reply == "Voulez-vous vraiment allumer Imprimante ?"
        assert not writes(calls) and current["state"] == "off"
        result = home.handle("oui")
        assert "activé" in result["reply"]
    finally:
        CURRENT_TURN.reset(token)
    assert current["state"] == "on"
    assert len(writes(calls)) == 1


def test_conversation_yes_bypasses_configured_model(tmp_path, monkeypatch):
    home, calls, current = setup_home(tmp_path, monkeypatch)
    model = Model()
    home.pending.propose(("browser", "session-app-000001"),
                         {"kind": "device", "operation": "turn_on",
                          "target": "switch.test", "value": None},
                         "Voulez-vous vraiment allumer Imprimante ?")
    app = create_app(Settings(tmp_path), home_service=home, voice_service=Speech(),
                     conversation_service=model)
    with TestClient(app) as client:
        response = client.post("/api/conversation/text", json={
            "text": "oui", "session_id": "session-app-000001"})
        rows = [json.loads(line) for line in response.text.splitlines()]
        assert rows[-1]["type"] == "done"
    assert model.received == []
    assert current["state"] == "on"
    assert len(writes(calls)) == 1


def test_home_command_route_keeps_confirmation_in_the_same_session(tmp_path, monkeypatch):
    home, calls, current = setup_home(tmp_path, monkeypatch)
    app = create_app(Settings(tmp_path), home_service=home, voice_service=Speech())
    with TestClient(app) as client:
        first = client.post("/api/home/command", json={
            "text": "allume imprimante", "session_id": "home-session-000001"})
        assert first.status_code == 200
        assert first.json()["status"] == "confirmation"
        assert not writes(calls)
        second = client.post("/api/home/command", json={
            "text": "oui", "session_id": "home-session-000001"})
        assert second.status_code == 200
        assert "activé" in second.json()["reply"]
    assert current["state"] == "on"
    assert len(writes(calls)) == 1
