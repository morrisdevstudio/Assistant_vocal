from datetime import datetime, timedelta, timezone

import pytest

from alfred.storage import Store
from alfred.timers import TimerService, duration
from alfred.timers import spoken_duration
from alfred.timer_actions import TimerActions
from alfred.timer_actions import TimerAction, TimerPlan

NOW = datetime(2026, 10, 27, 12, tzinfo=timezone.utc)


@pytest.fixture
def timers(tmp_path):
    store = Store(tmp_path)
    store.initialize()
    return TimerService(store)


@pytest.mark.parametrize("text,seconds", [
    ("huit minutes", 480), ("8 minutes", 480), ("une heure et demie", 5400),
    ("une demi-heure", 1800), ("deux minutes trente secondes", 150),
    ("1 heure et 15 minutes", 4500), ("quatre-vingt-dix secondes", 90),
    ("vingt et une minutes", 1260),
    ("vingt et un minutes", 1260), ("dix-sept secondes", 17),
    ("7min40", 460), ("7 minutes 40", 460), ("sept minutes quarante", 460),
    ("7min60", None),
    ("8 minutes et raconte une blague", None), ("-2 minutes", None),
    ("1 seconde et demie", None), ("deux heures trois heures", None),
])
def test_duration_full_phrase(text, seconds):
    assert duration(text) == seconds


@pytest.mark.parametrize("prefix", ["Alfred", "Jarvis", "Jarvisse"])
def test_creation_persistence_remaining_and_cancel(timers, prefix):
    result = timers.handle(f"{prefix}, mets un minuteur de huit minutes, s’il te plaît.", "rdc", now=NOW)
    assert result["action"] == "create"
    item = result["item"]
    assert datetime.fromisoformat(item["due_at"]) == NOW + timedelta(minutes=8)
    assert item["terminal_id"] == "browser-test"
    assert TimerService(timers.store).handle("liste les minuteurs", "rdc", now=NOW)["items"][0]["id"] == item["id"]
    reply = timers.handle("combien de temps reste-t-il au minuteur ?", "rdc", now=NOW + timedelta(seconds=65))
    assert "6 minutes et 55 secondes" in reply["text"]
    assert timers.handle("annule le minuteur", "rdc", now=NOW)["text"] == "Minuteur annulé."
    assert timers.store.get(item["id"])["status"] == "cancelled"


def test_current_timer_context_without_number_prefers_newest_and_ringing(timers):
    first = timers.handle("mets un minuteur de 10 secondes", "rdc", now=NOW)["item"]
    second = timers.handle("mets un minuteur de 2 minutes", "rdc", now=NOW)["item"]
    result = timers.handle("quel temps reste-t-il sur le minuteur ?", "rdc", now=NOW + timedelta(seconds=5))
    assert result["items"][0]["id"] == second["id"]
    assert "une minute et 55 secondes" in result["text"]
    timers.handle("annule le minuteur", "rdc", now=NOW + timedelta(seconds=5))
    assert timers.store.get(second["id"])["status"] == "cancelled"
    assert timers.store.get(first["id"])["status"] == "pending"

    ringing = timers.handle("mets un minuteur de 1 seconde", "rdc", now=NOW)["item"]
    timers.store.tick(NOW + timedelta(seconds=2))
    result = timers.handle("quel temps reste-t-il sur le minuteur ?", "rdc", now=NOW + timedelta(seconds=2))
    assert result["items"][0]["id"] == ringing["id"] and "sonne" in result["text"]
    assert timers.handle("annule le minuteur", "rdc", now=NOW + timedelta(seconds=2))["action"] == "cancel"
    assert timers.store.get(ringing["id"])["status"] == "cancelled"


@pytest.mark.parametrize("phrase", ["mets une minuterie de 7min40", "mets une minuterie de sept minutes quarante"])
def test_minuterie_alias_and_implicit_seconds(timers, phrase):
    result = timers.handle(phrase, "rdc", now=NOW)
    assert result["action"] == "create"
    assert datetime.fromisoformat(result["item"]["due_at"]) == NOW + timedelta(seconds=460)


def test_floor_and_reminder_isolation_and_ambiguous_cancellation(timers):
    a = timers.handle("mets un minuteur de 10 secondes", "rdc", now=NOW)["item"]
    b = timers.handle("mets un minuteur de 20 secondes", "rdc", now=NOW)["item"]
    c = timers.handle("mets un minuteur de 10 secondes", "etage1", now=NOW)["item"]
    reminder = timers.store.create(kind="reminder", title="test", due_at=NOW + timedelta(seconds=1),
                                   floor_id="rdc", terminal_id="test", now=NOW)
    assert timers.handle("annule le minuteur", "rdc", now=NOW)["action"] == "cancel"
    assert timers.store.get(a["id"])["status"] == "pending"
    items = timers.handle("liste les minuteurs", "rdc", now=NOW)["items"]
    assert len(items) == 1
    number = items[0]["number"]
    timers.handle(f"annule le minuteur {number}", "rdc", now=NOW)
    assert timers.store.get(b["id"])["status"] == "cancelled"
    timers.handle("stop", "rdc", now=NOW + timedelta(seconds=11))
    assert timers.store.get(a["id"])["status"] == "cancelled"
    assert timers.store.get(c["id"])["status"] == "ringing"
    assert timers.store.get(reminder["id"])["status"] == "awaiting_delivery"


def test_stop_preserves_future_timers_and_ids_survive_expiry(timers):
    timers.handle("mets un minuteur de 1 seconde", "rdc", now=NOW)
    future = timers.handle("mets un minuteur de 1 heure", "rdc", now=NOW)["item"]
    before = timers.store.active_timers("rdc")[-1]["number"]
    timers.handle("Stop !", "rdc", now=NOW + timedelta(seconds=2))
    assert timers.store.get(future["id"])["status"] == "pending"
    assert timers.store.active_timers("rdc")[0]["number"] == before
    timers.handle("annule le minuteur deux", "rdc", now=NOW)
    assert timers.store.get(future["id"])["status"] == "cancelled"


@pytest.mark.parametrize("text", ["mets un minuteur de 0 seconde", "mets un minuteur de 169 heures",
    "mets un minuteur de huit minutes et allume la lumière", "annule tous les minuteurs",
    "annule le minuteur et raconte une blague", "mets un minuteur de moins deux minutes"])
def test_no_action_on_invalid_or_mixed_commands(timers, text):
    assert timers.handle(text, "rdc", now=NOW)["action"] == "clarify"
    assert timers.store.list() == []


def test_missing_floor_and_unrelated_dialogue(timers):
    assert timers.handle("mets un minuteur de 8 minutes", None, now=NOW)["action"] == "clarify"
    assert timers.store.list() == []
    assert timers.handle("raconte une blague", "rdc", now=NOW) is None
    assert timers.handle("stop et allume la lumiere", "rdc", now=NOW) is None


def test_lookup_does_not_silently_drop_timers_after_one_hundred(timers):
    for _ in range(101):
        timers.handle("mets un minuteur de 1 minute", "rdc", now=NOW)
    result = timers.handle("liste les minuteurs", "rdc", now=NOW)
    assert len(result["items"]) == 101
    assert "101 minuteurs" in result["text"]
    assert timers.handle("annule le minuteur", "rdc", now=NOW)["action"] == "cancel"


@pytest.mark.parametrize("phrase,seconds", [
    ("mets un minuteur de huit minutes", 480),
    ("lance un minuteur d'une heure", 3600),
    ("dans cinq minutes, mets un minuteur", 300),
    ("rappelle-moi dans cinq minutes avec un minuteur", 300),
    ("programme une minuterie de deux minutes trente", 150),
    ("cree un minuteur pour une demi-heure", 1800),
])
def test_flexible_timer_creation(timers, phrase, seconds):
    result = TimerActions(timers).local(phrase, type("T", (), {"floor": "rdc", "key": ("browser", "test-terminal"), "cancelled": __import__("threading").Event()})())
    assert result and result["status"] == "confirmed"
    item = timers.store.active_timers("rdc")[-1]
    expected_remaining = seconds
    actual_remaining = (datetime.fromisoformat(item["due_at"]) - datetime.now(timezone.utc)).total_seconds()
    assert abs(actual_remaining - expected_remaining) < 3


@pytest.mark.parametrize("phrase,action", [
    ("liste les minuteurs", "list"),
    ("annule le minuteur", "cancel"),
    ("arrete la sonnerie", "stop"),
])
def test_flexible_timer_controls(timers, phrase, action):
    context = type("T", (), {"floor": "rdc", "key": ("browser", "test-terminal"), "cancelled": __import__("threading").Event()})()
    result = TimerActions(timers).local(phrase, context)
    assert result and result["actions"][0]["intent"]["operation"] == action


def test_natural_current_timer_question_uses_the_local_timer_path(timers):
    context = type("T", (), {"floor": "rdc", "key": ("browser", "test-terminal"),
                             "cancelled": __import__("threading").Event()})()
    timers.handle("mets un minuteur de huit minutes", "rdc", now=NOW)
    result = TimerActions(timers).local("quel temps reste-t-il sur le minuteur ?", context)
    assert result["status"] == "confirmed"
    assert result["actions"][0]["intent"]["operation"] == "list"
    assert result["reply"] == "Le minuteur sonne."
    assert "Précisez une durée" not in result["reply"]


def test_timer_plan_rejects_invalid_combinations():
    with pytest.raises(ValueError):
        TimerPlan(actions=[TimerAction(operation="create", seconds=30, number=2)])
    with pytest.raises(ValueError):
        TimerPlan(actions=[TimerAction(operation="list", seconds=2)])
    with pytest.raises(ValueError):
        TimerPlan(actions=[TimerAction(operation="create", seconds=0)])


def test_timer_plan_runs_four_timers_in_order_and_stops_on_interruption(timers):
    turn = type("T", (), {"floor": "rdc", "key": ("browser", "timer-plan"), "cancelled": __import__("threading").Event()})()
    result = TimerActions(timers).run([TimerAction(operation="create", seconds=x) for x in (10, 20, 30, 40)], turn)
    assert result["status"] == "confirmed" and len(result["actions"]) == 4
    assert len(timers.store.active_timers("rdc")) == 4
    turn.cancelled.set()
    interrupted = TimerActions(timers).run([TimerAction(operation="create", seconds=50)], turn)
    assert interrupted["status"] == "cancelled"
    assert len(timers.store.active_timers("rdc")) == 4


def test_timer_requires_floor_and_never_crosses_floor(timers):
    turn = type("T", (), {"floor": None, "key": ("browser", "timer-floor"), "cancelled": __import__("threading").Event()})()
    assert TimerActions(timers).run([TimerAction(operation="create", seconds=60)], turn)["status"] == "clarification"
    assert not timers.store.active_timers("rdc")


def test_timer_negative_duration_and_five_actions_are_refused(timers):
    turn = type("T", (), {"floor": "rdc", "key": ("browser", "timer-limit"), "cancelled": __import__("threading").Event()})()
    with pytest.raises(ValueError): TimerAction(operation="create", seconds=-1)
    with pytest.raises(ValueError): TimerPlan(actions=[TimerAction(operation="create", seconds=10)] * 5)
    assert not timers.store.active_timers("rdc")


def test_negative_timer_is_clarified_without_creating(timers):
    turn = type("T", (), {"floor": "rdc", "key": ("browser", "timer-neg"), "cancelled": __import__("threading").Event()})()
    result = TimerActions(timers).local("ne mets pas de minuteur", turn)
    assert result["status"] == "clarification"
    assert not timers.store.active_timers("rdc")
