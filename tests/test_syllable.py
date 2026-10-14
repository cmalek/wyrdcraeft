from wyrdcraeft.services.syllable import OESyllableBreaker


def test_syllable_breaker_public_api() -> None:
    breaker = OESyllableBreaker()

    assert breaker.is_vowel("ē")
    assert not breaker.is_vowel("b")
    assert breaker.find_vowel_nuclei("bēodan") == [(1, 3, "ēo"), (4, 5, "a")]
    assert breaker.split_consonants("") == ("", "")
    assert breaker.split_consonants("ngst") == ("ngst", "")
    assert breaker.split_consonants("xst") == ("x", "st")
    assert breaker.split_consonants("n") == ("", "n")
    assert breaker.split_consonants("xyz") == ("xy", "z")
    assert breaker.force_suffix_boundaries("cyning") == "cyn.ing"
    assert breaker.force_suffix_boundaries("word") == "word"

    split = [(part.onset, part.nucleus, part.coda) for part in breaker.split("cyning")]
    assert split == [("c", "y", ""), ("", "i", "ng")]
    blocked = [
        (part.onset, part.nucleus, part.coda) for part in breaker.split("singan")
    ]
    assert blocked == [("s", "i", "ng"), ("", "a", "")]
    assert breaker.split("þþþ") == []
    carried = [
        (part.onset, part.nucleus, part.coda) for part in breaker.split("hlāford")
    ]
    assert carried == [("hl", "ā", ""), ("", "o", "r")]
