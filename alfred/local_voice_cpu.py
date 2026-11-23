"""Accès aux profils Phonon par protocole stdio borné."""
from pathlib import Path
from alfred.chatterbox_cpu import ChatterboxCPU

ASSETS = {"phonon": ("config.json", "tokenizer.json", "model.q8.gguf", "voices.jsonl")}


class LocalVoiceCPU(ChatterboxCPU):
    worker_module = "alfred.local_voice_worker"
    config_path_fields = ("python", "site_packages", "model_dir", "voice_file")

    def __init__(self, config_path, engine="phonon"):
        if engine != "phonon":
            raise ValueError("Seul le moteur Phonon est disponible")
        super().__init__(config_path)
        self.engine = engine

    def available(self):
        try:
            config = self.configuration()
            return (config.get("engine") == "phonon" and Path(config["python"]).is_file()
                    and Path(config["voice_file"]).is_file()
                    and (Path(config["site_packages"]) / "ptts/__init__.py").is_file()
                    and all((Path(config["model_dir"]) / name).is_file() for name in ASSETS["phonon"]))
        except (OSError, ValueError, TypeError, KeyError):
            return False
