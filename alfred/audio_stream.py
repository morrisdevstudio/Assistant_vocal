"""Flux FLAC continu en mémoire, alimenté par les blocs de synthèse successifs."""
import asyncio
from fractions import Fraction
import io
import re
import time
import wave


def trim_block_edges(wav, *, first=False, last=False):
    """Retirer seulement l'excédent de silence aux jonctions des blocs PCM16.

    Analyse RMS à -60 dBFS par trames de 10 ms. Garder au moins 80 ms avant
    l'activité et 180 ms après, sans toucher à la première attaque ni à la fin
    de l'énoncé. Les échantillons conservés restent strictement identiques.
    """
    import numpy as np
    with wave.open(io.BytesIO(wav), "rb") as source:
        if source.getnchannels() != 1 or source.getsampwidth() != 2:
            raise ValueError("Bloc audio invalide")
        params = source.getparams()
        rate = source.getframerate()
        raw = source.readframes(source.getnframes())
    samples = np.frombuffer(raw, dtype="<i2")
    frame = max(1, round(rate * .01))
    count = len(samples) // frame
    if not count:
        return wav, 0
    frames = samples[:count * frame].astype("float64").reshape(-1, frame)
    rms = np.sqrt(np.mean(frames * frames, axis=1))
    active = np.flatnonzero(rms >= 32.768)
    if not len(active):
        return wav, 0
    # Une trame partiellement voisée peut tomber sous le seuil RMS : élargir
    # d'une trame avant de conserver les marges, notamment pour les consonnes.
    start = 0 if first else max(0, (int(active[0]) - 1) * frame - round(rate * .08))
    end = len(samples) if last else min(len(samples), (int(active[-1]) + 2) * frame + round(rate * .18))
    # S'arrêter sur un niveau presque nul, en élargissant les marges de garde.
    if start:
        low = max(0, start - frame)
        start = low + int(np.argmin(np.abs(samples[low:start + 1].astype("int32"))))
    if end < len(samples):
        high = min(len(samples), end + frame)
        end += int(np.argmin(np.abs(samples[end:high].astype("int32"))))
    if start == 0 and end == len(samples):
        return wav, 0
    output = io.BytesIO()
    with wave.open(output, "wb") as destination:
        destination.setparams(params)
        destination.writeframes(samples[start:end].tobytes())
    removed_ms = round((start + len(samples) - end) / rate * 1000)
    return output.getvalue(), removed_ms


def speech_blocks(text, target=180):
    """Couper sur la ponctuation sans ajouter de silence ni modifier les mots."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    blocks, pending = [], ""
    for sentence in sentences:
        clauses = re.split(r"(?<=[,;:])\s+", sentence) if len(sentence) > target else [sentence]
        pieces = []
        for clause in clauses:
            while len(clause) > target:
                cut = clause.rfind(" ", 0, target)
                if cut < 1:
                    break
                pieces.append(clause[:cut])
                clause = clause[cut:].lstrip()
            pieces.append(clause)
        for clause in pieces:
            if len(pending) >= 40 and len(pending) + len(clause) > target:
                blocks.append(pending)
                pending = ""
            pending = (pending + " " + clause).strip()
            if len(pending) >= 40 and pending[-1:] in ".!?":
                blocks.append(pending)
                pending = ""
    if pending:
        blocks.append(pending)
    return blocks


class StreamingFlac:
    """Un seul en-tête/encodeur FLAC pour toute la réponse, jamais des FLAC collés."""
    def __init__(self):
        self.loop = asyncio.get_running_loop()
        self.changed = asyncio.Event()
        self.ready = asyncio.Event()
        self.data = bytearray()
        self.done = False
        self.error = None
        self.container = self.encoder = self.resampler = None
        self.samples = 0
        self.blocks = 0

    def write(self, data):
        if len(self.data) + len(data) > 6 * 1024 * 1024:
            raise ValueError("Flux audio trop grand")
        self.data.extend(data)
        self.loop.call_soon_threadsafe(self.changed.set)
        return len(data)

    def tell(self):
        return len(self.data)

    def _encode(self, frames):
        for frame in frames:
            frame.pts = self.samples
            frame.time_base = Fraction(1, 48000)
            self.samples += frame.samples
            for packet in self.encoder.encode(frame):
                self.container.mux(packet)

    def feed(self, wav):
        import av
        import numpy as np
        if self.container is None:
            self.container = av.open(self, mode="w", format="flac")
            self.encoder = self.container.add_stream("flac", rate=48000)
            self.encoder.layout = "mono"
            self.resampler = av.AudioResampler(format="s16", layout="mono", rate=48000)
        with wave.open(io.BytesIO(wav), "rb") as source:
            if source.getnchannels() != 1 or source.getsampwidth() != 2:
                raise ValueError("Bloc audio invalide")
            rate = source.getframerate()
            pcm = np.frombuffer(source.readframes(source.getnframes()), dtype="<i2").copy()
        frame = av.AudioFrame.from_ndarray(pcm.reshape(1, -1), format="s16", layout="mono")
        frame.sample_rate = rate
        self._encode(self.resampler.resample(frame))
        self.blocks += 1
        if self.data:
            self.loop.call_soon_threadsafe(self.ready.set)

    def finish(self):
        if self.container:
            self._encode(self.resampler.resample(None))
            for packet in self.encoder.encode(None):
                self.container.mux(packet)
            self.container.close()
        self.done = True
        self.loop.call_soon_threadsafe(self.changed.set)
        self.loop.call_soon_threadsafe(self.ready.set)

    def fail(self, error):
        self.error = type(error).__name__
        self.done = True
        self.changed.set()
        self.ready.set()

    async def chunks(self):
        offset = 0
        deadline = time.monotonic() + 90
        while True:
            self.changed.clear()
            if offset < len(self.data):
                block = bytes(self.data[offset:offset + 16384])
                offset += len(block)
                yield block
            elif self.error:
                raise RuntimeError("Génération audio interrompue")
            elif self.done:
                return
            elif time.monotonic() >= deadline:
                raise TimeoutError("Flux audio expiré")
            else:
                await asyncio.wait_for(self.changed.wait(), 30)
