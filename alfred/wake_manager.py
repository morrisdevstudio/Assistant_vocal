"""Propriétaire unique de la veille, préparation transactionnelle et import borné."""
import asyncio
import copy
import json
import secrets
import sys
import time
from dataclasses import replace
from pathlib import Path
from alfred.wake_settings import WakeSettings, phrase
from alfred.wake_stt import STTWakeDetector

MAX_MODEL_BYTES = 10 * 1024 * 1024


class WakeManager:
    def __init__(self, settings, voice, terminal):
        models = settings.models_dir or settings.data_dir.parent / "models"
        self.preferences = WakeSettings(settings.data_dir, models, terminal.config)
        self.voice, self.terminal = voice, terminal
        self.original_verification = terminal.config.wake_verify if terminal.config else False
        self.owner = "esp32" if terminal.wake_armed else None
        self.browser = None
        self.busy = False
        self.lock = asyncio.Lock()
        self.receipts = {}
        self.last_error = None

    def occupied(self):
        return self.busy or bool(getattr(self.terminal, 'wake_test', None)) or self.terminal.phase in ("listening", "recording", "processing", "playing", "test_playing")

    def snapshot(self):
        if self.browser is None:
            self.owner = "esp32" if self.terminal.wake_armed else None
        return {"settings": copy.deepcopy(self.preferences.values),
                "models": self.preferences.catalogue(), "owner": self.owner,
                "busy": self.occupied(), "error": self.last_error,
                "browser": self.browser.status() if self.browser else {"armed": False},
                "raw_audio_saved": False}

    async def prepare(self, source, value=None):
        value = value or self.preferences.values[source]
        if value["engine"] == "stt":
            if not self.voice.status().get("stt_available"):
                raise ValueError("Parakeet n'est pas disponible.")
            return await asyncio.to_thread(STTWakeDetector,
                getattr(self.voice, "transcribe_wake", self.voice.transcribe),
                [value["phrase"], *value["variants"]])
        from alfred.wake_word import WakeWordDetector, verify_preprocess
        folder = self.preferences.folder
        entry = next((v for v in self.preferences.catalogue() if v["id"] == value["model"]), None)
        if entry is None:
            raise ValueError("Modèle de réveil absent.")
        def load():
            verify_preprocess(folder)
            return WakeWordDetector(folder / entry["id"], folder, value["threshold"])
        return await asyncio.to_thread(load)

    async def save(self, source, value):
        async with self.lock:
            if getattr(self.terminal, 'wake_test', None):
                raise ValueError("Arrêtez d'abord le test de réveil.")
            if self.occupied():
                raise ValueError("Une commande ou une réponse est en cours.")
            value = self.preferences.validate(value)
            candidate = await self.prepare(source, value)
            if self.occupied():
                raise ValueError("Une commande a commencé ; réglage conservé.")
            # Persister avant d'interrompre l'ancien moteur, pour conserver
            # l'état utilisable si le disque refuse l'écriture.
            self.preferences.save(source, value)
            if source == "esp32":
                armed = self.terminal.wake_armed
                self.terminal.stop_wake_word()
                self.configure_terminal(candidate)
                if armed:
                    await self.terminal.start_wake_word()
            elif self.browser:
                await self.stop_browser("Réglage modifié. Réactivez la veille.")
            return self.snapshot()

    def configure_terminal(self, detector):
        terminal = self.terminal
        value = self.preferences.values["esp32"]
        terminal.wake_detector = detector
        terminal.wake_phrases = self.preferences.phrases("esp32")
        terminal.wake_error = None
        if terminal.config:
            terminal.config = replace(terminal.config, wake_model=value["model"],
                wake_threshold=value["threshold"], wake_verify=False if value["engine"] == "stt" else self.original_verification)
        if isinstance(detector, STTWakeDetector):
            detector.callback = terminal._wake_detected
            detector.diagnostic_observer = lambda text, matched, final, duration: (
                terminal.wake_test.observe_stt(text, matched, final, duration)
                if getattr(terminal, 'wake_test', None) else None)

    async def start_terminal(self):
        async with self.lock:
            if getattr(self.terminal, 'wake_test', None):
                raise ValueError("Un test de réveil est en cours.")
            if self.occupied():
                raise ValueError("Une commande ou une réponse est en cours.")
            if not self.terminal.connected:
                raise ValueError("ESP32 déconnecté.")
            candidate = await self.prepare("esp32")
            if self.occupied():
                raise ValueError("Terminal occupé.")
            self.preferences.save_resume(True)
            await self.stop_browser("Veille transférée vers l’ESP32.")
            self.terminal.stop_wake_word()
            self.configure_terminal(candidate)
            result = await self.terminal.start_wake_word()
            self.owner = "esp32"
            return result

    async def restore_terminal(self):
        """Armer avant la connexion LAN, sans réactiver une veille arrêtée."""
        if (self.preferences.resume_esp32 and self.terminal.config
                and self.terminal.config.wake_word and self.terminal.wake_detector
                and not self.terminal.wake_error):
            await self.terminal.start_wake_word(wait_for_connection=True)
            self.owner = "esp32"

    def stop_terminal(self):
        result = self.terminal.stop_wake_word()
        if self.owner == "esp32":
            self.owner = None
        self.preferences.save_resume(False)
        return result

    async def stop_browser(self, reason="Veille arrêtée."):
        browser, self.browser = self.browser, None
        self.receipts.clear()
        self.busy = False
        if self.owner == "browser":
            self.owner = None
        if browser:
            await browser.close(reason)

    def ticket(self, phrases):
        self.receipts.clear()
        token = secrets.token_urlsafe(24)
        self.receipts[token] = (time.monotonic() + 30, list(phrases))
        return token

    def consume(self, token):
        entry = self.receipts.pop(token, None)
        if not entry or entry[0] < time.monotonic() or self.owner != "browser":
            raise ValueError("Tour de réveil expiré ou déjà utilisé.")
        return entry[1]

    async def import_model(self, label, wake_phrase, data):
        label = phrase(label)
        wake_phrase = phrase(wake_phrase)
        if not 0 < len(data) <= MAX_MODEL_BYTES:
            raise ValueError("Modèle vide ou supérieur à dix Mo.")
        folder = self.preferences.folder
        folder.mkdir(parents=True, exist_ok=True)
        filename = "custom-" + secrets.token_hex(12) + ".onnx"
        path = folder / filename
        path.write_bytes(data)
        process = None
        try:
            process = await asyncio.create_subprocess_exec(sys.executable, "-m", "alfred.validate_wake_model",
                str(path.resolve()), str(folder.resolve()), stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                **({"creationflags": 0x08000000} if sys.platform == "win32" else {}))
            if await asyncio.wait_for(process.wait(), 20) != 0:
                raise ValueError("Modèle ONNX incompatible ou données externes interdites.")
            async with self.lock:
                updated = {**self.preferences.custom, filename: [label, wake_phrase, []]}
                temp = self.preferences.custom_path.with_suffix(".tmp")
                temp.write_text(json.dumps(updated, ensure_ascii=False), encoding="utf-8")
                temp.replace(self.preferences.custom_path)
                self.preferences.custom = updated
            return {"id": filename, "label": label, "phrase": wake_phrase}
        except BaseException:
            if process and process.returncode is None:
                process.kill()
                await process.wait()
            path.unlink(missing_ok=True)
            raise
