import copy
import json
import threading

import pytest

from alfred.home_assistant import HomeError, HomeService, HomeStore
from alfred.home_catalog import HomeCatalog
from alfred.intent_context import CURRENT_TURN
from alfred.intents import IntentService
from alfred.music import Music
from alfred.music_actions import MusicAction, MusicActions, MusicPlan


PLAYER = "media_player.amp_salon_2"
PLAYLIST = {"uri": "qobuz://playlist/favorite", "name": "Ma sélection", "provider": "Qobuz"}


class Home(HomeService):
    def __init__(self, folder):
        super().__init__(HomeStore(folder, base_url="http://ha.test:8123", token="test", room="Bureau"))
        self.state = {"entity_id": PLAYER, "state": "idle", "attributes": {
            "friendly_name": "AMP_SALON", "supported_features": 1 + 4 + 8 + 16 + 32 + 64 + 128 + 256 + 4096 + 16384,
            "volume_level": .4, "is_volume_muted": False}}
        self.entries = [{"entity_id": PLAYER, "domain": "media_player", "name": "AMP_SALON", "allowed": True,
                         "supported": True, "capabilities": ["read", "media_pause", "volume_set", "volume_mute",
                         "media_previous_track", "media_next_track", "volume_up", "volume_down", "media_stop", "media_play"]}]
        self.calls = []
        self.apply = True
        self.fail = False

    def get_state(self, entity):
        return copy.deepcopy(self.state)

    def call_service(self, domain, service, payload):
        self.calls.append((domain, service, payload))
        if self.fail:
            raise HomeError("Réponse perdue")
        if self.apply:
            if service == "volume_set": self.state["attributes"]["volume_level"] = payload["volume_level"]
            if service == "volume_mute": self.state["attributes"]["is_volume_muted"] = payload["is_volume_muted"]
            if service == "media_play": self.state["state"] = "playing"
            if service == "media_pause": self.state["state"] = "paused"
            if service == "media_stop": self.state["state"] = "idle"


@pytest.fixture
def rig(tmp_path, monkeypatch):
    home = Home(tmp_path)
    monkeypatch.setattr(HomeCatalog, "snapshot", lambda self: {"entities": copy.deepcopy(home.entries), "excluded": []})
    music = Music(home, tmp_path)
    music.configure(PLAYER, default_playlist=PLAYLIST)
    controller = MusicActions(home, music)
    service = IntentService(home, tmp_path)
    service.music_actions = controller
    return home, music, controller, service


class Turn:
    floor = "rdc"
    cancelled = threading.Event()


def act(op, value=None):
    return MusicAction(operation=op, value=value)


def test_default_playlist_and_config_preserve_old_values(rig, tmp_path):
    home, music, controller, _ = rig
    result = controller.execute([act("play_default")])
    assert result["status"] in {"confirmed", "unconfirmed"}
    assert home.calls[-1][0:2] == ("music_assistant", "play_media")
    assert home.calls[-1][2]["media_id"] == PLAYLIST["uri"]
    music.configure(PLAYER, duck_percent=30)
    assert music.default_playlist() == PLAYLIST
    assert music._config()["duck_percent"] == 30


def test_missing_default_playlist_is_refused(rig):
    home, music, controller, _ = rig
    music.path.write_text(json.dumps({"player_entity_id": PLAYER, "duck_percent": 25}), encoding="utf-8")
    result = controller.execute([act("play_default")])
    assert result["status"] == "refused" and not home.calls


def test_only_configured_salon_player_is_accepted(rig):
    home, music, controller, _ = rig
    music.path.write_text(json.dumps({"player_entity_id": "media_player.desktop_gkejd2g", "duck_percent": 25}), encoding="utf-8")
    assert controller.execute([act("pause")])["status"] == "refused"
    assert not home.calls


def test_music_read_uses_title_and_artist_only_when_a_track_is_loaded(rig):
    home, _, controller, _ = rig
    home.state["attributes"].update(media_title="Les passantes", media_artist="Georges Brassens")
    home.state["state"] = "playing"
    assert controller.execute([act("read")])["reply"] == "Tu écoutes « Les passantes », de Georges Brassens."
    home.state["state"] = "paused"
    assert controller.execute([act("read")])["reply"].endswith("est en pause.")
    home.state["state"] = "idle"
    assert "Aucun morceau" in controller.execute([act("read")])["reply"]
    assert not home.calls


def test_volume_uses_five_point_step_and_is_clamped(rig):
    home, _, controller, _ = rig
    home.state["state"] = "playing"
    assert controller.execute([act("volume_delta", -5)])["status"] == "confirmed"
    assert home.state["attributes"]["volume_level"] == .35
    home.state["attributes"]["volume_level"] = .02
    assert controller.execute([act("volume_delta", -5)])["status"] == "confirmed"
    assert home.state["attributes"]["volume_level"] == 0


def test_duck_reference_is_not_used_as_normal_volume(rig):
    home, music, controller, _ = rig
    home.state["state"] = "playing"
    duck = music.duck("session-music-00001")
    assert duck["volume_level"] == .1
    assert controller.execute([act("volume_delta", -5)])["status"] == "confirmed"
    assert home.state["attributes"]["volume_level"] == .35
    assert music.restore("session-music-00001")["restored"] is False
    assert home.state["attributes"]["volume_level"] == .35


@pytest.mark.parametrize("op", ["mute", "unmute"])
def test_mute_and_unmute_are_verified(rig, op):
    home, _, controller, _ = rig
    assert controller.execute([act(op)])["status"] == "confirmed"
    assert home.state["attributes"]["is_volume_muted"] == (op == "mute")


def test_uncertain_exact_volume_stops_next_action(rig):
    home, _, controller, _ = rig
    home.apply = False
    result = controller.execute([act("volume", 30), act("pause")])
    assert result["status"] == "unconfirmed" and len(home.calls) == 1


def test_lost_music_response_never_repeats(rig):
    home, _, controller, _ = rig
    home.fail = True
    result = controller.execute([act("volume", 30)])
    assert result["status"] == "unconfirmed" and len(home.calls) == 1


def test_invalid_music_plan_rejected_before_dispatch(rig):
    with pytest.raises(ValueError):
        MusicAction(operation="volume", value=101)


def test_context_ambiguity_then_music_volume(rig):
    home, _, _, service = rig
    home.state["state"] = "playing"
    turn = service.context.begin(("browser", "music-session-0001", "guest"), "mets de la musique", threading.Event(), "rdc")
    token = CURRENT_TURN.set(turn)
    try:
        assert service.handle_local(turn.text, turn)["status"] in {"confirmed", "unconfirmed"} and len(home.calls) == 1
        follow = service.context.begin(("browser", "music-session-0001", "guest"), "mets à trente pour cent", threading.Event(), "rdc")
        # Une playlist par défaut a été envoyée : on peut régler le volume,
        # mais l'accord exact du curseur n'est pas automatisé.
        assert service.handle_local(follow.text, follow)["status"] == "confirmed"
        first = service.context.begin(("browser", "music-session-0001", "guest"), "baisse un peu", threading.Event(), "rdc")
        service.run_music([act("volume", 50)], first)
        second = service.context.begin(("browser", "music-session-0001", "guest"), "baisse un peu", threading.Event(), "rdc")
        assert service.handle_local(second.text, second)["status"] == "confirmed"
        assert home.state["attributes"]["volume_level"] == .45
    finally:
        CURRENT_TURN.reset(token)


def test_context_correction_and_same_session(rig):
    home, _, _, service = rig
    home.state["state"] = "playing"
    turn = service.context.begin(("browser", "music-session-0002", "guest"), "mets à cinquante pour cent", threading.Event(), "rdc")
    token = CURRENT_TURN.set(turn)
    try:
        service.run_music([act("volume", 50)], turn)
        follow = service.context.begin(("browser", "music-session-0002", "guest"), "non, vingt-cinq pour cent", threading.Event(), "rdc")
        assert service.handle_local(follow.text, follow)["status"] == "confirmed"
    finally:
        CURRENT_TURN.reset(token)


def test_four_actions_are_prepared_before_dispatch(rig):
    home, _, controller, _ = rig
    home.entries[0]["capabilities"].remove("media_play")
    result = controller.execute([act("pause"), act("resume")])
    assert result["status"] == "confirmed" and len(home.calls) == 2


def test_direct_music_returns_playlist_command(rig, tmp_path):
    home, _, _, service = rig
    turn = service.context.begin(("esp32", "music-session-0003", "guest"), "mets de la musique", threading.Event(), "rdc")
    token = CURRENT_TURN.set(turn)
    try:
        result = service.handle_local(turn.text, turn)
        assert result["status"] == "unconfirmed"
        assert home.calls[-1][2]["media_id"] == PLAYLIST["uri"]
    finally:
        CURRENT_TURN.reset(token)
