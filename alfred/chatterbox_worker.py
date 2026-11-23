"""Serveur stdio privé Chatterbox v2, CPU uniquement, sans audio sur disque."""
import argparse
import base64
import io
import json
import sys
import wave


def main():
    from alfred.runtime import prefer_interactive_cpu
    prefer_interactive_cpu()
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    from pathlib import Path
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    # Réserver stdout au protocole ; les impressions des bibliothèques ne doivent
    # jamais y intercaler leurs diagnostics ou un contenu de conversation.
    protocol = sys.stdout
    sys.stdout = sys.stderr

    def send(value):
        protocol.write(json.dumps(value) + "\n")
        protocol.flush()

    try:
        import numpy as np
        import torch
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        torch.set_num_threads(4)
        torch.set_num_interop_threads(2)
        model = ChatterboxMultilingualTTS.from_local(config["model_dir"], device="cpu")
        model.prepare_conditionals(config["reference"], exaggeration=.5)
        send({"ready": True, "device": "cpu"})
        for line in sys.stdin.buffer:
            if len(line) > 10000:
                raise ValueError("Requête trop longue")
            request = json.loads(line)
            text = request.get("text")
            if not isinstance(text, str) or not 1 <= len(text) <= 1000:
                raise ValueError("Texte invalide")
            torch.manual_seed(42)
            wav = model.generate(text, language_id="fr", exaggeration=.5, cfg_weight=.5)
            samples = wav.detach().cpu().float().numpy().squeeze()
            if (samples.ndim != 1 or not 0 < len(samples) <= model.sr * 30
                    or not np.isfinite(samples).all()):
                raise ValueError("Audio invalide")
            peak = float(np.max(np.abs(samples)))
            if peak > .8:
                samples = samples * (.8 / peak)
            pcm = (np.clip(samples, -1., 1.) * 32767).astype("<i2").tobytes()
            output = io.BytesIO()
            with wave.open(output, "wb") as stream:
                stream.setnchannels(1)
                stream.setsampwidth(2)
                stream.setframerate(model.sr)
                stream.writeframes(pcm)
            send({"audio": base64.b64encode(output.getvalue()).decode("ascii")})
    except (BrokenPipeError, EOFError):
        return
    except Exception:
        # Ne pas exposer le texte, l'audio ou des données de configuration.
        send({"error": "ChatterboxCPUError"})


if __name__ == "__main__":
    main()
