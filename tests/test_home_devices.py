"""Lecteurs et aspirateurs : transport simulé, actions et preuves bornées."""
import asyncio
import io
import json
import wave

import httpx
import pytest
from fastapi.testclient import TestClient

from alfred.app import create_app
from alfred.config import Settings
from alfred.home_assistant import HomeService, HomeStore
from alfred.home_catalog import HomeCatalog, DEVICE_FEATURES, capabilities
from alfred.music import parse_music_command


@pytest.fixture
def device(tmp_path, monkeypatch):
    def make(domain="media_player", features=None):
        attrs = {"supported_features": sum(set(DEVICE_FEATURES[domain].values())) if features is None else features}
        if domain == "media_player":
            attrs.update(volume_level=.2, is_volume_muted=False, source="TV", source_list=["TV", "Bluetooth Audio"], group_members=[])
        else:
            attrs.update(fan_speed="balanced", fan_speed_list=["quiet", "balanced", "turbo"])
        current = {"entity_id": domain + ".test", "state": "idle" if domain == "media_player" else "docked", "attributes": attrs}
        item = {"entity_id": current["entity_id"], "domain": domain, "name": "Télé" if domain == "media_player" else "Roborock",
                "allowed": True, "members": None, "attributes": attrs.copy(), "area": "Salon", "aliases": ["mon appareil"],
                "ha_aliases": ["autre nom"], "cleaning_areas": [{"id": "living", "name": "Salon"}]}
        items, calls = [item], []
        def respond(request):
            calls.append(request)
            if request.method == "GET":
                return httpx.Response(200, json=current)
            payload = json.loads(request.content)
            service = request.url.path.rsplit("/", 1)[-1]
            states = {"turn_on": "on", "turn_off": "off", "media_play": "playing", "media_pause": "paused", "media_stop": "idle",
                      "start": "cleaning", "pause": "paused", "stop": "idle", "return_to_base": "returning"}
            if service in states: current["state"] = states[service]
            for action, key in [("volume_set", "volume_level"), ("volume_mute", "is_volume_muted"), ("select_source", "source"), ("set_fan_speed", "fan_speed")]:
                if service == action: attrs[key] = payload[key]
            if service in {"volume_up", "volume_down"}:
                attrs["volume_level"] += .05 if service == "volume_up" else -.05
            return httpx.Response(200, json=[])
        home = HomeService(HomeStore(tmp_path, base_url="http://ha.test:8123", token="fake", room="Salon"),
                           lambda: httpx.Client(transport=httpx.MockTransport(respond)))
        monkeypatch.setattr(HomeCatalog, "snapshot", lambda self: {"entities": items})
        return home, calls, items, current
    return make


def posts(calls):
    return [x for x in calls if x.method == "POST"]


@pytest.mark.parametrize("phrase,service,key,value,reply", [
    ("Allume télé", "turn_on", None, None, "allumé"),
    ("Éteins télé", "turn_off", None, None, "éteint"),
    ("Mets télé en pause", "media_pause", None, None, "en pause"),
    ("Reprends télé", "media_play", None, None, "en lecture"),
    ("Arrête télé", "media_stop", None, None, "au repos"),
    ("Piste suivante sur télé", "media_next_track", None, None, "demandé"),
    ("Piste précédente sur télé", "media_previous_track", None, None, "demandé"),
    ("Règle le volume de télé à trente pour cent", "volume_set", "volume_level", .3, "trente pour cent"),
    ("Mets le volume à trente sur télé", "volume_set", "volume_level", .3, "trente pour cent"),
    ("Coupe le son de télé", "volume_mute", "is_volume_muted", True, "son coupé"),
    ("Remets le son de télé", "volume_mute", "is_volume_muted", False, "son rétabli"),
    ("Augmente le volume de télé", "volume_up", None, None, "vingt-cinq pour cent"),
    ("Baisse le volume de télé", "volume_down", None, None, "quinze pour cent"),
    ("Mets télé sur Bluetooth Audio", "select_source", "source", "Bluetooth Audio", "Bluetooth Audio"),
    ("Règle la source de télé sur TV", "select_source", "source", "TV", "TV"),
])
def test_media_commands(device, phrase, service, key, value, reply):
    home, calls, _, _ = device()
    result = home.handle("Hé Alfred " + phrase)
    assert reply in result["reply"]
    sent = posts(calls)
    assert len(sent) == 1
    assert sent[0].url.path == "/api/services/media_player/" + service
    if key: assert json.loads(sent[0].content)[key] == value


@pytest.mark.parametrize("phrase,service,key,value,reply", [
    ("Démarre l'aspirateur", "start", None, None, "nettoyage"),
    ("Reprends roborock", "start", None, None, "nettoyage"),
    ("Mets le robot en pause", "pause", None, None, "en pause"),
    ("Arrête mon appareil", "stop", None, None, "au repos"),
    ("Renvoie autre nom à sa base", "return_to_base", None, None, "retourne"),
    ("Localise roborock", "locate", None, None, "demandé"),
    ("Règle la puissance de roborock à silencieux", "set_fan_speed", "fan_speed", "quiet", "silencieux"),
    ("Mets roborock sur turbo", "set_fan_speed", "fan_speed", "turbo", "turbo"),
    ("Nettoie le salon", "clean_area", "cleaning_area_id", ["living"], "demandé"),
    ("Nettoie le salon avec roborock", "clean_area", "cleaning_area_id", ["living"], "demandé"),
])
def test_vacuum_commands(device, phrase, service, key, value, reply):
    home, calls, _, _ = device("vacuum")
    result = home.handle(phrase)
    assert reply in result["reply"]
    sent = posts(calls)
    assert len(sent) == 1
    assert sent[0].url.path == "/api/services/vacuum/" + service
    if key: assert json.loads(sent[0].content)[key] == value


@pytest.mark.parametrize("phrase", ["règle le volume de télé à cent un", "règle le volume de télé à moins un",
    "règle le volume de télé à trente décibels", "mets télé sur source inconnue", "mets télé en pause et allume la lampe"])
def test_invalid_values_and_mixed_sentences_never_write(device, phrase):
    home, calls, _, _ = device()
    result = home.handle(phrase)
    assert result is None or result.get("error")
    assert not posts(calls)


def test_read_state_volume_sources_and_power(device):
    home, calls, _, _ = device()
    for text, word in [("quel est l'état de télé", "au repos"), ("quel est le volume de télé", "vingt pour cent"),
                       ("quelle est la source de télé", "TV"), ("liste les sources de télé", "Bluetooth Audio")]:
        assert word in home.handle(text)["reply"]
    assert not posts(calls)
    home, calls, _, _ = device("vacuum")
    assert "à sa base" in home.handle("lis aspirateur")["reply"]
    assert "silencieux" in home.handle("liste les puissances de aspirateur")["reply"]
    assert "Salon" in home.handle("liste les pièces nettoyables par aspirateur")["reply"]
    assert not posts(calls)


def test_room_cleaning_never_falls_back_to_full_clean(device):
    home, calls, items, _ = device("vacuum")
    for text in ["nettoie la cuisine", "nettoie le salon et la cuisine", "nettoie le salon et raconte une blague"]:
        assert home.handle(text)["error"]
    items[0]["cleaning_areas"] = []
    assert home.handle("nettoie le salon")["error"]
    assert not posts(calls)


@pytest.mark.parametrize("domain,text", [("media_player", "mets télé en pause"), ("vacuum", "démarre aspirateur")])
def test_missing_feature_unknown_and_unavailable_never_write(device, domain, text):
    home, calls, items, current = device(domain, features=0)
    assert capabilities(domain, current["attributes"]) == ["read"]
    assert home.handle(text)["error"]
    current["attributes"]["supported_features"] = sum(set(DEVICE_FEATURES[domain].values()))
    for state in ["unknown", "unavailable"]:
        current["state"] = state
        assert home.handle(text)["error"]
    assert not posts(calls)


def test_groups_check_exposure_exclusions_and_live_members(device):
    home, calls, items, current = device()
    items[0]["allowed"] = False
    assert home.handle("mets télé en pause")["error"]
    items[0]["allowed"] = True
    current["attributes"]["group_members"] = ["media_player.test", "media_player.other"]
    assert home.handle("mets télé en pause")["error"]
    items.append({**items[0], "name": "Autre lecteur", "entity_id": "media_player.other", "allowed": False})
    assert home.handle("mets télé en pause")["error"]
    assert not posts(calls)
    items[1]["allowed"] = True
    items[1]["attributes"] = {"group_members": ["media_player.test", "media_player.other"]}
    assert home.handle("mets télé en pause")["reply"]
    assert len(posts(calls)) == 1


def test_nested_media_group_cannot_hide_an_excluded_group_member(device):
    home, calls, items, current = device()
    items[0]["members"] = ["media_player.child"]
    items.append({**items[0], "name": "Enfant", "entity_id": "media_player.child", "members": None,
                  "attributes": {"group_members": ["media_player.hidden"]}})
    items.append({**items[0], "name": "Exclu", "entity_id": "media_player.hidden", "members": None, "allowed": False})
    assert home.handle("mets télé en pause")["error"]
    assert not posts(calls)


def test_homonyms_require_piece_or_distinct_alias(device):
    home, calls, items, _ = device()
    items.append({**items[0], "entity_id": "media_player.other", "area": "Bureau"})
    assert home.handle("allume télé")["error"]
    assert not posts(calls)
    assert home.handle("allume télé du salon")["reply"]
    assert len(posts(calls)) == 1


def test_dispatch_failure_or_delayed_state_never_retries(device, monkeypatch):
    home, calls, _, _ = device("vacuum")
    sent = []
    monkeypatch.setattr(home, "call_service", lambda *args: sent.append(args))
    assert "non confirmé" in home.handle("démarre aspirateur")["reply"]
    assert len(sent) == 1
    def fail(*args):
        from alfred.home_assistant import HomeError
        sent.append(args)
        raise HomeError("Connexion impossible.")
    monkeypatch.setattr(home, "call_service", fail)
    assert home.handle("démarre aspirateur")["error"]
    assert len(sent) == 2


def test_music_queries_and_targeted_volume_do_not_collide():
    assert parse_music_command("Mets Airbourne sur l'ampli").query == "Airbourne"
    assert parse_music_command("Mets le volume à trente sur l'ampli") is None
    assert parse_music_command("Mets la musique en pause").action == "pause"


@pytest.mark.parametrize("domain,phrase,service", [("media_player", "mets télé en pause", "media_pause"), ("vacuum", "démarre aspirateur", "start")])
def test_api_text_voice_and_terminal(device, tmp_path, domain, phrase, service):
    home, calls, _, _ = device(domain)
    class Speech:
        def status(self): return {"ready": True}
        def transcribe(self, *args): return phrase, 1, 1
        def speak(self, text): return b"test-audio", 1
    app = create_app(Settings(tmp_path), home_service=home, voice_service=Speech())
    sid = "devices-routing-test-1234"
    data = io.BytesIO()
    with wave.open(data, "wb") as wav:
        wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(16000); wav.writeframes(bytes(32000))
    with TestClient(app) as client:
        assert client.post("/api/home/command", json={"text": phrase}).json()["reply"]
        response = client.post("/api/conversation/text", json={"text": phrase, "session_id": sid})
        assert '"mode": "home"' in response.text
        response = client.post("/api/conversation/voice", content=data.getvalue(), headers={"content-type": "audio/wav", "X-Alfred-Session": sid})
        assert '"mode": "home"' in response.text
        async def run():
            return await asyncio.wait_for(app.state.terminal.process(data.getvalue(), sid, "rdc"), 5)
        result = client.portal.call(run)
        assert result["mode"] == "home"
        assert len(posts(calls)) == 4
        assert all(x.url.path.endswith("/" + service) for x in posts(calls))
