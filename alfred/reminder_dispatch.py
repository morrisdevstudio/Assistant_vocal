"""Tentative unique pour les rappels arrivés à échéance, sans inventer une écoute."""
from alfred.credentials import ConfigurationError
from alfred.home_assistant import HomeError
from alfred.storage import utc_now


class ReminderDispatcher:
    def __init__(self, store, announcements):
        self.store = store
        self.announcements = announcements

    def sync(self):
        with self.store.connection() as db:
            rows = db.execute("""SELECT s.id, s.title, s.terminal_id, s.target_room, d.audience
                FROM schedules s JOIN reminder_details d ON d.schedule_id=s.id
                LEFT JOIN reminder_dispatch j ON j.schedule_id=s.id
                WHERE s.status='awaiting_delivery' AND j.schedule_id IS NULL
                ORDER BY s.due_at LIMIT 20""").fetchall()
        for row in rows:
            try:
                targets = self.announcements.select("room", row["target_room"])
                if len(targets) != 1:
                    raise HomeError("Destination ambiguë.")
                if row["terminal_id"] != "web-admin" and targets[0]["entity_id"] != row["terminal_id"]:
                    raise HomeError("Le terminal de création ne correspond plus à la pièce.")
            except (HomeError, ConfigurationError):
                self._claim(row["id"], "failed")
                continue
            if not self._claim(row["id"], "attempted"):
                continue
            try:
                result = self.announcements.send("Rappel : " + row["title"], "room", row["target_room"])
                phase = "sent" if not result["incomplete"] and len(result["accepted"]) == 1 else "failed"
            except Exception:
                phase = "failed"
            with self.store.connection() as db:
                db.execute("UPDATE reminder_dispatch SET phase=?, updated_at=? WHERE schedule_id=?",
                           (phase, utc_now().timestamp(), row["id"]))

    def _claim(self, identifier, phase):
        with self.store.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT status FROM schedules WHERE id=?", (identifier,)).fetchone()
            if row is None or row["status"] != "awaiting_delivery":
                return False
            result = db.execute("INSERT OR IGNORE INTO reminder_dispatch VALUES (?, ?, ?)",
                                (identifier, phase, utc_now().timestamp()))
            return result.rowcount == 1
