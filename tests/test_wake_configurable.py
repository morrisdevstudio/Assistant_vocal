import asyncio
import copy
import json
import threading
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from alfred.app import create_app
from alfred.config import Settings
from alfred.terminal import DirectTerminal, TerminalConfig
from alfred.wake_settings import WakeSettings, strip_prefix
from alfred.wake_stt import STTWakeDetector
from alfred.validate_wake_model import embedded
from alfred.voice import VoiceBusy, VoiceService


@pytest.mark.parametrize("text,expected,matched", [
    ("ALFÍ, allume la lampe", "allume la lampe", True),
    ("Alfy allume la lampe", "allume la lampe", True),
    ("Alfy", "", True), ("Fred allume", "Fred allume", False),
    ("Alfred allume", "Alfred allume", False),
    ("parle à Alfy", "parle à Alfy", False),
    ("Alfylou", "Alfylou", False), ("silence", "silence", False),
])
def test_only_initial_whole_words_are_matched(text, expected, matched):
    assert strip_prefix(text, ["Alfy", "Alfi"]) == (expected, matched)


def test_migrate_and_preserve_both_engines_and_sources(tmp_path):
    terminal = TerminalConfig("board.local", "aa:bb:cc:dd:ee:ff", "127.0.0.1",
        wake_name="jarvis", wake_model="jarvisse_20260916_004415.onnx", wake_threshold=.5)
    settings = WakeSettings(tmp_path / "data", tmp_path / "models", terminal)
    assert settings.values["esp32"]["model"] == terminal.wake_model
    value = {**settings.values["esp32"], "engine": "stt", "phrase": "Alfred", "variants": []}
    settings.save("esp32", value)
    loaded = WakeSettings(tmp_path / "data", tmp_path / "models", terminal)
    assert loaded.values["esp32"] == value
    assert loaded.values["browser"]["phrase"] == "Alfy"
    assert loaded.values["esp32"]["threshold"] == .5
    assert loaded.values["browser"]["engine"] == "stt"


def test_resume_preference_migrates_without_arming_and_survives_settings_changes(tmp_path):
    settings = WakeSettings(tmp_path, tmp_path)
    settings.save("esp32", settings.values["esp32"])
    legacy = json.loads(settings.path.read_text())
    legacy.pop("resume_esp32")
    settings.path.write_text(json.dumps(legacy))
    settings = WakeSettings(tmp_path, tmp_path)
    assert settings.resume_esp32 is False
    settings.save_resume(True)
    settings.save("esp32", {**settings.values["esp32"], "engine": "stt"})
    loaded = WakeSettings(tmp_path, tmp_path)
    assert loaded.resume_esp32 is True
    assert loaded.values["esp32"]["engine"] == "stt"


def test_service_restores_esp32_before_network_is_available(tmp_path, monkeypatch):
    from alfred.wake_manager import WakeManager
    class Detector:
        def reset_audio(self): pass
        def status(self): return {"detections": 0}
    config = TerminalConfig("board.local", "aa:bb:cc:dd:ee:ff", "127.0.0.1", wake_word=True)
    (tmp_path / "terminal.json").write_text(json.dumps({"enabled": True, **config.__dict__}))
    preferences = WakeSettings(tmp_path, tmp_path / "models", config)
    preferences.save_resume(True)
    async def disconnected(terminal):
        await terminal.stopping.wait()
    async def prepare(*args): return Detector()
    monkeypatch.setattr(DirectTerminal, "_run", disconnected)
    monkeypatch.setattr("alfred.app.load_wake_detector", lambda *args: (Detector(), None))
    monkeypatch.setattr(WakeManager, "prepare", prepare)
    for _ in range(2):
        with TestClient(create_app(Settings(tmp_path, poll_seconds=.02), voice_service=FakeVoice())) as client:
            terminal = client.app.state.terminal
            assert not terminal.connected
            assert terminal.wake_armed and terminal.wake_gate is not None
            assert terminal.wake_monitor is not None
            assert client.app.state.wake_manager.owner == "esp32"
    assert WakeSettings(tmp_path, tmp_path / "models").resume_esp32 is True


@pytest.mark.parametrize("route", ["/api/wake/stop/esp32", "/api/terminal/wake-word/stop"])
def test_explicit_stop_disables_resume(client, route):
    manager = client.app.state.wake_manager
    manager.preferences.save_resume(True)
    assert client.post(route, json={}).status_code == 200
    assert manager.preferences.resume_esp32 is False
    assert WakeSettings(manager.preferences.path.parent, manager.preferences.folder.parent).resume_esp32 is False


@pytest.mark.parametrize("change", [{"model": "../secret.onnx"}, {"phrase": ""},
    {"phrase": "un deux trois quatre cinq"}, {"variants": ["x"] * 9}, {"threshold": True},
    {"threshold": float("nan")}, {"engine": "remote"}])
def test_invalid_config_never_replaces_preferences(tmp_path, change):
    settings = WakeSettings(tmp_path, tmp_path)
    before = copy.deepcopy(settings.values)
    with pytest.raises(ValueError):
        settings.save("browser", {**settings.values["browser"], **change})
    assert settings.values == before
    assert not settings.path.exists()


class FakeVAD:
    def feed(self, data):
        return any(data)


def pcm(seconds, speech=True):
    return (b"\x01\x00" if speech else b"\x00\x00") * round(seconds * 16000)


def feed(detector, seconds, speech=True):
    data = pcm(seconds, speech)
    for at in range(0, len(data), 1024):
        detector.feed(data[at:at+1024])


def test_stt_keeps_command_audio_received_during_inference_and_matches_once():
    async def scenario():
        entered, release = threading.Event(), threading.Event()
        captures = []
        def transcribe(wav):
            entered.set()
            assert release.wait(3)
            return "Alfi allume la lumière", 1, 1
        async def detected(audio):
            captures.append(audio)
        detector = STTWakeDetector(transcribe, ["Alfy", "Alfi"], detected, FakeVAD)
        feed(detector, .7)
        await asyncio.to_thread(entered.wait, 2)
        feed(detector, .7)
        release.set()
        await detector.task
        assert len(captures) == 1
        assert len(captures[0]) >= len(pcm(1.3))
        assert detector.detections == 1
        assert "text" not in detector.status()
        feed(detector, .5)
        assert detector.detections == 1
    asyncio.run(scenario())


@pytest.mark.parametrize("text,expected", [("Alfy tu m'entends", 1), ("bruit sans interpellation", 0)])
def test_energy_backup_survives_a_vad_that_never_accepts_speech(text, expected):
    class StuckVAD:
        active = False
        def feed(self, data):
            return False

    async def scenario():
        captures = []
        async def detected(audio):
            captures.append(audio)
        detector = STTWakeDetector(lambda _: text, ["Alfy"], detected, StuckVAD)
        data = b"\xe8\x03" * 12800
        for offset in range(0, len(data), 1024):
            detector.feed(data[offset:offset + 1024])
        await detector.task
        assert detector.status()["energy_fallbacks"] > 0
        assert len(captures) == expected
    asyncio.run(scenario())


def test_rejected_wake_can_detect_the_next_request():
    async def scenario():
        captures = []
        async def callback(audio):
            captures.append(audio)
            return len(captures) > 1
        detector = STTWakeDetector(lambda _: "Alfy", ["Alfy"], callback, FakeVAD)
        feed(detector, .7)
        await detector.task
        assert not detector.status()["latched"]
        feed(detector, .7)
        await detector.task
        assert len(captures) == 2
        assert detector.status()["latched"]
    asyncio.run(scenario())


def test_stop_invalidates_late_stt_result_and_does_not_queue_multiple_workers():
    async def scenario():
        entered, release = threading.Event(), threading.Event()
        captures = []
        calls = []
        def transcribe(wav):
            calls.append(wav)
            entered.set()
            assert release.wait(3)
            return "Alfy"
        async def detected(audio):
            captures.append(audio)
        detector = STTWakeDetector(transcribe, ["Alfy"], detected, FakeVAD)
        feed(detector, .6)
        await asyncio.to_thread(entered.wait, 2)
        for _ in range(10):
            feed(detector, .3)
        detector.reset_audio()
        release.set()
        await detector.task
        assert not captures
        assert len(calls) == 1
    asyncio.run(scenario())


@pytest.mark.parametrize("text", ["Fred", "Alfred", "elle a fini", "parle à Alfy", ""])
def test_stt_does_not_activate_for_negatives(text):
    async def scenario():
        captures = []
        async def detected(audio):
            captures.append(audio)
        detector = STTWakeDetector(lambda _: text, ["Alfy", "Alfi"], detected, FakeVAD)
        feed(detector, .8)
        feed(detector, .8, False)
        await detector.task
        assert not captures
        assert detector.inferences == 1
    asyncio.run(scenario())


def test_silence_never_calls_stt():
    async def scenario():
        detector = STTWakeDetector(lambda _: pytest.fail("Silence transcrit"), ["Alfy"], vad_factory=FakeVAD)
        feed(detector, 10, False)
        assert detector.task is None
        assert len(detector.pre) <= .35 * 32000
    asyncio.run(scenario())


def test_external_onnx_data_rejected_even_inside_nested_graph():
    def field(number, data):
        return bytes([number * 8 + 2, len(data)]) + data
    external = field(13, b"location")
    model = field(7, field(5, external))
    with pytest.raises(ValueError, match="externes"):
        embedded(model)
    embedded(field(7, field(5, b"")))
    with pytest.raises(ValueError):
        embedded(b"not-an-onnx")


def test_foreground_waits_for_native_wake_inference_and_new_wake_yields(tmp_path, monkeypatch):
    engine = VoiceService(tmp_path)
    entered, release = threading.Event(), threading.Event()
    order = []
    errors = []
    def recognize(data):
        order.append("wake-start")
        entered.set()
        assert release.wait(3)
        order.append("wake-end")
        return "Alfy"
    monkeypatch.setattr(engine, "_recognize", recognize)
    monkeypatch.setattr(engine, "_check", lambda **kwargs: None)
    monkeypatch.setattr(engine, "_synthesize", lambda text: order.append("speak") or b"audio")
    from alfred.wake_stt import wav_pcm
    def background():
        try: engine.transcribe_wake(wav_pcm(pcm(.5)))
        except Exception as error: errors.append(error)
    def foreground():
        try: engine.speak("bonjour")
        except Exception as error: errors.append(error)
    wake = threading.Thread(target=background)
    command = threading.Thread(target=foreground)
    wake.start()
    assert entered.wait(2)
    try:
        with pytest.raises(VoiceBusy): engine.transcribe_wake(wav_pcm(pcm(.5)))
        command.start()
    finally:
        release.set()
        wake.join(3)
        if command.ident: command.join(3)
    assert not errors
    assert order == ["wake-start", "wake-end", "speak"]


class FakeVoice:
    def status(self):
        return {"stt_available": True, "tts_available": True}
    def transcribe(self, audio):
        return "Alfy allume la lampe", 1, 1
    def speak(self, text):
        return b"", 0


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(Settings(tmp_path, poll_seconds=.02), voice_service=FakeVoice())) as client:
        yield client


def test_config_api_failed_preparation_and_busy_are_transactional(client, monkeypatch):
    manager = client.app.state.wake_manager
    before = copy.deepcopy(manager.preferences.values)
    async def fail(*args):
        raise ValueError("Modèle indisponible")
    monkeypatch.setattr(manager, "prepare", fail)
    result = client.put("/api/wake/config/browser", json=before["browser"])
    assert result.status_code == 409
    assert manager.preferences.values == before
    assert client.get("/api/wake/config").json()["settings"] == before
    manager.busy = True
    result = client.put("/api/wake/config/browser", json=before["browser"])
    assert result.status_code == 409
    assert "cours" in result.json()["detail"]


def test_config_api_persists_and_rejects_cross_origin(client, monkeypatch):
    manager = client.app.state.wake_manager
    async def prepare(*args):
        return object()
    monkeypatch.setattr(manager, "prepare", prepare)
    value = {**manager.preferences.values["browser"], "phrase": "Mon Alfred"}
    assert client.put("/api/wake/config/browser", json=value).status_code == 200
    assert json.loads(manager.preferences.path.read_text(encoding="utf-8"))["browser"] == value
    assert client.put("/api/wake/config/browser", json=value, headers={"Origin": "https://evil.example"}).status_code == 403


def test_import_invalid_model_has_no_catalogue_entry(client):
    result = client.post("/api/wake/models", json={"label": "Alfy", "phrase": "Alfy", "model_base64": "YmFk"})
    assert result.status_code == 422
    assert not client.app.state.wake_manager.preferences.custom
    assert not list(client.app.state.wake_manager.preferences.folder.glob("custom-*.onnx"))


def test_websocket_requires_same_origin(client):
    from starlette.websockets import WebSocketDisconnect
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/wake/browser", headers={"Origin": "https://evil.example"}):
            pass


def test_browser_ownership_replaces_previous_socket_and_invalidates_ticket(client, monkeypatch):
    manager = client.app.state.wake_manager
    manager.preferences.save_resume(True)
    class Detector:
        def feed(self, data): return False
        def reset_audio(self): pass
        def status(self): return {"detections": 0}
    async def prepare(*args): return Detector()
    monkeypatch.setattr(manager, "prepare", prepare)
    with client.websocket_connect("/api/wake/browser", headers={"Origin": "http://testserver"}) as socket:
        assert socket.receive_json()["type"] == "ready"
        token = manager.ticket(["Alfy"])
        assert manager.consume(token) == ["Alfy"]
        with pytest.raises(ValueError): manager.consume(token)
        with client.websocket_connect("/api/wake/browser", headers={"Origin": "http://testserver"}) as other:
            assert other.receive_json()["type"] == "ready"
            assert socket.receive_json()["type"] == "stopped"
            assert manager.owner == "browser"
            other.send_json({"type": "resume"})
            assert other.receive_json()["type"] == "ready"
    assert manager.browser is None
    assert manager.owner is None
    assert manager.preferences.resume_esp32 is False


def test_browser_capture_keeps_complete_audio_and_only_issues_one_ticket(client, monkeypatch):
    import base64
    import io
    import wave
    import alfred.wake_browser as browser_module
    monkeypatch.setattr(browser_module, "SpeechActivity", FakeVAD)
    manager = client.app.state.wake_manager
    class Detector:
        def __init__(self): self.samples = 0
        def feed(self, data):
            self.samples += len(data)
            return self.samples >= 16000
        def reset_audio(self): self.samples = 0
        def status(self): return {"detections": 0}
    async def prepare(*args): return Detector()
    monkeypatch.setattr(manager, "prepare", prepare)
    with client.websocket_connect("/api/wake/browser", headers={"Origin": "http://testserver"}) as socket:
        assert socket.receive_json()["type"] == "ready"
        for _ in range(25): socket.send_bytes(pcm(.032))
        assert socket.receive_json()["type"] == "detected"
        assert client.put("/api/wake/config/browser", json=manager.preferences.values["browser"]).status_code == 409
        for _ in range(32): socket.send_bytes(pcm(.032, False))
        result = socket.receive_json()
        assert result["type"] == "command"
        with wave.open(io.BytesIO(base64.b64decode(result["audio_base64"]))) as wav:
            assert wav.getframerate() == 16000
            assert wav.readframes(12800) == pcm(.8)
        assert manager.consume(result["turn"]) == ["Alfy", "Alfi"]
        with pytest.raises(ValueError): manager.consume(result["turn"])


@pytest.mark.parametrize("transcript,mode", [("Alfy", "wake_empty"),
    ("Alfi mets un minuteur de trois minutes", "timer"), ("Al fit allume la lampe", "error")])
def test_dynamic_wake_prefix_is_removed_before_any_tool_or_ai(tmp_path, transcript, mode):
    from alfred.wake_stt import wav_pcm
    class Voice(FakeVoice):
        def transcribe(self, audio): return transcript, 1, 1
    class Conversation:
        def status(self): return {"configured": False}
        def stream(self, *args, **kwargs):
            pytest.fail("Ne doit pas appeler l'IA")
        def reset(self, *args): pass
    with TestClient(create_app(Settings(tmp_path, poll_seconds=.02), voice_service=Voice(),
                              conversation_service=Conversation())) as client:
        manager = client.app.state.wake_manager
        manager.owner = "browser"
        token = manager.ticket(["Alfy", "Alfi"])
        response = client.post("/api/conversation/voice", content=wav_pcm(pcm(1)), headers={
            "Content-Type": "audio/wav", "X-Alfred-Session": "wake-test-browser-0001",
            "X-Alfred-Floor": "rdc", "X-Alfred-Wake-Source": "browser", "X-Alfred-Wake-Turn": token})
        assert response.status_code == 200
        events = [json.loads(line) for line in response.text.splitlines()]
        assert events[-1]["type"] == ("error" if mode == "error" else "done"), events
        if mode != "error":
            assert events[-1]["mode"] == mode
        else:
            assert "variantes" in events[-1]["message"]
        assert client.post("/api/conversation/voice", content=wav_pcm(pcm(1)), headers={
            "Content-Type": "audio/wav", "X-Alfred-Session": "wake-test-browser-0001",
            "X-Alfred-Wake-Source": "browser", "X-Alfred-Wake-Turn": token}).status_code == 409


def test_terminal_rejects_unconfirmed_wake_without_signalling_device_error(tmp_path, monkeypatch):
    from alfred.wake_stt import wav_pcm

    class Voice(FakeVoice):
        def transcribe(self, audio):
            return "Fred, tu peux me donner les résultats des EL2 ?", 1, 1

    async def disconnected(terminal):
        await terminal.stopping.wait()

    config = TerminalConfig("board.local", "aa:bb:cc:dd:ee:ff", "127.0.0.1")
    (tmp_path / "terminal.json").write_text(json.dumps({"enabled": True, **config.__dict__}))
    monkeypatch.setattr(DirectTerminal, "_run", disconnected)
    app = create_app(Settings(tmp_path, poll_seconds=.02), voice_service=Voice())
    with TestClient(app) as client:
        terminal = app.state.terminal
        preferences = app.state.wake_manager.preferences
        preferences.values["esp32"].update(engine="stt", phrase="Alfred", variants=[])
        terminal.last_capture_source = "wake_word"
        rearm = AsyncMock()
        events = []
        monkeypatch.setattr(terminal, "_rearm_wake_word", rearm)
        monkeypatch.setattr(terminal, "_event", lambda name, data=None: events.append(name))
        client.portal.call(terminal._process, wav_pcm(pcm(1)))

        assert events == ["INTENT_END", "RUN_END"]
        assert terminal.wake_rejected == 1 and terminal.error is None
        assert "Aucun appel IA" in terminal.conversation_text()["exchange"]["error"]
        rearm.assert_awaited_once_with()
