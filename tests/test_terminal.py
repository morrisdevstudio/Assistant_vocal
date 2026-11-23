import asyncio
import io
import json
import wave

import numpy as np
import pytest

from alfred.terminal import AudioTickets, Capture, DirectTerminal, TerminalConfig, playback_audio


def pcm(seconds, level=0):
    return np.full(round(seconds * 16000), level, dtype="<i2").tobytes()


def test_capture_keeps_start_of_speech_and_finishes_after_pause():
    capture = Capture()
    for _ in range(100):
        assert capture.feed(pcm(.02)) == (False, False)
    assert len(capture.data) <= 19200
    started = False
    for _ in range(20):
        begin, _ = capture.feed(pcm(.02, 1500))
        started |= begin
    assert started
    done = False
    for _ in range(50):
        _, done = capture.feed(pcm(.02))
        if done:
            break
    assert done
    with wave.open(io.BytesIO(capture.wav()), "rb") as wav:
        assert wav.getframerate() == 16000
        samples = np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2")
        assert np.count_nonzero(samples == 1500) == 6400


def test_silence_never_becomes_speech_and_recording_is_bounded():
    capture = Capture()
    for _ in range(1600):
        capture.feed(pcm(.02))
    assert not capture.speaking
    assert len(capture.data) <= 19200
    for _ in range(1500):
        _, done = capture.feed(pcm(.02, 1000))
        if done:
            break
    assert done
    assert len(capture.data) <= 16000 * 2 * 30


def test_audio_ticket_expiration_and_no_path_traversal(monkeypatch):
    now = [10.]
    monkeypatch.setattr("alfred.terminal.time.monotonic", lambda: now[0])
    tickets = AudioTickets()
    path = tickets.put(b"wave-in-memory")
    assert tickets.get(path) == b"wave-in-memory"
    assert tickets.get("/audio/../../profile.json.wav") is None
    now[0] = 101
    assert tickets.get(path) is None
    with pytest.raises(ValueError):
        tickets.put(b"a" * (6 * 1024 * 1024 + 1))


def test_playback_uses_lossless_flac_48k_without_changing_duration():
    sf = pytest.importorskip("soundfile")
    pytest.importorskip("scipy")
    output = io.BytesIO()
    signal = .3 * np.sin(2 * np.pi * 180 * np.arange(44100) / 44100)
    sf.write(output, signal, 44100, format="WAV", subtype="PCM_16")
    flac = playback_audio(output.getvalue())
    assert flac.startswith(b"fLaC")
    samples, rate = sf.read(io.BytesIO(flac))
    assert rate == 48000
    assert samples.shape == (48000,)
    assert np.max(np.abs(samples)) < .31


def test_config_rejects_public_destination_and_loads_only_when_enabled(tmp_path):
    path = tmp_path / "terminal.json"
    assert TerminalConfig.load(path) is None
    value = {"enabled": True, "host": "8.8.8.8", "expected_mac": "00:11:22:33:44:55",
             "media_host": "192.168.77.24"}
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError):
        TerminalConfig.load(path)
    value["host"] = "board.local"
    path.write_text(json.dumps(value))
    assert TerminalConfig.load(path).floor_id == "rdc"
    assert TerminalConfig.load(path).progressive_tts is True
    value["progressive_tts"] = False
    path.write_text(json.dumps(value))
    assert TerminalConfig.load(path).progressive_tts is False
    value["enabled"] = False
    path.write_text(json.dumps(value))
    assert TerminalConfig.load(path) is None


def test_followup_silence_closes_without_calling_processor():
    async def scenario():
        async def process(*args):
            pytest.fail("Un silence ne doit déclencher aucun traitement IA")
        terminal = DirectTerminal(None, process, None)
        events = []
        terminal._event = lambda *args: events.append(args)
        terminal.capture = Capture()
        await terminal._capture_timeout(0)
        assert terminal.capture is None
        assert terminal.phase == "idle"
        assert events[-1][0] == "RUN_END"
    asyncio.run(scenario())


def test_standalone_wake_shows_waiting_then_finishes_display_on_silence():
    async def scenario():
        async def process(*args):
            result = {"type": "done", "mode": "wake_empty", "text": ""}
            terminal.observe_conversation(result)
            return result

        config = TerminalConfig("board.local", "aa:bb:cc:dd:ee:ff", "127.0.0.1")
        terminal = DirectTerminal(config, process, None, vad_factory=lambda: None)
        terminal._event = lambda *args: None
        await terminal._process(b"wake audio")
        waiting = terminal.conversation_text()["exchange"]
        assert waiting["state"] == "waiting_for_command"
        terminal.watchdog.cancel()
        await terminal._capture_timeout(0)
        finished = terminal.conversation_text()["exchange"]
        assert finished["state"] == "finished" and finished["id"] == waiting["id"]
        assert finished["revision"] == waiting["revision"] + 1
        assert finished["answer"] == "Aucune demande après le mot d’appel."

    asyncio.run(scenario())


@pytest.mark.parametrize("expired", [False, True])
def test_stt_test_cannot_execute_actions_or_tts_even_after_expiration(expired):
    async def scenario():
        async def forbidden(*args):
            pytest.fail("Le test STT ne doit pas atteindre la conversation")
        def no_tts(*args):
            pytest.fail("Le test STT ne doit pas jouer de voix")
        def transcribe(audio):
            assert not expired
            return "Texte privé de test", 1., 250
        # Signal DC artificiel pour tester l'isolation du diagnostic ; ce
        # signal n'est pas de la parole pour le véritable modèle neuronal.
        terminal = DirectTerminal(None, forbidden, no_tts, transcribe=transcribe,
                                  vad_factory=lambda: None)
        terminal.connected = True;terminal.phase = "idle"
        terminal._event = lambda *args: None
        terminal.arm_stt_test()
        if expired:
            terminal.stt_test_until = 0
        await terminal._start_capture("", 0, None, None)
        assert terminal.capture_test
        for _ in range(20):await terminal._audio(pcm(.02, 1500))
        for _ in range(50):await terminal._audio(pcm(.02))
        await terminal.turn
        result = terminal.stt_test_result()
        assert result["available"] and result["actions_executed"] is False
        assert "privé" not in json.dumps(terminal.status(), ensure_ascii=False)
        if expired:assert "expiré" in result["error"]
        else:assert result["text"] == "Texte privé de test"
        terminal._expire_stt_result(terminal.stt_result)
        assert not terminal.stt_test_result()["available"]
        await terminal.close()
    asyncio.run(scenario())


@pytest.mark.parametrize("lost_reply", [False, True])
def test_remote_stt_start_arms_diagnostic_before_device_command(lost_reply):
    from types import SimpleNamespace
    async def scenario():
        terminal = DirectTerminal(None, None, None, transcribe=lambda data: None)
        terminal.connected = True;terminal.phase = "idle"
        terminal.services = {"start_va": "start-service"}
        calls = []
        async def execute(service, data):
            assert terminal.stt_test_pending
            calls.append((service, data))
            if lost_reply:
                raise TimeoutError()
        terminal.client = SimpleNamespace(execute_service=execute)
        if lost_reply:
            with pytest.raises(TimeoutError):
                await terminal.start_stt_test()
            assert terminal.stt_test_pending and terminal.stt_test_until == 0
        else:
            assert (await terminal.start_stt_test())["started"]
        assert calls == [("start-service", {})]
    asyncio.run(scenario())


def test_failed_turn_is_never_retried_and_diagnostics_have_no_content():
    async def scenario():
        count = 0
        async def process(*args):
            nonlocal count
            count += 1
            raise RuntimeError("texte privé à ne pas conserver")
        config = TerminalConfig("board.local", "00:11:22:33:44:55", "192.168.77.24")
        terminal = DirectTerminal(config, process, None)
        events = []
        terminal._event = lambda *args: events.append(args)
        await terminal._process(b"test")
        assert count == 1
        assert terminal.expect_followup is False
        assert "privé" not in json.dumps(terminal.status(), ensure_ascii=False)
        assert events[-1][0] == "RUN_END"
    asyncio.run(scenario())


@pytest.mark.parametrize("needs_reply", [False, True])
def test_successful_turn_reports_latency_and_duration_without_reply_text(monkeypatch, needs_reply):
    import base64
    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(16000)
        wav.writeframes(pcm(1))
    monkeypatch.setattr("alfred.terminal.playback_audio", lambda data: b"flac-test")
    async def scenario():
        async def process(*args):
            return {"text": "Une réponse privée", "transcript": "Une demande privée",
                    "needs_reply": needs_reply,
                    "audio_base64": base64.b64encode(output.getvalue()).decode(),
                    "timings": {"stt_ms": 100, "llm_ms": 200, "tts_ms": 300}}
        terminal = DirectTerminal(TerminalConfig("board.local", "00:11:22:33:44:55", "192.168.77.24"),
                                  process, None)
        events = []
        terminal._event = lambda *args: events.append(args)
        await terminal._process(b"request")
        assert terminal.expect_followup is needs_reply
        intent = next(event[1] for event in events if event[0] == "INTENT_END")
        assert intent["continue_conversation"] == str(int(needs_reply))
        status = terminal.status()
        assert status["turns"] == 1
        assert status["last_timings"]["reply_audio_ms"] == 1000
        assert status["last_timings"]["reply_characters"] == len("Une réponse privée")
        assert status["last_timings"]["capture_finished_to_reply_ms"] >= 0
        assert "privée" not in json.dumps(status, ensure_ascii=False)
        exchange = terminal.conversation_text()["exchange"]
        assert exchange["transcript"] == "Une demande privée"
        assert exchange["answer"] == "Une réponse privée"
    asyncio.run(scenario())


def test_conversation_display_is_ephemeral_and_resets_between_turns(monkeypatch):
    now = [10.]
    monkeypatch.setattr("alfred.terminal.time.monotonic", lambda: now[0])
    terminal = DirectTerminal(None, None, None)
    terminal.begin_conversation_display()
    terminal.observe_conversation({"type": "transcript", "text": "Bonjour"})
    terminal.observe_conversation({"type": "delta", "text": "À votre "})
    terminal.observe_conversation({"type": "delta", "text": "service."})
    assert terminal.conversation_text()["exchange"]["answer"] == "À votre service."
    first_id = terminal.conversation_text()["exchange"]["id"]
    terminal.begin_conversation_display()
    exchange = terminal.conversation_text()["exchange"]
    assert exchange["id"] != first_id
    assert exchange["transcript"] == exchange["answer"] == ""
    now[0] += 901
    assert terminal.conversation_text() == {"available": False, "exchange": None}


def test_conversation_display_finishes_when_terminal_returns_to_wake_without_a_turn():
    terminal = DirectTerminal(None, None, None)
    terminal.phase = "processing"
    terminal.begin_conversation_display()
    assert terminal.conversation_text()["exchange"]["state"] == "processing"
    terminal.phase = "waking"
    result = terminal.conversation_text()["exchange"]
    assert result["state"] == "finished"
    assert result["error"] == "Échange interrompu."
    assert terminal.conversation_text()["exchange"] == result


def test_audio_http_is_limited_to_the_board_address():
    async def scenario():
        terminal = DirectTerminal(None, None, None)
        terminal.peer = "127.0.0.1"
        path = terminal.tickets.put(b"audio-in-memory")
        terminal.reply_path = path
        terminal.reply_started = 0
        terminal.last_timings = {}
        server = await asyncio.start_server(terminal._http, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        async def get(extra=""):
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            writer.write(f"GET {path} HTTP/1.1\r\nHost: test\r\n{extra}\r\n".encode())
            await writer.drain()
            data = await reader.read()
            writer.close()
            await writer.wait_closed()
            return data
        try:
            assert (await get()).endswith(b"audio-in-memory")
            assert terminal.last_timings["capture_finished_to_audio_request_ms"] > 0
            partial = await get("Range: bytes=0-4\r\n")
            assert b"206 Partial Content" in partial
            assert partial.endswith(b"audio")
            terminal.peer = "127.0.0.2"
            assert b"404 Not Found" in await get()
        finally:
            server.close()
            await server.wait_closed()
    asyncio.run(scenario())


def test_playback_state_uses_entity_state_not_enum():
    api = pytest.importorskip("aioesphomeapi")
    terminal = DirectTerminal(None, None, None)
    terminal.media_key = 123
    terminal.phase = "test_playing"
    terminal._state(api.MediaPlayerEntityState(key=123, state=api.MediaPlayerState.IDLE))
    assert terminal.media_state == "IDLE"
    assert terminal.phase == "idle"


def test_button_stop_ends_pipeline_and_cancels_the_pending_turn():
    async def scenario():
        terminal = DirectTerminal(None, None, None)
        terminal.capture = Capture()
        terminal.expect_followup = True
        events = []
        terminal._event = lambda *args: events.append(args)
        terminal.turn = asyncio.create_task(asyncio.sleep(10))
        await terminal._stop_capture(True)
        await asyncio.gather(terminal.turn, return_exceptions=True)
        assert terminal.turn.cancelled()
        assert terminal.capture is None
        assert not terminal.expect_followup
        assert events[-1][0] == "RUN_END"
    asyncio.run(scenario())
