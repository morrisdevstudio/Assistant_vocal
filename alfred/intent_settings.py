"""Réglages locaux du relais IA ; aucune route réseau de configuration ajoutée."""
import argparse
import json
import os
from pathlib import Path
import tempfile

DEFAULTS = {"lights": True, "music": True, "shopping": True, "announcements": True,
            "calendar": True, "timers": True, "devices": False}


def read(directory):
    path = Path(directory) / "intent-settings.json"
    if not path.exists():
        return dict(DEFAULTS)
    saved = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(saved, dict) or any(k not in DEFAULTS or not isinstance(v, bool) for k, v in saved.items()):
        raise ValueError("Réglages de compréhension invalides")
    return {**DEFAULTS, **saved}


def main():
    from alfred.config import Settings
    parser = argparse.ArgumentParser(description="Activer/désactiver un relais IA Alfred")
    parser.add_argument("--data-dir", type=Path, default=Settings.from_env().data_dir)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--enable", choices=DEFAULTS)
    mode.add_argument("--disable", choices=DEFAULTS)
    args = parser.parse_args()
    values = read(args.data_dir)
    family = args.enable or args.disable
    if family:
        values[family] = bool(args.enable)
        args.data_dir.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(dir=args.data_dir, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as output:
                json.dump(values, output, indent=2)
            os.replace(name, args.data_dir / "intent-settings.json")
        finally:
            if os.path.exists(name):
                os.unlink(name)
    print(json.dumps(values, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
