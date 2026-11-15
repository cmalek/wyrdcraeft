"""Tests for pure entry presentation rules."""

from __future__ import annotations

import pytest

from wyrdcraeft.services.dictionary.browse_query import EntryDetails, EntrySense
from wyrdcraeft.services.dictionary.entry_view import (
    class_row_value,
    drop_empty_columns,
    key_value_rows,
    show_summary,
    strip_pos_prefix,
)
from wyrdcraeft.services.morphology.catalog.query import LemmaMorphClassSummary


def _summary(
    label: str, *, unclassified: bool = False, source: str = ""
) -> LemmaMorphClassSummary:
    return LemmaMorphClassSummary(
        display_label=label,
        assignment_source=source,
        wright_sections=(),
        is_unclassified=unclassified,
    )


def _details(**overrides: object) -> EntryDetails:
    base: dict[str, object] = {
        "entry_id": 1,
        "headword": "cuman",
        "variants": [],
        "pos": "verb",
        "class_summary": [],
        "genders": [],
        "persons": [],
        "numbers": [],
        "summary_sense": "",
        "senses": [],
        "etymology": "",
        "morphology_groups": [],
        "declension_paradigm": "",
        "morph_class": None,
    }
    base.update(overrides)
    return EntryDetails(**base)  # type: ignore[arg-type]


def test_class_row_verb_strips_prefix() -> None:
    assert class_row_value("verb", _summary("verb, weak class 2")) == "weak class 2"


def test_class_row_unclassified() -> None:
    assert class_row_value("noun", None) == "unclassified"
    assert class_row_value("adjective", _summary("x", unclassified=True)) == "unclassified"


@pytest.mark.parametrize(
    "pos",
    ["adverb", "preposition", "pronoun", "conjunction", "interjection", "unknown"],
)
def test_class_row_other_pos_none(pos: str) -> None:
    assert class_row_value(pos, None) is None
    assert class_row_value(pos, _summary("strong")) is None


def test_strip_pos_prefix() -> None:
    assert strip_pos_prefix("verb, strong class 7") == "strong class 7"
    assert strip_pos_prefix("strong a-/ō-stem") == "strong a-/ō-stem"


def test_show_summary() -> None:
    sense = EntrySense(sense_label="I", gloss_en="to come", order_index=0)
    assert not show_summary(_details(summary_sense="", senses=[sense]))
    assert not show_summary(_details(summary_sense="to come", senses=[sense]))
    assert show_summary(_details(summary_sense="to go", senses=[sense]))
    assert show_summary(_details(summary_sense="to go", senses=[]))


def test_key_value_rows() -> None:
    details = _details(
        pos="noun",
        variants=["cume"],
        genders=["m"],
        morph_class=_summary("strong a-stem", source="catalog"),
    )
    rows = key_value_rows(details)
    labels = [label for label, _ in rows]
    assert labels[0] == "Variants"
    assert labels[1:] == ["Class", "Gender", "Source"]
    assert dict(rows)["Source"] == "catalog"


def test_key_value_rows_omits_empty() -> None:
    assert key_value_rows(_details(pos="adverb")) == []


def test_drop_empty_columns() -> None:
    cols, rows = drop_empty_columns(("a", "b", "c"), [("1", "", "x"), ("2", "", "")])
    assert cols == ("a", "c")
    assert rows == (("1", "x"), ("2", ""))
