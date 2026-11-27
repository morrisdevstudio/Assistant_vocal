"""Attendre le démarrage de l'ordonnanceur à l'adresse déclarée par systemd."""

import json
import os
from pathlib import Path
import ssl
import time
from urllib.request import ProxyHandler, HTTPSHandler, build_opener


def main():
    host = os.environ.get("ALFRED_HOST", "127.0.0.1")
    tls = os.environ.get("ALFRED_TLS") == "--https"
    handlers = [ProxyHandler({})]
    if tls:
        certificate = Path(os.environ["ALFRED_DATA_DIR"]).parent / "https/server.crt"
        context = ssl.create_default_context(cafile=os.environ.get("ALFRED_TLS_CA") or str(certificate))
        handlers.append(HTTPSHandler(context=context))
    opener = build_opener(*handlers)
    url = f"{'https' if tls else 'http'}://{host}:8765/health"
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            with opener.open(url, timeout=2) as response:
                if json.load(response).get("status") == "ok":
                    return
        except (OSError, ValueError):
            pass
        time.sleep(1)
    raise SystemExit(f"Alfred ne répond pas sur {url}")


if __name__ == "__main__":
    main()
