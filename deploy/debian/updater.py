"""Exécuter les mises à jour du paquet alfred-home sous systemd."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
from tempfile import NamedTemporaryFile, TemporaryDirectory

from alfred.updates import UpdateQueue, UpdatesBusy


QUEUE = UpdateQueue()
SOURCE = Path("/etc/apt/sources.list.d/alfred-home.sources")
LISTS = Path("/var/cache/alfred-updater/lists")
PACKAGE = "alfred-home"
SCOPE = ("-o", f"Dir::Etc::sourcelist={SOURCE}", "-o", "Dir::Etc::sourceparts=-",
         "-o", f"Dir::State::lists={LISTS}", "-o", "Dir::Cache::pkgcache=", "-o", "Dir::Cache::srcpkgcache=")


def run(program, *args, **kwargs):
    return subprocess.run((f"/usr/bin/{program}", *args), check=True, text=True,
                          env={**os.environ, "LC_ALL": "C", "DEBIAN_FRONTEND": "noninteractive"}, **kwargs)


def save(result):
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=QUEUE.directory, delete=False) as output:
        path = Path(output.name)
        try:
            json.dump(result, output, ensure_ascii=False)
            output.close()
            shutil.chown(path, user="root", group="alfred")
            path.chmod(0o640)
            path.replace(QUEUE.result)
        finally:
            path.unlink(missing_ok=True)


def installed_version():
    return run("dpkg-query", "-W", "-f=${Version}", PACKAGE, capture_output=True).stdout.strip()


def provision():
    for directory, mode in ((QUEUE.directory, 0o750), (QUEUE.requests, 0o770)):
        directory.mkdir(mode=mode, exist_ok=True)
        shutil.chown(directory, user="root", group="alfred")
        directory.chmod(mode)
    LISTS.mkdir(mode=0o755, parents=True, exist_ok=True)
    LISTS.parent.chmod(0o755)
    LISTS.chmod(0o755)
    lock = QUEUE.directory / "operation.lock"
    lock.touch()
    # flock() accède au fichier en lecture seule depuis le service Alfred.
    for path, content in ((lock, None), (QUEUE.key, secrets.token_urlsafe(32) + "\n")):
        if content is not None:
            try:
                with path.open("x", encoding="ascii") as output:
                    output.write(content)
            except FileExistsError:
                pass
        shutil.chown(path, user="root", group="alfred")
        path.chmod(0o640)


def record_installed():
    # Lors d'une mise à jour intégrée, le parent APT conserve ce verrou.
    try:
        with QUEUE.lock():
            result = QUEUE.read_result()
            version = installed_version()
            if result.get("installed") != version:
                save({"installed": version, "phase": "idle"})
    except UpdatesBusy:
        pass


def candidate_version():
    if not SOURCE.is_file():
        raise RuntimeError("Source APT Alfred absente dans /etc/apt/sources.list.d/alfred-home.sources.")
    run("apt-get", *SCOPE, "--error-on=any", "update")
    lines = run("apt-cache", *SCOPE, "policy", PACKAGE, capture_output=True).stdout.splitlines()
    candidate = next((line.split(maxsplit=1)[1] for line in lines if line.startswith("  Candidate: ")), None)
    if not candidate or candidate == "(none)":
        raise RuntimeError("Aucune version APT candidate pour Alfred.")
    return candidate


def install_version(version):
    with TemporaryDirectory(prefix="alfred-update-") as directory:
        # Seul l'utilisateur de téléchargement d'APT peut écrire dans ce dossier.
        shutil.chown(directory, user="_apt", group="root")
        run("apt-get", *SCOPE, "download", f"{PACKAGE}={version}", cwd=directory)
        shutil.chown(directory, user="root", group="root")
        os.chmod(directory, 0o755)
        files = list(Path(directory).glob("*.deb"))
        if len(files) != 1 or files[0].is_symlink() or not files[0].is_file():
            raise RuntimeError("APT doit fournir un seul paquet Debian.")
        package = files[0]
        shutil.chown(package, user="root", group="root")
        package.chmod(0o644)
        fields = run("dpkg-deb", "--show", "--showformat=${Package} ${Version}", package,
                     capture_output=True).stdout
        if fields.strip() != f"{PACKAGE} {version}":
            raise RuntimeError("Le paquet téléchargé ne correspond pas à la version vérifiée.")
        # Le .deb vient de l'index signé d'Alfred. Les sources Debian habituelles
        # restent disponibles à APT pour résoudre d'éventuelles dépendances.
        run("apt-get", "-o", "DPkg::Lock::Timeout=30", "--yes", "--only-upgrade", "--no-remove",
            "--no-install-recommends", "install", package)


def process(operation):
    result = QUEUE.read_result()
    result.update(phase="running", operation=operation, message="Opération en cours…")
    save(result)
    try:
        auto = QUEUE.directory / "auto.enabled"
        if operation in ("auto-on", "auto-off"):
            if operation == "auto-on":
                auto.touch()
                message = "Mises à jour automatiques activées."
            else:
                auto.unlink(missing_ok=True)
                message = "Mises à jour automatiques désactivées."
        else:
            installed = installed_version()
            candidate = candidate_version()
            comparison = subprocess.run(("/usr/bin/dpkg", "--compare-versions", candidate, "gt", installed),
                                        check=False).returncode
            if comparison not in (0, 1):
                raise RuntimeError("Impossible de comparer les versions Debian.")
            newer = comparison == 0
            result.update(installed=installed, candidate=candidate, update_available=newer,
                          checked_at=datetime.now(timezone.utc).isoformat())
            if newer and operation != "check":
                install_version(candidate)
                result.update(installed=installed_version(), update_available=False)
                message = "Alfred a été mis à jour."
            else:
                message = "Une mise à jour est disponible." if newer else "Alfred est à jour."
        result.update(phase="idle", message=message)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(error, file=sys.stderr, flush=True)
        result.update(phase="failed", message="L’opération APT a échoué. Consultez le journal du service de mises à jour.")
        raise
    finally:
        save(result)


def main(mode):
    os.umask(0o077)
    if mode == "provision":
        provision()
        return
    if mode == "record":
        record_installed()
        return
    try:
        with QUEUE.lock(blocking=mode == "manual"):
            pending = QUEUE.pending()
            if mode == "manual" and pending:
                (QUEUE.requests / pending).unlink()
                process(pending)
            elif mode == "auto" and not pending and (QUEUE.directory / "auto.enabled").is_file():
                process("auto")
    except UpdatesBusy:
        pass


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("provision", "record", "manual", "auto"):
        raise SystemExit("Mode attendu : provision, record, manual ou auto.")
    main(sys.argv[1])
