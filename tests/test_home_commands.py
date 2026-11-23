"""Recette des actions bornées : aucune requête ne quitte le transport simulé."""
import asyncio
import io
import json
import wave
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
import pytest
from fastapi.testclient import TestClient

from alfred.app import create_app
from alfred.config import Settings
from alfred.home_assistant import HomeService, HomeStore
from alfred.home_catalog import HomeCatalog
from alfred.home_commands import datetime_payload, numeric


def setup_home(tmp_path, monkeypatch, domain="switch", name="Prise", state="off", attrs=None):
    entity = domain + ".test"
    attrs = attrs or {}
    item = {"entity_id": entity, "domain": domain, "name": name, "allowed": True,
            "area": "Salon", "members": None, "aliases": ["mon appareil"], "ha_aliases": ["autre nom"], "attributes": attrs}
    items = [item]
    current = {"entity_id": entity, "state": state, "attributes": attrs.copy()}
    calls = []
    def respond(request):
        calls.append(request)
        if request.url.path == "/api/config":
            return httpx.Response(200, json={"time_zone": "Europe/Paris"})
        if request.method == "GET":
            return httpx.Response(200, json=current)
        data = json.loads(request.content)
        action = request.url.path.split("/")[-1]
        if action in {"turn_on", "turn_off"}:
            current["state"] = "on" if action == "turn_on" else "off"
        elif action == "set_value": current["state"] = str(data["value"])
        elif action == "select_option": current["state"] = data["option"]
        elif action in {"increment", "decrement"}:
            current["state"] = str(float(current["state"]) + attrs["step"] * (1 if action == "increment" else -1))
        elif action in {"select_next", "select_previous"}:
            options = attrs["options"]
            current["state"] = options[(options.index(current["state"]) + (1 if action == "select_next" else -1)) % len(options)]
        elif action == "set_datetime":
            if attrs.get("has_date") and attrs.get("has_time"):
                old = current["state"].split()
                current["state"] = data.get("date", old[0]) + " " + data.get("time", old[1])
            else:
                current["state"] = data.get("date") or data.get("time")
        return httpx.Response(200, json=[])
    home = HomeService(HomeStore(tmp_path, base_url="http://ha.test:8123", token="fake", room="Salon"),
                       lambda: httpx.Client(transport=httpx.MockTransport(respond)))
    monkeypatch.setattr(HomeCatalog, "snapshot", lambda self: {"entities": items})
    return home, calls, items, current


def writes(calls):
    return [request for request in calls if request.method == "POST"]


@pytest.mark.parametrize("domain", ["switch", "input_boolean"])
@pytest.mark.parametrize("name", ["Prise", "mon appareil", "autre nom"])
def test_switch_by_name_and_both_aliases(tmp_path, monkeypatch, domain, name):
    home, calls, _, current = setup_home(tmp_path, monkeypatch, domain)
    result = home.handle(f"Hé Alfred, active {name} s'il te plaît")
    assert "activé" in result["reply"]
    assert current["state"] == "on"
    assert writes(calls)[0].url.path == f"/api/services/{domain}/turn_on"
    assert "désactivé" in home.handle(f"désactive {name}")["reply"]
    assert "désactivé" in home.handle(f"quel est l'état de {name} ?")["reply"]
    assert "désactivé" in home.handle(f"quel est l'état du {name} ?")["reply"]


def test_temperature_room_current_negative_and_multiple(tmp_path, monkeypatch):
    home, calls, items, current = setup_home(tmp_path, monkeypatch, "sensor", "Sonde", "-2.5",
        {"device_class": "temperature", "unit_of_measurement": "°C"})
    for text in ["Quelle température ici ?", "Quelle est la température dans le salon ?",
                 "Quelle température ?", "Quelle température au salon ?",
                 "Quelle température fait-il dans le salon ?",
                 "Il fait quelle température ici ?", "Combien fait-il ici ?",
                 "Quelle est la température de la pièce ?"]:
        result = home.handle(text)
        assert "moins deux virgule cinq degrés Celsius" in result["reply"]
    assert not writes(calls)
    items.append({**items[0], "entity_id": "sensor.second", "name": "Autre"})
    assert "Plusieurs" in home.handle("quelle température dans le salon")["error"]
    items.pop()
    current["state"] = "unavailable"
    assert "indisponible" in home.handle("quelle température ici")["error"]


def test_temperature_partial_room_requires_precision(tmp_path, monkeypatch):
    attrs = {"device_class": "temperature", "unit_of_measurement": "°C"}
    home, calls, items, _ = setup_home(tmp_path, monkeypatch, "sensor", "Sonde parentale", "20", attrs)
    items[0]["area"] = "Chambre Parentale"
    items.append({**items[0], "entity_id": "sensor.auguste", "name": "Sonde Auguste",
                  "area": "Chambre Auguste"})
    assert "Plusieurs" in home.handle("quelle température dans la chambre")["error"]
    assert "Il fait vingt degrés Celsius" in home.handle("quelle température dans la chambre parentale")["reply"]
    assert "Sonde parentale" in home.handle("quelle température sur la sonde parentale")["reply"]
    assert not writes(calls)


@pytest.mark.parametrize("text,expected", [("vingt et un", 21), ("moins deux virgule cinq", -2.5),
    ("zéro virgule zéro cinq", .05), ("mille deux cent trente-quatre", 1234), ("-2,75", -2.75)])
def test_french_numbers(text, expected):
    assert float(numeric(text)) == expected


def test_number_limits_units_and_step(tmp_path, monkeypatch):
    home, calls, _, current = setup_home(tmp_path, monkeypatch, "input_number", "Seuil", "20",
        {"min": -10, "max": 40, "step": .5, "unit_of_measurement": "°C"})
    assert "moins deux virgule cinq" in home.handle("règle le seuil à moins deux virgule cinq degrés")["reply"]
    assert "moins deux" in home.handle("augmente le seuil d'un pas")["reply"]
    before = len(writes(calls))
    for text in ["mets le seuil à quarante et un", "mets le seuil à trois minutes", "mets le seuil à cinq et allume la prise"]:
        assert home.handle(text)["error"]
    assert len(writes(calls)) == before
    current["state"] = "40"
    assert home.handle("augmente le seuil")["error"]


def test_select_options_and_navigation(tmp_path, monkeypatch):
    home, calls, _, _ = setup_home(tmp_path, monkeypatch, "input_select", "Ambiance", "Jour", {"options": ["Jour", "Été", "Nuit"]})
    assert "Été" in home.handle("liste les options de ambiance")["reply"]
    assert "Été" in home.handle("mets ambiance sur été")["reply"]
    assert "Nuit" in home.handle("passe ambiance à l'option suivante")["reply"]
    assert "Été" in home.handle("option précédente de ambiance")["reply"]
    count = len(writes(calls))
    assert home.handle("mets ambiance sur inconnu")["error"]
    assert len(writes(calls)) == count


def test_date_and_time_keep_other_half(tmp_path, monkeypatch):
    home, calls, _, current = setup_home(tmp_path, monkeypatch, "input_datetime", "Réveil", "2026-11-14 08:00:00", {"has_date": True, "has_time": True})
    assert home.handle("règle réveil à sept heures trente")["reply"]
    assert current["state"] == "2026-11-14 07:30:00"
    assert "sept heures trente" in home.handle("lis réveil")["reply"]
    assert home.handle("mets réveil à le quinze novembre deux mille vingt-six")["reply"]
    assert current["state"] == "2026-11-15 07:30:00"
    assert home.handle("mets réveil à 2026-12-01 à 09:45")["reply"]
    assert current["state"] == "2026-12-01 09:45:00"
    before = len(writes(calls))
    for value in ["trente heures", "le trente et un février", "demain et allume la prise"]:
        assert home.handle("mets réveil à " + value)["error"]
    assert len(writes(calls)) == before


def test_relative_date_and_field_validation():
    zone = ZoneInfo("Pacific/Kiritimati")
    expected = datetime.now(zone).date().isoformat()
    assert datetime_payload("aujourd'hui", {"has_date": True}, zone) == {"date": expected}
    from alfred.home_assistant import HomeError
    with pytest.raises(HomeError):
        datetime_payload("demain", {"has_time": True}, zone)


def test_text_keeps_case_accents_punctuation_and_password_hidden(tmp_path, monkeypatch):
    home, calls, items, current = setup_home(tmp_path, monkeypatch, "input_text", "Message", "Bonjour", {"min": 0, "max": 100})
    assert home.handle("écris message à Élodie arrive à 18 h !")["reply"]
    assert json.loads(writes(calls)[0].content)["value"] == "Élodie arrive à 18 h !"
    current["attributes"]["mode"] = "password"
    count = len(writes(calls))
    assert home.handle("lis message")["error"]
    result = home.handle("mets message à ValeurConfidentielle")
    assert result["reply"] == "Champ confidentiel mis à jour."
    assert "ValeurConfidentielle" not in json.dumps(result)
    assert len(writes(calls)) == count + 1


def test_exclusions_groups_cycles_and_cross_domain_collision(tmp_path, monkeypatch):
    home, calls, items, _ = setup_home(tmp_path, monkeypatch)
    item = items[0]
    item["allowed"] = False
    assert home.handle("allume prise")["error"]
    item["allowed"] = True
    item["members"] = ["switch.missing"]
    assert home.handle("allume prise")["error"]
    item["members"] = [item["entity_id"]]
    assert home.handle("allume prise")["error"]
    item["members"] = None
    items.append({**item, "domain": "light", "entity_id": "light.test"})
    assert "Plusieurs" in home.handle("allume prise")["error"]
    assert not writes(calls)


def test_unconfirmed_action_and_network_error_never_repeated(tmp_path, monkeypatch):
    home, calls, _, _ = setup_home(tmp_path, monkeypatch)
    monkeypatch.setattr(home, "call_service", lambda *args: [])
    assert "non confirmé" in home.handle("active prise")["reply"]
    home, calls, _, _ = setup_home(tmp_path, monkeypatch, "input_button", "Routine", "unknown")
    counter = []
    def fail(*args):
        from alfred.home_assistant import HomeError
        counter.append(args)
        raise HomeError("Connexion à Home Assistant impossible.")
    monkeypatch.setattr(home, "call_service", fail)
    assert home.handle("appuie sur routine")["error"]
    assert len(counter) == 1


def test_button_dispatch_is_not_automation_completion(tmp_path, monkeypatch):
    home, calls, _, _ = setup_home(tmp_path, monkeypatch, "input_button", "Routine", "unknown")
    assert home.handle("déclenche routine")["reply"] == "Appui envoyé à Home Assistant."
    assert len(writes(calls)) == 1


def test_deferred_and_other_domains_never_written(tmp_path, monkeypatch):
    home, calls, items, _ = setup_home(tmp_path, monkeypatch, "climate", "Chauffage", "off")
    for domain in ["climate", "timer", "number", "select", "counter"]:
        items[0].update(domain=domain, entity_id=domain + ".test")
        for text in ["active chauffage", "mets chauffage à vingt", "lis chauffage"]:
            result = home.handle(text)
            assert result is None or result.get("error")
    assert not writes(calls)


def test_general_questions_do_not_contact_home_assistant(tmp_path, monkeypatch):
    home = HomeService(HomeStore(tmp_path))
    monkeypatch.setattr(HomeCatalog, "snapshot", lambda self: pytest.fail("unexpected catalogue lookup"))
    for text in ["Quelle est la capitale de la France ?", "Quelle heure est-il ?", "Raconte une histoire", "Quel est ton nom ?"]:
        assert home.handle(text) is None


def test_room_qualifier_disambiguates_and_context_does_not_leak(tmp_path, monkeypatch):
    from alfred.home_assistant import HOME_ROOM
    home, calls, items, _ = setup_home(tmp_path, monkeypatch)
    items.append({**items[0], "entity_id": "switch.other", "area": "Bureau"})
    assert home.handle("active prise")["error"]
    assert home.handle("active prise du salon")["reply"]
    assert len(writes(calls)) == 1
    token = HOME_ROOM.set("Bureau")
    try:
        assert home.room() == "Bureau"
    finally:
        HOME_ROOM.reset(token)
    assert home.room() == "Salon"


def test_api_text_voice_and_terminal_use_same_direct_path(tmp_path, monkeypatch):
    home, calls, _, _ = setup_home(tmp_path, monkeypatch)
    class Speech:
        def status(self): return {"ready": True}
        def transcribe(self, *args): return "active prise", 1, 1
        def speak(self, text): return b"test-audio", 1
    app = create_app(Settings(tmp_path), home_service=home, voice_service=Speech())
    sid = "12345678-1234-4234-9234-123456789abc"
    data = io.BytesIO()
    with wave.open(data, "wb") as wav:
        wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(16000); wav.writeframes(bytes(32000))
    with TestClient(app) as client:
        assert client.post("/api/home/command", json={"text": "active prise"}).json()["reply"]
        response = client.post("/api/conversation/text", json={"text": "active prise", "session_id": sid})
        assert '"mode": "home"' in response.text
        response = client.post("/api/conversation/voice", content=data.getvalue(), headers={"content-type": "audio/wav", "X-Alfred-Session": sid})
        assert '"mode": "home"' in response.text
        async def run():
            return await asyncio.wait_for(app.state.terminal.process(data.getvalue(), sid, "rdc"), 5)
        result = client.portal.call(run)
        assert result["mode"] == "home"
        assert len(writes(calls)) == 4


def test_terminal_temperature_uses_its_room_and_web_keeps_its_room(tmp_path, monkeypatch):
    from alfred.terminal import TerminalConfig
    attrs = {"device_class": "temperature", "unit_of_measurement": "°C"}
    home, calls, items, _ = setup_home(tmp_path, monkeypatch, "sensor", "Sonde salon", "20", attrs)
    items.append({**items[0], "entity_id": "sensor.bureau", "area": "Bureau", "name": "Sonde bureau"})
    monkeypatch.setattr(home, "get_state", lambda entity: {"entity_id": entity, "state": "20" if entity == "sensor.test" else "19", "attributes": attrs})
    class Speech:
        def status(self): return {"ready": True}
        def transcribe(self, *args): return "quelle température ici", 1, 1
        def speak(self, text): return b"test-audio", 1
    app = create_app(Settings(tmp_path), home_service=home, voice_service=Speech())
    sid = "temperature-room-test-12345"
    data = io.BytesIO()
    with wave.open(data, "wb") as wav:
        wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(16000); wav.writeframes(bytes(32000))
    with TestClient(app) as client:
        app.state.terminal.config = TerminalConfig("192.168.1.200", "00:11:22:33:44:55", "192.168.77.24", room="Bureau")
        async def run():
            return await asyncio.wait_for(app.state.terminal.process(data.getvalue(), sid, "rdc"), 5)
        result = client.portal.call(run)
        assert "« Bureau »" in result["text"]
        assert "dix-neuf" in result["text"]
        result = client.post("/api/home/command", json={"text": "quelle température ici"}).json()
        assert "« Salon »" in result["reply"]
        assert not writes(calls)


def test_tts_failure_after_button_does_not_repeat_action(tmp_path, monkeypatch):
    home, calls, _, _ = setup_home(tmp_path, monkeypatch, "input_button", "Routine", "unknown")
    class Speech:
        def status(self): return {"ready": True}
        def speak(self, text): raise RuntimeError("internal audio error")
    app = create_app(Settings(tmp_path), home_service=home, voice_service=Speech())
    with TestClient(app) as client:
        response = client.post("/api/conversation/text", json={"text": "appuie sur routine", "session_id": "button-no-retry-12345"})
        events = [json.loads(line) for line in response.text.splitlines()]
        assert events[-1]["type"] == "error"
        assert "Appui envoyé" in events[-1]["message"]
        assert "vérifiez le résultat" in events[-1]["message"]
        assert "internal audio error" not in response.text
        assert len(writes(calls)) == 1


@pytest.mark.parametrize("text", [
    "Est-ce que tu peux activer Prise, s'il te plaît ?",
    "Active Prise s'il de plaît.",
    "S'il vous plaît, active Prise !",
    "Merci de activer Prise.",
])
def test_shared_oral_cleanup_for_switches(tmp_path, monkeypatch, text):
    home, calls, _, current = setup_home(tmp_path, monkeypatch)
    result = home.handle(text)
    assert result and result.get("reply") and not result.get("error")
    assert current["state"] == "on"
    assert len(writes(calls)) == 1
