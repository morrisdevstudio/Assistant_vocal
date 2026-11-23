"""Mesure isolée Chatterbox v2 ; ne modifie ni service ni modèle sur disque."""
import argparse
from contextlib import nullcontext
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SHORT = "Il est vingt heures quarante-trois."
LONG = ("Il est vingt heures quarante-trois. Les enfants ont deux amis. "
        "Nous avons un rendez-vous. Du pain et un œuf. "
        "Il n'y a plus de pâtes. J'en veux plus, ajoute une portion.")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    p.add_argument("--precision", choices=("fp32", "amp16", "int8"), default="fp32")
    p.add_argument("--threads", type=int, default=4)
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--skip-long", action="store_true")
    p.add_argument("--validation", action="store_true")
    p.add_argument("--model-dir", type=Path, help="Dossier local des poids v2 ; sinon cache HF local")
    p.add_argument("--reference", type=Path, default=ROOT / ".local/data/voice-bank/alfred-reference-20261102/sample-short.wav")
    p.add_argument("--output-dir", type=Path, default=ROOT / ".local/chatterbox-benchmark")
    args = p.parse_args()
    if args.threads < 1 or args.repeats < 1:
        p.error("threads et repeats doivent être positifs")
    OUT = args.output_dir.resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    if not args.reference.is_file():
        p.error("Référence audio locale absente")
    if args.precision == "amp16" and args.device != "cuda":
        p.error("amp16 nécessite un GPU compatible")
    if args.precision == "int8" and args.device != "cpu":
        p.error("int8 est un essai CPU uniquement")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["TQDM_DISABLE"] = "1"
    import numpy as np
    import soundfile as sf
    import torch
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    from huggingface_hub import snapshot_download
    torch.set_num_threads(args.threads)
    torch.set_num_interop_threads(2)
    if args.device == "cuda" and not torch.cuda.is_available():
        p.error("Accélération GPU indisponible ; choisir cpu ou préparer le GPU")
    label = f"{args.device}-{args.precision}-t{args.threads}"
    if args.validation:
        label += "-validation"
    def sync():
        if args.device == "cuda":
            torch.cuda.synchronize()
    load_start = time.perf_counter()
    folder = str(args.model_dir.resolve()) if args.model_dir else snapshot_download("ResembleAI/chatterbox", local_files_only=True,
        allow_patterns=["ve.pt", "t3_mtl23ls_v2.safetensors", "s3gen.pt",
                        "grapheme_mtl_merged_expanded_v1.json", "conds.pt", "Cangjie5_TC.json"])
    model = ChatterboxMultilingualTTS.from_local(folder, device=args.device)
    if args.precision == "int8":
        assert args.device == "cpu"
        # Réduire seulement les couches linéaires du transformeur, garder les
        # embeddings, le conditionnement et la sortie audio en pleine précision.
        model.t3.tfmr = torch.ao.quantization.quantize_dynamic(
            model.t3.tfmr, {torch.nn.Linear}, dtype=torch.qint8, inplace=False)
    reference = args.reference.resolve()
    model.prepare_conditionals(str(reference), exaggeration=.5)
    sync()
    metadata = {"label": label, "torch": torch.__version__, "python": sys.version,
                "device": args.device, "precision": args.precision, "threads": args.threads,
                "model_revision_or_folder": Path(folder).name,
                "platform": sys.platform, "visible_cpu_count": os.cpu_count(),
                "load_seconds": round(time.perf_counter() - load_start, 3),
                "gpu": torch.cuda.get_device_name(0) if args.device == "cuda" else None,
                "records": []}
    print(json.dumps({k:v for k,v in metadata.items() if k!='records'}), flush=True)
    stages = {}
    for stage, obj, method in (("tokens", model.t3, "inference"),
                                ("vocoder", model.s3gen, "inference"),
                                ("watermark", model.watermarker, "apply_watermark")):
        original = getattr(obj, method)
        def wrapped(*a, _fn=original, _stage=stage, **kw):
            sync()
            t = time.perf_counter()
            value = _fn(*a, **kw)
            sync()
            stages[_stage] = round(time.perf_counter() - t, 4)
            return value
        setattr(obj, method, wrapped)
    texts = [("cold-short", SHORT)] + [(f"warm-short-{i+1}", SHORT) for i in range(args.repeats)]
    if not args.skip_long:
        texts.append(("long", LONG))
    if args.validation:
        texts = [("heure-seed7", SHORT), ("heure-seed123", SHORT),
                 ("negation", "Non, il n'y a plus de pâtes."),
                 ("liaisons", "Les enfants ont deux amis. Du pain et un œuf.")]
    for case, text in texts:
        seed = 123 if case == "heure-seed123" else 7 if args.validation else 42
        torch.manual_seed(seed)
        if args.device == "cuda":
            torch.cuda.manual_seed_all(seed)
        stages.clear()
        sync()
        started = time.perf_counter()
        context = torch.autocast("cuda", dtype=torch.float16) if args.precision == "amp16" else nullcontext()
        with context:
            wav = model.generate(text, language_id="fr", exaggeration=.5, cfg_weight=.5)
        sync()
        elapsed = time.perf_counter() - started
        samples = wav.detach().cpu().float().numpy().squeeze()
        if samples.ndim != 1 or not len(samples) or not np.isfinite(samples).all():
            raise RuntimeError("Audio invalide")
        peak = np.max(np.abs(samples))
        if peak > .8:
            samples *= .8 / peak
        name = f"{label}-{case}.wav"
        sf.write(OUT / name, samples, model.sr, subtype="PCM_16")
        row = {"case": case, "text": text, "file": name,
               "seed": seed,
               "generation_seconds": round(elapsed, 4), "stages_seconds": dict(stages),
               "audio_seconds": round(len(samples)/model.sr, 4),
               "gpu_peak_allocated_mb": round(torch.cuda.max_memory_allocated()/1024**2, 1)
                  if args.device == "cuda" else None}
        metadata["records"].append(row)
        (OUT/f"{label}.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(row, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
