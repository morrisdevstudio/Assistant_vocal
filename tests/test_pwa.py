"""Route /pwa : la PWA compilée est servie par Alfred, sans serveur séparé."""

from fastapi.testclient import TestClient

from alfred.app import create_app
from alfred.config import Settings


def make_client(tmp_path, pwa_directory=None):
    return create_app(Settings(tmp_path, poll_seconds=0.02, pwa_dir=pwa_directory))


def build_pwa(directory):
    (directory / "assets").mkdir(parents=True)
    (directory / "icons").mkdir()
    (directory / "index.html").write_text(
        '<!doctype html><script src="/pwa/assets/app.js"></script>', encoding="utf-8")
    (directory / "assets" / "app.js").write_text("console.log('pwa')", encoding="utf-8")
    (directory / "icons" / "alfred-192.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (directory / "manifest.webmanifest").write_text('{"start_url":"/pwa/"}', encoding="utf-8")
    (directory / "sw.js").write_text("self.skipWaiting()", encoding="utf-8")


def test_pwa_routes_serve_index_assets_and_manifest(tmp_path):
    pwa = tmp_path / "pwa"
    build_pwa(pwa)
    with TestClient(make_client(tmp_path / "data", pwa)) as client:
        for path in ("/pwa", "/pwa/"):
            response = client.get(path)
            assert response.status_code == 200
            assert '/pwa/assets/app.js' in response.text
            assert response.headers["cache-control"] == "no-store"

        asset = client.get("/pwa/assets/app.js")
        assert asset.status_code == 200
        assert "immutable" in asset.headers["cache-control"]

        manifest = client.get("/pwa/manifest.webmanifest")
        assert manifest.status_code == 200
        assert manifest.headers["content-type"].startswith("application/manifest+json")

        worker = client.get("/pwa/sw.js")
        assert worker.status_code == 200
        assert worker.headers["cache-control"] == "no-cache"

        icon = client.get("/pwa/icons/alfred-192.png")
        assert icon.status_code == 200
        assert icon.headers["content-type"] == "image/png"


def test_pwa_spa_fallback_is_limited_to_navigation(tmp_path):
    pwa = tmp_path / "pwa"
    build_pwa(pwa)
    with TestClient(make_client(tmp_path / "data", pwa)) as client:
        page = client.get("/pwa/minuteries")
        assert page.status_code == 200
        assert '<script src="/pwa/assets/app.js">' in page.text
        # Une ressource manquante ne doit jamais renvoyer du HTML avec un code 200.
        assert client.get("/pwa/assets/absent.js").status_code == 404
        assert client.get("/pwa/icons/absent.png").status_code == 404


def test_pwa_does_not_escape_its_directory(tmp_path):
    pwa = tmp_path / "pwa"
    build_pwa(pwa)
    (tmp_path / "secret.txt").write_text("confidentiel", encoding="utf-8")
    with TestClient(make_client(tmp_path / "data", pwa)) as client:
        response = client.get("/pwa/../secret.txt")
        assert response.status_code in (404, 400)
        assert "confidentiel" not in response.text


def test_missing_pwa_leaves_the_test_bench_working(tmp_path):
    with TestClient(make_client(tmp_path / "data", tmp_path / "absent")) as client:
        assert client.get("/pwa/").status_code == 404
        assert client.get("/").status_code == 200
        assert client.get("/api/status").status_code == 200
