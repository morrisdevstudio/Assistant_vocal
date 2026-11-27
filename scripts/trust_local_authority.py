"""Fait reconnaître l'autorité locale d'Alfred par cette machine.

Le certificat HTTPS d'Alfred est signé par l'autorité locale du projet
(`.local/https/ui-ca.crt`, servie sur `/alfred-local-ca.crt`). Les appareils
qui l'ont importée ouvrent `https://<IP>:8765/pwa/` sans avertissement. Sur un
Chromium de la machine de développement, le navigateur intégré d'un autre outil
(Timon, Electron…) refuse encore la page tant que l'autorité n'est pas dans le
magasin de confiance.

Le script ajoute le certificat public à deux magasins et n'installe aucun
secret :

- `/usr/local/share/ca-certificates`, lu par curl, Python et la plupart des
  navigateurs passant par OpenSSL (`update-ca-certificates` demande root) ;
- `~/.pki/nssdb`, le magasin NSS de l'utilisateur que Chromium et Electron
  lisent aussi, ajouté sans root quand `certutil` est disponible.

Redémarrer le navigateur concerné après l'exécution. Linux uniquement.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = ROOT / ".local" / "https" / "ui-ca.crt"
TARGET = Path("/usr/local/share/ca-certificates/alfred-local-ca.crt")
NICKNAME = "Alfred UI - Autorite locale"


def run(command, **options):
    return subprocess.run(command, check=True, **options)


def install_system(authority, assume_yes):
    """Copie l'autorité dans le magasin système, puis le régénère."""
    if not assume_yes:
        print(f"Écriture de {TARGET} et mise à jour du magasin système (sudo).")
    try:
        run(["sudo", "install", "-m", "0644", str(authority), str(TARGET)])
        run(["sudo", "update-ca-certificates"])
    except subprocess.CalledProcessError as error:
        return f"Magasin système non mis à jour ({error})."
    return "Magasin système mis à jour."


def nss_certutil():
    tool = shutil.which("certutil")
    if tool is not None:
        return tool
    local = ROOT / ".local" / "bin" / "certutil"
    return str(local) if local.is_file() else None


def nss_contains(tool, database):
    """Vrai si le magasin liste déjà l'autorité (le listing ne modifie rien)."""
    result = subprocess.run([tool, "-d", f"sql:{database}", "-L"], capture_output=True, text=True)
    if result.returncode:
        return None
    return any(line.strip().startswith(NICKNAME) for line in result.stdout.splitlines())


def install_nss(authority, home):
    """Ajoute l'autorité au magasin NSS de l'utilisateur, sans root."""
    tool = nss_certutil()
    if tool is None:
        return "certutil absent : magasin NSS non mis à jour (navigateur basé sur Chromium)."
    database = home / ".pki" / "nssdb"
    database.mkdir(parents=True, exist_ok=True)
    for folder in (database.parent, database):
        folder.chmod(0o700)
    present = nss_contains(tool, database)
    if present:
        return "Magasin NSS : autorité déjà présente."
    result = subprocess.run([tool, "-d", f"sql:{database}", "-A", "-t", "C,,", "-n", NICKNAME,
                             "-i", str(authority)], capture_output=True, text=True)
    if result.returncode:
        detail = result.stderr.strip() or f"code {result.returncode}"
        return f"Magasin NSS non mis à jour : {detail}"
    return "Magasin NSS mis à jour."


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--authority", type=Path, default=AUTHORITY,
                        help="certificat public de l'autorité (par défaut .local/https/ui-ca.crt)")
    parser.add_argument("--no-system", action="store_true",
                        help="ne pas toucher au magasin système (aucun sudo)")
    parser.add_argument("--yes", action="store_true", help="ne pas décrire l'opération avant de l'exécuter")
    args = parser.parse_args()
    authority = args.authority.resolve()
    if not authority.is_file():
        parser.error(f"autorité introuvable : {authority} (voir scripts/setup_ui_https.py)")
    if sys.platform != "linux":
        parser.error("script prévu pour Linux ; importer le certificat à la main sur les autres systèmes")
    if authority.name == "server.crt":
        parser.error("indiquer ui-ca.crt, pas le certificat du serveur")
    results = []
    if not args.no_system:
        results.append(install_system(authority, args.yes))
    results.append(install_nss(authority, Path.home()))
    for line in results:
        print(line)
    print(f"Empreinte attendue : voir `openssl x509 -in {authority} -noout -fingerprint -sha256`.")
    print("Redémarrer le navigateur concerné, puis ouvrir https://<IP>:8765/pwa/")


if __name__ == "__main__":
    main()
