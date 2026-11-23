import json
import threading
import httpx
import pytest
from fastapi.testclient import TestClient
from alfred.announcements import Announcements
from alfred.app import create_app
from alfred.config import Settings
from alfred.conversation import ConversationService
from alfred.credentials import CredentialStore
from alfred.home_assistant import HomeError, HomeService, HomeStore

TARGETS = [{"entity_id":"assist_satellite.bureau", "room":"Bureau", "floor":"rdc"},
           {"entity_id":"assist_satellite.chambre", "room":"Chambre", "floor":"etage1"}]


def setup(tmp_path, handler):
    store = HomeStore(tmp_path)
    store.save("http://192.168.77.21:8123", "faux-jeton-test-0123456789", "Bureau")
    home = HomeService(store, lambda: httpx.Client(transport=httpx.MockTransport(handler)))
    (tmp_path / "announcement-targets.json").write_text(json.dumps({"targets":TARGETS,"delivery_mode":"ha_pipeline"}))
    return Announcements(home, tmp_path), home


def test_announcement_scope_and_default_to_all_configured(tmp_path):
    calls=[]
    def handler(request):
        calls.append(json.loads(request.content))
        return httpx.Response(200,json=[])
    service, _ = setup(tmp_path,handler)
    assert service.send("Le repas est prêt") == {"accepted":["Bureau","Chambre"], "incomplete":False}
    assert [entry["entity_id"] for entry in calls] == ["assist_satellite.bureau", "assist_satellite.chambre"]
    calls.clear()
    service.send("Essai", "room", "bureau")
    assert [entry["entity_id"] for entry in calls] == ["assist_satellite.bureau"]
    with pytest.raises(HomeError): service.send("Essai", "room", "Cuisine")
    assert len(calls) == 1


def test_announcement_reports_partial_without_retry(tmp_path):
    calls=[]
    def handler(request):
        calls.append(request)
        if len(calls)==2: raise httpx.ReadTimeout("réponse perdue")
        return httpx.Response(200,json=[])
    service, _ = setup(tmp_path,handler)
    assert service.send("Essai") == {"accepted":["Bureau"],"incomplete":True}
    assert len(calls) == 2


def test_announcement_tool_and_api(tmp_path):
    calls=[]
    def handler(request):
        calls.append(json.loads(request.content))
        return httpx.Response(200,json=[])
    announcements, home = setup(tmp_path,handler)
    engine=ConversationService(CredentialStore(tmp_path,api_key="faux-jeton-test-0123456789"))
    engine.announcements=announcements
    reply=engine.run_shopping_tool({0:{"name":"annoncer_message","arguments":json.dumps({"message":"Repas prêt", "scope":"floor", "target":"etage1"})}},threading.Event())
    assert "1 terminal" in reply and calls[-1]["entity_id"] == "assist_satellite.chambre"
    with TestClient(create_app(Settings(tmp_path),home_service=home)) as client:
        result=client.post("/api/announcements",json={"message":"Essai","scope":"room","target":"Bureau"})
        assert result.status_code==200 and result.json()["accepted"]==["Bureau"]
        assert client.post("/api/announcements",json={"message":"Essai","scope":"room","target":"Cuisine"}).status_code==502


def test_unselected_voice_never_dispatches_text_to_home_assistant(tmp_path):
    service, _ = setup(tmp_path, lambda request: (_ for _ in ()).throw(AssertionError("aucun appel")))
    service.path.write_text(json.dumps({"targets": TARGETS}))
    with pytest.raises(HomeError, match="pas encore activée"):
        service.send("Message privé")
