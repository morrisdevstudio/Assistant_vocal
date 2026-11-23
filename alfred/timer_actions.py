"""Intentions de minuteurs et exécution par le service historique borné."""
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from alfred.home_assistant import HomeError, normalize
from alfred.timers import TimerService, duration, is_current_timer_query, number, spoken_duration


class TimerAction(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    operation: Literal["create", "list", "remaining", "cancel", "stop"]
    seconds: int | None = Field(default=None, ge=1, le=604800)
    number: int | None = Field(default=None, ge=1)
    name: str | None = Field(default=None, min_length=1, max_length=160)
    relation: Literal["new", "add"] = "new"

    @model_validator(mode="after")
    def valid_fields(self):
        if self.operation == "create" and self.number is not None:
            raise ValueError("Création avec numéro interdite")
        if self.operation == "cancel" and self.seconds is not None:
            raise ValueError("Annulation avec durée interdite")
        if self.operation in {"list", "remaining", "stop"} and (self.seconds is not None or self.number is not None):
            raise ValueError("Paramètres de minuteur incompatibles")
        if self.name is not None:
            self.name = self.name.strip()
            if not self.name or self.number is not None or self.operation in {"list", "stop"}:
                raise ValueError("Nom de minuteur incompatible")
        return self


class TimerPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    actions: list[TimerAction] = Field(min_length=1, max_length=4)


class TimerActions:
    def __init__(self, timers: TimerService):
        self.timers = timers

    def run(self, actions, turn, now=None, current_timer=False):
        if turn.floor not in {"rdc", "etage1"}:
            return {"status": "clarification", "actions": [],
                    "reply": "Choisissez d'abord l'étage de ce terminal."}
        results = []
        for action in actions:
            if turn.cancelled.is_set():
                return {"status": "partial" if results else "cancelled", "actions": results,
                        "reply": "Demande interrompue ; les minuteurs déjà créés restent actifs."}
            if action.operation == "create":
                if action.seconds is None:
                    return {"status": "clarification", "actions": results,
                            "reply": "Quelle durée pour le minuteur ?"}
                text = f"mets un minuteur de {action.seconds} secondes"
            elif action.operation == "cancel":
                text = "annule le minuteur" + (f" {action.number}" if action.number is not None else "")
            else:
                text = "liste les minuteurs" if action.operation == "list" else "stop"
                if action.operation == "remaining" or (action.operation == "list" and current_timer):
                    text = "quel temps reste-t-il sur le minuteur"
            value = self.timers.handle(text, turn.floor, terminal_id=turn.key[1], now=now, name=action.name)
            status = "clarification" if value["action"] == "clarify" else "confirmed"
            results.append({"family": "timer", "intent": action.model_dump(), "status": status,
                            "reply": (("Ajout de " if action.relation == "add" else "") + value["text"]), "number": (value.get("item") or {}).get("number")})
            if status == "clarification":
                return {"status": "clarification", "actions": results, "reply": value["text"]}
        return {"status": "confirmed", "actions": results,
                "reply": " ".join(x["reply"] for x in results)}

    def local(self, phrase, turn):
        """Formulations usuelles, exécutées par le même run()."""
        p = normalize(phrase).strip(" .!?")
        if re.match(r"(?:ne |n'|pas de|sans )", p) and "minuteur" in p:
            return {"status": "clarification", "actions": [], "reply": "Je ne crée pas de minuteur sur une phrase négative."}
        if is_current_timer_query(p):
            return self.run([TimerAction(operation="list")], turn, current_timer=True)
        named_query = re.fullmatch(r"(.+ (?:sur|pour) (?:le|mon) minuteur) (.{1,160})", p)
        if named_query and is_current_timer_query(named_query[1]):
            return self.run([TimerAction(operation="remaining", name=named_query[2])], turn)
        if p in {"quels sont les minuteurs", "liste les minuteurs", "liste mes minuteurs"}:
            return self.run([TimerAction(operation="list")], turn)
        if p in {"arrete la sonnerie", "arrete les sonneries"}:
            return self.run([TimerAction(operation="stop")], turn)
        cancel = re.fullmatch(r"(?:annule|arrete|coupe) (?:le|mon) minuteur(?: numero)?(?: (.{1,160}))?", p)
        if cancel:
            numeric = number(cancel[1]) if cancel[1] else None
            if cancel[1] and numeric is None:
                return self.run([TimerAction(operation="cancel", name=cancel[1])], turn)
            return self.run([TimerAction(operation="cancel", number=numeric)], turn)
        if re.fullmatch(r"(?:annule|arrete|coupe) (?:(?:tous|toutes) )?(?:les |mes )?minuteurs", p):
            return {"status": "clarification", "actions": [], "reply": "Quel minuteur voulez-vous annuler ? Vous pouvez le choisir dans Minuteries."}
        create = re.fullmatch(r"(?:(?:on met|mets?|lance|demarre|cree|programme)\s+)?(?:moi\s+)?(?:un |une |le |la )?(?:minuteur|minuterie|alarme)\s+(?:de |pour |dans |dans environ )?(.+)", p)
        if create and create[1].strip() == "un jour":
            return self.run([TimerAction(operation="create", seconds=86400)], turn)
        if not create:
            create = re.fullmatch(r"(?:dans|d'ici)\s+(.+?)\s*,?\s+(?:mets?|lance|demarre|cree)\s+(?:moi\s+)?(?:un |une )?minuteur", p)
        if create and duration(create[1].removeprefix("d'").removeprefix("de ").replace("d'une", "une").strip() or "une heure") is not None:
            raw = create[1].removeprefix("d'").removeprefix("de ").strip()
            if raw.startswith("d'une heure"):
                raw = "une heure"
            elif raw.startswith("de une heure"):
                raw = "une heure"
            seconds = duration(raw)
            if seconds is not None:
                if seconds < 1:
                    return {"status": "clarification", "actions": [], "reply": "La durée doit être positive."}
                return self.run([TimerAction(operation="create", seconds=seconds)], turn)
        else:
            create_any = re.search(r"(?:dans|d'ici)\s+([a-z0-9-]+(?: [a-z0-9-]+)?)\s+(?:minutes?|m)\b", p)
            if create_any:
                amount = create_any[1]
                # Le test de recherche du mot entier a été conservé ; accepter
                # explicitement les nombres en lettres et l'unité « minute ».
                seconds = duration(amount + " minute")
                if seconds is not None and ("minuteur" in p or "minuterie" in p):
                    return self.run([TimerAction(operation="create", seconds=seconds)], turn)
        add = re.fullmatch(r"(?:ajoute|rajoute) (?:encore )?(.+?)(?: au minuteur)?", p)
        if add and duration(add[1]) is not None and "minuteur" in p:
            seconds = duration(add[1])
            if seconds is not None:
                return self.run([TimerAction(operation="create", seconds=seconds, relation="add")], turn)
        return None
