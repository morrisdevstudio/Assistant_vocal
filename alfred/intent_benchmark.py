"""Recette synthétique reproductible du moteur ; pilote exclusivement en mémoire."""
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

from alfred.home_assistant import HomeService, HomeStore
from alfred.home_catalog import HomeCatalog
from alfred.intent_context import CURRENT_TURN
from alfred.intents import IntentService
from alfred.credentials import CredentialStore
from alfred.conversation import ConversationService


ROOMS = ("bureau", "salon", "cuisine", "chambre", "entrée")


def corpus():
    # Chaque famille de formulation est entièrement développement ou validation.
    # Aucun de ces exemples n'est présenté comme un essai humain.
    forms = [
        ("Éteins la lumière {room}.", "turn_off", None),
        ("Tu peux m'éteindre les lampes {room} ?", "turn_off", None),
        ("Je voudrais que tu éteignes les lumières {room}.", "turn_off", None),
        ("Fais le noir {where}.", "turn_off", None),
        ("Coupe l'éclairage {room}, merci.", "turn_off", None),
        ("Les lumières {room}, éteins-les.", "turn_off", None),
        ("{where}, je voudrais que tu coupes les lampes.", "turn_off", None),
        ("Pourrais-tu arrêter l'éclairage {room} ?", "turn_off", None),
        ("On éteint toutes les lumières {room}.", "turn_off", None),
        ("Éteins-moi toutes les lampes {room} s'il de plaît.", "turn_off", None),
        ("Allume la lumière {room}.", "turn_on", None),
        ("Je voudrais un peu de lumière {where}.", "turn_on", None),
        ("Éclaire {name}.", "turn_on", None),
        ("Mets la lumière {where}.", "turn_on", None),
        ("{where}, allume l'éclairage.", "turn_on", None),
        ("Les lampes {room}, tu peux les allumer ?", "turn_on", None),
        ("Je veux que tu allumes les lumières {room}.", "turn_on", None),
        ("Tu veux bien m'allumer la lumière {room} ?", "turn_on", None),
        ("Rallume les lampes {room} s'il te plaît.", "turn_on", None),
        ("Mets en marche l'éclairage {room}.", "turn_on", None),
        ("Mets les lumières {room} à trente pour cent.", "brightness", 30),
        ("Règle l'intensité {room} sur cinquante pour cent.", "brightness", 50),
        ("Je voudrais la lumière {room} à soixante pour cent.", "brightness", 60),
        ("Passe les lampes {room} à vingt pour cent.", "brightness", 20),
        ("{where}, règle les lumières à quarante pour cent.", "brightness", 40),
        ("La luminosité {room}, mets-la à quatre-vingts pour cent.", "brightness", 80),
        ("Peux-tu mettre l'éclairage {room} à dix pour cent ?", "brightness", 10),
        ("Mets l'intensité au maximum {where}.", "brightness", 100),
        ("Lumière à soixante-dix pour cent {where}.", "brightness", 70),
        ("{where}, je veux les lampes à quatre-vingt-dix pour cent.", "brightness", 90),
        ("Baisse un peu la lumière {room}.", "brightness_delta", -10),
        ("Augmente un peu l'éclairage {room}.", "brightness_delta", 10),
        ("Diminue la luminosité de dix points {room}.", "brightness_delta", -10),
        ("Monte les lumières de vingt points {room}.", "brightness_delta", 20),
        ("Réduis l'intensité {room} de cinq points.", "brightness_delta", -5),
        ("La lumière {room}, augmente-la de cinq points.", "brightness_delta", 5),
        ("{where}, baisse l'éclairage de quinze points.", "brightness_delta", -15),
        ("Un peu plus de lumière {room}, augmente de dix points.", "brightness_delta", 10),
        ("{where}, réduis la lumière de vingt points.", "brightness_delta", -20),
        ("Ajoute quinze points de luminosité {room}.", "brightness_delta", 15),
        ("Mets la lumière {room} en bleu.", "color", "bleu"),
        ("Passe les lampes {room} en rouge.", "color", "rouge"),
        ("Je voudrais un éclairage vert {room}.", "color", "vert"),
        ("Choisis la couleur jaune pour les lampes {room}.", "color", "jaune"),
        ("{where}, mets les lumières en rose.", "color", "rose"),
        ("La lumière {room}, je la veux violette.", "color", "violet"),
        ("Éclairage orange {where}, s'il vous plaît.", "color", "orange"),
        ("Colore en bleu l'éclairage {room}.", "color", "bleu"),
        ("Pourrais-tu passer au rouge {where} pour les lampes ?", "color", "rouge"),
        ("Je veux les lampes {room} en blanc.", "color", "blanc"),
        ("Mets le blanc à trois mille kelvins {where}.", "temperature", 3000),
        ("Règle la température de blanc {room} sur quatre mille kelvins.", "temperature", 4000),
        ("{where}, passe les lumières à deux mille sept cents kelvins.", "temperature", 2700),
        ("Je voudrais un blanc à cinq mille kelvins {where}.", "temperature", 5000),
        ("La température des lampes {room}, mets-la à trois mille cinq cents kelvins.", "temperature", 3500),
        ("Blanc à six mille kelvins {where}, merci.", "temperature", 6000),
        ("Passe l'éclairage {room} à quatre mille cinq cents kelvins.", "temperature", 4500),
        ("Choisis trois mille deux cents kelvins pour les lampes {room}.", "temperature", 3200),
        ("{where}, je veux un blanc de deux mille kelvins.", "temperature", 2000),
        ("Mets six mille cinq cents kelvins pour les lumières {room}.", "temperature", 6500),
        ("La lumière {room} est-elle allumée ?", "read", None),
        ("Quel est l'état des lampes {room} ?", "read", None),
        ("Dis-moi si l'éclairage {room} fonctionne en ce moment.", "read", None),
        ("Regarde si les lumières {room} sont éteintes.", "read", None),
        ("{where}, les lumières sont allumées ou éteintes ?", "read", None),
        ("Peux-tu lire l'état de la lampe {room} ?", "read", None),
        ("Je voudrais savoir si la lumière {room} est allumée.", "read", None),
        ("Vérifie l'état de l'éclairage {room}.", "read", None),
        ("Est-ce qu'il reste des lampes allumées {room} ?", "read", None),
        ("Informe-moi sur l'état des lumières {room}.", "read", None),
        ("N'éteins pas la lumière {room}.", "none", None),
        ("N'allume pas les lampes {room}.", "none", None),
        ("Hier j'ai éteint les lumières {room}.", "none", None),
        ("Si j'étais {where}, j'allumerais les lumières.", "none", None),
        ("Quand je dis « éteins la lumière {room} », c'est un exemple.", "none", None),
        ("Explique pourquoi une lumière clignote {room}.", "none", None),
        ("Demain, je te demanderai d'éteindre la lumière {room}.", "none", None),
        ("Est-ce que tu sais commander les lumières {room} ?", "none", None),
        ("Je ne veux pas que tu changes les lumières {room}.", "none", None),
        ("Ne touche pas à l'éclairage {room}.", "none", None),
        ("On n'y voit rien {where}.", "propose", None),
        ("Il fait sombre {where}.", "propose", None),
        ("C'est sombre {where}.", "propose", None),
        ("Il fait noir {where}.", "propose", None),
        ("On manque de lumière {where}.", "propose", None),
        ("C'est vraiment obscur {where}.", "propose", None),
        ("J'ai du mal à voir {where}.", "propose", None),
        ("Il n'y a pas assez de lumière {where}.", "propose", None),
        ("Je trouve l'éclairage insuffisant {room}.", "propose", None),
        ("On est dans le noir {where}.", "propose", None),
        ("Éteins la lumière {room}, puis rallume-la.", "sequence", None),
        ("Coupe les lampes {room} et rallume-les.", "sequence", None),
        ("Éteins et rallume les lumières {room}.", "sequence", None),
        ("Je veux que tu éteignes les lumières {room} puis que tu rallumes.", "sequence", None),
        ("{where}, coupe la lumière puis remets-la.", "sequence", None),
        ("Peux-tu éteindre puis rallumer les lampes {room} ?", "sequence", None),
        ("Extinction puis allumage de la lumière {room}, merci.", "sequence", None),
        ("La lumière {room}, éteins-la et ensuite rallume-la.", "sequence", None),
        ("Fais le noir {where}, puis allume à nouveau.", "sequence", None),
        ("{where}, arrête l'éclairage puis remets-le en marche.", "sequence", None),
    ]
    result = []
    for index, (template, op, value) in enumerate(forms):
        for room in ROOMS:
            room_phrase = "de l'entrée" if room == "entrée" else "de la " + room if room in {"cuisine", "chambre"} else "du " + room
            where = "dans l'entrée" if room == "entrée" else "dans la " + room if room in {"cuisine", "chambre"} else "dans le " + room
            text = template.format(room=room_phrase, where=where, name=room)
            result.append({"id": hashlib.sha256(text.encode()).hexdigest()[:16], "source": "synthetic", "template": index,
                           "split": "holdout" if index % 5 == 4 else "development", "text": text,
                           "expected": {"operation": op, "entity": "light." + ("entree" if room == "entrée" else room), "value": value}})
    return result


class SimulatedHome(HomeService):
    """Aucun appel HTTP Home Assistant : les seules écritures touchent ce dictionnaire."""
    def __init__(self, directory):
        super().__init__(HomeStore(directory, room="Bureau"))
        attrs = {"supported_color_modes": ["rgb", "color_temp"], "brightness": 128,
                 "min_color_temp_kelvin": 2000, "max_color_temp_kelvin": 6500}
        self.states, self.entries, self.writes = {}, [], []
        for room in ROOMS:
            e = "light." + ("entree" if room == "entrée" else room)
            self.states[e] = {"entity_id": e, "state": "on", "attributes": dict(attrs)}
            self.entries.append({"entity_id": e, "domain": "light", "area": room.title(), "name": "Lumière " + room,
                                 "allowed": True, "members": None, "aliases": [], "ha_aliases": [], "capabilities": ["turn_on", "turn_off", "read", "brightness", "brightness_delta", "color", "temperature"]})

    def get_state(self, e):
        return copy.deepcopy(self.states[e])

    def call_service(self, domain, service, payload):
        if domain != "light" or service not in {"turn_on", "turn_off"}:
            raise AssertionError("Service interdit dans ce simulateur")
        self.writes.append((domain, service, payload))
        for e in payload["entity_id"]:
            state = self.states[e]
            state["state"] = "on" if service == "turn_on" else "off"
            if "brightness_pct" in payload:
                state["attributes"]["brightness"] = round(payload["brightness_pct"] * 255 / 100)
            for key in ("rgb_color", "color_temp_kelvin"):
                if key in payload:
                    state["attributes"][key] = payload[key]


def score(case, result, writes):
    expected = case["expected"]
    if expected["operation"] == "none":
        return not writes
    if expected["operation"] == "propose":
        return not writes and result is not None and result["status"] == "clarification" and any(
            a["targets"] == [expected["entity"]] for a in result.get("proposal", []))
    if not result or result["status"] != "confirmed":
        return False
    actions = result["actions"]
    if expected["operation"] == "sequence":
        return len(actions) == 2 and [a["intent"]["operation"] for a in actions] == ["turn_off", "turn_on"] and all(a["targets"] == [expected["entity"]] for a in actions)
    if len(actions) != 1:
        return False
    a = actions[0]
    value = a["intent"]["value"]
    if isinstance(value, str):
        value = {"bleue": "bleu", "verte": "vert", "violette": "violet", "blanche": "blanc"}.get(value, value)
    return a["targets"] == [expected["entity"]] and a["intent"]["operation"] == expected["operation"] and value == expected["value"]


def main():
    from alfred.config import Settings
    parser = argparse.ArgumentParser(description="Recette de compréhension sans appareil réel")
    parser.add_argument("--live", action="store_true", help="Appeler le modèle déjà configuré, quota GOAT consommé ; appareils simulés")
    parser.add_argument("--split", choices=("development", "holdout"), default="development")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--output", type=Path, default=Settings.from_env().data_dir.parent / "performance" / "intent-evaluation.json")
    args = parser.parse_args()
    cases = [c for c in corpus() if c["split"] == args.split]
    random.Random(20261113).shuffle(cases)
    cases = cases[:max(1, args.limit)]
    if not args.live:
        print(json.dumps({"synthetic_total": len(corpus()), "selected": cases, "notice": "Aucun appel IA ni appareil. Ajouter --live pour mesurer la compréhension."}, ensure_ascii=False, indent=2))
        return
    results = []
    original = HomeCatalog.snapshot
    try:
        for case in cases:
            with tempfile.TemporaryDirectory() as directory:
                home = SimulatedHome(Path(directory))
                HomeCatalog.snapshot = lambda self: {"entities": home.entries}
                service = IntentService(home, Path(directory))
                home.intent_service = service
                engine = ConversationService(CredentialStore(Settings.from_env().data_dir))
                engine.intents = service
                turn = service.context.begin(("benchmark", case["id"], "guest"), case["text"], threading.Event(), "rdc")
                token = CURRENT_TURN.set(turn)
                start = time.monotonic()
                usage = {}
                try:
                    result = service.handle_local(turn.text, turn)
                    if result is None:
                        local = home.handle(turn.text)
                        if local is None:
                            for event in engine.stream(turn.text, case["id"], turn.cancelled):
                                usage = event.get("usage", usage)
                        result = turn.result
                    ok = score(case, result, home.writes)
                    detail = {"result": result, "usage": usage}
                except Exception as error:
                    ok, detail = False, {"error": type(error).__name__}
                finally:
                    CURRENT_TURN.reset(token)
                results.append({**case, **detail, "correct": ok, "ms": round((time.monotonic()-start)*1000)})
                print(f"{len(results)}/{len(cases)} {'OK' if ok else 'ECHEC'} {case['id']}", flush=True)
    finally:
        HomeCatalog.snapshot = original
    durations = sorted(r["ms"] for r in results)
    report = {"synthetic_only": True, "human_validation_pending": True, "split": args.split, "count": len(results),
              "correct": sum(r["correct"] for r in results), "median_ms": statistics.median(durations),
              "p95_ms": durations[max(0, int(.95*len(durations)+.999)-1)], "cases": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k != "cases"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
