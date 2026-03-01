from __future__ import annotations

import pytest

from wyrdcraeft.services.morphology.text_utils import OENormalizer

pytestmark = pytest.mark.morphology


@pytest.mark.parametrize(
    ("input_text", "expected"),
    [
        ("ð", "þ"),
        ("Ð", "Þ"),
        ("king", "cing"),
        ("KING", "cING"),
        ("þ", "þ"),
        ("Þ", "Þ"),
        ("", ""),
        (None, ""),
    ],
)
def test_eth2thorn_reference(input_text: str | None, expected: str) -> None:
    assert OENormalizer.eth2thorn(input_text) == expected  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("input_text", "expected"),
    [
        ("ǽ", "æ"),
        ("á", "a"),
        ("é", "e"),
        ("í", "i"),
        ("ý", "y"),
        ("ó", "o"),
        ("ú", "u"),
        ("stán", "stan"),
        ("bacan", "bacan"),
        ("", ""),
        (None, ""),
    ],
)
def test_remove_diacritics_reference(input_text: str | None, expected: str) -> None:
    assert OENormalizer.remove_diacritics(input_text) == expected  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("input_text", "expected"),
    [
        ("eó", "éo"),
        ("eá", "éa"),
        ("ié", "íe"),
        ("éo", "éo"),
        ("éa", "éa"),
        ("íe", "íe"),
        ("bacan", "bacan"),
        ("", ""),
        (None, ""),
    ],
)
def test_move_accents_reference(input_text: str | None, expected: str) -> None:
    assert OENormalizer.move_accents(input_text) == expected  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("vowels", "expected"),
    [
        (["e", "e"], ["i", "e"]),
        (["o", "o"], ["e", "o"]),
        (["u", "u"], ["y", "u"]),
        (["æ", "æ"], ["e", "æ"]),
        (["a", "a"], ["æ", "a", "e"]),
        (["á", "á"], ["ǽ", "á"]),
        (["ó", "ó"], ["é", "ó"]),
        (["ú", "ú"], ["ý", "ú"]),
        (["ea", "ea"], ["ea", "ie", "i"]),
        (["eo", "eo"], ["ie", "eo"]),
        (["io", "io"], ["ie", "io", "i"]),
        (["éa", "éa"], ["íe", "éa", "í"]),
        (["éo", "éo"], ["íe", "éo"]),
        (["ío", "ío"], ["íe", "ío", "í"]),
    ],
)
def test_iumlaut_reference(vowels: list[str], expected: list[str]) -> None:
    assert OENormalizer.iumlaut(vowels) == expected


@pytest.mark.parametrize(
    ("stem", "expected"),
    [
        ("stán", 1),
        ("bacan", 0),
        ("bringan", 1),
        ("word", 1),
        ("hof", 1),
        ("helpan", 1),
        ("sc", 0),
        ("cg", 0),
        ("", 0),
    ],
)
def test_stem_length_reference(stem: str, expected: int) -> None:
    assert OENormalizer.stem_length(stem) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("stán", 1),
        ("bacan", 2),
        ("æ", 1),
        ("a", 1),
        ("", 0),
        (None, 0),
        ("abban dún", 3),
    ],
)
def test_syllable_count_reference(text: str | None, expected: int) -> None:
    assert OENormalizer.syllable_count(text) == expected  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("y", "i"),
        ("ie", "i"),
        ("ý", "i"),
        ("íe", "i"),
        ("yfele", "ifele"),
        ("micle", "micle"),
        ("stán", "stan"),
        ("", ""),
        (None, ""),
    ],
)
def test_normalize_output_reference(text: str | None, expected: str) -> None:
    assert OENormalizer.normalize_output(text) == expected  # type: ignore[arg-type]
