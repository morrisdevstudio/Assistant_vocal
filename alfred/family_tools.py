"""Extensions de compréhension, activables après recette de chaque famille."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from alfred.home_assistant import HomeError, normalize
from alfred.home_commands import HomeCommands
from alfred.timer_actions import TimerAction, TimerActions, TimerPlan


class TimerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    operation: Literal["create", "list", "remaining", "cancel", "stop"]
    seconds: int | None = Field(default=None, ge=1, le=604800)
    number: int | None = Field(default=None, ge=1)


def timer_tool():
    return {"type": "function", "function": {
        "name": "controler_minuteurs",
        "description": "Interpréter les demandes naturelles de minuteur. create : durée explicite en secondes (1 à 604800), name seulement si un nom est demandé. remaining : temps restant. list : tous les minuteurs. cancel : annuler un minuteur. Pour remaining ou cancel, renseigner name si l'utilisateur nomme le minuteur, number uniquement si l'utilisateur donne explicitement un numéro pour cancel. Par défaut remaining et cancel visent le courant (sonnerie active puis plus récent du même étage). stop : arrêter la sonnerie. Une à quatre actions explicites. Une hypothèse n'est pas un ordre.",
        "parameters": TimerPlan.model_json_schema(),
    }}


class DeviceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    operation: Literal["turn_on", "turn_off", "read", "temperature", "options", "set", "increment", "decrement",
                       "select_next", "select_previous", "press", "device_pause", "device_resume", "device_stop",
                       "device_start", "return_to_base", "locate", "volume_set", "volume_up", "volume_down",
                       "mute", "unmute", "select_source", "set_fan_speed", "clean_area", "sources", "read_volume", "read_source"]
    target: str = Field(min_length=1, max_length=160)
    value: str | None = Field(default=None, max_length=500)


class TemperatureRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    target: str = Field(default="ici", min_length=1, max_length=160)


def tool(name, description, model):
    return {"type": "function", "function": {"name": name, "description": description,
            "parameters": model.model_json_schema()}}


TIMER_TOOL = tool("gerer_minuteur", "Demande naturelle de minuteur : create avec durée explicite en secondes, remaining pour le temps restant du courant, list pour tous, cancel sans numéro pour le courant ou par numéro explicite, stop pour la sonnerie. Ne pas inventer de durée ou transformer une hypothèse en ordre.", TimerRequest)
DEVICE_TOOL = tool("controler_appareil", "Une commande explicite sur un appareil/helper existant, températures, lecteurs et aspirateur. Pas de chauffage, d'application TV ni de service arbitraire. Utiliser l'outil de lumière pour une lampe.", DeviceRequest)
TEMPERATURE_TOOL = tool("lire_temperature", "Lire la température actuelle d'une pièce ou d'un capteur exposé. target contient la pièce, le nom du capteur ou « ici » pour la pièce du terminal. Utiliser pour toute question sur la température d'une pièce, jamais pour la température de couleur d'une lumière.", TemperatureRequest)


def execute_timer(timers, args, turn):
    command = TimerRequest.model_validate(args)
    if turn.floor not in {"rdc", "etage1"}:
        raise HomeError("Choisissez l'étage de ce terminal avant de commander un minuteur.")
    if command.operation == "create":
        if command.seconds is None or command.number is not None:
            raise HomeError("Précisez la durée du minuteur.")
        text = f"mets un minuteur de {command.seconds} secondes"
    elif command.operation == "cancel":
        if command.seconds is not None:
            raise HomeError("Quel minuteur voulez-vous annuler ?")
        text = "annule le minuteur" + (f" {command.number}" if command.number is not None else "")
    else:
        if command.seconds is not None or command.number is not None:
            raise HomeError("Cette demande ne prend ni durée ni numéro.")
        text = "liste les minuteurs" if command.operation == "list" else "stop"
        if command.operation == "remaining":
            text = "quel temps reste-t-il sur le minuteur"
    if turn.cancelled.is_set():
        return {"status": "cancelled", "reply": "Demande interrompue.", "actions": []}
    value = timers.handle(text, turn.floor, terminal_id=turn.key[0])
    return {"status": "clarification" if value["action"] == "clarify" else "confirmed", "reply": value["text"],
            "actions": [{"family": "timer", "intent": command.model_dump(), "number": value.get("item", {}).get("number")} ]}


def execute_timer_plan(timers, args, turn):
    plan = TimerPlan.model_validate(args)
    return TimerActions(timers).run(plan.actions, turn)


def execute_device(home, args, turn):
    command = DeviceRequest.model_validate(args)
    if turn.cancelled.is_set():
        return {"status": "cancelled", "reply": "Demande interrompue.", "actions": []}
    value, _ = HomeCommands(home).handle_command((command.operation, normalize(command.target), command.value))
    if value is None:
        raise HomeError("Précisez un appareil connu ou utilisez la commande de lumière pour une lampe.")
    if value.get("error"):
        raise HomeError(value["error"])
    if value.get("status") == "confirmation":
        return {"status": "confirmation", "reply": value["reply"],
                "actions": [{"family": "device", "intent": command.model_dump()}],
                "confirmation": True}
    reply = value["reply"]
    return {"status": "unconfirmed" if "non confirmé" in reply or "envoyé" in reply else "confirmed",
            "reply": reply, "actions": [{"family": "device", "intent": command.model_dump()}]}


def execute_temperature(home, args, turn):
    command = TemperatureRequest.model_validate(args)
    if turn.cancelled.is_set():
        return {"status": "cancelled", "reply": "Demande interrompue.", "actions": []}
    value, _ = HomeCommands(home).handle_command(("temperature", normalize(command.target), None))
    if value is None:
        raise HomeError("Précisez une pièce ou un capteur de température.")
    if value.get("error"):
        if value.get("clarification"):
            return {"status": "clarification", "reply": value["error"], "actions": []}
        raise HomeError(value["error"])
    return {"status": "confirmed", "reply": value["reply"],
            "actions": [{"family": "temperature", "intent": command.model_dump()}]}
