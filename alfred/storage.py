"""Échéances UTC persistantes ; aucune diffusion physique dans ce prototype."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from alfred.recurrence import next_weekly


def utc_now():
    return datetime.now(timezone.utc)


class ProcessLock:
    """Un seul ordonnanceur par dossier, Windows et Linux, même après un crash."""

    def __init__(self, directory: Path):
        self.path = directory / "scheduler.lock"
        self.handle = None

    def acquire(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.path.open("a+b")
        try:
            if self.path.stat().st_size == 0:
                self.handle.write(b"0")
                self.handle.flush()
            self.handle.seek(0)
            if __import__("os").name == "nt":
                import msvcrt
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            self.handle.close()
            self.handle = None
            raise RuntimeError("Un service Alfred utilise déjà ce dossier de données.") from error

    def release(self):
        if self.handle:
            self.handle.close()
            self.handle = None


class Store:
    def __init__(self, directory: Path):
        self.path = directory / "alfred.sqlite3"

    @contextmanager
    def connection(self):
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.execute("PRAGMA journal_mode=WAL")
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1, 2, 3, 4, 5, 6):
                raise RuntimeError("Version de base de données non prise en charge.")
            db.execute("""CREATE TABLE IF NOT EXISTS schedules (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL CHECK (kind IN ('timer', 'reminder')),
                title TEXT NOT NULL,
                due_at REAL NOT NULL,
                floor_id TEXT NOT NULL,
                terminal_id TEXT NOT NULL,
                target_room TEXT,
                status TEXT NOT NULL CHECK (status IN (
                    'pending', 'ringing', 'awaiting_delivery', 'completed', 'missed', 'cancelled'
                )),
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )""")
            db.execute("CREATE INDEX IF NOT EXISTS due_schedules ON schedules(status, due_at)")
            db.execute("""CREATE TABLE IF NOT EXISTS profiles (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL CHECK (role IN ('adult', 'child')),
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS voiceprints (
                id TEXT PRIMARY KEY,
                profile_id TEXT NOT NULL REFERENCES profiles(id),
                vector BLOB NOT NULL,
                dimensions INTEGER NOT NULL,
                model TEXT NOT NULL,
                duration_seconds REAL NOT NULL,
                created_at REAL NOT NULL,
                audio_file TEXT
            )""")
            db.execute("CREATE INDEX IF NOT EXISTS voiceprints_profile ON voiceprints(profile_id, model)")
            db.execute("""CREATE TABLE IF NOT EXISTS reminder_details (
                schedule_id TEXT PRIMARY KEY REFERENCES schedules(id),
                audience TEXT NOT NULL CHECK (audience IN ('personal', 'family')),
                owner_id TEXT REFERENCES profiles(id),
                CHECK ((audience='personal' AND owner_id IS NOT NULL) OR
                       (audience='family' AND owner_id IS NULL))
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS reminder_series (
                id TEXT PRIMARY KEY, anchor_at REAL NOT NULL, active INTEGER NOT NULL CHECK(active IN (0,1))
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS reminder_occurrences (
                schedule_id TEXT PRIMARY KEY REFERENCES schedules(id),
                series_id TEXT NOT NULL REFERENCES reminder_series(id)
            )""")
            db.execute("CREATE INDEX IF NOT EXISTS reminder_occurrences_series ON reminder_occurrences(series_id)")
            db.execute("""CREATE TABLE IF NOT EXISTS reminder_dispatch (
                schedule_id TEXT PRIMARY KEY REFERENCES schedules(id),
                phase TEXT NOT NULL CHECK(phase IN ('attempted', 'sent', 'failed')),
                updated_at REAL NOT NULL
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS calendar_watch (
                entity_id TEXT PRIMARY KEY, last_poll REAL NOT NULL
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS calendar_reminder_journal (
                occurrence_key TEXT PRIMARY KEY, start_at REAL NOT NULL,
                phase TEXT NOT NULL CHECK (phase IN ('attempted', 'sent', 'failed', 'missed'))
            )""")
            db.execute("PRAGMA user_version=6")

    @staticmethod
    def record(row):
        result = dict(row)
        for name in ("due_at", "created_at", "updated_at"):
            result[name] = datetime.fromtimestamp(result[name], timezone.utc).isoformat()
        return result

    def create(self, *, kind, title, due_at, floor_id, terminal_id, target_room=None, now=None):
        now = now or utc_now()
        identifier = uuid4().hex
        with self.connection() as db:
            db.execute("INSERT INTO schedules VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)", (
                identifier, kind, title, due_at.timestamp(), floor_id, terminal_id,
                target_room, now.timestamp(), now.timestamp(),
            ))
        return self.get(identifier)

    def get(self, identifier):
        with self.connection() as db:
            row = db.execute("""SELECT s.*, d.audience, d.owner_id, p.name AS owner_name, o.series_id, rd.phase AS dispatch_phase
                FROM schedules s LEFT JOIN reminder_details d ON d.schedule_id=s.id
                LEFT JOIN profiles p ON p.id=d.owner_id LEFT JOIN reminder_occurrences o ON o.schedule_id=s.id
                LEFT JOIN reminder_dispatch rd ON rd.schedule_id=s.id
                WHERE s.id=?""", (identifier,)).fetchone()
            return self.record(row) if row else None

    def list(self, limit=100):
        with self.connection() as db:
            rows = db.execute("""SELECT s.*, d.audience, d.owner_id, p.name AS owner_name, o.series_id, rd.phase AS dispatch_phase
                FROM schedules s LEFT JOIN reminder_details d ON d.schedule_id=s.id
                LEFT JOIN profiles p ON p.id=d.owner_id
                LEFT JOIN reminder_occurrences o ON o.schedule_id=s.id
                LEFT JOIN reminder_dispatch rd ON rd.schedule_id=s.id
                ORDER BY CASE WHEN s.status IN ('pending', 'ringing', 'awaiting_delivery')
                THEN 0 ELSE 1 END, s.due_at LIMIT ?""", (limit,)).fetchall()
            return [self.record(row) for row in rows]

    def create_reminder(self, *, title, due_at, floor_id, terminal_id, target_room,
                        audience, owner_id=None, recurrence="once", now=None):
        now = now or utc_now()
        identifier = uuid4().hex
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            if audience == "personal":
                if not owner_id or not db.execute("SELECT 1 FROM profiles WHERE id=?", (owner_id,)).fetchone():
                    raise ValueError("Sélectionnez un profil familial existant.")
            elif audience != "family" or owner_id is not None:
                raise ValueError("Destinataire de rappel invalide.")
            if recurrence not in ("once", "weekly"):
                raise ValueError("Récurrence non prise en charge.")
            db.execute("INSERT INTO schedules VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)",
                       (identifier, "reminder", title, due_at.timestamp(), floor_id, terminal_id,
                        target_room, now.timestamp(), now.timestamp()))
            db.execute("INSERT INTO reminder_details VALUES (?, ?, ?)", (identifier, audience, owner_id))
            if recurrence == "weekly":
                series_id = uuid4().hex
                db.execute("INSERT INTO reminder_series VALUES (?, ?, 1)", (series_id, due_at.timestamp()))
                db.execute("INSERT INTO reminder_occurrences VALUES (?, ?)", (identifier, series_id))
        return self.get(identifier)

    @staticmethod
    def _schedule_next_occurrences(db, rows, now):
        for row in rows:
            if not row["series_id"] or not row["active"]:
                continue
            if db.execute("""SELECT 1 FROM schedules s JOIN reminder_occurrences o ON o.schedule_id=s.id
                             WHERE o.series_id=? AND s.status='pending' LIMIT 1""", (row["series_id"],)).fetchone():
                continue
            anchor = datetime.fromtimestamp(row["anchor_at"], timezone.utc)
            due = next_weekly(anchor, now)
            identifier = uuid4().hex
            timestamp = now.timestamp()
            db.execute("INSERT INTO schedules VALUES (?, 'reminder', ?, ?, ?, ?, ?, 'pending', ?, ?)",
                       (identifier, row["title"], due.timestamp(), row["floor_id"], row["terminal_id"], row["target_room"], timestamp, timestamp))
            db.execute("INSERT INTO reminder_details VALUES (?, ?, ?)", (identifier, row["audience"], row["owner_id"]))
            db.execute("INSERT INTO reminder_occurrences VALUES (?, ?)", (identifier, row["series_id"]))

    @staticmethod
    def _due_recurring(db, timestamp):
        return db.execute("""SELECT s.*, d.audience, d.owner_id, o.series_id, r.anchor_at, r.active
            FROM schedules s JOIN reminder_details d ON d.schedule_id=s.id
            JOIN reminder_occurrences o ON o.schedule_id=s.id JOIN reminder_series r ON r.id=o.series_id
            WHERE s.status='pending' AND s.due_at<=?""", (timestamp,)).fetchall()

    def active_timers(self, floor_id):
        with self.connection() as db:
            rows = db.execute("""SELECT rowid AS number, * FROM schedules
                WHERE kind='timer' AND floor_id=? AND status IN ('pending', 'ringing')
                ORDER BY rowid""", (floor_id,)).fetchall()
            return [self.record(row) for row in rows]

    def current_timer(self, floor_id):
        """Minuteur courant : la sonnerie d'abord, puis la création la plus récente."""
        with self.connection() as db:
            row = db.execute("""SELECT rowid AS number, * FROM schedules
                WHERE kind='timer' AND floor_id=? AND status IN ('pending', 'ringing')
                ORDER BY (status='ringing') DESC, rowid DESC LIMIT 1""",
                (floor_id,)).fetchone()
            return self.record(row) if row else None

    def cancel_timer(self, floor_id, number=None, now=None):
        """Sélection et annulation indivisibles ; jamais de choix arbitraire."""
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            rows = db.execute("""SELECT rowid AS number, id FROM schedules
                WHERE kind='timer' AND floor_id=? AND status IN ('pending', 'ringing')""",
                (floor_id,)).fetchall()
            if number is not None:
                rows = [row for row in rows if str(row["number"]) == number]
            if len(rows) > 1:
                return "ambiguous"
            if not rows:
                return False
            db.execute("UPDATE schedules SET status='cancelled', updated_at=? WHERE id=?",
                       ((now or utc_now()).timestamp(), rows[0]["id"]))
            return True

    def recover(self, now=None, include_reminders=True):
        """Pas de rattrapage sonore au démarrage, y compris une ancienne sonnerie."""
        now = now or utc_now()
        timestamp = now.timestamp()
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            recurring = self._due_recurring(db, timestamp) if include_reminders else []
            result = db.execute("""UPDATE schedules
                SET status=CASE kind WHEN 'timer' THEN 'completed' ELSE 'missed' END,
                    updated_at=?
                WHERE ((status='pending' AND due_at<=?)
                   OR status IN ('ringing', 'awaiting_delivery'))
                  AND (? OR kind='timer')""", (timestamp, timestamp, include_reminders))
            count = result.rowcount
            self._schedule_next_occurrences(db, recurring, now)
            return count

    def tick(self, now=None, include_reminders=True):
        """Transitions atomiques, sans rejouer une échéance déjà traitée."""
        now = now or utc_now()
        timestamp = now.timestamp()
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            recurring = self._due_recurring(db, timestamp) if include_reminders else []
            result = db.execute("""UPDATE schedules
                SET status=CASE kind WHEN 'timer' THEN 'ringing' ELSE 'awaiting_delivery' END,
                    updated_at=? WHERE status='pending' AND due_at<=? AND (? OR kind='timer')""", (timestamp, timestamp, include_reminders))
            count = result.rowcount
            self._schedule_next_occurrences(db, recurring, now)
            return count

    def stop_floor(self, floor_id, now=None):
        timestamp = (now or utc_now()).timestamp()
        with self.connection() as db:
            result = db.execute("""UPDATE schedules SET status='completed', updated_at=?
                WHERE floor_id=? AND kind='timer' AND status='ringing'""", (timestamp, floor_id))
            return result.rowcount

    def cancel(self, identifier, now=None):
        timestamp = (now or utc_now()).timestamp()
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT status FROM schedules WHERE id=?", (identifier,)).fetchone()
            if row and row["status"] == "pending":
                db.execute("UPDATE reminder_series SET active=0 WHERE id=(SELECT series_id FROM reminder_occurrences WHERE schedule_id=?)", (identifier,))
            db.execute("""UPDATE schedules SET status='cancelled', updated_at=?
                WHERE id=? AND status IN ('pending', 'ringing', 'awaiting_delivery', 'missed')""",
                (timestamp, identifier))
        return self.get(identifier)
