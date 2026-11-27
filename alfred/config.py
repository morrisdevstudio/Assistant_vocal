"""Configuration locale, sans lecture implicite de secrets."""

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    poll_seconds: float = 0.5
    models_dir: Path | None = None
    command_code_api_key: str = field(default="", repr=False)
    command_code_model: str | None = None
    ha_url: str = field(default="", repr=False)
    ha_token: str = field(default="", repr=False)
    ha_room: str | None = None
    listen_host: str = "127.0.0.1"
    # Dossier de la PWA compilée ; None laisse Alfred chercher pwa/ puis ui/dist.
    pwa_dir: Path | None = None
    # Réservé aux tests de migration ; les rappels utilisateur relèvent désormais de HA.
    legacy_reminders: bool = False

    @classmethod
    def from_env(cls):
        default = Path(__file__).resolve().parents[1] / ".local" / "data"
        models = Path(__file__).resolve().parents[1] / ".local" / "models"
        return cls(data_dir=Path(os.environ.get("ALFRED_DATA_DIR", default)).resolve(),
                   models_dir=Path(os.environ.get("ALFRED_MODELS_DIR", models)).resolve(),
                   command_code_api_key=os.environ.get("ALFRED_COMMAND_CODE_API_KEY", ""),
                   command_code_model=os.environ.get("ALFRED_COMMAND_CODE_MODEL") or None,
                   ha_url=os.environ.get("ALFRED_HA_URL", ""),
                   ha_token=os.environ.get("ALFRED_HA_TOKEN", ""),
                   ha_room=os.environ.get("ALFRED_HA_ROOM") or None,
                   pwa_dir=Path(os.environ["ALFRED_PWA_DIR"]).resolve()
                   if os.environ.get("ALFRED_PWA_DIR") else None)
