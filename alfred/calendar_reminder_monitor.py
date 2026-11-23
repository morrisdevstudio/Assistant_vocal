"""Détecte les rappels marqués dans HA sans recopier le calendrier."""
import hashlib
from datetime import datetime, timedelta, timezone

from alfred.ha_calendar import CalendarBindings, parse_reminder_marker
from alfred.storage import utc_now


class CalendarReminderMonitor:
    def __init__(self, store, calendar, bindings: CalendarBindings, announcements, clock=utc_now):
        self.store, self.calendar, self.bindings, self.announcements = store, calendar, bindings, announcements
        self.clock = clock
        self.errors = set()
        self.recovering = set()

    def sync(self, startup=False):
        now = self.clock().astimezone(timezone.utc)
        config = self.bindings.load()
        with self.store.connection() as db:
            profiles={row["id"] for row in db.execute("SELECT id FROM profiles").fetchall()}
        entities = {entity for owner, entity in config["personal"].items() if owner in profiles}
        if config["family"]:
            entities.add(config["family"])
        if startup:
            self.recovering.update(entities)
        for entity in entities:
            try:
                self._sync_calendar(entity, now, entity in self.recovering)
                self.errors.discard(entity)
                self.recovering.discard(entity)
            except Exception:
                self.errors.add(entity)

    def _sync_calendar(self, entity, now, startup):
        with self.store.connection() as db:
            cursor = db.execute("SELECT last_poll FROM calendar_watch WHERE entity_id=?", (entity,)).fetchone()
        if cursor is None:
            self._save_cursor(entity, now)
            return
        previous = datetime.fromtimestamp(cursor["last_poll"], timezone.utc)
        if now <= previous:
            return
        if now - previous > timedelta(days=365):
            raise ValueError("Intervalle de reprise trop ancien")
        events = self.calendar.events(entity, previous, now + timedelta(seconds=1))
        missed = startup or now - previous > timedelta(seconds=20)
        for event in events:
            marker = parse_reminder_marker(event.get("description"))
            start = event.get("start")
            if isinstance(start, dict):
                start = start.get("dateTime")
            if not marker or not isinstance(start, str):
                continue
            try:
                due = datetime.fromisoformat(start.replace("Z", "+00:00"))
                if due.utcoffset() is None:
                    continue
                due = due.astimezone(timezone.utc)
            except ValueError:
                continue
            if not previous < due <= now:
                continue
            title = event.get("summary")
            if not isinstance(title, str) or not 1 <= len(title.strip()) <= 160 or any(ord(c)<32 for c in title):
                continue
            key = hashlib.sha256((entity + "\n" + marker["id"] + "\n" + due.isoformat()).encode()).hexdigest()
            if missed:
                self._claim(key, due, "missed")
                continue
            try:
                targets = self.announcements.select("room", marker["room"])
                if len(targets) != 1:
                    raise ValueError("Destination ambiguë")
            except Exception:
                self._claim(key, due, "failed")
                continue
            if not self._claim(key, due, "attempted"):
                continue
            try:
                outcome = self.announcements.send("Rappel : " + title, "room", marker["room"])
                phase = "sent" if not outcome["incomplete"] and len(outcome["accepted"])==1 else "failed"
            except Exception:
                phase = "failed"
            with self.store.connection() as db:
                db.execute("UPDATE calendar_reminder_journal SET phase=? WHERE occurrence_key=?", (phase,key))
        self._save_cursor(entity, now)

    def _save_cursor(self, entity, now):
        with self.store.connection() as db:
            db.execute("INSERT INTO calendar_watch VALUES (?, ?) ON CONFLICT(entity_id) DO UPDATE SET last_poll=excluded.last_poll",
                       (entity, now.timestamp()))

    def _claim(self, key, due, phase):
        with self.store.connection() as db:
            result=db.execute("INSERT OR IGNORE INTO calendar_reminder_journal VALUES (?, ?, ?)",
                              (key, due.timestamp(), phase))
            return result.rowcount == 1

    def status(self):
        with self.store.connection() as db:
            counts={row["phase"]: row["n"] for row in db.execute(
                "SELECT phase, COUNT(*) AS n FROM calendar_reminder_journal GROUP BY phase").fetchall()}
        return {"missed":counts.get("missed", 0), "unconfirmed":counts.get("failed",0)+counts.get("attempted",0),
                "calendar_errors":len(self.errors)}
