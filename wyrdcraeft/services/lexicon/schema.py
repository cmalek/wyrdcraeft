"""SQLAlchemy-managed schema helpers for lexicon browse read-model tables."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Final, cast

from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session

from wyrdcraeft.db.runtime import create_engine as create_sqlalchemy_engine
from wyrdcraeft.models.sqlalchemy import (
    LexiconBuildMeta,
    LexiconEntry,
    LexiconForm,
    LexiconSearchKey,
)

#: Lexicon dictionary-entry table storing one row per real Bosworth-Toller entry.
TABLE_LEXICON_ENTRIES: Final = "lexicon_entries"
#: Lexicon morphology projection table; rows may exist without a dictionary entry.
TABLE_LEXICON_FORMS: Final = "lexicon_forms"
#: Lexicon normalized search keys used for unified lookup and ranking.
TABLE_LEXICON_SEARCH_KEYS: Final = "lexicon_search_keys"
#: Lexicon build metadata key/value store.
TABLE_LEXICON_BUILD_META: Final = "lexicon_build_meta"

#: Ordered lexicon table names managed by rebuild workflows.
LEXICON_TABLE_NAMES: Final = (
    TABLE_LEXICON_ENTRIES,
    TABLE_LEXICON_FORMS,
    TABLE_LEXICON_SEARCH_KEYS,
    TABLE_LEXICON_BUILD_META,
)

#: Current lexicon read-model schema version written to ``lexicon_build_meta``.
SCHEMA_VERSION: Final = 1

#: Metadata key storing the active lexicon schema version.
META_KEY_SCHEMA_VERSION: Final = "schema_version"
#: Metadata key storing the ISO-8601 UTC timestamp of the last rebuild.
META_KEY_BUILT_AT: Final = "built_at"
#: Metadata key storing the source ``forms`` row count at rebuild time.
META_KEY_FORMS_SOURCE_COUNT: Final = "forms_source_count"
#: Metadata key storing the source ``bt_entries`` row count at rebuild time.
META_KEY_BT_ENTRIES_SOURCE_COUNT: Final = "bt_entries_source_count"

#: Search-key kind for dictionary headword matches.
KEY_KIND_LEMMA: Final = "lemma"
#: Search-key kind for dictionary variant spelling matches.
KEY_KIND_VARIANT: Final = "variant"
#: Search-key kind for morphology lemma/stem matches.
KEY_KIND_STEM: Final = "stem"
#: Search-key kind for inflected morphology form matches.
KEY_KIND_FORM: Final = "form"

#: Highest-priority rank tier for exact dictionary lemma or variant hits.
RANK_TIER_EXACT_ENTRY: Final = 1
#: Rank tier for morphology lemma or stem hits joined to a dictionary entry.
RANK_TIER_MORPH_LEMMA_STEM: Final = 2
#: Rank tier for morphology form hits joined to a dictionary entry.
RANK_TIER_MORPH_FORM: Final = 3
#: Rank tier for morphology-only hits with no dictionary entry join.
RANK_TIER_ORPHAN: Final = 4


def _sqlite_connection_path(connection: sqlite3.Connection) -> Path:
    """
    Resolve the file-backed SQLite path from an open ``sqlite3`` connection.

    Args:
        connection: Open SQLite connection.

    Returns:
        Filesystem path backing ``connection``.

    Raises:
        ValueError: The connection is not backed by a file path.

    """
    row = connection.execute("PRAGMA database_list").fetchone()
    if row is None or not str(row[2]).strip():
        msg = "lexicon schema helpers require a file-backed SQLite database"
        raise ValueError(msg)
    return Path(str(row[2])).expanduser().resolve()


def _connectable_from_target(
    target: Engine | Connection | Session | sqlite3.Connection,
) -> tuple[Engine | Connection, Engine | None]:
    """
    Resolve a SQLAlchemy connectable from one supported schema target.

    Args:
        target: SQLAlchemy or ``sqlite3`` object pointing at the target database.

    Returns:
        Tuple of ``(connectable, owned_engine)`` where ``owned_engine`` should be
        disposed by the caller when not ``None``.

    Raises:
        TypeError: ``target`` is not a supported schema target.

    """
    if isinstance(target, (Engine, Connection)):
        return target, None
    if isinstance(target, Session):
        return target.get_bind(), None
    if isinstance(target, sqlite3.Connection):
        engine = create_sqlalchemy_engine(_sqlite_connection_path(target))
        return engine, engine
    msg = f"unsupported lexicon schema target: {type(target)!r}"
    raise TypeError(msg)


def _create_lexicon_tables(connectable: Engine | Connection) -> None:
    """
    Create the lexicon read-model tables on one SQLAlchemy connectable.

    Args:
        connectable: SQLAlchemy engine or connection for the target database.

    Side Effects:
        Creates missing ``lexicon_*`` tables and indexes using declarative metadata.

    """
    cast("Any", LexiconEntry.__table__).create(bind=connectable, checkfirst=True)
    cast("Any", LexiconForm.__table__).create(bind=connectable, checkfirst=True)
    cast("Any", LexiconSearchKey.__table__).create(bind=connectable, checkfirst=True)
    cast("Any", LexiconBuildMeta.__table__).create(bind=connectable, checkfirst=True)


def create_lexicon_tables(
    target: Engine | Connection | Session | sqlite3.Connection,
) -> None:
    """
    Create lexicon read-model tables and indexes when missing.

    Args:
        target: SQLAlchemy or ``sqlite3`` handle for the target database.

    Side Effects:
        Creates missing ``lexicon_*`` tables and indexes using the canonical
        SQLAlchemy table definitions that Alembic manages.

    """
    connectable, owned_engine = _connectable_from_target(target)
    try:
        _create_lexicon_tables(connectable)
    finally:
        if owned_engine is not None:
            owned_engine.dispose()
