import json
import threading

import httpx
import pytest
from fastapi.testclient import TestClient

from alfred.app import create_app
from alfred.config import Settings
from alfred.home_assistant import (HomeError, HomeService, HomeStore, parse_light_command)
from alfred.credentials import ConfigurationError

TOKEN = "jeton-de-test-fictif-0123456789"
URL = "http://192.168.77.21:8123"


def states(off_names=("light.salon_plafond",), on_names=("light.cuisine", "light.hall")):
    items = [{"entity_id": name, "state": "off"} for name in off_names]
    items += [{"entity_id": name, "state": "on"} for name in on_names]
    items.append({"entity_id": "switch.prise", "state": "on"})
    return items


def handler(calls, area=("light.salon_plafond", "light.salon_lampe")):
    current = {x["entity_id"]: x for x in states()}
    current["light.salon_lampe"] = {"entity_id": "light.salon_lampe", "state": "on"}
    current["light.a"] = {"entity_id": "light.a", "state": "off"}
    def respond(request):
        calls.append(request)
        path = request.url.path
        if path == "/api/config":
            return httpx.Response(200, json={"location_name": "Maison", "version": "2026.10"})
        if path == "/api/states":
            return httpx.Response(200, json=states())
        if path.startswith("/api/states/"):
            return httpx.Response(200, json=current.get(path.rsplit("/", 1)[-1], {}))
        if path == "/api/template":
            return httpx.Response(200, json=list(area))
        if path.startswith("/api/services/light/"):
            data = json.loads(request.content)
            for entity in data["entity_id"]:
                current[entity] = {"entity_id": entity, "state": "on" if path.endswith("turn_on") else "off"}
            return httpx.Response(200, json=[])
        return httpx.Response(404, json={"message": "absent"})
    return respond


def service(tmp_path, respond=None, room="Salon"):
    store = HomeStore(tmp_path)
    store.save(URL, TOKEN, room)
    calls = []
    transport = httpx.MockTransport(respond or handler(calls))
    home = HomeService(store, lambda: httpx.Client(transport=transport))
    return home, calls


@pytest.fixture(autouse=True)
def fake_catalog(monkeypatch):
    from alfred.home_catalog import HomeCatalog
    names = ["light.salon_plafond", "light.salon_lampe", "light.cuisine", "light.hall", "light.a"]
    monkeypatch.setattr(HomeCatalog, "snapshot", lambda self: {"entities": [
        {"entity_id": name, "allowed": True, "members": None} for name in names]})


@pytest.mark.parametrize("text,expected", [
    ("Éteins toutes les lumières", (False, "all", None)),
    ("eteins toutes les lampes", (False, "all", None)),
    ("Allume toutes les lumières", (True, "all", None)),
    ("Éteins les lumières du salon", (False, "room", "salon")),
    ("allume la lumière de la chambre", (True, "room", "chambre")),
    ("éteins la lumière", (False, "current", None)),
    ("allume la lampe", (True, "current", None)),
    ("Éteins la lumière s'il te plaît", (False, "current", None)),
    ("Alfred, éteins toutes les lumières partout", (False, "all", None)),
    ("éteins toutes les lumières de la maison", (False, "all", None)),
])
def test_parse_light_commands(text, expected):
    command = parse_light_command(text)
    assert command and (command.turn_on, command.scope, command.room) == expected


@pytest.mark.parametrize("text", [
    "allume la télé", "éteins tout", "mets Airbourne sur l'ampli",
    "quelle heure est-il", "éteins le four", "", "allume",
    "éteins la lumière s'il te plaît et raconte une blague sur les chats",
])
def test_non_light_requests_are_not_commands(text):
    assert parse_light_command(text) is None


@pytest.mark.parametrize("prefix", [
    "Hé Alfred", "hé alfred", "Eh Alfred", "Hey Alfred", "hey alfred",
    "Et Alfred", "Alors Alfred", "Euh Alfred", "hé, Alfred", "Hé Alfred,", "Alexa", "Alexa,", "Jarvis", "Jarvis,", "Jarvisse", "Hé Jarvis",
])
@pytest.mark.parametrize("phrase,expected", [
    ("allume la lumière", (True, "current", None)),
    ("éteins toutes les lumières", (False, "all", None)),
    ("allume la lumière du salon", (True, "room", "salon")),
])
def test_wake_word_prefix_is_stripped_from_light_commands(prefix, phrase, expected):
    command = parse_light_command(f"{prefix} {phrase}")
    assert command and (command.turn_on, command.scope, command.room) == expected


def test_token_is_encrypted_and_never_public(tmp_path):
    store = HomeStore(tmp_path)
    assert not store.public()["configured"]
    store.save(URL, TOKEN, "Bureau")
    assert store.values() == (URL, TOKEN, "Bureau")
    assert TOKEN not in json.dumps(store.public())
    assert TOKEN.encode() not in store.path.read_bytes()
    with pytest.raises(ConfigurationError):
        store.save(URL, "", "Bureau")


def test_check_counts_lights_without_leaking_token(tmp_path):
    home, calls = service(tmp_path)
    result = home.check()
    assert result == {"location_name": "Maison", "version": "2026.10", "lights": 3, "lights_on": 2}
    assert calls[0].headers["authorization"] == "Bearer " + TOKEN
    assert home.status()["verified"] is True


def test_all_off_targets_only_lit_lights(tmp_path):
    home, calls = service(tmp_path)
    reply = home.execute(parse_light_command("éteins toutes les lumières"))
    assert reply == "deux lumières éteintes dans toute la maison."
    call = calls[-1]
    assert call.url.path == "/api/services/light/turn_off"
    assert json.loads(call.content)["entity_id"] == ["light.cuisine", "light.hall"]


def test_all_on_targets_every_light(tmp_path):
    home, calls = service(tmp_path)
    home.execute(parse_light_command("allume toutes les lumières"))
    assert json.loads(calls[-1].content)["entity_id"] == ["light.salon_plafond", "light.cuisine", "light.hall"]


def test_room_uses_area_template_and_current_room(tmp_path):
    home, calls = service(tmp_path, room="Salon")
    reply = home.execute(parse_light_command("éteins la lumière"))
    assert reply == "deux lumières éteintes dans la pièce « Salon »."
    template_call = [call for call in calls if call.url.path == "/api/template"][0]
    body = json.loads(template_call.content)
    assert "area_entities('Salon')" in body["template"]
    assert calls[-1].url.path == "/api/services/light/turn_off"


def test_room_name_is_sanitized(tmp_path):
    home, calls = service(tmp_path)
    home.execute(parse_light_command("éteins les lumières du salon"))
    body = json.loads([call for call in calls if call.url.path == "/api/template"][0].content)
    assert body["template"].startswith("{{ area_entities('salon')")
    assert body["template"].count("area_entities('salon')") == 1


def test_no_lights_on_reports_honestly(tmp_path):
    def respond(request):
        if request.url.path == "/api/states":
            return httpx.Response(200, json=[{"entity_id": "light.a", "state": "off"}])
        return httpx.Response(200, json={"location_name": "M", "version": "1"})
    home, _ = service(tmp_path, respond)
    assert home.execute(parse_light_command("éteins toutes les lumières")) == "Aucune lumière autorisée à éteindre."


def test_empty_room_is_an_error_not_a_success(tmp_path):
    def respond(request):
        if request.url.path == "/api/states":
            return httpx.Response(200, json=states())
        if request.url.path == "/api/template":
            return httpx.Response(200, json=[])
        return httpx.Response(200, json={"location_name": "M", "version": "1"})
    home, _ = service(tmp_path, respond)
    with pytest.raises(HomeError, match="Aucune lumière"):
        home.execute(parse_light_command("allume les lumières du grenier"))


def test_unauthorized_is_explicit_and_not_leaked(tmp_path):
    home, _ = service(tmp_path, lambda request: httpx.Response(401, text="detail " + TOKEN))
    result = home.handle("éteins toutes les lumières")
    assert result["error"] and TOKEN not in result["error"]
    assert not home._lock.locked()


def test_concurrent_command_is_refused(tmp_path):
    home, _ = service(tmp_path)
    home._lock.acquire()
    try:
        result = home.handle("éteins toutes les lumières")
    finally:
        home._lock.release()
    assert "déjà en cours" in result["error"]


def test_unmatched_text_returns_none(tmp_path):
    home, _ = service(tmp_path)
    assert home.handle("raconte-moi une histoire") is None


def test_config_api_stores_without_echo(tmp_path):
    with TestClient(create_app(Settings(tmp_path))) as client:
        assert client.get("/api/home/config").json()["configured"] is False
        saved = client.post("/api/home/config", json={"base_url": URL, "token": TOKEN, "room": "Bureau"})
        assert saved.status_code == 200
        assert TOKEN not in saved.text
        assert client.get("/api/home/config").json()["configured"] is True
        assert TOKEN not in client.get("/api/home/config").text
        assert client.post("/api/home/config", json={"base_url": "ftp://x", "token": TOKEN}).status_code == 422
        assert client.post("/api/home/config", json={"base_url": URL, "token": "court"}).status_code == 422
        assert client.post("/api/home/config", json={"base_url": URL, "token": TOKEN, "room": "Sa<lon>"}).status_code == 422


class FakeSpeech:
    def status(self):
        return {"stt_available": True, "tts_available": True}

    def speak(self, text):
        return b"synthetic", 5

    def transcribe(self, data):
        return "Éteins toutes les lumières", 1.0, 12


class FakeConversation:
    def __init__(self):
        self.calls = 0

    def status(self):
        return {"configured": True, "access_verified": True}

    def stream(self, *args, **kwargs):
        self.calls += 1
        yield {"type": "answer", "text": "réponse IA", "model": "x", "usage": {}, "llm_ms": 1, "truncated": False}

    def reset(self, session_id=None):
        pass


def test_light_command_remains_available_without_configured_llm(tmp_path):
    home, calls = service(tmp_path)
    ai = FakeConversation()
    ai.status = lambda: {"configured": False}
    with TestClient(create_app(Settings(tmp_path), voice_service=FakeSpeech(),
                               conversation_service=ai, home_service=home)) as client:
        result = client.post("/api/conversation/text", json={"text": "Éteins toutes les lumières",
                                                             "session_id": "session-test-000001"})
        events = [json.loads(line) for line in result.text.splitlines()]
        assert ai.calls == 0
        assert events[-1]["mode"] == "home"
        assert events[-1]["timings"]["llm_ms"] == 0
        assert any(event["type"] == "answer" for event in events)
        assert any(event.get("text", "").startswith("trois lumières éteintes") for event in events if event["type"] == "answer")


def test_light_command_works_without_command_code_key(tmp_path):
    home, _ = service(tmp_path)
    with TestClient(create_app(Settings(tmp_path), voice_service=FakeSpeech(), home_service=home)) as client:
        result = client.post("/api/conversation/text", json={"text": "Éteins toutes les lumières",
                                                             "session_id": "session-test-000002"})
        events = [json.loads(line) for line in result.text.splitlines()]
        assert events[-1]["type"] == "done" and events[-1]["mode"] == "home"


def test_normal_question_still_uses_the_llm(tmp_path):
    home, _ = service(tmp_path)
    ai = FakeConversation()
    with TestClient(create_app(Settings(tmp_path), voice_service=FakeSpeech(),
                               conversation_service=ai, home_service=home)) as client:
        result = client.post("/api/conversation/text", json={"text": "Bonjour Alfred",
                                                             "session_id": "session-test-000003"})
        events = [json.loads(line) for line in result.text.splitlines()]
        assert ai.calls == 1
        assert events[-1]["mode"] == "conversation"


def test_home_capability_and_command_api(tmp_path):
    home, _ = service(tmp_path)
    with TestClient(create_app(Settings(tmp_path), home_service=home)) as client:
        assert client.get("/api/status").json()["capabilities"]["home_assistant"] is True
        result = client.post("/api/home/command", json={"text": "Éteins toutes les lumières"})
        assert result.status_code == 200
        assert result.json()["scope"] == "all"
        assert client.post("/api/home/command", json={"text": "raconte une blague"}).status_code == 422


@pytest.mark.parametrize("prefix", ["tu peux m'", "tu pourrais m'", "peux-tu m'", "pourrais-tu ", "vous pouvez me "])
@pytest.mark.parametrize("verb,on", [("allumer", True), ("éteindre", False)])
def test_conversational_light_request_executes_locally(tmp_path, prefix, verb, on):
    home, calls = service(tmp_path, room="Bureau")
    result = home.handle(f"{prefix}{verb} la lumière du bureau ?")
    assert result is not None and result.get("reply") and not result.get("error")
    expected = "turn_on" if on else "turn_off"
    writes = [call for call in calls if call.url.path.startswith("/api/services/")]
    assert len(writes) == 1
    assert writes[0].url.path == f"/api/services/light/{expected}"
    assert json.loads(writes[0].content)["entity_id"] == ["light.salon_plafond", "light.salon_lampe"]


@pytest.mark.parametrize("text,on", [
    ("On éteint la lumière du bureau.", False),
    ("Éteint la lumière du bureau.", False),
    ("On allume la lumière du bureau.", True),
    ("éteins la lumière du bureau s'il te plaît.", False),
    ("éteins la lumière du bureau s'il de plaît.", False),
    ("Est-ce que tu peux m’éteindre la lumière du bureau, s’il te plaît ?", False),
])
def test_transcribed_light_order_without_configured_ai(tmp_path, text, on):
    home, calls = service(tmp_path, room="Bureau")
    ai = FakeConversation()
    ai.status = lambda: {"configured": False}
    with TestClient(create_app(Settings(tmp_path), voice_service=FakeSpeech(),
                               conversation_service=ai, home_service=home)) as client:
        result = client.post("/api/conversation/text", json={"text": text,
                             "session_id": "session-transcription-001"})
        events = [json.loads(line) for line in result.text.splitlines()]
    assert result.status_code == 200
    assert ai.calls == 0
    assert events[-1]["mode"] == "home"
    expected = "turn_on" if on else "turn_off"
    writes = [call for call in calls if call.url.path.startswith("/api/services/")]
    assert len(writes) == 1
    assert writes[0].url.path == f"/api/services/light/{expected}"


@pytest.mark.parametrize("text", [
    "On n'éteint pas la lumière du bureau.",
    "Est-ce qu'on éteint la lumière du bureau ?",
    "Hier on éteint la lumière du bureau.",
])
def test_light_narration_or_negation_does_not_act(tmp_path, text):
    home, calls = service(tmp_path, room="Bureau")
    assert home.handle(text) is None
    assert not any(call.url.path.startswith("/api/services/") for call in calls)


@pytest.mark.parametrize("prefix", [
    "", "S'il te plaît, ", "Merci de ", "Tu peux m'", "Est-ce que tu peux ",
    "Pourrais-tu bien ", "Je voudrais que tu ", "Tu veux bien ",
])
@pytest.mark.parametrize("suffix", [
    ".", " s'il te plaît.", ", s’il vous plaît ?", " s'il te plais !",
    " s'il de plaît.", " stp...", " merci beaucoup !", " s'il te plaît, merci.",
])
def test_oral_wrappers_keep_exact_room_and_single_action(tmp_path, prefix, suffix):
    home, calls = service(tmp_path, room="Salon")
    result = home.handle(prefix + "allumer la lumière du bureau" + suffix)
    assert result and result.get("reply") and not result.get("error")
    assert result["scope"] == "room" and result["room"] == "bureau"
    templates = [json.loads(call.content)["template"] for call in calls if call.url.path == "/api/template"]
    assert templates and all("area_entities('bureau')" in value for value in templates)
    writes = [call for call in calls if call.url.path.startswith("/api/services/")]
    assert len(writes) == 1 and writes[0].url.path == "/api/services/light/turn_on"


@pytest.mark.parametrize("text", [
    "Éteins-moi la lumière du bureau, s'il te plaît !",
    "Éteins moi la lumière du bureau.",
])
def test_light_order_with_spoken_pronoun(tmp_path, text):
    home, calls = service(tmp_path, room="Salon")
    result = home.handle(text)
    assert result and result.get("reply") and result["room"] == "bureau"
    assert sum(call.url.path == "/api/services/light/turn_off" for call in calls) == 1


@pytest.mark.parametrize("text,on", [
    ("Éteins toutes les lumières du bureau.", False),
    ("Allume toutes les lampes du bureau.", True),
    ("Éteins toutes les lumières du bureau s'il te plaît.", False),
])
def test_all_lights_in_room_never_expands_to_house(tmp_path, text, on):
    home, calls = service(tmp_path, room="Salon")
    result = home.handle(text)
    assert result and result["scope"] == "room" and result["room"] == "bureau"
    writes = [call for call in calls if call.url.path.startswith("/api/services/")]
    assert len(writes) == 1
    assert json.loads(writes[0].content)["entity_id"] == ["light.salon_plafond", "light.salon_lampe"]


def test_partout_is_explicit_house_scope():
    command = parse_light_command("Éteins les lumières partout.")
    assert command and command.scope == "all" and not command.turn_on
    assert parse_light_command("Éteins les lumières partout du bureau.") is None
