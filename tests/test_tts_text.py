import pytest

from alfred.tts_text import prepare_tts_text
from alfred.voice import VoiceService


@pytest.mark.parametrize("source,expected", [
    ("Il est 20h43.", "Il est vingt heures quarante-trois."),
    ("Il est 20 h 43.", "Il est vingt heures quarante-trois."),
    ("Il est 20:43.", "Il est vingt heures quarante-trois."),
    ("À 01h01.", "À une heure une."),
    ("À 21H31.", "À vingt et une heures trente et une."),
    ("À 00h00.", "À zéro heure."),
    ("À 12h00 puis 23h59.", "À douze heures puis vingt-trois heures cinquante-neuf."),
    ("À 20 h demain.", "À vingt heures demain."),
    ("À 20h, demain.", "À vingt heures, demain."),
    ("Il n'y a plus de pâtes.", "Il ne reste pas de pâtes."),
    ("Il n’y a plus d'eau.", "Il ne reste pas d'eau."),
    ("Non, il n'y en a plus.", "Non, il n'en reste pas."),
    ("Non il y a plus.", "Non, il n'en reste pas."),
    ("Non, il y en a plus !", "Non, il n'en reste pas !"),
    ("il n'y a plus", "il n'en reste pas"),
])
def test_spoken_french_is_explicit(source, expected):
    assert prepare_tts_text(source) == expected
    assert prepare_tts_text(expected) == expected


@pytest.mark.parametrize("text", [
    "Il y a plus de pâtes.", "J'en veux plus.", "Deux plus deux font quatre.",
    "C'est plus rapide.", "Il n'y a plus que deux pâtes.",
    "Il n'y en a plus de disponibles.",
    "Il y a plus.",
    "La voix et son débit restent identiques.",
])
def test_ambiguous_meanings_and_other_text_are_preserved(text):
    assert prepare_tts_text(text) == text


@pytest.mark.parametrize("source,expected", [
    ("1 lumière allumée.", "une lumière allumée."),
    ("2 lumières et 21 minutes.", "deux lumières et vingt et une minutes."),
    ("70, 71, 80, 81, 91", "soixante-dix, soixante et onze, quatre-vingts, quatre-vingt-un, quatre-vingt-onze"),
    ("200 et 201 ; 80000 et 200000.", "deux cents et deux cent un ; quatre-vingt mille et deux cent mille."),
    ("Prix : 12,05 euros.", "Prix : douze virgule zéro cinq euros."),
    ("Il n'y a plus de 10 personnes.", "Il n'y a plus de dix personnes."),
    ("Code 007 et modèle M3.", "Code zéro zéro sept et modèle M trois."),
])
def test_numbers_are_written_out(source, expected):
    assert prepare_tts_text(source) == expected


@pytest.mark.parametrize("voice", ["phonon-dumby-cpu", "phonon-alfred-cpu", "phonon-arnaud-cpu", "phonon-lucien-cpu"])
def test_phonon_receives_spoken_time_and_unchanged_negative_plus(tmp_path, monkeypatch, voice):
    engine=VoiceService(tmp_path,initial_voice=voice)
    received=[]
    monkeypatch.setattr(engine,"_check",lambda:None)
    monkeypatch.setattr(engine._local_voices[voice],"synthesize",lambda text:received.append(text) or b"wav")
    monkeypatch.setattr("alfred.voice.validate_wav",lambda data:.1)
    text="Il est 20h43. Il n'y a plus de pâtes."
    engine.speak(text)
    list(engine.speak_blocks([text]))
    assert received==["Il est vingt heures quarante-trois. Il n'y a plus de pâtes."]*2
