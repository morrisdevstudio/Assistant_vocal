"""Catalogue Assist et sélection locale des entités domotiques."""
import json
import threading
import time
from urllib.parse import urlsplit, urlunsplit

from websockets.sync.client import connect
from websockets.uri import parse_uri

from alfred.home_assistant import normalize
from alfred.home_settings import HomeSettings, effective_light_types
from alfred.light_trace import measure


DOMAINS = {"climate", "cover", "fan", "humidifier", "light", "media_player", "scene", "switch", "todo", "vacuum", "water_heater"}
BINARY_CLASSES = {"door", "garage_door", "lock", "motion", "opening", "presence", "window"}
SENSOR_CLASSES = {"aqi", "carbon_monoxide", "carbon_dioxide", "humidity", "pm10", "pm25", "temperature", "volatile_organic_compounds"}

# Home Assistant Core 2026.11, MediaPlayerEntityFeature / VacuumEntityFeature.
DEVICE_FEATURES = {
    "media_player": {"media_pause": 1, "volume_set": 4, "volume_mute": 8,
                     "media_previous_track": 16, "media_next_track": 32,
                     "turn_on": 128, "turn_off": 256, "volume_up": 1024,
                     "volume_down": 1024, "select_source": 2048,
                     "media_stop": 4096, "media_play": 16384},
    "vacuum": {"pause": 4, "stop": 8, "return_to_base": 16,
               "set_fan_speed": 32, "locate": 512, "start": 8192, "clean_area": 16384},
}


def capabilities(domain, attrs):
    if domain in DEVICE_FEATURES:
        features = attrs.get("supported_features", 0)
        if not isinstance(features, int) or isinstance(features, bool) or features < 0:
            features = 0
        actions = [name for name, bit in DEVICE_FEATURES[domain].items() if features & bit]
        return ["read", *actions]
    if domain == "light":
        from alfred.light_actions import light_capabilities
        return light_capabilities(attrs)
    if domain in {"switch", "input_boolean"}:
        return ["read", "turn_on", "turn_off"]
    if domain == "sensor" and attrs.get("device_class") == "temperature":
        return ["read"]
    return {"input_number": ["read", "set_value", "increment", "decrement"],
            "input_select": ["read", "options", "select_option", "select_next", "select_previous"],
            "input_datetime": ["read", "set_datetime"],
            "input_text": ["set_value"] if attrs.get("mode") == "password" else ["read", "set_value"],
            "input_button": ["press"]}.get(domain, [])


class CatalogError(RuntimeError):
    pass


class HomeCatalog:
    def __init__(self, home, websocket_factory=connect):
        self.home = home
        self.settings = HomeSettings(home.store.path.parent)
        self.websocket_factory = websocket_factory
        self._lock = threading.Lock()
        self._snapshot_context = threading.local()
        self._stats = {"snapshots": 0, "failures": 0, "last_ms": None,
                       "last_snapshot_at": None}

    def stats(self):
        with self._lock:
            return dict(self._stats)

    def control_snapshot(self):
        """Membres privés utilisables seulement à travers un groupe exposé."""
        catalog = self.snapshot()
        return {**catalog, "light_group_members": getattr(self._snapshot_context, "light_group_members", {})}

    def snapshot(self):
        started = time.monotonic()
        try:
            with measure("catalog_read"):
                value = self._snapshot()
        except Exception:
            with self._lock:
                self._stats["failures"] += 1
            raise
        with self._lock:
            self._stats.update(snapshots=self._stats["snapshots"] + 1,
                               last_ms=round((time.monotonic() - started) * 1000, 1),
                               last_snapshot_at=time.time())
        return value

    def _snapshot(self):
        base, token = self.home._endpoint()
        parsed = urlsplit(base)
        uri = urlunsplit(("wss" if parsed.scheme == "https" else "ws", parsed.netloc, parsed.path.rstrip("/") + "/websocket", "", ""))
        commands = [("homeassistant/expose_entity/list", {}), ("homeassistant/expose_new_entities/get", {"assistant": "conversation"}),
                    ("config/entity_registry/list", {}), ("config/area_registry/list", {}),
                    ("config/device_registry/list", {}), ("config/floor_registry/list", {}), ("get_states", {})]
        try:
            with self.websocket_factory(uri, open_timeout=5, close_timeout=2, proxy=None, max_size=32 * 1024 * 1024) as ws:
                if ws.protocol.uri != parse_uri(uri):
                    raise CatalogError("Redirection Home Assistant refusée.")
                if json.loads(ws.recv(timeout=10)).get("type") != "auth_required":
                    raise CatalogError("Authentification Home Assistant inattendue.")
                ws.send(json.dumps({"type": "auth", "access_token": token}))
                if json.loads(ws.recv(timeout=10)).get("type") != "auth_ok":
                    raise CatalogError("Jeton Home Assistant refusé.")
                results = []
                for number, (command, args) in enumerate(commands, 1):
                    ws.send(json.dumps({"id": number, "type": command, **args}))
                    response = json.loads(ws.recv(timeout=20))
                    if response.get("id") != number or response.get("success") is not True:
                        raise CatalogError("Lecture du catalogue Assist refusée ou indisponible.")
                    results.append(response["result"])
                registry_ids = {entry["entity_id"] for entry in results[2]}
                ids = [state["entity_id"] for state in results[6] if state.get("entity_id") in registry_ids]
                ws.send(json.dumps({"id": 8, "type": "config/entity_registry/get_entries", "entity_ids": ids}))
                response = json.loads(ws.recv(timeout=20))
                if response.get("id") != 8 or response.get("success") is not True or not isinstance(response.get("result"), dict):
                    raise CatalogError("Lecture des alias Home Assistant indisponible.")
                details = response["result"]
            exposure, defaults, registry, areas, devices, floors, states = results
            exposed = exposure["exposed_entities"]
            expose_new = defaults["expose_new"]
            if not isinstance(exposed, dict) or not isinstance(expose_new, bool) or any(not isinstance(x, list) for x in (registry, areas, devices, floors, states)):
                raise ValueError("format")
            saved = self.settings.load()
            exclusions, confirmations = set(saved["excluded"]), set(saved["confirmations"])
            aliases, names, rooms = saved["aliases"], saved["names"], saved["rooms"]
            light_types = saved["light_types"]
            regs = {x["entity_id"]: x for x in registry}
            area_map = {x["area_id"]: x for x in areas}
            device_map = {x["id"]: x for x in devices}
            floor_map = {x["floor_id"]: x for x in floors}
            areas_by_name = {normalize(area["name"]): area for area in areas}

            def location(entity, reg, device):
                ha_area = area_map.get(reg.get("area_id") or device.get("area_id"), {})
                alfred_area = rooms.get(entity, "")
                area = areas_by_name.get(normalize(alfred_area), {}) if alfred_area else ha_area
                floor = floor_map.get(area.get("floor_id"), {})
                return {"area": alfred_area or ha_area.get("name"), "floor": floor.get("name"),
                        "ha_area": ha_area.get("name"), "alfred_area": alfred_area}

            items = []
            for state in states:
                entity = state["entity_id"]
                domain = entity.split(".", 1)[0]
                reg = regs.get(entity, {})
                device = device_map.get(reg.get("device_id"), {})
                options = reg.get("options") or {}
                explicit = (options.get("conversation") or {}).get("should_expose")
                if explicit is None and exposed.get(entity, {}).get("conversation") is True:
                    explicit = True
                elif explicit is None and not reg and entity in exposed:
                    explicit = False
                attrs = state.get("attributes") or {}
                default = bool(reg) and expose_new and not reg.get("entity_category") and not reg.get("hidden_by") and (domain in DOMAINS or (domain == "binary_sensor" and attrs.get("device_class") in BINARY_CLASSES) or (domain == "sensor" and attrs.get("device_class") in SENSOR_CLASSES))
                if explicit is not True and not (explicit is None and default):
                    continue
                vacuum_mapping = ((details.get(entity, {}).get("options") or options).get("vacuum") or {}).get("area_mapping") or {}
                ha_name = attrs.get("friendly_name") or entity
                alfred_name = names.get(entity, "")
                items.append({"entity_id": entity, "name": alfred_name or ha_name,
                              "ha_name": ha_name, "alfred_name": alfred_name,
                              "device": device.get("name_by_user") or device.get("name"),
                              **location(entity, reg, device), "domain": domain,
                              "allowed": entity not in exclusions, "supported": bool(capabilities(domain, attrs)),
                              "confirmation_required": entity in confirmations,
                              **({"light_type": light_types.get(entity)} if domain == "light" else {}),
                              "capabilities": capabilities(domain, attrs),
                              "attributes": {key: attrs[key] for key in ("device_class", "unit_of_measurement", "min", "max", "step", "options", "has_date", "has_time", "mode", "supported_features", "source_list", "fan_speed_list", "group_members", "supported_color_modes", "brightness", "rgb_color", "color_temp_kelvin", "min_color_temp_kelvin", "max_color_temp_kelvin") if key in attrs},
                              "cleaning_areas": [{"id": key, "name": area_map[key]["name"]} for key, segments in vacuum_mapping.items() if domain == "vacuum" and isinstance(segments, list) and segments and key in area_map],
                              "state": None if domain == "input_text" and attrs.get("mode") == "password" else state.get("state"), "members": attrs.get("entity_id"),
                              "aliases": aliases.get(entity, []),
                              "ha_aliases": [x for x in (details.get(entity, {}).get("aliases") or []) if isinstance(x, str) and x.strip()]})
            # Ces informations ne sont ni des cibles autonomes, ni ajoutées au
            # catalogue public. Un groupe exposé autorise son sous-arbre, sauf
            # exclusions explicites, y compris lorsque ses membres sont masqués.
            visible = {x["entity_id"] for x in items}
            lights = {x["entity_id"]: x for x in states if str(x.get("entity_id", "")).startswith("light.")}
            pending = [m for x in items if x.get("domain") == "light" and isinstance(x.get("members"), list) for m in x["members"] if isinstance(m, str)]
            visited, private = set(), {}
            while pending:
                entity = pending.pop()
                if entity in visited or entity not in lights:
                    continue
                visited.add(entity)
                members = (lights[entity].get("attributes") or {}).get("entity_id")
                if entity not in visible:
                    attrs = lights[entity].get("attributes") or {}
                    reg = regs.get(entity, {})
                    private[entity] = {"entity_id": entity,
                                       "name": names.get(entity) or attrs.get("friendly_name") or entity,
                                       **location(entity, reg, device_map.get(reg.get("device_id"), {})),
                                       "allowed": entity not in exclusions,
                                       "light_type": light_types.get(entity),
                                       "members": members,
                                       "confirmation_required": entity in confirmations}
                if isinstance(members, list):
                    pending.extend(m for m in members if isinstance(m, str))
            classified = {**private, **{item["entity_id"]: item for item in items if item["domain"] == "light"}}
            for entity, light_type in effective_light_types(classified, classified).items():
                classified[entity]["light_type"] = light_type
            self._snapshot_context.light_group_members = private
            ha_rooms = {area["name"] for area in areas}
            ha_room_floors = {}
            for area in areas:
                floor = floor_map.get(area.get("floor_id"))
                if floor:
                    ha_room_floors[area["name"]] = {"name": floor["name"], "level": floor.get("level")}
            return {"entities": items, "ha_rooms": sorted(ha_rooms),
                    "ha_room_floors": ha_room_floors,
                    "rooms": sorted(ha_rooms | {item["area"] for item in items if item["area"]}),
                    "excluded": sorted(exclusions), "aliases": aliases,
                    "confirmations": sorted(confirmations), "synchronized": True}
        except CatalogError:
            raise
        except Exception as error:
            raise CatalogError("Impossible de déterminer les entités exposées à Assist.") from error
