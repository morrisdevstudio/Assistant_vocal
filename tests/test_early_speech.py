from alfred.early_speech import take_complete_sentence


def test_complete_sentences_are_emitted_incrementally_without_losing_text():
    pending = "Bonjour monsieur. Voici la"
    sentence, pending = take_complete_sentence(pending)
    assert sentence == "Bonjour monsieur."
    pending += " réponse demandée pour la maison."
    sentence, pending = take_complete_sentence(pending, final=True)
    assert sentence == "Voici la réponse demandée pour la maison."
    assert pending == ""


def test_short_stabilization_does_not_split_decimal_or_wait_forever():
    sentence, pending = take_complete_sentence("La valeur est 3.5")
    assert sentence is None
    assert pending == "La valeur est 3.5"
    sentence, pending = take_complete_sentence(pending, final=True)
    assert sentence == "La valeur est 3.5" and not pending


def test_incomplete_text_is_kept_until_more_deltas_arrive():
    assert take_complete_sentence("Bonjour, voici") == (None, "Bonjour, voici")
