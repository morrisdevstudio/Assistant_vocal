"""Réveil STT asynchrone : audio éphémère, une inférence et un dernier extrait."""
import asyncio
import io
import time
import wave
from alfred.wake_settings import strip_prefix
from alfred.voice import VoiceBusy

RATE_BYTES = 32000


def wav_pcm(pcm):
    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(pcm)
    return output.getvalue()


class STTWakeDetector:
    name = "stt"

    def __init__(self, transcribe, phrases, callback=None, vad_factory=None):
        from alfred.speech_activity import SpeechActivity
        self.transcribe, self.phrases, self.callback = transcribe, phrases, callback
        self.diagnostic_observer = None
        self.vad_factory = vad_factory or SpeechActivity
        self.vad = self.vad_factory()
        self.task = None
        self.pending = None
        self.generation = 0
        self.detections = 0
        self.last_detection = 0.
        self.inferences = 0
        self.last_ms = 0
        self.error = None
        self.audio = bytearray()
        self.pre = bytearray()
        self.silence = 0
        self.hop = 0
        self.segment = 0
        self.first = True
        self.detected = False
        self.energy_voiced = 0
        self.energy_fallbacks = 0

    def status(self):
        return {"detections": self.detections, "last_detection": self.last_detection,
                "threshold": None, "inferences": self.inferences, "last_ms": self.last_ms,
                "error": self.error, "busy": self.task is not None and not self.task.done(),
                "latched": self.detected, "pending": self.pending is not None,
                "vad_probability": getattr(self.vad, "probability", None),
                "energy_fallbacks": self.energy_fallbacks,
                "speech_active": self.vad.active if hasattr(self.vad, "active") else None}

    def reset_audio(self):
        self.generation += 1
        self.pending = None
        self.audio.clear()
        self.pre.clear()
        self.silence = self.hop = 0
        self.first = True
        self.detected = False
        self.energy_voiced = 0
        self.segment += 1
        self.vad = self.vad_factory()

    def feed(self, data):
        if self.detected:
            self.audio.extend(data)
            del self.audio[30 * RATE_BYTES:]
            return False
        active = self.vad.feed(data)
        # Silero n'est pas l'unique porte d'entrée : une voix audible peut être
        # rejetée par son état récurrent après des échanges successifs. Ce
        # secours ne valide jamais le mot d'appel, toujours vérifié par le STT.
        import numpy as np
        samples = np.frombuffer(data, dtype="<i2").astype("float32") if len(data) % 2 == 0 else []
        energetic = len(samples) > 0 and float(np.sqrt(np.mean(samples * samples))) > 490
        self.energy_voiced = self.energy_voiced + len(data) if energetic else 0
        if not active and self.energy_voiced >= int(.18 * RATE_BYTES):
            active = True
            self.energy_fallbacks += 1
        if not self.audio:
            self.pre.extend(data)
            del self.pre[:-int(.35 * RATE_BYTES)]
            if not active:
                return False
            self.audio.extend(self.pre)
            self.pre.clear()
            self.segment += 1
            self.first = True
        else:
            self.audio.extend(data)
        self.silence = 0 if active else self.silence + len(data)
        self.hop += len(data)
        final = self.silence >= int(.65 * RATE_BYTES)
        if self.hop >= RATE_BYTES // 2 or final:
            self.hop = 0
            # Une détection au bord gauche d'une fenêtre glissante ne doit pas
            # transformer une mention tardive en interpellation initiale.
            at_start = len(self.audio) <= 6 * RATE_BYTES
            self.pending = (self.generation, self.segment, bytes(self.audio[-6 * RATE_BYTES:]), final, at_start)
            if self.task is None or self.task.done():
                self.task = asyncio.create_task(self._run())
        if final or len(self.audio) >= 30 * RATE_BYTES:
            self.audio.clear()
            self.silence = self.hop = 0
        return False

    async def _run(self):
        while self.pending is not None:
            generation, segment, pcm, final, at_start = self.pending
            self.pending = None
            started = time.perf_counter()
            try:
                result = await asyncio.to_thread(self.transcribe, wav_pcm(pcm))
                text = result[0] if isinstance(result, tuple) else result
                self.last_ms = round((time.perf_counter() - started) * 1000)
                self.inferences += 1
                self.error = None
            except VoiceBusy:
                continue
            except Exception:
                if generation == self.generation:
                    self.error = "Transcription de veille indisponible."
                continue
            if generation != self.generation or segment != self.segment or self.detected or not at_start:
                continue
            _, matched = strip_prefix(text, self.phrases)
            if self.diagnostic_observer:
                self.diagnostic_observer(text, matched, final, self.last_ms)
            if not matched:
                continue
            self.detected = True
            self.pending = None
            self.detections += 1
            self.last_detection = time.monotonic()
            # Inclure l'audio arrivé pendant le calcul, même après la pause.
            captured = bytes(self.audio) if self.audio else pcm
            if self.callback:
                accepted = await self.callback(captured)
                if accepted is False and generation == self.generation:
                    # Un réveil refusé (terminal momentanément occupé) ne doit
                    # pas figer le détecteur en mode déjà-détecté.
                    self.reset_audio()
