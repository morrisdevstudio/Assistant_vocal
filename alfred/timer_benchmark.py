"""Recette synthétique des minuteurs ; stockage temporaire et IA seulement sur --live."""
import argparse
import hashlib
import json
import random
import tempfile
import threading
import time
from pathlib import Path

from alfred.storage import Store
from alfred.timers import TimerService
from alfred.intent_context import Turn
from alfred.intents import IntentService
from alfred.timer_actions import TimerActions, TimerPlan
from alfred.conversation import ConversationService
from alfred.credentials import CredentialStore
from alfred.config import Settings


def corpus():
    examples = [
        ("mets un minuteur de huit minutes", "create", 480),
        ("lance un minuteur d'une heure", "create", 3600),
        ("dans cinq minutes, mets un minuteur", "create", 300),
        ("rappelle-moi dans cinq minutes avec un minuteur", "create", 300),
        ("programme une minuterie de deux minutes trente", "create", 150),
        ("cree un minuteur pour une demi-heure", "create", 1800),
        ("ajoute deux minutes au minuteur", "create", 120),
        ("ajoute encore une minute au minuteur", "create", 60),
        ("minuteur de dix secondes", "create", 10),
        ("mets moi un minuteur de sept minutes quarante", "create", 460),
        ("mets un minuteur de quatre-vingt-dix secondes", "create", 90),
        ("mets un minuteur de un jour", "create", 86400),
        ("liste les minuteurs", "list", None),
        ("quels sont les minuteurs", "list", None),
        ("combien de temps reste-t-il", "list", None),
        ("annule le minuteur", "cancel", None),
        ("annule le minuteur deux", "cancel", None),
        ("arrete la sonnerie", "stop", None),
        ("ne mets pas de minuteur", "clarify", None),
        ("explique comment fonctionne un minuteur", "none", None),
        ("mets un minuteur de zéro seconde", "clarify", None),
        ("mets un minuteur de huit minutes et allume la lumière", "clarify", None),
        ("annule tous les minuteurs", "clarify", None),
        ("mets un minuteur de deux heures trois heures", "clarify", None),
        ("raconte une blague", "none", None),
        ("mets un minuteur de huit minutes s'il te plaît", "create", 480),
    ]
    result = []
    for i in range(4):
        for index, (text, operation, seconds) in enumerate(examples):
            result.append({"id": hashlib.sha256(f"timer:{i}:{text}".encode()).hexdigest()[:16],
                           "text": text, "split": "holdout" if index >= len(examples)-5 else "development",
                           "expected": {"operation": operation, "seconds": seconds}})
    return result


def score(case, result):
    expected = case["expected"]
    if expected["operation"] == "clarify":
        return bool(result and result.get("status") in {"clarification", "none"})
    if expected["operation"] == "none":
        return result is None
    if not result or not result.get("actions"):
        return False
    first = result["actions"][0]["intent"]
    return first["operation"] == expected["operation"] and (expected["seconds"] is None or first["seconds"] == expected["seconds"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--split", choices=("development", "holdout"), default="development")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--output", type=Path, default=Path(".local/performance/timers.json"))
    args = parser.parse_args()
    cases = [x for x in corpus() if x["split"] == args.split]
    random.Random(20261113).shuffle(cases); cases = cases[:max(1, args.limit)]
    if not args.live:
        print(json.dumps({"total": len(corpus()), "sample": cases[:args.limit], "notice": "Aucun appel IA ni modification d'échéance sans --live"}, ensure_ascii=False, indent=2)); return
    rows = []
    for case in cases:
        with tempfile.TemporaryDirectory() as td:
            store = Store(Path(td)); store.initialize(); timers = TimerService(store)
            intents = IntentService(None, Path(td)); intents.timers = timers
            turn = intents.context.begin(("bench", case["id"], "guest"), case["text"], threading.Event(), "rdc")
            started = time.monotonic(); result = intents.handle_local(case["text"], turn)
            if result is None:
                # Les phrases de compréhension douteuse doivent être mesurées
                # sans réseau ; seulement un tour général explicite consomme le
                # modèle configuré et son quota.
                if case["expected"]["operation"] in {"clarify", "none"}:
                    rows.append({**case, "result": result, "correct": score(case, result), "ms": 0})
                    continue
                engine = ConversationService(CredentialStore(Settings.from_env().data_dir)); engine.intents = intents
                try:
                    list(engine.stream(case["text"], case["id"], turn.cancelled)); result = turn.result
                except Exception as error:
                    result = {"status": "error", "error": type(error).__name__}
            rows.append({**case, "result": result, "correct": score(case, result), "ms": round((time.monotonic()-started)*1000)})
    report = {"synthetic": True, "human_pending": True, "count": len(rows), "correct": sum(x["correct"] for x in rows), "cases": rows}
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k != "cases"}, ensure_ascii=False))


if __name__ == "__main__": main()
