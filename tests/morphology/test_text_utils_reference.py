from __future__ import annotations

import pytest

from wyrdcraeft.services.morphology.text_utils import (
    OENormalizer,
    canonicalize_inflection_code,
)

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
        ("ǣ", "æ"),
        ("ā", "a"),
        ("ē", "e"),
        ("ī", "i"),
        ("ȳ", "y"),
        ("ō", "o"),
        ("ū", "u"),
        ("stān", "stan"),
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
        ("eó", "ēo"),  # acute input -> macron output
        ("eá", "ēa"),
        ("ié", "īe"),
        ("ēo", "ēo"),  # already macron unchanged
        ("ēa", "ēa"),
        ("īe", "īe"),
        ("bacan", "bacan"),
        ("", ""),
        (None, ""),
    ],
)
def test_move_accents_reference(input_text: str | None, expected: str) -> None:
    assert OENormalizer.move_accents(input_text) == expected  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("input_text", "expected"),
    [
        ("eā", "ēa"),
        ("eō", "ēo"),
        ("eī", "ēi"),
        ("iē", "īe"),
        ("EĀ", "ĒA"),
        ("a-beātan", "a-bēatan"),
        ("a-beōdan", "a-bēodan"),
        ("eīg-land", "ēig-land"),
        ("ælf-sciēne", "ælf-scīene"),
        ("eá", "ēa"),
        ("eó", "ēo"),
        ("ié", "īe"),
        ("ēa", "ēa"),
        ("bēon", "bēon"),
        ("bacan", "bacan"),
        ("", ""),
    ],
)
def test_swap_bt_diphthong_long_marks_reference(input_text: str, expected: str) -> None:
    assert OENormalizer.swap_bt_diphthong_long_marks(input_text) == expected


@pytest.mark.parametrize(
    ("input_text", "expected"),
    [
        ("eā", "ēa"),
        ("eō", "ēo"),
        ("eī", "ēi"),
        ("iē", "īe"),
        ("a-beātan", "a-bēatan"),
        ("a-beōdan", "a-bēodan"),
        ("eīg-land", "ēig-land"),
        ("ælf-sciēne", "ælf-scīene"),
        ("eá", "ēa"),
        ("eó", "ēo"),
        ("ié", "īe"),
        ("ēa", "ēa"),
        ("bēon", "bēon"),
        ("bacan", "bacan"),
        ("", ""),
    ],
)
def test_normalize_bt_display_spelling_reference(input_text: str, expected: str) -> None:
    assert OENormalizer.normalize_bt_display_spelling(input_text) == expected


@pytest.mark.parametrize(
    "value",
    ["ēa", "ēo", "ēi", "īe", "a-bēodan", "ælf-scīene"],
)
def test_normalize_bt_display_spelling_is_idempotent(value: str) -> None:
    normalized = OENormalizer.normalize_bt_display_spelling(value)
    assert OENormalizer.normalize_bt_display_spelling(normalized) == normalized


@pytest.mark.parametrize(
    ("vowels", "expected"),
    [
        (["e", "e"], ["i", "e"]),
        (["o", "o"], ["e", "o"]),
        (["u", "u"], ["y", "u"]),
        (["æ", "æ"], ["e", "æ"]),
        (["a", "a"], ["æ", "a", "e"]),
        (["ā", "ā"], ["ǣ", "ā"]),
        (["ō", "ō"], ["ē", "ō"]),
        (["ū", "ū"], ["ȳ", "ū"]),
        (["ea", "ea"], ["ea", "ie", "i"]),
        (["eo", "eo"], ["ie", "eo"]),
        (["io", "io"], ["ie", "io", "i"]),
        (["ēa", "ēa"], ["īe", "ēa", "ī"]),
        (["ēo", "ēo"], ["īe", "ēo"]),
        (["īo", "īo"], ["īe", "īo", "ī"]),
    ],
)
def test_iumlaut_reference(vowels: list[str], expected: list[str]) -> None:
    assert OENormalizer.iumlaut(vowels) == expected


@pytest.mark.parametrize(
    ("stem", "expected"),
    [
        ("stān", 1),
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
        ("stān", 1),
        ("bacan", 2),
        ("æ", 1),
        ("a", 1),
        ("", 0),
        (None, 0),
        ("abban dūn", 3),
    ],
)
def test_syllable_count_reference(text: str | None, expected: int) -> None:
    assert OENormalizer.syllable_count(text) == expected  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("y", "i"),
        ("ie", "i"),
        ("ȳ", "i"),
        ("īe", "i"),
        ("yfele", "ifele"),
        ("micle", "micle"),
        ("stān", "stan"),
        ("", ""),
        (None, ""),
    ],
)
def test_normalize_output_reference(text: str | None, expected: str) -> None:
    assert OENormalizer.normalize_output(text) == expected  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("if", "If"),
        ("psinsg1", "PsInSg1"),
        ("pssusg", "PsSuSg"),
        ("impsg", "ImSg"),
        ("idif", "IdIf"),
        ("PsInSg2", "PsInSg2"),
        ("", ""),
    ],
)
def test_canonicalize_inflection_code_reference(raw: str, expected: str) -> None:
    assert canonicalize_inflection_code(raw) == expected
