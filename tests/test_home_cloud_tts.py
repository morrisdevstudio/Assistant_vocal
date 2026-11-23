import io
import json
import wave

import httpx
import pytest

from alfred.home_cloud_tts import HomeCloudTTS, HomeCloudTTSError
from alfred.voice import VoiceService, VoiceUnavailable


class Store:
    def values(self):
        return "http://192.168.77.21:8123", "fake-token-for-tests", "Bureau"

    def public(self):
        return {"configured": True}


def wav():
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as stream:
        stream.setnchannels(2)
        stream.setsampwidth(2)
        stream.setframerate(48000)
        stream.writeframes(bytes(4800 * 4))
    return buffer.getvalue()


def client(handler):
    return lambda: httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True)


def test_cloud_generates_without_playback_and_fetches_only_same_ha():
    calls = []
    def handler(request):
        calls.append(request)
        assert request.url.host == "192.168.77.21"
        assert request.headers["authorization"] == "Bearer fake-token-for-tests"
        if request.method == "POST":
            assert request.url.path == "/api/tts_get_url"
            body = json.loads(request.content)
            assert body == {"engine_id": "tts.home_assistant_cloud", "message": "Il n'y a plus de pâtes.",
                            "language": "fr-FR", "options": {"voice": "HenriNeural"}, "cache": False}
            return httpx.Response(200, json={"path": "/api/tts_proxy/test.mp3"})
        assert request.url.path == "/api/tts_proxy/test.mp3"
        return httpx.Response(200, content=wav())
    engine = HomeCloudTTS(Store(), client(handler))
    output = engine.synthesize("Il n'y a plus de pâtes.")
    with wave.open(io.BytesIO(output), "rb") as audio:
        assert (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) == (1, 2, 24000)
        assert abs(audio.getnframes() / 24000 - .1) < .005
    assert len(calls) == 2


@pytest.mark.parametrize("path", ["https://evil.example/audio", "//evil.example/audio",
    "/api/tts_proxy/../secret", "/api/tts_proxy/test?token=x", "/other/path", None])
def test_cloud_never_fetches_arbitrary_url_or_leaks_credentials(path):
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"path": path})
    with pytest.raises(HomeCloudTTSError):
        HomeCloudTTS(Store(), client(handler)).synthesize("Bonjour")
    assert len(calls) == 1


@pytest.mark.parametrize("stage", ["generation", "audio"])
def test_redirects_are_refused_even_with_custom_client(stage):
    calls = []
    def handler(request):
        calls.append(request)
        if request.method == "POST" and stage == "audio":
            return httpx.Response(200, json={"path": "/api/tts_proxy/test.mp3"})
        return httpx.Response(302, headers={"Location": "https://evil.example/redirect"})
    with pytest.raises(HomeCloudTTSError):
        HomeCloudTTS(Store(), client(handler)).synthesize("Bonjour")
    assert len(calls) == (2 if stage == "audio" else 1)


def test_cloud_voice_removed_from_voice_service(tmp_path):
    engine=VoiceService(tmp_path)
    with pytest.raises(ValueError):engine.set_voice("ha-cloud-henri")
    assert not hasattr(engine,"_home_cloud")


def test_error_never_contains_token_or_response_body():
    def handler(request):
        return httpx.Response(403, text="sensitive server diagnostic")
    with pytest.raises(HomeCloudTTSError) as raised:
        HomeCloudTTS(Store(), client(handler)).synthesize("Bonjour")
    assert "fake-token" not in str(raised.value)
    assert "sensitive" not in str(raised.value)


def test_cloud_is_not_selected_implicitly_when_local_models_are_missing(tmp_path):
    engine=VoiceService(tmp_path)
    assert engine.status()["tts_voice_id"]=="phonon-dumby-cpu"
