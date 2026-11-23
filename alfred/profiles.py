"""Profils familiaux et empreintes vocales : aucun audio brut n'est conservé."""

import math
import re
import shutil
import struct
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .storage import utc_now

ROLES = ("adult", "child")


def clean_name(name):
    if not isinstance(name, str):
        raise ValueError("Le nom du profil doit être un texte.")
    cleaned = " ".join(name.split())
    if not cleaned or len(cleaned) > 40:
        raise ValueError("Le nom doit contenir entre 1 et 40 caractères.")
    return cleaned


def encode_vector(vector):
    values = [float(value) for value in vector]
    if not values:
        raise ValueError("Empreinte vide.")
    if any(not math.isfinite(value) for value in values):
        raise ValueError("Empreinte non finie.")
    return struct.pack("<%df" % len(values), *values), len(values)


def decode_vector(blob):
    return list(struct.unpack("<%df" % (len(blob) // 4), blob))


def cosine(left, right):
    if not left or len(left) != len(right):
        raise ValueError("Empreintes de dimensions différentes.")
    dot = sum(a * b for a, b in zip(left, right))
    norm_left = math.sqrt(sum(a * a for a in left))
    norm_right = math.sqrt(sum(b * b for b in right))
    if norm_left == 0 or norm_right == 0:
        return 0.0
    return dot / (norm_left * norm_right)


def _iso(timestamp):
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat()


class Profiles:
    """Stockage des identités et de leurs empreintes ; la reconnaissance viendra après."""

    def __init__(self, store, audio_root=None):
        self.store = store
        self.audio_root = Path(audio_root) if audio_root else store.path.parent / "profiles"

    def create(self, name, role="adult"):
        name = clean_name(name)
        if role not in ROLES:
            raise ValueError("Rôle inconnu.")
        identifier = uuid4().hex
        now = utc_now().timestamp()
        with self.store.connection() as db:
            try:
                db.execute(
                    "INSERT INTO profiles VALUES (?, ?, ?, ?, ?)",
                    (identifier, name, role, now, now),
                )
            except Exception as error:
                if "UNIQUE" in str(error):
                    raise ValueError("Un profil porte déjà ce nom.") from error
                raise
        return self.get(identifier)

    def get(self, identifier):
        with self.store.connection() as db:
            row = db.execute(
                """SELECT p.*, (SELECT COUNT(*) FROM voiceprints v WHERE v.profile_id=p.id)
                AS samples FROM profiles p WHERE p.id=?""",
                (identifier,),
            ).fetchone()
        return self._record(row) if row else None

    def list(self):
        with self.store.connection() as db:
            rows = db.execute(
                """SELECT p.*, (SELECT COUNT(*) FROM voiceprints v WHERE v.profile_id=p.id)
                AS samples FROM profiles p ORDER BY p.created_at"""
            ).fetchall()
        return [self._record(row) for row in rows]

    def rename(self, identifier, name):
        name = clean_name(name)
        with self.store.connection() as db:
            try:
                result = db.execute(
                    "UPDATE profiles SET name=?, updated_at=? WHERE id=?",
                    (name, utc_now().timestamp(), identifier),
                )
            except Exception as error:
                if "UNIQUE" in str(error):
                    raise ValueError("Un profil porte déjà ce nom.") from error
                raise
        return self.get(identifier) if result.rowcount else None

    def delete(self, identifier):
        with self.store.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("""SELECT 1 FROM reminder_details d JOIN schedules s ON s.id=d.schedule_id
                             WHERE d.owner_id=? AND s.status IN ('pending','awaiting_delivery','missed') LIMIT 1""", (identifier,)).fetchone():
                raise ValueError("Ce profil possède des rappels à traiter ou à annuler avant sa suppression.")
            db.execute("DELETE FROM voiceprints WHERE profile_id=?", (identifier,))
            result = db.execute("DELETE FROM profiles WHERE id=?", (identifier,))
        if result.rowcount:
            shutil.rmtree(self.audio_root / identifier, ignore_errors=True)
        return bool(result.rowcount)

    def save_audio(self, profile_id, data):
        if not self.get(profile_id):
            raise ValueError("Profil inconnu.")
        directory = self.audio_root / profile_id
        directory.mkdir(parents=True, exist_ok=True)
        name = uuid4().hex + ".wav"
        (directory / name).write_bytes(data)
        return name

    def audio_path(self, profile_id, name):
        if not re.fullmatch(r"[0-9a-f]{32}[.]wav", name or ""):
            return None
        path = self.audio_root / profile_id / name
        return path if path.is_file() else None

    def add_voiceprint(self, profile_id, vector, model, duration_seconds, audio_file=None):
        if not self.get(profile_id):
            raise ValueError("Profil inconnu.")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("Modèle d'empreinte manquant.")
        try:
            duration = float(duration_seconds)
        except (TypeError, ValueError) as error:
            raise ValueError("Durée d'échantillon invalide.") from error
        if not math.isfinite(duration) or duration <= 0 or duration > 60:
            raise ValueError("Durée d'échantillon hors limites.")
        blob, dimensions = encode_vector(vector)
        identifier = uuid4().hex
        with self.store.connection() as db:
            db.execute(
                "INSERT INTO voiceprints VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (identifier, profile_id, blob, dimensions, model.strip(), duration,
                 utc_now().timestamp(), audio_file),
            )
        return identifier

    def samples(self, profile_id):
        with self.store.connection() as db:
            rows = db.execute(
                """SELECT audio_file, duration_seconds, created_at FROM voiceprints
                WHERE profile_id=? AND audio_file IS NOT NULL ORDER BY created_at""",
                (profile_id,),
            ).fetchall()
        return [{"audio_file": row["audio_file"],
                 "duration_seconds": row["duration_seconds"],
                 "created_at": _iso(row["created_at"])} for row in rows]

    def clear_voiceprints(self, profile_id):
        with self.store.connection() as db:
            result = db.execute("DELETE FROM voiceprints WHERE profile_id=?", (profile_id,))
        return result.rowcount

    def reset(self, profile_id):
        """Réenrôlement complet : empreintes et fichiers audio du profil."""
        if not self.get(profile_id):
            raise ValueError("Profil inconnu.")
        count = self.clear_voiceprints(profile_id)
        shutil.rmtree(self.audio_root / profile_id, ignore_errors=True)
        return count

    def centroid(self, profile_id, model):
        with self.store.connection() as db:
            rows = db.execute(
                "SELECT vector, dimensions FROM voiceprints WHERE profile_id=? AND model=?",
                (profile_id, model),
            ).fetchall()
        if not rows:
            return None
        dimensions = rows[0]["dimensions"]
        vectors = [decode_vector(row["vector"]) for row in rows]
        if any(len(vector) != dimensions for vector in vectors):
            raise ValueError("Empreintes de dimensions différentes.")
        total = [0.0] * dimensions
        for vector in vectors:
            for index, value in enumerate(vector):
                total[index] += value
        return [value / len(vectors) for value in total]

    def enrollment_vectors(self, model):
        """Empreintes ordonnées localement pour la calibration ; jamais renvoyées par l'API."""
        with self.store.connection() as db:
            profiles = db.execute("SELECT id, role FROM profiles ORDER BY id").fetchall()
            result = []
            for profile in profiles:
                rows = db.execute("SELECT id, vector FROM voiceprints WHERE profile_id=? AND model=? ORDER BY created_at,id",
                                  (profile["id"], model)).fetchall()
                result.append({"id":profile["id"], "role":profile["role"],
                               "samples":[{"id":row["id"], "vector":decode_vector(row["vector"])} for row in rows]})
            return result

    def identify(self, vector, model, threshold):
        try:
            threshold = float(threshold)
        except (TypeError, ValueError) as error:
            raise ValueError("Seuil invalide.") from error
        if not 0 <= threshold <= 1:
            raise ValueError("Le seuil doit être compris entre 0 et 1.")
        encode_vector(vector)
        best = None
        for profile in self.list():
            if not profile["samples"]:
                continue
            centroid = self.centroid(profile["id"], model)
            if centroid is None or len(centroid) != len(vector):
                continue
            score = cosine(vector, centroid)
            if best is None or score > best["score"]:
                best = {"profile_id": profile["id"], "name": profile["name"], "score": score}
        if best is None or best["score"] < threshold:
            return None
        return best

    @staticmethod
    def _record(row):
        return {
            "id": row["id"],
            "name": row["name"],
            "role": row["role"],
            "samples": row["samples"] if "samples" in row.keys() else 0,
            "created_at": _iso(row["created_at"]),
            "updated_at": _iso(row["updated_at"]),
        }

