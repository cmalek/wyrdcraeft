"""Helpers for building morphology SQLite databases used in lexicon tests."""

from __future__ import annotations

import io
from pathlib import Path

from wyrdcraeft.db.runtime import upgrade_canonical_db
from wyrdcraeft.services.dictionary.pipeline import BTIndexPipeline
from wyrdcraeft.services.dictionary.sinks import BTSqliteSink
from wyrdcraeft.services.morphology.generation.common import print_one_form
from wyrdcraeft.services.morphology.generation.sinks import (
    CompositeSink,
    SqliteIndexSink,
    TsvParitySink,
)
from wyrdcraeft.services.morphology.session import GeneratorSession

_SAMPLE_LINES = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "dictionary"
    / "sample_lines.txt"
)


def seed_forms(db_path: Path) -> None:
    """
    Write minimal ``forms`` rows into a morphology SQLite database.

    Args:
        db_path: Target morphology database path.

    Side Effects:
        Creates or updates ``forms`` rows in ``db_path``.

    """
    session = GeneratorSession()
    output = io.StringIO()
    sqlite_sink = SqliteIndexSink(db_path)
    sink = CompositeSink(TsvParitySink(output), sqlite_sink)
    try:
        print_one_form(
            session,
            {
                "BT": "abbad",
                "title": "abbad",
                "stem": "abbad",
                "form": "abbades",
                "formParts": "0-abbad-0",
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
        print_one_form(
            session,
            {
                "BT": "orphan-lemma",
                "title": "orphan-lemma",
                "stem": "orphan-lemma",
                "form": "orphan-form",
                "formParts": "0-orphan-lemma-0",
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


def seed_bt_tables(db_path: Path) -> None:
    """
    Attach minimal Bosworth-Toller ``bt_*`` tables to a morphology database.

    Args:
        db_path: Target morphology database path.

    Side Effects:
        Creates or refreshes ``bt_*`` rows in ``db_path`` without altering
        existing ``forms`` rows.

    """
    sink = BTSqliteSink(db_path, attach_mode=True)
    try:
        BTIndexPipeline().run(_SAMPLE_LINES, sink)
    finally:
        sink.close()


def make_lexicon_source_db(db_path: Path) -> Path:
    """
    Build a morphology database seeded with ``forms`` and ``bt_*`` tables.

    Args:
        db_path: Target database file path.

    Returns:
        ``db_path`` after seeding source tables for lexicon rebuild tests.

    Side Effects:
        Applies Alembic migrations, then writes morphology and dictionary source
        rows into ``db_path``.

    """
    upgrade_canonical_db(db_path)
    seed_forms(db_path)
    seed_bt_tables(db_path)
    return db_path
