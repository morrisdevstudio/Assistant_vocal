"""API de prototype : locale, sans identité vocale ni connexion à la maison."""

import asyncio
import queue as stdlib_queue
import logging
import base64
import json
import re
import threading
from uuid import uuid4
from contextlib import asynccontextmanager, nullcontext, suppress
from contextvars import ContextVar
from datetime import datetime, timedelta
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlsplit

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, SecretStr, StrictBool, field_validator, model_validator
from starlette.middleware.trustedhost import TrustedHostMiddleware

from alfred import __version__
from alfred.config import Settings
from alfred.diagnostics import Diagnostics
from alfred.intents import IntentService, LIGHT_ON_ROOM
from alfred.intent_context import CURRENT_TURN
from alfred.light_trace import ACTIVE_TRACE, measure
from alfred.storage import ProcessLock, Store, utc_now
from alfred.timers import TimerService
from alfred.shopping import Shopping
from alfred.announcements import Announcements, announce_reply
from alfred.reminder_actions import ReminderActions
from alfred.reminder_dispatch import ReminderDispatcher
from alfred.calendar_reminder_monitor import CalendarReminderMonitor
from alfred.ha_calendar import CalendarBindings, CalendarClient, parse_reminder_marker
from alfred.calendar_actions import CalendarActions
from alfred.bells import BellController, TerminalBellController, read_targets
from alfred.voice import (MAX_AUDIO_BYTES, InvalidAudio, VoiceBusy, VoiceService,
                          VoiceUnavailable, validate_wav)
from alfred.conversation import ConversationCancelled, ConversationError, ConversationService
from alfred.credentials import ConfigurationError, CredentialStore, DEFAULT_MODEL
from alfred.internet import InternetService, InternetError
from alfred.home_assistant import (HomeBusy, HomeError, HomeService, HomeStore,
                                   command_reply)
from alfred.home_catalog import HomeCatalog, CatalogError
from alfred.tts_text import prepare_tts_text
from alfred.early_speech import take_complete_sentence
from alfred.audio_stream import StreamingFlac
from alfred.music import PLAYER_PATTERN, Music, music_reply
from alfred.music_actions import MusicActions
from alfred.profiles import Profiles, cosine
from alfred.speaker import MODEL_REPOSITORY, SpeakerBusy, SpeakerService, SpeakerUnavailable
from alfred.voice_identity import VoiceIdentity
from alfred.terminal_leds import DEFAULT_COLORS, LedEffect, LedPhase
from alfred.terminal import DirectTerminal, TerminalConfig
from alfred.wake_manager import WakeManager
from alfred.wake_routes import install_wake_routes
from alfred.wake_settings import strip_prefix

logger = logging.getLogger("alfred")
STATIC = Path(__file__).parent / "static"
terminal_observer = ContextVar("terminal_observer", default=None)


class ScheduleInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    kind: Literal["timer", "reminder"]
    title: str = Field(min_length=1, max_length=160)
    floor_id: Literal["rdc", "etage1"]
    terminal_id: str = Field(min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    target_room: str | None = Field(default=None, min_length=1, max_length=80)
    duration_seconds: int | None = Field(default=None, ge=1, le=604800, strict=True)
    due_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def valid_time(self):
        if self.kind == "timer":
            if self.duration_seconds is None or self.due_at is not None:
                raise ValueError("Un minuteur demande une durée, sans date d'échéance.")
        elif self.due_at is None or self.duration_seconds is not None:
            raise ValueError("Un rappel demande une échéance avec fuseau, sans durée.")
        return self


class FloorInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    floor_id: Literal["rdc", "etage1"]


class ReminderInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=160)
    due_at: AwareDatetime
    floor_id: Literal["rdc", "etage1"]
    target_room: str = Field(min_length=1, max_length=80)
    audience: Literal["personal", "family"] = "personal"
    recurrence: Literal["once", "weekly"] = "once"
    owner_id: str | None = Field(default=None, max_length=64)

    @model_validator(mode="after")
    def valid_audience(self):
        if (self.audience == "personal") != bool(self.owner_id):
            raise ValueError("Sélectionnez un profil pour un rappel personnel seulement.")
        return self


class SpeechInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    text: str = Field(min_length=1, max_length=500)


class VoiceConfigInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    voice: str = Field(pattern=r"^phonon-(?:dumby|alfred|arnaud|lucien)-cpu$")


AIModelId = Annotated[str, Field(min_length=3, max_length=160,
                                pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._:/-]*$")]


class AIModelInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    model: AIModelId


class AIModelUpdate(AIModelInput):
    action: Literal["add", "select"]


class AIConfigInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    api_key: SecretStr | None = None
    model: AIModelId = DEFAULT_MODEL

    @field_validator("api_key")
    @classmethod
    def validate_key(cls, value):
        if value is not None:
            text = value.get_secret_value()
            if not 16 <= len(text) <= 512 or not text.isascii() or any(char.isspace() for char in text):
                raise ValueError("Clé invalide.")
        return value


class SessionInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    session_id: str = Field(min_length=16, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")


class InternetConfigInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    api_key: SecretStr | None = None
    location_id: int | None = Field(default=None, ge=1)
    clear_location: bool = False
    credit_limit: int = Field(default=1000, ge=0, le=1000)

    @field_validator("api_key")
    @classmethod
    def validate_key(cls, value):
        if value is not None:
            text = value.get_secret_value()
            if not 16 <= len(text) <= 512 or not text.isascii() or any(c.isspace() for c in text):
                raise ValueError("Clé invalide.")
        return value


class ChatInput(SessionInput):
    text: str = Field(min_length=1, max_length=4000)
    floor_id: Literal["rdc", "etage1"] | None = None
    speak: bool | None = None
    allow_internet: bool = True


class HomeTextInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    text: str = Field(min_length=1, max_length=4000)
    session_id: str | None = Field(default=None, min_length=16, max_length=80,
                                   pattern=r"^[A-Za-z0-9_-]+$")


class MusicConfigInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    entity_id: str = Field(pattern=r"^media_player\.[a-z0-9_]+$", max_length=255)
    duck_percent: int | None = Field(default=None, ge=5, le=80)
    default_playlist: dict | None = None
    clear_playlist: bool = False

    @field_validator("default_playlist")
    @classmethod
    def valid_playlist(cls, value):
        if value is None:
            return value
        if set(value) != {"uri", "name", "provider"} or not all(
                isinstance(value[k], str) and 1 <= len(value[k]) <= 500 for k in value):
            raise ValueError("Playlist par défaut invalide.")
        if not re.match(r"^[a-z][a-z0-9+.-]*://", value["uri"]):
            raise ValueError("Référence de playlist invalide.")
        return value


class MusicPlayInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    query: str = Field(min_length=1, max_length=160)
    media_type: Literal["artist", "album", "track", "playlist", "radio"] = "artist"
    artist: str | None = Field(default=None, min_length=1, max_length=80)
    entity_id: str | None = Field(default=None, pattern=f"^{PLAYER_PATTERN}$", max_length=255)


class MusicControlInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["pause", "resume", "stop", "next", "previous", "volume_up", "volume_down", "seek"]
    position: float | None = Field(default=None, ge=0, le=86400, allow_inf_nan=False)
    entity_id: str | None = Field(default=None, pattern=f"^{PLAYER_PATTERN}$", max_length=255)


class TimerInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=160)
    duration_seconds: int = Field(ge=1, le=604800, strict=True)
    floor_id: Literal["rdc", "etage1"]


class FamilyReminderInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=160)
    due_at: AwareDatetime
    target_room: str = Field(min_length=1, max_length=80)
    floor_id: Literal["rdc", "etage1"]


class ShoppingConfigInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    entity_id: str = Field(pattern=r"^todo\.[a-z0-9_]+$", max_length=255)


class ShoppingItemInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    item: str = Field(min_length=1, max_length=120)


class ShoppingRenameInput(ShoppingItemInput):
    new_name: str = Field(min_length=1, max_length=120)


class ShoppingDeleteInput(ShoppingItemInput):
    confirm_delete: Literal[True]


class ShoppingPurgeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirm_delete: Literal[True]


class AnnouncementInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    message: str = Field(min_length=1, max_length=300)
    scope: Literal["house", "floor", "room"] = "house"
    target: str | None = Field(default=None, max_length=80)


class HomeDeviceTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(max_length=255, pattern=r"^[a-z_]+\.[a-z0-9_]+$")


class TerminalLedInput(BaseModel):
    colors: dict[LedPhase, Annotated[str, Field(pattern=r"^#[0-9a-fA-F]{6}$")] | None] = Field(default_factory=dict)
    effects: dict[LedPhase, LedEffect] = Field(default_factory=dict)


HomeDeviceField = Literal["allowed", "confirmation_required", "aliases", "alfred_name", "alfred_area", "light_type"]


class HomeDeviceSetting(HomeDeviceTarget):
    setting: HomeDeviceField
    value: StrictBool | list[str] | str


class HomeDeviceChanges(HomeDeviceTarget):
    settings: dict[HomeDeviceField, StrictBool | list[str] | str] = Field(min_length=1)
    local_room: str | None = Field(default=None, min_length=1, max_length=60)


class HomeConfigInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    base_url: str = Field(min_length=8, max_length=200)
    token: SecretStr | None = None
    room: str = Field(default="Bureau", min_length=1, max_length=60)

    @field_validator("base_url")
    @classmethod
    def valid_url(cls, value):
        parsed = urlsplit(value)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise ValueError("Adresse Home Assistant invalide.")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("Adresse Home Assistant invalide.")
        return value.rstrip("/")

    @field_validator("token")
    @classmethod
    def valid_token(cls, value):
        if value is not None:
            text = value.get_secret_value()
            if not 20 <= len(text) <= 512 or not text.isascii() or any(c.isspace() for c in text):
                raise ValueError("Jeton invalide.")
        return value

    @field_validator("room")
    @classmethod
    def valid_room(cls, value):
        if not all(ch.isalnum() or ch in " -'" for ch in value):
            raise ValueError("Nom de pièce invalide.")
        return value


class ProfileInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=40)
    role: Literal["adult", "child"] = "adult"


class ProfileNameInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=40)


def load_wake_detector(settings, config):
    """Charge le détecteur une fois ; l'échec est signalé sans bloquer Alfred."""
    from alfred.wake_word import WakeWordDetector, verify_preprocess
    models = settings.models_dir or settings.data_dir.parent / "models"
    folder = models / "wake-word"
    model = folder / config.wake_model
    try:
        verify_preprocess(folder)
        if not model.is_file():
            raise FileNotFoundError("Modèle de mot d'appel absent : " + model.name)
        return WakeWordDetector(model, folder, threshold=config.wake_threshold), None
    except Exception as error:
        logger.error("Mot d'appel indisponible (%s)", type(error).__name__)
        return None, type(error).__name__


def create_app(settings: Settings | None = None, voice_service=None, conversation_service=None,
               home_service=None, speaker_service=None, calendar_service=None):
    settings = settings or Settings.from_env()
    store = Store(settings.data_dir)
    timers = TimerService(store)
    home = home_service or HomeService(HomeStore(settings.data_dir, settings.ha_url,
                                                  settings.ha_token, settings.ha_room))
    voice = voice_service or VoiceService(
        settings.models_dir or settings.data_dir.parent / "models",
        voice_file=settings.data_dir / "voice.json",
    )
    def voice_metadata():
        metadata = getattr(voice, "metadata", None)
        return metadata() if callable(metadata) else {}
    credentials = CredentialStore(settings.data_dir, settings.command_code_api_key, settings.command_code_model)
    conversation = conversation_service or ConversationService(credentials)
    internet = InternetService(settings.data_dir)
    if isinstance(conversation, ConversationService):
        conversation.internet = internet
    shopping = Shopping(home, settings.data_dir)
    announcements = Announcements(home, settings.data_dir)
    music = Music(home, settings.data_dir)
    intents = IntentService(home, settings.data_dir)
    intents.timers = timers
    intents.music_actions = MusicActions(home, music)
    diagnostics = Diagnostics(settings.data_dir)
    home.intent_service = intents
    if isinstance(conversation, ConversationService):
        conversation.intents = intents
    profiles = Profiles(store, settings.data_dir / "profiles")
    calendar_bindings = CalendarBindings(settings.data_dir)
    try:
        bindings = calendar_bindings.load()
        calendar_entities = set(bindings["personal"].values()) | ({bindings["family"]} if bindings["family"] else set())
        calendar_client = calendar_service or CalendarClient(home, calendar_entities)
    except HomeError:
        calendar_client = None
    if isinstance(conversation, ConversationService):
        conversation.shopping = shopping
        conversation.announcements = announcements
        conversation.music = music
        if settings.legacy_reminders:
            conversation.reminders = ReminderActions(store, profiles, announcements)
        elif calendar_client:
            conversation.reminders = ReminderActions(store, profiles, announcements, calendars=calendar_client, bindings=calendar_bindings)
            conversation.calendar_actions = CalendarActions(calendar_client, calendar_bindings, profiles)
    speaker = speaker_service or SpeakerService(
        settings.models_dir or settings.data_dir.parent / "models")
    voice_identity = VoiceIdentity(profiles, speaker, settings.data_dir)
    workers = set()
    cancellation_flags = set()

    @asynccontextmanager
    async def lifespan(app):
        with nullcontext() if home_service is not None else home.connection_pool():
            async with run_service(app):
                yield

    @asynccontextmanager
    async def run_service(app):
        lock = ProcessLock(settings.data_dir)
        lock.acquire()
        task = None
        bell_task = None
        direct_bell_task = None
        music_task = None
        reminder_task = None
        calendar_task = None
        diagnostic_task = None
        app.state.terminal_config_error = None
        stop_bells = asyncio.Event()
        stop_music = asyncio.Event()
        stop_reminders = asyncio.Event()
        stop_calendars = asyncio.Event()
        try:
            store.initialize()
            app.state.scheduler_ok = False
            app.state.recovered = store.recover(include_reminders=settings.legacy_reminders)
            try:
                targets = read_targets(settings.data_dir / "bell-targets.json")
                app.state.bell_config_error = None
            except ValueError as error:
                targets = []
                app.state.bell_config_error = str(error)
                logger.error("Configuration de sonnerie invalide")
            bell = BellController(store, home, targets)
            bell.initialize()
            app.state.bell = bell
            app.state.scheduler_ok = True
            app.state.last_tick = None
            if callable(getattr(voice, "preload_stt", None)):
                try:
                    await asyncio.to_thread(voice.preload_stt)
                except Exception:
                    logger.warning("Chargement du moteur de transcription impossible")
            if hasattr(voice, "warmup"):
                def warm_voice():
                    try:
                        voice.warmup()
                    except Exception:
                        logger.warning("Chargement de la voix impossible")
                threading.Thread(target=warm_voice, daemon=True, name="alfred-voice-warmup").start()

            async def run_scheduler():
                state = app.state
                while True:
                    try:
                        # Transaction locale courte ; reste dans cette tâche pour
                        # garantir sa fin avant de libérer le verrou au shutdown.
                        store.tick(include_reminders=settings.legacy_reminders)
                        state.last_tick = utc_now().isoformat()
                        state.scheduler_ok = True
                    except Exception:
                        state.scheduler_ok = False
                        logger.exception("Erreur de l'ordonnanceur")
                    await asyncio.sleep(settings.poll_seconds)

            task = asyncio.create_task(run_scheduler())

            async def run_bells():
                while not stop_bells.is_set():
                    try:
                        await asyncio.to_thread(bell.sync)
                    except Exception:
                        logger.exception("Erreur du service de sonnerie")
                    try:
                        await asyncio.wait_for(stop_bells.wait(), timeout=0.5)
                    except asyncio.TimeoutError:
                        pass

            bell_task = asyncio.create_task(run_bells())

            async def run_music_duck_expiry():
                while not stop_music.is_set():
                    try:
                        await asyncio.to_thread(music.expire_duck)
                    except Exception:
                        logger.exception("Restauration du volume musical impossible")
                    try:
                        await asyncio.wait_for(stop_music.wait(), timeout=1)
                    except asyncio.TimeoutError:
                        pass

            music_task = asyncio.create_task(run_music_duck_expiry())

            async def purge_diagnostics():
                while not stop_music.is_set():
                    try:
                        # Purge aussi lorsque personne ne converse avec Alfred.
                        await asyncio.to_thread(diagnostics.list, 1)
                    except Exception:
                        logger.warning("Purge du journal de diagnostic indisponible")
                    try:
                        await asyncio.wait_for(stop_music.wait(), timeout=60)
                    except asyncio.TimeoutError:
                        pass

            diagnostic_task = asyncio.create_task(purge_diagnostics())

            dispatcher = ReminderDispatcher(store, announcements)
            async def run_reminder_dispatch():
                while not stop_reminders.is_set():
                    try:
                        await asyncio.to_thread(dispatcher.sync)
                    except Exception:
                        logger.exception("Erreur du service de diffusion des rappels")
                    try:
                        await asyncio.wait_for(stop_reminders.wait(), timeout=1)
                    except asyncio.TimeoutError:
                        pass

            if settings.legacy_reminders:
                reminder_task = asyncio.create_task(run_reminder_dispatch())
            if calendar_client and not settings.legacy_reminders:
                app.state.calendar_monitor = CalendarReminderMonitor(store, calendar_client, calendar_bindings, announcements)
                try:
                    await asyncio.to_thread(app.state.calendar_monitor.sync, True)
                    initial_recovery = False
                except Exception:
                    logger.error("Initialisation du suivi des calendriers indisponible")
                    initial_recovery = True
                async def run_calendar_monitor():
                    first = initial_recovery
                    while not stop_calendars.is_set():
                        try:
                            await asyncio.to_thread(app.state.calendar_monitor.sync, first)
                            first = False
                        except Exception:
                            logger.error("Suivi des calendriers indisponible")
                        try:
                            await asyncio.wait_for(stop_calendars.wait(), timeout=3)
                        except asyncio.TimeoutError:
                            pass
                calendar_task = asyncio.create_task(run_calendar_monitor())
            try:
                terminal_config = TerminalConfig.load(settings.data_dir / "terminal.json")
            except (OSError, ValueError, TypeError):
                terminal_config = None
                app.state.terminal_config_error = "Configuration du terminal invalide."
            wake_detector, wake_error = None, None
            if terminal_config is not None and terminal_config.wake_word:
                wake_detector, wake_error = load_wake_detector(settings, terminal_config)
            app.state.terminal = DirectTerminal(terminal_config, process_terminal_audio, voice.speak,
                                               getattr(voice, "speak_blocks", None),
                                               getattr(voice, "transcribe", None),
                                               wake_detector=wake_detector,
                                               led_path=settings.data_dir / "terminal-leds.json")
            app.state.terminal.wake_error = wake_error
            app.state.terminal.wake_journal = diagnostics
            app.state.wake_manager = WakeManager(settings, voice, app.state.terminal)
            wake_manager = app.state.wake_manager
            if terminal_config and wake_manager.preferences.path.exists():
                try:
                    wake_manager.configure_terminal(await wake_manager.prepare("esp32"))
                except Exception:
                    app.state.terminal.wake_error = "Moteur de réveil enregistré indisponible."
                    app.state.terminal.wake_detector = None
            await app.state.terminal.start()
            await wake_manager.restore_terminal()
            if terminal_config is not None and not targets:
                app.state.direct_bell = TerminalBellController(
                    store, app.state.terminal, terminal_config.floor_id)

                async def run_direct_bells():
                    while not stop_bells.is_set():
                        try:
                            await app.state.direct_bell.sync()
                        except Exception:
                            logger.exception("Erreur de la sonnerie directe")
                        try:
                            await asyncio.wait_for(stop_bells.wait(), timeout=0.5)
                        except asyncio.TimeoutError:
                            pass

                direct_bell_task = asyncio.create_task(run_direct_bells())
            yield
        finally:
            if bell_task:
                stop_bells.set()
                await bell_task
            if direct_bell_task:
                stop_bells.set()
                await direct_bell_task
            if bell_task:
                try:
                    await asyncio.to_thread(app.state.bell.sync, True)
                except Exception:
                    logger.exception("Arrêt de sonnerie non confirmé")
            if hasattr(app.state, "direct_bell"):
                try:
                    await app.state.direct_bell.sync(True)
                except Exception:
                    logger.exception("Arrêt de la sonnerie directe non confirmé")
            if hasattr(app.state, "terminal"):
                session = getattr(app.state.terminal, 'wake_test', None)
                if session:
                    await session.finish('service_arrete')
                await app.state.wake_manager.stop_browser("Service arrêté.")
                detector = getattr(app.state.terminal, "wake_detector", None)
                if detector and hasattr(detector, "reset_audio"):
                    detector.reset_audio()
                await app.state.terminal.close()
            for flag in cancellation_flags.copy():
                flag.set()
            if workers:
                await asyncio.gather(*workers.copy(), return_exceptions=True)
            if task:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
            if reminder_task:
                stop_reminders.set()
                await reminder_task
            if music_task:
                stop_music.set()
                await music_task
            if diagnostic_task:
                stop_music.set()
                await diagnostic_task
            if calendar_task:
                stop_calendars.set()
                await calendar_task
            if callable(getattr(voice, "close", None)):
                await asyncio.to_thread(voice.close)
            lock.release()

    app = FastAPI(title="Alfred — prototype local", version=__version__, lifespan=lifespan)
    app.state.music = music
    app.state.intents = intents
    app.state.diagnostics = diagnostics

    async def process_terminal_audio(audio, session_id, floor_id, defer_tts=False):
        """Même parcours applicatif que le navigateur, sans requête LAN ni duplication des outils."""
        import httpx
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                    base_url="http://127.0.0.1") as client:
            token = terminal_observer.set(app.state.terminal.observe_conversation)
            from alfred.home_assistant import HOME_ROOM
            config = app.state.terminal.config
            room_token = HOME_ROOM.set(config.room if config else None)
            try:
                response = await client.post("/api/conversation/voice", content=audio, headers={
                    "Content-Type": "audio/wav", "X-Alfred-Session": session_id,
                    "X-Alfred-Floor": floor_id, "X-Alfred-Wake-Source": "esp32",
                    "X-Alfred-Wake-Strict": "1" if app.state.terminal.last_capture_source == "wake_word" else "0"},
                    params={"defer_tts": "true" if defer_tts else "false"})
            finally:
                terminal_observer.reset(token)
                HOME_ROOM.reset(room_token)
            response.raise_for_status()
            transcript = ""
            result = None
            for line in response.text.splitlines():
                event = json.loads(line)
                if event["type"] == "transcript":
                    transcript = event.get("text", "")
                elif event["type"] == "error":
                    if event.get("code") in {"wake_rejected", "request_failed"}:
                        return {"mode": event["code"]}
                    raise VoiceUnavailable("Le traitement vocal du terminal a échoué.")
                elif event["type"] == "done":
                    result = {**event, "transcript": transcript, "deferred_tts": defer_tts}
            if result is None:
                raise VoiceUnavailable("Réponse du terminal incomplète.")
            return result
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=[
        "localhost", "127.0.0.1", "[::1]", "testserver", settings.listen_host])

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exception):
        if request.url.path in ("/api/ai/config", "/api/home/config", "/api/internet/config"):
            # Ne jamais renvoyer le contenu du champ clé dans une erreur Pydantic.
            return JSONResponse({"detail":"Configuration invalide : vérifiez la clé et l'identifiant du modèle."}, status_code=422)
        if request.url.path in ("/api/ai/models", "/api/ai/models/test"):
            return JSONResponse({"detail": "Indiquez un identifiant de modèle valide (fournisseur/modèle)."}, status_code=422)
        return await request_validation_exception_handler(request, exception)

    @app.middleware("http")
    async def local_requests(request: Request, call_next):
        if request.url.path.startswith("/api/terminal/light-trace"):
            host = request.client.host if request.client else None
            if host not in ("127.0.0.1", "::1", settings.listen_host):
                return JSONResponse({"detail": "Lancez le banc sur le serveur Alfred."}, status_code=403)
        # Pas de CORS ; refuser aussi les écritures déclenchées depuis un autre site.
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            origin = request.headers.get("origin")
            if origin:
                parsed = urlsplit(origin)
                if parsed.netloc != request.headers.get("host") or parsed.scheme not in ("http", "https"):
                    return JSONResponse({"detail": "Origine non autorisée."}, status_code=403)
            audio_route = (request.url.path in ("/api/voice/turn", "/api/conversation/voice",
                                                "/api/profiles/identify")
                           or request.url.path.endswith("/enroll")
                           or request.url.path.startswith("/api/voice-identity/probe/"))
            expected_type = "audio/wav" if audio_route else "application/json"
            # Une suppression n'a pas de corps : rien à typer.
            if (request.method != "DELETE"
                    and request.headers.get("content-type", "").split(";")[0] != expected_type):
                return JSONResponse({"detail": f"Utiliser {expected_type}."}, status_code=415)
        response = await call_next(request)
        is_versioned_static = (request.method in ("GET", "HEAD")
                               and request.url.path.startswith("/static/")
                               and request.url.query)
        response.headers["Cache-Control"] = ("public, max-age=3600"
                                             if is_versioned_static else "no-store")
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "connect-src 'self'; media-src 'self' blob:; worker-src 'self'; "
            "img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'"
        )
        return response

    @app.get("/health")
    async def health():
        healthy = getattr(app.state, "scheduler_ok", False)
        return JSONResponse({"status": "ok" if healthy else "degraded", "version": __version__},
                            status_code=200 if healthy else 503)

    @app.get("/api/status")
    async def status():
        vocal = voice.status()
        bells = {**app.state.bell.status(), "configuration_error": app.state.bell_config_error}
        if hasattr(app.state, "direct_bell"):
            bells["direct"] = app.state.direct_bell.status()
        return {
            "version": __version__, "mode": "local-prototype", "server_time": utc_now().isoformat(),
            "scheduler_ok": app.state.scheduler_ok, "last_tick": app.state.last_tick,
            "recovered_on_start": app.state.recovered,
            "bells": bells,
            "capabilities": {"schedules": True, "stt": vocal["stt_available"], "tts": vocal["tts_available"],
                             "speaker_profiles": speaker.status()["available"],
                             "home_assistant": home.status().get("configured", False),
                             "music": music.configured(),
                             "command_code": conversation.status()["access_verified"],
                             "esp32": app.state.terminal.connected},
        }

    @app.get("/api/diagnostics")
    async def diagnostics_history(limit: int = 100):
        return await asyncio.to_thread(diagnostics.list, limit)

    @app.post("/api/wake-test/start")
    async def wake_test_start():
        from alfred.wake_test import WakeTest
        terminal = app.state.terminal
        manager = app.state.wake_manager
        async with manager.lock:
            if getattr(terminal, 'wake_test', None):
                raise HTTPException(409, "Un test est déjà en cours.")
            try:
                session = WakeTest(terminal, manager, diagnostics)
                await session.start()
                app.state.last_wake_test = session
                return session.snapshot()
            except (ValueError, IndexError) as error:
                raise HTTPException(409, str(error)) from error

    @app.get("/api/wake-test")
    async def wake_test_status():
        session = getattr(app.state, 'last_wake_test', None)
        return session.snapshot() if session else None

    @app.post("/api/wake-test/{action}")
    async def wake_test_action(action: str, request: Request):
        session = getattr(app.state, 'last_wake_test', None)
        if not session or session.closed:
            raise HTTPException(409, "Aucun test en cours.")
        payload = await request.json()
        if payload.get('id') != session.id or payload.get('number') != len(session.results)+1:
            raise HTTPException(409, "Cet essai est déjà terminé.")
        try:
            if action == 'missed': session.record('missed')
            elif action == 'retry': session.retry()
            elif action == 'ready': session.ready()
            elif action == 'skip': session.skip()
            elif action == 'stop': await session.finish('arrete')
            else: raise HTTPException(404, "Action inconnue.")
            return session.snapshot()
        except ValueError as error:
            raise HTTPException(409, str(error)) from error

    @app.get("/api/terminal/status")
    def terminal_status():
        health = getattr(app.state.terminal, "health", None)
        return {**app.state.terminal.status(),
                "health": health() if callable(health) else None,
                "configuration_error": app.state.terminal_config_error}

    @app.post("/api/terminal/light-trace", status_code=201)
    async def start_light_trace():
        terminal = app.state.terminal
        if not hasattr(terminal, "arm_light_trace"):
            raise HTTPException(503, "Terminal indisponible.")
        try:
            return terminal.arm_light_trace()
        except ValueError as error:
            raise HTTPException(409, str(error)) from error

    @app.get("/api/terminal/light-trace/{trace_id}")
    async def read_light_trace(trace_id: str):
        trace = getattr(app.state.terminal, "light_trace", None)
        if trace is None or trace.id != trace_id:
            raise HTTPException(404, "Essai introuvable.")
        return trace.snapshot()

    @app.delete("/api/terminal/light-trace/{trace_id}")
    async def finish_light_trace(trace_id: str):
        trace = getattr(app.state.terminal, "light_trace", None)
        if trace is None or trace.id != trace_id:
            raise HTTPException(404, "Essai introuvable.")
        trace.snapshot()
        trace.finish("measurement_stopped")
        return trace.snapshot()

    def terminal_led_payload(terminal):
        leds = terminal.leds
        observed = leds.observed
        return {"colors": leds.colors, "defaults": DEFAULT_COLORS,
                "effects": leds.effects, "effect_options": leds.effect_options(),
                "connected": terminal.connected, "supported": leds.ring is not None,
                "on": observed.state if observed is not None else None,
                "active_effect": observed.effect if observed is not None and observed.state else None}

    @app.get("/api/terminal/leds")
    async def terminal_led_settings():
        return terminal_led_payload(app.state.terminal)

    @app.post("/api/terminal/leds")
    async def save_terminal_leds(payload: TerminalLedInput):
        if not (payload.colors or payload.effects):
            raise HTTPException(422, "Choisissez une couleur ou un effet à enregistrer.")
        terminal = app.state.terminal
        try:
            terminal.leds.save(payload.colors, payload.effects)
        except OSError as error:
            raise HTTPException(503, "Impossible d’enregistrer les réglages LED du satellite.") from error
        return terminal_led_payload(terminal)

    @app.post("/api/terminal/stt-test")
    async def arm_terminal_stt_test(start: bool = False):
        try:
            if start:
                return await app.state.terminal.start_stt_test()
            return app.state.terminal.arm_stt_test()
        except Exception as error:
            raise HTTPException(409, "Terminal absent ou occupé.") from error

    @app.get("/api/terminal/conversation")
    async def terminal_conversation():
        return JSONResponse(app.state.terminal.conversation_text(),
                            headers={"Cache-Control": "no-store"})

    @app.post("/api/terminal/wake-word/start")
    async def start_wake_word():
        try:
            if isinstance(app.state.terminal, DirectTerminal):
                return await app.state.wake_manager.start_terminal()
            return await app.state.terminal.start_wake_word()
        except Exception as error:
            raise HTTPException(409, "Mot d'appel indisponible ou terminal occupé.") from error

    @app.post("/api/terminal/wake-word/stop")
    def stop_wake_word():
        if getattr(app.state.terminal, 'wake_test', None):
            raise HTTPException(409, "Arrêtez d'abord le test de réveil.")
        if isinstance(app.state.terminal, DirectTerminal):
            return app.state.wake_manager.stop_terminal()
        return app.state.terminal.stop_wake_word()

    @app.post("/api/terminal/wake-word/false-alarm")
    def mark_false_alarm():
        app.state.terminal.false_alarms += 1
        return {"false_alarms": app.state.terminal.false_alarms}

    @app.get("/api/terminal/stt-test/result")
    def terminal_stt_test_result():
        return JSONResponse(app.state.terminal.stt_test_result(), headers={"Cache-Control": "no-store"})

    @app.post("/api/terminal/test")
    async def terminal_test():
        try:
            return await app.state.terminal.test()
        except Exception as error:
            raise HTTPException(503, "Lecture sur le terminal impossible ou terminal occupé.") from error

    @app.post("/api/terminal/bell-test")
    async def terminal_bell_test():
        terminal = app.state.terminal
        if terminal.config is None or not terminal.connected:
            raise HTTPException(409, "Terminal absent ou déconnecté.")
        if any(item["status"] == "ringing"
               for item in store.active_timers(terminal.config.floor_id)):
            raise HTTPException(409, "Un minuteur sonne déjà sur ce terminal.")
        try:
            await terminal.test_bell()
        except Exception as error:
            raise HTTPException(503, "Test de sonnerie impossible ou terminal occupé.") from error
        return {"rang": True, "seconds": 2.5}

    @app.post("/api/terminal/test-microphone")
    async def terminal_test_microphone():
        try:
            return await app.state.terminal.test_microphone()
        except Exception as error:
            raise HTTPException(503, "Test micro impossible ou terminal occupé.") from error

    @app.post("/api/terminal/test-progressive")
    async def terminal_test_progressive():
        try:
            return await app.state.terminal.test_progressive()
        except Exception as error:
            raise HTTPException(503, "Lecture progressive non confirmée.") from error

    @app.get("/api/voice/status")
    def voice_status():
        return {**voice.status(), "conversation_ai": conversation.status()["configured"]}

    @app.post("/api/voice/config")
    def save_voice_config(payload: VoiceConfigInput):
        voice_call(voice.set_voice, payload.voice)
        return {**voice.status(), "conversation_ai": conversation.status()["configured"]}

    @app.get("/api/ai/config")
    def ai_config():
        return conversation.status()

    @app.post("/api/ai/models")
    def update_ai_models(payload: AIModelUpdate):
        try:
            credentials.update_model(payload.model, activate=payload.action == "select")
            return conversation.status()
        except ConfigurationError as error:
            raise HTTPException(422, str(error)) from error

    @app.post("/api/ai/models/test")
    def test_ai_model(payload: AIModelInput):
        try:
            result = None
            for event in conversation.stream("Réponds uniquement : Alfred est prêt.", uuid4().hex,
                                             threading.Event(), probe_model=payload.model):
                if event["type"] == "answer":
                    result = event
            if result is None:
                raise ConversationError("Aucune réponse complète reçue.")
            return {"ok": True, "model": result["model"], "llm_ms": result["llm_ms"]}
        except (ConversationError, ConfigurationError) as error:
            raise HTTPException(502, str(error)) from error

    app.state.internet = internet

    @app.get("/api/internet/config")
    def internet_config():
        return JSONResponse(internet.public(), headers={"Cache-Control": "no-store"})

    @app.post("/api/internet/config")
    def save_internet_config(payload: InternetConfigInput):
        try:
            return JSONResponse(internet.configure(
                key=payload.api_key.get_secret_value() if payload.api_key is not None else None,
                location_id=payload.location_id, clear_location=payload.clear_location,
                credit_limit=payload.credit_limit), headers={"Cache-Control": "no-store"})
        except (InternetError, ConfigurationError) as error:
            raise HTTPException(422, str(error)) from error

    @app.get("/api/internet/locations")
    def internet_locations(q: str):
        if not 2 <= len(q.strip()) <= 160:
            raise HTTPException(422, "Saisissez une commune entre deux et cent soixante caractères.")
        try:
            return JSONResponse({"results": internet.locations(q.strip())}, headers={"Cache-Control": "no-store"})
        except InternetError as error:
            raise HTTPException(502, str(error)) from error

    @app.post("/api/internet/check")
    def internet_check():
        try:
            result = internet.execute("rechercher_web", {"query": "site.tavily.com Tavily"}, threading.Event())
            return {"ok": bool(result["sources"]), **internet.public()}
        except (InternetError, ConfigurationError) as error:
            raise HTTPException(502, str(error)) from error

    @app.post("/api/ai/config")
    def save_ai_config(payload: AIConfigInput):
        try:
            key = payload.api_key.get_secret_value() if payload.api_key is not None else None
            result = credentials.save(key, payload.model)
            conversation.reset()
            return {**result, "access_verified": False}
        except ConfigurationError as error:
            raise HTTPException(422, str(error)) from error

    @app.post("/api/ai/check")
    def check_ai():
        stop = threading.Event()
        session = uuid4().hex
        try:
            result = None
            for event in conversation.stream("Réponds uniquement : Alfred est prêt.", session, stop):
                if event["type"] == "answer":
                    result = event
            if result is None:
                raise ConversationError("Aucune réponse complète reçue.")
            return {"ok":True, "model":result["model"], "usage":result["usage"], "llm_ms":result["llm_ms"]}
        except (ConversationError, ConfigurationError) as error:
            raise HTTPException(502, str(error)) from error
        finally:
            conversation.reset(session)

    @app.get("/api/home/config")
    def home_config():
        return home.status()

    @app.get("/api/home/catalog")
    def home_catalog():
        try:
            return home.catalog().snapshot()
        except (CatalogError, HomeError, ConfigurationError) as error:
            raise HTTPException(502, str(error)) from error

    @app.get("/api/home/devices")
    def home_devices(editable: bool = False):
        items = []
        catalog = home_catalog()
        for entity in catalog["entities"]:
            item = {
                "id": entity["entity_id"], "name": entity["name"], "device": entity["device"],
                "area": entity["area"], "domain": entity["domain"], "allowed": entity["allowed"],
                "unavailable": entity.get("state") == "unavailable",
            }
            if editable:
                item.update(ha_name=entity.get("ha_name", entity["name"]),
                            alfred_name=entity.get("alfred_name", ""),
                            ha_area=entity.get("ha_area", entity["area"]),
                            alfred_area=entity.get("alfred_area", ""))
                item.update({field: entity[field] for field in
                             ("supported", "capabilities", "confirmation_required", "aliases", "ha_aliases")})
                if entity["domain"] == "light":
                    item["light_type"] = entity.get("light_type", "main")
            items.append(item)
        if editable:
            return {"items": items, "rooms": catalog.get("rooms", []), "ha_rooms": catalog.get("ha_rooms", []),
                    "ha_room_floors": catalog.get("ha_room_floors", {})}
        return {"items": items}

    @app.patch("/api/home/devices")
    def update_home_device(payload: HomeDeviceSetting | HomeDeviceChanges):
        legacy = isinstance(payload, HomeDeviceSetting)
        changes = {payload.setting: payload.value} if legacy else payload.settings
        try:
            saved = home.catalog().settings.update(payload.id, changes, lambda: home_catalog().get("ha_rooms", []),
                                                    local_room=None if legacy else payload.local_room)
            return {"value": saved[payload.setting]} if legacy else {"settings": saved}
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        except OSError as error:
            raise HTTPException(500, "Impossible d’enregistrer les réglages domotiques.") from error

    @app.put("/api/home/exclusions")
    def home_exclusions(payload: list[str]):
        try:
            return {"excluded": home.catalog().settings.replace("excluded", payload)}
        except (ValueError, OSError) as error:
            raise HTTPException(422, str(error)) from error

    @app.put("/api/home/aliases")
    def home_aliases(payload: dict[str, list[str]]):
        try:
            return {"aliases": home.catalog().settings.replace("aliases", payload)}
        except (ValueError, OSError) as error:
            raise HTTPException(422, str(error)) from error

    @app.put("/api/home/confirmations")
    def home_confirmations(payload: list[str]):
        try:
            return {"confirmations": home.catalog().settings.replace("confirmations", payload)}
        except (ValueError, OSError) as error:
            raise HTTPException(422, str(error)) from error

    @app.post("/api/home/config")
    def save_home_config(payload: HomeConfigInput):
        try:
            token = payload.token.get_secret_value() if payload.token is not None else None
            return {**home.store.save(payload.base_url, token, payload.room), "verified": False}
        except ConfigurationError as error:
            raise HTTPException(422, str(error)) from error

    @app.post("/api/home/check")
    def check_home():
        try:
            return {"ok": True, **home.check()}
        except (HomeError, HomeBusy, ConfigurationError) as error:
            raise HTTPException(502, str(error)) from error

    @app.get("/api/shopping/config")
    def shopping_config():
        try:
            return {"entity_id": shopping.entity()}
        except HomeError as error:
            raise HTTPException(500, str(error)) from error

    @app.post("/api/shopping/config")
    def save_shopping_config(payload: ShoppingConfigInput):
        shopping.configure(payload.entity_id)
        return {"entity_id": payload.entity_id}

    @app.get("/api/shopping/items")
    def shopping_items(all_statuses: bool = False):
        try:
            return {"items": shopping.request("get_all" if all_statuses else "get_items")}
        except (HomeError, ConfigurationError) as error:
            raise HTTPException(502, str(error)) from error

    @app.get("/api/shopping/items/completed")
    def completed_shopping_items():
        try:
            return {"items": shopping.request("get_completed")}
        except (HomeError, ConfigurationError) as error:
            raise HTTPException(502, str(error)) from error

    @app.post("/api/shopping/items")
    def add_shopping_item(payload: ShoppingItemInput):
        try:
            result = shopping.request("add_item", payload.item)
            message = "Cet article est déjà dans la liste." if result["duplicate"] else "Article remis dans la liste." if result.get("restored") else "Ajout demandé à Home Assistant."
            return {"message": message, "duplicate": result["duplicate"], "restored": bool(result.get("restored"))}
        except (HomeError, ConfigurationError) as error:
            raise HTTPException(502, str(error)) from error

    @app.post("/api/shopping/items/complete")
    def complete_shopping_item(payload: ShoppingItemInput):
        try:
            result = shopping.request("complete_item", payload.item)
            return {"message": result["completed"] + " est coché dans la liste de courses."}
        except (HomeError, ConfigurationError) as error:
            raise HTTPException(502, str(error)) from error

    @app.post("/api/shopping/items/rename")
    def rename_shopping_item(payload: ShoppingRenameInput):
        try:
            result = shopping.request("rename_item", payload.item, payload.new_name)
            return {"message": result["old_name"] + " devient " + result["new_name"] + "."}
        except (HomeError, ConfigurationError) as error:
            raise HTTPException(502, str(error)) from error

    @app.post("/api/shopping/items/restore")
    def restore_shopping_item(payload: ShoppingItemInput):
        try:
            result = shopping.request("restore_item", payload.item)
            return {"message": result["restored"] + " est de nouveau dans la liste de courses."}
        except (HomeError, ConfigurationError) as error:
            raise HTTPException(502, str(error)) from error

    @app.post("/api/shopping/items/delete")
    def delete_shopping_item(payload: ShoppingDeleteInput):
        try:
            result = shopping.request("delete_item", payload.item)
            return {"message": result["deleted"] + " a été supprimé définitivement."}
        except (HomeError, ConfigurationError) as error:
            raise HTTPException(502, str(error)) from error

    @app.post("/api/shopping/items/purge")
    def purge_shopping_items(payload: ShoppingPurgeInput):
        try:
            result = shopping.request("purge_items")
            if result.get("incomplete"):
                return {"message": f"Purge non confirmée après {result['removed']} suppression(s). Vérifiez la liste avant de recommencer."}
            if result.get("remaining"):
                return {"message": f"{result['removed']} suppression(s) acceptée(s), mais {result['remaining']} article(s) restent."}
            return {"message": f"Liste purgée : {result['removed']} article(s) supprimé(s), cochés compris."}
        except (HomeError, ConfigurationError) as error:
            raise HTTPException(502, str(error)) from error

    @app.post("/api/home/command")
    def home_command(payload: HomeTextInput):
        import time
        started = time.monotonic()
        session = payload.session_id or "home-panel"
        turn = intents.context.begin(("home-api", session, "guest"), payload.text, threading.Event())
        token = CURRENT_TURN.set(turn)
        result = None
        try:
            result = home.handle(payload.text)
            if result is None:
                raise HTTPException(422, "Commande domotique non reconnue.")
            if result.get("error"):
                raise HTTPException(502, result["error"])
            return {**result, "exchange_id": turn.exchange_id, "execution": turn.result}
        finally:
            try:
                reply = (result or {}).get("reply", "")
                intents.context.finish(turn, reply)
                diagnostics.append({"exchange_id": turn.exchange_id, "source": "home-api", "transcript": payload.text,
                                    "answer": reply, "error": (result or {}).get("error") if result else "Commande domotique non reconnue.", "result": turn.result,
                                    "route": "local", "timings": {"total_ms": round((time.monotonic()-started)*1000)}})
            except Exception:
                logger.warning("Journal de diagnostic indisponible")
            CURRENT_TURN.reset(token)

    @app.get("/api/music/config")
    def music_config(entity_id: str | None = Query(default=None, pattern=f"^{PLAYER_PATTERN}$", max_length=255)):
        try:
            return music.status(entity_id)
        except (HomeError, ConfigurationError) as error:
            raise HTTPException(502, str(error)) from error

    @app.post("/api/music/config")
    def save_music_config(payload: MusicConfigInput):
        try:
            return music.configure(payload.entity_id, payload.duck_percent, payload.default_playlist, payload.clear_playlist)
        except (HomeError, ConfigurationError) as error:
            raise HTTPException(502, str(error)) from error

    @app.get("/api/music/players")
    def music_players(music_assistant_only: bool = False):
        try:
            return {"items": music.players(music_assistant_only), "selected": music._read()}
        except (HomeError, ConfigurationError) as error:
            raise HTTPException(502, str(error)) from error

    @app.get("/api/music/artwork")
    def music_artwork(entity_id: str = Query(pattern=f"^{PLAYER_PATTERN}$", max_length=255)):
        try:
            artwork = music.artwork(entity_id)
        except (HomeError, ConfigurationError) as error:
            raise HTTPException(502, str(error)) from error
        if artwork is None:
            raise HTTPException(404, "Aucune pochette disponible.")
        image, content_type = artwork
        return Response(image, media_type=content_type,
                        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})

    @app.get("/api/music/playlists")
    def music_playlists():
        try:
            return {"items": music.playlists(), "selected": music.default_playlist()}
        except (HomeError, ConfigurationError) as error:
            raise HTTPException(502, str(error)) from error

    @app.get("/api/music/library")
    def music_library(media_type: Literal["artist", "album", "track", "playlist"],
                      query: str = Query(default="", max_length=160)):
        try:
            return {"items": music.library(media_type, query.strip())}
        except (HomeError, ConfigurationError) as error:
            raise HTTPException(502, str(error)) from error

    @app.post("/api/music/play")
    def play_music(payload: MusicPlayInput):
        try:
            return music.play(payload.query, payload.media_type, payload.artist, payload.entity_id)
        except (HomeError, ConfigurationError) as error:
            raise HTTPException(502, str(error)) from error

    @app.post("/api/music/control")
    def control_music(payload: MusicControlInput):
        try:
            if payload.action == "seek" or payload.position is not None:
                return music.seek(payload.action, payload.position, payload.entity_id)
            return music.control(payload.action, payload.entity_id)
        except (HomeError, ConfigurationError) as error:
            raise HTTPException(502, str(error)) from error

    @app.post("/api/music/duck")
    def duck_music(payload: SessionInput):
        try:
            return music.duck(payload.session_id)
        except (HomeError, ConfigurationError) as error:
            raise HTTPException(502, str(error)) from error

    @app.post("/api/music/restore")
    def restore_music(payload: SessionInput):
        try:
            return music.restore(payload.session_id)
        except (HomeError, ConfigurationError) as error:
            raise HTTPException(502, str(error)) from error

    @app.post("/api/announcements")
    def send_announcement(payload: AnnouncementInput):
        try:
            result = announcements.send(payload.message, payload.scope, payload.target)
            return {"message": announce_reply(result), **result}
        except (HomeError, ConfigurationError) as error:
            raise HTTPException(502, str(error)) from error

    @app.post("/api/conversation/reset")
    def reset_conversation(payload: SessionInput):
        conversation.reset(payload.session_id)
        intents.context.reset(payload.session_id)
        pending = getattr(home, "pending", None)
        if pending is not None:
            pending.clear_session(payload.session_id)
        return {"reset":True}

    def conversation_response(request, session_id, text=None, audio=None, floor_id=None, defer_tts=False,
                              wake_phrases=None, wake_strict=False, stream_speech=False, allow_internet=True):
        observer = terminal_observer.get()
        trace = ACTIVE_TRACE.get() if observer is not None else None
        early_state = {"stream": None, "path": None}
        def speak_reply(reply):
            if defer_tts:
                return b"", 0
            with measure("tts"):
                return voice.speak(reply)

        def speak_stabilized_sentences(feed, cancelled):
            """Produit un WAV dès qu'une phrase complète est stabilisée."""
            pending = ""
            final = False
            while not final:
                item = feed()
                if item is None:
                    final = True
                else:
                    pending += item
                sentence, pending = take_complete_sentence(pending, final=final)
                while sentence:
                    if cancelled.is_set():
                        return
                    audio, elapsed = voice.speak(sentence)
                    yield audio, elapsed
                    sentence, pending = take_complete_sentence(pending, final=final)


        async def events():
            loop = asyncio.get_running_loop()
            if (stream_speech and not defer_tts and callable(getattr(voice, "speak", None))
                    and getattr(voice, "supports_early_speech", False)):
                early_state["stream"] = StreamingFlac()
                early_state["path"] = app.state.terminal.tickets.put_stream(early_state["stream"])
            queue = asyncio.Queue()
            cancelled = threading.Event()
            cancellation_flags.add(cancelled)
            observed = {"answer": "", "error": None, "timings": {}}

            def emit(value):
                if value is not None:
                    active_turn = CURRENT_TURN.get()
                    if active_turn is not None:
                        value = {**value, "exchange_id": active_turn.exchange_id}
                        if value.get("type") == "done" and active_turn.result is not None:
                            value["execution"] = active_turn.result
                    if value.get("type") in ("answer", "done"):
                        observed["answer"] = value.get("text", "")
                        if value.get("usage") is not None:
                            observed["usage"] = value["usage"]
                    elif value.get("type") == "error":
                        observed["error"] = value.get("message", "Erreur")
                    if value.get("type") == "done":
                        result = (active_turn.result if active_turn else None) or {}
                        value.setdefault("needs_reply", bool(active_turn and active_turn.needs_reply)
                                         or result.get("status") in ("confirmation", "clarification"))
                        observed["mode"] = value.get("mode")
                        observed["timings"] = value.get("timings", {})
                if value is not None and value.get("type") in ("delta", "answer", "done") and isinstance(value.get("text"), str):
                    value = {**value, "text": prepare_tts_text(value["text"], reformulate_absence=False)}
                if observer is not None and value is not None and not cancelled.is_set():
                    observer(value)
                if not loop.is_closed():
                    loop.call_soon_threadsafe(queue.put_nowait, value)

            def produce():
                import time
                started = time.monotonic()
                turn = None
                turn_token = None
                try:
                    prompt = text
                    stt_ms = 0
                    speaker_id = None
                    if audio is not None:
                        emit({"type":"phase", "phase":"transcribing"})
                        if trace:
                            trace.mark("stt_started")
                        with measure("stt"):
                            prompt, duration, stt_ms = voice.transcribe(audio)
                        if trace:
                            trace.mark("transcript_final")
                        if cancelled.is_set():
                            return
                        if wake_phrases:
                            prompt, matched = strip_prefix(prompt, wake_phrases)
                            if wake_strict and not matched:
                                emit({"type": "transcript", "text": prompt, "stt_ms": stt_ms,
                                      "input_seconds": round(duration, 2)})
                                emit({"type": "error", "code": "wake_rejected", "message": "Le mot d’appel n’est pas confirmé dans la phrase complète. Vérifiez les variantes du réveil. Aucun appel IA effectué."})
                                return
                            if matched and not prompt:
                                emit({"type": "done", "text": "", "mode": "wake_empty",
                                      "audio_base64": "", "timings": {"stt_ms": stt_ms, "llm_ms": 0, "tts_ms": 0}})
                                return
                        emit({"type":"transcript", "text":prompt, "stt_ms":stt_ms,
                              "input_seconds":round(duration, 2)})
                        if not prompt:
                            emit({"type":"error", "message":"Aucune parole reconnue. Aucun appel IA effectué."})
                            return
                        try:
                            state = voice_identity.status()["state"]
                            speaker_id = voice_identity.identify_wav(audio) if state == "ready" else None
                            person = profiles.get(speaker_id) if speaker_id else None
                            emit({"type":"identity", "state":"recognized" if person else ("unknown" if state=="ready" else "inactive"),
                                  "name":person["name"] if person else None})
                        except Exception:
                            # Aucune identité supposée en cas de modèle indisponible ou d'échantillon invalide.
                            speaker_id = None
                            emit({"type":"identity", "state":"unknown", "name":None})
                    if cancelled.is_set():
                        return
                    source = "esp32" if observer is not None else "browser"
                    turn = intents.context.begin((source, session_id, speaker_id or "guest"), prompt, cancelled, floor_id)
                    turn_token = CURRENT_TURN.set(turn)
                    # Priorité aux arrêts et confirmations, puis aux ordres de lumière explicites.
                    model_routing = getattr(conversation, "status", lambda: {"configured": False})()["configured"]
                    from alfred.home_assistant import clean_home_request, normalize as normalize_request
                    emergency = normalize_request(clean_home_request(prompt)).strip(" .!?") in {
                        "stop", "arrete la sonnerie", "arrete les sonneries", "coupe la sonnerie"}
                    local_intent = None
                    confirm = getattr(home, "confirmation_request", None)
                    confirmation = confirm(prompt) if callable(confirm) and prompt else None
                    light_intent = intents.global_light_off(turn, interrupted=confirmation is not None or emergency) if prompt else None
                    if confirmation is not None or emergency or light_intent is not None:
                        intents.context.pending(turn, family=LIGHT_ON_ROOM)
                    if confirmation is not None:
                        local_intent = confirmation
                        if not local_intent.get("reply"):
                            local_intent["reply"] = (local_intent.get("error")
                                                     or "La commande n'a pas pu être exécutée.")
                    elif emergency:
                        stopped = timers.handle("stop", floor_id)
                        local_intent = {"mode": "timer", "reply": stopped["text"],
                                        "status": "confirmed", "actions": []}
                    elif light_intent is not None:
                        local_intent = light_intent
                    elif prompt and model_routing:
                        local_intent = intents.explicit_light_on(turn)
                    elif prompt:
                        local_intent = intents.handle_local(prompt, turn)
                    if local_intent is not None:
                        turn.result = local_intent
                        turn.route = local_intent.get("mode", "local")
                        reply = local_intent["reply"]
                        emit({"type": "phase", "phase": local_intent.get("mode", "home")})
                        emit({"type": "answer", "text": reply})
                        try:
                            output, tts_ms = speak_reply(reply)
                        except Exception:
                            emit({"type": "error", "message": reply + " Lecture vocale impossible ; vérifiez le résultat avant de répéter la demande."})
                            return
                        if not cancelled.is_set():
                            emit({"type": "done", "text": reply, "mode": local_intent.get("mode", "home"), "audio_base64": base64.b64encode(output).decode("ascii"),
                                  "timings": {"stt_ms": stt_ms, "llm_ms": 0, "tts_ms": tts_ms}, **voice_metadata()})
                        return
                    timer = timers.handle(prompt, floor_id) if prompt and not model_routing else None
                    if timer is not None and timer.get("action") == "clarify" and intents.enabled("timers"):
                        timer = None
                    if timer is not None:
                        reply = timer["text"]
                        emit({"type": "phase", "phase": "timer"})
                        emit({"type": "answer", "text": reply})
                        if cancelled.is_set():
                            return
                        emit({"type": "phase", "phase": "speaking"})
                        try:
                            output, tts_ms = speak_reply(reply)
                        except Exception:
                            emit({"type": "error", "message": reply +
                                  " La lecture vocale a échoué. Consultez le suivi des échéances "
                                  "avant de renouveler la commande."})
                            return
                        if not cancelled.is_set():
                            emit({"type": "done", "text": reply, "mode": "timer",
                                  "needs_reply": timer.get("action") == "clarify",
                                  "audio_base64": base64.b64encode(output).decode("ascii"),
                                  "timings": {"stt_ms": stt_ms, "llm_ms": 0, "tts_ms": tts_ms},
                                  **voice_metadata()})
                        return
                    # En présence de l'IA, elle interprète librement les demandes de courses.
                    # Sans clé, les commandes explicites restent disponibles localement.
                    use_shopping_tool = model_routing
                    shopping_reply = shopping.handle(prompt) if prompt and not use_shopping_tool else None
                    if shopping_reply is not None:
                        emit({"type": "phase", "phase": "home"})
                        emit({"type": "answer", "text": shopping_reply})
                        if cancelled.is_set():
                            return
                        try:
                            output, tts_ms = speak_reply(shopping_reply)
                        except Exception:
                            emit({"type": "error", "message": shopping_reply + " Lecture vocale impossible ; vérifiez la liste avant de répéter une demande."})
                            return
                        if not cancelled.is_set():
                            emit({"type": "done", "text": shopping_reply, "mode": "home",
                                  "audio_base64": base64.b64encode(output).decode("ascii"),
                                  "timings": {"stt_ms": stt_ms, "llm_ms": 0, "tts_ms": tts_ms},
                                  **voice_metadata()})
                        return
                    # Commandes musicales certaines : exécution locale, sans coût LLM.
                    music_result = music.handle(prompt) if prompt and not model_routing else None
                    if music_result is not None:
                        emit({"type": "phase", "phase": "music"})
                        reply = music_reply(music_result)
                        if cancelled.is_set():
                            return
                        emit({"type": "answer", "text": reply})
                        if cancelled.is_set():
                            return
                        try:
                            output, tts_ms = speak_reply(reply)
                        except Exception:
                            emit({"type": "error", "message": reply + " Lecture vocale impossible ; vérifiez le lecteur avant de renouveler la commande."})
                            return
                        if not cancelled.is_set():
                            emit({"type": "done", "text": reply, "mode": "music",
                                  "audio_base64": base64.b64encode(output).decode("ascii"),
                                  "timings": {"stt_ms": stt_ms, "llm_ms": 0, "tts_ms": tts_ms},
                                  **voice_metadata()})
                        return
                    # Commande domotique certaine : exécutée localement, sans LLM.
                    house = home.handle(prompt) if prompt and not model_routing else None
                    if house is not None:
                        emit({"type": "phase", "phase": "home"})
                        reply = command_reply(house)
                        if cancelled.is_set():
                            return
                        emit({"type": "answer", "text": reply})
                        emit({"type": "phase", "phase": "speaking"})
                        try:
                            output, tts_ms = speak_reply(reply)
                        except Exception:
                            emit({"type": "error", "message": reply + " Lecture vocale impossible ; vérifiez le résultat avant de répéter la demande."})
                            return
                        if not cancelled.is_set():
                            emit({"type": "done", "text": reply, "mode": "home",
                                  "audio_base64": base64.b64encode(output).decode("ascii"),
                                  "timings": {"stt_ms": stt_ms, "llm_ms": 0,
                                               "tts_ms": tts_ms},
                                  "needs_reply": house.get("status") == "confirmation" or house.get("clarification") is True,
                                  **voice_metadata()})
                        return
                    if not conversation.status()["configured"]:
                        emit({"type": "error",
                              "message": "Configurez d'abord votre clé Command Code dans Alfred."})
                        return
                    emit({"type":"phase", "phase":"thinking"})
                    if trace:
                        trace.mark("model_routed")
                    answer = None
                    pending_delta = ""
                    streamed_text = False
                    text_queue = stdlib_queue.Queue()
                    stream = (conversation.stream(prompt, session_id, cancelled, speaker_id=speaker_id,
                                                  allow_internet=allow_internet)
                              if isinstance(conversation, ConversationService) else conversation.stream(prompt, session_id, cancelled))
                    early_metrics = {"audio_blocks": 0, "early_tts": False}
                    early_future = None
                    early_stream_obj = None
                    early_path = None
                    if early_state["stream"] is not None:
                        early_stream_obj = early_state["stream"]
                        early_path = early_state["path"]
                        def early_produce(result_cell):
                            blocks = speak_stabilized_sentences(lambda: text_queue.get(), cancelled)
                            total_ms = 0
                            try:
                                for audio, elapsed in blocks:
                                    total_ms += elapsed
                                    early_stream_obj.feed(audio)
                                    early_metrics["audio_blocks"] += 1
                                    early_metrics["early_tts_ms"] = total_ms
                                early_stream_obj.finish()
                            except BaseException as error:
                                early_stream_obj.fail(error)
                                raise
                            result_cell.update(path=early_path)

                        early_result = {}
                        early_future = asyncio.run_coroutine_threadsafe(
                            asyncio.to_thread(early_produce, early_result), loop)

                    for event in stream:
                        if cancelled.is_set():
                            return
                        if event["type"] == "delta":
                            streamed_text = streamed_text or bool(event["text"].strip())
                            pending_delta += event["text"]
                            text_queue.put(event["text"])
                            boundaries = list(re.finditer(r"\s+", pending_delta))
                            if boundaries:
                                end = boundaries[-1].end()
                                emit({**event, "text": pending_delta[:end]})
                                pending_delta = pending_delta[end:]
                            continue
                        if event["type"] == "answer":
                            answer = event
                        emit(event)
                    # Un outil peut fournir une réponse finale sans delta texte.
                    # La synthèse anticipée doit aussi recevoir cette réponse.
                    if answer is not None and not streamed_text:
                        text_queue.put(answer["text"])
                    text_queue.put(None)
                    if cancelled.is_set() or answer is None:
                        if early_future:
                            with suppress(Exception):
                                early_future.result(timeout=5)
                        return
                    emit({"type":"phase", "phase":"speaking"})
                    try:
                        if early_future:
                            if early_future.done() and early_future.cancelled():
                                early_path = None
                                output, tts_ms = b"", 0
                            elif early_future.done() and early_future.exception() is None:
                                early_path = early_result.get("path")
                                output, tts_ms = b"", early_metrics.get("early_tts_ms", 0)
                            elif early_future.done():
                                logger.warning("Synthèse anticipée ignorée après une erreur bornée")
                                output, tts_ms = speak_reply(answer["text"])
                                early_path = None
                            else:
                                early_future.result(timeout=90)
                                early_path = early_result.get("path")
                                if not early_path or not early_metrics["audio_blocks"]:
                                    raise VoiceUnavailable("Aucune phrase audio stabilisée.")
                                output, tts_ms = b"", early_metrics.get("early_tts_ms", 0)
                        else:
                            output, tts_ms = speak_reply(answer["text"])
                    except Exception:
                        if answer.get("tool_used"):
                            emit({"type":"error", "message":answer["text"] + " Lecture vocale impossible ; vérifiez le résultat avant de répéter la demande."})
                            return
                        raise
                    if not cancelled.is_set():
                        done_event = {"type":"done", "text":answer["text"], "mode":"conversation",
                              "sources":answer.get("sources", []),
                              "timings":{"stt_ms":stt_ms, "llm_ms":answer["llm_ms"], "tts_ms":tts_ms},
                              **voice_metadata()}
                        if early_path:
                            config = app.state.terminal.config
                            media_host = config.media_host if config else settings.listen_host
                            media_port = config.media_port if config else 8766
                            done_event.update(audio_url=f"http://{media_host}:{media_port}{early_path}",
                                              progressive_audio=True,
                                              early_audio_blocks=early_metrics["audio_blocks"])
                        else:
                            done_event["audio_base64"] = base64.b64encode(output).decode("ascii")
                        emit(done_event)
                except ConversationCancelled:
                    pass
                except (ConversationError, ConfigurationError) as error:
                    emit({"type": "error", "code": "request_failed", "message": str(error)})
                except (InvalidAudio, VoiceBusy, VoiceUnavailable) as error:
                    emit({"type":"error", "message":str(error)})
                except Exception as error:
                    logger.error("Échec conversation (%s)", type(error).__name__)
                    logger.debug("Détail technique de l'échec", exc_info=True)
                    emit({"type":"error", "message":"La réponse n'a pas pu être terminée. Réessayez."})
                finally:
                    if trace:
                        trace.outcome(turn, observed.get("mode"), cancelled=cancelled.is_set(),
                                      failed=observed["error"] is not None)
                    if turn is not None:
                        try:
                            intents.context.finish(turn, observed["answer"])
                            diagnostics.append({"exchange_id": turn.exchange_id, "source": turn.key[0],
                                "session": session_id, "speaker": speaker_id or "guest", "transcript": turn.text,
                                "answer": observed["answer"], "error": observed["error"],
                                "usage": observed.get("usage", {}),
                                "route": turn.route if turn.result else observed.get("mode", "conversation"),
                                "result": turn.result, "timings": {"stt_ms": stt_ms, **observed["timings"],
                                "total_ms": round((time.monotonic()-started)*1000)}, "cancelled": cancelled.is_set()})
                        except Exception:
                            logger.warning("Journal de diagnostic indisponible (aucun contenu de conversation affiché)")
                    if turn_token is not None:
                        CURRENT_TURN.reset(turn_token)
                    emit(None)

            from starlette.concurrency import run_in_threadpool
            worker = asyncio.create_task(run_in_threadpool(produce))
            workers.add(worker)
            worker.add_done_callback(workers.discard)
            try:
                while True:
                    if await request.is_disconnected():
                        break
                    try:
                        value = await asyncio.wait_for(queue.get(), timeout=0.25)
                    except asyncio.TimeoutError:
                        continue
                    if value is None:
                        break
                    yield json.dumps(value, ensure_ascii=False)+"\n"
            finally:
                cancelled.set()
                cancellation_flags.discard(cancelled)

        return StreamingResponse(events(), media_type="application/x-ndjson")

    @app.post("/api/conversation/text")
    async def conversation_text(payload: ChatInput, request: Request):
        return conversation_response(request, payload.session_id, text=payload.text,
                                     floor_id=payload.floor_id, defer_tts=payload.speak is False,
                                     stream_speech=payload.speak is None, allow_internet=payload.allow_internet)

    @app.post("/api/conversation/voice")
    async def conversation_voice(request: Request, session_id: str = Header(
            alias="X-Alfred-Session", min_length=16, max_length=80, pattern=r"^[A-Za-z0-9_-]+$"),
            floor_id: Literal["rdc", "etage1"] | None = Header(default=None, alias="X-Alfred-Floor"),
            allow_internet: bool = Header(default=True, alias="X-Alfred-Allow-Internet"),
            defer_tts: bool = False):
        if defer_tts and (request.client is None or request.client.host != "127.0.0.1"):
            raise HTTPException(403, "Mode réservé au pont interne.")
        wake_phrases = None
        wake_strict = False
        wake_source = request.headers.get("X-Alfred-Wake-Source")
        if wake_source == "esp32":
            if terminal_observer.get() is None:
                raise HTTPException(403, "Source réservée au pont interne.")
            wake_phrases = app.state.wake_manager.preferences.phrases("esp32")
            wake_strict = (request.headers.get("X-Alfred-Wake-Strict") == "1"
                           and app.state.wake_manager.preferences.values["esp32"]["engine"] == "stt")
        elif wake_source == "browser":
            try:
                wake_phrases = app.state.wake_manager.consume(request.headers.get("X-Alfred-Wake-Turn"))
                wake_strict = app.state.wake_manager.preferences.values["browser"]["engine"] == "stt"
            except ValueError as error:
                raise HTTPException(409, str(error)) from error
        data = await read_audio(request)
        try:
            from alfred.voice import validate_wav
            validate_wav(data)
        except InvalidAudio as error:
            raise HTTPException(422, str(error)) from error
        return conversation_response(request, session_id, audio=data, floor_id=floor_id, defer_tts=defer_tts,
                                     wake_phrases=wake_phrases, wake_strict=wake_strict, allow_internet=allow_internet)

    def voice_call(function, *args):
        try:
            return function(*args)
        except InvalidAudio as error:
            raise HTTPException(422, str(error)) from error
        except VoiceUnavailable as error:
            raise HTTPException(503, str(error)) from error
        except VoiceBusy as error:
            raise HTTPException(409, str(error)) from error
        except Exception as error:
            # Ne pas journaliser de texte ou d'audio utilisateur ni le détail des modèles.
            logger.error("Échec moteur vocal (%s)", type(error).__name__)
            raise HTTPException(503, "Le moteur vocal a rencontré une erreur. Réessayez ou vérifiez l'installation locale.") from error

    @app.post("/api/voice/speak")
    def speak(payload: SpeechInput):
        audio, elapsed = voice_call(voice.speak, payload.text)
        metadata = voice_metadata()
        return Response(audio, media_type="audio/wav", headers={
            "X-TTS-Ms": str(elapsed),
            "X-Alfred-Voice-Id": str(metadata.get("voice_id") or ""),
            "X-Alfred-Voice-Engine": str(metadata.get("voice_engine") or ""),
            "X-Alfred-Voice-Fallback": "1" if metadata.get("voice_fallback") else "0",
            "X-Alfred-Voice-Speed": str(metadata.get("voice_speed") or ""),
        })

    @app.post("/api/voice/turn")
    async def voice_turn(request: Request):
        data = await read_audio(request)
        # L'inférence ne bloque pas l'ordonnanceur ; un seul appel moteur à la fois.
        from starlette.concurrency import run_in_threadpool
        return await run_in_threadpool(voice_call, voice.turn, data)

    async def read_audio(request):
        data = bytearray()
        async for chunk in request.stream():
            if len(data) + len(chunk) > MAX_AUDIO_BYTES:
                raise HTTPException(413, "Audio trop volumineux (6 Mo maximum).")
            data.extend(chunk)
        return bytes(data)

    def profile_call(function, *args, **kwargs):
        try:
            return function(*args, **kwargs)
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        except SpeakerUnavailable as error:
            raise HTTPException(503, str(error)) from error
        except SpeakerBusy as error:
            raise HTTPException(409, str(error)) from error

    @app.get("/api/profiles")
    def list_profiles():
        return {"items": profiles.list(), "speaker": speaker.status(),
                "model": MODEL_REPOSITORY}

    @app.post("/api/profiles", status_code=201)
    def create_profile(payload: ProfileInput):
        return profile_call(profiles.create, payload.name, payload.role)

    @app.patch("/api/profiles/{identifier}")
    def rename_profile(identifier: str, payload: ProfileNameInput):
        record = profile_call(profiles.rename, identifier, payload.name)
        if record is None:
            raise HTTPException(404, "Profil introuvable.")
        return record

    @app.delete("/api/profiles/{identifier}")
    def delete_profile(identifier: str):
        if not profile_call(profiles.delete, identifier):
            raise HTTPException(404, "Profil introuvable.")
        return {"deleted": True}

    @app.post("/api/profiles/{identifier}/enroll", status_code=201)
    async def enroll_profile(identifier: str, request: Request):
        if not profiles.get(identifier):
            raise HTTPException(404, "Profil introuvable.")
        data = await read_audio(request)
        from starlette.concurrency import run_in_threadpool
        duration = profile_call(validate_wav, data)
        vector = await run_in_threadpool(profile_call, speaker.embed_wav, data)
        audio_file = profiles.save_audio(identifier, data)
        profiles.add_voiceprint(identifier, vector, MODEL_REPOSITORY, duration, audio_file)
        record = profiles.get(identifier)
        return {"profile_id": identifier, "samples": record["samples"],
                "duration_seconds": round(duration, 2), "audio_file": audio_file}

    @app.post("/api/profiles/identify")
    async def identify_speaker(request: Request):
        data = await read_audio(request)
        from starlette.concurrency import run_in_threadpool
        profile_call(validate_wav, data)
        vector = await run_in_threadpool(profile_call, speaker.embed_wav, data)
        scores = []
        for profile in profiles.list():
            centroid = profiles.centroid(profile["id"], MODEL_REPOSITORY)
            if centroid and len(centroid) == len(vector):
                scores.append({"profile_id": profile["id"], "name": profile["name"],
                               "score": round(cosine(vector, centroid), 4)})
        scores.sort(key=lambda item: item["score"], reverse=True)
        return {"scores": scores, "best": scores[0] if scores else None}

    @app.get("/api/voice-identity/status")
    def voice_identity_status():
        return voice_identity.status()

    @app.post("/api/voice-identity/calibrate")
    def calibrate_voice_identity():
        return profile_call(voice_identity.calibrate)

    @app.post("/api/voice-identity/probe/{identifier}")
    async def probe_voice_identity(identifier: str, request: Request):
        data = await read_audio(request)
        from starlette.concurrency import run_in_threadpool
        return await run_in_threadpool(profile_call, voice_identity.probe, identifier, data)

    @app.post("/api/profiles/{identifier}/reset")
    def reset_profile(identifier: str):
        return {"cleared": profile_call(profiles.reset, identifier)}

    @app.get("/api/profiles/{identifier}/samples")
    def profile_samples(identifier: str):
        if not profiles.get(identifier):
            raise HTTPException(404, "Profil introuvable.")
        return {"items": profiles.samples(identifier)}

    @app.get("/api/profiles/{identifier}/samples/{name}")
    def profile_sample(identifier: str, name: str):
        path = profiles.audio_path(identifier, name)
        if path is None:
            raise HTTPException(404, "Échantillon introuvable.")
        return FileResponse(path, media_type="audio/wav")

    @app.get("/api/schedules")
    def schedules():
        return {"items": store.list(), "limit": 100}

    @app.post("/api/reminders", status_code=201)
    def create_reminder(payload: ReminderInput):
        if not settings.legacy_reminders:
            raise HTTPException(409, "Les rappels seront enregistrés dans les calendriers Home Assistant ; intégration en préparation.")
        now = utc_now()
        if not now < payload.due_at <= now + timedelta(days=366):
            raise HTTPException(422, "Choisir une échéance future dans les 366 prochains jours.")
        try:
            return store.create_reminder(title=payload.title, due_at=payload.due_at,
                floor_id=payload.floor_id, terminal_id="web-admin", target_room=payload.target_room,
                audience=payload.audience, owner_id=payload.owner_id, recurrence=payload.recurrence, now=now)
        except ValueError as error:
            raise HTTPException(422, str(error)) from error

    @app.post("/api/calendar-reminders", status_code=201)
    def create_calendar_reminder(payload: ReminderInput):
        if not calendar_client or settings.legacy_reminders:
            raise HTTPException(503, "Calendriers Home Assistant non configurés.")
        now = utc_now()
        if not now < payload.due_at <= now + timedelta(days=366):
            raise HTTPException(422, "Choisir une échéance future dans les 366 prochains jours.")
        try:
            if payload.audience == "personal" and not profiles.get(payload.owner_id):
                raise HomeError("Profil familial introuvable.")
            entity = calendar_bindings.personal(payload.owner_id) if payload.audience == "personal" else calendar_bindings.family()
            targets = announcements.select("room", payload.target_room)
            if len(targets) != 1 or targets[0]["floor"] != payload.floor_id:
                raise HomeError("La pièce et l'étage ne correspondent pas à un terminal unique.")
            calendar_client.create_reminder(entity, payload.title, payload.due_at,
                                            targets[0]["room"], recurrence=payload.recurrence)
            return {"message": "Rappel enregistré dans le calendrier Home Assistant."}
        except (HomeError, ConfigurationError) as error:
            raise HTTPException(502, str(error)) from error

    @app.get("/api/calendar-reminders/status")
    def calendar_reminder_status():
        monitor = getattr(app.state, "calendar_monitor", None)
        if monitor is None:
            return {"available":False, "missed":0, "unconfirmed":0, "calendar_errors":0}
        return {"available":True, **monitor.status()}

    @app.get("/api/calendar-reminders/family")
    def family_reminders():
        if not calendar_client or settings.legacy_reminders:
            raise HTTPException(503, "Calendrier familial Home Assistant indisponible.")
        now = utc_now()
        try:
            events = calendar_client.events(calendar_bindings.family(), now, now + timedelta(days=366))
        except (HomeError, ConfigurationError) as error:
            raise HTTPException(502, str(error)) from error
        try:
            targets = announcements.targets()
        except HomeError:
            targets = []
        items = []
        for event in events:
            marker = parse_reminder_marker(event.get("description"))
            start, title = event.get("start"), event.get("summary")
            if isinstance(start, dict):
                start = start.get("dateTime")
            if marker and isinstance(start, str) and isinstance(title, str):
                try:
                    due = datetime.fromisoformat(start)
                except ValueError:
                    continue
                if due.tzinfo is not None and due >= now:
                    items.append({"id": marker["id"] + "-" + due.isoformat(), "title": title, "due_at": due.isoformat(), "room": marker["room"]})
        return {"items": sorted(items, key=lambda item: datetime.fromisoformat(item["due_at"])),
                "targets": [{"room": target["room"], "floor_id": target["floor"]} for target in targets]}

    @app.post("/api/calendar-reminders/family", status_code=201)
    def create_family_reminder(payload: FamilyReminderInput):
        return create_calendar_reminder(ReminderInput(**payload.model_dump(), audience="family"))

    @app.get("/api/timers")
    def web_timers(floor_id: Literal["rdc", "etage1"]):
        return {"items": store.active_timers(floor_id)}

    @app.post("/api/timers", status_code=201)
    def create_web_timer(payload: TimerInput):
        now = utc_now()
        return store.create(kind="timer", title=payload.title, due_at=now + timedelta(seconds=payload.duration_seconds),
                            floor_id=payload.floor_id, terminal_id="web-app", now=now)

    @app.post("/api/timers/{identifier}/cancel")
    def cancel_web_timer(identifier: str):
        record = store.get(identifier)
        if record is None or record["kind"] != "timer":
            raise HTTPException(404, "Minuterie introuvable.")
        return store.cancel(identifier)

    @app.post("/api/schedules", status_code=201)
    def create_schedule(payload: ScheduleInput):
        if payload.kind == "reminder" and not settings.legacy_reminders:
            raise HTTPException(409, "Les rappels seront enregistrés dans les calendriers Home Assistant ; intégration en préparation.")
        now = utc_now()
        due_at = now + timedelta(seconds=payload.duration_seconds) if payload.kind == "timer" else payload.due_at
        if not now < due_at <= now + timedelta(days=366):
            raise HTTPException(422, "Choisir une échéance future dans les 366 prochains jours.")
        return store.create(kind=payload.kind, title=payload.title, due_at=due_at,
                            floor_id=payload.floor_id, terminal_id=payload.terminal_id,
                            target_room=payload.target_room, now=now)

    @app.post("/api/schedules/{identifier}/cancel")
    def cancel(identifier: str):
        record = store.cancel(identifier)
        if record is None:
            raise HTTPException(404, "Échéance introuvable.")
        return record

    @app.post("/api/stop")
    def stop(payload: FloorInput):
        return {"floor_id": payload.floor_id, "stopped": store.stop_floor(payload.floor_id)}

    @app.get("/")
    async def index():
        return FileResponse(STATIC / "index.html")

    install_wake_routes(app)
    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app
