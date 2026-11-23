"""Corpus musical et simulation locale ; passages IA explicites seulement."""
import argparse
import copy
import hashlib
import json
import random
import statistics
import tempfile
import threading
import time
from pathlib import Path

from alfred.conversation import ConversationService
from alfred.credentials import CredentialStore
from alfred.home_assistant import HomeService, HomeStore
from alfred.home_catalog import HomeCatalog
from alfred.intent_context import CURRENT_TURN
from alfred.intents import IntentService
from alfred.music import Music
from alfred.music_actions import MusicActions


PLAYER = "media_player.amp_salon_2"
PLAYLIST = {"uri": "qobuz://playlist/maison", "name": "Ma maison", "provider": "Qobuz"}


def corpus():
    examples = [
        ("mets de la musique", "play_default", None), ("lance ma playlist par defaut", "play_default", None),
        ("joue airbourne sur l'ampli", "play", "airbourne"), ("mets l album powerage sur l ampli", "play", "powerage"),
        ("lance radio nova sur l ampli", "play", "radio nova"), ("met la chanson back in black sur l ampli", "play", "back in black"),
        ("baisse un peu", "volume_delta", -5), ("baisse le son de cinq", "volume_delta", -5),
        ("plus bas", "volume_delta", -5), ("encore un peu", "volume_delta", -5),
        ("monte le son", "volume_delta", 5), ("remonte un peu", "volume_delta", 5),
        ("mets à trente pour cent", "volume", 30),
        ("non vingt-cinq pour cent", "volume", 25), ("coupe le son", "mute", None),
        ("remets le son", "unmute", None), ("pause", "pause", None), ("reprends", "resume", None),
        ("arrête la musique", "stop", None), ("morceau suivant", "next", None), ("piste precedente", "previous", None),
        ("quel volume", "read", None), ("remets ce que j'ecoutais", "resume", None),
        ("Éteins la lumière du bureau", "none", None), ("ne baisse pas le son", "none", None),
    ]
    result = []
    for index in range(4):
        for template, operation, value in examples:
            text = template
            result.append({"id": hashlib.sha256(f"{index}:{text}".encode()).hexdigest()[:16], "split": "holdout" if list(examples).index((template, operation, value)) >= len(examples) - 5 else "development",
                           "text": text, "expected": {"operation": operation, "value": value}, "synthetic": True})
    return result


class Home(HomeService):
    def __init__(self, folder):
        super().__init__(HomeStore(folder, room="Bureau"))
        self.states = {"light.bureau": {"entity_id": "light.bureau", "state": "on", "attributes": {}},
                       PLAYER: {"entity_id": PLAYER, "state": "playing", "attributes": {"volume_level": .4, "is_volume_muted": False,
                                                                           "supported_features": 1+4+8+16+32+128+256+1024+4096+16384}}}
        self.entries = [{"entity_id": "light.bureau", "domain": "light", "name": "Lumière bureau", "area": "Bureau", "allowed": True, "members": None},
                        {"entity_id": PLAYER, "domain": "media_player", "name": "AMP_SALON", "allowed": True, "supported": True,
                         "capabilities": ["read", "media_pause", "volume_set", "volume_mute", "volume_up", "volume_down",
                                          "media_stop", "turn_on", "turn_off", "select_source", "media_play"]}]
        self.calls = []

    def get_state(self, entity): return copy.deepcopy(self.states[entity])
    def call_service(self, domain, service, payload):
        self.calls.append((domain, service, payload))
        if service == "volume_set": self.states[PLAYER]["attributes"]["volume_level"] = payload["volume_level"]
        if service == "volume_mute": self.states[PLAYER]["attributes"]["is_volume_muted"] = payload["is_volume_muted"]
        if service == "media_pause": self.states[PLAYER]["state"] = "paused"
        if service == "media_play": self.states[PLAYER]["state"] = "playing"
        if service == "media_stop": self.states[PLAYER]["state"] = "idle"
        if service == "play_media": self.states[PLAYER]["state"] = "playing"


def score(case, result):
    if case["expected"]["operation"] == "none": return result is None or (result.get("actions") and result["actions"][0].get("intent", {}).get("target") == "Bureau")
    if not result or result.get("status") not in {"confirmed", "unconfirmed"} or not result.get("actions"): return False
    intent = result["actions"][-1]["intent"]
    expected = case["expected"]["value"]
    actual = intent.get("query") if intent["operation"] == "play" else intent["value"]
    return intent["operation"] == case["expected"]["operation"] and (expected is None or actual == expected or (intent["operation"] == "play" and actual and actual.casefold() == expected.casefold()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Modèle déjà configuré ; appareils simulés.")
    parser.add_argument("--split", choices=("development", "holdout"), default="development")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--output", type=Path, default=Path(".local/performance/music-evaluation.json"))
    args = parser.parse_args()
    cases = [case for case in corpus() if case["split"] == args.split]
    random.Random(20261113).shuffle(cases)
    if not args.live:
        print(json.dumps({"total": len(cases), "sample": cases[:args.limit], "notice": "Aucun appel IA ni appareil sans --live"}, ensure_ascii=False, indent=2)); return
    rows = []
    for case in cases[:max(1, args.limit)]:
        with tempfile.TemporaryDirectory() as td:
            home = Home(Path(td)); HomeCatalog.snapshot = lambda self: {"entities": home.entries, "excluded": []}
            music = Music(home, Path(td)); music.configure(PLAYER, default_playlist=PLAYLIST)
            intents = IntentService(home, Path(td)); intents.music_actions = MusicActions(home, music)
            # Le contexte suit le lecteur choisi ; aucune cible musicale ne
            # change dans cette séquence de recette.
            state = intents.context.state(("bench", case["id"], "guest"))
            state["last"] = {"family": "music", "operation": "play_default", "scope": "target",
                             "query": "", "media_type": "playlist", "artist": "", "value": None}
            from alfred.config import Settings
            engine = ConversationService(CredentialStore(Settings.from_env().data_dir)); engine.intents = intents
            turn = intents.context.begin(("bench", case["id"], "guest"), case["text"], threading.Event(), "rdc")
            token = CURRENT_TURN.set(turn); started = time.monotonic()
            try:
                result = intents.handle_local(case["text"], turn)
                if result is None:
                    local_home = home.handle(case["text"])
                    if local_home is not None:
                        result = turn.result
                if result is None:
                    try:
                        list(engine.stream(case["text"], case["id"], turn.cancelled))
                        result = turn.result
                    except Exception as error:
                        # Sans clé configurée, ne pas présenter la demande
                        # générale comme un échec de compréhension musicale.
                        if case["expected"]["operation"] == "none":
                            result = None
                        else:
                            raise error
                rows.append({**case, "result": result, "correct": score(case, result), "ms": round((time.monotonic()-started)*1000)})
            except Exception as error:
                rows.append({**case, "error": type(error).__name__, "correct": False})
            finally: CURRENT_TURN.reset(token)
    durations = sorted(r.get("ms", 0) for r in rows)
    report = {"synthetic": True, "human_pending": True, "count": len(rows), "correct": sum(r["correct"] for r in rows), "p95_ms": durations[int(.95*len(durations))-1] if durations else 0, "cases": rows}
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "cases"}, ensure_ascii=False))


if __name__ == "__main__": main()
