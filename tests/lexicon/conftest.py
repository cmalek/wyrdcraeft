"""Shared fixtures for lexicon schema and service tests."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

import pytest

from wyrdcraeft.cli import (
    cli as _cli,  # noqa: F401 - ensure CLI loaded before generation imports
)
from wyrdcraeft.db.runtime import upgrade_canonical_db
from wyrdcraeft.services.lexicon.schema import (
    KEY_KIND_FORM,
    KEY_KIND_LEMMA,
    META_KEY_BUILT_AT,
    RANK_TIER_EXACT_ENTRY,
    RANK_TIER_ORPHAN,
)

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path


@pytest.fixture
def lexicon_db_path(tmp_path: Path) -> Path:
    """
    Temporary SQLite database with canonical source and search-index tables.

    Returns:
        Path to a database file with lexicon schema applied.

    """
    db_path = tmp_path / "lexicon-test.sqlite3"
    upgrade_canonical_db(db_path)
    return db_path


@pytest.fixture
def lexicon_db_connection(
    lexicon_db_path: Path,
) -> Generator[sqlite3.Connection]:
    """
    Open SQLite connection to a lexicon test database.

    Yields:
        Connection with ``row_factory`` set to ``sqlite3.Row``.

    """
    connection = sqlite3.connect(lexicon_db_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def _noun_pos_id(connection: sqlite3.Connection) -> int:
    """Return the seeded ``noun`` part-of-speech row id."""
    row = connection.execute(
        "SELECT id FROM parts_of_speech WHERE code = 'noun'",
    ).fetchone()
    assert row is not None
    return int(row[0])


def _inflection_code_id(connection: sqlite3.Connection, *, code: str) -> int:
    """Return a seeded inflection-code row id."""
    row = connection.execute(
        "SELECT id FROM inflection_codes WHERE code = ?",
        (code,),
    ).fetchone()
    assert row is not None
    return int(row[0])


@pytest.fixture
def seeded_lexicon_db(lexicon_db_path: Path) -> Path:
    """
    Lexicon database seeded with one entry, one linked form, and one orphan form.

    Returns:
        Path to the seeded database file.

    """
    with sqlite3.connect(lexicon_db_path) as connection:
        noun_pos_id = _noun_pos_id(connection)
        genitive_code_id = _inflection_code_id(
            connection,
            code="genitive singular",
        )
        nominative_code_id = _inflection_code_id(
            connection,
            code="nominative singular",
        )
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
                1,
                "abbod",
                "abbod",
                "abbod",
                noun_pos_id,
                "[]",
                "",
                "[]",
                "[]",
            ),
        )
        connection.execute(
            """
            INSERT INTO bt_senses (
                id,
                entry_id,
                sense_label,
                gloss_en,
                order_index
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (1, 1, "I", "an abbot", 0),
        )
        connection.executemany(
            """
            INSERT INTO forms (
                id, counter, formi, BT, title, normalized_title, stem, form,
                formParts, var, probability, comment,
                bt_key, title_key, stem_key, form_key, formi_key,
                entry_id, wordclass_id, inflection_code_id
            ) VALUES (
                ?, 0, ?, ?, ?, ?, ?, ?, ?, '0', '1', '',
                ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            [
                (
                    10,
                    "abbodes",
                    "abbod",
                    "abbod",
                    "abbod",
                    "abbod",
                    "abbodes",
                    "0-abbod-0",
                    "abbod",
                    "abbod",
                    "abbod",
                    "abbodes",
                    "abbodes",
                    1,
                    noun_pos_id,
                    genitive_code_id,
                ),
                (
                    11,
                    "orphan-form",
                    "orphan-lemma",
                    "orphan-lemma",
                    "orphan-lemma",
                    "orphan-lemma",
                    "orphan-form",
                    "0-orphan-lemma-0",
                    "orphan-lemma",
                    "orphan-lemma",
                    "orphan-lemma",
                    "orphan-form",
                    "orphan-form",
                    None,
                    noun_pos_id,
                    nominative_code_id,
                ),
            ],
        )
        connection.executemany(
            """
            INSERT INTO search_keys (
                key_text,
                key_kind,
                rank_tier,
                entry_id,
                form_id,
                display_text
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                ("abbod", KEY_KIND_LEMMA, RANK_TIER_EXACT_ENTRY, 1, None, "abbod"),
                (
                    "orphan-form",
                    KEY_KIND_FORM,
                    RANK_TIER_ORPHAN,
                    None,
                    11,
                    "orphan-form",
                ),
            ],
        )
        connection.executemany(
            """
            INSERT INTO search_build_meta (key, value) VALUES (?, ?)
            """,
            [
                (META_KEY_BUILT_AT, "2026-06-28T00:00:00Z"),
            ],
        )
        connection.commit()
    return lexicon_db_path
