import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient
from websockets.uri import parse_uri

from alfred.app import create_app
from alfred.config import Settings
from alfred.home_assistant import HomeService, HomeStore, parse_light_command
from alfred.home_catalog import HomeCatalog, CatalogError
from alfred.home_exclusions import HomeExclusions, ExclusionError
from alfred.home_aliases import HomeAliases, AliasError, HomeLabels
from alfred.home_confirmations import HomeConfirmations
from alfred.light_actions import LightAction, LightActions


def test_exclusions_persist_and_invalid_save_keeps_previous(tmp_path):
    store = HomeExclusions(tmp_path)
    assert store.save(["light.a", "light.a"]) == ["light.a"]
    with pytest.raises(ExclusionError):
        store.save(["../invalid"])
    assert HomeExclusions(tmp_path).load() == ["light.a"]


class FakeSocket:
    def __init__(self, uri, responses):
        self.protocol = SimpleNamespace(uri=parse_uri(uri))
        self.responses = iter([{"type": "auth_required"}, {"type": "auth_ok"}] + responses)
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def send(self, value): pass
    def recv(self, **kwargs): return json.dumps(next(self.responses))


def test_catalog_respects_explicit_and_default_exposure(tmp_path):
    store = HomeStore(tmp_path, base_url="http://localhost:8123", token="test")
    home = HomeService(store)
    state = lambda name, **attrs: {"entity_id": name, "state": "off", "attributes": attrs}
    results = [
        {"exposed_entities": {"light.explicit": {"conversation": True}, "light.alexa": {"cloud.alexa": True}}},
        {"expose_new": True},
        [{"entity_id": "light.blocked", "options": {"conversation": {"should_expose": False}}}, {"entity_id": "light.alexa", "options": {"conversation": {"should_expose": False}}}, {"entity_id": "light.default"}, {"entity_id": "sensor.temp"}],
        [], [], [],
        [state("light.explicit"), state("light.alexa"), state("light.default"), state("light.blocked"), state("sensor.temp", device_class="temperature")],
        {"light.default": {"aliases": ["lumière douce"]}},
    ]
    responses = [{"id": i, "success": True, "result": value} for i, value in enumerate(results, 1)]
    catalog = HomeCatalog(home, websocket_factory=lambda uri, **kwargs: FakeSocket(uri, responses)).snapshot()
    assert {x["entity_id"] for x in catalog["entities"]} == {"light.explicit", "light.default", "sensor.temp"}
    assert next(x for x in catalog["entities"] if x["entity_id"] == "light.default")["ha_aliases"] == ["lumière douce"]


def test_home_service_reuses_the_catalog_client(tmp_path):
    home = HomeService(HomeStore(tmp_path, base_url="http://localhost:8123", token="test"))
    assert home.catalog() is home.catalog()


def test_devices_endpoint_returns_only_directory_fields(tmp_path, monkeypatch):
    home = HomeService(HomeStore(tmp_path))
    entity = {"entity_id": "input_text.note", "name": "Note", "device": None, "area": "Bureau",
              "domain": "input_text", "allowed": False, "state": "private value", "attributes": {"mode": "text"},
              "supported": True, "capabilities": ["read"], "confirmation_required": True,
              "aliases": ["Mémo"], "ha_aliases": ["Note Bureau"]}
    monkeypatch.setattr(HomeCatalog, "snapshot", lambda self: {"entities": [entity]})
    with TestClient(create_app(Settings(tmp_path), home_service=home)) as client:
        response = client.get("/api/home/devices")
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
        assert response.json() == {"items": [{"id": "input_text.note", "name": "Note", "device": None,
                                              "area": "Bureau", "domain": "input_text", "allowed": False,
                                              "unavailable": False}]}
        editable = client.get("/api/home/devices?editable=true").json()["items"][0]
        assert editable == {**response.json()["items"][0], **{
            key: entity[key] for key in ("supported", "capabilities", "confirmation_required", "aliases", "ha_aliases")},
            "ha_name": "Note", "alfred_name": "", "ha_area": "Bureau", "alfred_area": ""}
        entity["state"] = "unavailable"
        assert client.get("/api/home/devices").json()["items"][0]["unavailable"] is True


def test_device_edits_preserve_other_entities_and_settings(tmp_path):
    home = HomeService(HomeStore(tmp_path))
    HomeExclusions(tmp_path).save(["light.other"])
    HomeConfirmations(tmp_path).save(["light.other"])
    HomeAliases(tmp_path).save({"light.other": ["Autre"]})
    with TestClient(create_app(Settings(tmp_path), home_service=home)) as client:
        def save(setting, value):
            return client.patch("/api/home/devices", json={"id": "light.test", "setting": setting, "value": value})

        assert save("allowed", False).json() == {"value": False}
        assert save("confirmation_required", True).json() == {"value": True}
        assert save("aliases", [" Test ", "Test"]).json() == {"value": ["Test"]}
        assert save("confirmation_required", []).status_code == 422
        assert save("aliases", ["x" * 81]).status_code == 422
        store = home.catalog().settings
        assert store.load()["excluded"] == ["light.other", "light.test"]
        assert store.load()["confirmations"] == ["light.other", "light.test"]
        assert store.load()["aliases"] == {"light.other": ["Autre"], "light.test": ["Test"]}
        assert save("aliases", []).json() == {"value": []}
        assert save("allowed", True).json() == {"value": True}
        assert store.load()["aliases"] == {"light.other": ["Autre"]}
        assert store.load()["excluded"] == ["light.other"]
        assert store.load()["confirmations"] == ["light.other", "light.test"]


def test_custom_name_drives_switch_replies_and_can_be_reset(tmp_path):
    entity = "switch.pc_salon_commutateur"
    original = "PC salon Commutateur"
    state = {"entity_id": entity, "state": "off", "attributes": {"friendly_name": original}}
    calls = []

    def respond(request):
        calls.append(request.method)
        assert request.method == "GET"
        return httpx.Response(200, json=state)

    home = HomeService(HomeStore(tmp_path, base_url="http://localhost:8123", token="test"),
                       lambda: httpx.Client(transport=httpx.MockTransport(respond)))
    results = [{"exposed_entities": {entity: {"conversation": True}}}, {"expose_new": False},
               [{"entity_id": entity}], [], [], [], [state], {entity: {"aliases": ["Prise PC"]}}]
    responses = [{"id": i, "success": True, "result": value} for i, value in enumerate(results, 1)]
    home.catalog().websocket_factory = lambda uri, **kwargs: FakeSocket(uri, responses)
    HomeConfirmations(tmp_path).save([entity])
    with TestClient(create_app(Settings(tmp_path), home_service=home)) as client:
        def rename(value):
            return client.patch("/api/home/devices", json={"id": entity, "setting": "alfred_name", "value": value})

        assert rename("  Imprimante  ").json() == {"value": "Imprimante"}
        assert rename(["Invalide"]).status_code == 422
        assert rename("x" * 81).status_code == 422
        item = client.get("/api/home/devices?editable=true").json()["items"][0]
        assert (item["name"], item["alfred_name"], item["ha_name"]) == ("Imprimante", "Imprimante", original)
        assert item["ha_aliases"] == ["Prise PC"]
        for name in ("Imprimante", original, "Prise PC"):
            assert "Imprimante" in home.handle(f"Quel est l'état de {name} ?")["reply"]
        assert home.handle("Allume l’imprimante")["reply"] == "Voulez-vous vraiment allumer Imprimante ?"
        assert rename("").json() == {"value": ""}
        assert client.get("/api/home/devices?editable=true").json()["items"][0]["name"] == original
    assert calls == ["GET"] * 4


def test_device_batch_migrates_settings_and_changes_room_targets(tmp_path, monkeypatch):
    group, moved, remaining, unassigned = ("light.salon", "light.lampe", "light.plafond", "light.baladeuse")
    branch, hidden = "light.groupe_interieur", "light.ampoule_masquee"
    ids = [group, moved, remaining, unassigned, branch, hidden]
    home = HomeService(HomeStore(tmp_path, base_url="http://localhost:8123", token="test"),
                       lambda: pytest.fail("Le réglage et la résolution ne doivent pas appeler de service HA."))
    registry = [{"entity_id": entity, "area_id": None if entity in {unassigned, hidden} else "salon"}
                for entity in ids]
    registry[-1]["options"] = {"conversation": {"should_expose": False}}
    states = [{"entity_id": entity, "state": "on", "attributes": {}} for entity in ids]
    states[0]["attributes"]["entity_id"] = [moved, remaining, branch]
    states[4]["attributes"]["entity_id"] = [hidden]
    results = [{"exposed_entities": {}}, {"expose_new": True}, registry,
               [{"area_id": "salon", "name": "Salon"}, {"area_id": "bureau", "name": "Bureau", "floor_id": "up"},
                {"area_id": "atelier", "name": "Atelier"}],
               [], [{"floor_id": "up", "name": "Premier", "level": 1}], states, {}]
    responses = [{"id": i, "success": True, "result": value} for i, value in enumerate(results, 1)]
    home.catalog().websocket_factory = lambda uri, **kwargs: FakeSocket(uri, responses)
    actions = LightActions(home)
    HomeLabels(tmp_path, "home-rooms.json").set_label(remaining, "Ancienne pièce")
    HomeLabels(tmp_path, "home-names.json").set_label(remaining, "Plafonnier")

    def targets(room):
        return actions.resolve(LightAction(operation="read", scope="room", target=room), actions.catalog())

    with TestClient(create_app(Settings(tmp_path), home_service=home)) as client:
        def assign(entity, value):
            return client.patch("/api/home/devices", json={"id": entity, "setting": "alfred_area", "value": value})

        def edit(entity, **changes):
            return client.patch("/api/home/devices", json={"id": entity, "settings": changes})

        store = home.catalog().settings
        assert not store.path.exists()
        assert edit(moved, alfred_area="Pièce inconnue", alfred_name="Nouvelle lampe").status_code == 422
        assert not store.path.exists()
        assert edit(remaining, alfred_area="Ancienne pièce", aliases=["Plafond"]).json()["settings"]["alfred_area"] == "Ancienne pièce"
        assert store.path.exists()
        assert assign(remaining, "").status_code == 200
        result = edit(moved, alfred_area="Bureau", alfred_name="Lampe de travail", aliases=["Lampe de bureau"],
                      confirmation_required=True)
        assert result.json()["settings"] == {"alfred_area": "Bureau", "alfred_name": "Lampe de travail",
                                             "aliases": ["Lampe de bureau"], "allowed": True, "confirmation_required": True}
        assert assign(branch, "Bureau").json() == {"value": "Bureau"}
        assert assign(unassigned, "Atelier").json() == {"value": "Atelier"}
        assert assign(unassigned, ["Invalide"]).status_code == 422
        assert assign(unassigned, "Deux\nlignes").status_code == 422

        before = store.path.read_bytes()
        assert edit(moved, alfred_name="Autre lampe", aliases=["x" * 81]).status_code == 422
        assert store.path.read_bytes() == before
        with monkeypatch.context() as patch:
            def failed_replace(*args):
                raise OSError("Écriture simulée")

            patch.setattr("alfred.home_aliases.os.replace", failed_replace)
            assert edit(moved, alfred_name="Autre lampe", confirmation_required=False).status_code == 500
        assert store.path.read_bytes() == before
        assert not list(tmp_path.glob("home-device-settings-*.tmp"))

        directory = client.get("/api/home/devices?editable=true").json()
        items = {item["id"]: item for item in directory["items"]}
        assert set(directory["ha_rooms"]) == {"Salon", "Bureau", "Atelier"}
        assert directory["ha_room_floors"] == {"Bureau": {"name": "Premier", "level": 1}}
        assert items[remaining]["name"] == "Plafonnier"
        assert items[remaining]["aliases"] == ["Plafond"]
        assert items[moved]["confirmation_required"] is True
        assert items[moved]["ha_area"] == "Salon"
        assert items[unassigned]["ha_area"] is None
        assert items[unassigned]["area"] == items[unassigned]["alfred_area"] == "Atelier"
        assert next(item for item in actions.catalog()["entities"] if item["entity_id"] == moved)["floor"] == "Premier"
        assert targets("salon") == [remaining]
        assert targets("bureau") == sorted([moved, hidden])
        assert targets("atelier") == [unassigned]
        assert actions.resolve(LightAction(operation="turn_off", scope="all", exclude_rooms=["salon"]),
                               actions.catalog()) == sorted([moved, hidden, unassigned])

        assert assign(moved, "").json() == {"value": ""}
        assert assign(branch, "").json() == {"value": ""}
        assert assign(unassigned, "").json() == {"value": ""}

        # Un fichier d'avant le classement peut être relu sans migration manuelle.
        saved = json.loads(store.path.read_text(encoding="utf-8"))
        saved.pop("light_types")
        store.path.write_text(json.dumps(saved), encoding="utf-8")
        directory = client.get("/api/home/devices?editable=true").json()
        assert all(item["light_type"] == "main" for item in directory["items"])
        saved["light_types"] = {group: "ambient", remaining: "automatic"}
        store.path.write_text(json.dumps(saved), encoding="utf-8")
        directory = client.get("/api/home/devices?editable=true").json()
        assert next(item for item in directory["items"] if item["id"] == remaining)["light_type"] == "secondary"
        assert edit(group, light_type="secondary").json()["settings"]["light_type"] == "secondary"
        assert edit(remaining, light_type="main").json()["settings"]["light_type"] == "main"
        assert LightActions(home).resolve(LightAction(operation="turn_on", scope="room", target="Salon"),
                                         actions.catalog()) == [remaining]
        assert edit("switch.prise", light_type="secondary").status_code == 422
        assert edit(group, light_type="automatic").status_code == 422
        assert edit(group, light_type="main").json()["settings"]["light_type"] == "main"
        assert targets("salon") == sorted([moved, remaining, hidden])
        restored = next(item for item in client.get("/api/home/devices").json()["items"] if item["id"] == unassigned)
        assert restored["area"] is None

        local_room = "Toilettes du haut"
        assert assign(unassigned, local_room).status_code == 422
        payload = {"id": unassigned, "settings": {"alfred_area": local_room}}
        assert client.patch("/api/home/devices", json={**payload, "local_room": "Une autre pièce"}).status_code == 422
        assigned = client.patch("/api/home/devices", json={**payload, "local_room": local_room})
        assert assigned.status_code == 200
        assert assigned.json()["settings"]["alfred_area"] == local_room
        assert targets(local_room) == [unassigned]
        directory = client.get("/api/home/devices?editable=true").json()
        assert local_room in directory["rooms"]
        assert local_room not in directory["ha_rooms"]
        assert assign(unassigned, "").json() == {"value": ""}


def test_hidden_group_descendants_are_private_and_keep_exclusions(tmp_path):
    HomeExclusions(tmp_path).save(["light.leaf"])
    HomeConfirmations(tmp_path).save(["light.group", "light.leaf"])
    home = HomeService(HomeStore(tmp_path, base_url="http://localhost:8123", token="test"))
    ids = ["light.group", "light.nested", "light.leaf", "light.orphan"]
    registry = [{"entity_id": e, "options": {"conversation": {"should_expose": e == "light.group"}}} for e in ids]
    states = [{"entity_id": e, "state": "off", "attributes": {}} for e in ids]
    states[0]["attributes"]["entity_id"] = ["light.nested"]
    states[1]["attributes"]["entity_id"] = ["light.leaf"]
    states[2]["attributes"]["friendly_name"] = "Feuille"
    results = [{"exposed_entities": {"light.group": {"conversation": True}}}, {"expose_new": True},
               registry, [], [], [], states, {}]
    responses = [{"id": n, "success": True, "result": value} for n, value in enumerate(results, 1)]
    source = HomeCatalog(home, websocket_factory=lambda uri, **kw: FakeSocket(uri, responses))
    public = source.snapshot()
    assert [x["entity_id"] for x in public["entities"]] == ["light.group"]
    assert "light_group_members" not in public
    private = source.control_snapshot()
    assert set(private["light_group_members"]) == {"light.nested", "light.leaf"}
    assert private["light_group_members"]["light.leaf"]["allowed"] is False
    assert private["light_group_members"]["light.leaf"]["confirmation_required"] is True
    assert private["light_group_members"]["light.leaf"]["name"] == "Feuille"
    assert public["confirmations"] == ["light.group", "light.leaf"]
    assert public["entities"][0]["confirmation_required"] is True
    assert "light.orphan" not in private["light_group_members"]


def test_group_with_excluded_member_is_never_sent(tmp_path, monkeypatch):
    calls = []
    def respond(request):
        calls.append(request)
        if request.url.path == "/api/states":
            return httpx.Response(200, json=[{"entity_id": "light.group", "state": "on"}, {"entity_id": "light.a", "state": "on"}, {"entity_id": "light.b", "state": "on"}])
        return httpx.Response(200, json=[])
    store = HomeStore(tmp_path, base_url="http://localhost:8123", token="test")
    home = HomeService(store, lambda: httpx.Client(transport=httpx.MockTransport(respond)))
    entities = [{"entity_id": "light.group", "allowed": True, "members": ["light.a", "light.b"]},
                {"entity_id": "light.a", "allowed": True, "members": None},
                {"entity_id": "light.b", "allowed": False, "members": None}]
    monkeypatch.setattr(HomeCatalog, "snapshot", lambda self: {"entities": entities})
    home.execute(parse_light_command("éteins toutes les lumières"))
    assert json.loads(calls[-1].content)["entity_id"] == ["light.a"]


def test_catalog_failure_blocks_action(tmp_path, monkeypatch):
    home = HomeService(HomeStore(tmp_path, base_url="http://localhost:8123", token="test"))
    def fail(self): raise CatalogError("indisponible")
    monkeypatch.setattr(HomeCatalog, "snapshot", fail)
    assert "indisponible" in home.handle("allume toutes les lumières")["error"]


def test_alias_lights_and_ambiguous_alias_are_safe(tmp_path, monkeypatch):
    calls = []
    def respond(request):
        calls.append(request)
        return httpx.Response(200, json=[])
    home = HomeService(HomeStore(tmp_path, base_url="http://localhost:8123", token="test"), lambda: httpx.Client(transport=httpx.MockTransport(respond)))
    aliases = HomeAliases(tmp_path)
    aliases.save({"light.a": ["Lampe du canapé"]})
    entities = [{"entity_id": "light.a", "domain": "light", "allowed": True, "members": None, "aliases": ["Lampe du canapé"]}]
    monkeypatch.setattr(HomeCatalog, "snapshot", lambda self: {"entities": entities})
    result = home.handle("Hé Alfred allume la lampe du canapé")
    assert result["scope"] == "entity"
    assert result["reply"] == "une lumière allumée pour « lampe du canape »."
    assert json.loads(calls[-1].content)["entity_id"] == ["light.a"]
    aliases.save({"light.a": ["Lampe du canapé"], "light.b": ["Lampe du canapé"]})
    entities.append({"entity_id": "light.b", "domain": "light", "allowed": True, "members": None, "aliases": ["Lampe du canapé"]})
    count = len(calls)
    assert "Plusieurs" in home.handle("allume la lampe du canapé")["error"]
    assert len(calls) == count


def test_alias_excluded_light_never_acts(tmp_path, monkeypatch):
    aliases = HomeAliases(tmp_path)
    aliases.save({"light.a": ["coin lecture"]})
    home = HomeService(HomeStore(tmp_path, base_url="http://localhost:8123", token="test"), lambda: httpx.Client(transport=httpx.MockTransport(lambda request: pytest.fail("unexpected HA command"))))
    monkeypatch.setattr(HomeCatalog, "snapshot", lambda self: {"entities": [{"entity_id": "light.a", "domain": "light", "allowed": False, "members": None, "aliases": ["coin lecture"]}]})
    assert home.handle("allume coin lecture")["error"]


def test_alias_works_with_light_noun(tmp_path, monkeypatch):
    calls = []
    def respond(request):
        calls.append(request)
        return httpx.Response(200, json=[])
    HomeAliases(tmp_path).save({"light.bureau": ["bizarre"]})
    home = HomeService(HomeStore(tmp_path, base_url="http://localhost:8123", token="test"), lambda: httpx.Client(transport=httpx.MockTransport(respond)))
    monkeypatch.setattr(HomeCatalog, "snapshot", lambda self: {"entities": [{"entity_id": "light.bureau", "domain": "light", "allowed": True, "members": None, "aliases": ["bizarre"]}]})
    assert home.handle("Allume la lumière bizarre")["scope"] == "entity"
    assert json.loads(calls[-1].content)["entity_id"] == ["light.bureau"]


def test_home_assistant_alias_works_without_local_alias(tmp_path, monkeypatch):
    calls = []
    def respond(request):
        calls.append(request)
        return httpx.Response(200, json=[])
    home = HomeService(HomeStore(tmp_path, base_url="http://localhost:8123", token="test"), lambda: httpx.Client(transport=httpx.MockTransport(respond)))
    entity = {"entity_id": "light.entree", "domain": "light", "allowed": True, "members": None, "aliases": [], "ha_aliases": ["lumière porte d'entrée"]}
    monkeypatch.setattr(HomeCatalog, "snapshot", lambda self: {"entities": [entity]})
    result = home.handle("Allume la lumière porte d'entrée")
    assert result["scope"] == "entity"
    assert json.loads(calls[-1].content)["entity_id"] == ["light.entree"]
    entity["allowed"] = False
    count = len(calls)
    assert home.handle("Allume la lumière porte d'entrée")["error"]
    assert len(calls) == count


def test_helpers_require_explicit_exposure_and_password_state_is_hidden(tmp_path):
    home = HomeService(HomeStore(tmp_path, base_url="http://localhost:8123", token="test"))
    results = [
        {"exposed_entities": {"input_boolean.visible": {"conversation": True}, "input_text.secret": {"conversation": True}}},
        {"expose_new": True},
        [{"entity_id": "input_boolean.visible"}, {"entity_id": "input_boolean.hidden"}, {"entity_id": "input_text.secret"}],
        [], [], [],
        [{"entity_id": "input_boolean.visible", "state": "off", "attributes": {}},
         {"entity_id": "input_boolean.hidden", "state": "off", "attributes": {}},
         {"entity_id": "input_text.secret", "state": "PRIVATE_TEST_VALUE", "attributes": {"mode": "password", "max": 255}}],
        {},
    ]
    responses = [{"id": i, "success": True, "result": value} for i, value in enumerate(results, 1)]
    result = HomeCatalog(home, websocket_factory=lambda uri, **kwargs: FakeSocket(uri, responses)).snapshot()
    assert {x["entity_id"] for x in result["entities"]} == {"input_boolean.visible", "input_text.secret"}
    secret = next(x for x in result["entities"] if x["domain"] == "input_text")
    assert secret["state"] is None
    assert secret["capabilities"] == ["set_value"]
    assert "PRIVATE_TEST_VALUE" not in json.dumps(result)


def test_catalog_reports_native_features_and_vacuum_area_mapping(tmp_path):
    home = HomeService(HomeStore(tmp_path, base_url="http://localhost:8123", token="test"))
    results = [
        {"exposed_entities": {"vacuum.robot": {"conversation": True}, "media_player.tv": {"conversation": True}}},
        {"expose_new": False},
        [{"entity_id": "vacuum.robot"}, {"entity_id": "media_player.tv"}],
        [{"area_id": "living", "name": "Salon"}], [], [],
        [{"entity_id": "vacuum.robot", "state": "docked", "attributes": {"supported_features": 8192 + 16384, "fan_speed_list": ["quiet"]}},
         {"entity_id": "media_player.tv", "state": "idle", "attributes": {"supported_features": 1 + 4, "group_members": ["media_player.tv"], "source_list": ["HDMI"]}}],
        {"vacuum.robot": {"options": {"vacuum": {"area_mapping": {"living": ["17"], "unknown": ["18"], "empty": []}}}}},
    ]
    responses = [{"id": i, "success": True, "result": value} for i, value in enumerate(results, 1)]
    result = HomeCatalog(home, websocket_factory=lambda uri, **kwargs: FakeSocket(uri, responses)).snapshot()
    robot, tv = result["entities"]
    assert robot["cleaning_areas"] == [{"id": "living", "name": "Salon"}]
    assert robot["capabilities"] == ["read", "start", "clean_area"]
    assert tv["capabilities"] == ["read", "media_pause", "volume_set"]
    assert tv["attributes"]["group_members"] == ["media_player.tv"]
