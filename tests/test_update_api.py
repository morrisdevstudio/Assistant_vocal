from fastapi.testclient import TestClient

from alfred import app as app_module
from alfred.config import Settings
from alfred.updates import UpdatesBusy


def test_debian_update_requests_require_admin_code_and_are_serialized(tmp_path, monkeypatch):
    class Queue:
        available = True
        pending = None

        def status(self):
            return {"available": True, "installed": "0.6.0-1"}

        def authorized(self, supplied):
            return supplied == "test-administration-code"

        def enqueue(self, operation):
            if self.pending:
                raise UpdatesBusy
            self.pending = operation

    queue = Queue()
    monkeypatch.setattr(app_module, "UpdateQueue", lambda: queue)
    with TestClient(app_module.create_app(Settings(tmp_path)), base_url="https://testserver") as client:
        assert client.get("/api/updates").json() == {"available": True, "installed": "0.6.0-1"}
        assert client.post("/api/updates/install", json={}).status_code == 403
        assert queue.pending is None
        headers = {"X-Alfred-Update-Key": "test-administration-code"}
        assert client.post("http://testserver/api/updates/install", json={}, headers=headers).status_code == 403
        assert queue.pending is None
        assert client.post("/api/updates/install", json={}, headers=headers).status_code == 202
        assert queue.pending == "install"
        assert client.post("/api/updates/check", json={}, headers=headers).status_code == 409
        assert client.post("/api/updates/arbitrary", json={}, headers=headers).status_code == 422


def test_update_controls_are_unavailable_without_the_debian_package(tmp_path, monkeypatch):
    class Queue:
        available = False

        def status(self):
            return {"available": False}

    monkeypatch.setattr(app_module, "UpdateQueue", Queue)
    with TestClient(app_module.create_app(Settings(tmp_path))) as client:
        assert client.get("/api/updates").json() == {"available": False}
        assert client.post("/api/updates/check", json={}).status_code == 503
