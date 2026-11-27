"""Un satellite ESPHome relié directement à Alfred, sans connexion Home Assistant.

Le micro ne transmet qu'après bouton/réveil. Audio en mémoire ; serveur FLAC
éphémère limité à l'adresse de la carte, pour le lecteur HTTP du firmware.
"""
import asyncio
import base64
from contextlib import nullcontext, suppress
from dataclasses import dataclass
import io
import ipaddress
import json
import re
from pathlib import Path
import secrets
import socket
import time
import uuid
import wave
from alfred.audio_stream import StreamingFlac, speech_blocks, trim_block_edges
from alfred.light_trace import ACTIVE_TRACE, LightTrace, mark, measure
from alfred.speech_activity import SpeechActivity
from alfred.terminal_leds import TerminalLeds


RATE = 16000


def playback_audio(wav):
    """FLAC mono 48 kHz attendu par le firmware ; aucun effet sur le timbre."""
    import numpy as np
    import soundfile as sf
    from math import gcd
    from scipy.signal import resample_poly
    if len(wav) > 6 * 1024 * 1024:
        raise ValueError("Réponse audio trop grande")
    samples, rate = sf.read(io.BytesIO(wav), dtype="float32")
    if samples.ndim != 1 or not np.isfinite(samples).all():
        raise ValueError("Réponse audio invalide")
    if rate != 48000:
        divisor = gcd(rate, 48000)
        samples = resample_poly(samples, 48000 // divisor, rate // divisor)
    output = io.BytesIO()
    sf.write(output, samples, 48000, format="FLAC", subtype="PCM_16")
    return output.getvalue()


@dataclass(frozen=True)
class TerminalConfig:
    host: str
    expected_mac: str
    media_host: str
    media_port: int = 8766
    floor_id: str = "rdc"
    room: str = "Bureau"
    progressive_tts: bool = True
    wake_word: bool = False
    wake_model: str = "alfred-he.onnx"
    wake_name: str = "alfred"
    wake_verify: bool = True
    wake_threshold: float = .25
    wake_session_seconds: int = 900

    @classmethod
    def load(cls, path):
        if not path.exists():
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("enabled") is not True:
            return None
        config = cls(**{k: v for k, v in value.items() if k != "enabled"})
        if (not config.host.endswith(".local") and
                not ipaddress.ip_address(config.host).is_private):
            raise ValueError("Adresse du terminal non locale")
        if (not ipaddress.ip_address(config.media_host).is_private
                or not 1024 <= config.media_port <= 65535
                or config.floor_id not in ("rdc", "etage1")
                or not isinstance(config.progressive_tts, bool)
                or not isinstance(config.wake_word, bool)
                or not isinstance(config.wake_model, str)
                or config.wake_name not in ("alfred", "alexa", "jarvis")
                or not isinstance(config.wake_verify, bool)
                or not isinstance(config.wake_threshold, (int, float))
                or isinstance(config.wake_threshold, bool)
                or not 0 < config.wake_threshold < 1
                or not isinstance(config.wake_session_seconds, int)
                or isinstance(config.wake_session_seconds, bool)
                or not 30 <= config.wake_session_seconds <= 3600
                or len(config.expected_mac.split(":")) != 6):
            raise ValueError("Configuration du terminal invalide")
        return config


class Capture:
    """PCM16 mono borné, pré-capture courte et détection de pause locale."""
    def __init__(self, speech_activity=None):
        self.data = bytearray()
        self.speech_activity = speech_activity
        self.voiced = 0
        self.silence = 0
        self.speaking = False
        self.received = 0
        self.end_reason = None
        self.last_voice_at = None

    def feed(self, data):
        import numpy as np
        if not data or len(data) % 2:
            return False, False
        samples = np.frombuffer(data, dtype="<i2").astype("float32")
        loud = (self.speech_activity.feed(data) if self.speech_activity is not None
                else float(np.sqrt(np.mean(samples * samples))) > 490)
        if loud:
            self.last_voice_at = time.perf_counter()
        duration = len(samples) / RATE
        self.received += len(data)
        self.data.extend(data)
        started = False
        if not self.speaking:
            self.voiced = self.voiced + duration if loud else 0
            if self.voiced >= .18:
                self.speaking = started = True
            else:
                # Garder le début de la parole sans conserver toute l'attente.
                del self.data[:-int(.6 * RATE) * 2]
        else:
            self.silence = 0 if loud else self.silence + duration
        done = self.speaking and (self.silence >= .9 or len(self.data) >= RATE * 2 * 29)
        if done:
            self.end_reason = "speech_pause" if self.silence >= .9 else "max_duration"
        return started, done

    def wav(self):
        output = io.BytesIO()
        with wave.open(output, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(RATE)
            wav.writeframes(self.data[:RATE * 2 * 30])
        return output.getvalue()


class WakeGate:
    """Veille continue : les trames nourrissent le détecteur jusqu'au mot d'appel.

    Les deux secondes précédentes restent en mémoire pour vérifier le mot ;
    la prise de commande conserve son pré-roll habituel de 0,6 seconde.
    """
    def __init__(self, detector, preroll_seconds=2.0):
        self.detector = detector
        self.preroll = bytearray()
        self.limit = max(2, int(preroll_seconds * RATE) * 2)

    def feed(self, data):
        self.preroll.extend(data)
        if len(self.preroll) > self.limit:
            del self.preroll[:-self.limit]
        return self.detector.feed(data)

    def take(self):
        data, self.preroll = bytes(self.preroll), bytearray()
        return data


class AudioTickets:
    def __init__(self):
        self.items = {}
        self.downloads = 0

    def put(self, audio):
        if not audio or len(audio) > 6 * 1024 * 1024:
            raise ValueError("Réponse audio invalide")
        return self._put(audio)

    def put_stream(self, stream):
        return self._put(stream)

    def _put(self, audio):
        token = secrets.token_urlsafe(24)
        self.items = {k: v for k, v in self.items.items() if v[0] > time.monotonic()}
        while len(self.items) >= 2:
            self.items.pop(next(iter(self.items)))
        self.items[token] = (time.monotonic() + 90, audio)
        try:
            asyncio.get_running_loop().call_later(90, self.items.pop, token, None)
        except RuntimeError:
            pass
        return "/audio/" + token + ".flac"

    def get(self, path):
        if not path.startswith("/audio/") or not path.endswith(".flac"):
            return None
        entry = self.items.get(path[7:-5])
        if not entry or entry[0] <= time.monotonic():
            return None
        return entry[1]


class DirectTerminal:
    def __init__(self, config, process, speak, speak_blocks=None, transcribe=None,
                 vad_factory=SpeechActivity, wake_detector=None, *, led_path=None):
        self.config, self.process, self.speak = config, process, speak
        self.speak_blocks = speak_blocks
        self.transcribe = transcribe
        self.vad_factory = vad_factory
        self.wake_detector = wake_detector
        self.wake_test = None
        self.wake_journal = None
        self.stt_test_until = 0
        self.stt_test_pending = False
        self.capture_test = False
        self.capture_test_expired = False
        self.stt_result = None
        self.client = None
        self.server = None
        self.worker = self.turn = self.watchdog = None
        self.leds = TerminalLeds(led_path)
        self.stopping = asyncio.Event()
        self.capture = None
        self.phase = "disabled" if config is None else "connecting"
        self.error = None
        self.connected = False
        self.peer = None
        self.device_name = None
        self.services = {}
        self.session_id = uuid.uuid4().hex
        self.tickets = AudioTickets()
        self.expect_followup = False
        self.captures = self.turns = self.audio_bytes = 0
        self.last_timings = None
        self.light_trace = None
        self.light_trace_reply = None
        self.conversation_display = None
        self.conversation_display_until = 0
        self.reply_started = None
        self.reply_path = None
        self.reply_downloaded = False
        self.playback_deadline = 0.
        self.wake_recoveries = 0
        self.wake_renewals = 0
        self.wake_last_recovery_reason = None
        self.wake_flow_started_at = 0.
        self.last_progress_at = time.monotonic()
        self.diagnostic = False
        self.playback_finished = asyncio.Event()
        self.playback_success = None
        self.last_capture = None
        self.capture_sources = {"wake_word": 0, "followup": 0, "button_or_device": 0}
        self.last_capture_source = None
        self.wake_verification_audio = None
        self.wake_rejected = 0
        self.wake_silent_rejected = 0
        self.wake_error = None
        self.wake_phrases = None
        self.wake_armed = False
        self.false_alarms = 0
        self.wake_gate = None
        self.wake_session = None
        self.wake_monitor = None
        self.wake_last_audio = 0.
        self.micro_peak = 0
        self.micro_rms = 0.
        self.micro_zero_since = None
        self.wake_last_attempt = 0.
        self.wake_restart_lock = asyncio.Lock()
        self.va_active = False
        self.wake_primed = False
        self.bell_active = False
        self.bell_test = False
        self.bell_error = None

    def status(self):
        return {"enabled": self.config is not None, "connected": self.connected,
                "phase": self.phase, "error": self.error, "device": self.device_name,
                "room": self.config.room if self.config else None,
                "captures": self.captures, "turns": self.turns,
                "audio_bytes_received": self.audio_bytes,
                "micro_signal": {"peak": self.micro_peak, "rms": self.micro_rms,
                    "zero_seconds": round(time.monotonic() - self.micro_zero_since, 1)
                    if self.micro_zero_since is not None else 0},
                "audio_downloads": self.tickets.downloads, "last_timings": self.last_timings,
                "playback_state": getattr(self, "media_state", None),
                "progressive_tts": bool(self.config and self.config.progressive_tts and self.speak_blocks),
                "stt_test_armed": self.stt_test_until > time.monotonic(),
                "speech_detector": getattr(self.vad_factory, "name", "test-energy"),
                "last_capture": self.last_capture,
                "capture_sources": dict(self.capture_sources),
                "last_capture_source": self.last_capture_source,
                "wake_rejected": self.wake_rejected,
                "wake_silent_rejected": self.wake_silent_rejected,
                "wake_recoveries": self.wake_recoveries,
                "wake_renewals": self.wake_renewals,
                "last_recovery_reason": self.wake_last_recovery_reason,
                "wake_word": self.wake_status(),
                "health": self.health(),
                "bell": {"active": self.bell_active, "test": self.bell_test,
                         "error": self.bell_error},
                "transport": "esphome-native-direct", "raw_audio_saved": False}

    def begin_conversation_display(self):
        self.conversation_display = {"id": uuid.uuid4().hex, "revision": 0,
                                     "transcript": "", "answer": "", "error": None,
                                     "state": "processing"}
        self.conversation_display_until = time.monotonic() + 900

    def observe_conversation(self, event):
        if self.conversation_display is None:
            return
        kind = event.get("type")
        if kind not in ("transcript", "delta", "answer", "done", "error"):
            return
        value = dict(self.conversation_display)
        if kind == "transcript":
            value["transcript"] = event.get("text", "")
        elif kind == "delta":
            value["answer"] += event.get("text", "")
        elif kind in ("answer", "done"):
            value["answer"] = event.get("text", "")
            value["sources"] = event.get("sources", [])
            if kind == "done":
                value["state"] = "waiting_for_command" if event.get("mode") == "wake_empty" else "finished"
        else:
            value["error"] = event.get("message", "La demande n’a pas pu être terminée.")
            value["state"] = "finished"
        value["revision"] += 1
        self.conversation_display = value
        self.conversation_display_until = time.monotonic() + 900

    def finish_wake_followup(self):
        if (self.conversation_display or {}).get("state") == "waiting_for_command":
            self.observe_conversation({"type": "done", "text": "Aucune demande après le mot d’appel."})

    def conversation_text(self):
        if time.monotonic() >= self.conversation_display_until:
            self.conversation_display = None
        elif (self.phase in ("idle", "waking", "disconnected") and self.capture is None
              and (self.turn is None or self.turn.done())):
            self.finish_wake_followup()
            if (self.conversation_display or {}).get("state") == "processing":
                self.observe_conversation({"type": "error", "message": "Échange interrompu."})
        return {"available": self.conversation_display is not None,
                "exchange": self.conversation_display}

    def wake_status(self):
        """Etat du mot d'appel : aucun score brut ne quitte le processus."""
        detector = self.wake_detector
        if detector is None:
            return {"enabled": False, "armed": False, "error": self.wake_error}
        counters = detector.status()
        receiving = (self.wake_armed and self.connected and not self.capture and self.phase == "waking"
                     and self.wake_last_audio > 0
                     and time.monotonic() - self.wake_last_audio < 6)
        receiving_since = (self.wake_flow_started_at if receiving else None)
        return {"enabled": True, "armed": self.wake_armed, "receiving": receiving,
                "receiving_seconds": (round(time.monotonic() - receiving_since, 1)
                                      if receiving_since else 0),
                "last_audio_age_seconds": (round(time.monotonic() - self.wake_last_audio, 1)
                                            if self.wake_last_audio else None),
                "name": getattr(self.config, "wake_name", "alfred"),
                "engine": getattr(detector, "name", "openwakeword"),
                "phrase": self.wake_phrases[0] if self.wake_phrases else None,
                "inferences": counters.get("inferences", 0),
                "last_ms": counters.get("last_ms", 0),
                "busy": counters.get("busy", False),
                "latched": counters.get("latched", False),
                "pending": counters.get("pending", False),
                "speech_active": counters.get("speech_active"),
                "vad_probability": counters.get("vad_probability"),
                "energy_fallbacks": counters.get("energy_fallbacks", 0),
                "verification": getattr(self.config, "wake_verify", True),
                "detections": counters["detections"], "last_wake_at": counters["last_detection"],
                "threshold": counters["threshold"], "false_alarms": self.false_alarms,
                "error": self.wake_error or counters.get("error")}

    def health(self):
        """Petit bilan exploitable sans contenu audio ni texte privé."""
        now = time.monotonic()
        counters = self.wake_detector.status() if self.wake_detector else {}
        detector_stalled = bool(self.wake_armed and self.phase in ("idle", "waking")
                                and not self.capture and counters.get("latched")
                                and now - counters.get("last_detection", now) >= 6)
        components = {
            "transport": ("connecting" if not self.connected else "ok"),
            "microphone": ("paused" if self.capture or self.phase not in ("idle", "waking")
                           else "idle" if not self.wake_armed else "ok" if self.wake_last_audio
                           and now - self.wake_last_audio < 6 else "stalled"),
            "detector": ("disabled" if self.wake_detector is None else
                         "stalled" if detector_stalled else
                         "ok" if self.wake_armed and not self.wake_error else
                         "degraded" if self.wake_armed else "inactive"),
            "playback": ("playing" if self.phase in ("playing", "test_playing") else "idle"),
        }
        degraded = bool(self.wake_armed and self.wake_error) or detector_stalled
        return {"status": "degraded" if degraded else "ok" if self.connected or self.config is None
                else "connecting",
                "components": components,
                "phase": self.phase,
                "last_progress_age_seconds": round(now - self.last_progress_at, 1),
                "recovery_reason": self.wake_last_recovery_reason,
                "error": (type(self.error).__name__ if isinstance(self.error, Exception) else self.error)}

    async def start(self):
        if self.config:
            self.worker = asyncio.create_task(self._run())

    async def close(self):
        self.stopping.set()
        self.wake_armed = False
        if self.bell_active and self.connected and self.client:
            with suppress(Exception):
                await self.set_bell(False)
        for task in (self.turn, self.watchdog, self.worker, self.wake_session, self.wake_monitor):
            if task:
                task.cancel()
        await asyncio.gather(*[t for t in (self.turn, self.watchdog, self.worker,
                                           self.wake_session, self.wake_monitor) if t],
                             return_exceptions=True)
        self.wake_session = None
        self.wake_gate = None
        if self.client:
            with suppress(Exception):
                await self.client.disconnect()
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        self.capture = None
        self.stt_result = None
        self.stt_test_until = 0
        self.stt_test_pending = False
        self.tickets.items.clear()
        self.connected = False

    async def _run(self):
        try:
            from aioesphomeapi import APIClient, MediaPlayerInfo
            # Charger avant d'ouvrir l'écoute, pas pendant les premiers mots.
            await asyncio.to_thread(self.vad_factory)
            if self.config.wake_word and self.wake_detector is None and not self.wake_error:
                self.wake_error = "Détecteur non chargé"
            self.server = await asyncio.start_server(self._http, self.config.media_host,
                                                    self.config.media_port, limit=8192)
            while not self.stopping.is_set():
                disconnected = asyncio.Event()

                async def lost(expected):
                    disconnected.set()

                try:
                    self.peer = await asyncio.to_thread(socket.gethostbyname, self.config.host)
                    if not ipaddress.ip_address(self.peer).is_private:
                        raise ValueError("Adresse non locale")
                    self.client = APIClient(self.peer, 6053, None, client_info="Alfred direct")
                    await asyncio.wait_for(self.client.connect(on_stop=lost, login=True), 10)
                    info = await self.client.device_info()
                    if info.mac_address.lower() != self.config.expected_mac.lower():
                        raise ValueError("Identité du terminal différente")
                    if not info.voice_assistant_feature_flags & 4:
                        raise ValueError("Audio API non pris en charge")
                    entities, services = await self.client.list_entities_services()
                    self.services = {s.name: s for s in services}
                    self.media_key = next(x.key for x in entities if isinstance(x, MediaPlayerInfo))
                    self.leds.attach(entities)
                    self.device_name = info.name
                    self.connected, self.phase, self.error = True, "idle", None
                    if self.bell_active:
                        # Le son peut avoir survécu à une coupure TCP. Le couper
                        # avant toute nouvelle évaluation, sans supposer son état.
                        with suppress(Exception):
                            await self.set_bell(False)
                    unsubscribe = self.client.subscribe_voice_assistant(
                        handle_start=self._start_capture, handle_stop=self._stop_capture,
                        handle_audio=self._audio, handle_announcement_finished=self._announcement_finished)
                    self.client.subscribe_states(self._state)
                    if self.wake_armed:
                        self.wake_primed = self.va_active = False
                        await self._rearm_wake_word()
                    try:
                        if self.leds.ring is None:
                            await disconnected.wait()
                        else:
                            await self.leds.track(self, disconnected)
                    finally:
                        with suppress(Exception):
                            unsubscribe()
                except asyncio.CancelledError:
                    raise
                except Exception as error:
                    self.error = type(error).__name__
                finally:
                    self.connected, self.phase = False, "disconnected"
                    if getattr(self.wake_test, "capture_only", False):
                        await self.wake_test.finish("flux_interrompu")
                    self.leds.detach()
                    self.wake_last_audio = 0.
                    self.capture = None
                    self.expect_followup = False
                    self.finish_wake_followup()
                    for task in (self.turn, self.watchdog):
                        if task:
                            task.cancel()
                    if self.client:
                        with suppress(Exception):
                            await self.client.disconnect()
                try:
                    await asyncio.wait_for(self.stopping.wait(), 3)
                except asyncio.TimeoutError:
                    pass
        except asyncio.CancelledError:
            raise
        except Exception as error:
            self.error, self.phase = type(error).__name__, "unavailable"

    def _event(self, name, data=None):
        from aioesphomeapi import VoiceAssistantEventType
        if self.connected:
            self.client.send_voice_assistant_event(
                getattr(VoiceAssistantEventType, "VOICE_ASSISTANT_" + name), data)

    def _state(self, state):
        from aioesphomeapi import MediaPlayerEntityState
        self.leds.observe(state)
        if isinstance(state, MediaPlayerEntityState) and state.key == self.media_key:
            self.media_state = state.state.name if state.state is not None else "UNKNOWN"
            if self.phase == "test_playing" and self.media_state == "IDLE":
                self.phase = "idle"

    async def _announcement_finished(self, result):
        self.playback_success = result.success
        self.playback_finished.set()
        self.playback_deadline = 0.
        if self.phase == "rearming":
            return
        if self.phase in ("playing", "test_playing"):
            self.phase = "idle"
        # La carte peut ouvrir la fenêtre de reprise après la lecture.
        # Le superviseur relance seulement si aucune prise ne suit.
        if self.expect_followup:
            self.wake_last_attempt = time.monotonic()
        else:
            await self._rearm_wake_word()

    async def _rearm_wake_word(self, reset_session=False, reason="restart"):
        """Le firmware repasse en IDLE après une réponse : relancer la veille."""
        if not self.wake_armed or not self.connected or self.capture:
            return
        async with self.wake_restart_lock:
            if not self.wake_armed or not self.connected or self.capture:
                return
            if reset_session:
                # start_va est ignoré tant que le firmware n'est pas IDLE.
                # Terminer la session et laisser sa boucle arrêter le micro.
                self.phase = "rearming"
                self.expect_followup = False
                self._event("INTENT_END", {"continue_conversation": "0"})
                self._event("RUN_END")
                if "stop_va" in self.services:
                    try:
                        async with asyncio.timeout(5):
                            await self.client.execute_service(self.services["stop_va"], {})
                    except Exception as error:
                        self.wake_error = "Arrêt impossible : " + type(error).__name__
                        self.wake_last_attempt = time.monotonic()
                        self.phase = "idle"
                        return
                await asyncio.sleep(.3)
                if not self.wake_armed or not self.connected or self.capture:
                    return
                if reason != "renewal":
                    self.wake_recoveries += 1
            self.wake_primed = self.va_active = False
            if self.wake_gate:
                self.wake_gate.preroll.clear()
                reset = getattr(self.wake_detector, "reset_audio", None)
                if reset:
                    reset()
            self.wake_last_audio = 0.
            self.micro_zero_since = None
            self.wake_last_attempt = time.monotonic()
            self.expect_followup = False
            try:
                async with asyncio.timeout(5):
                    await self.client.execute_service(self.services["start_va"], {})
            except Exception as error:
                self.wake_error = "Relance impossible : " + type(error).__name__
                self.phase = "idle"
            else:
                # Le flux n'est confirmé que par la réception de trames.
                self.phase = "waking"
                self.wake_error = "En attente du flux micro"

    async def _monitor_wake_word(self):
        while self.wake_armed:
            await asyncio.sleep(2)
            await self._check_wake_word()

    async def _check_wake_word(self):
        if not self.wake_armed or not self.connected or self.capture:
            return
        now = time.monotonic()
        # Une notification de fin de lecture perdue ne doit pas laisser
        # le détecteur suspendu pour toujours. Attendre la fin du producteur
        # et une marge sur la durée réelle avant toute récupération.
        if self.phase == "playing":
            if (not self.playback_deadline or now < self.playback_deadline
                    or (self.turn and not self.turn.done())):
                return
            self.playback_deadline = 0.
            self.phase = "idle"
        if self.phase not in ("idle", "waking"):
            return
        if self.expect_followup and now - self.wake_last_attempt < 8:
            return
        detector = self.wake_detector
        counters = detector.status() if detector else {}
        # Des octets micro ne prouvent pas que le détecteur peut accepter un
        # nouveau réveil. Un verrou de détection orphelin ignore tout l'audio.
        if (counters.get("latched") and now - counters.get("last_detection", now) >= 6
                and now - self.wake_last_attempt >= 6
                and (self.turn is None or self.turn.done())):
            self.wake_last_recovery_reason = "detector_latched"
            await self._rearm_wake_word(reset_session=True, reason="detector_latched")
            return
        renewal = now - self.wake_last_attempt >= max(30, getattr(self.config, "wake_session_seconds", 900) - 10)
        stalled = now - self.wake_last_audio >= 6 and now - self.wake_last_attempt >= 6
        if renewal:
            self.wake_renewals += 1
            self.wake_last_recovery_reason = "renewal"
        elif stalled:
            self.wake_last_recovery_reason = "micro_stalled"
        if renewal or stalled:
            self.wake_error = "Flux micro absent : tentative de relance"
            await self._rearm_wake_word(reset_session=True,
                                        reason="renewal" if renewal else "micro_stalled")

    async def _start_capture(self, conversation_id, flags, audio_settings, wake_word):
        # Une nouvelle activation annule le calcul précédent, sans rejouer d'action.
        for task in (self.turn, self.watchdog):
            if task and task is not asyncio.current_task():
                task.cancel()
        followup = self.expect_followup and not wake_word
        self.expect_followup = False
        if self.wake_armed and self.wake_gate is not None:
            if followup:
                # Reprise de conversation : vraie prise, la carte streame déjà.
                self.wake_primed = True
                return self._open_capture(followup=True)
            if self.wake_primed:
                # Veille déjà amorcée : ce start_va vient de K2, il ouvre une prise.
                return self._open_capture(followup=False)
            # Amorçage de la veille : la carte streame pour le détecteur.
            self.va_active = self.wake_primed = True
            self.phase = "waking"
            return 0  # port 0 : le client répond par VoiceAssistantResponse, la carte streame
        self.wake_primed = False
        return self._open_capture(followup)

    def _open_capture(self, followup=False):
        """Ouvre une vraie prise, avec ou sans veille active."""
        if self.wake_test:
            return None
        if getattr(self.wake_detector, "name", None) == "stt":
            self.wake_detector.reset_audio()
        try:
            self.capture = Capture(self.vad_factory())
        except Exception as error:
            self.error = type(error).__name__
            self.phase = "idle"
            return None
        # Même un test expiré consomme l'activation comme diagnostic : ne pas
        # transformer une phrase de test tardive en commande de maison.
        self.capture_test = self.stt_test_pending
        self.capture_test_expired = self.capture_test and self.stt_test_until <= time.monotonic()
        self.stt_test_pending = False
        self.stt_test_until = 0
        source = "followup" if followup else "button_or_device"
        self.last_capture_source = source
        self.capture_sources[source] += 1
        self.captures += 1
        self.phase, self.error = "listening", None
        self._event("RUN_START")
        self._event("STT_START")
        self.watchdog = asyncio.create_task(self._capture_timeout(8 if followup else 30))
        return 0  # API_AUDIO : le PCM arrive sur la connexion TCP, sans port UDP.

    async def _capture_timeout(self, delay):
        await asyncio.sleep(delay)
        if self.capture:
            if self.capture.speaking:
                await self._finish_capture()
            else:
                self.capture = None
                if self.wake_verification_audio is not None:
                    self.wake_silent_rejected += 1
                    self.wake_verification_audio = None
                self.phase = "idle"
                self.finish_wake_followup()
                self._event("INTENT_END", {"continue_conversation": "0"})
                self._event("RUN_END")
                await self._rearm_wake_word()

    async def _audio(self, data, second_channel=None):
        self.audio_bytes += len(data)
        if data and len(data) % 2 == 0:
            import numpy as np
            samples = np.frombuffer(data, dtype="<i2").astype("int32")
            self.micro_peak = int(np.max(np.abs(samples)))
            self.micro_rms = round(float(np.sqrt(np.mean(samples.astype("float64") ** 2))), 1)
            if self.micro_peak:
                self.micro_zero_since = None
            elif self.micro_zero_since is None:
                self.micro_zero_since = time.monotonic()
        if self.wake_gate is not None and not self.capture:
            # Veille : on ne transmet au détecteur que hors lecture, pour que le
            # haut-parleur de la carte ne se déclenche pas lui-même.
            if self.phase in ("idle", "waking"):
                self.wake_last_audio = time.monotonic()
                self.phase = "waking"
                self.wake_error = None
                if not self.wake_flow_started_at:
                    self.wake_flow_started_at = self.wake_last_audio
                self.last_progress_at = self.wake_last_audio
                if getattr(self.wake_test, "capture_only", False):
                    await self.wake_test.observe(data)
                    return
                detected = self.wake_gate.feed(data)
                if self.wake_test:
                    self.wake_test.observe(data)
                if detected:
                    await self._wake_detected()
            return
        if not self.capture:
            return
        if self.diagnostic:
            return  # Test de transport : aucune transcription ni action.
        if self.wake_verification_audio is not None:
            remaining = RATE * 2 * 4 - len(self.wake_verification_audio)
            if remaining > 0:
                self.wake_verification_audio.extend(data[:remaining])
        started, done = self.capture.feed(data)
        self.last_progress_at = time.monotonic()
        if started:
            self.phase = "recording"
            self._event("STT_VAD_START")
            if self.watchdog:
                self.watchdog.cancel()
            self.watchdog = asyncio.create_task(self._capture_timeout(29))
        if done:
            await self._finish_capture()

    async def _finish_capture(self):
        if not self.capture:
            return
        capture, self.capture = self.capture, None
        verification, self.wake_verification_audio = self.wake_verification_audio, None
        if self.watchdog and self.watchdog is not asyncio.current_task():
            self.watchdog.cancel()
        if not capture.speaking:
            self.finish_wake_followup()
            if verification is not None:
                self.wake_silent_rejected += 1
            self._event("RUN_END")
            self.phase = "idle"
            await self._rearm_wake_word()
            return
        self.phase = "processing"
        self.last_capture = {"end_reason": capture.end_reason or "device_end_or_timeout",
                             "audio_ms": round(len(capture.data) / 32),
                             "detector": getattr(self.vad_factory, "name", "test-energy")}
        trace = self._claim_light_trace(capture) if not self.capture_test else None
        self._event("STT_VAD_END")
        operation = (self._transcribe_test(capture.wav(), self.capture_test_expired)
                     if self.capture_test else self._verify_wake_then_process(capture.wav(), verification)
                     if verification is not None else self._process(capture.wav()))
        self.capture_test = False
        self.turn = asyncio.create_task(self._trace_light_turn(operation, trace) if trace else operation)

    def arm_light_trace(self):
        if (not self.connected or self.phase not in ("idle", "waking")
                or self.capture or self.expect_followup or self.wake_test):
            raise ValueError("Attendez que le terminal connecté revienne en veille.")
        if self.light_trace and self.light_trace.snapshot()["state"] in ("armed", "captured"):
            raise ValueError("Un essai est déjà en cours.")
        self.light_trace = LightTrace()
        self.light_trace_reply = None
        return self.light_trace.snapshot()

    def _claim_light_trace(self, capture, reason=None):
        trace = self.light_trace
        if trace and trace.snapshot()["state"] == "armed":
            if trace.claim(time.perf_counter(), capture.last_voice_at,
                           reason or capture.end_reason or "device_end_or_timeout"):
                return trace
        return None

    async def _trace_light_turn(self, operation, trace):
        token = ACTIVE_TRACE.set(trace)
        try:
            await operation
        except asyncio.CancelledError:
            trace.finish("cancelled")
            raise
        except Exception:
            trace.finish("error")
            raise
        finally:
            ACTIVE_TRACE.reset(token)

    def _trace_audio_request(self, path):
        reply = self.light_trace_reply
        if reply and reply[0] == path:
            reply[1].finish("complete", "audio_requested")

    async def _stop_capture(self, abort):
        if self.phase == "rearming":
            return  # Réponse à notre arrêt de session, pas une nouvelle commande.
        if not abort:
            await self._finish_capture()
            return
        if self.capture and self.capture.speaking and not self.capture_test:
            trace = self._claim_light_trace(self.capture, "cancelled")
            if trace:
                trace.finish("cancelled")
        self.capture = None
        self.wake_verification_audio = None
        self.expect_followup = False
        self.finish_wake_followup()
        for task in (self.turn, self.watchdog):
            if task:
                task.cancel()
        self.phase = "idle"
        self._event("INTENT_END", {"continue_conversation": "0"})
        self._event("RUN_END")
        await self._rearm_wake_word()

    async def _verify_wake_then_process(self, wav, audio):
        """Confirmer localement le nom avant toute conversation ou action."""
        sample = io.BytesIO()
        with wave.open(sample, "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(RATE)
            output.writeframes(audio)
        try:
            if self.transcribe is None:
                raise RuntimeError("Vérification vocale indisponible")
            with measure("wake_verification"):
                text, _, _ = await asyncio.to_thread(self.transcribe, sample.getvalue())
            name = getattr(self.config, "wake_name", "alfred")
            if self.wake_phrases:
                from alfred.wake_settings import strip_prefix
                accepted = strip_prefix(text, self.wake_phrases)[1]
            else:
                accepted = bool(re.search(r"\b" + re.escape(name) + r"\b", text, flags=re.IGNORECASE))
        except asyncio.CancelledError:
            raise
        except Exception:
            accepted = False
            self.wake_error = "Vérification du réveil indisponible"
        if accepted:
            await self._process(wav)
            return
        if trace := ACTIVE_TRACE.get():
            trace.finish("wake_rejected")
        self.wake_rejected += 1
        self.phase = "idle"
        self._event("INTENT_END", {"continue_conversation": "0"})
        self._event("RUN_END")
        await self._rearm_wake_word()

    def arm_stt_test(self):
        if not self.connected or self.phase != "idle" or self.transcribe is None:
            raise ValueError("Terminal absent ou occupé")
        self.stt_result = None
        self.stt_test_pending = True
        self.stt_test_until = time.monotonic() + 60
        return {"armed": True, "expires_in_seconds": 60}

    async def start_wake_word(self, *, wait_for_connection=False):
        """Ouvre une veille continue sur la carte ; aucun second départ requis ensuite."""
        allowed = ("idle", "connecting", "disconnected") if wait_for_connection else ("idle",)
        if (not self.connected and not wait_for_connection) or self.phase not in allowed:
            raise ValueError("Terminal absent ou occupé")
        if not self.wake_detector:
            raise ValueError("Mot d'appel non configuré")
        if self.wake_armed:
            return {"armed": True, "already": True}
        self.wake_gate = WakeGate(self.wake_detector)
        self.wake_armed = True
        self.wake_error = None
        self.wake_last_attempt = time.monotonic()
        self.wake_last_audio = 0.
        self.wake_flow_started_at = 0.
        self.last_progress_at = time.monotonic()
        if self.connected:
            try:
                await self.client.execute_service(self.services["start_va"], {})
            except Exception as error:
                # Une réponse perdue ne prouve pas l'absence de démarrage : la veille
                # reste armée et se contente d'attendre les premières trames.
                self.wake_error = type(error).__name__
        self.wake_monitor = asyncio.create_task(self._monitor_wake_word())
        seconds = getattr(self.config, "wake_session_seconds", 900)
        return {"armed": True, "expires_in_seconds": seconds}

    def stop_wake_word(self, reason="stopped"):
        if self.wake_detector:
            reset = getattr(self.wake_detector, "reset_audio", None)
            if reset:
                reset()
        self.wake_armed = False
        self.wake_gate = None
        self.wake_error = None
        self.wake_primed = False
        self.va_active = False
        self.wake_last_audio = 0.
        self.wake_flow_started_at = 0.
        if self.wake_monitor:
            self.wake_monitor.cancel()
            self.wake_monitor = None
        if self.wake_session:
            self.wake_session.cancel()
            self.wake_session = None
        if self.phase in ("idle", "waking") and self.connected:
            with suppress(Exception):
                self._event("INTENT_END", {"continue_conversation": "0"})
                self._event("RUN_END")
        if self.connected:
            self.phase = "idle"
        return {"armed": False, "reason": reason}

    def _restart_wake_session(self):
        """La carte borne une session : la renouveler avant son expiration."""
        if self.wake_session:
            self.wake_session.cancel()
        if not self.wake_armed:
            self.wake_session = None
            return
        seconds = getattr(self.config, "wake_session_seconds", 900)
        self.wake_session = asyncio.create_task(
            self._wake_session_loop(max(30, seconds - 10)))

    async def _wake_session_loop(self, delay):
        await asyncio.sleep(delay)
        if not self.wake_armed or not self.connected:
            return
        try:
            await self.client.execute_service(self.services["start_va"], {})
        except Exception as error:
            self.wake_error = type(error).__name__
        else:
            self._restart_wake_session()

    async def _wake_detected(self, stt_audio=None):
        """Le mot ouvre la prise suivante sans repartir : la carte streame déjà."""
        if self.wake_test:
            self.wake_test.detected()
            return True
        if self.wake_journal:
            event = {'source': 'wake', 'event': 'detected',
                     'engine': getattr(self.wake_detector, 'name', None),
                     'phrase': self.wake_phrases[0] if self.wake_phrases else None,
                     'detector': self.wake_detector.status(),
                     'peak': self.micro_peak, 'rms': self.micro_rms}
            async def write_event():
                try:
                    await asyncio.to_thread(self.wake_journal.append, event)
                except Exception:
                    pass
            asyncio.create_task(write_event())
        if (not self.wake_gate or not self.wake_armed or self.capture
                or self.phase not in ("idle", "waking")):
            return False
        preroll = self.wake_gate.take()
        if stt_audio is not None:
            preroll = stt_audio
        self.wake_verification_audio = (bytearray(preroll)
                                        if getattr(self.config, "wake_verify", True) else None)
        self.last_capture_source = "wake_word"
        self.capture_sources["wake_word"] += 1
        self.phase, self.error = "waking", None
        self.captures += 1
        # RUN_START a déjà amorcé le flux ; on signale le début de transcription.
        self._event("STT_START")
        self._event("STT_VAD_START")
        try:
            self.capture = Capture(self.vad_factory())
        except Exception as error:
            self.wake_error, self.phase = type(error).__name__, "idle"
            return False
        self.capture_test = False
        self.capture_test_expired = False
        self.expect_followup = False
        # La pré-capture contient déjà le mot et la première syllabe de la commande.
        if preroll:
            if stt_audio is not None:
                # Silero doit recevoir ses petites trames successives : un seul
                # bloc comprenant la pause perdrait l'amorce de parole.
                for offset in range(0, len(preroll), 1024):
                    self.capture.feed(preroll[offset:offset+1024])
            else:
                self.capture.feed(preroll[-int(.6 * RATE) * 2:])
        if self.watchdog:
            self.watchdog.cancel()
        # Ne pas rester trente secondes en prise après un bruit sans parole.
        self.watchdog = asyncio.create_task(self._capture_timeout(6))
        return True

    async def start_stt_test(self):
        self.arm_stt_test()
        try:
            await self.client.execute_service(self.services["start_va"], {})
        except Exception:
            # Une réponse perdue ne prouve pas que la carte n'a pas démarré.
            # Garder l'intention diagnostic pour toute activation tardive.
            self.stt_test_until = 0
            raise
        return {"started": True, "actions_executed": False}

    def stt_test_result(self):
        if self.stt_result is not None:
            return {"available": True, **self.stt_result}
        return {"available": False, "armed": self.stt_test_until > time.monotonic()}

    def _expire_stt_result(self, result):
        if self.stt_result is result:
            self.stt_result = None

    async def _transcribe_test(self, audio, expired=False):
        try:
            if expired:
                self.stt_result = {"error": "Test expiré : relancez-le depuis la page.",
                                   "actions_executed": False, "raw_audio_saved": False}
                asyncio.get_running_loop().call_later(120, self._expire_stt_result, self.stt_result)
                self.phase = "idle"
                self._event("RUN_END")
                return
            text, duration, elapsed = await asyncio.to_thread(self.transcribe, audio)
            result = {"text": text, "input_seconds": round(duration, 2), "stt_ms": elapsed,
                      "actions_executed": False, "raw_audio_saved": False}
            result["capture_end"] = (self.last_capture or {}).get("end_reason")
        except asyncio.CancelledError:
            raise
        except Exception as error:
            self.error = type(error).__name__
            result = {"error": "Transcription impossible. Réessayez une fois le moteur disponible.",
                      "actions_executed": False, "raw_audio_saved": False}
        self.stt_result = result
        asyncio.get_running_loop().call_later(120, self._expire_stt_result, result)
        self.expect_followup = False
        self.phase = "idle"
        self._event("INTENT_END", {"continue_conversation": "0"})
        self._event("RUN_END")

    async def _process(self, wav):
        started = time.perf_counter()
        trace = ACTIVE_TRACE.get()
        self.begin_conversation_display()
        exchange_id = self.conversation_display["id"]
        try:
            if self.speak_blocks and self.config.progressive_tts:
                operation = self.process(wav, self.session_id, self.config.floor_id, True)
            else:
                operation = self.process(wav, self.session_id, self.config.floor_id)
            result = await asyncio.wait_for(operation, 90)
            if result.get("mode") in {"wake_rejected", "request_failed"}:
                if trace:
                    trace.finish(result["mode"])
                if result["mode"] == "wake_rejected":
                    self.wake_rejected += 1
                else:
                    self.leds.flash_error()
                self.error = None
                self.phase = "idle"
                self.expect_followup = False
                self._event("INTENT_END", {"continue_conversation": "0"})
                self._event("RUN_END")
                await self._rearm_wake_word()
                return
            if result.get("mode") == "wake_empty":
                if trace:
                    trace.finish("wake_empty")
                self._open_capture(followup=True)
                if self.capture is None:
                    self.finish_wake_followup()
                    return
                if self.watchdog:
                    self.watchdog.cancel()
                self.watchdog = asyncio.create_task(self._capture_timeout(6))
                return
            self.observe_conversation({"type": "transcript", "text": result.get("transcript", "")})
            self.observe_conversation({"type": "answer", "text": result["text"]})
            self._event("STT_END", {"text": result.get("transcript") or "Parole reçue"})
            self._event("INTENT_START")
            if result.get("deferred_tts") and self.speak_blocks:
                await self._stream_reply(result, started)
                return
            needs_reply = result.get("needs_reply") is True
            audio = base64.b64decode(result["audio_base64"], validate=True)
            conversion_started = time.perf_counter()
            path = self.tickets.put(await asyncio.to_thread(playback_audio, audio))
            conversion_ms = round((time.perf_counter() - conversion_started) * 1000)
            with wave.open(io.BytesIO(audio), "rb") as source:
                reply_audio_ms = round(source.getnframes() / source.getframerate() * 1000)
            self.reply_started, self.reply_path, self.reply_downloaded = started, path, False
            if trace:
                self.light_trace_reply = path, trace
                trace.mark("audio_ready")
            self.last_timings = {**(result.get("timings") or {}),
                                 "conversion_ms": conversion_ms,
                                 "capture_finished_to_reply_ms": round((time.perf_counter() - started) * 1000),
                                 "reply_characters": len(result["text"]),
                                 "reply_audio_ms": reply_audio_ms}
            self.expect_followup = needs_reply
            self._event("INTENT_END", {"conversation_id": self.session_id,
                                       "continue_conversation": "1" if needs_reply else "0"})
            self._event("TTS_START", {"text": result["text"]})
            self._event("TTS_END", {"url": self._url(path)})
            self._event("RUN_END")

            self.phase = "playing"
            self.playback_deadline = time.monotonic() + max(30, reply_audio_ms / 1000 + 15)
            self.last_progress_at = time.monotonic()
            self.turns += 1
        except asyncio.CancelledError:
            display = self.conversation_display or {}
            if display.get("id") == exchange_id and display.get("state") == "processing" and not display.get("answer"):
                self.observe_conversation({"type": "done", "text": "Échange interrompu."})
            raise
        except Exception as error:
            if trace:
                trace.finish("timeout" if isinstance(error, TimeoutError) else "error")
            self.error, self.phase = type(error).__name__, "idle"
            if not self.conversation_display.get("error"):
                self.observe_conversation({"type": "error", "message": "La demande n’a pas pu être terminée. Vérifiez avant de répéter une action."})
            self.expect_followup = False
            self._event("INTENT_END", {"continue_conversation": "0"})
            self._event("ERROR", {"code": "alfred-error", "message": "La demande n'a pas pu être terminée. Vérifiez avant de répéter une action."})
            self._event("RUN_END")

    async def _stream_reply(self, result, started, *, test=False):
        needs_reply = result.get("needs_reply") is True
        stream = StreamingFlac()
        path = self.tickets.put_stream(stream)
        metrics = {**result.get("timings", {}), "audio_blocks": 0, "trimmed_silence_ms": 0,
                   "reply_characters": len(result["text"]), "progressive": True}
        self.last_timings = metrics
        self.reply_started, self.reply_path, self.reply_downloaded = started, path, False
        if trace := ACTIVE_TRACE.get():
            self.light_trace_reply = path, trace

        async def produce():
            blocks = speech_blocks(result["text"])
            iterator = self.speak_blocks(blocks)
            total_ms = 0
            pending = None
            try:
                while True:
                    with (measure("tts_first_block") if not metrics["audio_blocks"] else nullcontext()):
                        pending = asyncio.create_task(asyncio.to_thread(next, iterator, None))
                        item = await asyncio.shield(pending)
                    pending = None
                    if item is None:
                        break
                    audio, elapsed = item
                    total_ms += elapsed
                    audio, removed_ms = await asyncio.to_thread(
                        trim_block_edges, audio, first=metrics["audio_blocks"] == 0,
                        last=metrics["audio_blocks"] == len(blocks) - 1)
                    metrics["trimmed_silence_ms"] += removed_ms
                    await asyncio.to_thread(stream.feed, audio)
                    metrics["audio_blocks"] += 1
                    if metrics["audio_blocks"] == 1:
                        metrics["tts_first_block_ms"] = elapsed
                await asyncio.to_thread(stream.finish)
                metrics["tts_ms"] = total_ms
                metrics["reply_audio_ms"] = round(stream.samples / 48)
                metrics["capture_finished_to_all_audio_ms"] = round((time.perf_counter() - started) * 1000)
            except BaseException as error:
                stream.fail(error)
                raise
            finally:
                # Un calcul natif déjà engagé ne peut pas être interrompu, mais
                # aucun bloc suivant ni aucune action ne doit être rejoué.
                if pending:
                    with suppress(Exception):
                        await pending
                iterator.close()

        producer = asyncio.create_task(produce())
        try:
            await asyncio.wait_for(stream.ready.wait(), 30)
            if stream.error or not stream.data:
                await producer
                raise ValueError("Aucun bloc audio")
            mark("audio_ready")
            metrics["capture_finished_to_reply_ms"] = round((time.perf_counter() - started) * 1000)
            self.expect_followup = needs_reply
            self._event("INTENT_END", {"conversation_id": self.session_id,
                                       "continue_conversation": "1" if needs_reply else "0"})
            self._event("TTS_START", {"text": result["text"]})
            self._event("TTS_END", {"url": self._url(path)})
            self._event("RUN_END")
            self.phase = "playing"
            self.playback_deadline = time.monotonic() + 120
            self.last_progress_at = time.monotonic()
            if not test:
                self.turns += 1
            await producer
            if self.phase == "playing":
                self.playback_deadline = time.monotonic() + max(30, metrics.get("reply_audio_ms", 0) / 1000 + 15)
        finally:
            if not producer.done():
                producer.cancel()
            await asyncio.gather(producer, return_exceptions=True)

    def _url(self, path):
        return f"http://{self.config.media_host}:{self.config.media_port}{path}"

    async def test_progressive(self):
        if not self.connected or self.phase != "idle" or self.speak_blocks is None:
            raise ValueError("Terminal absent, occupé ou flux indisponible")
        text = ("Bonjour. Je suis Alfred, votre assistant pour la maison. "
                "Cette réponse est lue progressivement pendant que je prépare la suite. "
                "Vous pouvez me demander de consulter vos rappels ou de préparer votre liste de courses. "
                "Je reste à votre disposition.")
        self.playback_finished.clear()
        self.playback_success = None
        self.phase = "test_preparing"
        try:
            await self._stream_reply({"text": text, "timings": {}}, time.perf_counter(), test=True)
            await asyncio.wait_for(self.playback_finished.wait(), 45)
            return {"finished": self.playback_success, "timings": self.last_timings}
        finally:
            self.phase = "idle"

    async def test(self):
        if not self.connected or self.phase not in ("idle", "test_playing"):
            raise ValueError("Terminal absent ou occupé")
        from alfred.voice import SAMPLE_TEXT
        audio, elapsed = await asyncio.to_thread(self.speak, SAMPLE_TEXT)
        url = self._url(self.tickets.put(await asyncio.to_thread(playback_audio, audio)))
        self.phase = "test_playing"
        before = self.tickets.downloads
        try:
            response = await self.client.send_voice_assistant_announcement_await_response(
                url, timeout=35, text=SAMPLE_TEXT)
            return {"accepted": True, "finished": response.success,
                    "audio_downloaded": self.tickets.downloads > before, "tts_ms": elapsed}
        except Exception as error:
            from aioesphomeapi import MediaPlayerCommand
            self.error = type(error).__name__
            self.client.media_player_command(self.media_key, command=MediaPlayerCommand.STOP,
                                             announcement=True)
            raise
        finally:
            self.phase = "idle"

    async def set_bell(self, active):
        """Active ou coupe la sonnerie native, sans passer par Home Assistant."""
        if not self.config or not self.connected or self.client is None:
            raise ValueError("Terminal absent ou déconnecté.")
        service = self.services.get("start_ringing" if active else "stop_ringing")
        if service is None:
            raise ValueError("Service de sonnerie absent du firmware.")
        if self.bell_active == active:
            return
        try:
            await self.client.execute_service(service, {})
        except Exception:
            self.bell_error = "Commande de sonnerie non confirmée."
            raise
        self.bell_active = active
        self.bell_error = None

    async def test_bell(self, seconds=2.5):
        """Fait sonner brièvement la carte, sans perturber un minuteur réel."""
        if self.bell_test:
            raise ValueError("Un test de sonnerie est déjà en cours.")
        if self.bell_active:
            raise ValueError("Une sonnerie est déjà active.")
        self.bell_test = True
        try:
            await self.set_bell(True)
            await asyncio.sleep(seconds)
        finally:
            self.bell_test = False
            with suppress(Exception):
                await self.set_bell(False)

    async def test_microphone(self):
        if not self.connected or self.phase != "idle":
            raise ValueError("Terminal absent ou occupé")
        before = self.audio_bytes
        self.diagnostic = True
        try:
            await self.client.execute_service(self.services["start_va"], {})
            await asyncio.sleep(2)
        finally:
            with suppress(Exception):
                await self.client.execute_service(self.services["stop_va"], {})
            self.capture = None
            if self.watchdog:
                self.watchdog.cancel()
            self.diagnostic = False
            self.phase = "idle"
        received = self.audio_bytes - before
        return {"audio_bytes_received": received, "pcm_seconds": round(received / 32000, 2),
                "transcribed": False, "raw_audio_saved": False}

    async def _http(self, reader, writer):
        try:
            peer = writer.get_extra_info("peername")
            header = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), 3)
            method, path, _ = header.split(b"\r\n", 1)[0].decode("ascii").split(" ")
            audio = self.tickets.get(path) if peer and peer[0] == self.peer else None
            if isinstance(audio, StreamingFlac):
                if not audio.done:
                    await self._stream_http(writer, method, path, audio)
                    return
                audio = None if audio.error else bytes(audio.data)
            if method not in ("GET", "HEAD") or audio is None:
                writer.write(b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
            else:
                # ESPHome relit les en-têtes/portions du fichier avec HTTP Range.
                start, end = 0, len(audio) - 1
                partial = re.search(rb"\r\nRange: bytes=(\d+)-(\d*)\r\n", header, re.I)
                if partial:
                    start = int(partial[1])
                    end = min(int(partial[2]) if partial[2] else end, end)
                    if not 0 <= start <= end:
                        writer.write(b"HTTP/1.1 416 Range Not Satisfiable\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
                        await writer.drain()
                        return
                body = audio[start:end + 1]
                status = "206 Partial Content" if partial else "200 OK"
                content_range = f"Content-Range: bytes {start}-{end}/{len(audio)}\r\n" if partial else ""
                writer.write((f"HTTP/1.1 {status}\r\nContent-Type: audio/flac\r\n"
                              f"Content-Length: {len(body)}\r\n{content_range}"
                              "Accept-Ranges: bytes\r\nCache-Control: no-store\r\n"
                              "Connection: close\r\n\r\n").encode())
                if method == "GET":
                    if path == self.reply_path and not self.reply_downloaded:
                        self.reply_downloaded = True
                        self._trace_audio_request(path)
                        if self.last_timings is not None and self.reply_started is not None:
                            self.last_timings["capture_finished_to_audio_request_ms"] = round(
                                (time.perf_counter() - self.reply_started) * 1000)
                    writer.write(body)
                    self.tickets.downloads += 1
            await asyncio.wait_for(writer.drain(), 5)
        except (OSError, ValueError, RuntimeError, asyncio.TimeoutError, asyncio.IncompleteReadError,
                asyncio.LimitOverrunError):
            pass
        finally:
            writer.close()
            with suppress(OSError):
                await writer.wait_closed()

    async def _stream_http(self, writer, method, path, stream):
        if method not in ("GET", "HEAD"):
            writer.write(b"HTTP/1.1 405 Method Not Allowed\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
            return
        writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: audio/flac\r\n"
                     b"Transfer-Encoding: chunked\r\nCache-Control: no-store\r\nConnection: close\r\n\r\n")
        if method == "HEAD":
            await writer.drain()
            return
        self.tickets.downloads += 1
        if path == self.reply_path and not self.reply_downloaded:
            self.reply_downloaded = True
            self._trace_audio_request(path)
            if self.last_timings is not None:
                self.last_timings["capture_finished_to_audio_request_ms"] = round(
                    (time.perf_counter() - self.reply_started) * 1000)
                self.last_timings["blocks_ready_at_audio_request"] = stream.blocks
                self.last_timings["all_audio_ready_at_request"] = stream.done
        async for data in stream.chunks():
            writer.write(f"{len(data):x}\r\n".encode() + data + b"\r\n")
            await asyncio.wait_for(writer.drain(), 10)
        writer.write(b"0\r\n\r\n")
        await writer.drain()
