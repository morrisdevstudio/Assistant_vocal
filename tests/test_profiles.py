import sqlite3

import pytest

from alfred.profiles import Profiles, cosine
from alfred.storage import Store

MODEL = "modele-de-test"


def make(tmp_path):
    store = Store(tmp_path)
    store.initialize()
    return Profiles(store)


def test_profile_lifecycle(tmp_path):
    profiles = make(tmp_path)
    created = profiles.create("Camille", "adult")
    assert created["role"] == "adult"
    assert created["samples"] == 0
    assert profiles.get(created["id"])["name"] == "Camille"
    assert [item["id"] for item in profiles.list()] == [created["id"]]
    renamed = profiles.rename(created["id"], "  Camille   B  ")
    assert renamed["name"] == "Camille B"
    assert profiles.rename("inconnu", "X") is None
    assert profiles.delete(created["id"])
    assert not profiles.delete(created["id"])
    assert profiles.list() == []


def test_names_and_roles_are_checked(tmp_path):
    profiles = make(tmp_path)
    profiles.create("Léa", "child")
    with pytest.raises(ValueError):
        profiles.create("Léa", "adult")
    with pytest.raises(ValueError):
        profiles.create("   ", "adult")
    with pytest.raises(ValueError):
        profiles.create("Invité", "guest")
    with pytest.raises(ValueError):
        profiles.create("x" * 41, "adult")


def test_voiceprints_are_averaged_and_identify_the_closest_profile(tmp_path):
    profiles = make(tmp_path)
    camille = profiles.create("Camille")
    hugo = profiles.create("Hugo")
    profiles.add_voiceprint(camille["id"], [1.0, 0.0, 0.0], MODEL, 4.5)
    profiles.add_voiceprint(camille["id"], [0.9, 0.1, 0.0], MODEL, 3.0)
    profiles.add_voiceprint(hugo["id"], [0.0, 1.0, 0.0], MODEL, 5.0)

    centroid = profiles.centroid(camille["id"], MODEL)
    assert centroid[0] == pytest.approx(0.95)
    assert profiles.get(camille["id"])["samples"] == 2

    match = profiles.identify([0.9, 0.1, 0.0], MODEL, 0.8)
    assert match["profile_id"] == camille["id"]
    assert match["score"] > 0.99
    assert profiles.identify([0.9, 0.1, 0.0], MODEL, 0.99)["name"] == "Camille"
    assert profiles.identify([0.0, 0.0, 1.0], MODEL, 0.8) is None
    assert profiles.identify([1.0, 0.0], MODEL, 0.8) is None


def test_voiceprints_require_a_known_profile_and_valid_data(tmp_path):
    profiles = make(tmp_path)
    profile = profiles.create("Camille")
    with pytest.raises(ValueError):
        profiles.add_voiceprint("inconnu", [1.0], MODEL, 3.0)
    with pytest.raises(ValueError):
        profiles.add_voiceprint(profile["id"], [], MODEL, 3.0)
    with pytest.raises(ValueError):
        profiles.add_voiceprint(profile["id"], [1.0], MODEL, 0)
    with pytest.raises(ValueError):
        profiles.add_voiceprint(profile["id"], [float("nan")], MODEL, 3.0)
    with pytest.raises(ValueError):
        profiles.identify([1.0], MODEL, 1.5)
    with pytest.raises(ValueError):
        cosine([1.0], [1.0, 2.0])


def test_deleting_a_profile_removes_its_voiceprints(tmp_path):
    profiles = make(tmp_path)
    profile = profiles.create("Camille")
    profiles.add_voiceprint(profile["id"], [1.0, 2.0], MODEL, 3.0)
    assert profiles.clear_voiceprints("inconnu") == 0
    profiles.delete(profile["id"])
    with profiles.store.connection() as db:
        assert db.execute("SELECT COUNT(*) FROM voiceprints").fetchone()[0] == 0


def test_version_one_database_is_migrated_without_losing_schedules(tmp_path):
    path = tmp_path / "alfred.sqlite3"
    connection = sqlite3.connect(path)
    connection.execute("""CREATE TABLE schedules (
        id TEXT PRIMARY KEY,
        kind TEXT NOT NULL CHECK (kind IN ('timer', 'reminder')),
        title TEXT NOT NULL,
        due_at REAL NOT NULL,
        floor_id TEXT NOT NULL,
        terminal_id TEXT NOT NULL,
        target_room TEXT,
        status TEXT NOT NULL,
        created_at REAL NOT NULL,
        updated_at REAL NOT NULL
    )""")
    connection.execute(
        "INSERT INTO schedules VALUES ('ancien', 'timer', 'Pâtes', 1.0, 'rdc', 'browser-test', NULL, 'pending', 1.0, 1.0)"
    )
    connection.execute("PRAGMA user_version=1")
    connection.commit()
    connection.close()

    store = Store(tmp_path)
    store.initialize()
    with store.connection() as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 6
    assert [item["id"] for item in store.list()] == ["ancien"]
    assert Profiles(store).list() == []


def test_unknown_schema_version_is_refused(tmp_path):
    path = tmp_path / "alfred.sqlite3"
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA user_version=9")
    connection.commit()
    connection.close()
    with pytest.raises(RuntimeError):
        Store(tmp_path).initialize()

