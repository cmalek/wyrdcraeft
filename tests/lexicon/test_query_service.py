"""Tests for the lexicon query service."""

from __future__ import annotations

import io
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
from wyrdcraeft.services.morphology.generation.common import print_one_form
from wyrdcraeft.services.morphology.generation.sinks import (
    CompositeSink,
    SqliteIndexSink,
    TsvParitySink,
)
from wyrdcraeft.services.morphology.session import GeneratorSession

if TYPE_CHECKING:
    from pathlib import Path


def _rebuild_query_service(db_path: Path) -> LexiconQueryService:
    rebuild_lexicon(db_path)
    return LexiconQueryService(db_path)


def _write_linked_form(
    db_path: Path,
    *,
    bt: str,
    form: str,
    wordclass: str = "noun",
    function: str = "No",
) -> None:
    """
    Write one morphology form after ``bt_*`` tables already exist.

    Note:
        ``FormFkResolver.resolve_entry_id`` resolves ``entry_id`` for this
        form at write time via ``NormalizedTitleJoinIndex``, so this helper
        must run after ``lexicon_source_db`` has seeded dictionary tables.

    Args:
        db_path: Morphology SQLite database already seeded with ``bt_*`` rows.

    Keyword Args:
        bt: Lemma title text shared by ``BT``/``title``/``stem`` fields.
        form: Emitted surface form text.
        wordclass: Morphology generator wordclass label.
        function: Morphology generator function code.

    Side Effects:
        Inserts one additional ``forms`` row into ``db_path``.

    """
    session = GeneratorSession()
    output = io.StringIO()
    sqlite_sink = SqliteIndexSink(db_path)
    sink = CompositeSink(TsvParitySink(output), sqlite_sink)
    try:
        print_one_form(
            session,
            {
                "BT": bt,
                "title": bt,
                "stem": bt,
                "form": form,
                "formParts": f"0-{bt}-0",
                "var": "0",
                "probability": "0",
                "function": function,
                "wright": "0",
                "paradigm": "demo",
                "paraID": "0",
                "wordclass": wordclass,
                "class1": "",
                "class2": "",
                "class3": "",
                "comment": "",
            },
            sink,
        )
    finally:
        sqlite_sink.close()


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
    _write_linked_form(lexicon_source_db, bt="abbad", form="abbadum")
    service = _rebuild_query_service(lexicon_source_db)

    results = service.search("abbadum")

    assert results.main_entry_count == 1
    assert not results.orphans
    hit = results.main_entries[0]
    assert hit.headword == "abbad"
    assert hit.rank_tier == 3
    assert hit.key_kind == "form"
    assert hit.matched_text == "abbadum"


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
        connection.row_factory = sqlite3.Row
        entry_id = int(
            connection.execute(
                "SELECT id FROM bt_entries WHERE norm_key = ?",
                ("abbad",),
            ).fetchone()[0]
        )
        connection.execute(
            """
            INSERT INTO forms (
                counter, formi, BT, title, normalized_title, stem, form,
                formParts, var, probability, function, wright, paradigm,
                paraID, wordclass, class1, class2, class3, comment,
                bt_key, title_key, stem_key, form_key, formi_key, entry_id
            ) VALUES (
                0, 'abbades', 'abbad', 'abbad', 'abbad', 'abbad', 'abbades',
                '0-abbad-0', '0', '0', ?, '0', 'demo', '0', 'noun',
                ?, ?, ?, '',
                'abbad', 'abbad', 'abbad', 'abbades', 'abbades', ?
            )
            """,
            ("genitive singular", "m", "strong", "a-stem", entry_id),
        )
        connection.execute(
            """
            INSERT INTO forms (
                counter, formi, BT, title, normalized_title, stem, form,
                formParts, var, probability, function, wright, paradigm,
                paraID, wordclass, class1, class2, class3, comment,
                bt_key, title_key, stem_key, form_key, formi_key, entry_id
            ) VALUES (
                0, 'abbadu', 'abbad', 'abbad', 'abbad', 'abbad', 'abbadu',
                '0-abbad-0', '0', '0', ?, '0', 'demo', '0', 'noun',
                ?, ?, ?, '',
                'abbad', 'abbad', 'abbad', 'abbadu', 'abbadu', ?
            )
            """,
            ("nominative plural", "m", "strong", "a-stem", entry_id),
        )
        connection.commit()

    service = LexiconQueryService(lexicon_source_db)

    details = service.get_details(entry_id)

    assert details is not None
    assert details.entry_id == entry_id
    assert details.headword == "abbad"
    assert details.pos == "noun"
    assert details.variants == ["abbod", "abbot", "abbud"]
    assert details.summary_sense == "an abbot; abbot"
    assert [sense.gloss_en for sense in details.senses] == [
        "an abbot; abbot",
        "bishops were sometimes subject to an abbot, as they were to the abbots of Iona",
    ]
    assert details.class_summary == ["m", "strong", "a-stem"]
    assert details.genders == ["m"]
    assert details.persons == []
    assert details.numbers == ["singular", "plural"]
    groups_by_function = {
        group.function: group for group in details.morphology_groups
    }
    assert groups_by_function["No"].wordclass == "noun"
    assert groups_by_function["genitive singular"].wordclass == "noun"
    assert groups_by_function["nominative plural"].function == "nominative plural"


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
