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
    Temporary SQLite database with empty ``lexicon_*`` tables.

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


@pytest.fixture
def seeded_lexicon_db(lexicon_db_path: Path) -> Path:
    """
    Lexicon database seeded with one entry, one linked form, and one orphan form.

    Returns:
        Path to the seeded database file.

    """
    with sqlite3.connect(lexicon_db_path) as connection:
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
                1,
                "abbod",
                "noun",
                "abbod",
                "an abbot",
                "",
                '["abbod"]',
                "[]",
                '[{"sense_label": "I", "gloss_en": "an abbot"}]',
            ),
        )
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
                10,
                1,
                "abbod",
                "abbod",
                "abbod",
                "abbodes",
                "abbodes",
                "noun",
                "genitive singular",
                "1",
                "m",
                "",
                "",
                "",
            ),
        )
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
                11,
                None,
                "orphan-lemma",
                "orphan-lemma",
                "orphan-lemma",
                "orphan-form",
                "orphan-form",
                "noun",
                "nominative singular",
                "1",
                "m",
                "",
                "",
                "",
            ),
        )
        connection.executemany(
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
            INSERT INTO lexicon_build_meta (key, value) VALUES (?, ?)
            """,
            [
                (META_KEY_BUILT_AT, "2026-06-28T00:00:00Z"),
            ],
        )
        connection.commit()
    return lexicon_db_path
