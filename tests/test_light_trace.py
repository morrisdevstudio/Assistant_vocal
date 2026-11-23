import json
from time import perf_counter

import httpx
import pytest
from fastapi.testclient import TestClient

from alfred.app import create_app
from alfred.config import Settings
from alfred.conversation import ConversationService
from alfred.credentials import CredentialStore
from alfred.home_assistant import HomeService, HomeStore
from alfred.light_benchmark import summarize, write_report
from alfred.light_trace import LightTrace
from alfred.terminal import Capture, DirectTerminal


PATH = "/api/terminal/light-trace"
TARGET = "light.bureau"


@pytest.mark.parametrize("backend", [
    "applied", "local", "never_confirmed", "timeout", "cancelled", "ambiguous", "negated", "excluded",
])
def test_trace_follows_esp32_conversation_through_simulated_home(tmp_path, monkeypatch, backend):
    config = {"enabled": True, "host": "board.local", "media_host": "192.168.1.20",
              "expected_mac": "00:11:22:33:44:55", "wake_word": False}
    (tmp_path / "terminal.json").write_text(json.dumps(config))
    state = "off"
    calls = []
    prompts = []
    entry = {"entity_id": TARGET, "domain": "light", "area": "Bureau", "name": "Lampe du bureau",
             "allowed": backend != "excluded", "members": None}

    def ha(request):
        nonlocal state
        if request.method == "POST":
            calls.append(json.loads(request.content))
            if backend == "timeout":
                raise httpx.ReadTimeout("Réponse perdue", request=request)
            if backend in {"applied", "local"}:
                state = "on"
            return httpx.Response(200, json=[])
        assert request.url.path.endswith(TARGET)
        return httpx.Response(200, json={"entity_id": TARGET, "state": state, "attributes": {}})

    def model(request):
        prompts.append(json.loads(request.content)["messages"][-1]["content"])
        tool = "controler_lumieres"
        args = {"actions": [{"operation": "turn_on", "scope": "room", "target": "Bureau"}]}
        if backend == "ambiguous":
            tool = "preciser_demande"
            args = {"question": "Quelle lampe ?"}
        event = {"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {
            "name": tool, "arguments": json.dumps(args)}}]}, "finish_reason": "tool_calls"}]}
        return httpx.Response(200, headers={"content-type": "text/event-stream"},
                              text=f"data: {json.dumps(event)}\n\ndata: [DONE]\n\n")

    async def connect(terminal):
        terminal.connected, terminal.phase = True, "idle"

    home = HomeService(HomeStore(tmp_path, base_url="http://ha.test", token="test"),
                       lambda: httpx.Client(transport=httpx.MockTransport(ha)))
    monkeypatch.setattr(home.catalog(), "_snapshot", lambda: {"entities": [entry]})
    monkeypatch.setattr(DirectTerminal, "start", connect)
    monkeypatch.setattr(DirectTerminal, "_event", lambda *args: None)
    monkeypatch.setattr("alfred.terminal.playback_audio", lambda audio: b"flac")
    model_service = ConversationService(CredentialStore(tmp_path, api_key="fake-key-for-test"),
                                        lambda: httpx.Client(transport=httpx.MockTransport(model)))

    class Speech:
        def transcribe(self, audio):
            phrases = {"ambiguous": "Allume-la", "negated": "N'allume pas la lumière du bureau",
                       "applied": "Je voudrais un peu de lumière dans le bureau"}
            return phrases.get(backend, "Allume la lumière du bureau"), .5, 4

        def speak(self, text):
            capture = Capture()
            capture.data.extend(bytes(16000))
            return capture.wav(), 2

    app = create_app(Settings(tmp_path), voice_service=Speech(),
                     conversation_service=model_service, home_service=home)
    with TestClient(app, client=("127.0.0.1", 50000)) as client:
        response = client.post(PATH, json={})
        assert response.status_code == 201
        url = f"{PATH}/{response.json()['id']}"
        assert client.post(PATH, json={}).status_code == 409
        terminal = app.state.terminal

        async def run_capture():
            capture = Capture()
            capture.data.extend(bytes(16000))
            capture.speaking = True
            capture.end_reason = "speech_pause"
            capture.last_voice_at = perf_counter() - .9
            terminal.capture = capture
            if backend == "cancelled":
                await terminal._stop_capture(True)
                return
            await terminal._finish_capture()
            await terminal.turn
            if backend == "negated":
                assert terminal.conversation_display.get("error")
                return
            assert terminal.reply_path, terminal.conversation_display.get("error")
            terminal._trace_audio_request("/unrelated")
            assert terminal.light_trace.snapshot()["state"] == "captured"
            terminal._trace_audio_request(terminal.reply_path)

        client.portal.call(run_capture)
        trace = client.get(url).json()
        assert client.get(f"{PATH}/unrelated").status_code == 404
        applied = backend in {"applied", "local"}
        row = summarize(trace, "Pièce", 1, [TARGET], applied, True)
        write_report(tmp_path, [{"row": row, "events": trace["events"]}])
        assert "Allume la lumière" not in (tmp_path / "traces.json").read_text(encoding="utf-8")
        assert row["first_try_success"] is applied
        assert row["vad_ms"] >= 900
        if backend == "cancelled":
            assert trace["state"] == "cancelled"
            assert calls == []
            assert row["stt_ms"] is None
            return

        names = [event["event"] for event in trace["events"]]
        assert trace["state"] == ("request_failed" if backend == "negated" else "complete")
        assert row["exchange_id"]
        if backend in {"ambiguous", "negated", "excluded"}:
            assert "service_sent" not in names
            assert bool(prompts) is (backend != "excluded")
            assert row["route"] == ("local" if backend == "excluded" else "ai")
            assert row["speech_to_send_ms"] is None
            assert not calls
            return

        expected = ["last_voice_detected", "capture_closed", "stt_started", "transcript_final", "catalog_read"]
        if backend == "applied":
            expected += ["model_request_started", "model_tool_ready"]
            assert prompts == ["Je voudrais un peu de lumière dans le bureau"]
        else:
            assert not prompts
        expected += ["light_intent_ready", "service_sent", "audio_ready", "audio_requested"]
        assert [names.index(name) for name in expected] == sorted(names.index(name) for name in expected)
        assert row["route"] == ("ai" if backend == "applied" else "local")
        assert row["catalog_calls"] == (4 if backend == "applied" else 3)
        assert row["pre_state_calls"] == 2
        assert (row["model_catalog_ms"] is not None) is (backend == "applied")
        assert row["speech_to_send_ms"] >= row["vad_ms"]
        assert row["speech_to_audio_request_ms"] >= row["speech_to_audio_ready_ms"]
        assert calls == [{"entity_id": [TARGET]}]
        assert ("service_acknowledged" in names) is (backend != "timeout")
        assert ("state_confirmed" in names) is applied
        assert row["action_status"] == ("confirmed" if applied else "unconfirmed")


def test_trace_distinguishes_no_capture_and_session_timeout():
    now = [1.]
    no_capture = LightTrace(clock=lambda: now[0])
    captured = LightTrace(clock=lambda: now[0])
    captured.claim(now[0], None, "device_end_or_timeout")
    now[0] += 150
    assert no_capture.snapshot()["state"] == "no_capture"
    assert captured.snapshot()["state"] == "timeout"
    captured.mark("audio_requested")
    assert len(captured.snapshot()["events"]) == 1
