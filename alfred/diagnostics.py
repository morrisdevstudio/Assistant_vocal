"""Journal local borné, sans API réseau ni audio. python -m alfred.diagnostics."""
import argparse
from contextlib import contextmanager
import json
import re
import sqlite3
import threading
import time
from pathlib import Path
from uuid import uuid4

LABELS = ("correct", "transcription", "comprehension", "action", "cible")


def scrub(value):
    if isinstance(value, dict):
        return {k: ("[secret masqué]" if re.search(r"^(?:.*secret.*|.*password.*|(?:access_|refresh_)?token|api.?key|authorization)$", k, re.I)
                    else scrub(v)) for k, v in value.items() if k not in {"audio", "audio_base64"}}
    if isinstance(value, (list, tuple)):
        return [scrub(v) for v in value[:64]]
    if isinstance(value, str):
        value = re.sub(r"(?i)\bBearer\s+\S+|\b(?:sk-|cmd_)[\w-]{12,}", "[secret masqué]", value)
        value = re.sub(r"(?i)((?:(?:clé|cle)(?:\s+api)?|api.?key|password|mot de passe|token|jeton)\s*(?::|=|\best\b)\s*)\S+", r"\1[secret masqué]", value)
        return value[:8000]
    return value


class Diagnostics:
    def __init__(self, directory, *, clock=time.time, max_bytes=100 * 1024 * 1024):
        self.path = Path(directory) / "diagnostics.sqlite3"
        self.clock, self.max_bytes = clock, max_bytes
        self.lock = threading.Lock()

    @contextmanager
    def connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        new = not self.path.exists()
        db = sqlite3.connect(self.path, timeout=2)
        if new:
            self.path.chmod(0o600)
            db.execute("PRAGMA auto_vacuum=FULL")
        db.execute("PRAGMA journal_mode=DELETE")
        page = db.execute("PRAGMA page_size").fetchone()[0]
        db.execute(f"PRAGMA max_page_count={max(16, self.max_bytes // page)}")
        db.execute("CREATE TABLE IF NOT EXISTS exchanges (id TEXT PRIMARY KEY, created REAL NOT NULL, body TEXT NOT NULL, label TEXT, note TEXT)")
        db.execute("CREATE INDEX IF NOT EXISTS diagnostic_created ON exchanges(created)")
        try:
            with db:
                yield db
        finally:
            db.close()

    def purge(self, db):
        db.execute("DELETE FROM exchanges WHERE created < ?", (self.clock() - 7 * 86400,))
        # Garder une marge pour index, pages et prochaine insertion.
        budget = int(self.max_bytes * .65)
        while db.execute("SELECT COALESCE(SUM(LENGTH(body)+COALESCE(LENGTH(note),0)+256),0) FROM exchanges").fetchone()[0] > budget:
            db.execute("DELETE FROM exchanges WHERE id IN (SELECT id FROM exchanges ORDER BY created LIMIT 20)")

    def append(self, event):
        event = scrub(event)
        identifier = event.get("exchange_id") or uuid4().hex
        body = json.dumps(event, ensure_ascii=False)
        if len(body.encode()) > min(65536, self.max_bytes // 4):
            raise ValueError("Diagnostic trop volumineux")
        with self.lock, self.connect() as db:
            self.purge(db)
            db.execute("INSERT OR REPLACE INTO exchanges(id,created,body) VALUES(?,?,?)", (identifier, self.clock(), body))
            self.purge(db)
        return identifier

    def list(self, limit=100):
        with self.lock, self.connect() as db:
            self.purge(db)
            rows = db.execute("SELECT id,created,body,label,note FROM exchanges ORDER BY created DESC LIMIT ?", (max(1, min(limit, 10000)),)).fetchall()
        return [{"id": r[0], "created": r[1], **json.loads(r[2]), "annotation": r[3], "note": r[4]} for r in rows]

    def annotate(self, identifier, label, note=""):
        if label not in LABELS:
            raise ValueError("Annotation inconnue")
        with self.lock, self.connect() as db:
            self.purge(db)
            if not db.execute("UPDATE exchanges SET label=?,note=? WHERE id=?", (label, scrub(note)[:1000], identifier)).rowcount:
                raise ValueError("Échange introuvable ou expiré")


def main():
    from alfred.config import Settings
    parser = argparse.ArgumentParser(description="Historique Alfred local, sans accès réseau")
    parser.add_argument("--data-dir", type=Path, default=Settings.from_env().data_dir)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--export", type=Path)
    parser.add_argument("--annotate")
    parser.add_argument("--label", choices=LABELS)
    parser.add_argument("--note", default="")
    args = parser.parse_args()
    journal = Diagnostics(args.data_dir)
    if args.annotate:
        if not args.label:
            parser.error("--label requis avec --annotate")
        journal.annotate(args.annotate, args.label, args.note)
    result = json.dumps(journal.list(args.limit), ensure_ascii=False, indent=2)
    if args.export:
        args.export.write_text(result, encoding="utf-8")
        args.export.chmod(0o600)
    else:
        print(result)


if __name__ == "__main__":
    main()
