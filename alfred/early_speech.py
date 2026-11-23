"""Découpage oral pendant que le texte IA arrive, sans anticiper les actions."""
import re

MIN_CHARS = 16
MAX_CHARS = 180
END = re.compile(r"[.!?…](?:[\s\"'»\]\n]|$)")
ABBREVIATIONS = {"m.", "mm.", "dr.", "st.", "etc.", "vs.", "no."}


def take_complete_sentence(buffer, final=False):
    """Retourne (phrase stabilisée, reste du texte) sans couper un nombre.

    Une phrase courte attend un peu de contexte, sauf à la fin définitive.
    Le texte lui-même est le seul état ; une annulation jette encore le reste.
    """
    if not buffer:
        return None, ""
    candidates = list(END.finditer(buffer))
    for marker in candidates:
        ending = marker.end()
        prefix = buffer[:ending].strip()
        if len(prefix) < MIN_CHARS and not final:
            continue
        lower = buffer[max(0, marker.start() - 5):marker.end()].lower()
        if any(lower.endswith(item) for item in ABBREVIATIONS):
            continue
        # Le découpage reste sur une frontière de phrase et garde la ponctuation.
        return prefix, buffer[ending:].lstrip()
    if len(buffer) > MAX_CHARS:
        boundaries = list(re.finditer(r"[;:]\s+|[.!?…]\s+", buffer))
        for marker in boundaries:
            if len(buffer[:marker.end()].strip()) >= MIN_CHARS:
                return buffer[:marker.end()].strip(), buffer[marker.end():].lstrip()
    if final and buffer.strip():
        return buffer.strip(), ""
    return None, buffer
