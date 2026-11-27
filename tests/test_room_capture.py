import asyncio
import io
import wave
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from alfred.room_capture import CAPTURE_SECONDS, install_room_capture_routes
from alfred.terminal import DirectTerminal


def setup_capture(armed=True):
    detector = Mock()
    terminal = DirectTerminal(None, None, None, wake_detector=detector)
    terminal.connected = True
    terminal.phase = "idle"
    terminal.wake_armed = armed
    gate = Mock()
    if armed:
        terminal.wake_gate = gate

    async def arm():
        terminal.wake_armed = True
        terminal.wake_gate = gate

    terminal.start_wake_word = AsyncMock(side_effect=arm)
    app = FastAPI()
    app.state.terminal = terminal
    app.state.wake_manager = SimpleNamespace(
        owner="esp32" if armed else None, lock=asyncio.Lock(),
        occupied=lambda: terminal.wake_test is not None,
    )
    install_room_capture_routes(app)
    return app, terminal, gate


def start_capture(client):
    response = client.post("/api/room-capture", json={})
    assert response.status_code == 200
    return {"X-Alfred-Capture": response.json()["token"]}


def test_room_capture_bypasses_wake_and_downloads_once():
    app, terminal, gate = setup_capture()
    with TestClient(app) as client:
        headers = start_capture(client)
        assert client.post("/api/room-capture", json={}).status_code == 409
        chunk = b"\x11\x22" * 16000
        for _ in range(CAPTURE_SECONDS):
            client.portal.call(terminal._audio, chunk)
        assert terminal.wake_armed and terminal.wake_test is None
        gate.feed.assert_not_called()
        assert client.get("/api/room-capture/wav").status_code == 404
        assert client.get("/api/room-capture", headers=headers).json()["state"] == "ready"
        result = client.get("/api/room-capture/wav", headers=headers)
        assert result.status_code == 200
        assert result.headers["cache-control"] == "no-store"
        with wave.open(io.BytesIO(result.content)) as wav:
            assert (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) == (1, 2, 16000)
            assert wav.readframes(wav.getnframes()) == chunk * CAPTURE_SECONDS
        assert client.get("/api/room-capture/wav", headers=headers).status_code == 409


def test_cancel_discards_audio_and_restores_disarmed_terminal():
    app, terminal, gate = setup_capture(armed=False)
    with TestClient(app) as client:
        headers = start_capture(client)
        client.portal.call(terminal._audio, b"\x11\x22" * 16000)
        gate.feed.assert_not_called()
        assert client.delete("/api/room-capture", headers=headers).json()["state"] == "interrompu"
        assert not terminal.wake_armed and terminal.wake_test is None
        assert not app.state.room_capture.pcm
