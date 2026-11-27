"""Sert la PWA React compilée sous /pwa/, au même serveur et même origine qu'Alfred.

Les appels `/api/...` de la PWA restent ainsi relatifs : aucune CORS, aucune
duplication du contrôle d'origine. Le dossier est fourni par le paquet Debian
(`pwa/` à côté du paquet `alfred/`) ou, en développement, par `ui/dist`.
"""

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

PREFIX = "/pwa"
INDEX = "index.html"
# Nom sous lequel la PWA propose de télécharger l'autorité locale, pour
# l'installer une fois par appareil (Android : « Installer un certificat »).
CA_NAME = "alfred-local-ca.crt"
# Ressources fingerprintées par Vite : leur contenu ne change jamais sans nom neuf.
IMMUTABLE_PREFIX = "assets/"


def resolve_directory() -> Path | None:
    override = os.environ.get("ALFRED_PWA_DIR")
    root = Path(__file__).resolve().parent.parent
    candidates = [Path(override)] if override else []
    candidates += [root / "pwa", root / "ui" / "dist"]
    for candidate in candidates:
        if (candidate / INDEX).is_file():
            return candidate
    return None


def install_pwa_routes(app: FastAPI, directory: Path | None = None) -> Path | None:
    folder = Path(directory) if directory else resolve_directory()
    if folder is None or not (folder / INDEX).is_file():
        # Le banc d'essai reste utilisable ; seule la PWA est absente.
        return None

    root = folder.resolve()

    def send(relative: str, immutable: bool):
        target = (root / relative).resolve()
        if root not in target.parents and target != root:
            raise HTTPException(404, "Ressource introuvable.")
        if not target.is_file():
            raise HTTPException(404, "Ressource introuvable.")
        headers = {
            "Cache-Control": f"public, max-age=31536000, immutable" if immutable else "no-store",
        }
        if target.name == "sw.js":
            # Le worker doit être revalidé pour détecter une nouvelle version.
            headers["Cache-Control"] = "no-cache"
        return FileResponse(target, headers=headers)

    @app.get(PREFIX, include_in_schema=False)
    def pwa_without_slash():
        return send(INDEX, False)

    @app.get(PREFIX + "/", include_in_schema=False)
    def pwa_index():
        return send(INDEX, False)

    @app.get(PREFIX + "/manifest.webmanifest", include_in_schema=False)
    def pwa_manifest():
        target = root / "manifest.webmanifest"
        if not target.is_file():
            raise HTTPException(404, "Manifeste absent.")
        return FileResponse(target, media_type="application/manifest+json",
                            headers={"Cache-Control": "no-store"})

    @app.get(PREFIX + "/{path:path}", include_in_schema=False)
    def pwa_file(path: str):
        if not path or path.endswith("/"):
            return send(INDEX, False)
        if (root / path).is_file():
            return send(path, path.startswith(IMMUTABLE_PREFIX))
        # Repli SPA : seule une navigation de page aboutit sur l'index.
        if "." in path.rsplit("/", 1)[-1] or path.split("/", 1)[0] in {"assets", "icons"}:
            raise HTTPException(404, "Ressource introuvable.")
        return send(INDEX, False)

    return root


def install_ca_route(app: FastAPI, certificate: Path | None) -> Path | None:
    """Sert l'autorité locale pour que les appareils puissent la télécharger.

    L'aide d'installation de la PWA pointe sur `/alfred-local-ca.crt` : sans
    cette route, le lien répond 404 et l'appareil ne peut pas faire confiance
    au certificat HTTPS d'Alfred.
    """
    if certificate is None:
        return None
    source = Path(certificate)
    if not source.is_file():
        return None

    @app.get("/" + CA_NAME, include_in_schema=False)
    def local_authority():
        return FileResponse(source, media_type="application/x-x509-ca-cert",
                            filename=CA_NAME, headers={"Cache-Control": "no-store"})

    return source
