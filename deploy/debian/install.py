"""Installer, mettre à jour ou réactiver la version précédente d'Alfred."""

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
from tempfile import TemporaryDirectory


ROOT = Path("/opt/alfred")
RELEASES = ROOT / "releases"
CURRENT = ROOT / "current"
PREVIOUS = ROOT / "previous"
STATE = Path("/var/lib/alfred")
CONFIG = Path("/etc/alfred")
BACKUPS = Path("/var/backups/alfred")
SERVICE = "alfred-home.service"
UNIT = Path("/etc/systemd/system") / SERVICE
RELEASE_ID = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+[A-Za-z0-9.+-]*-[0-9a-f]{12}")


def run(*args, check=True, **kwargs):
    return subprocess.run(args, check=check, **kwargs)


def prepare_host():
    import pwd

    try:
        pwd.getpwnam("alfred")
    except KeyError:
        run("useradd", "--system", "--user-group", "--no-create-home", "--home-dir", STATE,
            "--shell", "/usr/sbin/nologin", "alfred")
    for directory in (STATE, CONFIG):
        directory.mkdir(mode=0o755, parents=True, exist_ok=True)
    for directory in (STATE / "data", STATE / "models", STATE / "https"):
        if not directory.exists():
            directory.mkdir(mode=0o750)
            shutil.chown(directory, user="alfred" if directory.name == "data" else "root", group="alfred")
    BACKUPS.mkdir(mode=0o700, parents=True, exist_ok=True)


def stage_release(bundle):
    release_id = (bundle / "RELEASE").read_text(encoding="ascii").strip()
    if not RELEASE_ID.fullmatch(release_id):
        raise ValueError("Identifiant de version invalide dans RELEASE.")
    target = RELEASES / release_id
    if target.is_symlink():
        raise RuntimeError(f"Répertoire de version attendu : {target}")
    if target.exists():
        marker = target / "RELEASE"
        if marker.is_file() and marker.read_text(encoding="ascii").strip() == release_id:
            return target
        if any(link.is_symlink() and link.resolve() == target for link in (CURRENT, PREVIOUS)):
            raise RuntimeError(f"Version référencée incomplète : {target}")
        shutil.rmtree(target)

    target.mkdir(mode=0o755)
    try:
        for directory in ("alfred", "bin", "pwa"):
            shutil.copytree(bundle / directory, target / directory)
        for filename in ("install.py", "health.py", "alfred.service", "README.md"):
            shutil.copyfile(bundle / filename, target / filename)
        run(sys.executable, "-m", "venv", target / ".venv")
        python = target / ".venv/bin/python"
        run(python, "-m", "pip", "install", "--no-index", "--only-binary=:all:",
            "--find-links", bundle / "wheels", "-c", bundle / "constraints.txt", "-r", bundle / "runtime.txt")
        run(python, "-m", "pip", "check")
        libraries = run("ldd", target / "bin/alfred-murmure-stt", capture_output=True, text=True)
        if "not found" in libraries.stdout:
            raise RuntimeError(f"Bibliothèques manquantes pour Parakeet :\n{libraries.stdout}")
        run("runuser", "-u", "alfred", "--", python, "-B", "-c",
            "import alfred.app, av, onnxruntime, ptts, soundfile, scipy.signal, aioesphomeapi", cwd=target)
        shutil.copyfile(bundle / "RELEASE", target / "RELEASE")
    except BaseException:
        shutil.rmtree(target)
        raise
    return target


def selected(link):
    if not link.is_symlink():
        if link.exists():
            raise RuntimeError(f"Lien de version attendu : {link}")
        return None
    target = link.resolve(strict=True)
    if target.parent != RELEASES or not RELEASE_ID.fullmatch(target.name) or not (target / "RELEASE").is_file():
        raise RuntimeError(f"Version invalide : {target}")
    return target


def point(link, target):
    with TemporaryDirectory(dir=ROOT) as temporary:
        new_link = Path(temporary) / "version"
        new_link.symlink_to(target, target_is_directory=True)
        new_link.replace(link)


def backup_data(release):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = BACKUPS / f"{stamp}-{release.name}.tar.gz"
    with TemporaryDirectory(dir=BACKUPS) as temporary:
        archive = Path(temporary) / backup.name
        with tarfile.open(archive, "w:gz") as output:
            output.add(STATE / "data", arcname="data")
        archive.chmod(0o600)
        archive.replace(backup)
    print(f"Sauvegarde locale : {backup}", flush=True)


def start(release):
    # Toute modification locale du service appartient à un drop-in systemd.
    with TemporaryDirectory(dir=UNIT.parent) as temporary:
        unit = Path(temporary) / UNIT.name
        shutil.copyfile(release / "alfred.service", unit)
        unit.chmod(0o644)
        unit.replace(UNIT)
    run("systemctl", "daemon-reload")
    run("systemctl", "reset-failed", SERVICE, check=False,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    point(CURRENT, release)
    run("systemctl", "start", SERVICE)


def activate(target):
    current = selected(CURRENT)
    has_unit = UNIT.is_file()
    if current == target and has_unit:
        run("systemctl", "start", SERVICE)
        run("systemctl", "enable", SERVICE)
        return
    if current is not None:
        if has_unit:
            run("systemctl", "stop", SERVICE)
        try:
            backup_data(current)
        except BaseException:
            if has_unit:
                run("systemctl", "start", SERVICE)
            raise
    try:
        start(target)
        run("systemctl", "enable", SERVICE)
        if current is not None and current != target:
            point(PREVIOUS, current)
    except BaseException:
        if selected(CURRENT) == target:
            run("systemctl", "stop", SERVICE)
        if current is not None:
            start(current)
            print(f"Version précédente redémarrée : {current.name}", file=sys.stderr)
        else:
            CURRENT.unlink(missing_ok=True)
        raise
    print(f"Alfred actif : {target.name}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rollback", action="store_true", help="réactiver la version précédente")
    parser.add_argument("--apt", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    info = platform.freedesktop_os_release() if sys.platform == "linux" else {}
    if (info.get("ID"), info.get("VERSION_ID"), platform.machine(), sys.version_info[:2]) != (
        "debian", "13", "x86_64", (3, 13),
    ):
        parser.error("Ce paquet cible Debian 13 amd64 avec Python 3.13.")
    if os.geteuid() != 0:
        parser.error("Lancez l'installation avec sudo.")

    import fcntl

    os.umask(0o022)
    RELEASES.mkdir(mode=0o755, parents=True, exist_ok=True)
    with (ROOT / "install.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        legacy = UNIT.with_name("alfred.service")
        if (legacy.is_file() and "WorkingDirectory=/opt/alfred/current\n" in legacy.read_text(encoding="utf-8")
                and run("systemctl", "is-active", "--quiet", legacy.name, check=False).returncode == 0):
            parser.error("Arrêtez et désactivez d’abord l’ancien service alfred.service d’Alfred.")
        prepare_host()
        if args.apt:
            run(sys.executable, "-EsB", Path(__file__).with_name("updater.py"), "provision")
        if args.rollback:
            target = selected(PREVIOUS)
            if target is None:
                parser.error("Aucune version précédente installée.")
        else:
            bundle = Path(__file__).resolve().parent
            target = stage_release(bundle)
        activate(target)


if __name__ == "__main__":
    main()
