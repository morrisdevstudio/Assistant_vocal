"""Transcription locale et synthèse Phonon ; audio uniquement en mémoire."""
import base64
import io
import json
import os
import threading
import time
import wave
from pathlib import Path
from alfred.parakeet_stt import MODEL_DIRECTORY, ParakeetSTT, ParakeetError
from alfred.tts_text import prepare_tts_text
from alfred.chatterbox_cpu import ChatterboxCPUError
from alfred.local_voice_cpu import LocalVoiceCPU

MAX_AUDIO_BYTES = 6 * 1024 * 1024
MAX_AUDIO_SECONDS = 30
SAMPLE_TEXT = "Bonsoir. Je suis Alfred. Que puis-je faire pour vous ?"
DEFAULT_VOICE = "phonon-dumby-cpu"
VOICES = {
    "phonon-dumby-cpu": {"label": "Dumby · Phonon · CPU", "description": "Profil vocal Dumby · synthèse locale", "engine": "phonon"},
    "phonon-alfred-cpu": {"label": "Alfred · Phonon · voix clonée", "description": "Profil vocal personnalisé · synthèse locale CPU", "engine": "phonon"},
    "phonon-arnaud-cpu": {"label": "Phonon · Arnaud · CPU", "description": "Français local · voix du catalogue Gradium", "engine": "phonon"},
    "phonon-lucien-cpu": {"label": "Phonon · Lucien · CPU", "description": "Français local · voix du catalogue Gradium", "engine": "phonon"},
}

class InvalidAudio(ValueError):
    pass


class VoiceUnavailable(RuntimeError):
    pass


class VoiceBusy(RuntimeError):
    pass


def validate_wav(data: bytes):
    if not data or len(data) > MAX_AUDIO_BYTES:
        raise InvalidAudio("L'audio doit être un WAV de moins de 6 Mo.")
    try:
        with wave.open(io.BytesIO(data), "rb") as audio:
            channels, width, rate, frames = (audio.getnchannels(), audio.getsampwidth(),
                                             audio.getframerate(), audio.getnframes())
            if channels != 1 or width != 2 or not 8000 <= rate <= 96000:
                raise InvalidAudio("Utiliser un WAV PCM mono 16 bits, de 8 à 96 kHz.")
            duration = frames / rate
            if not 0 < duration <= MAX_AUDIO_SECONDS:
                raise InvalidAudio("L'enregistrement doit durer de plus de zéro à 30 secondes.")
            if len(audio.readframes(frames)) != frames * width:
                raise InvalidAudio("Le fichier WAV est incomplet.")
            return duration
    except (wave.Error, EOFError) as error:
        raise InvalidAudio("Le fichier n'est pas un WAV PCM valide.") from error


def pcm_16khz(data):
    """WAV validé → mono 16 kHz, sans décodage de conteneur externe implicite."""
    import av
    import numpy as np
    with wave.open(io.BytesIO(data), "rb") as source:
        rate = source.getframerate()
        pcm = np.frombuffer(source.readframes(source.getnframes()), dtype="<i2").copy()
    frame = av.AudioFrame.from_ndarray(pcm.reshape(1, -1), format="s16", layout="mono")
    frame.sample_rate = rate
    resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)
    frames = resampler.resample(frame) + resampler.resample(None)
    if not frames:
        return np.empty(0, dtype=np.float32)
    return np.concatenate([part.to_ndarray().reshape(-1) for part in frames]).astype(np.float32) / 32768


class VoiceService:
    supports_early_speech = True

    def __init__(self, directory: Path, voice_file: Path | None = None,
                 initial_voice: str | None = None):
        self.directory = directory
        data_dir = voice_file.parent if voice_file else directory.parent / "data"
        self.stt_model = "parakeet"
        self._parakeet = ParakeetSTT(directory / MODEL_DIRECTORY, data_dir / "stt-murmure.json")
        self.voice_file = voice_file
        self._local_voices = {
            name: LocalVoiceCPU(data_dir / (name.removesuffix("-cpu") + ".json"), "phonon")
            for name in VOICES
        }
        if initial_voice is not None and initial_voice not in VOICES:
            raise ValueError("Voix Phonon inconnue.")
        self._voice_id = initial_voice or self._read_preference() or DEFAULT_VOICE
        self.last_voice_id = None
        self.last_fallback = False
        self.last_error = None
        self.last_speed = None
        self._lock = threading.Lock()
        self._priority_lock = threading.Lock()
        self._foreground_waiters = 0
        self._wake_processing = False

    def _acquire_foreground(self):
        with self._priority_lock:
            self._foreground_waiters += 1
            wake = self._wake_processing
        try:
            return self._lock.acquire(timeout=46 if wake else 0)
        finally:
            with self._priority_lock:
                self._foreground_waiters -= 1

    def transcribe_wake(self, data):
        """Une analyse de veille cède toujours devant un traitement utilisateur."""
        duration = validate_wav(data)
        with self._priority_lock:
            if self._foreground_waiters or not self._lock.acquire(blocking=False):
                raise VoiceBusy("Moteur occupé.")
            self._wake_processing = True
        try:
            started = time.perf_counter()
            return self._recognize(data), duration, round((time.perf_counter()-started)*1000)
        finally:
            with self._priority_lock:
                self._wake_processing = False
                self._lock.release()

    def _available(self, voice_id):
        return voice_id in self._local_voices and self._local_voices[voice_id].available()

    def _read_preference(self):
        if self.voice_file is None:
            return None
        try:
            value = json.loads(self.voice_file.read_text(encoding="utf-8"))["voice"]
            return value if value in VOICES else None
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def _save_preference(self):
        if self.voice_file is None:
            return
        self.voice_file.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.voice_file.with_suffix(".tmp")
        temporary.write_text(json.dumps({"voice": self._voice_id, "version": 2}), encoding="utf-8")
        os.replace(temporary, self.voice_file)
        try:
            self.voice_file.chmod(0o600)
        except OSError:
            pass


    def status(self):
        stt = self._parakeet.available()
        tts = self._available(self._voice_id)
        return {"stt_available": stt, "tts_available": tts, "busy": self._lock.locked(),
                "stt_model": "Parakeet TDT 0.6B v3 · Murmure 1.11.3 · CPU INT8",
                "stt_model_id": "parakeet", "stt_engine": "murmure-native",
                "stt_ready": self._parakeet.ready,
                "tts_voice": VOICES[self._voice_id]["label"],
                "tts_voice_id": self._voice_id, "tts_engine": "phonon", "tts_speed": 1.0,
                "local_cpu_ready": {key: engine.ready for key, engine in self._local_voices.items()},
                "last_fallback": False,
                "voices": [{"id": key, **value, "available": self._available(key)} for key, value in VOICES.items()],
                "max_seconds": MAX_AUDIO_SECONDS, "conversation_ai": False, "raw_audio_saved": False}

    def set_voice(self, voice_id):
        if voice_id not in VOICES:
            raise ValueError("Voix Phonon inconnue.")
        if not self._available(voice_id):
            raise VoiceUnavailable("Cette voix Phonon n'est pas installée sur ce service.")
        if not self._acquire_foreground():
            raise VoiceBusy("Un traitement vocal est déjà en cours. Réessayez dans un instant.")
        try:
            previous = self._voice_id
            try:
                self._local_voices[voice_id].start()
            except ChatterboxCPUError as error:
                raise VoiceUnavailable("Cette voix Phonon n'a pas pu être chargée.") from error
            self._voice_id = voice_id
            try:
                self._save_preference()
            except OSError:
                self._voice_id = previous
                raise
            if voice_id != previous:
                self._local_voices[previous].close()
        finally:
            self._lock.release()

    def warmup(self):
        self._local_voices[self._voice_id].start()

    @staticmethod
    def _wav_from_float(samples, rate, *, max_gain=2.2, peak_limit=0.88):
        import numpy as np
        samples = np.asarray(samples, dtype=np.float32).reshape(-1)
        peak = float(np.max(np.abs(samples))) if samples.size else 0.0
        if peak > 0:
            samples = samples * min(max_gain, peak_limit / peak)
        pcm = np.clip(samples, -1.0, 1.0)
        pcm = (pcm * 32767).astype("<i2")
        output = io.BytesIO()
        with wave.open(output, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(rate)
            wav.writeframes(pcm.tobytes())
        return output.getvalue()


    def _recognize(self, data):
        try:
            return self._parakeet.transcribe(pcm_16khz(data))
        except ParakeetError as error:
            raise VoiceUnavailable(str(error)) from error




    def _synthesize(self, text):
        voice_id = self._voice_id
        text = prepare_tts_text(text, reformulate_absence=False)
        self.last_voice_id = voice_id
        self.last_fallback = False
        self.last_error = None
        self.last_speed = None
        try:
            audio = self._local_voices[voice_id].synthesize(text)
            validate_wav(audio)
            self.last_speed = 1.0
            return audio
        except (ChatterboxCPUError, InvalidAudio) as error:
            self.last_error = type(error).__name__
            raise VoiceUnavailable("Phonon n'a pas pu terminer la réponse. Aucun changement de voix automatique.") from error

    def close(self):
        self._parakeet.close()
        for engine in self._local_voices.values():
            engine.close()

    def _check(self, needs_stt=False):
        status = self.status()
        if not status["tts_available"] or (needs_stt and not status["stt_available"]):
            raise VoiceUnavailable("Moteurs ou modèles absents. Préparer les modèles locaux avant ce test.")


    def speak(self, text):
        self._check()
        if not self._acquire_foreground():
            raise VoiceBusy("Un traitement vocal est déjà en cours. Réessayez dans un instant.")
        try:
            started = time.perf_counter()
            audio = self._synthesize(text)
            return audio, round((time.perf_counter()-started)*1000)
        finally:
            self._lock.release()


    def speak_blocks(self, blocks):
        """Même profil verrouillé sur toute la réponse, un WAV à la fois."""
        self._check()
        if not self._acquire_foreground():
            raise VoiceBusy("Un traitement vocal est déjà en cours.")
        try:
            for text in blocks:
                started = time.perf_counter()
                audio = self._synthesize(text)
                yield audio, round((time.perf_counter() - started) * 1000)
        finally:
            self._lock.release()


    def metadata(self):
        engine = (VOICES[self.last_voice_id]["engine"] if self.last_voice_id else
                  VOICES[self._voice_id]["engine"])
        return {"voice_id": self.last_voice_id or self._voice_id, "voice_engine": engine,
                "voice_fallback": self.last_fallback, "voice_speed": self.last_speed}


    def preload_stt(self):
        with self._lock:
            self._parakeet.preload()




    def transcribe(self, data):
        duration = validate_wav(data)
        if not self.status()["stt_available"]:
            raise VoiceUnavailable("Modèle de transcription absent. Préparer le modèle local avant ce test.")
        if not self._acquire_foreground():
            raise VoiceBusy("Un traitement vocal est déjà en cours. Réessayez dans un instant.")
        try:
            started = time.perf_counter()
            text = self._recognize(data)
            return text, duration, round((time.perf_counter()-started)*1000)
        finally:
            self._lock.release()


    def turn(self, data):
        duration = validate_wav(data)
        self._check(needs_stt=True)
        if not self._acquire_foreground():
            raise VoiceBusy("Un traitement vocal est déjà en cours. Réessayez dans un instant.")
        try:
            started = time.perf_counter()
            text = self._recognize(data)
            stt_ms = round((time.perf_counter()-started)*1000)
            if not text:
                return {"text": "", "reply_text": "Aucune parole reconnue. Réessayez près du micro.",
                        "audio_base64": None, "timings": {"stt_ms": stt_ms, "tts_ms": 0},
                        "input_seconds": round(duration, 2), "mode": "audio-test"}
            # Aucun outil, action domotique ou raisonnement n'est déclenché dans ce banc.
            reply = "J'ai entendu : " + text[:500] + ". Ceci est un test audio. La conversation avec l'intelligence artificielle n'est pas encore connectée."
            tts_started = time.perf_counter()
            audio = self._synthesize(reply)
            return {"text": text, "reply_text": reply, "audio_base64": base64.b64encode(audio).decode("ascii"),
                    "timings": {"stt_ms": stt_ms, "tts_ms": round((time.perf_counter()-tts_started)*1000)},
                    "input_seconds": round(duration, 2), "mode": "audio-test"}
        finally:
            self._lock.release()


