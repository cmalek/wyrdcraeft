"""Tests for lexicon read-model schema helpers."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

import pytest

from wyrdcraeft.db.runtime import DatabaseStartupRuntime, upgrade_canonical_db
from wyrdcraeft.settings import Settings

if TYPE_CHECKING:
    from pathlib import Path


DROPPED_SEARCH_TABLE_NAMES = frozenset({"search_keys", "search_build_meta"})

EXPECTED_CANONICAL_TABLES = {
    "alembic_version",
    "forms",
    "bt_entries",
    "bt_senses",
    "bt_variants",
    "bt_edit_log",
}

EXPECTED_CANONICAL_INDEXES = {
    "idx_forms_bt_key",
    "idx_forms_title_key",
    "idx_forms_stem_key",
    "idx_forms_form_key",
    "idx_forms_formi_key",
    "idx_forms_normalized_title",
    "idx_forms_wordclass_id",
    "idx_forms_inflection_code_id",
    "idx_forms_morph_class_id",
    "idx_forms_entry_id",
    "idx_bt_entries_norm_key",
    "idx_bt_entries_normalized_title",
    "idx_bt_variants_spelling",
    "idx_bt_variants_normalized_title",
}

EXPECTED_FORMS_COLUMNS = {
    "id",
    "counter",
    "formi",
    "BT",
    "title",
    "normalized_title",
    "stem",
    "form",
    "formParts",
    "var",
    "probability",
    "comment",
    "bt_key",
    "title_key",
    "stem_key",
    "form_key",
    "formi_key",
    "wordclass_id",
    "inflection_code_id",
    "morph_class_id",
    "entry_id",
}

DROPPED_FORMS_LEGACY_COLUMNS = {
    "wright",
    "paradigm",
    "paraID",
    "wordclass",
    "function",
    "class1",
    "class2",
    "class3",
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


def _forms_column_names(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute("PRAGMA table_info(forms)").fetchall()
    return {str(row[1]) for row in rows}


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


def _unknown_pos_id(connection: sqlite3.Connection) -> int:
    """Return the seeded ``unknown`` part-of-speech row id."""
    row = connection.execute(
        "SELECT id FROM parts_of_speech WHERE code = 'unknown'",
    ).fetchone()
    assert row is not None
    return int(row[0])


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
    assert set(DROPPED_SEARCH_TABLE_NAMES).isdisjoint(table_names)
    assert "lexicon_entries" not in table_names
    assert "lexicon_forms" not in table_names
    assert "lexicon_search_keys" not in table_names
    assert "lexicon_build_meta" not in table_names


def test_fresh_canonical_db_has_expected_indexes(tmp_path: Path) -> None:
    db_path = _fresh_canonical_db(tmp_path)

    with sqlite3.connect(db_path) as connection:
        index_names = _index_names(connection)

    assert index_names >= EXPECTED_CANONICAL_INDEXES


def test_fresh_canonical_db_has_expected_forms_columns(tmp_path: Path) -> None:
    db_path = _fresh_canonical_db(tmp_path)

    with sqlite3.connect(db_path) as connection:
        forms_columns = _forms_column_names(connection)

    assert forms_columns == EXPECTED_FORMS_COLUMNS
    assert DROPPED_FORMS_LEGACY_COLUMNS.isdisjoint(forms_columns)


def test_alembic_upgrade_drops_legacy_search_tables(
    lexicon_db_path: Path,
) -> None:
    with sqlite3.connect(lexicon_db_path) as connection:
        table_names = _table_names(connection)

    assert set(DROPPED_SEARCH_TABLE_NAMES).isdisjoint(table_names)


def test_alembic_upgrade_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "lexicon-idempotent.sqlite3"
    upgrade_canonical_db(db_path)
    with sqlite3.connect(db_path) as connection:
        first_tables = _table_names(connection)

    upgrade_canonical_db(db_path)
    with sqlite3.connect(db_path) as connection:
        second_tables = _table_names(connection)

    assert first_tables == second_tables


def test_bt_entries_round_trip(lexicon_db_connection: sqlite3.Connection) -> None:
    connection = lexicon_db_connection
    pos_id = _unknown_pos_id(connection)
    connection.execute(
        """
        INSERT INTO bt_entries (
            id,
            norm_key,
            headword,
            normalized_title,
            pos_id,
            genders_json,
            etymology,
            see_also_json,
            source_line_nos_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            42,
            "cyning",
            "cyning",
            "cyning",
            pos_id,
            '["masculine"]',
            "from PGmc *kuningaz",
            "[]",
            "[1]",
        ),
    )
    connection.commit()

    row = connection.execute(
        """
        SELECT id, norm_key, headword
        FROM bt_entries
        WHERE id = ?
        """,
        (42,),
    ).fetchone()

    assert row is not None
    assert row["id"] == 42
    assert row["norm_key"] == "cyning"
    assert row["headword"] == "cyning"


def test_orphan_form_without_entry_is_allowed(
    lexicon_db_connection: sqlite3.Connection,
) -> None:
    connection = lexicon_db_connection
    connection.execute(
        """
        INSERT INTO forms (
            counter, formi, BT, title, normalized_title, stem, form,
            formParts, var, probability, comment,
            bt_key, title_key, stem_key, form_key, formi_key
        ) VALUES (
            99, 'unlinked-form', 'unlinked', 'unlinked', 'unlinked', 'unlinked',
            'unlinked-form', '0-unlinked-0', '0', '1', '',
            'unlinked', 'unlinked', 'unlinked', 'unlinked-form', 'unlinked-form'
        )
        """
    )
    connection.commit()

    row = connection.execute(
        """
        SELECT id, entry_id, form
        FROM forms
        WHERE form = ?
        """,
        ("unlinked-form",),
    ).fetchone()
    entry_count = connection.execute(
        "SELECT COUNT(*) FROM bt_entries"
    ).fetchone()[0]

    assert row is not None
    assert row["entry_id"] is None
    assert row["form"] == "unlinked-form"
    assert entry_count == 0


@pytest.mark.parametrize("table_name", sorted(DROPPED_SEARCH_TABLE_NAMES))
def test_each_search_table_is_absent_after_alembic_upgrade(
    tmp_path: Path,
    table_name: str,
) -> None:
    db_path = tmp_path / f"{table_name}.sqlite3"
    upgrade_canonical_db(db_path)
    with sqlite3.connect(db_path) as connection:
        exists = connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table' AND name = ?
            """,
            (table_name,),
        ).fetchone()

    assert exists is None
