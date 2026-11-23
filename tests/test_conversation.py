import json
import os
import threading

import httpx
import pytest
from fastapi.testclient import TestClient

from alfred.app import create_app
from alfred.config import Settings
from alfred.conversation import ConversationCancelled, ConversationError, ConversationService
from alfred.credentials import CredentialStore, DEFAULT_MODEL

KEY="fake-test-key-not-a-real-credential"
SID="browser-session-test-0001"


def sse(answer="À votre service.", finish="stop", done=True):
    events=[{"choices":[{"delta":{"content":answer}}]},
            {"choices":[{"delta":{},"finish_reason":finish}]},
            {"choices":[],"usage":{"prompt_tokens":10,"completion_tokens":5,"total_tokens":15}}]
    return "".join("data: "+json.dumps(event)+"\n\n" for event in events)+("data: [DONE]\n\n" if done else "")


def service(tmp_path,handler=None):
    credentials=CredentialStore(tmp_path,api_key=KEY)
    handler=handler or (lambda request:httpx.Response(200,headers={"content-type":"text/event-stream"},text=sse()))
    transport=httpx.MockTransport(handler)
    return ConversationService(credentials,lambda:httpx.Client(transport=transport))


def complete(engine,text="Bonjour",sid=SID):
    return list(engine.stream(text,sid,threading.Event()))


def test_internet_can_be_disabled_per_turn_without_changing_server_setting(tmp_path):
    requests = []
    def handler(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=sse())
    engine = service(tmp_path, handler)
    engine.internet = object()
    list(engine.stream("Bonjour", SID, threading.Event(), allow_internet=False))
    complete(engine)
    assert "tools" not in requests[0]
    assert "rechercher_web" in {tool["function"]["name"] for tool in requests[1]["tools"]}


def tool_stream(name, arguments, finish="tool_calls"):
    events = [{"choices": [{"delta": {"tool_calls": [{"index": 0, "id": "call-1", "type": "function", "function": {"name": name, "arguments": arguments[:3]}}]}}]},
              {"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {"arguments": arguments[3:]}}]}, "finish_reason": finish}]}]
    return "".join("data: " + json.dumps(event) + "\n\n" for event in events) + "data: [DONE]\n\n"


@pytest.mark.parametrize("name,args,expected", [("lire_courses", "{}", "lait"),
                                                 ("ajouter_course", '{"article":"pain"}', "pain")])
def test_shopping_tool_executes_validated_model_request(tmp_path, name, args, expected):
    requests = []
    def handler(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=tool_stream(name,args))
    class Shopping:
        def __init__(self): self.calls = []
        def request(self, action, item=None):
            self.calls.append((action,item))
            return ["lait"] if action == "get_items" else None
    engine = service(tmp_path,handler)
    engine.shopping = Shopping()
    result = complete(engine, "Il nous manque du pain")
    assert expected in result[-1]["text"]
    assert len(engine.shopping.calls) == 1
    assert len(requests[0]["tools"]) == 10


def test_multiple_articles_and_parallel_tool_calls(tmp_path):
    class Shopping:
        def __init__(self): self.calls = []
        def request(self, action, item=None): self.calls.append(item)
    engine = service(tmp_path)
    engine.shopping = Shopping()
    calls = {0: {"name": "ajouter_courses", "arguments": json.dumps({"articles": ["lait", "pain"]})},
             1: {"name": "ajouter_course", "arguments": json.dumps({"article": "café"})}}
    result = engine.run_shopping_tool(calls, threading.Event())
    assert engine.shopping.calls == ["lait", "pain", "café"]
    assert all(item in result for item in ("lait", "pain", "café"))


def test_multiple_articles_validate_all_before_writes(tmp_path):
    class Shopping:
        def request(self, *args): raise AssertionError("aucun ajout ne doit être exécuté")
    engine = service(tmp_path)
    engine.shopping = Shopping()
    calls = {0: {"name": "ajouter_courses", "arguments": json.dumps({"articles": ["lait", ""]})}}
    with pytest.raises(ConversationError): engine.run_shopping_tool(calls, threading.Event())


def test_partial_failure_does_not_repeat_or_continue(tmp_path):
    from alfred.home_assistant import HomeError
    class Shopping:
        def __init__(self): self.calls = []
        def request(self, action, item=None):
            self.calls.append(item)
            if item == "pain": raise HomeError("réponse perdue")
    engine = service(tmp_path)
    engine.shopping = Shopping()
    calls = {0: {"name": "ajouter_courses", "arguments": json.dumps({"articles": ["lait", "pain", "café"]})}}
    reply = engine.run_shopping_tool(calls, threading.Event())
    assert engine.shopping.calls == ["lait", "pain"]
    assert "lait" in reply and "pain non confirmé" in reply and "café" in reply
    assert "Vérifiez la liste" in reply


def test_mixed_duplicate_and_new_items_are_reported(tmp_path):
    class Shopping:
        def request(self, action, item=None): return {"duplicate": item == "lait"}
    engine = service(tmp_path)
    engine.shopping = Shopping()
    calls = {0: {"name": "ajouter_courses", "arguments": json.dumps({"articles": ["lait", "pain"]})}}
    reply = engine.run_shopping_tool(calls, threading.Event())
    assert "Déjà dans la liste : lait" in reply
    assert "pain : ajout demandé" in reply


def test_same_item_twice_in_one_request_is_only_added_once(tmp_path):
    class Shopping:
        def __init__(self): self.calls = []
        def request(self, action, item=None):
            self.calls.append(item)
            return {"duplicate": False}
    engine = service(tmp_path)
    engine.shopping = Shopping()
    calls = {0: {"name": "ajouter_courses", "arguments": json.dumps({"articles": ["café", "du cafe"]})}}
    reply = engine.run_shopping_tool(calls, threading.Event())
    assert engine.shopping.calls == ["café"]
    assert "Déjà dans la liste : du cafe" in reply


def test_complete_tool_uses_requested_item(tmp_path):
    class Shopping:
        def request(self, action, item=None):
            assert action == "complete_item" and item == "lait"
            return {"completed": "du lait"}
    engine = service(tmp_path)
    engine.shopping = Shopping()
    result = engine.run_shopping_tool({0: {"name": "cocher_course", "arguments": '{"article":"lait"}'}}, threading.Event())
    assert "du lait est coché" in result


def test_delete_tool_requires_explicit_permanent_request(tmp_path):
    class Shopping:
        def __init__(self): self.calls = []
        def request(self, action, item=None):
            self.calls.append((action, item))
            return {"deleted": item}
    engine = service(tmp_path)
    engine.shopping = Shopping()
    calls = {0: {"name":"supprimer_course", "arguments":'{"article":"lait"}'}}
    assert "Aucun article" in engine.run_shopping_tool(calls, threading.Event(), "retire le lait")
    assert "Aucun article" in engine.run_shopping_tool(calls, threading.Event(), "ne supprime pas définitivement le lait")
    assert not engine.shopping.calls
    assert "supprimé définitivement" in engine.run_shopping_tool(calls, threading.Event(), "supprime le lait")
    assert engine.shopping.calls == [("delete_item", "lait")]


def test_purge_requires_explicit_request_and_handles_partial_result(tmp_path):
    class Shopping:
        def __init__(self): self.calls = []
        def request(self, action, cancelled=None):
            self.calls.append(action)
            return {"removed": 1, "incomplete": True}
    engine = service(tmp_path)
    engine.shopping = Shopping()
    calls = {0: {"name":"purger_courses", "arguments":"{}"}}
    assert "Aucun article" in engine.run_shopping_tool(calls, threading.Event(), "ne purge pas la liste")
    assert not engine.shopping.calls
    assert "Vérifiez la liste" in engine.run_shopping_tool(calls, threading.Event(), "purge la liste")
    assert engine.shopping.calls == ["purge_items"]


@pytest.mark.parametrize("name,args,finish", [("autre", "{}", "tool_calls"),
    ("ajouter_course", '{"article":"pain","autre":1}', "tool_calls"),
    ("ajouter_course", '{"article":"pain"}', "length")])
def test_invalid_or_incomplete_tool_never_executes(tmp_path, name, args, finish):
    engine = service(tmp_path,lambda request: httpx.Response(200,headers={"content-type":"text/event-stream"},text=tool_stream(name,args,finish)))
    class Shopping:
        def request(self, *args): raise AssertionError("action interdite")
    engine.shopping = Shopping()
    with pytest.raises(ConversationError): complete(engine)


def test_follow_up_reuses_only_same_session_context(tmp_path):
    requests = []
    def handler(request):
        body = json.loads(request.content)
        requests.append(body)
        article = "café" if body["messages"][-1]["content"] == "Et du café aussi" else "lait"
        return httpx.Response(200, headers={"content-type": "text/event-stream"},
                              text=tool_stream("ajouter_course", json.dumps({"article": article})))
    class Shopping:
        def __init__(self): self.calls = []
        def request(self, action, item=None): self.calls.append((action, item))
    engine = service(tmp_path, handler)
    engine.shopping = Shopping()
    complete(engine, "Ajoute du lait")
    complete(engine, "Et du café aussi")
    assert engine.shopping.calls == [("add_item", "lait"), ("add_item", "café")]
    assert requests[1]["messages"][1]["content"] == "Ajoute du lait"
    assert "lait" in requests[1]["messages"][2]["content"]
    complete(engine, "Autre onglet", sid="autre-session-test-0001")
    assert len(requests[2]["messages"]) == 2
    engine.reset(SID)
    complete(engine, "Nouvelle discussion")
    assert len(requests[3]["messages"]) == 2


def test_answer_without_tool_does_not_modify_list(tmp_path):
    engine = service(tmp_path)
    class Shopping:
        def request(self, *args): raise AssertionError("Une question ne doit pas modifier la liste")
    engine.shopping = Shopping()
    answer = complete(engine, "Tu aimes le lait ?")[-1]
    assert answer["tool_used"] is False


def test_credentials_round_trip_are_never_returned(tmp_path):
    store=CredentialStore(tmp_path)
    assert not store.public()["configured"]
    store.save(KEY,DEFAULT_MODEL)
    assert store.values()==(KEY,DEFAULT_MODEL)
    assert KEY not in json.dumps(store.public())
    if os.name=="nt":
        assert store.path.read_bytes().startswith(b"DPAPI\n")
        assert KEY.encode() not in store.path.read_bytes()
    else:
        assert store.path.stat().st_mode & 0o077 == 0
    store.save(None,"deepseek/other-model")
    assert store.values()==(KEY,"deepseek/other-model")


def test_stream_request_is_bounded_and_contains_no_tools(tmp_path):
    requests=[]
    def handler(request):
        requests.append(request)
        return httpx.Response(200,headers={"content-type":"text/event-stream"},text=sse())
    engine=service(tmp_path,handler)
    events=complete(engine)
    assert events[0]=={"type":"delta","text":"À votre service."}
    assert events[-1]["type"]=="answer"
    assert events[-1]["usage"]["total_tokens"]==15
    assert engine.verified
    body=json.loads(requests[0].content)
    assert body["stream"] is True
    assert body["max_tokens"]==256
    assert "tools" not in body
    assert requests[0].headers["authorization"]=="Bearer "+KEY
    assert str(requests[0].url)=="https://api.commandcode.ai/provider/v1/chat/completions"


def test_calendar_transition_never_advertises_local_reminder_creation(tmp_path):
    bodies=[]
    def handler(request):
        bodies.append(json.loads(request.content))
        return httpx.Response(200,headers={"content-type":"text/event-stream"},text=sse())
    engine=service(tmp_path,handler)
    engine.shopping=object()
    complete(engine,"Bonjour")
    assert "creer_rappel" not in [tool["function"]["name"] for tool in bodies[0]["tools"]]
    assert "calendriers Home Assistant" in bodies[0]["messages"][0]["content"]
    assert "utilise creer_rappel" not in bodies[0]["messages"][0]["content"]


def test_context_is_temporary_isolated_and_resettable(tmp_path):
    bodies=[]
    def handler(request):
        bodies.append(json.loads(request.content))
        return httpx.Response(200,headers={"content-type":"text/event-stream"},text=sse())
    engine=service(tmp_path,handler)
    complete(engine,"Mon premier message")
    complete(engine,"Et ensuite ?")
    assert len(bodies[-1]["messages"])==4
    complete(engine,"Autre onglet",sid="browser-session-test-0002")
    assert len(bodies[-1]["messages"])==2
    engine.reset(SID)
    complete(engine,"Repartons")
    assert len(bodies[-1]["messages"])==2


@pytest.mark.parametrize("status",[401,403,429,500,302])
def test_errors_never_echo_provider_or_key_and_are_not_retried(tmp_path,status):
    requests=[]
    def handler(request):
        requests.append(request)
        return httpx.Response(status,text="private provider detail "+KEY)
    engine=service(tmp_path,handler)
    with pytest.raises(ConversationError) as result:
        complete(engine)
    assert KEY not in str(result.value)
    assert "private provider" not in str(result.value)
    assert len(requests)==1
    assert not engine._history
    assert not engine.verified
    assert not engine._busy.locked()


def test_cancelled_request_does_not_contact_provider(tmp_path):
    engine=service(tmp_path)
    flag=threading.Event();flag.set()
    with pytest.raises(ConversationCancelled):list(engine.stream("Test",SID,flag))
    assert engine.requests_started==0
    assert not engine._history


def test_reset_in_flight_does_not_restore_old_context(tmp_path):
    engine=service(tmp_path)
    iterator=engine.stream("Message",SID,threading.Event())
    assert next(iterator)["type"]=="delta"
    engine.reset(SID)
    with pytest.raises(ConversationCancelled):list(iterator)
    assert not engine._history


def test_configuration_change_invalidates_in_flight_context(tmp_path):
    engine=service(tmp_path)
    iterator=engine.stream("Message",SID,threading.Event())
    assert next(iterator)["type"]=="delta"
    engine.reset()
    with pytest.raises(ConversationCancelled):list(iterator)
    assert not engine._history


def test_incomplete_stream_is_not_saved(tmp_path):
    partial='data: {"choices":[{"delta":{"content":"Début"}}]}\n\n'
    engine=service(tmp_path,lambda request:httpx.Response(200,headers={"content-type":"text/event-stream"},text=partial))
    with pytest.raises(ConversationError):complete(engine)
    assert not engine._history


def test_missing_key_is_explicit_and_no_call_occurs(tmp_path):
    engine=ConversationService(CredentialStore(tmp_path))
    with pytest.raises(ConversationError,match="clé"):complete(engine)
    assert engine.requests_started==0


def test_configuration_api_never_returns_a_key_even_on_validation_error(tmp_path):
    with TestClient(create_app(Settings(tmp_path))) as client:
        assert not client.get("/api/ai/config").json()["configured"]
        response=client.post("/api/ai/config",json={"api_key":KEY,"model":DEFAULT_MODEL})
        assert response.status_code==200
        assert KEY not in response.text
        assert client.get("/api/ai/config").json()["configured"]
        invalid=KEY+" invalid"
        result=client.post("/api/ai/config",json={"api_key":invalid,"model":DEFAULT_MODEL})
        assert result.status_code==422
        assert KEY not in result.text
        assert invalid not in result.text
        assert client.post("/api/ai/config",json={"api_key":KEY,"model":"https://other.example"}).status_code==422
        assert client.post("/api/ai/config",json={"api_key":KEY,"model":DEFAULT_MODEL},headers={"Origin":"https://other.example"}).status_code==403


class FakeSpeech:
    def status(self):return {"stt_available":True,"tts_available":True}
    def speak(self,text):return b"synthetic-test-audio",10
    def transcribe(self,data):return "Bonjour",1.0,20


class EarlySpeech(FakeSpeech):
    supports_early_speech = True
    calls = []
    def speak(self, text):
        import io
        import wave
        EarlySpeech.calls.append(text)
        output = io.BytesIO()
        with wave.open(output, "wb") as wav:
            wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(16000)
            wav.writeframes(bytes(3200))
        return output.getvalue(), 1


def test_long_stream_uses_complete_sentences_and_one_audio_url(tmp_path):
    long_answer = "Voici une première phrase complète pour votre demande. " * 2
    engine = service(tmp_path, lambda request: httpx.Response(
        200, headers={"content-type": "text/event-stream"}, text=sse(long_answer)))
    EarlySpeech.calls = []
    with TestClient(create_app(Settings(tmp_path), voice_service=EarlySpeech(),
                               conversation_service=engine)) as client:
        result = client.post("/api/conversation/text", json={"text": "Bonjour", "session_id": SID})
        events = [json.loads(line) for line in result.text.splitlines()]
        done = next(event for event in events if event["type"] == "done")
        assert done["audio_url"].startswith("http://")
        assert done["progressive_audio"] is True
        assert "audio_base64" not in done
        assert EarlySpeech.calls and all(len(text) > 16 for text in EarlySpeech.calls)
        assert " ".join(EarlySpeech.calls) == long_answer.strip()


def test_direct_terminal_uses_the_existing_voice_conversation_pipeline(tmp_path):
    import asyncio
    import base64
    import io
    import wave
    audio = io.BytesIO()
    with wave.open(audio, "wb") as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(16000)
        wav.writeframes(bytes(32000))
    engine = service(tmp_path)
    class DisplaySpeech(FakeSpeech):
        def speak(self, text):
            exchange = app.state.terminal.conversation_text()["exchange"]
            assert exchange["transcript"] == "Bonjour"
            assert exchange["answer"] == text
            return super().speak(text)
    app = create_app(Settings(tmp_path), voice_service=DisplaySpeech(), conversation_service=engine)
    with TestClient(app) as client:
        async def run():
            app.state.terminal.begin_conversation_display()
            return await asyncio.wait_for(app.state.terminal.process(audio.getvalue(), SID, "rdc"), 5)
        result = client.portal.call(run)
        assert result["transcript"] == "Bonjour"
        assert result["type"] == "done"
        assert base64.b64decode(result["audio_base64"]) == b"synthetic-test-audio"
        assert result["timings"]["tts_ms"] == 10
        assert engine.requests_started == 1
        assert KEY not in json.dumps(result)
        display = client.get("/api/terminal/conversation")
        assert display.headers["cache-control"] == "no-store"
        assert display.json()["exchange"]["transcript"] == "Bonjour"
        assert display.json()["exchange"]["answer"] == result["text"]
        # Un échange navigateur ultérieur ne remplace pas le texte du terminal.
        before = display.json()
        client.post("/api/conversation/text", json={"session_id": SID, "text": "Bonsoir"})
        assert client.get("/api/terminal/conversation").json() == before


def test_deferred_voice_route_cannot_be_requested_by_an_external_client(tmp_path):
    with TestClient(create_app(Settings(tmp_path), voice_service=FakeSpeech())) as client:
        result = client.post("/api/conversation/voice?defer_tts=true", content=b"test",
                             headers={"Content-Type": "audio/wav", "X-Alfred-Session": SID})
        assert result.status_code == 403
        assert KEY not in result.text


def test_terminal_can_defer_speech_until_text_and_actions_are_complete(tmp_path):
    import asyncio
    import io
    import wave
    class DeferredSpeech(FakeSpeech):
        def speak(self, text):
            pytest.fail("Le pont doit produire lui-même les blocs, sans synthèse complète préalable")
    audio = io.BytesIO()
    with wave.open(audio, "wb") as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(16000)
        wav.writeframes(bytes(32000))
    engine = service(tmp_path)
    app = create_app(Settings(tmp_path), voice_service=DeferredSpeech(), conversation_service=engine)
    with TestClient(app) as client:
        async def run():
            return await asyncio.wait_for(app.state.terminal.process(audio.getvalue(), SID, "rdc", True), 5)
        result = client.portal.call(run)
        assert result["deferred_tts"] is True
        assert result["text"]
        assert result["audio_base64"] == ""
        assert result["timings"]["tts_ms"] == 0
        assert engine.requests_started == 1


def test_streaming_text_api_emits_answer_then_local_voice(tmp_path):
    engine=service(tmp_path)
    with TestClient(create_app(Settings(tmp_path),voice_service=FakeSpeech(),conversation_service=engine)) as client:
        result=client.post("/api/conversation/text",json={"text":"Bonjour","session_id":SID})
        assert result.status_code==200
        assert result.headers["content-type"].startswith("application/x-ndjson")
        events=[json.loads(line) for line in result.text.splitlines()]
        assert [event["type"] for event in events]==["phase","delta","answer","phase","done"]
        assert events[-1]["timings"]["tts_ms"]==10
        assert KEY not in result.text
        assert client.get("/api/status").json()["capabilities"]["command_code"]
        assert client.get("/api/schedules").json()["items"]==[]
        assert client.post("/api/conversation/reset",json={"session_id":SID}).json()["reset"]
        assert not engine._history


def test_no_key_still_allows_audio_test_and_reports_chat_unavailable(tmp_path):
    with TestClient(create_app(Settings(tmp_path),voice_service=FakeSpeech())) as client:
        result=client.post("/api/conversation/text",json={"text":"Bonjour","session_id":SID})
        assert result.status_code==200
        events=[json.loads(line) for line in result.text.splitlines() if line.strip()]
        assert any(event["type"]=="error" and "Command Code" in event["message"] for event in events)
        assert not any(event["type"]=="answer" for event in events)
        assert not client.get("/api/status").json()["capabilities"]["command_code"]


def test_access_check_uses_no_personal_history(tmp_path):
    engine=service(tmp_path)
    complete(engine,"Message privé de test")
    with TestClient(create_app(Settings(tmp_path),voice_service=FakeSpeech(),conversation_service=engine)) as client:
        result=client.post("/api/ai/check",json={})
        assert result.status_code==200
        assert KEY not in result.text
        assert engine.verified
        assert len(engine._history)==1


def test_model_manager_keeps_legacy_model_and_probes_without_activating(tmp_path):
    original, candidate = "provider/current-model", "provider/other-model"
    credentials = CredentialStore(tmp_path)
    credentials._write({"api_key": KEY, "model": original})
    requests = []

    def handler(request):
        body = json.loads(request.content)
        requests.append(body)
        if body["model"] == "provider/denied":
            return httpx.Response(403)
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=sse())

    engine = service(tmp_path, handler)
    complete(engine, "Message privé de test")
    app = create_app(Settings(tmp_path), voice_service=FakeSpeech(), conversation_service=engine)
    with TestClient(app) as client:
        assert client.get("/api/ai/config").json()["models"] == [original]
        assert client.post("/api/ai/models", json={"action": "select", "model": candidate}).status_code == 422
        add = client.post("/api/ai/models", json={"action": "add", "model": candidate})
        assert add.status_code == 200 and KEY not in add.text
        assert add.json()["models"] == [original, candidate]
        assert add.json()["model"] == original

        probe = client.post("/api/ai/models/test", json={"model": candidate})
        assert probe.status_code == 200
        assert probe.json() == {"ok": True, "model": candidate, "llm_ms": probe.json()["llm_ms"]}
        assert isinstance(probe.json()["llm_ms"], int) and probe.json()["llm_ms"] >= 0
        assert requests[-1]["model"] == candidate and "tools" not in requests[-1]
        assert requests[-1]["messages"] == [{"role": "user", "content": "Réponds uniquement : Alfred est prêt."}]
        assert len(engine._history) == 1
        refused = client.post("/api/ai/models/test", json={"model": "provider/denied"})
        assert refused.status_code == 502 and "Accès refusé" in refused.json()["detail"]
        assert client.get("/api/ai/config").json()["model"] == original

        switched = client.post("/api/ai/models", json={"action": "select", "model": candidate}).json()
        assert switched["model"] == candidate and not switched["access_verified"]
        assert complete(engine)[-1]["model"] == candidate
        switched_back = client.post("/api/ai/models", json={"action": "select", "model": original}).json()
        assert switched_back["model"] == original
        assert client.post("/api/ai/models", json={"action": "select", "model": candidate},
                           headers={"Origin": "https://other.example"}).status_code == 403
    assert CredentialStore(tmp_path).public()["models"] == [original, candidate]


def test_silent_voice_does_not_use_command_code(tmp_path):
    import io
    import wave
    class Silent(FakeSpeech):
        def transcribe(self,data):return "",1.0,20
    audio=io.BytesIO()
    with wave.open(audio,"wb") as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(16000);wav.writeframes(bytes(32000))
    engine=service(tmp_path)
    with TestClient(create_app(Settings(tmp_path),voice_service=Silent(),conversation_service=engine)) as client:
        response=client.post("/api/conversation/voice",content=audio.getvalue(),headers={"Content-Type":"audio/wav","X-Alfred-Session":SID})
        events=[json.loads(line) for line in response.text.splitlines()]
        assert events[-1]["type"]=="error"
        assert engine.requests_started==0


def test_voice_conversation_reuses_local_speech_with_no_house_action(tmp_path):
    import io
    import wave
    audio=io.BytesIO()
    with wave.open(audio,"wb") as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(16000);wav.writeframes(bytes(32000))
    engine=service(tmp_path)
    with TestClient(create_app(Settings(tmp_path),voice_service=FakeSpeech(),conversation_service=engine)) as client:
        response=client.post("/api/conversation/voice",content=audio.getvalue(),headers={"Content-Type":"audio/wav","X-Alfred-Session":SID})
        events=[json.loads(line) for line in response.text.splitlines()]
        assert events[1]["type"]=="transcript"
        assert events[-1]["type"]=="done"
        assert events[-1]["timings"]["stt_ms"]==20
        assert engine.requests_started==1
        assert client.get("/api/schedules").json()["items"]==[]
