"""Mot d'appel : trame, seuil, anti-rebond et veille sans second départ."""
import asyncio

import numpy as np
import pytest

from alfred.terminal import Capture, DirectTerminal, TerminalConfig, WakeGate
from alfred.wake_word import FRAME_BYTES, FRAME_SAMPLES, WakeWordError, verify_preprocess


class FakeDetector:
    """Compteur de trames : déclenche une fois, au numéro choisi, sans modèle réel."""
    name = "fake"

    def __init__(self, fire_at=None):
        self.fire_at = fire_at
        self.frames = 0
        self.fired = False
        self.detections = 0

    def feed(self, pcm):
        assert len(pcm) % 2 == 0
        self.frames += len(pcm) // FRAME_BYTES
        if (self.fire_at is not None and not self.fired
                and self.frames >= self.fire_at):
            self.fired = True
            self.detections += 1
            return True
        return False

    def status(self):
        return {"detections": self.detections, "score": 0., "last_detection": 0.,
                "threshold": .5}


def frame():
    return np.zeros(FRAME_SAMPLES, dtype="<i2").tobytes()


def tone(seconds, level=1200):
    return np.full(round(seconds * 16000), level, dtype="<i2").tobytes()


def test_gate_keeps_only_recent_preroll_and_signals_detection():
    detector = FakeDetector(fire_at=3)
    gate = WakeGate(detector, preroll_seconds=.6)
    for _ in range(120):
        gate.feed(frame())
    preroll = gate.take()
    assert detector.detections == 1
    assert len(preroll) <= 19200 + FRAME_BYTES
    assert gate.preroll == bytearray()


def test_gate_preroll_never_exceeds_the_configured_window():
    gate = WakeGate(FakeDetector(), preroll_seconds=.6)
    for _ in range(500):
        gate.feed(frame())
    assert len(gate.preroll) <= int(.6 * 16000) * 2 + FRAME_BYTES


def test_wake_word_is_disabled_by_default_in_terminal_config(tmp_path):
    path = tmp_path / "terminal.json"
    value = {"enabled": True, "host": "board.local", "expected_mac": "00:11:22:33:44:55",
             "media_host": "192.168.77.24"}
    path.write_text(__import__("json").dumps(value))
    config = TerminalConfig.load(path)
    assert config.wake_word is False
    assert config.wake_model == "alfred-he.onnx"
    assert config.wake_threshold == .25


@pytest.mark.parametrize("field,value", [
    ("wake_threshold", 0), ("wake_threshold", 1), ("wake_threshold", "0.5"),
    ("wake_session_seconds", 5), ("wake_session_seconds", 7200),
    ("wake_model", 3), ("wake_word", "oui"),
])
def test_invalid_wake_word_settings_are_rejected(tmp_path, field, value):
    path = tmp_path / "terminal.json"
    data = {"enabled": True, "host": "board.local", "expected_mac": "00:11:22:33:44:55",
            "media_host": "192.168.77.24", field: value}
    path.write_text(__import__("json").dumps(data))
    with pytest.raises(ValueError):
        TerminalConfig.load(path)


def test_preprocess_must_be_present_and_intact(tmp_path):
    with pytest.raises(WakeWordError):
        verify_preprocess(tmp_path)
    for name in ("melspectrogram.onnx", "embedding_model.onnx"):
        (tmp_path / name).write_bytes(b"pas le bon modele")
    with pytest.raises(WakeWordError):
        verify_preprocess(tmp_path)


def test_wake_arming_returns_port_zero_so_the_client_answers():
    async def scenario():
        ports = []
        terminal = DirectTerminal(None, None, None, vad_factory=lambda: None,
                                  wake_detector=FakeDetector())
        terminal.connected = True
        terminal.phase = "idle"
        terminal.services = {"start_va": "start-service"}
        terminal._event = lambda name, data=None: None

        class Client:
            async def execute_service(client, service, data):
                # Le firmware déclenche handle_start ; son retour est le port audio.
                ports.append(await terminal._start_capture("", 0, None, None))
        terminal.client = Client()
        await terminal.start_wake_word()
        # Sans ce port 0, le client Python envoie VoiceAssistantResponse(error=True)
        # et la carte rapporte failed_to_start sans jamais streamer.
        assert ports == [0]
        assert terminal.phase == "waking"
        await terminal.close()
    asyncio.run(scenario())


@pytest.mark.parametrize("recognized,accepted", [("bruit de porte", False), ("Hé Alfred allume", True)])
def test_wake_verifier_blocks_false_activation_before_processing(recognized, accepted):
    async def scenario():
        processed = []
        terminal = DirectTerminal(None, None, None,
                                  transcribe=lambda wav: (recognized, 1., 1),
                                  vad_factory=lambda: None, wake_detector=FakeDetector())
        terminal._event = lambda *args: None
        async def process(wav):
            processed.append(wav)
        terminal._process = process
        await terminal._verify_wake_then_process(b"request", bytearray(tone(1)))
        assert bool(processed) is accepted
        assert terminal.wake_rejected == (0 if accepted else 1)
        await terminal.close()
    asyncio.run(scenario())


def test_button_still_opens_a_capture_while_the_wake_word_is_armed():
    async def scenario():
        calls = []
        terminal = DirectTerminal(None, None, None, vad_factory=lambda: None,
                                  wake_detector=FakeDetector())
        terminal.connected = True
        terminal.phase = "idle"
        terminal.services = {"start_va": "start-service"}
        terminal._event = lambda *args: None

        class Client:
            async def execute_service(client, service, data):
                calls.append(service)
                # Chaque start_va déclenche _start_capture, comme sur la carte.
                await terminal._start_capture("", 0, None, None)
        terminal.client = Client()
        await terminal.start_wake_word()
        assert terminal.wake_primed and terminal.capture is None
        # K2 appuie : un nouveau start_va doit ouvrir une vraie prise.
        await terminal.client.execute_service("start-service", {})
        assert terminal.capture is not None, "K2 doit rester utilisable veille active"
        assert terminal.phase == "listening"
        assert len(calls) == 2
        terminal.stop_wake_word()
        await terminal.close()
    asyncio.run(scenario())


def test_wake_word_keeps_the_followup_window_without_a_second_start():
    async def scenario():
        calls = []
        terminal = DirectTerminal(None, None, None, vad_factory=lambda: None,
                                  wake_detector=FakeDetector())
        terminal.connected = True
        terminal.phase = "idle"
        terminal.services = {"start_va": "start-service"}
        terminal._event = lambda *args: None

        class Client:
            async def execute_service(client, service, data):
                calls.append((service, data))
        terminal.client = Client()
        await terminal.start_wake_word()
        assert len(calls) == 1
        # Après une réponse, la fenêtre de reprise ouvrira une vraie prise.
        terminal.expect_followup = True
        terminal.phase = "idle"
        await terminal._start_capture("", 0, None, None)
        assert terminal.capture is not None, "la reprise de huit secondes doit rester une prise"
        assert len(calls) == 1
        terminal.stop_wake_word()
        await terminal.close()
    asyncio.run(scenario())


def test_wake_detection_starts_capture_without_second_device_start():
    async def scenario():
        calls = []
        class Client:
            async def execute_service(client, service, data):
                calls.append((service, data))
        terminal = DirectTerminal(None, None, None, vad_factory=lambda: None,
                                  wake_detector=FakeDetector())
        terminal.connected = True
        terminal.phase = "idle"
        terminal.client = Client()
        terminal.services = {"start_va": "start-service"}
        terminal._event = lambda *args: None
        assert (await terminal.start_wake_word())["armed"] is True
        assert calls == [("start-service", {})], "un seul départ pour la veille"
        assert terminal.wake_armed and terminal.wake_gate is not None
        # Le flux de la carte alimente le détecteur, pas une prise.
        await terminal._audio(frame())
        assert terminal.capture is None
        terminal.wake_gate.detector.fire_at = 1
        await terminal._audio(frame())
        assert terminal.capture is not None, "le mot ouvre la prise sans redémarrer"
        assert terminal.status()["last_capture_source"] == "wake_word"
        assert terminal.status()["capture_sources"]["wake_word"] == 1
        assert len(calls) == 1
        assert terminal.phase == "waking"
        terminal.stop_wake_word()
        assert not terminal.wake_armed and terminal.wake_gate is None
        await terminal.close()
    asyncio.run(scenario())


def test_wake_audio_is_ignored_while_the_reply_is_playing():
    async def scenario():
        terminal = DirectTerminal(None, None, None, vad_factory=lambda: None,
                                  wake_detector=FakeDetector(fire_at=1))
        terminal.connected = True
        terminal.wake_gate = WakeGate(terminal.wake_detector)
        terminal.wake_armed = True
        terminal.phase = "playing"
        await terminal._audio(tone(.02))
        assert terminal.capture is None
        assert terminal.wake_detector.detections == 0
        terminal.wake_gate = None
        await terminal.close()
    asyncio.run(scenario())


def test_wake_word_requires_a_detector_and_an_idle_terminal():
    async def scenario():
        terminal = DirectTerminal(None, None, None, vad_factory=lambda: None)
        terminal.connected = True
        terminal.phase = "idle"
        with pytest.raises(ValueError):
            await terminal.start_wake_word()
        terminal.wake_detector = FakeDetector()
        terminal.phase = "processing"
        with pytest.raises(ValueError):
            await terminal.start_wake_word()
        await terminal.close()
    asyncio.run(scenario())


def test_status_reports_wake_word_counters_without_audio_or_text():
    async def scenario():
        terminal = DirectTerminal(None, None, None, vad_factory=lambda: None,
                                  wake_detector=FakeDetector())
        terminal.connected = True
        terminal.false_alarms = 2
        payload = terminal.status()
        wake = payload["wake_word"]
        assert wake["enabled"] is True and wake["false_alarms"] == 2
        assert set(wake) == {"enabled", "armed", "receiving", "receiving_seconds",
                             "last_audio_age_seconds", "name", "verification",
                             "detections", "last_wake_at", "threshold", "false_alarms",
                                 "error", "engine", "phrase", "inferences", "last_ms",
                                 "busy", "latched", "pending", "speech_active", "vad_probability", "energy_fallbacks"}
        import json
        assert "Texte" not in json.dumps(payload)
        await terminal.close()
    asyncio.run(scenario())


@pytest.mark.parametrize("name", ["alexa", "jarvis"])
def test_verifier_accepts_configured_name(name):
    async def scenario():
        from types import SimpleNamespace
        processed = []
        terminal = DirectTerminal(SimpleNamespace(wake_name=name), None, None,
                                  transcribe=lambda wav: (f"{name} quelle heure", 1., 1),
                                  vad_factory=lambda: None, wake_detector=FakeDetector())
        terminal._event = lambda *args: None
        async def process(wav):
            processed.append(wav)
        terminal._process = process
        await terminal._verify_wake_then_process(b"request", bytearray(tone(1)))
        assert processed == [b"request"]
        assert terminal.wake_status()["name"] == name
        await terminal.close()
    asyncio.run(scenario())


def test_receiving_requires_recent_wake_audio():
    async def scenario():
        terminal = DirectTerminal(None, None, None, vad_factory=lambda: None,
                                  wake_detector=FakeDetector())
        terminal.connected = terminal.wake_armed = True
        terminal.phase = "waking"
        terminal.wake_gate = WakeGate(terminal.wake_detector)
        assert not terminal.wake_status()["receiving"]
        await terminal._audio(frame())
        assert terminal.wake_status()["receiving"]
        terminal.wake_last_audio -= 7
        assert not terminal.wake_status()["receiving"]
        await terminal.close()
    asyncio.run(scenario())


def test_health_distinguishes_flow_and_reports_stall_without_private_content():
    import json
    import time

    async def scenario():
        terminal = DirectTerminal(None, None, None, vad_factory=lambda: None,
                                  wake_detector=FakeDetector())
        assert terminal.health()["status"] == "ok"
        terminal.connected = terminal.wake_armed = True
        terminal.phase = "waking"
        terminal.wake_gate = WakeGate(terminal.wake_detector)
        assert terminal.health()["components"]["microphone"] == "stalled"
        await terminal._audio(frame())
        health = terminal.health()
        assert health["status"] == "ok"
        assert health["components"]["microphone"] == "ok"
        assert terminal.wake_status()["receiving_seconds"] >= 0
        terminal.wake_last_audio -= 8
        assert terminal.health()["components"]["microphone"] == "stalled"
        assert "texte privé" not in json.dumps(terminal.status(), ensure_ascii=False)
        await terminal.close()

    asyncio.run(scenario())


def test_diagnostic_capture_counts_received_audio_once():
    async def scenario():
        terminal = DirectTerminal(None, None, None, vad_factory=lambda: None)
        terminal.capture = object()
        terminal.diagnostic = True
        data = frame()
        await terminal._audio(data)
        assert terminal.audio_bytes == len(data)
        terminal.capture = None
        await terminal.close()
    asyncio.run(scenario())


def test_microphone_signal_distinguishes_received_zeros_from_real_signal():
    import numpy as np

    async def scenario():
        terminal = DirectTerminal(None, None, None)
        await terminal._audio(bytes(1024))
        assert terminal.micro_zero_since is not None
        assert terminal.status()["micro_signal"]["peak"] == 0
        await terminal._audio(np.array([-32768, 32767], dtype="<i2").tobytes())
        signal = terminal.status()["micro_signal"]
        assert signal["peak"] == 32768
        assert signal["rms"] > 32000
        assert signal["zero_seconds"] == 0
        assert terminal.micro_zero_since is None
        await terminal.close()
    asyncio.run(scenario())


def test_periodic_renewal_is_not_counted_as_incident_recovery():
    import time
    from types import SimpleNamespace

    async def scenario():
        calls = []
        terminal = DirectTerminal(None, None, None, vad_factory=lambda: None,
                                  wake_detector=FakeDetector())
        terminal.connected = terminal.wake_armed = True
        terminal.phase = "waking"
        terminal.wake_gate = WakeGate(terminal.wake_detector)
        terminal.services = {"start_va": "start"}
        terminal._event = lambda *args: None
        async def execute(service, data): calls.append(service)
        terminal.client = SimpleNamespace(execute_service=execute)
        terminal.wake_last_audio = time.monotonic()
        terminal.wake_last_attempt = time.monotonic() - 1000
        await terminal._check_wake_word()
        assert terminal.wake_renewals == 1
        assert terminal.wake_recoveries == 0
        assert terminal.status()["last_recovery_reason"] == "renewal"
        await terminal.close()

    asyncio.run(scenario())


def test_silent_followup_rearms_without_breaking_k2():
    async def scenario():
        calls = []
        terminal = DirectTerminal(None, None, None, vad_factory=lambda: None,
                                  wake_detector=FakeDetector())
        terminal.connected = True
        terminal.phase = "idle"
        terminal.services = {"start_va": "start"}
        terminal._event = lambda *args: None
        class Client:
            async def execute_service(self, service, data):
                calls.append(service)
                await terminal._start_capture("", 0, None, None)
        terminal.client = Client()
        await terminal.start_wake_word()
        terminal.expect_followup = True
        await terminal._start_capture("", 0, None, None)
        assert terminal.capture is not None
        await terminal._capture_timeout(0)
        assert terminal.capture is None and terminal.phase == "waking"
        assert len(calls) == 2
        await terminal._start_capture("", 0, None, None)
        assert terminal.capture is not None
        await terminal.close()
    asyncio.run(scenario())


@pytest.mark.parametrize("ending", ["timeout", "device_stop", "abort"])
def test_followup_end_rearms_without_waiting_for_monitor(ending):
    async def scenario():
        calls = []
        terminal = DirectTerminal(None, None, None, vad_factory=lambda: None,
                                  wake_detector=FakeDetector())
        terminal.connected = terminal.wake_armed = True
        terminal.wake_gate = WakeGate(terminal.wake_detector)
        terminal.wake_primed = True
        terminal.phase = "listening"
        terminal.capture = Capture()
        terminal.services = {"start_va": "start"}
        terminal._event = lambda *args: None
        class Client:
            async def execute_service(self, service, data):
                calls.append(service)
                await terminal._start_capture("", 0, None, None)
                # Céder au scheduler révèle une éventuelle auto-annulation.
                await asyncio.sleep(0)
        terminal.client = Client()
        if ending == "timeout":
            terminal.watchdog = asyncio.create_task(terminal._capture_timeout(0))
            await terminal.watchdog
        else:
            await terminal._stop_capture(ending == "abort")
        assert calls == ["start"]
        assert terminal.phase == "waking"
        await terminal._audio(frame())
        assert terminal.wake_status()["receiving"]
        await terminal.close()
    asyncio.run(scenario())


def test_false_wake_without_speech_discards_audio_and_rearms():
    async def scenario():
        terminal = DirectTerminal(None, None, None, vad_factory=lambda: None,
                                  wake_detector=FakeDetector())
        terminal.connected = terminal.wake_armed = True
        terminal.wake_gate = WakeGate(terminal.wake_detector)
        terminal.capture = Capture()
        terminal.wake_verification_audio = bytearray(tone(1))
        terminal.services = {"start_va": "start"}
        terminal._event = lambda *args: None
        class Client:
            async def execute_service(self, service, data):
                await terminal._start_capture("", 0, None, None)
        terminal.client = Client()
        await terminal._capture_timeout(0)
        assert terminal.wake_verification_audio is None
        assert terminal.wake_silent_rejected == 1
        assert terminal.phase == "waking"
        await terminal.close()
    asyncio.run(scenario())


def test_rearm_failure_is_visible_and_later_retry_can_recover():
    async def scenario():
        terminal = DirectTerminal(None, None, None, vad_factory=lambda: None,
                                  wake_detector=FakeDetector())
        terminal.connected = terminal.wake_armed = True
        terminal.wake_gate = WakeGate(terminal.wake_detector)
        terminal.services = {"start_va": "start"}
        class Client:
            fail = True
            async def execute_service(self, service, data):
                if self.fail:
                    raise OSError()
                await terminal._start_capture("", 0, None, None)
        terminal.client = Client()
        await terminal._rearm_wake_word()
        assert "OSError" in terminal.wake_error
        assert not terminal.wake_status()["receiving"]
        terminal.client.fail = False
        await terminal._rearm_wake_word()
        await terminal._audio(frame())
        assert terminal.wake_status()["receiving"] and terminal.wake_error is None
        await terminal.close()
    asyncio.run(scenario())


def test_monitor_recovers_stalled_stream_and_reconnect():
    async def scenario():
        calls = []
        terminal = DirectTerminal(None, None, None, vad_factory=lambda: None,
                                  wake_detector=FakeDetector())
        terminal.connected = True
        terminal.phase = "idle"
        terminal.services = {"start_va": "start"}
        terminal._event = lambda *args: None
        class Client:
            async def execute_service(self, service, data):
                calls.append(service)
                await terminal._start_capture("", 0, None, None)
        terminal.client = Client()
        await terminal.start_wake_word()
        terminal.wake_last_attempt -= 7
        await terminal._check_wake_word()
        assert len(calls) == 2
        await terminal._audio(frame())
        assert terminal.wake_status()["receiving"]
        terminal.connected = False
        assert not terminal.wake_status()["receiving"]
        terminal.connected = True
        terminal.phase = "idle"
        terminal.wake_last_attempt -= 7
        terminal.wake_last_audio = 0
        await terminal._check_wake_word()
        assert len(calls) == 3
        await terminal._audio(frame())
        assert terminal.wake_status()["receiving"]
        await terminal.close()
    asyncio.run(scenario())


@pytest.mark.parametrize("phase", ["waking", "playing"])
def test_stalled_session_is_stopped_before_restart_without_replaying_command(phase):
    import time
    from types import SimpleNamespace

    async def scenario():
        calls = []
        device = {"active": True}
        terminal = DirectTerminal(None, None, None, vad_factory=lambda: None,
                                  wake_detector=FakeDetector())
        terminal.connected = terminal.wake_armed = True
        terminal.phase = phase
        terminal.wake_gate = WakeGate(terminal.wake_detector)
        terminal.wake_last_attempt = time.monotonic() - 20
        terminal.playback_deadline = time.monotonic() - 1
        terminal.services = {"start_va": "start", "stop_va": "stop"}

        def event(name, data=None):
            calls.append(name)

        async def execute(service, data):
            calls.append(service)
            if service == "stop":
                device["active"] = False
                await terminal._stop_capture(True)
                await terminal._announcement_finished(SimpleNamespace(success=False))
            elif not device["active"]:
                device["active"] = True
                assert await terminal._start_capture("", 0, None, None) == 0

        terminal._event = event
        terminal.client = SimpleNamespace(execute_service=execute)
        # Comme le firmware réel, start seul ne fait rien en session active.
        await terminal._rearm_wake_word()
        assert calls == ["start"] and not terminal.wake_status()["receiving"]
        terminal.wake_last_attempt -= 20
        terminal.phase = phase
        await terminal._check_wake_word()
        assert calls == ["start", "INTENT_END", "RUN_END", "stop", "start"]
        assert terminal.capture is None and terminal.turn is None
        assert terminal.wake_recoveries == 1
        await terminal._audio(frame())
        assert terminal.wake_status()["receiving"]
        before = list(calls)
        await terminal._check_wake_word()
        assert calls == before, "ne pas interrompre une veille saine"
        await terminal.close()

    asyncio.run(scenario())


def test_monitor_recovers_orphaned_detection_even_when_microphone_flows():
    import time
    from unittest.mock import AsyncMock

    async def scenario():
        detector = FakeDetector()
        detector.status = lambda: {"latched": True, "last_detection": time.monotonic() - 20}
        terminal = DirectTerminal(None, None, None, wake_detector=detector)
        terminal.connected = terminal.wake_armed = True
        terminal.phase = "waking"
        terminal.wake_last_audio = time.monotonic()
        terminal.wake_last_attempt = time.monotonic() - 20
        terminal._rearm_wake_word = AsyncMock()
        assert terminal.health()["components"]["microphone"] == "ok"
        assert terminal.health()["components"]["detector"] == "stalled"
        await terminal._check_wake_word()
        terminal._rearm_wake_word.assert_awaited_once_with(reset_session=True, reason="detector_latched")
        terminal._rearm_wake_word.reset_mock()
        terminal.capture = object()
        await terminal._check_wake_word()
        terminal._rearm_wake_word.assert_not_awaited()
    asyncio.run(scenario())


def test_monitor_preserves_capture_processing_and_unfinished_playback():
    import time

    async def scenario():
        terminal = DirectTerminal(None, None, None, vad_factory=lambda: None,
                                  wake_detector=FakeDetector())
        terminal.connected = terminal.wake_armed = True
        terminal.wake_last_attempt = time.monotonic() - 40
        terminal._event = lambda *args: pytest.fail("Une opération active doit être préservée")
        for phase in ("processing", "recording", "listening"):
            terminal.phase = phase
            await terminal._check_wake_word()
        terminal.phase = "playing"
        terminal.playback_deadline = time.monotonic() + 30
        await terminal._check_wake_word()
        terminal.playback_deadline = time.monotonic() - 1
        terminal.turn = asyncio.create_task(asyncio.sleep(60))
        await terminal._check_wake_word()
        terminal.turn.cancel()
        await asyncio.gather(terminal.turn, return_exceptions=True)
        terminal.capture = Capture()
        await terminal._check_wake_word()
        await terminal.close()

    asyncio.run(scenario())


def test_failed_session_stop_remains_retryable():
    import time
    from types import SimpleNamespace

    async def scenario():
        calls = []
        terminal = DirectTerminal(None, None, None, wake_detector=FakeDetector())
        terminal.connected = terminal.wake_armed = True
        terminal.phase = "waking"
        terminal.services = {"start_va": "start", "stop_va": "stop"}
        terminal._event = lambda *args: None

        async def execute(service, data):
            calls.append(service)
            if len(calls) == 1:
                raise OSError("contenu privé")

        terminal.client = SimpleNamespace(execute_service=execute)
        terminal.wake_last_attempt = time.monotonic() - 20
        await terminal._check_wake_word()
        assert calls == ["stop"] and terminal.phase == "idle"
        assert terminal.wake_error == "Arrêt impossible : OSError"
        await terminal._check_wake_word()
        assert calls == ["stop"], "borner la fréquence des tentatives"
        terminal.wake_last_attempt -= 20
        await terminal._check_wake_word()
        assert calls == ["stop", "stop", "start"]
        assert terminal.phase == "waking"
        await terminal.close()

    asyncio.run(scenario())


def test_preroll_does_not_drop_the_first_syllable_of_the_command():
    async def scenario():
        terminal = DirectTerminal(None, None, None, vad_factory=lambda: None,
                                  wake_detector=FakeDetector())
        terminal.connected = True
        terminal.wake_gate = WakeGate(terminal.wake_detector, preroll_seconds=.6)
        terminal.wake_armed = True
        terminal.phase = "waking"
        terminal._event = lambda *args: None
        # Parole continue avant le déclenchement, puis la même prise continue.
        for _ in range(40):
            terminal.wake_gate.preroll.extend(tone(.02, 900))
        terminal.wake_gate.detector.fired = True
        await terminal._wake_detected()
        assert terminal.capture is not None
        start = len(terminal.capture.data)
        for _ in range(30):
            await terminal._audio(tone(.02, 900))
        assert len(terminal.capture.data) > start
        assert any(b != 0 for b in terminal.capture.data), "le pré-roll garde la parole"
        await terminal.close()
    asyncio.run(scenario())


def test_jarvis_config_loads(tmp_path):
    import json
    path = tmp_path / "terminal.json"
    path.write_text(json.dumps({"enabled": True, "host": "board.local",
        "expected_mac": "00:11:22:33:44:55", "media_host": "192.168.77.24",
        "wake_name": "jarvis", "wake_model": "jarvisse_20260916_004415.onnx",
        "wake_threshold": .5, "wake_verify": False}))
    config = TerminalConfig.load(path)
    assert config.wake_name == "jarvis"
    assert config.wake_threshold == .5
    assert config.wake_verify is False
