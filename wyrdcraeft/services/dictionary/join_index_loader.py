"""Shared loader for normalized-title dictionary join indexes."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from sqlalchemy import text
from sqlalchemy.engine import Connection

from wyrdcraeft.services.dictionary.normalized_title_join import (
    NormalizedTitleJoinIndex,
)
from wyrdcraeft.services.dictionary.query import _bt_pos_from_code

if TYPE_CHECKING:
    import sqlite3


def _fetch_rows(
    connection: Connection | sqlite3.Connection,
    sql: str,
) -> list[tuple[object, object, object]]:
    """
    Fetch three-column join rows from SQLAlchemy or SQLite connections.

    Args:
        connection: Open canonical database connection.
        sql: Query text returning ``(entry_id, normalized_title, pos_code)`` rows.

    Returns:
        Materialized row tuples usable by ``NormalizedTitleJoinIndex`` loaders.

    """
    if isinstance(connection, Connection):
        rows = connection.execute(text(sql)).fetchall()
    else:
        rows = connection.execute(sql).fetchall()
    return [(row[0], row[1], row[2]) for row in rows]


def load_normalized_title_join_index(
    connection: Connection | sqlite3.Connection,
) -> NormalizedTitleJoinIndex:
    """
    Build a dictionary join index from canonical ``bt_entries`` and variants.

    Args:
        connection: Open canonical database connection.

    Returns:
        Preloaded join index using Bosworth-Toller POS labels.

    """
    entry_rows = _fetch_rows(
        connection,
        """
        SELECT bt_entries.id, bt_entries.normalized_title, parts_of_speech.code
        FROM bt_entries
        JOIN parts_of_speech ON parts_of_speech.id = bt_entries.pos_id
        """,
    )
    variant_rows = _fetch_rows(
        connection,
        """
        SELECT bt_variants.entry_id, bt_variants.normalized_title, parts_of_speech.code
        FROM bt_variants
        JOIN bt_entries ON bt_entries.id = bt_variants.entry_id
        JOIN parts_of_speech ON parts_of_speech.id = bt_entries.pos_id
        WHERE trim(coalesce(bt_variants.normalized_title, '')) != ''
        """,
    )

    def _bt_pos_label(code: str) -> str:
        return _bt_pos_from_code(code).value

    return NormalizedTitleJoinIndex.from_entry_variant_rows(
        [
            (
                int(cast("int | str", entry_id)),
                str(normalized_title),
                _bt_pos_label(str(pos_code)),
            )
            for entry_id, normalized_title, pos_code in entry_rows
        ],
        [
            (
                int(cast("int | str", entry_id)),
                str(normalized_title),
                _bt_pos_label(str(pos_code)),
            )
            for entry_id, normalized_title, pos_code in variant_rows
        ],
    )
