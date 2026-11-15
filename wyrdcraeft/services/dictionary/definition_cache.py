"""Read and fill the cached definition line on ``bt_entries``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from wyrdcraeft.models.dictionary import sense_path_sort_key
from wyrdcraeft.services.dictionary.definition_line import definition_line

if TYPE_CHECKING:
    from sqlalchemy.engine import Connection


class DefinitionLineCache:
    """
    Lazily computed, stored definition line per dictionary entry (ADR 0028).

    ``bt_entries.definition_line_cache`` is null until the line is computed.
    SQLite triggers null it again whenever the entry's senses, variants or
    part of speech change, so a stored value is always current.

    After the first failed write (for example ``database is locked`` while a
    build holds the database) the instance stops writing, so later misses do
    not each wait out SQLite's busy timeout; they still compute and return
    the line. A new instance writes again.

    A cache built with ``write=False`` never writes: ``get`` returns the
    stored line or computes it, so a caller on the UI thread never waits on
    a database lock. Browse's row-fill worker is the only writer.

    Args:
        connection: Connection to the canonical database.

    Keyword Args:
        write: Whether ``get`` stores computed lines (``True``) or only reads
            and computes them (``False``).

    """

    #: Connection to the canonical database.
    _connection: Connection
    #: Whether cache writes are still attempted; cleared after a failed write.
    _writes_enabled: bool

    def __init__(self, connection: Connection, *, write: bool = True) -> None:
        """
        Bind the cache to one long-lived connection.

        Args:
            connection: Connection to the canonical database.

        Keyword Args:
            write: Whether ``get`` stores computed lines.

        """
        #: Connection to the canonical database.
        self._connection = connection
        #: Whether cache writes are still attempted; cleared after a failed write.
        self._writes_enabled = write

    def peek(self, entry_id: int) -> str | None:
        """
        Return the stored line without computing it.

        Args:
            entry_id: Dictionary entry identifier.

        Returns:
            Stored definition line, or ``None`` when not yet computed or the
            entry does not exist.

        """
        value = self._connection.execute(
            text("SELECT definition_line_cache FROM bt_entries WHERE id = :entry_id"),
            {"entry_id": entry_id},
        ).scalar_one_or_none()
        return None if value is None else str(value)

    def get(self, entry_id: int) -> str:
        """
        Return the entry's definition line, computing and storing it on a miss.

        Side Effects:
            On a miss, writes the computed line to
            ``bt_entries.definition_line_cache`` and commits, unless the
            cache was built with ``write=False``. A failed write (for example
            a locked database) is rolled back and ignored.

        Args:
            entry_id: Dictionary entry identifier.

        Returns:
            Definition line; an empty string when the entry has no senses or
            does not exist.

        """
        row = self._connection.execute(
            text(
                """
                SELECT e.definition_line_cache AS cached_line, p.code AS pos
                FROM bt_entries e
                JOIN parts_of_speech p ON p.id = e.pos_id
                WHERE e.id = :entry_id
                """
            ),
            {"entry_id": entry_id},
        ).mappings().first()
        if row is None:
            return ""
        if row["cached_line"] is not None:
            return str(row["cached_line"])
        line = definition_line(str(row["pos"]), self._glosses(entry_id))
        self._store(entry_id, line)
        return line

    def _glosses(self, entry_id: int) -> list[str]:
        """
        Load the entry's English glosses in sense order.

        Args:
            entry_id: Dictionary entry identifier.

        Returns:
            Stripped glosses in the details view's order: by ``sense_path``,
            then ``order_index`` and ``id``.

        """
        rows = self._connection.execute(
            text(
                """
                SELECT gloss_en, sense_path FROM bt_senses
                WHERE entry_id = :entry_id
                ORDER BY order_index ASC, id ASC
                """
            ),
            {"entry_id": entry_id},
        ).mappings().all()
        ordered = sorted(
            rows, key=lambda row: sense_path_sort_key(str(row["sense_path"]))
        )
        return [str(row["gloss_en"]).strip() for row in ordered]

    def _store(self, entry_id: int, line: str) -> None:
        """
        Write one computed line to the cache column and commit.

        Side Effects:
            Updates ``bt_entries.definition_line_cache`` and commits; on an
            ``OperationalError`` rolls back, leaves the column null and
            disables further writes on this instance.

        Args:
            entry_id: Dictionary entry identifier.
            line: Computed definition line to store.

        """
        if not self._writes_enabled:
            return
        try:
            self._connection.execute(
                text(
                    "UPDATE bt_entries SET definition_line_cache = :line "
                    "WHERE id = :entry_id"
                ),
                {"line": line, "entry_id": entry_id},
            )
            self._connection.commit()
        except OperationalError:
            self._connection.rollback()
            self._writes_enabled = False
