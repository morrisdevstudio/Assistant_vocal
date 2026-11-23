"""Session PCM navigateur : veille, capture puis transfert éphémère d'un seul tour."""
import base64
import time
from alfred.terminal import Capture
from alfred.wake_stt import STTWakeDetector
from alfred.speech_activity import SpeechActivity


class BrowserWakeSession:
    def __init__(self, manager, socket, detector):
        self.manager, self.socket, self.detector = manager, socket, detector
        self.active = True
        self.phase = "waking"
        self.capture = None
        self.pre = bytearray()
        self.last_audio = time.monotonic()
        if isinstance(detector, STTWakeDetector):
            detector.callback = self.detected

    def status(self):
        return {"armed": self.active, "phase": self.phase, **self.detector.status()}

    async def send(self, value):
        if self.active:
            await self.socket.send_json(value)

    async def detected(self, pcm=None):
        if not self.active or self.phase != "waking" or self.manager.browser is not self:
            return
        self.phase = "recording"
        self.manager.busy = True
        self.capture = Capture(SpeechActivity())
        audio = pcm if pcm is not None else bytes(self.pre)
        for offset in range(0, len(audio), 1024):
            self.capture.feed(audio[offset:offset+1024])
        self.pre.clear()
        await self.send({"type": "detected"})

    async def feed(self, data):
        if not self.active:
            return
        if not data or len(data) > 16384 or len(data) % 2:
            raise ValueError("Trame PCM invalide.")
        self.last_audio = time.monotonic()
        if self.phase == "waking":
            self.pre.extend(data)
            del self.pre[:-6 * 32000]
            if self.detector.feed(data):
                await self.detected()
        elif self.phase == "recording" and self.capture:
            _, done = self.capture.feed(data)
            if done:
                capture, self.capture = self.capture, None
                self.phase = "processing"
                self.manager.busy = True
                token = self.manager.ticket(self.manager.preferences.phrases("browser"))
                await self.send({"type": "command", "turn": token,
                                 "audio_base64": base64.b64encode(capture.wav()).decode("ascii")})

    async def resume(self):
        if not self.active:
            return
        self.manager.busy = False
        self.capture = None
        self.pre.clear()
        self.detector.reset_audio()
        self.phase = "waking"
        await self.send({"type": "ready"})

    async def close(self, reason):
        if not self.active:
            return
        self.active = False
        self.detector.reset_audio()
        self.pre.clear()
        self.capture = None
        try:
            await self.socket.send_json({"type": "stopped", "reason": reason})
            await self.socket.close()
        except Exception:
            pass
