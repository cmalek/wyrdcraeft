"""Tests for lexicon read-model rebuild service."""

from __future__ import annotations

import json
import sqlite3
import threading
from typing import TYPE_CHECKING

import pytest

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
from wyrdcraeft.services.lexicon.query import LexiconQueryService
from wyrdcraeft.services.lexicon.schema import (
    KEY_KIND_FORM,
    KEY_KIND_LEMMA,
    KEY_KIND_STEM,
    KEY_KIND_VARIANT,
    META_KEY_BT_ENTRIES_SOURCE_COUNT,
    META_KEY_BUILT_AT,
    META_KEY_FORMS_SOURCE_COUNT,
    META_KEY_SCHEMA_VERSION,
    RANK_TIER_EXACT_ENTRY,
    RANK_TIER_MORPH_FORM,
    RANK_TIER_MORPH_LEMMA_STEM,
    RANK_TIER_ORPHAN,
    SCHEMA_VERSION,
    create_lexicon_tables,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_rebuild_lexicon_projects_entries_forms_keys_and_meta(
    lexicon_source_db: Path,
) -> None:
    report = rebuild_lexicon(lexicon_source_db)

    assert report.schema_version == SCHEMA_VERSION
    assert report.bt_entries_source_count > 0
    assert report.forms_source_count > 0
    assert report.entries_written == report.bt_entries_source_count
    assert report.search_keys_written > 0

    with sqlite3.connect(lexicon_source_db) as connection:
        connection.row_factory = sqlite3.Row
        entry = connection.execute(
            """
            SELECT entry_id, norm_key, summary_sense, variants_json, senses_json
            FROM lexicon_entries
            WHERE norm_key = ?
            """,
            ("abbad",),
        ).fetchone()
        assert entry is not None
        assert str(entry["summary_sense"]).strip()
        assert json.loads(str(entry["variants_json"]))
        senses = json.loads(str(entry["senses_json"]))
        assert senses
        assert str(senses[0]["gloss_en"]).strip()

        linked_forms = connection.execute(
            "SELECT COUNT(*) FROM lexicon_forms WHERE entry_id IS NOT NULL"
        ).fetchone()[0]
        orphan_forms = connection.execute(
            "SELECT COUNT(*) FROM lexicon_forms WHERE entry_id IS NULL"
        ).fetchone()[0]
        assert linked_forms > 0
        assert orphan_forms > 0

        tiers_present = {
            int(row[0])
            for row in connection.execute(
                "SELECT DISTINCT rank_tier FROM lexicon_search_keys"
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
                "SELECT DISTINCT key_kind FROM lexicon_search_keys"
            ).fetchall()
        }
        assert {
            KEY_KIND_LEMMA,
            KEY_KIND_VARIANT,
            KEY_KIND_STEM,
            KEY_KIND_FORM,
        }.issubset(kinds_present)

        meta_rows = dict(
            connection.execute(
                "SELECT key, value FROM lexicon_build_meta ORDER BY key"
            ).fetchall()
        )
        assert meta_rows[META_KEY_SCHEMA_VERSION] == str(SCHEMA_VERSION)
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
        lexicon_entries = connection.execute(
            "SELECT COUNT(*) FROM lexicon_entries"
        ).fetchone()[0]
        lexicon_forms = connection.execute("SELECT COUNT(*) FROM lexicon_forms").fetchone()[
            0
        ]
        lexicon_keys = connection.execute(
            "SELECT COUNT(*) FROM lexicon_search_keys"
        ).fetchone()[0]

    assert forms_before == forms_after
    assert entries_before == entries_after
    assert variants_before == variants_after
    assert senses_before == senses_after
    assert first.entries_written == second.entries_written == lexicon_entries
    assert first.forms_written == second.forms_written == lexicon_forms
    assert first.search_keys_written == second.search_keys_written == lexicon_keys


def test_create_lexicon_tables_dedupes_null_join_search_keys_with_insert_or_ignore(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "search-keys-dedupe.sqlite3"
    with sqlite3.connect(db_path) as connection:
        create_lexicon_tables(connection)
        connection.execute(
            """
            INSERT OR IGNORE INTO lexicon_search_keys (
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
            INSERT OR IGNORE INTO lexicon_search_keys (
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

        count = connection.execute(
            "SELECT COUNT(*) FROM lexicon_search_keys"
        ).fetchone()[0]

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
        connection: sqlite3.Connection,
        entries: list[dict[str, object]],
        forms_count: int,
    ) -> int:
        original(self, connection, entries, forms_count)
        connection.execute("DELETE FROM temp_lexicon_search_keys_stage")
        connection.execute(
            """
            INSERT INTO temp_lexicon_search_keys_stage (
                key_text,
                key_kind,
                rank_tier,
                entry_id,
                form_id,
                display_text
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("abbad", KEY_KIND_LEMMA, RANK_TIER_EXACT_ENTRY, 1, None, "abbad"),
        )
        connection.execute(
            """
            INSERT INTO temp_lexicon_search_keys_stage (
                key_text,
                key_kind,
                rank_tier,
                entry_id,
                form_id,
                display_text
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("abbad", KEY_KIND_LEMMA, RANK_TIER_EXACT_ENTRY, 1, None, "abbad"),
        )
        connection.execute(
            """
            INSERT INTO temp_lexicon_search_keys_stage (
                key_text,
                key_kind,
                rank_tier,
                entry_id,
                form_id,
                display_text
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("abbode", KEY_KIND_VARIANT, RANK_TIER_EXACT_ENTRY, 1, None, "abbode"),
        )
        return 3

    monkeypatch.setattr(LexiconBuilder, "_build_search_keys", build_duplicates)

    report = rebuild_lexicon(lexicon_source_db, event_sink=events.append)

    with sqlite3.connect(lexicon_source_db) as connection:
        db_count = connection.execute(
            "SELECT COUNT(*) FROM lexicon_search_keys"
        ).fetchone()[0]

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
                counter, formi, BT, title, stem, form, formParts, var,
                probability, function, wright, paradigm, paraID, wordclass,
                class1, class2, class3, comment,
                bt_key, title_key, stem_key, form_key, formi_key
            ) VALUES (
                999, 'new-form', 'new', 'new', 'new', 'new-form', '0-new-0',
                '0', '0', 'No', '0', 'demo', '0', 'noun',
                '', '', '', '',
                'new', 'new', 'new', 'new-form', 'new-form'
            )
            """
        )
        connection.commit()

    report = check_lexicon_staleness(lexicon_source_db)

    assert report.is_stale
    assert "forms" in report.reason


def test_build_then_query_integration_smoke(lexicon_source_db: Path) -> None:
    report = rebuild_lexicon(lexicon_source_db)

    with sqlite3.connect(lexicon_source_db) as connection:
        meta = read_lexicon_build_meta(connection)

    assert meta is not None
    assert meta.built_at == report.built_at
    assert report.pos_inferred >= 0

    service = LexiconQueryService(lexicon_source_db)
    try:
        results = service.search("ABBOD")
        assert results.main_entry_count == 1
        details = service.get_details(results.main_entries[0].entry_id)
        assert details is not None
        assert details.headword == "abbad"
    finally:
        service.close()


def test_rebuild_lexicon_infers_pos_from_unambiguous_morphology(
    lexicon_source_db: Path,
) -> None:
    with sqlite3.connect(lexicon_source_db) as connection:
        connection.execute(
            "UPDATE bt_entries SET pos = '' WHERE norm_key = ?",
            ("abbad",),
        )
        connection.commit()

    report = rebuild_lexicon(lexicon_source_db)
    assert report.pos_inferred >= 1

    with sqlite3.connect(lexicon_source_db) as connection:
        connection.row_factory = sqlite3.Row
        pos = connection.execute(
            "SELECT pos FROM bt_entries WHERE norm_key = ?",
            ("abbad",),
        ).fetchone()
        assert pos is not None
        assert str(pos["pos"]) == "noun"


def test_rebuild_lexicon_emits_structured_stage_log_and_counter_event_contract(
    lexicon_source_db: Path,
) -> None:
    events: list[object] = []

    report = rebuild_lexicon(lexicon_source_db, event_sink=events.append)

    assert report.entries_written > 0
    assert any(isinstance(event, BuildStageStarted) for event in events)
    assert any(
        isinstance(event, BuildLog) and event.stage == LexiconBuildStage.LOAD_FORMS
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
    assert started_stages.count(LexiconBuildStage.LOAD_ENTRIES) == 1


def test_rebuild_lexicon_emits_infer_pos_stage_start_without_progress_callback(
    lexicon_source_db: Path,
) -> None:
    with sqlite3.connect(lexicon_source_db) as connection:
        connection.execute(
            "UPDATE bt_entries SET pos = '' WHERE norm_key = ?",
            ("abbad",),
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
            and event.stage == LexiconBuildStage.LOAD_FORMS
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
        and event.stage == LexiconBuildStage.LOAD_FORMS
        for event in events
    )


def test_rebuild_lexicon_emits_load_forms_progress_with_current_item(
    lexicon_source_db: Path,
) -> None:
    events: list[object] = []

    report = rebuild_lexicon(lexicon_source_db, event_sink=events.append)

    load_form_events = [
        event
        for event in events
        if getattr(event, "stage", None) == LexiconBuildStage.LOAD_FORMS
    ]
    assert load_form_events
    assert any(getattr(event, "current_item", "") for event in load_form_events)
    progress_events = [
        event for event in load_form_events if isinstance(event, BuildStageProgress)
    ]
    assert len(progress_events) <= report.forms_source_count


def test_rebuild_lexicon_emits_insert_forms_progress_during_batch_insert(
    lexicon_source_db: Path,
) -> None:
    events: list[object] = []

    report = rebuild_lexicon(lexicon_source_db, event_sink=events.append)

    insert_progress_events = [
        event
        for event in events
        if isinstance(event, BuildStageProgress)
        and event.stage == LexiconBuildStage.INSERT_FORMS
    ]
    assert insert_progress_events
    assert insert_progress_events[0].completed == 0
    assert insert_progress_events[-1].completed == max(report.forms_source_count, 1)
    if report.forms_source_count > 1:
        assert len(insert_progress_events) > 2


def test_rebuild_lexicon_cancel_rolls_back_partial_form_work(
    lexicon_source_db: Path,
) -> None:
    cancel_event = threading.Event()

    def sink(event: object) -> None:
        if (
            getattr(event, "stage", None) == LexiconBuildStage.LOAD_FORMS
            and getattr(event, "completed", 0) >= 1
        ):
            cancel_event.set()

    with pytest.raises(LexiconBuildCancelledError):
        rebuild_lexicon(lexicon_source_db, event_sink=sink, cancel_event=cancel_event)

    with sqlite3.connect(lexicon_source_db) as connection:
        assert connection.execute("SELECT COUNT(*) FROM lexicon_forms").fetchone()[0] == 0
