"""API des réglages et canal audio de veille navigateur, de même origine."""
import asyncio
import base64
import binascii
import json
import time
from urllib.parse import urlsplit
from fastapi import HTTPException, Request, WebSocket, WebSocketDisconnect
from alfred.wake_browser import BrowserWakeSession
from alfred.wake_manager import MAX_MODEL_BYTES


def install_wake_routes(app):
    def manager():
        return app.state.wake_manager

    def source_check(source):
        if source not in ("browser", "esp32"):
            raise HTTPException(404, "Source de réveil inconnue.")

    @app.get("/api/wake/config")
    async def config():
        return manager().snapshot()

    @app.put("/api/wake/config/{source}")
    async def save(source: str, request: Request):
        source_check(source)
        data = await request.body()
        if len(data) > 8192:
            raise HTTPException(413, "Réglages trop volumineux.")
        try:
            return await manager().save(source, json.loads(data))
        except (ValueError, OSError, RuntimeError) as error:
            raise HTTPException(409, str(error) if isinstance(error, ValueError) else "Préparation du réveil impossible ; ancien réglage conservé.") from error

    @app.post("/api/wake/models")
    async def import_model(request: Request):
        data = bytearray()
        async for part in request.stream():
            data.extend(part)
            if len(data) > MAX_MODEL_BYTES * 4 // 3 + 8192:
                raise HTTPException(413, "Modèle supérieur à dix Mo.")
        try:
            payload = json.loads(data)
            if not isinstance(payload, dict) or set(payload) != {"label", "phrase", "model_base64"}:
                raise ValueError("Import invalide.")
            binary = base64.b64decode(payload["model_base64"], validate=True)
            return await manager().import_model(payload["label"], payload["phrase"], binary)
        except (ValueError, TypeError, binascii.Error, asyncio.TimeoutError) as error:
            raise HTTPException(422, "Import refusé : modèle incompatible, invalide ou validation expirée.") from error

    @app.post("/api/wake/stop/{source}")
    async def stop(source: str):
        source_check(source)
        m = manager()
        if getattr(m.terminal, 'wake_test', None):
            raise HTTPException(409, "Arrêtez d'abord le test de réveil.")
        async with m.lock:
            if source == "browser":
                await m.stop_browser()
            else:
                m.stop_terminal()
        return m.snapshot()

    @app.websocket("/api/wake/browser")
    async def browser(socket: WebSocket):
        origin = urlsplit(socket.headers.get("origin", ""))
        if origin.scheme not in ("http", "https") or origin.netloc != socket.headers.get("host"):
            await socket.close(code=1008)
            return
        await socket.accept()
        m = manager()
        session = None
        try:
            async with m.lock:
                if m.occupied():
                    raise ValueError("Une commande ou une réponse est en cours.")
                detector = await m.prepare("browser")
                if m.occupied():
                    raise ValueError("Une commande vient de commencer.")
                m.preferences.save_resume(False)
                await m.stop_browser("Veille transférée vers un autre onglet.")
                m.terminal.stop_wake_word()
                m.owner = "browser"
                session = BrowserWakeSession(m, socket, detector)
                m.browser = session
            await session.send({"type": "ready"})
            while session.active:
                message = await asyncio.wait_for(socket.receive(), 15)
                if message["type"] == "websocket.disconnect":
                    break
                if message.get("bytes") is not None:
                    await session.feed(message["bytes"])
                else:
                    text = message.get("text", "")
                    if len(text) > 256:
                        raise ValueError("Message trop volumineux.")
                    value = json.loads(text)
                    if value == {"type": "resume"}:
                        await session.resume()
                    elif value == {"type": "pause"}:
                        session.phase = "paused"
                        session.detector.reset_audio()
                    elif value == {"type": "ping"}:
                        pass
                    else:
                        raise ValueError("Message de veille inconnu.")
        except (WebSocketDisconnect, asyncio.TimeoutError):
            pass
        except Exception:
            if session:
                await session.close("Veille interrompue : vérifiez le moteur et le microphone.")
            else:
                await socket.send_json({"type": "stopped", "reason": "Veille indisponible ou assistant occupé."})
                await socket.close()
        finally:
            async with m.lock:
                if m.browser is session and session is not None:
                    await m.stop_browser("Connexion de veille fermée.")
