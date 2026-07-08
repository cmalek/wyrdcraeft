"""Tests for BT display spelling normalization."""

from __future__ import annotations

import pytest

from wyrdcraeft.services.dictionary.bt_spelling import BTSpellingNormalizer


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("ā-beōdan.", "ā-bēodan."),
        ("a-beōdan;", "a-bēodan;"),
        ("ā-beōwed", "ā-bēowed"),
        ("a-bitweōnum", "a-bitwēonum"),
        ("a-breōtan;", "a-brēotan;"),
        ("ā-breōtan.", "ā-brēotan."),
        ("a-breōðan;", "a-brēoðan;"),
        ("ā-breōþan.", "ā-brēoþan."),
        ("ā-breōtness,", "ā-brēotness,"),
        ("a-ceōcian?", "a-cēocian?"),
        ("ā-ceōcian", "ā-cēocian"),
        ("a-ceōcung,", "a-cēocung,"),
        ("ā-ceōcung", "ā-cēocung"),
        ("a-ceōsan;", "a-cēosan;"),
        ("ā-ceōsan", "ā-cēosan"),
        ("ā-cleōfan", "ā-clēofan"),
        ("a-creōpian;", "a-crēopian;"),
        ("a-dreōgan,", "a-drēogan,"),
        ("ā-dreōgan.", "ā-drēogan."),
        ("a-dreōpan;", "a-drēopan;"),
        ("a-dreōsan;", "a-drēosan;"),
        ("abbod-leāst, e;", "abbod-lēast, e;"),
        ("āc-leāf,", "āc-lēaf,"),
        ("a-deāf;", "a-dēaf;"),
        ("ā-deāfian.", "ā-dēafian."),
        ("ælf-sciēne,", "ælf-scīene,"),
        ("eīg-land,", "ēig-land,"),
        ("tō-geīht;", "tō-gēiht;"),
    ],
)
def test_normalize_real_bt_diphthong_cases(source: str, expected: str) -> None:
    """
    Normalize representative real BT headword spellings from ``oe_bt.txt``.
    """
    normalizer = BTSpellingNormalizer()
    assert normalizer.normalize(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("eā", "ēa"),
        ("eō", "ēo"),
        ("eī", "ēi"),
        ("iē", "īe"),
    ],
)
def test_bt_spelling_normalizer_matches_oe_normalizer(
    source: str,
    expected: str,
) -> None:
    from wyrdcraeft.services.dictionary.bt_spelling import BTSpellingNormalizer
    from wyrdcraeft.services.morphology.text_utils import OENormalizer

    assert BTSpellingNormalizer().normalize(source) == expected
    assert OENormalizer.normalize_bt_display_spelling(source) == expected


@pytest.mark.parametrize("value", ["ā-bēodan", "abbod-lēast", "ælf-scīene"])
def test_normalize_is_idempotent(value: str) -> None:
    """
    Normalizing an already-normalized spelling is a no-op.
    """
    normalizer = BTSpellingNormalizer()
    assert normalizer.normalize(normalizer.normalize(value)) == value
