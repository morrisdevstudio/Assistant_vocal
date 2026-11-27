"""Prise PCM de calibration, isolée de la conversation et du journal."""

import asyncio
import secrets

from fastapi import HTTPException, Request, Response

from alfred.wake_stt import RATE_BYTES, wav_pcm


CAPTURE_SECONDS = 12
DOWNLOAD_SECONDS = 90
PRIVATE = {"Cache-Control": "no-store"}


class RoomCapture:
    capture_only = True

    def __init__(self, terminal):
        self.terminal = terminal
        self.previously_armed = terminal.wake_armed
        self.token = secrets.token_urlsafe(24)
        self.pcm = bytearray()
        self.state = "waiting"
        self.last_frame = None
        self.task = None
        self.expiry = None

    async def start(self):
        if not self.terminal.wake_detector:
            raise ValueError("Détecteur de réveil indisponible.")
        self.terminal.wake_detector.reset_audio()
        self.terminal.wake_test = self
        try:
            if not self.previously_armed:
                await asyncio.wait_for(self.terminal.start_wake_word(), 5)
            self.task = asyncio.create_task(self.monitor())
        except BaseException:
            await self.finish("interrompu")
            raise

    async def monitor(self):
        try:
            await asyncio.sleep(CAPTURE_SECONDS + 6)
            await self.finish("flux_interrompu")
        except asyncio.CancelledError:
            pass

    async def observe(self, data):
        if self.state not in ("waiting", "recording") or not data or len(data) % 2:
            return
        now = asyncio.get_running_loop().time()
        if self.last_frame is not None and now - self.last_frame > 1.5:
            await self.finish("flux_interrompu")
            return
        self.last_frame = now
        self.state = "recording"
        remaining = CAPTURE_SECONDS * RATE_BYTES - len(self.pcm)
        self.pcm.extend(data[:remaining])
        if len(self.pcm) == CAPTURE_SECONDS * RATE_BYTES:
            await self.finish("termine")

    def detected(self):
        self.terminal.wake_detector.reset_audio()

    def discard(self, state="expire"):
        if self.expiry:
            self.expiry.cancel()
            self.expiry = None
        self.pcm.clear()
        self.state = state

    async def finish(self, reason):
        if self.terminal.wake_test is self:
            if self.task and self.task is not asyncio.current_task():
                self.task.cancel()
            self.terminal.wake_detector.reset_audio()
            self.terminal.wake_test = None
            if not self.previously_armed:
                self.terminal.stop_wake_word()
        if reason == "termine":
            self.state = "ready"
            self.expiry = asyncio.get_running_loop().call_later(DOWNLOAD_SECONDS, self.discard)
        else:
            self.discard(reason)

    def snapshot(self):
        return {"state": self.state, "remaining": CAPTURE_SECONDS - len(self.pcm) // RATE_BYTES}


def install_room_capture_routes(app):
    def authorized(token):
        session = getattr(app.state, "room_capture", None)
        if not session or not token or not secrets.compare_digest(token.encode(), session.token.encode()):
            raise HTTPException(404, "Prise introuvable.", headers=PRIVATE)
        return session

    @app.post("/api/room-capture")
    async def start(request: Request, response: Response):
        if request.headers.get("content-type") != "application/json":
            raise HTTPException(415, "Utilisez le bouton de calibration.")
        response.headers.update(PRIVATE)
        terminal = app.state.terminal
        manager = app.state.wake_manager
        async with manager.lock:
            previous = getattr(app.state, "room_capture", None)
            if previous and previous.state == "ready":
                raise HTTPException(409, "Une prise attend d'être téléchargée ou supprimée.")
            if not terminal.connected or manager.occupied() or manager.owner == "browser":
                raise HTTPException(409, "ESP32 déconnecté ou occupé.")
            session = RoomCapture(terminal)
            try:
                await session.start()
            except (ValueError, TimeoutError) as error:
                raise HTTPException(409, str(error) or "Le micro n'a pas démarré.") from error
            app.state.room_capture = session
            return {"token": session.token, **session.snapshot()}

    @app.get("/api/room-capture")
    async def status(request: Request, response: Response):
        response.headers.update(PRIVATE)
        return authorized(request.headers.get("x-alfred-capture")).snapshot()

    @app.delete("/api/room-capture")
    async def cancel(request: Request, response: Response):
        response.headers.update(PRIVATE)
        session = authorized(request.headers.get("x-alfred-capture"))
        await session.finish("interrompu")
        return session.snapshot()

    @app.get("/api/room-capture/wav")
    async def download(request: Request):
        session = authorized(request.headers.get("x-alfred-capture"))
        if session.state != "ready":
            raise HTTPException(409, "La prise n'est pas disponible.", headers=PRIVATE)
        data = wav_pcm(session.pcm)
        session.discard("telecharge")
        return Response(data, media_type="audio/wav", headers={
            **PRIVATE, "Content-Disposition": 'attachment; filename="alfred-esp32.wav"',
        })

    @app.get("/api/room-capture/signal")
    def signal():
        import numpy as np
        from alfred.room_benchmark import RATE, test_signal
        samples = np.pad(test_signal(), (RATE, RATE * 2)).astype("<i2")
        return Response(wav_pcm(samples.tobytes()), media_type="audio/wav")
