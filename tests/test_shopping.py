import json
import httpx
import pytest
from fastapi.testclient import TestClient
from alfred.app import create_app
from alfred.config import Settings
from alfred.home_assistant import HomeStore, HomeService
from alfred.shopping import Shopping, item_key

ENTITY = "todo.liste_familiale_test"


@pytest.mark.parametrize("phrase", ["il y a quoi dans la liste", "Y a quoi sur la liste ?",
    "qu'est-ce qu'il y a dans la liste de courses", "Alfred, lis ma liste", "Jarvis, lis ma liste", "Jarvisse, lis ma liste"])
def test_natural_list_questions_route_to_shopping(tmp_path, phrase):
    def handler(request):
        if request.method == "GET":
            return httpx.Response(200, json={"entity_id": ENTITY, "state": "1"})
        return httpx.Response(200, json={"service_response": {ENTITY: {"items": [{"summary": "lait"}]}}})
    shop, _ = make(tmp_path, handler)
    assert "lait" in shop.handle(phrase)
    assert shop.handle("il y a quoi dans la liste des films") is None


def make(tmp_path, handler):
    store = HomeStore(tmp_path)
    store.save("http://192.168.77.21:8123", "faux-jeton-test-0123456789", "Bureau")
    home = HomeService(store, lambda: httpx.Client(transport=httpx.MockTransport(handler)))
    shop = Shopping(home, tmp_path)
    shop.configure(ENTITY)
    return shop, home


def test_read_and_add_use_only_configured_list(tmp_path):
    calls = []
    def handler(request):
        calls.append(request)
        if request.method == "GET":
            return httpx.Response(200, json={"entity_id": ENTITY, "state": "1"})
        if request.url.path.endswith("get_items"):
            assert request.url.params.get("return_response") == ""
            return httpx.Response(200, json={"service_response": {ENTITY: {"items": [{"summary": "lait"}]}}})
        return httpx.Response(200, json=[])
    shop, _ = make(tmp_path, handler)
    assert "lait" in shop.handle("qu'y a-t-il sur la liste de courses ?")
    assert "ajout demandé" in shop.handle("ajoute du pain à la liste de courses")
    assert json.loads(calls[-1].content) == {"entity_id": ENTITY, "item": "du pain"}
    assert "un seul article" in shop.handle("ajoute du pain et raconte une blague à la liste de courses")
    assert len(calls) == 6


def test_unknown_result_on_timeout_does_not_retry(tmp_path):
    calls = []
    def handler(request):
        calls.append(request)
        if request.method == "GET":
            return httpx.Response(200, json={"entity_id": ENTITY, "state": "0"})
        raise httpx.ReadTimeout("test")
    shop, _ = make(tmp_path, handler)
    assert "non confirmé" in shop.handle("ajoute du lait à la liste de courses")
    assert len(calls) == 2


def test_conversation_and_api_use_the_same_list(tmp_path):
    calls = []
    def handler(request):
        calls.append(request)
        if request.method == "GET":
            return httpx.Response(200, json={"entity_id": ENTITY, "state": "0"})
        if request.url.path.endswith("get_items"):
            return httpx.Response(200, json={"service_response": {ENTITY: {"items": []}}})
        return httpx.Response(200, json=[])
    _, home = make(tmp_path, handler)
    class Voice:
        def speak(self, text): return b"audio", 1
    class AI:
        def stream(self, *args, **kwargs): raise AssertionError("IA non attendue")
    with TestClient(create_app(Settings(tmp_path), home_service=home, voice_service=Voice(), conversation_service=AI())) as client:
        assert client.get("/api/shopping/config").json()["entity_id"] == ENTITY
        response = client.post("/api/conversation/text", json={"text":"ajoute du lait à la liste de courses", "session_id":"session-test-000001"})
        events = [json.loads(line) for line in response.text.splitlines()]
        assert events[-1]["mode"] == "home"
        assert json.loads(calls[-1].content)["item"] == "du lait"
        assert client.post("/api/shopping/config", json={"entity_id":"light.salon"}).status_code == 422


def test_duplicates_are_skipped_for_voice_and_web(tmp_path):
    calls = []
    def handler(request):
        calls.append(request)
        if request.method == "GET":
            return httpx.Response(200, json={"entity_id": ENTITY, "state": "1"})
        return httpx.Response(200, json={"service_response": {ENTITY: {"items": [{"summary": "Café"}]}}})
    shop, home = make(tmp_path, handler)
    assert "déjà" in shop.handle("ajoute du cafe à la liste de courses")
    with TestClient(create_app(Settings(tmp_path), home_service=home)) as client:
        result = client.post("/api/shopping/items", json={"item": "le CAFÉ"})
        assert result.json()["duplicate"] is True
        assert "déjà" in result.json()["message"]
    assert not any(call.url.path.endswith("add_item") for call in calls)
    assert item_key("durian") != item_key("rian")
    assert item_key("2 litres de lait") != item_key("lait")


def test_add_is_not_attempted_if_list_cannot_be_read(tmp_path):
    calls = []
    def handler(request):
        calls.append(request)
        if request.method == "GET":
            return httpx.Response(200, json={"entity_id": ENTITY, "state": "1"})
        return httpx.Response(503, json={})
    shop, _ = make(tmp_path, handler)
    with pytest.raises(Exception): shop.request("add_item", "pain")
    assert not any(call.url.path.endswith("add_item") for call in calls)


def test_complete_targets_uid_and_keeps_existing_list(tmp_path):
    calls = []
    def handler(request):
        calls.append(request)
        if request.method == "GET":
            return httpx.Response(200, json={"entity_id": ENTITY, "state": "1"})
        if request.url.path.endswith("get_items"):
            return httpx.Response(200, json={"service_response": {ENTITY: {"items": [{"summary": "Café", "uid": "article-unique"}]}}})
        return httpx.Response(200, json=[])
    shop, home = make(tmp_path, handler)
    assert shop.request("complete_item", "du cafe") == {"completed": "Café"}
    assert calls[-1].url.path.endswith("update_item")
    assert json.loads(calls[-1].content) == {"entity_id": ENTITY, "item": "article-unique", "status": "completed"}
    with TestClient(create_app(Settings(tmp_path), home_service=home)) as client:
        assert "coché" in client.post("/api/shopping/items/complete", json={"item": "café"}).json()["message"]


@pytest.mark.parametrize("items", [[], [{"summary": "lait", "uid": "1"}, {"summary": "du lait", "uid": "2"}], [{"summary": "lait"}]])
def test_complete_refuses_missing_ambiguous_or_no_uid(tmp_path, items):
    calls = []
    def handler(request):
        calls.append(request)
        if request.method == "GET":
            return httpx.Response(200, json={"entity_id": ENTITY, "state": "1"})
        return httpx.Response(200, json={"service_response": {ENTITY: {"items": items}}})
    shop, _ = make(tmp_path, handler)
    with pytest.raises(Exception): shop.request("complete_item", "lait")
    assert not any(call.url.path.endswith("update_item") for call in calls)


def test_rename_restore_and_delete_target_exact_uid(tmp_path):
    calls = []
    def handler(request):
        calls.append(request)
        if request.method == "GET":
            return httpx.Response(200, json={"entity_id": ENTITY, "state": "1"})
        if request.url.path.endswith("get_items"):
            status = json.loads(request.content)["status"]
            items = ([{"summary": "lait", "uid": "active"}] if status == "needs_action" else
                     [{"summary": "café", "uid": "checked"}] if status == "completed" else
                     [{"summary": "lait", "uid": "active"}, {"summary": "café", "uid": "checked"}])
            return httpx.Response(200, json={"service_response": {ENTITY: {"items": items}}})
        return httpx.Response(200, json=[])
    shop, home = make(tmp_path, handler)
    assert shop.request("rename_item", "lait", "2 litres de lait")["new_name"] == "2 litres de lait"
    assert json.loads(calls[-1].content) == {"entity_id": ENTITY, "item": "active", "rename": "2 litres de lait"}
    assert shop.request("restore_item", "café")["restored"] == "café"
    assert json.loads(calls[-1].content)["status"] == "needs_action"
    assert shop.request("delete_item", "café")["deleted"] == "café"
    assert calls[-1].url.path.endswith("remove_item")
    assert json.loads(calls[-1].content)["item"] == "checked"
    with TestClient(create_app(Settings(tmp_path), home_service=home)) as client:
        assert client.get("/api/shopping/items/completed").json()["items"] == ["café"]
        assert client.post("/api/shopping/items/delete", json={"item":"café", "confirm_delete":False}).status_code == 422


def test_restore_refuses_duplicate_active_and_delete_refuses_ambiguity(tmp_path):
    calls = []
    def handler(request):
        calls.append(request)
        if request.method == "GET":
            return httpx.Response(200, json={"entity_id": ENTITY, "state": "1"})
        status = json.loads(request.content)["status"]
        entries = [{"summary": "lait", "uid": "a"}, {"summary": "du lait", "uid": "b"}]
        if status == "completed": entries = entries[:1]
        return httpx.Response(200, json={"service_response": {ENTITY: {"items": entries}}})
    shop, _ = make(tmp_path, handler)
    for action in ("restore_item", "delete_item"):
        with pytest.raises(Exception): shop.request(action, "lait")
    assert not any(call.url.path.endswith(("update_item", "remove_item")) for call in calls)


def test_rename_refuses_existing_new_name(tmp_path):
    calls = []
    def handler(request):
        calls.append(request)
        if request.method == "GET":
            return httpx.Response(200, json={"entity_id": ENTITY, "state": "2"})
        return httpx.Response(200, json={"service_response": {ENTITY: {"items": [
            {"summary": "lait", "uid": "a"}, {"summary": "café", "uid": "b"}]}}})
    shop, _ = make(tmp_path, handler)
    with pytest.raises(Exception): shop.request("rename_item", "lait", "du cafe")
    assert not any(call.url.path.endswith("update_item") for call in calls)


def test_list_lifecycle_via_api(tmp_path):
    records = []
    def handler(request):
        if request.method == "GET":
            return httpx.Response(200, json={"entity_id": ENTITY, "state": "0"})
        payload = json.loads(request.content)
        if request.url.path.endswith("get_items"):
            status = payload["status"]
            allowed = status if isinstance(status, list) else [status]
            return httpx.Response(200, json={"service_response": {ENTITY: {"items": [r.copy() for r in records if r["status"] in allowed]}}})
        if request.url.path.endswith("add_item"):
            records.append({"uid": "test-uid", "summary": payload["item"], "status": "needs_action"})
        if request.url.path.endswith("update_item"):
            record = next(r for r in records if r["uid"] == payload["item"])
            record.update({"summary": payload.get("rename", record["summary"]), "status": payload.get("status", record["status"])})
        if request.url.path.endswith("remove_item"):
            records[:] = [r for r in records if r["uid"] != payload["item"]]
        return httpx.Response(200, json=[])
    _, home = make(tmp_path, handler)
    with TestClient(create_app(Settings(tmp_path), home_service=home)) as client:
        assert client.post("/api/shopping/items", json={"item": "lait"}).status_code == 200
        assert client.post("/api/shopping/items/rename", json={"item": "lait", "new_name": "2 litres de lait"}).status_code == 200
        assert client.post("/api/shopping/items/complete", json={"item": "2 litres de lait"}).status_code == 200
        assert client.get("/api/shopping/items").json()["items"] == []
        assert client.get("/api/shopping/items/completed").json()["items"] == ["2 litres de lait"]
        response = client.post("/api/shopping/items", json={"item": "2 litres de lait"})
        assert response.json()["restored"] is True
        assert len(records) == 1
        assert client.get("/api/shopping/items").json()["items"] == ["2 litres de lait"]
        assert client.post("/api/shopping/items/delete", json={"item": "2 litres de lait", "confirm_delete": True}).status_code == 200
        assert records == []


def test_purge_deletes_active_and_completed_by_uid(tmp_path):
    entries = [{"summary": "lait", "uid": "1", "status": "needs_action"},
               {"summary": "café", "uid": "2", "status": "completed"}]
    def handler(request):
        if request.method == "GET": return httpx.Response(200, json={"entity_id": ENTITY, "state": "1"})
        body = json.loads(request.content)
        if request.url.path.endswith("get_items"):
            return httpx.Response(200, json={"service_response": {ENTITY: {"items": entries.copy()}}})
        entries[:] = [entry for entry in entries if entry["uid"] != body["item"]]
        return httpx.Response(200, json=[])
    shop, _ = make(tmp_path, handler)
    assert shop.request("purge_items") == {"removed": 2, "remaining": 0, "incomplete": False}
    assert entries == []


def test_purge_stops_on_failure_without_retry(tmp_path):
    calls = []
    def handler(request):
        calls.append(request)
        if request.method == "GET": return httpx.Response(200, json={"entity_id": ENTITY, "state": "1"})
        if request.url.path.endswith("get_items"):
            return httpx.Response(200, json={"service_response": {ENTITY: {"items": [{"summary":"a","uid":"1"}, {"summary":"b","uid":"2"}]}}})
        raise httpx.ReadTimeout("perdu")
    shop, _ = make(tmp_path, handler)
    assert shop.request("purge_items") == {"removed": 0, "incomplete": True}
    assert sum(r.url.path.endswith("remove_item") for r in calls) == 1


@pytest.mark.parametrize("completed", [
    [{"summary": "Sucre", "uid": "checked-1"}],
    [{"summary": "Sucre", "uid": "checked-1"}, {"summary": "du sucre", "uid": "checked-2"}],
])
def test_add_restores_single_completed_or_refuses_ambiguous(tmp_path, completed):
    calls = []
    def handler(request):
        calls.append(request)
        if request.method == "GET": return httpx.Response(200, json={"entity_id": ENTITY, "state": "0"})
        if request.url.path.endswith("get_items"):
            status = json.loads(request.content)["status"]
            return httpx.Response(200, json={"service_response": {ENTITY: {"items": completed if status == "completed" else []}}})
        return httpx.Response(200, json=[])
    shop, _ = make(tmp_path, handler)
    if len(completed) == 1:
        assert shop.request("add_item", "du sucre")["restored"] is True
        assert json.loads(calls[-1].content) == {"entity_id": ENTITY, "item": "checked-1", "status": "needs_action"}
    else:
        with pytest.raises(Exception): shop.request("add_item", "du sucre")
        assert not any(r.url.path.endswith("update_item") for r in calls)
    assert not any(r.url.path.endswith("add_item") for r in calls)
