"""Reconnaissance expérimentale : calibration locale et essais indépendants obligatoires."""
import hashlib
import json
import math
import os
import tempfile
import threading

from alfred.profiles import cosine
from alfred.speaker import MODEL_REPOSITORY


class VoiceIdentity:
    def __init__(self, profiles, speaker, directory):
        self.profiles, self.speaker = profiles, speaker
        self.path = directory / "voice-identity-calibration.json"
        self.lock = threading.Lock()

    def _data(self):
        profiles=self.profiles.enrollment_vectors(MODEL_REPOSITORY)
        signature=hashlib.sha256(json.dumps([(p["id"],p["role"],[s["id"] for s in p["samples"]]) for p in profiles],separators=(",",":")).encode()).hexdigest()
        return profiles,signature

    def _load(self):
        try:
            data=json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data,dict) or data.get("version")!=1: return None
            return data
        except (OSError, ValueError, TypeError):
            return None

    def _save(self,data):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        fd,name=tempfile.mkstemp(prefix="voice-cal-",suffix=".tmp",dir=self.path.parent)
        try:
            with os.fdopen(fd,"w",encoding="utf-8") as stream:
                if os.name!="nt": os.fchmod(stream.fileno(),0o600)
                json.dump(data,stream,ensure_ascii=False)
                stream.flush();os.fsync(stream.fileno())
            os.replace(name,self.path)
        finally:
            if os.path.exists(name): os.unlink(name)

    @staticmethod
    def _references(profiles):
        result={}
        for profile in profiles:
            samples=profile["samples"]
            if len(samples)<6: raise ValueError("Chaque profil doit avoir six échantillons d'enrôlement.")
            vectors=[s["vector"] for s in samples[:-2]]
            size=len(vectors[0]) if vectors else 0
            if not size or any(len(v)!=size or any(not math.isfinite(x) for x in v) for v in vectors):
                raise ValueError("Empreintes vocales invalides.")
            result[profile["id"]]=[sum(v[i] for v in vectors)/len(vectors) for i in range(size)]
            if not any(result[profile["id"]]): raise ValueError("Empreinte vocale inutilisable.")
        return result

    def calibrate(self):
        with self.lock:
            profiles,signature=self._data()
            if len(profiles)<2: raise ValueError("Il faut au moins deux personnes enrôlées pour comparer leurs voix.")
            refs=self._references(profiles)
            positive=[]; negatives=[]; gaps=[]
            for profile in profiles:
                for sample in profile["samples"][-2:]:
                    vector=sample["vector"]
                    if any(len(vector)!=len(ref) for ref in refs.values()) or any(not math.isfinite(x) for x in vector) or not any(vector): raise ValueError("Empreintes de test invalides.")
                    scores={key:cosine(vector,ref) for key,ref in refs.items()}
                    own=scores[profile["id"]]
                    impostor=max(score for key,score in scores.items() if key!=profile["id"])
                    positive.append(own); negatives.append(impostor); gaps.append(own-impostor)
            if min(positive)-max(negatives)<0.03 or min(gaps)<0.03:
                raise ValueError("Les voix ne sont pas assez séparées pour une calibration fiable ; refaire les échantillons au calme.")
            data={"version":1,"signature":signature,"threshold":(min(positive)+max(negatives))/2,
                  "margin":min(gaps)/2,"probes":{p["id"]:0 for p in profiles},"validated":False}
            self._save(data)
            return {"state":"tests_required","profiles":len(profiles),"tests_per_profile":2}

    def status(self):
        profiles,signature=self._data(); data=self._load()
        if not data or data.get("signature")!=signature:
            return {"state":"not_calibrated", "profiles":len(profiles),
                    "complete_profiles":sum(len(p["samples"])>=6 for p in profiles)}
        return {"state":"ready" if data.get("validated") else "tests_required", "profiles":len(profiles),
                "probes":data.get("probes",{}), "tests_per_profile":2}

    def classify(self, vector, *, require_validated=True):
        profiles,signature=self._data();data=self._load()
        if not data or data.get("signature")!=signature or (require_validated and not data.get("validated")):
            return None
        refs=self._references(profiles)
        if any(len(vector)!=len(ref) for ref in refs.values()): return None
        scores=sorted(((cosine(vector,ref),identifier) for identifier,ref in refs.items()),reverse=True)
        if len(scores)<2 or scores[0][0]<data["threshold"] or scores[0][0]-scores[1][0]<data["margin"]:
            return None
        return scores[0][1]

    def probe(self, profile_id, wav):
        self._check_audio(wav)
        with self.lock:
            profiles,signature=self._data();data=self._load()
            if not data or data.get("signature")!=signature: raise ValueError("Calibrez de nouveau après toute modification des profils.")
            if profile_id not in data.get("probes",{}): raise ValueError("Profil non inclus dans la calibration.")
            vector=self.speaker.embed_wav(wav)
            found=self.classify(vector,require_validated=False)
            if found!=profile_id:
                data["validated"]=False; data["probes"][profile_id]=0;self._save(data)
                return {"match":False,"validated":False,"message":"Voix non reconnue avec assez de confiance. Réessayez ou refaites l'enrôlement."}
            data["probes"][profile_id]=min(2,data["probes"][profile_id]+1)
            data["validated"]=all(value>=2 for value in data["probes"].values())
            self._save(data)
            return {"match":True,"validated":data["validated"],"remaining":2-data["probes"][profile_id]}

    def identify_wav(self,wav):
        if self.status()["state"]!="ready": return None
        try: self._check_audio(wav)
        except ValueError: return None
        return self.classify(self.speaker.embed_wav(wav))

    @staticmethod
    def _check_audio(wav):
        from alfred.voice import pcm_16khz, validate_wav
        import numpy as np
        if validate_wav(wav)<2: raise ValueError("Parlez pendant au moins deux secondes pour ce test.")
        signal=np.asarray(pcm_16khz(wav),dtype="float32")
        if signal.size==0 or not np.isfinite(signal).all() or float(np.sqrt(np.mean(signal*signal)))<0.005:
            raise ValueError("La voix est trop faible pour être identifiée.")
