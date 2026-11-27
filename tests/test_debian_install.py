import importlib.util
from pathlib import Path
import subprocess
import tarfile

import pytest


INSTALLER_PATH = Path(__file__).resolve().parents[1] / "deploy/debian/install.py"
SPEC = importlib.util.spec_from_file_location("debian_installer", INSTALLER_PATH)
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


@pytest.fixture
def installation(tmp_path, monkeypatch):
    state = tmp_path / "state"
    backups = tmp_path / "backups"
    unit = tmp_path / "alfred.service"
    (state / "data").mkdir(parents=True)
    (state / "data/alfred.sqlite3").write_bytes(b"data")
    backups.mkdir()
    previous = tmp_path / "0.6.0-0123456789ab"
    candidate = tmp_path / "0.6.1-123456789abc"
    for version in (previous, candidate):
        version.mkdir()
        (version / "alfred.service").write_text(version.name, encoding="ascii")
    unit.write_text(previous.name, encoding="ascii")
    monkeypatch.setattr(installer, "STATE", state)
    monkeypatch.setattr(installer, "BACKUPS", backups)
    monkeypatch.setattr(installer, "UNIT", unit)
    links = {installer.CURRENT: previous}
    monkeypatch.setattr(installer, "selected", links.get)
    monkeypatch.setattr(installer, "point", links.__setitem__)
    return previous, candidate, links


def test_update_saves_data_before_start(installation, monkeypatch):
    previous, candidate, links = installation
    events = []

    def systemctl(command, action, *args, **kwargs):
        assert command == "systemctl"
        events.append((action, links[installer.CURRENT]))
        if action == "start":
            backup, = installer.BACKUPS.glob("*.tar.gz")
            with tarfile.open(backup) as archive:
                assert archive.extractfile("data/alfred.sqlite3").read() == b"data"

    monkeypatch.setattr(installer, "run", systemctl)
    installer.activate(candidate)

    assert events[0] == ("stop", previous)
    assert events[-2:] == [("start", candidate), ("enable", candidate)]
    assert links == {installer.CURRENT: candidate, installer.PREVIOUS: previous}


def test_failed_start_reactivates_previous_version_without_overwriting_data(installation, monkeypatch):
    previous, candidate, links = installation
    service_actions = []

    def systemctl(command, action, *args, **kwargs):
        running = links[installer.CURRENT]
        service_actions.append((action, running))
        if action == "start" and running == candidate:
            (installer.STATE / "data/alfred.sqlite3").write_bytes(b"new data")
            raise subprocess.CalledProcessError(1, (command, action, *args))

    monkeypatch.setattr(installer, "run", systemctl)
    with pytest.raises(subprocess.CalledProcessError):
        installer.activate(candidate)

    assert service_actions[-1] == ("start", previous)
    assert ("stop", candidate) in service_actions
    assert installer.UNIT.read_text(encoding="ascii") == previous.name
    assert (installer.STATE / "data/alfred.sqlite3").read_bytes() == b"new data"
    assert links == {installer.CURRENT: previous}
