"""Chargement explicite de Phonon français, dans le processus CPU isolé."""
from pathlib import Path


class PhononVoice:
    def __init__(self, config):
        import ptts
        ptts.set_num_threads(4)
        root = Path(config["model_dir"])
        self.model = ptts.TTS(str(root), lang="fr", device="cpu", quant="q8",
                              temperature=.3, seed=42, voice_catalog=str(root / "voices.jsonl"))
        if "fr" not in self.model.languages:
            raise ValueError("Le checkpoint Phonon ne prend pas en charge le français")
        self.voice = config["voice_name"]
        self.model.add_voice(self.voice, config["voice_file"])
        self.sample_rate = self.model.sample_rate

    def synthesize(self, text):
        return self.model.synth(text, voice=self.voice, seed=42), self.sample_rate



def load_engine(config):
    if config["engine"] != "phonon":
        raise ValueError("Seul le moteur Phonon est disponible")
    return PhononVoice(config)
