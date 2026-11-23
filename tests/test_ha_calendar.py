import json
from datetime import datetime, timedelta, timezone
import httpx
import pytest
from alfred.ha_calendar import CalendarClient, CalendarBindings, parse_reminder_marker
from alfred.home_assistant import HomeError, HomeService, HomeStore
from websockets.uri import parse_uri

START=datetime(2026,11,1,18,0,tzinfo=timezone.utc)


def client(tmp_path, handler):
    store=HomeStore(tmp_path);store.save("http://192.168.77.21:8123","jeton-fictif-0123456789","Bureau")
    home=HomeService(store,lambda:httpx.Client(transport=httpx.MockTransport(handler)))
    return CalendarClient(home,{"calendar.personnel"})


def test_calendar_access_uses_ha_as_source(tmp_path):
    calls=[]
    def handler(request):
        calls.append(request)
        if request.url.path.endswith("get_events"):
            return httpx.Response(200,json={"service_response":{"calendar.personnel":{"events":[{"summary":"test fictif"}]}}})
        return httpx.Response(200,json=[])
    calendar=client(tmp_path,handler)
    assert calendar.events("calendar.personnel",START,START+timedelta(days=1))[0]["summary"]=="test fictif"
    assert "demandée" in calendar.create("calendar.personnel","test fictif",START,START+timedelta(minutes=5))
    assert json.loads(calls[-1].content)["entity_id"]=="calendar.personnel"


def test_no_write_on_wrong_calendar_or_unimplemented_recurrence(tmp_path):
    calls=[]
    calendar=client(tmp_path,lambda request: calls.append(request) or httpx.Response(200,json=[]))
    with pytest.raises(HomeError): calendar.create("calendar.travail","test",START,START+timedelta(minutes=1))
    with pytest.raises(HomeError): calendar.create("calendar.personnel","test",START,START+timedelta(minutes=1),recurrence="weekly")
    assert not calls


def test_uncertain_creation_is_not_retried(tmp_path):
    calls=[]
    def handler(request): calls.append(request); raise httpx.ReadTimeout("perdu")
    calendar=client(tmp_path,handler)
    with pytest.raises(HomeError,match="non confirmée"): calendar.create("calendar.personnel","test",START,START+timedelta(minutes=1))
    assert len(calls)==1


def test_calendar_bindings_do_not_guess_missing_person_or_family(tmp_path):
    owner="a"*32
    (tmp_path/"calendar-targets.json").write_text(json.dumps({"personal":{owner:"calendar.personnel"},"family":None}))
    bindings=CalendarBindings(tmp_path)
    assert bindings.personal(owner)=="calendar.personnel"
    with pytest.raises(HomeError): bindings.personal("b"*32)
    with pytest.raises(HomeError): bindings.family()


def test_recurring_reminder_uses_single_home_assistant_event_and_marker(tmp_path):
    store=HomeStore(tmp_path);store.save("http://192.168.77.21:8123","jeton-fictif-0123456789","Bureau")
    home=HomeService(store)
    sent=[]
    class FakeWebSocket:
        def __init__(self, uri):
            self.protocol=type("Protocol",(),{"uri":parse_uri(uri)})()
            self.responses=iter([json.dumps({"type":"auth_required"}),json.dumps({"type":"auth_ok"}),json.dumps({"type":"result","id":1,"success":True})])
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def recv(self,timeout=None): return next(self.responses)
        def send(self,value): sent.append(json.loads(value))
    client=CalendarClient(home,{"calendar.personnel"},websocket_factory=lambda uri,**kw:FakeWebSocket(uri))
    assert "enregistré" in client.create_reminder("calendar.personnel","Essai fictif",START,"Bureau",recurrence="weekly")
    event=sent[-1]["event"]
    assert event["rrule"]=="FREQ=WEEKLY"
    assert event["dtstart"]==START.isoformat() and "start" not in event
    assert parse_reminder_marker(event["description"])["room"]=="Bureau"
    assert sent[-1]["entity_id"]=="calendar.personnel"
    assert parse_reminder_marker("Rendez-vous habituel") is None
    assert parse_reminder_marker('ALFRED_RAPPEL_V1:{"room":"Bureau"}') is None


def test_websocket_redirect_is_refused_before_sending_token(tmp_path):
    store=HomeStore(tmp_path);store.save("http://192.168.77.21:8123","jeton-fictif-0123456789","Bureau")
    sent=[]
    class FakeWebSocket:
        protocol=type("Protocol",(),{"uri":parse_uri("ws://ailleurs.example/api/websocket")})()
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def send(self,value): sent.append(value)
    calendar=CalendarClient(HomeService(store),{"calendar.personnel"},websocket_factory=lambda *a,**kw:FakeWebSocket())
    with pytest.raises(HomeError,match="Redirection"): calendar.create_reminder("calendar.personnel","test",START,"Bureau")
    assert sent==[]


def test_websocket_uncertain_result_never_retries(tmp_path):
    store=HomeStore(tmp_path);store.save("http://192.168.77.21:8123","jeton-fictif-0123456789","Bureau")
    connections=[]; sent=[]
    class FakeWebSocket:
        def __init__(self,uri): self.protocol=type("Protocol",(),{"uri":parse_uri(uri)})();self.n=0
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def recv(self,timeout=None):
            self.n+=1
            if self.n==1: return json.dumps({"type":"auth_required"})
            if self.n==2: return json.dumps({"type":"auth_ok"})
            raise TimeoutError("réponse perdue")
        def send(self,value): sent.append(json.loads(value))
    def connect_once(uri,**kwargs): connections.append(uri);return FakeWebSocket(uri)
    calendar=CalendarClient(HomeService(store),{"calendar.personnel"},websocket_factory=connect_once)
    with pytest.raises(HomeError,match="non confirmée"): calendar.create_reminder("calendar.personnel","test",START,"Bureau",recurrence="weekly")
    assert len(connections)==1 and sum(x.get("type")=="calendar/event/create" for x in sent)==1
