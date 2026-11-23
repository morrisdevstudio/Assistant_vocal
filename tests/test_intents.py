import copy
import json
import threading
from contextlib import contextmanager
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from alfred.app import create_app
from alfred.config import Settings
from alfred.conversation import ConversationService
from alfred.credentials import CredentialStore
from alfred.diagnostics import Diagnostics
from alfred.home_assistant import HomeService, HomeStore, HomeError
from alfred.home_catalog import HomeCatalog
from alfred.intent_context import CURRENT_TURN, IntentContext
from alfred.intents import IntentService
from alfred.light_actions import LightAction, LightPlan


class Home(HomeService):
    def __init__(self, folder):
        super().__init__(HomeStore(folder, base_url="http://ha.test:8123", token="fake", room="Bureau"))
        attrs = {"supported_color_modes": ["rgb", "color_temp"], "brightness": 128,
                 "min_color_temp_kelvin": 2000, "max_color_temp_kelvin": 6500, "rgb_color": [255, 255, 255]}
        self.states = {"light." + r: {"entity_id": "light."+r, "state": "on", "attributes": copy.deepcopy(attrs)} for r in ("bureau", "salon")}
        self.entries = [{"entity_id": e, "domain": "light", "name": "Lumière " + e.split('.')[1],
                         "area": e.split('.')[1].title(), "allowed": True, "members": None,
                         "aliases": [], "ha_aliases": [], "attributes": s["attributes"]} for e, s in self.states.items()]
        self.calls = []
        self.apply = True
        self.fail = False
        self.after_call = None

    def get_state(self, entity):
        return copy.deepcopy(self.states[entity])

    def call_service(self, domain, service, payload):
        self.calls.append((domain, service, payload))
        if self.fail:
            raise HomeError("Réponse perdue")
        if self.apply:
            for e in payload["entity_id"]:
                self.states[e]["state"] = "off" if service == "turn_off" else "on"
                attrs = self.states[e]["attributes"]
                if "brightness_pct" in payload:
                    attrs["brightness"] = round(payload["brightness_pct"] * 255 / 100)
                for key in ("rgb_color", "color_temp_kelvin"):
                    if key in payload:
                        attrs[key] = payload[key]
        if self.after_call:
            self.after_call()


@pytest.fixture
def rig(tmp_path, monkeypatch):
    home = Home(tmp_path)
    monkeypatch.setattr(HomeCatalog, "snapshot", lambda self: {"entities": copy.deepcopy(home.entries)})
    service = IntentService(home, tmp_path)
    return home, service


@contextmanager
def turn(service, text="Éteins le bureau et le salon", session="session-test-001", speaker="guest", source="browser"):
    t = service.context.begin((source, session, speaker), text, threading.Event(), "rdc")
    token = CURRENT_TURN.set(t)
    try:
        yield t
    finally:
        service.context.finish(t, t.result["reply"] if t.result else "")
        CURRENT_TURN.reset(token)


def action(op="turn_off", target="Bureau", scope="room", value=None):
    return LightAction(operation=op, scope=scope, target=target, value=value)


@pytest.mark.parametrize("phrase,expected", [
    ("Allume la lumière du plan de travail.", ["light.plan_de_travail"]),
    ("Allume la lumière du plan travail.", ["light.plan_de_travail"]),
    ("Allume la lumière de la cuisine.", ["light.plan_de_travail", "light.plafonnier"]),
    ("Tu peux allumer la lumière dans la cuisine ?", ["light.plan_de_travail", "light.plafonnier"]),
    ("Allume les lumières de la cuisine.", ["light.plan_de_travail", "light.plafonnier"]),
    ("Je voudrais un peu de lumière dans la cuisine.", None),
    ("Allume la lumière de la cuisine puis mets de la musique.", None),
    ("N'allume pas la lumière de la cuisine.", None),
    ("Allume la lumière du grenier demain.", None),
    ("Allume la lumière du grenier à huit.", None),
    ("Allume la lumière du grenier en rouge.", None),
])
def test_local_light_on_with_benchmark_transcriptions(rig, phrase, expected):
    home, svc = rig
    for suffix, name in (("plan_de_travail", "Lumière plan de travail"), ("plafonnier", "Plafonnier"),
                         ("ambiance", "Ruban")):
        entity = f"light.{suffix}"
        home.entries.append({"entity_id": entity, "name": name, "area": "Cuisine",
                             "allowed": True, "members": None,
                             "light_type": "secondary" if suffix == "ambiance" else "main"})
        home.states[entity] = {"entity_id": entity, "state": "off", "attributes": {}}
    with turn(svc, phrase, source="esp32") as current:
        result = svc.explicit_light_on(current)
    if expected is None:
        assert result is None
        assert not home.calls
    else:
        assert result["status"] == "confirmed"
        assert sorted(payload["entity_id"][0] for _, _, payload in home.calls) == sorted(expected)


def test_local_light_on_leaves_room_name_collision_to_model(rig):
    home, svc = rig
    home.entries[1]["aliases"] = ["Lumière Bureau"]
    with turn(svc, "Allume la lumière du bureau") as current:
        assert svc.explicit_light_on(current) is None
    assert not home.calls


def test_local_light_on_leaves_omitted_preposition_collision_to_model(rig):
    home, svc = rig
    home.entries[0]["aliases"] = ["Plan travail"]
    home.entries[1]["aliases"] = ["Plan de travail"]
    with turn(svc, "Allume le plan travail") as current:
        assert svc.explicit_light_on(current) is None
    assert not home.calls


@pytest.mark.parametrize("reply", ["Salon", "Le salon", "Dans le salon"])
def test_local_light_on_keeps_order_until_room_answer(rig, reply):
    home, svc = rig
    home.states["light.salon"]["state"] = "off"
    with turn(svc, "Allume la lumière de la fumée", source="esp32") as current:
        result = svc.explicit_light_on(current)
        assert result["status"] == "clarification" and result["reply"] == "Dans quelle pièce ?"
    assert not home.calls
    with turn(svc, reply, source="esp32") as current:
        assert svc.explicit_light_on(current)["status"] == "confirmed"
    assert home.calls == [("light", "turn_on", {"entity_id": ["light.salon"]})]


@pytest.mark.parametrize("interruption", ["cancel", "new_request", "expired", "different_session"])
def test_local_light_on_room_answer_cannot_resume_interrupted_request(rig, interruption):
    home, svc = rig
    now = 10
    svc.context.clock = lambda: now
    home.states["light.salon"]["state"] = "off"
    with turn(svc, "Allume la lumière de la fumée", source="esp32") as current:
        assert svc.explicit_light_on(current)["status"] == "clarification"
    if interruption in {"cancel", "new_request"}:
        phrase = "Annule" if interruption == "cancel" else "Quelle heure est-il ?"
        with turn(svc, phrase, source="esp32") as current:
            result = svc.explicit_light_on(current)
            assert result is None if interruption == "new_request" else result["status"] == "cancelled"
    if interruption == "expired":
        now += 31
    session = "other-test-session" if interruption == "different_session" else "session-test-001"
    with turn(svc, "Salon", source="esp32", session=session) as current:
        assert svc.explicit_light_on(current) is None
    assert not home.calls


def test_local_light_on_honors_confirmation_and_stale_targets(rig, monkeypatch):
    home, svc = rig
    home.entries[0]["confirmation_required"] = True
    home.states["light.bureau"]["state"] = "off"
    with turn(svc, "Allume la lumière du bureau") as current:
        assert svc.explicit_light_on(current)["status"] == "confirmation"
    assert not home.calls

    snapshots = iter(({"entities": copy.deepcopy(home.entries)},
                      {"entities": [dict(home.entries[1], area="Bureau")]}))
    monkeypatch.setattr(HomeCatalog, "snapshot", lambda self: next(snapshots))
    with turn(svc, "Allume la lumière du bureau") as current:
        assert svc.explicit_light_on(current)["status"] == "refused"
    assert not home.calls


def test_local_and_ai_share_same_executor_and_context(rig):
    home, svc = rig
    home.intent_service = svc
    with turn(svc) as t:
        result = home.handle("Éteins toutes les lumières du bureau.")
        assert result["reply"] and t.result["status"] == "confirmed"
    with turn(svc, "rallume-la") as t:
        result = svc.handle_local(t.text, t)
    assert result["status"] == "confirmed"
    assert [x[1] for x in home.calls] == ["turn_off", "turn_on"]
    assert all(x[2]["entity_id"] == ["light.bureau"] for x in home.calls)


@pytest.mark.parametrize("phrase,room,operation,expected", [
    ("Allume les lumières du salon", "Bureau", "turn_on", ["light.salon"]),
    ("Allume les lumières ici", "Salon", "turn_on", ["light.salon"]),
    ("Allume toutes les lumières de la maison", "Bureau", "turn_on", ["light.bureau", "light.salon"]),
    ("Éteins les lumières du salon", "Bureau", "turn_off", ["light.salon", "light.tom"]),
    ("Allume les lumières d’ambiance du salon", "Bureau", "turn_on", ["light.tom"]),
    ("Allume les lumières du salon, y compris l’ambiance", "Bureau", "turn_on", ["light.salon", "light.tom"]),
    ("Allume le Tom", "Bureau", "turn_on", ["light.tom"]),
])
def test_light_categories_direct_and_ai(rig, monkeypatch, phrase, room, operation, expected):
    home, svc = rig
    home.intent_service = svc
    monkeypatch.setattr(home, "room", lambda: room)
    monkeypatch.setattr(svc, "enabled", lambda family="lights": family == "lights")
    home.entries[1]["name"] = "Plafonnier"
    home.entries.append({**home.entries[1], "entity_id": "light.tom", "name": "Tom", "light_type": "secondary"})
    home.states["light.tom"] = {**home.states["light.salon"], "entity_id": "light.tom"}
    for route in ("direct", "ai"):
        for state in home.states.values():
            state["state"] = "off" if operation == "turn_on" else "on"
        home.calls.clear()
        with turn(svc, phrase) as t:
            if route == "direct":
                home.handle(phrase)
            else:
                svc.run_tools([("controler_lumieres", {"actions": [
                    {"operation": operation, "scope": "entity", "target": "Tom"},
                ]})], t.cancelled)
            assert t.result["status"] == "confirmed"
            assert t.result["actions"][0]["targets"] == expected
        assert sorted(entity for _, _, payload in home.calls for entity in payload["entity_id"]) == expected


def test_light_category_inheritance_and_reading(rig):
    home, svc = rig
    home.entries[1]["light_type"] = "main"
    for name in ("tom", "ruban", "coin"):
        home.states["light." + name] = {**home.states["light.salon"], "entity_id": "light." + name}
    leaves = [{**home.entries[1], "entity_id": "light." + name, "name": name, "light_type": None}
              for name in ("tom", "ruban", "coin")]
    home.entries.extend(leaves + [
        {"entity_id": "light.branche", "name": "Branche", "area": "Salon", "allowed": True,
         "light_type": "main", "members": ["light.ruban", "light.coin"]},
        {"entity_id": "light.racine", "name": "Racine", "area": "Salon", "allowed": True,
         "light_type": "secondary", "members": ["light.salon", "light.tom", "light.branche"]},
        {"entity_id": "light.autre", "name": "Autre", "area": "Salon", "allowed": True,
         "light_type": "secondary", "members": ["light.coin"]},
    ])
    catalog = svc.lights.catalog()
    assert svc.lights.resolve(action("turn_on", target="Salon"), catalog) == ["light.ruban", "light.salon"]
    assert svc.lights.resolve(LightAction(operation="turn_on", scope="room", target="Salon", category="ambient"),
                              catalog) == ["light.coin", "light.tom"]
    assert svc.lights.resolve(action("turn_on", target="Racine", scope="entity"), catalog) == [
        "light.coin", "light.ruban", "light.salon", "light.tom"]
    with turn(svc, "Quelles lumières sont allumées ?"):
        result = svc.execute([LightAction(operation="read")])
        assert "tom" in result["reply"].lower()
        assert not home.calls
    home.entries[0]["light_type"] = "secondary"
    home.states["light.bureau"]["state"] = "off"
    with turn(svc, "Allume les lumières du bureau"):
        result = svc.execute([action("turn_on")])
        assert result["status"] == "refused" and "principale" in result["reply"]
        assert not home.calls


@pytest.mark.parametrize("op,value,key,expected", [
    ("brightness", 30, "brightness_pct", 30),
    ("brightness_delta", -10, "brightness_pct", 40),
    ("color", "bleu", "rgb_color", [0, 0, 255]),
    ("temperature", 3000, "color_temp_kelvin", 3000),
])
def test_supported_light_parameters(rig, op, value, key, expected):
    home, svc = rig
    with turn(svc) as t:
        result = svc.execute([action(op, value=value)])
    assert result["status"] == "confirmed"
    assert home.calls[0][2][key] == expected


def test_dimming_an_off_light_does_not_turn_it_on(rig):
    home, svc = rig
    home.states["light.bureau"]["state"] = "off"
    with turn(svc):
        assert svc.execute([action("brightness_delta", value=-10)])["status"] == "confirmed"
    assert home.calls == []


@pytest.mark.parametrize("bad", [action("brightness", value=101), action("color", value="inconnue"),
                                      action("temperature", value=1500), action(target="garage")])
def test_whole_batch_is_prepared_before_first_write(rig, bad):
    home, svc = rig
    with turn(svc):
        result = svc.execute([action(), bad])
    assert result["status"] == "refused"
    assert not home.calls


def test_mixed_capabilities_do_not_partially_apply(rig):
    home, svc = rig
    home.states["light.salon"]["attributes"]["supported_color_modes"] = ["onoff"]
    with turn(svc, "Toutes les lumières de la maison"):
        result = svc.execute([action("brightness", scope="all", value=40)])
    assert result["status"] == "refused" and not home.calls


def test_group_cannot_bypass_excluded_member(rig):
    home, svc = rig
    home.entries[1]["allowed"] = False
    home.entries.append({"entity_id": "light.groupe", "domain": "light", "name": "Groupe", "allowed": True,
                         "members": ["light.bureau", "light.salon"]})
    with turn(svc):
        result = svc.execute([action(scope="entity", target="Groupe")])
    assert result["status"] == "refused" and not home.calls


def test_sensitive_light_asks_once_and_executes_after_yes(rig):
    home, svc = rig
    home.intent_service = svc
    home.entries[0]["confirmation_required"] = True
    with turn(svc, "éteins la lumière du bureau"):
        result = home.handle("éteins la lumière du bureau")
        assert result["status"] == "confirmation"
        assert "Voulez-vous vraiment éteindre Lumière bureau ?" == result["reply"]
        assert not home.calls
    with turn(svc, "oui"):
        result = home.handle("oui")
    assert result["status"] == "confirmed"
    assert [x[2]["entity_id"] for x in home.calls] == [["light.bureau"]]


def test_sensitive_group_or_bulk_command_has_one_question(rig):
    home, svc = rig
    home.intent_service = svc
    home.entries[0]["confirmation_required"] = True
    with turn(svc, "Toutes les lumières"):
        result = svc.execute([action(scope="all", target="")])
        assert result["status"] == "confirmation"
        assert "Lumière bureau" in result["reply"]
        assert not home.calls
    with turn(svc, "oui"):
        result = home.handle("oui")
    assert result["status"] == "confirmed"
    assert len(home.calls) == 2


def hidden_group(rig, *, single=False):
    home, svc = rig
    children = copy.deepcopy(home.entries[:1] if single else home.entries)
    home.entries[:] = [{"entity_id": "light.moodlight", "domain": "light", "name": "Moodlight", "area": "Bureau",
                        "allowed": True, "members": [e["entity_id"] for e in children], "aliases": ["ambiance"]}]
    catalog = {"entities": home.entries, "light_group_members": {e["entity_id"]: e for e in children}, "excluded": []}
    svc.lights.catalog = lambda: copy.deepcopy(catalog)
    return home, svc, catalog


def test_exposed_group_controls_unexposed_members_without_exposing_them(rig):
    home, svc, _ = hidden_group(rig)
    with turn(svc, "Éteins la lumière d'ambiance du bureau"):
        result = svc.execute([action(scope="entity", target="ambiance")])
    assert result["status"] == "confirmed"
    assert {c[2]["entity_id"][0] for c in home.calls} == {"light.bureau", "light.salon"}
    home.calls.clear()
    with turn(svc, "Allume la lampe masquée"):
        result = svc.execute([action("turn_on", scope="entity", target="light.bureau")])
    assert result["status"] == "refused" and not home.calls


def test_room_and_house_include_authorized_group_hidden_members(rig):
    home, svc, _ = hidden_group(rig)
    with turn(svc, "Éteins toutes les lumières du bureau"):
        assert svc.execute([action()])["status"] == "confirmed"
    assert len(home.calls) == 2
    with turn(svc, "Allume toutes les lumières de la maison"):
        assert svc.execute([action("turn_on", scope="all")])["status"] == "confirmed"
    assert len(home.calls) == 4


@pytest.mark.parametrize("states, expected", [
    (("off", "off"), "Toutes les lumières sont éteintes."),
    (("on", "off"), "Il reste une lumière allumée, Lumière bureau."),
    (("on", "on"), "Les lumières encore allumées sont Lumière bureau et Lumière salon."),
    (("on", "unavailable"), "Il reste une lumière allumée, Lumière bureau. L'état de certaines lumières reste indisponible."),
    (("off", "unknown"), "Je ne peux pas confirmer que toutes les lumières sont éteintes. Certains états sont indisponibles."),
])
def test_light_status_without_location_summarizes_the_house(rig, monkeypatch, states, expected):
    home, svc, _ = hidden_group(rig)
    monkeypatch.setattr(svc, "enabled", lambda family="lights": family == "lights")
    for state, reading in zip(home.states.values(), states):
        state["state"] = reading
    with turn(svc, "Dis moi si j'ai oublié d'éteindre des lumières") as t:
        reply = svc.run_tools([("controler_lumieres", {"actions": [{"operation": "read"}]})], t.cancelled)
    assert reply == expected
    assert t.result["actions"][0]["targets"] == ["light.bureau", "light.salon"]
    assert home.calls == []


@pytest.mark.parametrize("phrase, scope, target, lamps", [
    ("Combien de lumières sont allumées ici ?", "current", "", ["light.bureau"]),
    ("Quelles lumières sont allumées au salon ?", "room", "Salon", ["light.salon"]),
    ("Quelles lumières sont allumées ici ?", "all", "", None),
    ("Quelles lumières sont allumées au salon ?", "all", "", None),
    ("Toute la maison", "all", "", ["light.bureau", "light.salon"]),
])
def test_light_status_respects_requested_location(rig, phrase, scope, target, lamps):
    home, svc = rig
    with turn(svc, phrase):
        result = svc.execute([action("read", scope=scope, target=target)])
    if lamps is None:
        assert result["status"] == "refused"
    else:
        assert result["status"] == "confirmed"
        assert result["actions"][0]["targets"] == lamps
    assert home.calls == []


def test_light_write_still_requires_explicit_house_scope(rig):
    home, svc = rig
    with turn(svc, "Éteins les lumières"):
        result = svc.execute([action(scope="all")])
    assert result["status"] == "refused"
    assert home.calls == []


@pytest.mark.parametrize("excluded", ["light.bureau", "light.moodlight"])
def test_exposed_group_never_bypasses_explicit_exclusions(rig, excluded):
    home, svc, catalog = hidden_group(rig)
    catalog["excluded"] = [excluded]
    with turn(svc):
        result = svc.execute([action(scope="entity", target="ambiance")])
    assert result["status"] == "refused" and not home.calls


def test_single_hidden_member_reference_preserves_group_authority(rig):
    home, svc, _ = hidden_group(rig, single=True)
    with turn(svc):
        assert svc.execute([action(scope="entity", target="ambiance")])["status"] == "confirmed"
    with turn(svc, "rallume-la") as t:
        assert svc.handle_local(t.text, t)["status"] == "confirmed"
    assert [c[1] for c in home.calls] == ["turn_off", "turn_on"]


def test_hidden_group_cannot_replace_a_different_explicit_room(rig):
    home, svc, _ = hidden_group(rig)
    # Une autre cible exposée rend le nom de cette pièce observable au résolveur.
    home.entries.append({"entity_id": "light.other", "domain": "light", "name": "Autre", "area": "Cuisine", "allowed": True, "members": None})
    with turn(svc, "Éteins la lumière de la cuisine"):
        result = svc.execute([action(scope="entity", target="ambiance")])
    assert result["status"] == "refused" and not home.calls


def test_nested_hidden_group_controls_and_deduplicates_members(rig):
    home, svc, catalog = hidden_group(rig)
    private = catalog["light_group_members"]
    private["light.nested"] = {"entity_id": "light.nested", "allowed": True, "members": ["light.bureau", "light.salon"]}
    home.entries[0]["members"] = ["light.nested", "light.bureau"]
    with turn(svc):
        assert svc.execute([action(scope="entity", target="ambiance")])["status"] == "confirmed"
    assert len(home.calls) == 2


def test_group_waits_for_delayed_state_without_resending(rig):
    home, svc, _ = hidden_group(rig)
    original_read = home.get_state
    stale_reads = 0

    def read(entity):
        nonlocal stale_reads
        state = original_read(entity)
        if home.calls and entity in home.calls[0][2]["entity_id"] and stale_reads < 3:
            stale_reads += 1
            state["state"] = "on"
        return state

    home.get_state = read
    with turn(svc):
        assert svc.execute([action(scope="entity", target="ambiance")])["status"] == "confirmed"
    assert len(home.calls) == 2


@pytest.mark.parametrize("broken", ["missing", "cycle", "excluded_nested"])
def test_hidden_nested_groups_are_validated_before_any_action(rig, broken):
    home, svc, catalog = hidden_group(rig)
    private = catalog["light_group_members"]
    private["light.nested"] = {"entity_id": "light.nested", "allowed": True, "members": ["light.bureau", "light.salon"]}
    home.entries[0]["members"] = ["light.nested"]
    if broken == "missing":
        private["light.nested"]["members"].append("light.unknown")
    elif broken == "cycle":
        private["light.nested"]["members"].append("light.moodlight")
    else:
        catalog["excluded"] = ["light.nested"]
    with turn(svc):
        assert svc.execute([action(scope="entity", target="ambiance")])["status"] == "refused"
    assert not home.calls


def test_explicit_room_never_expands_to_house(rig):
    home, svc = rig
    with turn(svc, "Éteins toutes les lumières du bureau"):
        result = svc.execute([action(scope="all")])
    assert result["status"] == "refused" and not home.calls


def test_uncertain_dispatch_stops_batch_without_retry(rig):
    home, svc = rig
    home.fail = True
    with turn(svc):
        result = svc.execute([action(), action(target="Salon")])
    assert result["status"] == "unconfirmed" and len(home.calls) == 1


def test_unconfirmed_state_stops_batch(rig):
    home, svc = rig
    home.apply = False
    with turn(svc):
        result = svc.execute([action(), action(target="Salon")])
    assert result["status"] == "unconfirmed" and len(home.calls) == 1


def test_cancellation_between_actions(rig):
    home, svc = rig
    with turn(svc) as t:
        home.after_call = t.cancelled.set
        result = svc.execute([action(), action(target="Salon")])
    assert result["status"] == "partial" and len(home.calls) == 1


def test_permissions_rechecked_between_actions(rig):
    home, svc = rig
    home.after_call = lambda: home.entries[1].update(allowed=False)
    with turn(svc):
        result = svc.execute([action(), action(target="Salon")])
    assert result["status"] == "partial" and len(home.calls) == 1


def test_implicit_proposal_and_yes(rig):
    home, svc = rig
    home.states["light.bureau"]["state"] = "off"
    with turn(svc, "On n'y voit rien ici"):
        result = svc.execute([action("turn_on", scope="current")], propose=True, question="J'allume ici ?")
    assert result["status"] == "clarification" and not home.calls
    with turn(svc, "oui") as t:
        result = svc.handle_local(t.text, t)
    assert result["status"] == "confirmed" and len(home.calls) == 1


def test_proposal_expiration_and_session_isolation(rig):
    home, svc = rig
    clock = [0.]
    svc.context = IntentContext(clock=lambda: clock[0])
    with turn(svc):
        svc.execute([action()], propose=True)
    with turn(svc, "oui", session="another-session") as t:
        assert svc.handle_local(t.text, t)["status"] == "clarification"
    clock[0] = 31
    with turn(svc, "oui") as t:
        assert svc.handle_local(t.text, t)["status"] == "clarification"
    assert not home.calls


def test_new_request_cancels_pending_proposal(rig):
    home, svc = rig
    with turn(svc):
        svc.execute([action()], propose=True)
    with turn(svc, "bonjour") as t:
        svc.handle_local(t.text, t)
    with turn(svc, "oui") as t:
        assert svc.handle_local(t.text, t)["status"] == "clarification"
    assert not home.calls


def test_reference_isolation_and_context_expiration(rig):
    home, svc = rig
    now = [0.]
    svc.context = IntentContext(clock=lambda: now[0])
    with turn(svc):
        svc.execute([action()])
    for extra in ({"speaker": "other"}, {"source": "esp32"}):
        with turn(svc, "rallume-la", **extra) as t:
            assert svc.handle_local(t.text, t)["status"] == "refused"
    now[0] = 301
    with turn(svc, "rallume-la") as t:
        assert svc.handle_local(t.text, t)["status"] == "refused"
    assert len(home.calls) == 1


def test_correction_and_same_action_other_room(rig):
    home, svc = rig
    with turn(svc):
        svc.execute([action("brightness", value=30)])
    with turn(svc, "non cinquante pour cent") as t:
        assert svc.handle_local(t.text, t)["status"] == "confirmed"
    with turn(svc, "pareil dans le salon") as t:
        assert svc.handle_local(t.text, t)["status"] == "confirmed"
    assert home.calls[-1][2] == {"entity_id": ["light.salon"], "brightness_pct": 50}


def test_fifth_action_rejected():
    with pytest.raises(ValueError):
        LightPlan(actions=[action()] * 5)


class Speech:
    def status(self): return {"ready": True}
    def speak(self, text): return b"wav", 1


def test_room_clarification_and_answer_use_conversation_api(rig, tmp_path):
    home, _ = rig
    home.states["light.salon"]["state"] = "off"

    def respond(request):
        pytest.fail("La clarification précise doit rester locale.")

    engine = ConversationService(CredentialStore(tmp_path, api_key="fake-key-for-test"),
                                 lambda: httpx.Client(transport=httpx.MockTransport(respond)))
    app = create_app(Settings(tmp_path), voice_service=Speech(), conversation_service=engine,
                     home_service=home)
    with TestClient(app) as client:
        def say(phrase):
            response = client.post("/api/conversation/text", json={
                "text": phrase, "session_id": "clarification-room-session"})
            return json.loads(response.text.splitlines()[-1])

        question = say("Allume la lumière de la fumée.")
        assert question["text"] == "Dans quelle pièce ?" and question["needs_reply"]
        assert question["execution"]["status"] == "clarification"
        assert not home.calls
        done = say("Dans le salon.")
        assert done["execution"]["status"] == "confirmed" and not done["needs_reply"]
        assert home.calls == [("light", "turn_on", {"entity_id": ["light.salon"]})]


def sse_tool(arguments):
    event = {"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {"name": "controler_lumieres", "arguments": json.dumps(arguments)}}]}, "finish_reason": "tool_calls"}]}
    return "data: " + json.dumps(event) + "\n\ndata: [DONE]\n\n"


def test_real_connector_mock_provider_to_executor_and_journal(rig, tmp_path):
    home, _ = rig
    bodies = []
    def respond(request):
        bodies.append(json.loads(request.content))
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=sse_tool({"actions": [action().model_dump()]}))
    engine = ConversationService(CredentialStore(tmp_path, api_key="fake-key-for-test"), lambda: httpx.Client(transport=httpx.MockTransport(respond)))
    with TestClient(create_app(Settings(tmp_path), voice_service=Speech(), conversation_service=engine, home_service=home)) as client:
        response = client.post("/api/conversation/text", json={"text": "Fais le noir dans le bureau", "session_id": "test-intent-session-001"})
        events = [json.loads(x) for x in response.text.splitlines()]
        assert events[-1]["type"] == "done" and events[-1]["mode"] == "conversation"
        assert home.states["light.bureau"]["state"] == "off" and len(home.calls) == 1
        tools = [x["function"]["name"] for x in bodies[0]["tools"]]
        assert "controler_lumieres" in tools
        assert "Ne dis pas que les lumières" not in bodies[0]["messages"][0]["content"]
        rows = client.app.state.diagnostics.list()
        assert rows[0]["result"]["status"] == "confirmed" and rows[0]["route"] == "ai"
        assert "fake-key-for-test" not in json.dumps(rows)
        history = client.get("/api/diagnostics")
        assert history.status_code == 200
        assert history.json()[0]["result"]["status"] == "confirmed"
        assert "fake-key-for-test" not in history.text


def test_global_light_off_and_lamp_clarification_through_conversation(rig, tmp_path):
    home, _ = rig
    home.states["light.moodlight"] = {"entity_id": "light.moodlight", "state": "on", "attributes": {}}
    home.entries.append({"entity_id": "light.moodlight", "name": "Moodlight", "area": "Bureau",
                         "allowed": True, "members": None})

    def respond(request):
        pytest.fail("Une extinction globale explicite ou son choix de lampe doit être traité localement.")

    engine = ConversationService(CredentialStore(tmp_path, api_key="fake-key-for-test"),
                                 lambda: httpx.Client(transport=httpx.MockTransport(respond)))
    with TestClient(create_app(Settings(tmp_path), voice_service=Speech(),
                               conversation_service=engine, home_service=home)) as client:
        def say(phrase, *, needs_reply=False):
            response = client.post("/api/conversation/text", json={
                "text": phrase, "session_id": "global-lights-test-session"})
            event = json.loads(response.text.splitlines()[-1])
            assert event["type"] == "done"
            assert "pièce ou toute la maison" not in event["text"]
            assert event["needs_reply"] is needs_reply
            return event["text"]

        question = say("Tu peux éteindre toutes les lumières sauf celle du plafonnier du bureau.", needs_reply=True)
        assert "Quelle lampe" in question and "Moodlight" in question and "Lumière bureau" in question
        assert not home.calls
        say("la lumière bureau")
        assert home.calls == [("light", "turn_off", {"entity_id": [entity]})
                              for entity in ("light.moodlight", "light.salon")]
        assert home.states["light.bureau"]["state"] == "on"
        say("Éteins toutes les lumière")
        assert home.calls[-1] == ("light", "turn_off", {"entity_id": ["light.bureau"]})
        assert all(item["state"] == "off" for item in home.states.values())


@pytest.mark.parametrize("interrupt", ["annule", "mets un minuteur", "expire", "autre session"])
def test_lamp_choice_does_not_execute_after_end_of_clarification(rig, interrupt):
    home, svc = rig
    now = 0
    svc.context.clock = lambda: now
    with turn(svc, "Éteins toutes les lumières sauf le plafonnier du bureau", source="esp32") as t:
        assert svc.global_light_off(t)["status"] == "clarification"
    if interrupt == "expire":
        now = 31
    elif interrupt != "autre session":
        with turn(svc, interrupt, source="esp32") as t:
            result = svc.global_light_off(t)
            assert result is None if interrupt != "annule" else result["status"] == "cancelled"
    session = "other-esp32-session" if interrupt == "autre session" else "session-test-001"
    with turn(svc, "la lumière bureau", source="esp32", session=session) as t:
        assert svc.global_light_off(t) is None
    assert not home.calls


def test_room_named_before_light_exception_cannot_become_global(rig):
    home, svc = rig
    with turn(svc, "Éteins toutes les lumières du bureau sauf Lumière Bureau") as t:
        assert svc.global_light_off(t) is None
        result = svc.execute([LightAction(operation="turn_off", scope="all",
                                          exclude_entities=["Lumière Bureau"])], turn=t)
    assert result["status"] == "refused"
    assert not home.calls


@pytest.mark.parametrize("target,state,status", [("Bureau", "21.5", "confirmed"),
    ("Salon", "21.5", "clarification"), ("Bureau", "unavailable", "clarification")])
def test_temperature_tool_reaches_executor_through_conversation(rig, tmp_path, target, state, status):
    home, _ = rig
    attrs = {"device_class": "temperature", "unit_of_measurement": "°C"}
    home.states["sensor.bureau"] = {"entity_id": "sensor.bureau", "state": state,
                                    "attributes": attrs.copy()}
    home.entries.append({"entity_id": "sensor.bureau", "domain": "sensor", "name": "Sonde bureau",
                         "area": "Bureau", "allowed": True, "members": None,
                         "aliases": [], "ha_aliases": [], "attributes": attrs})
    bodies = []
    event = {"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {
        "name": "lire_temperature", "arguments": json.dumps({"target": target})}}]},
        "finish_reason": "tool_calls"}]}
    stream = "data: " + json.dumps(event) + "\n\ndata: [DONE]\n\n"
    def respond(request):
        bodies.append(json.loads(request.content))
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=stream)
    engine = ConversationService(CredentialStore(tmp_path, api_key="fake-key-for-test"),
                                 lambda: httpx.Client(transport=httpx.MockTransport(respond)))
    with TestClient(create_app(Settings(tmp_path), voice_service=Speech(),
                               conversation_service=engine, home_service=home)) as client:
        response = client.post("/api/conversation/text", json={
            "text": "Quelle température fait-il au bureau ?", "session_id": "temperature-tool-session"})
        events = [json.loads(x) for x in response.text.splitlines()]
        assert events[-1]["type"] == "done" and events[-1]["mode"] == "conversation"
        assert events[-1]["execution"]["status"] == status
        if status == "confirmed":
            assert "vingt et un virgule cinq" in events[-1]["text"]
        else:
            assert events[-1]["execution"]["actions"] == []
        assert "lire_temperature" in {x["function"]["name"] for x in bodies[0]["tools"]}
        assert "Pour toute question sur la température actuelle" in bodies[0]["messages"][0]["content"]
        assert "sensor.bureau" in bodies[0]["messages"][0]["content"]
    assert not home.calls


def test_semantic_relay_can_be_disabled(rig, tmp_path):
    home, svc = rig
    (tmp_path / "intent-settings.json").write_text('{"lights":false}', encoding="utf-8")
    with turn(svc) as current:
        system, tools = svc.system_context()
        assert system == ""
        assert [tool["function"]["name"] for tool in tools] == ["preciser_demande"]
        question = "Quelle pièce souhaitez-vous commander ?"
        assert svc.run_tools([("preciser_demande", {"question": question})], current.cancelled) == question
        assert current.result["status"] == "clarification"
        assert not home.calls


def test_diagnostics_retention_annotation_export_and_scrub(tmp_path):
    clock = [0.]
    journal = Diagnostics(tmp_path, clock=lambda: clock[0], max_bytes=128*1024)
    identifier = journal.append({"answer": "Bearer top-secret", "audio_base64": "discard", "api_key": "secret"})
    journal.annotate(identifier, "cible", "Erreur de pièce")
    row = journal.list()[0]
    assert row["annotation"] == "cible" and row["note"] == "Erreur de pièce"
    assert "top-secret" not in json.dumps(row) and "audio_base64" not in row
    for n in range(80):
        journal.append({"answer": str(n)*300})
    assert journal.path.stat().st_size <= journal.max_bytes
    clock[0] = 7*86400+1
    assert journal.list() == []


@pytest.mark.parametrize("wrong", [action(scope="current"), action(scope="entity", target="light.bureau")])
def test_named_room_cannot_be_replaced_by_current_or_wrong_entity(rig, wrong):
    home, svc = rig
    with turn(svc, "Éteins le salon"):
        result = svc.execute([wrong])
    assert result["status"] == "refused" and not home.calls


def test_compound_sentence_does_not_execute_a_local_prefix(rig):
    from alfred.home_assistant import parse_light_command
    assert parse_light_command("Éteins les lumières du bureau et allume celles du salon") is None


def test_new_family_tools_are_staged_and_can_be_enabled(rig, tmp_path):
    from alfred.storage import Store
    from alfred.timers import TimerService
    home, svc = rig
    store = Store(tmp_path)
    store.initialize()
    svc.timers = TimerService(store)
    assert svc.enabled("timers") and not svc.enabled("devices")
    (tmp_path / "intent-settings.json").write_text('{"timers":true}', encoding="utf-8")
    with turn(svc, "Préviens-moi dans trois minutes") as t:
        reply = svc.run_tools([("gerer_minuteur", {"operation": "create", "seconds": 180})], t.cancelled)
        assert "lancé" in reply
        assert t.result["status"] == "confirmed"
        assert len(store.active_timers("rdc")) == 1
    assert not home.calls


def test_disabled_family_is_enforced_server_side(rig):
    _, svc = rig
    (svc.directory / "intent-settings.json").write_text('{"timers":false}', encoding="utf-8")
    with turn(svc) as t:
        with pytest.raises(HomeError):
            svc.run_tools([("gerer_minuteur", {"operation": "create", "seconds": 180})], t.cancelled)


def test_corpus_has_500_cases_and_disjoint_template_holdout():
    from alfred.intent_benchmark import corpus
    cases = corpus()
    assert len(cases) == 500 and len({c["id"] for c in cases}) == 500
    dev = {c["template"] for c in cases if c["split"] == "development"}
    held = {c["template"] for c in cases if c["split"] == "holdout"}
    assert not dev & held
    assert sum(c["split"] == "holdout" for c in cases) == 100


def test_diagnostic_token_counters_are_not_secrets(tmp_path):
    d = Diagnostics(tmp_path)
    d.append({"usage": {"prompt_tokens": 123, "completion_tokens": 45}, "token": "secret"})
    row = d.list()[0]
    assert row["usage"]["prompt_tokens"] == 123
    assert row["token"] == "[secret masqué]"


def test_timer_local_and_ai_share_executor_and_are_enabled(rig, tmp_path):
    from alfred.storage import Store
    from alfred.timers import TimerService
    home, svc = rig
    store = Store(tmp_path); store.initialize(); svc.timers = TimerService(store)
    with turn(svc, "mets un minuteur de huit minutes") as t:
        result = svc.handle_local(t.text, t)
        assert result["status"] == "confirmed" and result["mode"] == "timer"
    assert len(store.active_timers("rdc")) == 1
    with turn(svc, "prépare un minuteur de cinq minutes") as t:
        svc.run_tools([("controler_minuteurs", {"actions": [{"operation": "create", "seconds": 300}]})], t.cancelled)
        assert t.result["status"] == "confirmed"
    assert len(store.active_timers("rdc")) == 2 and not home.calls


@pytest.mark.parametrize("phrase", [
    "prévois un minuteur pour la cuisson pendant sept minutes",
    "où en est mon minuteur de cuisson",
    "supprime le minuteur que je viens de lancer",
])
def test_unrecognised_timer_wording_reaches_semantic_tools_without_action(rig, phrase):
    from alfred.storage import Store
    from alfred.timers import TimerService
    home, svc = rig
    store = Store(svc.directory); store.initialize(); svc.timers = TimerService(store)
    with turn(svc, phrase) as t:
        assert svc.handle_local(t.text, t) is None
        assert store.active_timers("rdc") == []
        assert not home.calls
        _, offered = svc.system_context()
        assert "controler_minuteurs" in {x["function"]["name"] for x in offered}


def test_semantic_remaining_tool_selects_current_timer(rig):
    from alfred.storage import Store
    from alfred.timers import TimerService
    _, svc = rig
    store = Store(svc.directory); store.initialize(); svc.timers = TimerService(store)
    svc.timers.handle("mets un minuteur de huit minutes", "rdc")
    svc.timers.handle("mets un minuteur de deux minutes", "rdc")
    with turn(svc, "où en est mon minuteur de cuisson") as t:
        svc.run_tools([("controler_minuteurs", {"actions": [{"operation": "remaining"}]})], t.cancelled)
        assert t.result["reply"] == "Il reste 2 minutes."
    assert len(store.active_timers("rdc")) == 2


def test_llm_light_exceptions_preserve_rooms_and_skip_already_off(rig):
    home, svc = rig
    for name, state in (("cuisine", "on"), ("couloir", "off")):
        home.states["light." + name] = {"entity_id": "light." + name, "state": state, "attributes": {}}
        home.entries.append({"entity_id": "light." + name, "name": name, "area": name.title(),
                             "allowed": True, "members": None})
    with turn(svc, "Éteins toutes les lumières sauf celles du bureau et du salon") as t:
        svc.run_tools([("controler_lumieres", {"actions": [{"operation": "turn_off", "scope": "all",
                        "exclude_rooms": ["Bureau", "Salon"]}]})], t.cancelled)
        assert t.result["status"] == "confirmed"
    assert home.calls == [("light", "turn_off", {"entity_id": ["light.cuisine"]})]
    assert home.states["light.bureau"]["state"] == home.states["light.salon"]["state"] == "on"
    assert home.states["light.couloir"]["state"] == "off"


@pytest.mark.parametrize("excluded", [[], ["Bureau"], ["Bureau", "Salon", "Pièce inconnue"]])
def test_missing_or_unknown_light_exception_never_executes(rig, excluded):
    home, svc = rig
    with turn(svc, "Éteins toutes les lumières sauf celles du bureau et du salon") as t:
        result = svc.execute([LightAction(operation="turn_off", scope="all", exclude_rooms=excluded)], turn=t)
        assert result["status"] == "refused"
    assert not home.calls


def test_excluded_room_stays_protected_through_cross_room_group(rig):
    home, svc = rig
    home.entries.append({"entity_id": "light.groupe", "name": "Groupe maison", "area": "Entrée",
                         "allowed": True, "members": ["light.bureau", "light.salon"]})
    with turn(svc, "Éteins toutes les lumières sauf celles du bureau") as t:
        result = svc.execute([LightAction(operation="turn_off", scope="all", exclude_rooms=["Bureau"])], turn=t)
        assert result["status"] == "confirmed"
    assert home.calls == [("light", "turn_off", {"entity_id": ["light.salon"]})]


def test_lamp_alias_can_be_excluded_from_whole_house(rig):
    home, svc = rig
    home.entries[0]["aliases"] = ["lampe de travail"]
    with turn(svc, "Éteins toutes les lumières sauf la lampe de travail") as t:
        result = svc.execute([LightAction(operation="turn_off", scope="all",
                                         exclude_entities=["lampe de travail"])], turn=t)
        assert result["status"] == "confirmed"
    assert home.calls == [("light", "turn_off", {"entity_id": ["light.salon"]})]


def test_timer_ai_tool_is_offered_and_disabled_relay_is_refused(rig):
    from alfred.storage import Store
    from alfred.timers import TimerService
    _, svc = rig
    store = Store(svc.directory); store.initialize(); svc.timers = TimerService(store)
    with turn(svc, "mets un minuteur de quatre minutes") as t:
        _, tools = svc.system_context()
        assert "controler_minuteurs" in {x["function"]["name"] for x in tools}
    (svc.directory / "intent-settings.json").write_text('{"timers":false}', encoding="utf-8")
    with turn(svc) as t:
        with pytest.raises(HomeError):
            svc.run_tools([("controler_minuteurs", {"actions": [{"operation": "list"}]})], t.cancelled)


def test_temperature_tool_is_offered_read_only_and_independent_from_device_family(rig):
    home, svc = rig
    attrs = {"device_class": "temperature", "unit_of_measurement": "°C"}
    home.states["sensor.bureau"] = {"entity_id": "sensor.bureau", "state": "21.5", "attributes": attrs.copy()}
    home.entries.append({"entity_id": "sensor.bureau", "domain": "sensor", "name": "Sonde bureau",
                         "area": "Bureau", "allowed": True, "members": None,
                         "aliases": [], "ha_aliases": [], "attributes": attrs})
    with turn(svc, "quelle température fait-il au bureau") as t:
        _, tools = svc.system_context()
        assert "lire_temperature" in {x["function"]["name"] for x in tools}
        assert not svc.enabled("devices")
        reply = svc.run_tools([("lire_temperature", {"target": "bureau"})], t.cancelled)
        assert "vingt et un virgule cinq" in reply
        assert t.result["status"] == "confirmed"
    assert not home.calls


def test_temperature_tool_refuses_unknown_room(rig):
    _, svc = rig
    with turn(svc, "quelle température dans la chambre inconnue") as t:
        reply = svc.run_tools([("lire_temperature", {"target": "chambre inconnue"})], t.cancelled)
        assert "Je ne trouve pas de mesure de température" in reply
        assert t.result["status"] == "clarification"
        assert t.result["actions"] == []
