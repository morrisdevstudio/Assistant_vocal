"""Validation isolée d'un ONNX openWakeWord ; aucune donnée externe autorisée."""
import math
import os
import sys
from pathlib import Path


def fields(data):
    def integer(at):
        value = shift = 0
        while at < len(data) and shift < 70:
            byte = data[at]
            at += 1
            value |= (byte & 127) << shift
            if byte < 128:
                return value, at
            shift += 7
        raise ValueError("Protobuf invalide")
    at = 0
    while at < len(data):
        tag, at = integer(at)
        number, wire = tag >> 3, tag & 7
        if not number:
            raise ValueError("Champ invalide")
        if wire == 0:
            value, at = integer(at)
        elif wire == 2:
            count, at = integer(at)
            if count > len(data) - at:
                raise ValueError("Champ tronqué")
            value, at = data[at:at+count], at+count
        elif wire in (1, 5):
            count = 8 if wire == 1 else 4
            if count > len(data) - at:
                raise ValueError("Champ tronqué")
            value, at = data[at:at+count], at+count
        else:
            raise ValueError("Encodage inconnu")
        yield number, wire, value


def embedded(data, kind="model", depth=0):
    # Champs du schéma officiel : https://github.com/onnx/onnx/blob/main/onnx/onnx.proto
    if depth > 24:
        raise ValueError("Graphe trop profond")
    children = {"model": {7: "graph", 25: "function"},
                "graph": {1: "node", 5: "tensor", 15: "sparse"},
                "function": {7: "node", 11: "attribute"},
                "node": {5: "attribute"},
                "attribute": {5: "tensor", 6: "graph", 10: "tensor", 11: "graph",
                              22: "sparse", 23: "sparse"},
                "sparse": {1: "tensor", 2: "tensor"}}
    for number, wire, value in fields(data):
        if kind == "tensor" and (number == 13 or (number == 14 and value != 0)):
            raise ValueError("Données ONNX externes interdites")
        child = children.get(kind, {}).get(number)
        if child:
            if wire != 2:
                raise ValueError("Graphe invalide")
            embedded(value, child, depth+1)


def limit_memory():
    if sys.platform == "win32":
        # Limite privée du processus ; le handle doit vivre jusqu'à la sortie.
        import ctypes
        from ctypes import wintypes
        class Basic(ctypes.Structure):
            _fields_ = [("times", ctypes.c_int64 * 2), ("flags", wintypes.DWORD),
                        ("min", ctypes.c_size_t), ("max", ctypes.c_size_t),
                        ("active", wintypes.DWORD), ("affinity", ctypes.c_size_t),
                        ("priority", wintypes.DWORD), ("scheduling", wintypes.DWORD)]
        class Extended(ctypes.Structure):
            _fields_ = [("basic", Basic), ("io", ctypes.c_uint64 * 6),
                        ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                        ("peak_process", ctypes.c_size_t), ("peak_job", ctypes.c_size_t)]
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.CreateJobObjectW.restype = wintypes.HANDLE
        kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        job = kernel.CreateJobObjectW(None, None)
        limits = Extended()
        limits.basic.flags = 0x100  # JOB_OBJECT_LIMIT_PROCESS_MEMORY
        limits.process_memory = 1024 * 1024 * 1024
        if not job or not kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            raise ValueError("Limite mémoire indisponible")
        if not kernel.AssignProcessToJobObject(job, kernel.GetCurrentProcess()):
            raise ValueError("Isolation mémoire indisponible")
    else:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (4 * 1024**3, 4 * 1024**3))


def validate(model, folder):
    embedded(Path(model).read_bytes())
    from alfred.wake_word import WakeWordDetector, verify_preprocess
    import numpy as np
    verify_preprocess(folder)
    detector = WakeWordDetector(model, folder)
    if len(detector.model.models) != 1:
        raise ValueError("Un seul détecteur est requis")
    detector.feed(np.zeros(16000 * 3, dtype="<i2").tobytes())
    if not math.isfinite(detector.score) or not 0 <= detector.score <= 1:
        raise ValueError("Sortie de modèle incompatible")


if __name__ == "__main__":
    try:
        for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
            os.environ[variable] = "1"
        limit_memory()
        validate(sys.argv[1], sys.argv[2])
    except Exception:
        sys.exit(1)
