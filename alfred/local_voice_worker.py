"""Synthèse CPU locale par stdio ; aucune écoute réseau ni fichier audio."""
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
    protocol = sys.stdout
    sys.stdout = sys.stderr

    def send(value):
        protocol.write(json.dumps(value) + "\n")
        protocol.flush()

    try:
        import numpy as np
        from alfred.local_voice_models import load_engine
        engine = load_engine(config)
        send({"ready": True, "device": "cpu", "engine": config["engine"]})
        for line in sys.stdin.buffer:
            if len(line) > 10000:
                raise ValueError("Requête trop longue")
            text = json.loads(line).get("text")
            if not isinstance(text, str) or not 1 <= len(text) <= 1000:
                raise ValueError("Texte invalide")
            np.random.seed(42)
            samples, rate = engine.synthesize(text)
            samples = np.asarray(samples, dtype=np.float32).squeeze()
            if (samples.ndim != 1 or not 0 < len(samples) <= rate * 30
                    or not np.isfinite(samples).all()):
                raise ValueError("Audio invalide")
            peak = float(np.max(np.abs(samples)))
            if peak > .8:
                samples = samples * (.8 / peak)
            pcm = (np.clip(samples, -1., 1.) * 32767).astype("<i2").tobytes()
            output = io.BytesIO()
            with wave.open(output, "wb") as destination:
                destination.setnchannels(1)
                destination.setsampwidth(2)
                destination.setframerate(rate)
                destination.writeframes(pcm)
            send({"audio": base64.b64encode(output.getvalue()).decode("ascii")})
    except (BrokenPipeError, EOFError):
        return
    except Exception:
        send({"error": "LocalVoiceError"})


if __name__ == "__main__":
    main()
