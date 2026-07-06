"""Tests for morphology catalog POS normalization helpers."""

from __future__ import annotations

import sqlite3

import pytest

from wyrdcraeft.models.dictionary import BTPos
from wyrdcraeft.services.morphology.catalog.pos import (
    catalog_pos_from_bt_pos,
    catalog_pos_from_wordclass,
    pos_id_from_bt_pos,
    pos_id_from_catalog_pos,
    pos_id_from_wordclass,
)
from wyrdcraeft.services.morphology.catalog.pos_seed import ensure_parts_of_speech

#: Generator wordclass keys from ``generation/query.py`` ``_WORDCLASS_TO_BT_POS``.
_GENERATION_WORDCLASSES: frozenset[str] = frozenset(
    {
        "noun",
        "verb",
        "adjective",
        "adverb",
        "numeral",
        "pronoun",
        "preposition",
        "conjunction",
        "interjection",
        "indeclinable",
    },
)

#: Expected catalog POS for each morphology generator wordclass.
_WORDCLASS_EXPECTED: dict[str, str | None] = {
    "noun": "noun",
    "verb": "verb",
    "adjective": "adjective",
    "adverb": "adverb",
    "pronoun": "pronoun",
    "participle": "adjective",
    "preposition": None,
    "conjunction": None,
    "interjection": None,
    "indeclinable": None,
    "numeral": None,
}

#: BT POS values used in morphology dictionary joins → catalog POS.
_BT_POS_JOIN_EXPECTED: dict[str, str] = {
    BTPos.NOUN.value: "noun",
    BTPos.VERB.value: "verb",
    BTPos.ADJ.value: "adjective",
    BTPos.ADV.value: "adverb",
    BTPos.PRON.value: "pronoun",
    BTPos.NUMERAL.value: "numeral",
}

#: BT POS values joined but without catalog morph classes.
_BT_POS_UNMAPPED: tuple[str, ...] = (
    BTPos.PREP.value,
    BTPos.CONJ.value,
    BTPos.INTERJ.value,
    BTPos.INDECL.value,
    BTPos.UNKNOWN.value,
)

#: CLI POS aliases mirrored by both dictionary lookup filters and catalog helpers.
_CLI_POS_ALIASES: dict[str, str] = {
    "n": BTPos.NOUN.value,
    "v": BTPos.VERB.value,
    "a": BTPos.ADJ.value,
    "adjective": BTPos.ADJ.value,
    "adverb": BTPos.ADV.value,
    "num": BTPos.NUMERAL.value,
}


@pytest.mark.parametrize(
    ("wordclass", "expected"),
    sorted(_WORDCLASS_EXPECTED.items()),
    ids=sorted(_WORDCLASS_EXPECTED),
)
def test_catalog_pos_from_wordclass(wordclass: str, expected: str | None) -> None:
    assert catalog_pos_from_wordclass(wordclass) == expected
    assert catalog_pos_from_wordclass(f"  {wordclass.upper()}  ") == expected


def test_wordclass_map_covers_generation_query_keys() -> None:
    assert set(_WORDCLASS_EXPECTED) == _GENERATION_WORDCLASSES | {"participle"}


@pytest.mark.parametrize(
    ("bt_pos", "expected"),
    sorted(_BT_POS_JOIN_EXPECTED.items()),
    ids=sorted(_BT_POS_JOIN_EXPECTED),
)
def test_catalog_pos_from_bt_pos_join_values(bt_pos: str, expected: str) -> None:
    assert catalog_pos_from_bt_pos(bt_pos) == expected


@pytest.mark.parametrize(
    ("alias", "stored_pos"),
    sorted(_CLI_POS_ALIASES.items()),
    ids=sorted(_CLI_POS_ALIASES),
)
def test_catalog_pos_from_bt_pos_cli_aliases(alias: str, stored_pos: str) -> None:
    assert catalog_pos_from_bt_pos(alias) == catalog_pos_from_bt_pos(stored_pos)


@pytest.mark.parametrize("bt_pos", _BT_POS_UNMAPPED, ids=_BT_POS_UNMAPPED)
def test_catalog_pos_from_bt_pos_raises_for_unmapped(bt_pos: str) -> None:
    with pytest.raises(ValueError, match="no catalog POS mapping"):
        catalog_pos_from_bt_pos(bt_pos)


def test_catalog_pos_from_wordclass_unknown_returns_none() -> None:
    assert catalog_pos_from_wordclass("particle") is None


@pytest.mark.parametrize(
    ("bt_pos", "expected_code"),
    [
        (BTPos.NOUN.value, "noun"),
        (BTPos.ADJ.value, "adjective"),
        (BTPos.PREP.value, "preposition"),
        (BTPos.UNKNOWN.value, "unknown"),
        ("a", "adjective"),
    ],
    ids=("noun", "adj", "prep", "unknown", "alias-a"),
)
def test_pos_id_from_bt_pos(bt_pos: str, expected_code: str) -> None:
    with sqlite3.connect(":memory:") as connection:
        pos_map = ensure_parts_of_speech(connection)

        assert pos_id_from_bt_pos(connection, bt_pos) == pos_map[expected_code]


def test_pos_id_from_bt_pos_raises_for_unknown_value() -> None:
    with sqlite3.connect(":memory:") as connection:
        ensure_parts_of_speech(connection)

        with pytest.raises(ValueError, match="no canonical POS mapping"):
            pos_id_from_bt_pos(connection, "particle")


def test_pos_id_from_wordclass_returns_none_for_unmappable_value() -> None:
    with sqlite3.connect(":memory:") as connection:
        ensure_parts_of_speech(connection)

        assert pos_id_from_wordclass(connection, "particle") is None


@pytest.mark.parametrize(
    ("wordclass", "expected_code"),
    [
        ("noun", "noun"),
        ("preposition", "preposition"),
        ("numeral", "numeral"),
        ("participle", "participle"),
    ],
    ids=("noun", "preposition", "numeral", "participle"),
)
def test_pos_id_from_wordclass_resolves_seeded_rows(
    wordclass: str,
    expected_code: str,
) -> None:
    with sqlite3.connect(":memory:") as connection:
        pos_map = ensure_parts_of_speech(connection)

        assert pos_id_from_wordclass(connection, wordclass) == pos_map[expected_code]


def test_pos_id_from_catalog_pos_resolves_seeded_adjective_row() -> None:
    with sqlite3.connect(":memory:") as connection:
        pos_map = ensure_parts_of_speech(connection)

        assert pos_id_from_catalog_pos(connection, "adjective") == pos_map["adjective"]


def test_pos_id_resolvers_remain_stable_after_double_seed() -> None:
    with sqlite3.connect(":memory:") as connection:
        first_pos_map = ensure_parts_of_speech(connection)
        second_pos_map = ensure_parts_of_speech(connection)

        assert first_pos_map == second_pos_map
        assert pos_id_from_catalog_pos(connection, "adjective") == second_pos_map["adjective"]
