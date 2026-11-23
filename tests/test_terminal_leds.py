from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from alfred.app import create_app
from alfred.config import Settings
from alfred.terminal_leds import TerminalLeds


def test_palette_api_merges_and_persists_changes(tmp_path):
    path = "/api/terminal/leds"
    file = tmp_path / "terminal-leds.json"
    file.write_text('{"listening": "#123456"}', encoding="utf-8")
    with TestClient(create_app(Settings(tmp_path))) as client:
        original = client.get(path).json()
        assert original["colors"]["standby"] is None and not original["connected"]
        assert original["colors"]["listening"] == "#123456"
        assert set(original["effects"].values()) == {"solid"}
        assert "rotation" in original["effect_options"]
        response = client.post(path, json={"colors": {"listening": "#00aaff", "processing": "#000000"}})
        assert response.status_code == 200
        assert response.json()["colors"] == {**original["colors"], "listening": "#00AAFF", "processing": None}
        effect = client.post(path, json={"effects": {"listening": "rotation", "standby": "breathing"}})
        assert effect.status_code == 200
        assert effect.json()["effects"] == {**original["effects"], "listening": "rotation", "standby": "breathing"}
        assert effect.json()["colors"] == response.json()["colors"]
        assert client.post(path, json={"effects": {"error": "Volume Level"}}).status_code == 422
        for colors in ({}, {"anything": "#FFFFFF"}, {"error": "rainbow"}):
            assert client.post(path, json={"colors": colors}).status_code == 422
        assert client.post(path, json={"colors": {"standby": "#FFFFFF"}},
                           headers={"Origin": "https://example.com"}).status_code == 403
    reloaded = TerminalLeds(file)
    assert reloaded.colors == response.json()["colors"]
    assert reloaded.effects == effect.json()["effects"]


def test_animation_changes_at_same_color_and_is_ignored_when_off():
    api = pytest.importorskip("aioesphomeapi")
    leds = TerminalLeds()
    leds.attach([api.LightInfo(key=1, object_id="status_ring", effects=["None", "Spinner"])])
    terminal = SimpleNamespace(phase="waking", error=None, bell_active=False, bell_test=False, client=Mock())
    assert leds.effect_options() == ["solid", "rotation"]
    leds.observe(api.LightState(key=1, state=True, effect="None"))
    leds.colors["standby"] = "#FFFFFF"
    leds.update(terminal, 1)
    leds.effects["standby"] = "rotation"
    leds.update(terminal, 1.1)
    assert terminal.client.light_command.call_count == 2
    assert terminal.client.light_command.call_args.kwargs["effect"] == "Spinner"

    leds.observe(api.LightState(key=1, state=True, effect="Spinner", brightness=.25,
                               color_brightness=1, red=1, green=1, blue=1))
    leds.update(terminal, 3)
    assert terminal.client.light_command.call_count == 2
    leds.effects["standby"] = "comet"
    leds.update(terminal, 4)
    assert terminal.client.light_command.call_args.kwargs["effect"] == "None"
    leds.colors["standby"] = None
    leds.effects["standby"] = "rotation"
    leds.update(terminal, 5)
    terminal.client.light_command.assert_called_with(1, state=False, transition_length=0)


def test_wake_monitoring_clears_stale_reply_and_preserves_local_indicators():
    api = pytest.importorskip("aioesphomeapi")
    leds = TerminalLeds()
    leds.attach([api.LightInfo(key=1, object_id="status_ring"),
                 api.SwitchInfo(key=2, object_id="microphone_mute")])
    terminal = SimpleNamespace(phase="waking", error=None, bell_active=False, bell_test=False, client=Mock())
    leds.observe(api.LightState(key=1, state=True, effect="Wipe"))
    leds.update(terminal, 10)
    terminal.client.light_command.assert_not_called()  # L’état du bouton muet est encore inconnu.
    leds.observe(api.SwitchState(key=2, state=False))
    leds.update(terminal, 10)
    terminal.client.light_command.assert_called_once_with(1, state=False, transition_length=0)
    leds.update(terminal, 10.1)
    assert terminal.client.light_command.call_count == 1

    terminal.phase = "processing"
    leds.observe(api.LightState(key=1, state=False))
    leds.update(terminal, 10.2)
    assert terminal.client.light_command.call_args.kwargs["effect"] == "None"
    assert terminal.client.light_command.call_args.kwargs["rgb"] == pytest.approx((1, 166 / 245, 35 / 245))

    terminal.client.light_command.reset_mock()
    leds.observe(api.SwitchState(key=2, state=True))
    leds.update(terminal, 11)
    leds.observe(api.SwitchState(key=2, state=False))
    terminal.bell_active = True
    leds.update(terminal, 12)
    terminal.bell_active = False
    for effect in ("Volume Level", "Timer Progress"):
        leds.observe(api.LightState(key=1, state=True, effect=effect))
        leds.update(terminal, 13)
    terminal.client.light_command.assert_not_called()
