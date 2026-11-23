"""Palette de l’anneau RGB pilotée par les états du satellite Alfred."""
import asyncio
import json
import logging
import re
import time
from contextlib import suppress
from typing import Literal

from alfred.home_aliases import write_names


LedPhase = Literal["standby", "listening", "processing", "speaking", "error"]
LedEffect = Literal["solid", "rotation", "comet", "breathing", "scan"]
EFFECT_NAMES: dict[LedEffect, str] = {
    "solid": "None", "rotation": "Spinner", "comet": "Comet",
    "breathing": "Breathe", "scan": "Scan",
}
DEFAULT_COLORS: dict[LedPhase, str | None] = {
    "standby": None,
    "listening": "#44AFFF",
    "processing": "#F5A623",
    "speaking": "#A77AFF",
    "error": "#FF302F",
}
PHASES = {
    "listening": "listening", "recording": "listening",
    "processing": "processing", "test_preparing": "processing",
    "playing": "speaking", "test_playing": "speaking",
}
BRIGHTNESS = 0.25
logger = logging.getLogger(__name__)


class TerminalLeds:
    def __init__(self, path=None):
        self.path = path
        self.colors = DEFAULT_COLORS.copy()
        self.effects: dict[LedPhase, LedEffect] = dict.fromkeys(DEFAULT_COLORS, "solid")
        if path is not None:
            try:
                saved = json.loads(path.read_text(encoding="utf-8"))
                for state in self.colors.keys() & saved.keys():
                    color = saved[state]
                    if color is None or isinstance(color, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", color):
                        self.colors[state] = color.upper() if color and color != "#000000" else None
                effects = saved.get("effects")
                if isinstance(effects, dict):
                    for state in self.effects.keys() & effects.keys():
                        effect = effects[state]
                        if isinstance(effect, str) and effect in EFFECT_NAMES:
                            self.effects[state] = effect
            except FileNotFoundError:
                pass
            except (OSError, ValueError, AttributeError):
                logger.warning("Palette LED illisible, couleurs par défaut utilisées.")
        self.detach()

    def save(self, colors, effects):
        palette = {**self.colors, **{
            state: color.upper() if color and color != "#000000" else None for state, color in colors.items()
        }}
        animations = {**self.effects, **effects}
        write_names(self.path, {**palette, "effects": animations})
        self.colors, self.effects = palette, animations

    def effect_options(self):
        if not self.ring:
            return list(EFFECT_NAMES)
        return [effect for effect, name in EFFECT_NAMES.items() if effect == "solid" or name in self.ring.effects]

    def attach(self, entities):
        from aioesphomeapi import LightInfo, SwitchInfo

        self.detach()
        self.ring = next((entity for entity in entities if isinstance(entity, LightInfo)
                          and entity.object_id == "status_ring"), None)
        self.mute = next((entity for entity in entities if isinstance(entity, SwitchInfo)
                          and entity.object_id == "microphone_mute"), None)

    def detach(self):
        self.ring = self.mute = self.observed = self.last_error = None
        self.muted = None
        self.error_until = self.retry_at = 0.
        self.last_target = None

    def observe(self, state):
        from aioesphomeapi import LightState, SwitchState

        if isinstance(state, LightState) and self.ring and state.key == self.ring.key:
            self.observed = state
        if isinstance(state, SwitchState) and self.mute and state.key == self.mute.key:
            self.muted = state.state

    def flash_error(self):
        self.error_until = time.monotonic() + 2

    def update(self, terminal, now):
        from aioesphomeapi import ColorMode

        if terminal.error != self.last_error:
            self.last_error = terminal.error
            if terminal.error:
                self.error_until = now + 2
        state = self.observed
        if (state is None or terminal.bell_active or terminal.bell_test
                or (self.mute and self.muted is not False)
                or (state.state and state.effect in {"Volume Level", "Timer Progress"})):
            self.last_target = None
            return
        phase = PHASES.get(terminal.phase, "error" if now < self.error_until else "standby")
        color = self.colors[phase]
        effect = EFFECT_NAMES[self.effects[phase]]
        if effect not in self.ring.effects:
            effect = "None"
        target = (color, effect if color else None)
        if target == self.last_target and now < self.retry_at:
            return
        if not color or color == "#000000":
            if not state.state:
                return
            command = {"state": False, "transition_length": 0}
        else:
            channels = tuple(int(color[index:index + 2], 16) for index in (1, 3, 5))
            peak = max(channels)
            rgb = tuple(channel / peak for channel in channels)
            brightness = BRIGHTNESS * peak / 255
            if (state.state and (state.effect or "None") == effect
                    and abs(state.brightness - brightness) < .004 and state.color_brightness > .99
                    and all(abs(actual - target) < .01 for actual, target in
                            zip((state.red, state.green, state.blue), rgb))):
                return
            command = {"state": True, "color_mode": ColorMode.RGB, "rgb": rgb,
                       "brightness": brightness, "color_brightness": 1.,
                       "effect": effect, "transition_length": 0}
        self.last_target, self.retry_at = target, now + .55
        terminal.client.light_command(self.ring.key, **command)

    async def track(self, terminal, disconnected):
        from aioesphomeapi import APIConnectionError

        while not disconnected.is_set():
            with suppress(APIConnectionError, OSError):
                self.update(terminal, time.monotonic())
            try:
                await asyncio.wait_for(disconnected.wait(), .15)
            except asyncio.TimeoutError:
                pass
