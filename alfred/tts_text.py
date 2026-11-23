"""Préparation française pour la lecture, sans modifier le texte affiché.

Les homographes ambigus ne sont pas corrigés sans contexte négatif explicite.
La voix, son débit et les paramètres du moteur restent ceux de l'utilisateur.
"""
import re


_SMALL = (
    "zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit",
    "neuf", "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize",
    "dix-sept", "dix-huit", "dix-neuf",
)
_TENS = {20: "vingt", 30: "trente", 40: "quarante", 50: "cinquante", 60: "soixante"}
# Bornes complètes : ne pas transformer un fragment d'heure invalide ou de durée
# avec secondes, ni une heure contenue dans une URL ou un identifiant.
_TIME = re.compile(
    r"(?<![\w/:])(?P<hour>\d{1,2})"
    r"(?:\s*[hH](?:\s*(?P<hminute>\d{1,2}))?|\s*:\s*(?P<cminute>\d{2}))"
    r"(?![\w:]|\s*\d)"
)
_NEGATIVE_STOCK = re.compile(
    r"\bil n[’']y (?P<en>en )?a plus"
    r"(?P<tail> de\b(?!\s+\d)| d[’']|(?=[\s]*[.!?;,\n]|\s*$))",
    re.I,
)
_INFORMAL_NO = re.compile(
    r"\bnon[,\s]+il y (?:en )?a plus(?=\s*[.!?;\n]|\s*$)", re.I
)


def _number(value, feminine=False):
    if value < 20:
        return "une" if value == 1 and feminine else _SMALL[value]
    if value < 70:
        tens, unit = divmod(value, 10)
        base = _TENS[tens * 10]
        if unit == 1:
            return base + (" et une" if feminine else " et un")
        return base + ("-" + _SMALL[unit] if unit else "")
    if value < 80:
        return "soixante" + (" et onze" if value == 71 else "-" + _number(value - 60))
    if value < 100:
        return "quatre-vingts" if value == 80 else "quatre-vingt-" + _number(value - 80, feminine)
    if value < 1000:
        hundreds, rest = divmod(value, 100)
        base = ("cent" if hundreds == 1 else _number(hundreds) + " cent")
        return base + ("s" if hundreds > 1 and not rest else "") + (" " + _number(rest, feminine) if rest else "")
    for scale, singular, plural in ((10**12, "billion", "billions"), (10**9, "milliard", "milliards"), (10**6, "million", "millions"), (1000, "mille", "mille")):
        if value >= scale:
            amount, rest = divmod(value, scale)
            if amount >= 1000 and scale == 10**12:
                return " ".join(_SMALL[int(digit)] for digit in str(value))
            prefix = "" if scale == 1000 and amount == 1 else _number(amount) + " "
            # « quatre-vingts mille » et « deux cents mille » perdent leur s.
            if scale == 1000:
                prefix = re.sub(r"(vingt|cent)s $", r"\1 ", prefix)
            return prefix + (singular if amount == 1 else plural) + (" " + _number(rest, feminine) if rest else "")


_DIGITS = re.compile(r"\d+(?:[,.]\d+)?")
_FEMININE = re.compile(r"^\s+(?:lumières?|lampes?|minutes?|secondes?|heures?|personnes?|fois|pièces?|années?|semaines?)\b", re.I)
_ORDINAL = re.compile(r"(?<!\w)(\d+)(?:er|re|ème|eme|e)(?!\w)", re.I)


def numbers_to_words(text):
    """Écrit les nombres en français ; les zéros initiaux restent audibles."""
    def ordinal(match):
        value = int(match.group(1))
        if value == 1:
            return "première" if match.group().lower().endswith("re") else "premier"
        word = _number(value)
        if word.endswith("cinq"): word += "u"
        elif word.endswith("neuf"): word = word[:-1] + "v"
        elif word.endswith("e"): word = word[:-1]
        return word + "ième"
    text = _ORDINAL.sub(ordinal, text)
    def convert(match):
        raw = match.group()
        parts = re.split(r"([,.])", raw, maxsplit=1)
        whole = parts[0]
        before = text[match.start() - 1:match.start()]
        after = text[match.end():match.end() + 1]
        if before.isalpha() or after.isalpha() or (len(whole) > 1 and whole.startswith("0")):
            result = " ".join(_SMALL[int(c)] for c in whole)
        else:
            result = _number(int(whole), feminine=bool(_FEMININE.match(text[match.end():])))
        if len(parts) > 1:
            fraction = parts[2]
            result += " virgule " + (" ".join(_SMALL[int(c)] for c in fraction) if fraction.startswith("0") else _number(int(fraction)))
        if before.isalpha(): result = " " + result
        if after.isalpha(): result += " "
        return result
    return _DIGITS.sub(convert, text)


def _time(match):
    hour = int(match["hour"])
    minute = int(match["hminute"] or match["cminute"] or 0)
    if hour > 23 or minute > 59:
        return match[0]
    result = _number(hour, feminine=True) + (" heure" if hour in (0, 1) else " heures")
    return result + (" " + _number(minute, feminine=True) if minute else "")


def _negative_stock(match):
    tail = match["tail"]
    # « Il n'y en a plus de disponibles » ne suit pas la même construction.
    if match["en"] and tail:
        return match[0]
    result = "il ne reste pas" + tail if tail else "il n'en reste pas"
    return result[0].upper() + result[1:] if match[0][0].isupper() else result


def prepare_tts_text(text, reformulate_absence=True):
    """Heures explicites et négations d'absence ; aucun remplacement global de plus."""
    text = _TIME.sub(_time, text)
    if not reformulate_absence:
        return numbers_to_words(text)
    text = _NEGATIVE_STOCK.sub(_negative_stock, text)
    text = _INFORMAL_NO.sub(
        lambda m: ("Non" if m[0][0].isupper() else "non") + ", il n'en reste pas", text
    )
    return numbers_to_words(text)
