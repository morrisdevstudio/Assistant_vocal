"""Liste familiale : Home Assistant reste l'unique source des articles."""
import json
import re
import threading

import httpx

from alfred.home_assistant import WAKE_PREFIX, HomeError, normalize
from alfred.credentials import ConfigurationError


def item_key(value):
    """Comparer les graphies courantes sans confondre les quantités ou variantes."""
    value = normalize(value).strip(" .,!?:;")
    return re.sub(r"^(?:(?:du|de la|des|un|une|le|la|les)\s+|(?:de l'|l')\s*)", "", value).strip()


def extract_records(response, entity):
    try:
        items = response["service_response"][entity]["items"]
        if not isinstance(items, list) or any(not isinstance(x, dict) or not isinstance(x.get("summary"), str) for x in items):
            raise ValueError()
        return items
    except (KeyError, TypeError, ValueError) as error:
        raise HomeError("Réponse de la liste de courses illisible.") from error


def extract_items(response, entity):
    return [x["summary"] for x in extract_records(response, entity)]


class Shopping:
    def __init__(self, home, directory):
        self.home = home
        self.path = directory / "shopping.json"
        self.lock = threading.Lock()

    def entity(self):
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))["entity_id"]
        except FileNotFoundError:
            return None
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise HomeError("Configuration de la liste de courses illisible.") from error
        if not isinstance(value, str) or not re.fullmatch(r"todo\.[a-z0-9_]+", value):
            raise HomeError("Configuration de la liste de courses invalide.")
        return value

    def configure(self, entity):
        if not re.fullmatch(r"todo\.[a-z0-9_]+", entity):
            raise ValueError("Identifiant de liste invalide.")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"entity_id": entity}), encoding="utf-8")

    def request(self, action, item=None, new_name=None, cancelled=None):
        if action in ("add_item", "complete_item", "rename_item", "restore_item", "delete_item") and (not isinstance(item, str) or not item_key(item)):
            raise HomeError("Précisez un article de la liste.")
        if action == "rename_item" and (not isinstance(new_name, str) or not item_key(new_name) or len(new_name.strip()) > 120 or any(ord(ch) < 32 for ch in new_name)):
            raise HomeError("Précisez un nouveau nom d'article valide.")
        if action not in ("add_item", "get_items", "get_completed", "get_all", "complete_item", "rename_item", "restore_item", "delete_item", "purge_items"):
            raise HomeError("Opération de courses inconnue.")
        entity = self.entity()
        if not entity:
            raise HomeError("Configurez d'abord la liste de courses familiale dans Alfred.")
        if not self.lock.acquire(blocking=False):
            raise HomeError("Une opération sur la liste est déjà en cours.")
        try:
            base, token = self.home._endpoint()
            try:
                with self.home.client_factory() as client:
                    state = self.home._request(client, token, "GET", base + "/states/" + entity)
                    if not isinstance(state, dict) or state.get("entity_id") != entity or state.get("state") in ("unavailable", "unknown"):
                        raise HomeError("La liste de courses est indisponible dans Home Assistant.")
                    payload = {"entity_id": entity}
                    if action == "purge_items":
                        existing = self.home._request(client, token, "POST", base + "/services/todo/get_items?return_response",
                                                      {"entity_id": entity, "status": ["needs_action", "completed"]})
                        records = extract_records(existing, entity)
                        uids = [entry.get("uid") for entry in records]
                        if any(not isinstance(uid, str) or not uid for uid in uids) or len(set(uids)) != len(uids):
                            raise HomeError("Identifiants invalides : aucune suppression effectuée.")
                        removed = 0
                        for uid in uids:
                            if cancelled is not None and cancelled.is_set():
                                return {"removed": removed, "incomplete": True}
                            try:
                                self.home._request(client, token, "POST", base + "/services/todo/remove_item",
                                                   {"entity_id": entity, "item": uid})
                            except (HomeError, httpx.HTTPError):
                                return {"removed": removed, "incomplete": True}
                            removed += 1
                        try:
                            remaining = self.home._request(client, token, "POST", base + "/services/todo/get_items?return_response",
                                                           {"entity_id": entity, "status": ["needs_action", "completed"]})
                            count = len(extract_records(remaining, entity))
                        except (HomeError, httpx.HTTPError):
                            return {"removed": removed, "incomplete": True}
                        return {"removed": removed, "remaining": count, "incomplete": False}
                    if action in ("complete_item", "rename_item", "restore_item", "delete_item"):
                        status = "completed" if action == "restore_item" else ["needs_action", "completed"] if action == "delete_item" else "needs_action"
                        existing = self.home._request(client, token, "POST", base + "/services/todo/get_items?return_response",
                                                      {"entity_id": entity, "status": status})
                        records = extract_records(existing, entity)
                        matches = [entry for entry in records if item_key(entry["summary"]) == item_key(item)]
                        if not matches:
                            raise HomeError(f"{item} est introuvable dans la liste demandée.")
                        if len(matches) != 1:
                            raise HomeError(f"Plusieurs articles correspondent à {item}. Précisez dans Home Assistant.")
                        uid = matches[0].get("uid")
                        if not isinstance(uid, str) or not uid:
                            raise HomeError("Identifiant de l'article indisponible ; aucune modification effectuée.")
                        if action == "delete_item":
                            self.home._request(client, token, "POST", base + "/services/todo/remove_item",
                                               {"entity_id": entity, "item": uid})
                            return {"deleted": matches[0]["summary"]}
                        if action == "restore_item":
                            active = self.home._request(client, token, "POST", base + "/services/todo/get_items?return_response",
                                                        {"entity_id": entity, "status": "needs_action"})
                            if any(item_key(entry) == item_key(matches[0]["summary"]) for entry in extract_items(active, entity)):
                                raise HomeError("Cet article est déjà dans la liste des courses à faire.")
                            self.home._request(client, token, "POST", base + "/services/todo/update_item",
                                               {"entity_id": entity, "item": uid, "status": "needs_action"})
                            return {"restored": matches[0]["summary"]}
                        if action == "rename_item":
                            if any(entry is not matches[0] and item_key(entry["summary"]) == item_key(new_name) for entry in records):
                                raise HomeError("Un autre article porte déjà ce nom ; aucune modification effectuée.")
                            self.home._request(client, token, "POST", base + "/services/todo/update_item",
                                               {"entity_id": entity, "item": uid, "rename": new_name.strip()})
                            return {"old_name": matches[0]["summary"], "new_name": new_name.strip()}
                        self.home._request(client, token, "POST", base + "/services/todo/update_item",
                                           {"entity_id": entity, "item": uid, "status": "completed"})
                        return {"completed": matches[0]["summary"]}
                    if action == "add_item":
                        existing = self.home._request(client, token, "POST", base + "/services/todo/get_items?return_response",
                                                      {"entity_id": entity, "status": "needs_action"})
                        if any(item_key(entry) == item_key(item) for entry in extract_items(existing, entity)):
                            return {"duplicate": True}
                        completed = self.home._request(client, token, "POST", base + "/services/todo/get_items?return_response",
                                                       {"entity_id": entity, "status": "completed"})
                        matches = [entry for entry in extract_records(completed, entity) if item_key(entry["summary"]) == item_key(item)]
                        if len(matches) > 1:
                            raise HomeError("Plusieurs articles cochés correspondent ; précisez dans Home Assistant.")
                        if matches:
                            uid = matches[0].get("uid")
                            if not isinstance(uid, str) or not uid:
                                raise HomeError("Identifiant de l'article indisponible ; aucune modification effectuée.")
                            self.home._request(client, token, "POST", base + "/services/todo/update_item",
                                               {"entity_id": entity, "item": uid, "status": "needs_action"})
                            return {"duplicate": False, "restored": True}
                        payload["item"] = item
                    elif action == "get_all":
                        payload["status"] = ["needs_action", "completed"]
                    else:
                        payload["status"] = "completed" if action == "get_completed" else "needs_action"
                    service = "get_items" if action in ("get_completed", "get_all") else action
                    suffix = "?return_response" if service == "get_items" else ""
                    response = self.home._request(client, token, "POST", base + "/services/todo/" + service + suffix, payload)
            except httpx.HTTPError as error:
                if action in ("add_item", "complete_item", "rename_item", "restore_item", "delete_item"):
                    raise HomeError("Modification non confirmée : vérifiez la liste avant de réessayer.") from error
                raise HomeError("Connexion à Home Assistant impossible.") from error
            if action == "add_item":
                return {"duplicate": False}
            if action == "get_all":
                items = extract_records(response, entity)
                if any(not isinstance(item.get("uid"), str) or not item["uid"] or
                       item.get("status") not in ("needs_action", "completed") for item in items):
                    raise HomeError("État de la liste de courses illisible.")
                return [{"id": item["uid"], "name": item["summary"], "checked": item["status"] == "completed"} for item in items]
            return extract_items(response, entity)
        finally:
            self.lock.release()

    def handle(self, text):
        cleaned = text.strip().strip(" .?!")
        cleaned = WAKE_PREFIX.sub("", cleaned)
        norm = normalize(cleaned)
        listing = re.fullmatch(
            r"(?:qu['’]y a-t-il (?:sur|dans)|qu['’]est-ce qu['’]il y a (?:sur|dans)|"
            r"(?:il y a quoi|y a quoi|qu['’]est-ce qu['’]il y a) (?:sur|dans)|"
            r"lis|lire|affiche|montre|quelle est|donne-moi)\s+"
            r"(?:la|ma|notre)\s+liste(?:\s+de\s+courses)?", norm)
        if not listing and not re.search(r"\b(?:courses|course)\b", norm):
            return None
        add = re.fullmatch(r"(?:ajoute|ajouter|mets|mettre)\s+(.+?)\s+(?:à|a|sur|dans)\s+(?:la|ma|notre)\s+liste\s+de\s+courses(?:\s+s'il te plaît)?", cleaned, re.I)
        complete = re.fullmatch(r"(?:coche|retire|enlève|enleve)\s+(.+?)\s+(?:de|dans|sur)\s+(?:la|ma|notre)\s+liste\s+de\s+courses", cleaned, re.I)
        if not add and not complete and not listing:
            return "Pour les courses, demandez par exemple d'ajouter un article ou de lire la liste."
        if add:
            item = add.group(1).strip()
            if len(item) > 120 or re.search(r"\b(?:et|puis)\b|[,;]", normalize(item)):
                return "Précisez un seul article à ajouter à la liste de courses."
        try:
            if complete:
                result = self.request("complete_item", complete.group(1).strip())
                return f"{result['completed']} est coché dans la liste de courses."
            if add:
                result = self.request("add_item", item)
                if result["duplicate"]:
                    return f"{item} est déjà dans la liste de courses."
                if result.get("restored"):
                    return f"{item} est de nouveau dans la liste de courses."
                return f"{item} : ajout demandé à la liste de courses."
            items = self.request("get_items")
            if not items:
                return "La liste de courses est vide."
            return "Liste de courses : " + ", ".join(items[:20]) + (f". Et {len(items)-20} autre(s) article(s)." if len(items) > 20 else ".")
        except (HomeError, ConfigurationError) as error:
            return str(error)
