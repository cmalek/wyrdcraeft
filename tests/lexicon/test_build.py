"""Tests for lexicon search-index rebuild service."""

from __future__ import annotations

import io
import sqlite3
import threading
from typing import TYPE_CHECKING

import pytest

from tests.lexicon.source_db import make_lexicon_source_db
from wyrdcraeft.db.runtime import upgrade_canonical_db
from wyrdcraeft.models.lexicon_build import (
    BuildCounterUpdated,
    BuildLog,
    BuildStageProgress,
    BuildStageStarted,
    LexiconBuildStage,
)
from wyrdcraeft.services.lexicon.build import (
    LexiconBuildCancelledError,
    LexiconBuilder,
    MissingLexiconSourceTablesError,
    check_lexicon_staleness,
    read_lexicon_build_meta,
    rebuild_lexicon,
)
from wyrdcraeft.services.lexicon.schema import (
    KEY_KIND_FORM,
    KEY_KIND_LEMMA,
    KEY_KIND_STEM,
    KEY_KIND_VARIANT,
    META_KEY_BT_ENTRIES_SOURCE_COUNT,
    META_KEY_BUILT_AT,
    META_KEY_FORMS_SOURCE_COUNT,
    RANK_TIER_EXACT_ENTRY,
    RANK_TIER_MORPH_FORM,
    RANK_TIER_MORPH_LEMMA_STEM,
    RANK_TIER_ORPHAN,
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


def _write_linked_abbod_form(db_path: Path) -> None:
    """
    Write one additional ``abbod`` form after dictionary tables already exist.

    Note:
        ``FormFkResolver.resolve_entry_id`` resolves this form's ``entry_id``
        via ``bt_variants.normalized_title`` at write time (the ``abbad``
        entry's ``abbod`` spelling variant), producing a form linked to a
        dictionary entry for tests that exercise the morphology linked tier.

    Args:
        db_path: Morphology SQLite database already seeded with ``bt_*`` rows.

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
                "BT": "abbod",
                "title": "abbod",
                "stem": "abbod",
                "form": "abbod",
                "formParts": "0-abbod-0",
                "var": "0",
                "probability": "0",
                "function": "No",
                "wright": "0",
                "paradigm": "demo",
                "paraID": "0",
                "wordclass": "noun",
                "class1": "",
                "class2": "",
                "class3": "",
                "comment": "",
            },
            sink,
        )
    finally:
        sqlite_sink.close()


def test_rebuild_lexicon_emits_dictionary_and_morphology_search_keys(
    lexicon_source_db: Path,
) -> None:
    _write_linked_abbod_form(lexicon_source_db)

    report = rebuild_lexicon(lexicon_source_db)

    assert report.bt_entries_source_count > 0
    assert report.forms_source_count > 0
    assert report.search_keys_written > 0

    with sqlite3.connect(lexicon_source_db) as connection:
        connection.row_factory = sqlite3.Row

        tiers_present = {
            int(row[0])
            for row in connection.execute(
                "SELECT DISTINCT rank_tier FROM search_keys"
            ).fetchall()
        }
        assert {
            RANK_TIER_EXACT_ENTRY,
            RANK_TIER_MORPH_LEMMA_STEM,
            RANK_TIER_MORPH_FORM,
            RANK_TIER_ORPHAN,
        }.issubset(tiers_present)

        kinds_present = {
            str(row[0])
            for row in connection.execute(
                "SELECT DISTINCT key_kind FROM search_keys"
            ).fetchall()
        }
        assert {
            KEY_KIND_LEMMA,
            KEY_KIND_VARIANT,
            KEY_KIND_STEM,
            KEY_KIND_FORM,
        }.issubset(kinds_present)

        linked_row = connection.execute(
            """
            SELECT bt_entries.norm_key
            FROM search_keys
            JOIN bt_entries ON bt_entries.id = search_keys.entry_id
            WHERE search_keys.rank_tier = ?
            """,
            (RANK_TIER_MORPH_LEMMA_STEM,),
        ).fetchone()
        assert linked_row is not None
        assert linked_row["norm_key"] == "abbad"

        orphan_count = connection.execute(
            "SELECT COUNT(*) FROM search_keys WHERE rank_tier = ?",
            (RANK_TIER_ORPHAN,),
        ).fetchone()[0]
        assert orphan_count > 0

        meta_rows = dict(
            connection.execute(
                "SELECT key, value FROM search_build_meta ORDER BY key"
            ).fetchall()
        )
        assert meta_rows[META_KEY_FORMS_SOURCE_COUNT] == str(report.forms_source_count)
        assert meta_rows[META_KEY_BT_ENTRIES_SOURCE_COUNT] == str(
            report.bt_entries_source_count
        )
        assert meta_rows[META_KEY_BUILT_AT] == report.built_at


def test_rebuild_lexicon_is_idempotent_and_preserves_sources(
    lexicon_source_db: Path,
) -> None:
    with sqlite3.connect(lexicon_source_db) as connection:
        forms_before = connection.execute("SELECT COUNT(*) FROM forms").fetchone()[0]
        entries_before = connection.execute("SELECT COUNT(*) FROM bt_entries").fetchone()[
            0
        ]
        variants_before = connection.execute(
            "SELECT COUNT(*) FROM bt_variants"
        ).fetchone()[0]
        senses_before = connection.execute("SELECT COUNT(*) FROM bt_senses").fetchone()[0]

    first = rebuild_lexicon(lexicon_source_db)
    second = rebuild_lexicon(lexicon_source_db)

    with sqlite3.connect(lexicon_source_db) as connection:
        forms_after = connection.execute("SELECT COUNT(*) FROM forms").fetchone()[0]
        entries_after = connection.execute("SELECT COUNT(*) FROM bt_entries").fetchone()[
            0
        ]
        variants_after = connection.execute("SELECT COUNT(*) FROM bt_variants").fetchone()[
            0
        ]
        senses_after = connection.execute("SELECT COUNT(*) FROM bt_senses").fetchone()[0]
        search_keys = connection.execute(
            "SELECT COUNT(*) FROM search_keys"
        ).fetchone()[0]

    assert forms_before == forms_after
    assert entries_before == entries_after
    assert variants_before == variants_after
    assert senses_before == senses_after
    assert first.search_keys_written == second.search_keys_written == search_keys


def test_rebuild_lexicon_uses_existing_alembic_managed_lexicon_tables(
    lexicon_source_db: Path,
) -> None:
    report = rebuild_lexicon(lexicon_source_db)

    assert report.search_keys_written > 0


def test_rebuild_lexicon_joins_abbod_form_via_variant_normalized_title(
    tmp_path: Path,
) -> None:
    db_path = make_lexicon_source_db(tmp_path / "variant-join.sqlite3")
    _write_linked_abbod_form(db_path)

    rebuild_lexicon(db_path)

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        form_row = connection.execute(
            "SELECT id, entry_id FROM forms WHERE normalized_title = ?",
            ("abbod",),
        ).fetchone()
        assert form_row is not None
        assert form_row["entry_id"] is not None

        entry_row = connection.execute(
            "SELECT norm_key FROM bt_entries WHERE id = ?",
            (form_row["entry_id"],),
        ).fetchone()
        assert entry_row is not None
        assert entry_row["norm_key"] == "abbad"

        search_key_row = connection.execute(
            """
            SELECT rank_tier
            FROM search_keys
            WHERE entry_id = ? AND form_id = ?
            """,
            (form_row["entry_id"], form_row["id"]),
        ).fetchone()
        assert search_key_row is not None
        assert int(search_key_row["rank_tier"]) in {
            RANK_TIER_MORPH_LEMMA_STEM,
            RANK_TIER_MORPH_FORM,
        }


def test_alembic_managed_search_keys_dedupe_null_join_rows_with_insert_or_ignore(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "search-keys-dedupe.sqlite3"
    upgrade_canonical_db(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO search_keys (
                key_text,
                key_kind,
                rank_tier,
                entry_id,
                form_id,
                display_text
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("abbad", KEY_KIND_LEMMA, RANK_TIER_ORPHAN, None, None, "abbad"),
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO search_keys (
                key_text,
                key_kind,
                rank_tier,
                entry_id,
                form_id,
                display_text
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("abbad", KEY_KIND_LEMMA, RANK_TIER_ORPHAN, None, None, "abbad"),
        )

        count = connection.execute("SELECT COUNT(*) FROM search_keys").fetchone()[0]

    assert count == 1


def test_rebuild_lexicon_raises_on_missing_source_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "missing-sources.sqlite3"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE forms (id INTEGER PRIMARY KEY)")
        connection.commit()

    with pytest.raises(MissingLexiconSourceTablesError):
        rebuild_lexicon(db_path)


def test_rebuild_lexicon_reports_search_keys_counter_from_db_truth(
    lexicon_source_db: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[object] = []
    original = LexiconBuilder._build_search_keys

    def build_duplicates(
        self: LexiconBuilder,
        connection: object,
        forms_source_count: int,
    ) -> list[dict[str, object]]:
        original(self, connection, forms_source_count)
        return [
            {
                "key_text": "abbad",
                "key_kind": KEY_KIND_LEMMA,
                "rank_tier": RANK_TIER_EXACT_ENTRY,
                "entry_id": 1,
                "form_id": None,
                "display_text": "abbad",
            },
            {
                "key_text": "abbad",
                "key_kind": KEY_KIND_LEMMA,
                "rank_tier": RANK_TIER_EXACT_ENTRY,
                "entry_id": 1,
                "form_id": None,
                "display_text": "abbad",
            },
            {
                "key_text": "abbode",
                "key_kind": KEY_KIND_VARIANT,
                "rank_tier": RANK_TIER_EXACT_ENTRY,
                "entry_id": 1,
                "form_id": None,
                "display_text": "abbode",
            },
        ]

    monkeypatch.setattr(LexiconBuilder, "_build_search_keys", build_duplicates)

    report = rebuild_lexicon(lexicon_source_db, event_sink=events.append)

    with sqlite3.connect(lexicon_source_db) as connection:
        db_count = connection.execute("SELECT COUNT(*) FROM search_keys").fetchone()[0]

    counter_values = [
        event.value
        for event in events
        if isinstance(event, BuildCounterUpdated)
        and event.counter == "search_keys_written"
    ]
    assert counter_values
    assert report.search_keys_written == db_count == counter_values[-1] == 2


def test_check_lexicon_staleness_reports_fresh_after_rebuild(
    lexicon_source_db: Path,
) -> None:
    rebuild_lexicon(lexicon_source_db)

    report = check_lexicon_staleness(lexicon_source_db)

    assert not report.is_stale
    assert report.meta is not None
    assert report.current_forms_count == report.meta.forms_source_count
    assert report.current_bt_entries_count == report.meta.bt_entries_source_count


def test_check_lexicon_staleness_detects_new_forms_rows(
    lexicon_source_db: Path,
) -> None:
    rebuild_lexicon(lexicon_source_db)

    with sqlite3.connect(lexicon_source_db) as connection:
        connection.execute(
            """
            INSERT INTO forms (
                counter, formi, BT, title, normalized_title, stem, form,
                formParts, var, probability, comment,
                bt_key, title_key, stem_key, form_key, formi_key
            ) VALUES (
                999, 'new-form', 'new', 'new', 'new', 'new', 'new-form',
                '0-new-0', '0', '0', '',
                'new', 'new', 'new', 'new-form', 'new-form'
            )
            """
        )
        connection.commit()

    report = check_lexicon_staleness(lexicon_source_db)

    assert report.is_stale
    assert "forms" in report.reason


def test_build_then_search_keys_support_undiacritized_lookup(
    lexicon_source_db: Path,
) -> None:
    report = rebuild_lexicon(lexicon_source_db)

    meta = read_lexicon_build_meta(lexicon_source_db)

    assert meta is not None
    assert meta.built_at == report.built_at
    assert report.pos_inferred >= 0

    with sqlite3.connect(lexicon_source_db) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT bt_entries.headword
            FROM search_keys
            JOIN bt_entries ON bt_entries.id = search_keys.entry_id
            WHERE search_keys.key_text = ?
            """,
            ("abbod",),
        ).fetchone()

    assert row is not None
    assert row["headword"] == "abbad"


def _unknown_pos_id(connection: sqlite3.Connection) -> int:
    """Return the seeded ``unknown`` part-of-speech row id."""
    row = connection.execute(
        "SELECT id FROM parts_of_speech WHERE code = 'unknown'",
    ).fetchone()
    assert row is not None
    return int(row[0])


def test_rebuild_lexicon_infers_pos_from_unambiguous_morphology(
    lexicon_source_db: Path,
) -> None:
    with sqlite3.connect(lexicon_source_db) as connection:
        connection.execute(
            "UPDATE bt_entries SET pos_id = ? WHERE norm_key = ?",
            (_unknown_pos_id(connection), "abbad"),
        )
        connection.commit()

    report = rebuild_lexicon(lexicon_source_db)
    assert report.pos_inferred >= 1

    with sqlite3.connect(lexicon_source_db) as connection:
        connection.row_factory = sqlite3.Row
        pos = connection.execute(
            """
            SELECT parts_of_speech.code
            FROM bt_entries
            JOIN parts_of_speech ON parts_of_speech.id = bt_entries.pos_id
            WHERE bt_entries.norm_key = ?
            """,
            ("abbad",),
        ).fetchone()
        assert pos is not None
        assert str(pos["code"]) == "noun"


def test_rebuild_lexicon_emits_structured_stage_log_and_counter_event_contract(
    lexicon_source_db: Path,
) -> None:
    events: list[object] = []

    report = rebuild_lexicon(lexicon_source_db, event_sink=events.append)

    assert report.search_keys_written > 0
    assert any(isinstance(event, BuildStageStarted) for event in events)
    assert any(
        isinstance(event, BuildLog)
        and event.stage == LexiconBuildStage.BUILD_MORPHOLOGY_KEYS
        for event in events
    )
    assert any(
        isinstance(event, BuildCounterUpdated)
        and event.counter == "search_keys_written"
        for event in events
    )


def test_rebuild_lexicon_emits_single_stage_start_per_top_level_stage(
    lexicon_source_db: Path,
) -> None:
    events: list[object] = []

    rebuild_lexicon(lexicon_source_db, event_sink=events.append)

    started_stages = [
        event.stage for event in events if isinstance(event, BuildStageStarted)
    ]
    assert started_stages.count(LexiconBuildStage.BUILD_DICTIONARY_KEYS) == 1


def test_rebuild_lexicon_emits_infer_pos_stage_start_without_progress_callback(
    lexicon_source_db: Path,
) -> None:
    with sqlite3.connect(lexicon_source_db) as connection:
        connection.execute(
            "UPDATE bt_entries SET pos_id = ? WHERE norm_key = ?",
            (_unknown_pos_id(connection), "abbad"),
        )
        connection.commit()

    events: list[object] = []

    rebuild_lexicon(lexicon_source_db, event_sink=events.append)

    assert any(
        isinstance(event, BuildStageStarted)
        and event.stage == LexiconBuildStage.INFER_POS
        for event in events
    )


def test_rebuild_lexicon_emits_completed_progress_for_verify_sources(
    lexicon_source_db: Path,
) -> None:
    events: list[object] = []

    rebuild_lexicon(lexicon_source_db, event_sink=events.append)

    verify_progress_events = [
        event
        for event in events
        if isinstance(event, BuildStageProgress)
        and event.stage == LexiconBuildStage.VERIFY_SOURCES
    ]

    assert verify_progress_events
    assert verify_progress_events[-1].completed == 1
    assert verify_progress_events[-1].total == 1


def test_rebuild_lexicon_cancel_raises_cancelled_error_when_cancel_requested(
    lexicon_source_db: Path,
) -> None:
    cancel_event = threading.Event()
    events: list[object] = []

    def sink(event: object) -> None:
        events.append(event)
        if (
            isinstance(event, BuildStageStarted)
            and event.stage == LexiconBuildStage.BUILD_MORPHOLOGY_KEYS
        ):
            cancel_event.set()

    with pytest.raises(LexiconBuildCancelledError):
        rebuild_lexicon(
            lexicon_source_db,
            event_sink=sink,
            cancel_event=cancel_event,
        )

    assert any(
        isinstance(event, BuildStageStarted)
        and event.stage == LexiconBuildStage.BUILD_MORPHOLOGY_KEYS
        for event in events
    )


def test_rebuild_lexicon_emits_morphology_key_progress_with_current_item(
    lexicon_source_db: Path,
) -> None:
    events: list[object] = []

    report = rebuild_lexicon(lexicon_source_db, event_sink=events.append)

    morphology_events = [
        event
        for event in events
        if getattr(event, "stage", None) == LexiconBuildStage.BUILD_MORPHOLOGY_KEYS
    ]
    assert morphology_events
    assert any(getattr(event, "current_item", "") for event in morphology_events)
    progress_events = [
        event for event in morphology_events if isinstance(event, BuildStageProgress)
    ]
    assert len(progress_events) <= report.forms_source_count


def test_rebuild_lexicon_emits_insert_search_keys_progress_during_batch_insert(
    lexicon_source_db: Path,
) -> None:
    events: list[object] = []

    report = rebuild_lexicon(lexicon_source_db, event_sink=events.append)

    insert_progress_events = [
        event
        for event in events
        if isinstance(event, BuildStageProgress)
        and event.stage == LexiconBuildStage.INSERT_SEARCH_KEYS
    ]
    assert insert_progress_events
    assert insert_progress_events[0].completed == 0
    assert insert_progress_events[-1].completed == insert_progress_events[-1].total
    assert insert_progress_events[-1].completed >= report.search_keys_written


def test_rebuild_lexicon_cancel_rolls_back_partial_form_work(
    lexicon_source_db: Path,
) -> None:
    cancel_event = threading.Event()

    def sink(event: object) -> None:
        if (
            getattr(event, "stage", None) == LexiconBuildStage.BUILD_MORPHOLOGY_KEYS
            and getattr(event, "completed", 0) >= 1
        ):
            cancel_event.set()

    with pytest.raises(LexiconBuildCancelledError):
        rebuild_lexicon(lexicon_source_db, event_sink=sink, cancel_event=cancel_event)

    with sqlite3.connect(lexicon_source_db) as connection:
        assert connection.execute("SELECT COUNT(*) FROM search_keys").fetchone()[0] == 0
