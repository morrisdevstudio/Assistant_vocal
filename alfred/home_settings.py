"""Réglages domotiques enregistrés ensemble dans une seule transaction."""

import json
import threading

from alfred.home_aliases import HomeAliases, HomeLabels, write_names
from alfred.home_confirmations import HomeConfirmations
from alfred.home_exclusions import HomeExclusions


def effective_light_types(targets, descendants):
    """Trouver le type le plus proche pour chaque lumière ou groupe."""
    parents = {}
    for entity, item in descendants.items():
        members = item.get("members")
        if isinstance(members, list):
            for member in members:
                if isinstance(member, str):
                    parents.setdefault(member, set()).add(entity)

    result = {}
    for target in targets:
        visited, layer = set(), {target}
        while layer:
            types = {descendants[entity].get("light_type") for entity in layer} & HomeSettings.light_types
            if types:
                result[target] = "secondary" if "secondary" in types else "main"
                break
            visited.update(layer)
            layer = {parent for entity in layer for parent in parents.get(entity, ())} - visited
        else:
            result[target] = "main"
    return result


class HomeSettings:
    light_types = {"main", "secondary"}

    def __init__(self, directory):
        self.path = directory / "home-device-settings.json"
        self._lock = threading.Lock()
        self._legacy = {
            "aliases": HomeAliases(directory),
            "names": HomeLabels(directory, "home-names.json"),
            "rooms": HomeLabels(directory, "home-rooms.json"),
            "excluded": HomeExclusions(directory),
            "confirmations": HomeConfirmations(directory),
        }

    def load(self):
        try:
            with self.path.open(encoding="utf-8") as source:
                data = json.load(source)
        except FileNotFoundError:
            return {**{key: store.load() for key, store in self._legacy.items()}, "light_types": {}}
        except (OSError, ValueError) as error:
            raise ValueError("Impossible de lire les réglages domotiques.") from error
        if not isinstance(data, dict) or set(data) - {"light_types"} != self._legacy.keys():
            raise ValueError("Format des réglages domotiques invalide.")
        return self._validate(data)

    def _validate(self, data):
        light_types = data.get("light_types", {})
        if not isinstance(light_types, dict) or any(
            not entity.startswith("light.") or not isinstance(value, str)
            or value not in self.light_types | {"automatic", "ambient"}
            for entity, value in light_types.items()
        ):
            raise ValueError("Type d’éclairage invalide.")
        return {
            "aliases": self._legacy["aliases"].validate(data["aliases"]),
            "names": HomeLabels.validate_labels(data["names"]),
            "rooms": HomeLabels.validate_labels(data["rooms"]),
            "excluded": HomeExclusions.validate(data["excluded"]),
            "confirmations": HomeConfirmations.validate(data["confirmations"]),
            "light_types": {entity: "secondary" if value == "ambient" else value
                            for entity, value in light_types.items() if value != "automatic"},
        }

    def replace(self, key, value):
        with self._lock:
            data = self._validate({**self.load(), key: value})
            write_names(self.path, data)
            return data[key]

    def update(self, entity, changes, available_rooms, *, local_room=None):
        if local_room is not None and (not local_room.strip() or local_room != changes.get("alfred_area")):
            raise ValueError("La pièce locale doit correspondre à l’affectation demandée.")
        with self._lock:
            data = self.load()
            for field, value in changes.items():
                if field == "aliases":
                    data["aliases"][entity] = value
                elif field == "light_type":
                    if not entity.startswith("light.") or not isinstance(value, str) or value not in self.light_types:
                        raise ValueError("Choisissez Principal ou Secondaire pour une lumière.")
                    data["light_types"][entity] = value
                elif field in {"alfred_name", "alfred_area"}:
                    key = "names" if field == "alfred_name" else "rooms"
                    value = HomeLabels.validate_name(value)
                    if field == "alfred_area" and value and value != local_room and value != data[key].get(entity):
                        if value not in available_rooms():
                            raise ValueError("Choisissez une pièce du registre Home Assistant.")
                    if value:
                        data[key][entity] = value
                    else:
                        data[key].pop(entity, None)
                else:
                    if not isinstance(value, bool):
                        raise ValueError("Une valeur activée ou désactivée est attendue.")
                    excluded = field == "allowed"
                    key = "excluded" if excluded else "confirmations"
                    members = set(data[key])
                    if value != excluded:
                        members.add(entity)
                    else:
                        members.discard(entity)
                    data[key] = list(members)
            data = self._validate(data)
            write_names(self.path, data)
            return {
                "alfred_name": data["names"].get(entity, ""),
                "alfred_area": data["rooms"].get(entity, ""),
                "aliases": data["aliases"].get(entity, []),
                "allowed": entity not in data["excluded"],
                "confirmation_required": entity in data["confirmations"],
                **({"light_type": data["light_types"][entity]} if entity in data["light_types"] else {}),
            }
