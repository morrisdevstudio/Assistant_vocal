"""Parcours vocal guidé sur le terminal ESP32 et export local des mesures."""
import argparse
from contextlib import suppress
import csv
from datetime import datetime
import json
from pathlib import Path
import re
import ssl
from statistics import median
import time

import httpx


ENDPOINT = "/api/terminal/light-trace"
ATTEMPTS = 3
TIMINGS = {
    "vad_ms": "Fin de parole → fermeture",
    "wake_ms": "Vérification du réveil",
    "capture_to_stt_ms": "Fermeture → début du STT",
    "stt_ms": "Transcription",
    "understanding_ms": "Texte final → décision",
    "transcript_to_model_ms": "Texte final → appel Command Code",
    "model_ms": "Appel Command Code → outil complet",
    "decision_to_send_ms": "Décision → premier envoi",
    "lock_ms": "Acquisition du verrou",
    "model_catalog_ms": "Catalogue pour le contexte du modèle",
    "catalog_ms": "Catalogue avant envoi, contexte compris",
    "pre_state_ms": "Lectures des états avant envoi",
    "first_service_ms": "Premier envoi → réponse HA",
    "speech_to_send_ms": "Fin de parole → premier envoi",
    "speech_to_first_on_ms": "Fin de parole → premier état on",
    "speech_to_last_on_ms": "Fin de parole → dernier état on",
    "first_to_last_on_ms": "Premier → dernier état on",
    "tts_ms": "Synthèse jusqu'au premier bloc",
    "speech_to_audio_ready_ms": "Fin de parole → audio prêt",
    "speech_to_audio_request_ms": "Fin de parole → demande audio ESP32",
}


def summarize(trace, case, attempt, expected, seen, first_try):
    events = trace["events"]

    def at(name):
        return next((e["ms"] for e in events if e["event"] == name), None)

    def span(start, end):
        return round(end - start, 2) if start is not None and end is not None else None

    def total(items):
        return round(sum(e["duration_ms"] for e in items), 2) if items else None

    sent = at("service_sent")
    before_send = events if sent is None else events[:next(
        i for i, e in enumerate(events) if e["event"] == "service_sent")]
    catalog = [e for e in before_send if e["event"] == "catalog_read"]
    model_start = at("model_request_started")
    model_catalog = [e for e in catalog if model_start is not None and e["ms"] <= model_start]
    states = [e for e in before_send if e["event"] == "state_read"]
    on = [e for e in events if e["event"] == "state_confirmed" and e["state"] == "on"]
    first_on = on[0]["ms"] if on else None
    last_on = on[-1]["ms"] if on else None
    speech_end = at("last_voice_detected")
    decision = at("model_tool_ready")
    if decision is None:
        decision = at("light_intent_ready")
    result = trace["result"]
    commands = [e for e in events if e["event"] == "service_sent"]
    dispatched = [target for command in commands for target in (command["targets"] or [])]
    confirmed = {e["target"] for e in on}
    success = (first_try and seen and result.get("status") == "confirmed"
               and set(dispatched) == confirmed == set(expected)
               and len(dispatched) == len(expected)
               and all(command["service"] == "turn_on" for command in commands))
    return {
        "case": case, "attempt": attempt, "exchange_id": result.get("exchange_id"),
        "route": result.get("route") or ("ai" if at("model_routed") is not None else None),
        "trace_state": trace["state"],
        "capture_reason": next((e["reason"] for e in events if e["event"] == "capture_closed"), None),
        "action_status": result.get("status"), "expected": " ".join(expected),
        "dispatched": " ".join(dispatched), "on_confirmed": " ".join(sorted(confirmed)),
        "physically_seen": seen, "single_utterance": first_try, "first_try_success": success,
        "vad_ms": span(speech_end, at("capture_closed")),
        "wake_ms": total([e for e in events if e["event"] == "wake_verification"]),
        "capture_to_stt_ms": span(at("capture_closed"), at("stt_started")),
        "stt_ms": total([e for e in events if e["event"] == "stt"]),
        "understanding_ms": span(at("transcript_final"), decision),
        "transcript_to_model_ms": span(at("transcript_final"), model_start),
        "model_ms": span(model_start, at("model_tool_ready")),
        "decision_to_send_ms": span(decision, sent),
        "lock_ms": total([e for e in before_send if e["event"] == "home_lock"]),
        "model_catalog_ms": total(model_catalog),
        "catalog_calls": len(catalog) if decision is not None or catalog else None,
        "catalog_ms": total(catalog),
        "pre_state_calls": len(states) if decision is not None or states else None,
        "pre_state_ms": total(states),
        "first_service_ms": next((span(sent, e["ms"]) for e in events
                                  if commands and e["event"] == "service_acknowledged"
                                  and e["targets"] == commands[0]["targets"]
                                  and e["service"] == commands[0]["service"]), None),
        "speech_to_send_ms": span(speech_end, sent),
        "speech_to_first_on_ms": span(speech_end, first_on),
        "speech_to_last_on_ms": span(speech_end, last_on),
        "first_to_last_on_ms": span(first_on, last_on),
        "tts_ms": total([e for e in events if e["event"] in {"tts", "tts_first_block"}]),
        "speech_to_audio_ready_ms": span(speech_end, at("audio_ready")),
        "speech_to_audio_request_ms": span(speech_end, at("audio_requested")),
    }


def write_report(directory, results):
    rows = [trial["row"] for trial in results]
    (directory / "traces.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    with (directory / "essais.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), delimiter=";")
        writer.writeheader()
        writer.writerows(rows)

    lines = ["# Latence de l’allumage sur l’ESP32", "",
             "Durées en millisecondes. Chaque cellule indique les essais dans l’ordre, puis la médiane "
             "des valeurs observées. « · » représente une étape absente.", ""]
    for case in dict.fromkeys(row["case"] for row in rows):
        trials = [row for row in rows if row["case"] == case]
        passed = sum(row["first_try_success"] for row in trials)
        lines.extend([f"## {case} · {passed}/{len(trials)} réussites au premier énoncé", "",
                      "| Mesure | Essais | Médiane |", "| --- | --- | --- |"])
        for key, label in TIMINGS.items():
            values = [row[key] for row in trials]
            observed = [value for value in values if value is not None]
            samples = " / ".join(f"{value:g}" if value is not None else "·" for value in values)
            middle = f"{median(observed):g}" if observed else "·"
            lines.append(f"| {label} | {samples} | {middle} |")
        lines.append("")
    (directory / "bilan.md").write_text("\n".join(lines), encoding="utf-8")


def arm(client):
    deadline = time.monotonic() + 35
    while True:
        response = client.post(ENDPOINT, json={})
        if response.status_code != 409 or time.monotonic() >= deadline:
            response.raise_for_status()
            return response.json()["id"]
        time.sleep(1)


def record(client, path):
    while True:
        response = client.get(path)
        response.raise_for_status()
        data = response.json()
        if data["state"] not in {"armed", "captured"}:
            return data
        time.sleep(.5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8765")
    parser.add_argument("--ca", type=Path, help="Certificat d’autorité ou certificat auto-signé pour le HTTPS local")
    parser.add_argument("--lampe", required=True, help="Nom prononcé de la lampe")
    parser.add_argument("--entite", required=True, help="Identifiant Home Assistant de la lampe")
    parser.add_argument("--piece", required=True, help="Nom de la pièce affiché dans Alfred")
    parser.add_argument("--du", required=True, help="Forme prononcée, par exemple « du bureau »")
    parser.add_argument("--dans", required=True, help="Forme prononcée, par exemple « dans le bureau »")
    parser.add_argument("--entites-piece", required=True, nargs="+", help="Lampes attendues dans la pièce")
    parser.add_argument("--sortie", type=Path, default=Path(".local/light-benchmark"))
    args = parser.parse_args()
    room_targets = list(dict.fromkeys(args.entites_piece))
    if len(room_targets) < 2 or any(not re.fullmatch(r"light\.[a-z0-9_]+", e) for e in [args.entite, *room_targets]):
        parser.error("Fournissez l’identifiant light.* de la lampe et au moins deux identifiants distincts pour la pièce.")
    cases = [
        ("Lampe nommée", f"Allume {args.lampe}.", [args.entite]),
        ("Pièce explicite", f"Allume la lumière {args.du}.", room_targets),
        ("Formulation polie", f"Tu peux m’allumer la lumière {args.du} ?", room_targets),
        ("Formulation naturelle", f"Je voudrais un peu de lumière {args.dans}.", room_targets),
        ("Plusieurs lampes", f"Allume les lumières {args.du}.", room_targets),
    ]
    tls = ssl.create_default_context(cafile=str(args.ca)) if args.ca else True
    directory = args.sortie / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    results = []
    print(f"Pièce : {args.piece}. Chaque essai comporte un seul énoncé, après le mot de réveil.")
    try:
        with httpx.Client(base_url=args.url, verify=tls, timeout=5, trust_env=False) as client:
            for attempt in range(1, ATTEMPTS + 1):
                for case, phrase, expected in cases:
                    input(f"\n{case} ({attempt}/{ATTEMPTS}). Éteins les cibles et attends la veille, puis Entrée. ")
                    path = f"{ENDPOINT}/{arm(client)}"
                    try:
                        print(f"Dis une fois : « {phrase} »")
                        trace = record(client, path)
                    except (KeyboardInterrupt, httpx.HTTPError):
                        with suppress(httpx.HTTPError):
                            client.delete(path).raise_for_status()
                        raise
                    print(f"Fin de mesure : {trace['state']}.")
                    seen = input("Toutes les lampes attendues se sont-elles réellement allumées ? [o/N] ").strip().lower() == "o"
                    first_try = input("La demande a-t-elle abouti sans répétition ni précision ? [o/N] ").strip().lower() == "o"
                    row = summarize(trace, case, attempt, expected, seen, first_try)
                    results.append({"phrase": phrase, "row": row, "events": trace["events"]})
                    directory.mkdir(parents=True, exist_ok=True)
                    write_report(directory, results)
    except (KeyboardInterrupt, EOFError):
        print("\nParcours interrompu.")
    except httpx.HTTPStatusError as error:
        parser.exit(1, f"Banc indisponible ({error.response.status_code}) : {error.response.text}\n")
    except httpx.HTTPError as error:
        parser.exit(1, f"Connexion au serveur Alfred impossible : {error}\n")
    if results:
        print(f"Bilan et traces : {directory.resolve()}")


if __name__ == "__main__":
    main()
