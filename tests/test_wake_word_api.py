"""Routes du mot d'appel : veille, arrêt et compteur de faux réveils."""
import pytest
from fastapi.testclient import TestClient

from alfred.app import create_app
from alfred.config import Settings


class FakeTerminal:
    """Terminal factice : aucun matériel, aucun audio, aucun modèle."""

    def __init__(self, wake=True, armed=False):
        self.wake = wake
        self.armed = armed
        self.false_alarms = 0
        self.started = 0
        self.stopped = 0

    def status(self):
        return {"enabled": True, "connected": True, "wake_word": {
            "enabled": self.wake, "armed": self.armed, "detections": self.started,
            "last_wake_at": 0., "threshold": .5,
            "false_alarms": self.false_alarms, "error": None}}

    async def start_wake_word(self):
        if not self.wake:
            raise ValueError("Mot d'appel non configuré")
        self.armed = True
        self.started += 1
        return {"armed": True}

    def stop_wake_word(self):
        self.armed = False
        self.stopped += 1
        return {"armed": False}

    async def close(self):
        self.armed = False


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(Settings(tmp_path, poll_seconds=0.02))) as instance:
        yield instance


def post(client, path):
    return client.post(path, headers={"Content-Type": "application/json"}, content=b"{}")


@pytest.mark.parametrize("wake,code", [(True, 200), (False, 409)])
def test_wake_word_start_and_stop(client, wake, code):
    terminal = FakeTerminal(wake=wake)
    client.app.state.terminal = terminal
    response = post(client, "/api/terminal/wake-word/start")
    assert response.status_code == code
    assert terminal.started == (1 if wake else 0)
    assert post(client, "/api/terminal/wake-word/stop").status_code == 200
    assert terminal.stopped == 1


def test_false_alarm_counter_is_exposed_without_content(client):
    terminal = FakeTerminal(armed=True)
    client.app.state.terminal = terminal
    assert post(client, "/api/terminal/wake-word/false-alarm").json() == {"false_alarms": 1}
    assert post(client, "/api/terminal/wake-word/false-alarm").json() == {"false_alarms": 2}
    wake = client.get("/api/terminal/status").json()["wake_word"]
    assert wake["false_alarms"] == 2
    assert "text" not in wake and "audio" not in wake
