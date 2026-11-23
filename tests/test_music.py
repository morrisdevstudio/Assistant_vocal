import json
import threading
import tempfile

import httpx
import pytest
from fastapi.testclient import TestClient

from alfred.app import create_app
from alfred.config import Settings
from alfred.conversation import ConversationService
from alfred.credentials import CredentialStore
from alfred.home_assistant import HomeError, HomeService
from alfred.music import Music, parse_music_command


PLAYER = "media_player.amp_salon_2"


def test_library_discovery_is_reused_then_refreshed(monkeypatch):
    clock = 100
    endpoint = ("http://ha.local/api", "test-token")
    discoveries = []
    transport = httpx.MockTransport(lambda request: httpx.Response(400, json={"message": "Intégration absente"}))
    home = HomeService(None, lambda: httpx.Client(transport=transport))

    def discover(base, token):
        discoveries.append((base, token))
        return f"entry-{len(discoveries)}"

    monkeypatch.setattr("alfred.home_assistant.time.monotonic", lambda: clock)
    monkeypatch.setattr(home, "_endpoint", lambda: endpoint)
    monkeypatch.setattr(home, "_discover_music_entry", discover)

    assert home.config_entry_id() == home.config_entry_id() == "entry-1"
    with pytest.raises(HomeError, match="Intégration absente"):
        home.call_service_response("music_assistant", "get_library", {"config_entry_id": "entry-1"})
    assert home.config_entry_id() == "entry-2"
    endpoint = (endpoint[0], "rotated-token")
    assert home.config_entry_id() == "entry-3"
    clock += 61
    assert home.config_entry_id() == "entry-4"
    assert len(discoveries) == 4


class FakeHome:
    def __init__(self, directory=None):
        from pathlib import Path
        from alfred.home_assistant import HomeStore
        self.store = HomeStore(directory or Path(tempfile.gettempdir()))
        self.calls = []
        self.player_state = {"entity_id": PLAYER, "state": "idle",
                             "attributes": {"friendly_name": "Ampli du salon", "media_title": "Antigone",
                                            "volume_level": 0.4, "is_volume_muted": False,
                                            "supported_features": 1 + 4 + 8 + 16 + 32 + 128 + 256 + 1024 + 4096 + 16384}}

    def states(self, domain=None):
        return [self.player_state, {"entity_id": "media_player.salon_amp_salon", "state": "off",
                                    "attributes": {"friendly_name": "AMP_SALON"}}]

    def get_state(self, entity_id):
        if entity_id not in {PLAYER, "media_player.salon_amp_salon"}:
            raise HomeError("Lecteur introuvable.")
        return self.player_state if entity_id == PLAYER else {
            "entity_id": entity_id, "state": "off", "attributes": {"friendly_name": "AMP_SALON"}}

    def call_service(self, domain, service, payload):
        self.calls.append((domain, service, payload))
        if domain == "media_player" and service == "volume_set":
            self.player_state["attributes"]["volume_level"] = payload["volume_level"]
        return []

    def call_service_response(self, domain, service, payload):
        assert (domain, service) == ("music_assistant", "get_library")
        assert payload["media_type"] == "playlist"
        return [{"uri": "qobuz://playlist/1", "name": "Détente", "provider": "Qobuz"},
                {"uri": "library://playlist/1", "name": "Détente", "metadata": {"provider": "Library"}}]

    def config_entries(self):
        return [{"entry_id": "ma-entry", "domain": "music_assistant", "state": "loaded"}]

    def config_entry_id(self):
        return "ma-entry"

    def status(self):
        return {"configured": True, "verified": True}


class FakeVoice:
    def status(self):
        return {"stt_available": False, "tts_available": True}

    def speak(self, text):
        return b"synthetic-wav", 2


class FakeConversation:
    def __init__(self):
        self.calls = 0

    def status(self):
        return {"configured": True, "access_verified": True}

    def stream(self, *args, **kwargs):
        self.calls += 1
        yield {"type": "answer", "text": "Cette demande devrait rester locale.",
               "model": "x", "usage": {}, "llm_ms": 1, "truncated": False}

    def reset(self, session_id=None):
        pass


@pytest.mark.parametrize("text,expected", [
    ("Mets Airbourne sur l'ampli", ("play", "Airbourne", "artist")),
    ("Jarvis, mets Airbourne sur l'ampli", ("play", "Airbourne", "artist")),
    ("Jarvisse, pause la musique", ("pause", None, None)),
    ("joue l'album Powerage sur l'ampli", ("play", "Powerage", "album")),
    ("mets la chanson Back in Black sur l'ampli", ("play", "Back in Black", "track")),
    ("mets de la musique d'Airbourne sur l'ampli", ("play", "Airbourne", "artist")),
    ("pause la musique", ("pause", None, None)),
    ("reprends la musique", ("resume", None, None)),
    ("arrête la musique", ("stop", None, None)),
    ("musique suivante", ("next", None, None)),
])
def test_parse_music_commands(text, expected):
    command = parse_music_command(text)
    assert command and (command.action, command.query, command.media_type) == expected


@pytest.mark.parametrize("text", [
    "stop", "mets de la musique sur l'ampli", "mets Airbourne sur l'ampli et raconte une blague",
    "quelle musique joues-tu", "allume la lumière", "",
])
def test_mixed_or_incomplete_music_requests_are_refused(text):
    assert parse_music_command(text) is None


def test_configured_player_receives_music_assistant_request(tmp_path):
    home = FakeHome()
    music = Music(home, tmp_path)
    with pytest.raises(HomeError, match="Aucun lecteur"):
        music.play("Airbourne")
    status = music.configure(PLAYER)
    assert status["configured"] and status["configured_player"] == "Ampli du salon"
    result = music.play("Airbourne", "artist")
    assert "Lecture de « Airbourne » demandée" in result["message"]
    assert home.calls == [("music_assistant", "play_media", {
        "entity_id": PLAYER, "media_id": "Airbourne", "media_type": "artist", "enqueue": "play"
    })]


def test_music_library_uses_real_favorites_and_global_search(tmp_path):
    class LibraryHome(FakeHome):
        def call_service_response(self, domain, service, payload):
            assert domain == "music_assistant"
            assert payload["config_entry_id"] == "ma-entry"
            if service == "get_library":
                assert payload["favorite"] is True and payload["media_type"] == "album"
                return {"service_response": {"items": [{"uri": "library://album/1", "name": "Favori"}]}}
            assert service == "search" and payload["media_type"] == ["album"] and payload["name"] == "test"
            return {"albums": [{"uri": "qobuz://album/1", "name": "Résultat"}, {"name": "Incomplet"}]}
    music = Music(LibraryHome(tmp_path), tmp_path)
    music.configure(PLAYER)
    assert music.library("album") == [{"uri": "library://album/1", "name": "Favori"}]
    assert music.library("album", "test") == [{"uri": "qobuz://album/1", "name": "Résultat"}]


def test_pause_and_stop_target_the_selected_player(tmp_path):
    home = FakeHome()
    music = Music(home, tmp_path)
    music.configure(PLAYER)
    assert "Pause" in music.control("pause")["message"]
    assert "Arrêt" in music.control("stop")["message"]
    assert [call[1] for call in home.calls] == ["media_pause", "media_stop"]
    assert all(call[2] == {"entity_id": PLAYER} for call in home.calls)


def test_music_is_ducked_then_restored_without_overwriting_manual_change(tmp_path):
    home = FakeHome()
    home.player_state["state"] = "playing"
    music = Music(home, tmp_path)
    music.configure(PLAYER, duck_percent=25)
    assert music.duck("music-duck-session-01") == {
        "ducked": True, "owned": True, "volume_level": 0.1, "confirmed": True}
    assert home.calls[-1] == ("media_player", "volume_set", {
        "entity_id": PLAYER, "volume_level": 0.1})
    assert music.duck("music-duck-session-01")["owned"] is True
    assert len(home.calls) == 1
    assert music.restore("music-duck-session-01")["restored"] is True
    assert home.player_state["attributes"]["volume_level"] == 0.4

    assert music.duck("music-duck-session-02")["ducked"] is True
    home.player_state["attributes"]["volume_level"] = 0.33
    result = music.restore("music-duck-session-02")
    assert result == {"ducked": False, "restored": False, "reason": "manual_change"}
    assert home.player_state["attributes"]["volume_level"] == 0.33


def test_music_is_not_ducked_when_player_is_not_playing(tmp_path):
    home = FakeHome()
    music = Music(home, tmp_path)
    music.configure(PLAYER)
    result = music.duck("music-duck-session-03")
    assert result == {"ducked": False, "owned": False, "reason": "not_playing"}
    assert not home.calls


def test_expired_duck_is_restored_as_fallback(tmp_path):
    home = FakeHome()
    home.player_state["state"] = "playing"
    music = Music(home, tmp_path)
    music.configure(PLAYER)
    music.duck("music-expiry-session-01")
    music._active_duck["expires_at"] = 0
    assert music.expire_duck()["restored"] is True
    assert home.player_state["attributes"]["volume_level"] == 0.4


def test_api_config_players_play_and_control(tmp_path):
    home = FakeHome()
    with TestClient(create_app(Settings(tmp_path), home_service=home, voice_service=FakeVoice())) as client:
        assert client.get("/api/music/config").json()["configured"] is False
        players = client.get("/api/music/players").json()["items"]
        assert any(item["entity_id"] == PLAYER for item in players)
        saved = client.post("/api/music/config", json={"entity_id": PLAYER})
        assert saved.status_code == 200 and saved.json()["configured"] is True
        assert saved.json()["duck_percent"] == 25
        played = client.post("/api/music/play", json={"query": "Airbourne", "media_type": "artist"})
        assert played.status_code == 200 and "Airbourne" in played.json()["message"]
        paused = client.post("/api/music/control", json={"action": "pause"})
        assert paused.status_code == 200 and "Pause" in paused.json()["message"]
        assert client.post("/api/music/config", json={"entity_id": "light.salon"}).status_code == 422


def test_pwa_targets_music_assistant_output_without_changing_default(tmp_path):
    home = FakeHome(tmp_path)
    other = "media_player.bureau"
    other_state = {"entity_id": other, "state": "off", "attributes": {
        "mass_player_type": "player", "entity_picture": "/api/media_player_proxy/media_player.bureau?token=private",
    }}
    get_state = home.get_state
    states = home.states
    home.get_state = lambda entity: other_state if entity == other else get_state(entity)
    home.states = lambda domain: [*states(domain), other_state]
    home.media_player_image = lambda entity: (b"jpeg", "image/jpeg") if entity == other else None
    app = create_app(Settings(tmp_path), home_service=home, voice_service=FakeVoice())
    with TestClient(app) as client:
        assert client.post("/api/music/config", json={"entity_id": PLAYER}).status_code == 200
        outputs = client.get("/api/music/players?music_assistant_only=true").json()
        assert outputs["selected"] == PLAYER
        assert [row["entity_id"] for row in outputs["items"]] == [other]

        status = client.get("/api/music/config", params={"entity_id": other})
        assert status.json()["player_entity_id"] == other
        url = status.json()["current"]["artwork_url"]
        assert "private" not in url
        image = client.get(url)
        assert (image.status_code, image.headers["content-type"], image.content) == (200, "image/jpeg", b"jpeg")

        assert client.post("/api/music/play", json={"entity_id": other, "query": "Airbourne"}).status_code == 200
        assert client.post("/api/music/control", json={"entity_id": other, "action": "pause"}).status_code == 200
        assert client.post("/api/music/control", json={"entity_id": other, "action": "seek", "position": 15}).status_code == 200
        for action, service in (("next", "media_next_track"), ("previous", "media_previous_track")):
            response = client.post("/api/music/control", json={"entity_id": other, "action": action})
            assert response.status_code == 200
            assert home.calls[-1] == ("media_player", service, {"entity_id": other})
        assert [call[2]["entity_id"] for call in home.calls] == [other] * 5
        assert client.post("/api/music/play", json={"entity_id": "media_player.salon_amp_salon",
                                                   "query": "Airbourne"}).status_code == 502
        assert len(home.calls) == 5
        assert client.get("/api/music/config").json()["player_entity_id"] == PLAYER


def test_playlists_saved_by_uri_and_old_config_is_compatible(tmp_path):
    home = FakeHome()
    music = Music(home, tmp_path)
    music.configure(PLAYER)
    with TestClient(create_app(Settings(tmp_path), home_service=home, voice_service=FakeVoice())) as client:
        playlists = client.get("/api/music/playlists")
        assert playlists.status_code == 200
        assert [x["provider"] for x in playlists.json()["items"]] == ["Library", "Qobuz"]
        chosen = playlists.json()["items"][1]
        saved = client.post("/api/music/config", json={"entity_id": PLAYER, "duck_percent": 25,
                                                          "default_playlist": chosen})
        assert saved.status_code == 200 and saved.json()["default_playlist"] == chosen
        # Un ancien client sans nouveau champ conserve la playlist.
        old = client.post("/api/music/config", json={"entity_id": PLAYER, "duck_percent": 30})
        assert old.json()["duck_percent"] == 30 and old.json()["default_playlist"] == chosen
        invalid = client.post("/api/music/config", json={"entity_id": PLAYER, "duck_percent": 25,
                                                           "default_playlist": {"uri": "javascript:bad", "name": "X", "provider": "Qobuz"}})
        assert invalid.status_code == 422


def test_duck_api_is_owned_by_the_browser_session(tmp_path):
    home = FakeHome()
    home.player_state["state"] = "playing"
    with TestClient(create_app(Settings(tmp_path), home_service=home, voice_service=FakeVoice())) as client:
        client.post("/api/music/config", json={"entity_id": PLAYER, "duck_percent": 20})
        result = client.post("/api/music/duck", json={"session_id": "music-browser-session-1"})
        assert result.json() == {"ducked": True, "owned": True, "volume_level": 0.08, "confirmed": True}
        denied = client.post("/api/music/restore", json={"session_id": "music-browser-session-2"})
        assert denied.json()["reason"] == "other_interaction"
        restored = client.post("/api/music/restore", json={"session_id": "music-browser-session-1"})
        assert restored.json()["restored"] is True


def test_direct_voice_style_command_without_configured_llm(tmp_path, monkeypatch):
    home = FakeHome(tmp_path)
    from alfred.home_catalog import HomeCatalog
    monkeypatch.setattr(HomeCatalog, "snapshot", lambda self: {
        "entities": [{"entity_id": PLAYER, "domain": "media_player", "allowed": True,
            "supported": True, "capabilities": ["read", "media_pause", "volume_set", "volume_mute",
            "media_previous_track", "media_next_track", "volume_up", "volume_down", "media_stop", "media_play"]}],
        "excluded": []})
    Music(home, tmp_path).configure(PLAYER)
    ai = FakeConversation()
    ai.status = lambda: {"configured": False}
    with TestClient(create_app(Settings(tmp_path), home_service=home,
                               voice_service=FakeVoice(), conversation_service=ai)) as client:
        response = client.post("/api/conversation/text", json={
            "text":"Mets Airbourne sur l'ampli", "session_id":"music-session-0001"})
        events = [json.loads(line) for line in response.text.splitlines()]
        assert ai.calls == 0
        assert events[-1]["mode"] == "music"
        assert events[-1]["timings"]["llm_ms"] == 0
        assert home.calls[-1][1] == "play_media"


def test_conversation_tool_uses_music_service(tmp_path):
    requests = []
    def handler(request):
        requests.append(json.loads(request.content))
        event = {"choices":[{"delta":{"tool_calls":[{"index":0,"function":{
            "name":"jouer_musique", "arguments":json.dumps({"titre":"Airbourne", "media_type":"artist"})
        }}]}, "finish_reason":"tool_calls"}]}
        return httpx.Response(200, headers={"content-type":"text/event-stream"},
                              text="data: " + json.dumps(event) + "\n\ndata: [DONE]\n\n")

    class EngineMusic:
        def play(self, query, media_type, artist=None):
            assert (query, media_type, artist) == ("Airbourne", "artist", None)
            return {"message":"Lecture demandée à l'ampli du salon."}

    credentials = CredentialStore(tmp_path, api_key="fake-test-key-not-real")
    engine = ConversationService(credentials,
                                 lambda: httpx.Client(transport=httpx.MockTransport(handler)))
    engine.music = EngineMusic()
    result = list(engine.stream("Mets Airbourne", "music-session-0002", threading.Event()))
    assert "Lecture demandée" in result[-1]["text"]
    tool_names = {tool["function"]["name"] for tool in requests[0]["tools"]}
    assert {"jouer_musique", "controler_musique"} <= tool_names
