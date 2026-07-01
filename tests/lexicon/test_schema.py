"""Tests for lexicon read-model schema helpers."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

import pytest

from wyrdcraeft.db.runtime import DatabaseStartupRuntime
from wyrdcraeft.services.lexicon.schema import (
    KEY_KIND_LEMMA,
    LEXICON_TABLE_NAMES,
    META_KEY_SCHEMA_VERSION,
    RANK_TIER_EXACT_ENTRY,
    SCHEMA_VERSION,
    create_lexicon_tables,
    migrate_lexicon_schema,
)
from wyrdcraeft.settings import Settings

if TYPE_CHECKING:
    from pathlib import Path


EXPECTED_CANONICAL_TABLES = {
    "alembic_version",
    "forms",
    "bt_entries",
    "bt_senses",
    "bt_variants",
    "bt_edit_log",
    "lexicon_entries",
    "lexicon_forms",
    "lexicon_search_keys",
    "lexicon_build_meta",
}

EXPECTED_CANONICAL_INDEXES = {
    "idx_forms_bt_key",
    "idx_forms_title_key",
    "idx_forms_stem_key",
    "idx_forms_form_key",
    "idx_forms_formi_key",
    "idx_bt_entries_norm_key",
    "idx_bt_variants_spelling",
    "idx_lexicon_entries_norm_pos",
    "idx_lexicon_forms_entry_id",
    "idx_lexicon_search_keys_key_text",
    "idx_lexicon_search_keys_entry_id",
    "idx_lexicon_search_keys_form_id",
    "idx_lexicon_search_keys_dedupe",
}


def _table_names(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
        """
    ).fetchall()
    return {str(row[0]) for row in rows}


def _index_names(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'index'
        ORDER BY name
        """
    ).fetchall()
    return {str(row[0]) for row in rows}


def _fresh_canonical_db(tmp_path: Path) -> Path:
    settings = Settings(app_data_dir=tmp_path / "app-data")
    runtime = DatabaseStartupRuntime(
        settings=settings,
        interactive=False,
    )

    runtime.ensure_ready()

    return runtime.db_path


def test_fresh_canonical_db_has_expected_tables(tmp_path: Path) -> None:
    db_path = _fresh_canonical_db(tmp_path)

    with sqlite3.connect(db_path) as connection:
        table_names = _table_names(connection)

    assert table_names >= EXPECTED_CANONICAL_TABLES


def test_fresh_canonical_db_lexicon_forms_include_paradigm(
    tmp_path: Path,
) -> None:
    db_path = _fresh_canonical_db(tmp_path)

    with sqlite3.connect(db_path) as connection:
        columns = {
            str(row[1])
            for row in connection.execute("PRAGMA table_info(lexicon_forms)").fetchall()
        }

    assert "paradigm" in columns


def test_fresh_canonical_db_has_expected_indexes(tmp_path: Path) -> None:
    db_path = _fresh_canonical_db(tmp_path)

    with sqlite3.connect(db_path) as connection:
        index_names = _index_names(connection)

    assert index_names >= EXPECTED_CANONICAL_INDEXES


def test_create_lexicon_tables_creates_expected_tables(
    lexicon_db_path: Path,
) -> None:
    with sqlite3.connect(lexicon_db_path) as connection:
        table_names = _table_names(connection)

    assert set(LEXICON_TABLE_NAMES).issubset(table_names)


def test_create_lexicon_tables_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "lexicon-idempotent.sqlite3"
    with sqlite3.connect(db_path) as connection:
        create_lexicon_tables(connection)
        first_tables = _table_names(connection)
        create_lexicon_tables(connection)
        second_tables = _table_names(connection)

    assert first_tables == second_tables


def test_apply_lexicon_schema_adds_paradigm_to_legacy_forms_table(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "legacy-lexicon.sqlite3"
    with sqlite3.connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE lexicon_forms (
                form_id INTEGER PRIMARY KEY,
                entry_id INTEGER,
                bt TEXT NOT NULL,
                title TEXT NOT NULL,
                stem TEXT NOT NULL,
                form TEXT NOT NULL,
                formi TEXT NOT NULL,
                wordclass TEXT NOT NULL,
                function TEXT NOT NULL,
                probability TEXT NOT NULL,
                class1 TEXT NOT NULL,
                class2 TEXT NOT NULL,
                class3 TEXT NOT NULL
            );
            """
        )
        connection.commit()

    with sqlite3.connect(db_path) as connection:
        migrate_lexicon_schema(connection)
        connection.commit()
        columns = {
            str(row[1])
            for row in connection.execute("PRAGMA table_info(lexicon_forms)").fetchall()
        }

    assert "paradigm" in columns


def test_lexicon_entries_round_trip(lexicon_db_connection: sqlite3.Connection) -> None:
    connection = lexicon_db_connection
    connection.execute(
        """
        INSERT INTO lexicon_entries (
            entry_id,
            norm_key,
            pos,
            headword,
            summary_sense,
            etymology,
            variants_json,
            genders_json,
            senses_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            42,
            "cyning",
            "noun",
            "cyning",
            "a king",
            "from PGmc *kuningaz",
            '["cyning"]',
            '["masculine"]',
            '[{"sense_label": "I", "gloss_en": "a king"}]',
        ),
    )
    connection.commit()

    row = connection.execute(
        """
        SELECT entry_id, norm_key, pos, headword, summary_sense
        FROM lexicon_entries
        WHERE entry_id = ?
        """,
        (42,),
    ).fetchone()

    assert row is not None
    assert row["entry_id"] == 42
    assert row["norm_key"] == "cyning"
    assert row["pos"] == "noun"
    assert row["headword"] == "cyning"
    assert row["summary_sense"] == "a king"


def test_lexicon_search_keys_round_trip(
    lexicon_db_connection: sqlite3.Connection,
) -> None:
    connection = lexicon_db_connection
    connection.execute(
        """
        INSERT INTO lexicon_entries (
            entry_id,
            norm_key,
            pos,
            headword,
            summary_sense,
            etymology,
            variants_json,
            genders_json,
            senses_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (7, "cyning", "noun", "cyning", "a king", "", "[]", "[]", "[]"),
    )
    connection.execute(
        """
        INSERT INTO lexicon_search_keys (
            key_text,
            key_kind,
            rank_tier,
            entry_id,
            form_id,
            display_text
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("cyning", KEY_KIND_LEMMA, RANK_TIER_EXACT_ENTRY, 7, None, "cyning"),
    )
    connection.commit()

    row = connection.execute(
        """
        SELECT key_text, key_kind, rank_tier, entry_id, display_text
        FROM lexicon_search_keys
        WHERE key_text = ?
        """,
        ("cyning",),
    ).fetchone()

    assert row is not None
    assert row["key_kind"] == KEY_KIND_LEMMA
    assert row["rank_tier"] == RANK_TIER_EXACT_ENTRY
    assert row["entry_id"] == 7
    assert row["display_text"] == "cyning"


def test_orphan_form_without_entry_is_allowed(
    lexicon_db_connection: sqlite3.Connection,
) -> None:
    connection = lexicon_db_connection
    connection.execute(
        """
        INSERT INTO lexicon_forms (
            form_id,
            entry_id,
            bt,
            title,
            stem,
            form,
            formi,
            wordclass,
            function,
            probability,
            class1,
            class2,
            class3,
            paradigm
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            99,
            None,
            "unlinked",
            "unlinked",
            "unlinked",
            "unlinked-form",
            "unlinked-form",
            "verb",
            "present",
            "1",
            "",
            "",
            "",
            "",
        ),
    )
    connection.commit()

    row = connection.execute(
        """
        SELECT form_id, entry_id, form
        FROM lexicon_forms
        WHERE form_id = ?
        """,
        (99,),
    ).fetchone()
    entry_count = connection.execute(
        "SELECT COUNT(*) FROM lexicon_entries"
    ).fetchone()[0]

    assert row is not None
    assert row["entry_id"] is None
    assert row["form"] == "unlinked-form"
    assert entry_count == 0


def test_seeded_lexicon_db_fixture_has_orphan_and_entry(
    seeded_lexicon_db: Path,
) -> None:
    with sqlite3.connect(seeded_lexicon_db) as connection:
        entry_count = connection.execute(
            "SELECT COUNT(*) FROM lexicon_entries"
        ).fetchone()[0]
        linked_forms = connection.execute(
            "SELECT COUNT(*) FROM lexicon_forms WHERE entry_id IS NOT NULL"
        ).fetchone()[0]
        orphan_forms = connection.execute(
            "SELECT COUNT(*) FROM lexicon_forms WHERE entry_id IS NULL"
        ).fetchone()[0]
        schema_version = connection.execute(
            """
            SELECT value
            FROM lexicon_build_meta
            WHERE key = ?
            """,
            (META_KEY_SCHEMA_VERSION,),
        ).fetchone()[0]
        search_key_count = connection.execute(
            "SELECT COUNT(*) FROM lexicon_search_keys"
        ).fetchone()[0]

    assert entry_count == 1
    assert linked_forms == 1
    assert orphan_forms == 1
    assert int(schema_version) == SCHEMA_VERSION
    assert search_key_count == 2


@pytest.mark.parametrize("table_name", LEXICON_TABLE_NAMES)
def test_each_lexicon_table_exists_after_create(
    tmp_path: Path,
    table_name: str,
) -> None:
    db_path = tmp_path / f"{table_name}.sqlite3"
    with sqlite3.connect(db_path) as connection:
        create_lexicon_tables(connection)
        exists = connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table' AND name = ?
            """,
            (table_name,),
        ).fetchone()

    assert exists is not None
