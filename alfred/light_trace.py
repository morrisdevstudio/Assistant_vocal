"""Mesures opt-in d'un seul tour ESP32, sans contenu vocal."""
from contextlib import contextmanager
from contextvars import ContextVar
from secrets import token_urlsafe
from threading import Lock
from time import perf_counter


ACTIVE_TRACE = ContextVar("light_trace", default=None)


class LightTrace:
    def __init__(self, clock=perf_counter):
        self.id = token_urlsafe(18)
        self.clock = clock
        self.deadline = clock() + 150
        self.origin = None
        self.state = "armed"
        self.events = []
        self.result = {}
        self.lock = Lock()

    def claim(self, at, last_voice, reason):
        with self.lock:
            if self.state != "armed":
                return False
            self.origin, self.state = at, "captured"
            if last_voice is not None:
                self._mark("last_voice_detected", last_voice)
            self._mark("capture_closed", at, reason=reason)
            return True

    def _mark(self, name, at, **fields):
        if self.state == "captured" and len(self.events) < 512:
            self.events.append({"event": name, "ms": round((at - self.origin) * 1000, 2), **fields})

    def mark(self, name, **fields):
        with self.lock:
            self._mark(name, self.clock(), **fields)

    def outcome(self, turn, mode, *, cancelled, failed):
        with self.lock:
            if self.state != "captured":
                return
            result = turn.result if turn and turn.result else {}
            actions = [{"operation": action.get("intent", {}).get("operation"),
                        "targets": action.get("targets", []), "status": action.get("status")}
                       for action in result.get("actions", []) if isinstance(action, dict)]
            self.result = {"exchange_id": turn.exchange_id if turn else None,
                           "route": turn.route if result else mode,
                           "status": result.get("status"),
                           "actions": actions, "cancelled": cancelled, "error": failed}

    def finish(self, state, event=None):
        with self.lock:
            if self.state in ("armed", "captured"):
                if event:
                    self._mark(event, self.clock())
                self.state = state

    def snapshot(self):
        with self.lock:
            if self.state in ("armed", "captured") and self.clock() >= self.deadline:
                self.state = "no_capture" if self.state == "armed" else "timeout"
            return {"id": self.id, "state": self.state, "events": list(self.events),
                    "result": self.result}


def mark(name, **fields):
    trace = ACTIVE_TRACE.get()
    if trace is not None:
        trace.mark(name, **fields)


@contextmanager
def measure(name, **fields):
    trace = ACTIVE_TRACE.get()
    if trace is None:
        yield
        return
    start = trace.clock()
    try:
        yield
    finally:
        trace.mark(name, duration_ms=round((trace.clock() - start) * 1000, 2), **fields)
