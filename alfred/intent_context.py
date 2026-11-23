"""Contexte éphémère par source/session/locuteur, partagé local et IA."""
from collections import OrderedDict
from contextvars import ContextVar
from dataclasses import dataclass, field
import threading
import time
from uuid import uuid4


@dataclass
class Turn:
    key: tuple
    text: str
    cancelled: threading.Event
    floor: str | None = None
    exchange_id: str = field(default_factory=lambda: uuid4().hex)
    result: dict | None = None
    route: str = "conversation"
    needs_reply: bool = False


CURRENT_TURN = ContextVar("alfred_intent_turn", default=None)


def ask_for_reply(text):
    turn = CURRENT_TURN.get()
    if turn is not None:
        turn.needs_reply = True
    return text


class IntentContext:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.lock = threading.RLock()
        self.sessions = OrderedDict()

    def state(self, key):
        with self.lock:
            now = self.clock()
            for old, state in list(self.sessions.items()):
                if now - state["updated"] >= 300:
                    del self.sessions[old]
            state = self.sessions.setdefault(key, {"history": [], "last": None, "pending": None, "active": None, "updated": now})
            self.sessions.move_to_end(key)
            while len(self.sessions) > 128:
                _, expired = self.sessions.popitem(last=False)
                if expired["active"]:
                    expired["active"].set()
            return state

    def reset(self, session):
        with self.lock:
            for key in list(self.sessions):
                if key[1] == session:
                    state = self.sessions.pop(key)
                    if state["active"]:
                        state["active"].set()

    def begin(self, key, text, cancelled, floor=None):
        with self.lock:
            state = self.state(key)
            if state["active"]:
                state["active"].set()
            state["active"] = cancelled
            state["updated"] = self.clock()
        return Turn(key, text, cancelled, floor)

    def finish(self, turn, reply):
        with self.lock:
            state = self.state(turn.key)
            if state["active"] is not turn.cancelled:
                return
            if turn.cancelled.is_set():
                state["pending"] = None
                state["active"] = None
                return
            state["history"] = [*state["history"], {"user": turn.text, "assistant": reply}][-6:]
            state["updated"] = self.clock()
            state["active"] = None

    def last(self, turn):
        with self.lock:
            return self.state(turn.key)["last"]

    def remember(self, turn, actions):
        with self.lock:
            state = self.state(turn.key)
            if state["active"] is turn.cancelled and not turn.cancelled.is_set():
                state["last"] = actions[-1] if actions else state["last"]

    def pending(self, turn, proposal=None, *, family=None):
        with self.lock:
            state = self.state(turn.key)
            if family and (state["active"] is not turn.cancelled or turn.cancelled.is_set()):
                return None
            if proposal is not None:
                state["pending"] = (self.clock() + 30, proposal)
                return proposal
            pending = state["pending"]
            if family and pending and pending[1].get("family") != family:
                return None
            state["pending"] = None
            return pending[1] if pending and pending[0] > self.clock() else None
