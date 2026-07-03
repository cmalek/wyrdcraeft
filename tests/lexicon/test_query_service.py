"""Tests for the lexicon query service."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

import pytest

from wyrdcraeft.services.dictionary.bt_spelling import BTSpellingNormalizer
from wyrdcraeft.services.lexicon.build import rebuild_lexicon
from wyrdcraeft.services.lexicon.query import (
    LexiconQueryService,
    SearchHit,
    _main_results_sort_key,
    _search_candidate_keys,
)

if TYPE_CHECKING:
    from pathlib import Path


def _rebuild_query_service(db_path: Path) -> LexiconQueryService:
    rebuild_lexicon(db_path)
    return LexiconQueryService(db_path)


def test_search_prefers_exact_dictionary_variant_and_dedupes_entries(
    lexicon_source_db: Path,
) -> None:
    service = _rebuild_query_service(lexicon_source_db)

    results = service.search("ABBOD")

    assert results.main_entry_count == 1
    assert not results.orphans
    assert len(results.main_entries) == 1
    hit = results.main_entries[0]
    assert hit.headword == "abbad"
    assert hit.pos == "noun"
    assert hit.rank_tier == 1
    assert hit.key_kind == "variant"
    assert hit.matched_text == "abbod"
    assert hit.summary_sense == "an abbot; abbot"


def test_search_candidate_keys_use_diacritic_stripped_normalizer() -> None:
    normalizer = BTSpellingNormalizer()
    keys = _search_candidate_keys("abbōd", normalizer)

    assert "abbod" in keys
    assert not any("ō" in key for key in keys)


@pytest.mark.parametrize("query", ["abbod", "abbōd", "ABBOD"])
def test_search_finds_abbad_for_undiacritized_and_macron_queries(
    lexicon_source_db: Path,
    query: str,
) -> None:
    service = _rebuild_query_service(lexicon_source_db)

    results = service.search(query)

    assert results.main_entry_count == 1
    assert results.main_entries[0].headword == "abbad"
    assert results.main_entries[0].pos == "noun"


def test_search_returns_morphology_form_hits_after_exact_matches(
    lexicon_source_db: Path,
) -> None:
    service = _rebuild_query_service(lexicon_source_db)

    results = service.search("abades")

    assert results.main_entry_count == 1
    assert not results.orphans
    hit = results.main_entries[0]
    assert hit.headword == "abbad"
    assert hit.rank_tier == 3
    assert hit.key_kind == "form"
    assert hit.matched_text == "abades"


def test_search_separates_orphan_hits_from_dictionary_entries(
    lexicon_source_db: Path,
) -> None:
    service = _rebuild_query_service(lexicon_source_db)

    results = service.search("orphan-form")

    assert not results.main_entries
    assert results.main_entry_count == 0
    assert len(results.orphans) == 1
    orphan = results.orphans[0]
    assert orphan.form_id > 0
    assert orphan.lemma == "orphan-lemma"
    assert orphan.wordclass == "noun"
    assert orphan.function == "No"
    assert orphan.rank_tier == 4
    assert orphan.key_kind == "form"
    assert orphan.matched_text == "orphan-form"


def test_query_service_uses_existing_alembic_managed_schema(
    lexicon_source_db: Path,
) -> None:
    rebuild_lexicon(lexicon_source_db)

    service = LexiconQueryService(lexicon_source_db)

    results = service.search("abbad")

    assert results.main_entry_count == 1


def test_get_details_returns_entry_payload_with_grouped_morphology(
    lexicon_source_db: Path,
) -> None:
    rebuild_lexicon(lexicon_source_db)
    with sqlite3.connect(lexicon_source_db) as connection:
        entry_id = int(
            connection.execute(
                "SELECT entry_id FROM lexicon_entries WHERE norm_key = ?",
                ("abbad",),
            ).fetchone()[0]
        )
        connection.execute(
            """
            UPDATE lexicon_forms
            SET function = ?, class1 = ?, class2 = ?, class3 = ?
            WHERE form_id = ?
            """,
            ("genitive singular", "m", "strong", "a-stem", 1),
        )
        connection.execute(
            """
            UPDATE lexicon_forms
            SET function = ?, class1 = ?, class2 = ?, class3 = ?
            WHERE form_id = ?
            """,
            ("nominative plural", "m", "strong", "a-stem", 2),
        )
        connection.commit()

    service = LexiconQueryService(lexicon_source_db)

    details = service.get_details(entry_id)

    assert details is not None
    assert details.entry_id == entry_id
    assert details.headword == "abbad"
    assert details.pos == "noun"
    assert details.variants == ["abbod", "abbud", "abbot"]
    assert details.summary_sense == "an abbot; abbot"
    assert [sense.gloss_en for sense in details.senses] == [
        "an abbot; abbot",
        "bishops were sometimes subject to an abbot, as they were to the abbots of Iona",
    ]
    assert details.class_summary == ["m", "strong", "a-stem"]
    assert details.genders == ["m"]
    assert details.persons == []
    assert details.numbers == ["singular", "plural"]
    assert len(details.morphology_groups) == 2
    assert details.morphology_groups[0].wordclass == "noun"
    assert details.morphology_groups[0].function == "genitive singular"
    assert details.morphology_groups[1].function == "nominative plural"


def test_main_results_sort_key_orders_by_lexical_distance() -> None:
    closer = SearchHit(
        entry_id=1,
        headword="mōd",
        pos="noun",
        summary_sense="",
        rank_tier=2,
        key_kind="stem",
        matched_text="mōd",
    )
    farther = SearchHit(
        entry_id=2,
        headword="acol-mōd",
        pos="adj",
        summary_sense="",
        rank_tier=2,
        key_kind="stem",
        matched_text="acol-mōd",
    )

    assert _main_results_sort_key("mōd", closer) < _main_results_sort_key(
        "mōd",
        farther,
    )
