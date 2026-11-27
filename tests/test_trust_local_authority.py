"""Tests du script d'installation de l'autorité locale."""

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("trust_local_authority",
                                              ROOT / "scripts" / "trust_local_authority.py")


def load():
    module = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(module)
    return module


def test_target_and_nickname_are_expected():
    module = load()
    assert module.TARGET.name == "alfred-local-ca.crt"
    assert module.AUTHORITY.name == "ui-ca.crt"
    assert "Alfred" in module.NICKNAME


def test_missing_certutil_still_reports_a_magasin(monkeypatch, tmp_path):
    module = load()
    monkeypatch.setattr(module.shutil, "which", lambda name: None)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    authority = tmp_path / "ui-ca.crt"
    authority.write_text("x")
    message = module.install_nss(authority, tmp_path / "home")
    assert "certutil" in message
    assert "non mis à jour" in message


def test_nss_keeps_private_permissions(monkeypatch, tmp_path):
    module = load()
    calls = []

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr(module.shutil, "which", lambda name: "/usr/bin/certutil")
    monkeypatch.setattr(module.subprocess, "run", lambda command, **options: calls.append(command) or Result())
    authority = tmp_path / "ui-ca.crt"
    authority.write_text("x")
    home = tmp_path / "home"
    assert module.install_nss(authority, home) == "Magasin NSS mis à jour."
    assert (home / ".pki" / "nssdb").is_dir()
    assert (home / ".pki").stat().st_mode & 0o777 == 0o700
    assert calls and calls[0][0] == "/usr/bin/certutil"
    assert f"sql:{home / '.pki' / 'nssdb'}" in calls[0]


def test_present_authority_is_not_added_again(monkeypatch, tmp_path):
    module = load()
    calls = []

    class Listed:
        returncode = 0
        stdout = f"\nCertificate Nickname\n\n{module.NICKNAME}   C,,\n"
        stderr = ""

    class Added:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr(module.shutil, "which", lambda name: "/usr/bin/certutil")
    monkeypatch.setattr(module.subprocess, "run", lambda command, **options: calls.append(command) or Listed())
    authority = tmp_path / "ui-ca.crt"
    authority.write_text("x")
    assert module.install_nss(authority, tmp_path / "home") == "Magasin NSS : autorité déjà présente."
    assert len(calls) == 1 and "-L" in calls[0]


def test_failed_listing_still_attempts_an_add(monkeypatch, tmp_path):
    module = load()
    calls = []

    class Failed:
        returncode = 1
        stdout = ""
        stderr = "erreur"

    monkeypatch.setattr(module.shutil, "which", lambda name: "/usr/bin/certutil")
    monkeypatch.setattr(module.subprocess, "run", lambda command, **options: calls.append(command) or Failed())
    authority = tmp_path / "ui-ca.crt"
    authority.write_text("x")
    message = module.install_nss(authority, tmp_path / "home")
    assert "non mis à jour" in message
    assert any("-A" in call for call in calls)


def test_system_failure_is_reported(monkeypatch, tmp_path):
    module = load()

    def failing(command, **options):
        raise module.subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(module.subprocess, "run", failing)
    authority = tmp_path / "ui-ca.crt"
    authority.write_text("x")
    assert "non mis à jour" in module.install_system(authority, True)


def test_server_certificate_is_refused(monkeypatch, tmp_path, capsys):
    module = load()
    authority = tmp_path / "server.crt"
    authority.write_text("x")
    monkeypatch.setattr(sys, "argv", ["trust", "--authority", str(authority), "--no-system"])
    monkeypatch.setattr(module, "AUTHORITY", authority)
    with pytest.raises(SystemExit):
        module.main()
    assert "ui-ca.crt" in capsys.readouterr().err
