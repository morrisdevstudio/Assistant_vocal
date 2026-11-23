"""Voix Henri via l'accès Home Assistant Cloud existant, sans lecture sur HA."""
import io
from urllib.parse import urlsplit
import wave

import httpx

MAX_ENCODED_BYTES = 6 * 1024 * 1024
MAX_PCM_BYTES = 24000 * 2 * 60


class HomeCloudTTSError(RuntimeError):
    pass


def decode_audio(data):
    """Audio HA → WAV mono PCM16 24 kHz, uniquement en mémoire."""
    import av
    pcm = bytearray()
    with av.open(io.BytesIO(data)) as source:
        resampler = av.AudioResampler(format="s16", layout="mono", rate=24000)
        def append(frames):
            for frame in frames:
                block = frame.to_ndarray().astype("<i2", copy=False).tobytes()
                if len(pcm) + len(block) > MAX_PCM_BYTES:
                    raise HomeCloudTTSError("La réponse vocale est trop longue.")
                pcm.extend(block)
        for frame in source.decode(audio=0):
            append(resampler.resample(frame))
        append(resampler.resample(None))
    if not pcm:
        raise HomeCloudTTSError("Aucun audio reçu de Home Assistant Cloud.")
    output = io.BytesIO()
    with wave.open(output, "wb") as destination:
        destination.setnchannels(1)
        destination.setsampwidth(2)
        destination.setframerate(24000)
        destination.writeframes(pcm)
    return output.getvalue()


class HomeCloudTTS:
    def __init__(self, store, client_factory=None):
        self.store = store
        self.client_factory = client_factory or (lambda: httpx.Client(
            timeout=httpx.Timeout(15, connect=5), trust_env=False, follow_redirects=False))

    def available(self):
        try:
            return bool(self.store.public()["configured"])
        except Exception:
            return False

    def synthesize(self, text):
        try:
            base, token, _ = self.store.values()
            if not base or not token:
                raise HomeCloudTTSError("Home Assistant n'est pas configuré.")
            base = base.rstrip("/")
            headers = {"Authorization": "Bearer " + token}
            with self.client_factory() as client:
                response = client.post(base + "/api/tts_get_url", headers=headers, follow_redirects=False, json={
                    "engine_id": "tts.home_assistant_cloud", "message": text,
                    "language": "fr-FR", "options": {"voice": "HenriNeural"}, "cache": False,
                })
                if response.status_code != 200:
                    raise HomeCloudTTSError("La synthèse Home Assistant Cloud est indisponible.")
                path = response.json().get("path", "")
                if not isinstance(path, str):
                    raise HomeCloudTTSError("Adresse audio invalide.")
                parsed = urlsplit(path)
                # Ne jamais envoyer le jeton à une URL issue de la réponse ou
                # suivre une redirection. Télécharger le proxy sur le même HA.
                if (parsed.scheme or parsed.netloc or parsed.query or parsed.fragment
                        or not path.startswith("/api/tts_proxy/")
                        or ".." in path.split("/") or "\\" in path):
                    raise HomeCloudTTSError("Adresse audio refusée.")
                encoded = bytearray()
                with client.stream("GET", base + path, headers=headers, follow_redirects=False) as audio:
                    if audio.status_code != 200:
                        raise HomeCloudTTSError("Audio Home Assistant Cloud indisponible.")
                    for block in audio.iter_bytes():
                        if len(encoded) + len(block) > MAX_ENCODED_BYTES:
                            raise HomeCloudTTSError("Audio Home Assistant Cloud trop volumineux.")
                        encoded.extend(block)
            return decode_audio(bytes(encoded))
        except HomeCloudTTSError:
            raise
        except Exception as error:
            # Les exceptions HTTP peuvent inclure URL, texte ou détails privés.
            raise HomeCloudTTSError("Connexion ou audio Home Assistant Cloud indisponible.") from error
