"""Relink morphology ``forms.entry_id`` values after dictionary rebuilds."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from wyrdcraeft.models.dictionary import BTPos
from wyrdcraeft.services.dictionary.join_index_loader import (
    load_normalized_title_join_index,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from wyrdcraeft.services.dictionary.normalized_title_join import (
        NormalizedTitleJoinIndex,
    )


#: Morphology wordclass values mapped to Bosworth-Toller POS labels.
_WORDCLASS_TO_BT_POS: dict[str, str] = {
    "noun": BTPos.NOUN.value,
    "verb": BTPos.VERB.value,
    "adjective": BTPos.ADJ.value,
    "adverb": BTPos.ADV.value,
    "numeral": BTPos.NUMERAL.value,
    "pronoun": BTPos.PRON.value,
    "preposition": BTPos.PREP.value,
    "conjunction": BTPos.CONJ.value,
    "interjection": BTPos.INTERJ.value,
    "indeclinable": BTPos.INDECL.value,
}


class FormsEntryRelinker:
    """
    Recompute every ``forms.entry_id`` FK against the current dictionary rows.

    This service must run after every ``bt_entries`` wipe/reload because
    Bosworth-Toller primary keys are rebuilt and previous ``forms.entry_id``
    values can become stale or point at removed entries.

    Note:
        Join behavior follows the shared normalized-title policy used for
        morphology lookup in ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, the relinker resolves
        each form's lemma title plus part of speech against current
        ``bt_entries`` / ``bt_variants`` rows and leaves ``entry_id`` null when
        the match policy yields no unique answer. Part-of-speech scope:
        ``cross-PoS``.

    Args:
        connection: SQLAlchemy connection or engine bound to the canonical
            database.

    """

    #: SQLAlchemy connection resource used for relink queries and updates.
    _connection: Connection | Engine
    #: Preloaded normalized-title join index from current dictionary rows.
    _join_index: NormalizedTitleJoinIndex

    def __init__(self, connection: Connection | Engine) -> None:
        """
        Initialize the relinker from an existing SQLAlchemy bind.

        Args:
            connection: SQLAlchemy connection or engine bound to the canonical
                database.

        """
        #: SQLAlchemy connection resource used for relink queries and updates.
        self._connection = connection
        with self._begin_connection() as active_connection:
            #: Preloaded normalized-title join index from current dictionary rows.
            self._join_index = load_normalized_title_join_index(active_connection)

    @contextmanager
    def _begin_connection(self) -> Iterator[Connection]:
        """
        Yield an active SQLAlchemy connection for one relink operation.

        Returns:
            Context manager yielding a connection. Engine-backed calls own their
            transaction; connection-backed calls reuse the caller's transaction.

        """
        if isinstance(self._connection, Connection):
            yield self._connection
            return
        with self._connection.begin() as connection:
            yield connection

    def clear_all_entry_ids(self) -> int:
        """
        Clear every populated ``forms.entry_id`` before dictionary replacement.

        Returns:
            Number of form rows whose non-null ``entry_id`` was cleared.

        Side Effects:
            Updates ``forms.entry_id`` to ``NULL`` for all populated rows.

        """
        with self._begin_connection() as connection:
            result = connection.execute(
                text("UPDATE forms SET entry_id = NULL WHERE entry_id IS NOT NULL")
            )
        return int(result.rowcount or 0)

    def relink_all(
        self,
        *,
        batch_size: int = 25000,
        progress: Callable[[int, int], None] | None = None,
    ) -> int:
        """
        Recompute ``forms.entry_id`` for every stored morphology form row.

        Keyword Args:
            batch_size: Maximum number of rows to resolve and update per batch.
            progress: Optional callback receiving ``(processed_rows, total_rows)``
                after each batch commit.

        Returns:
            Number of form rows processed by the relink pass.

        Raises:
            ValueError: ``batch_size`` is less than 1.

        Side Effects:
            Updates ``forms.entry_id`` in-place using the current dictionary join
            policy.

        """
        if batch_size < 1:
            msg = "batch_size must be positive"
            raise ValueError(msg)

        with self._begin_connection() as connection:
            total_rows = int(
                connection.execute(text("SELECT COUNT(*) FROM forms")).scalar_one()
            )
            if total_rows == 0:
                return 0

            rows = connection.execute(
                text(
                    """
                    SELECT
                        forms.id,
                        forms.normalized_title,
                        parts_of_speech.code AS wordclass
                    FROM forms
                    LEFT JOIN parts_of_speech ON parts_of_speech.id = forms.wordclass_id
                    ORDER BY forms.id
                    """
                )
            )
            update_stmt = text(
                "UPDATE forms SET entry_id = :entry_id WHERE id = :id"
            )
            processed_rows = 0

            while True:
                batch = rows.fetchmany(batch_size)
                if not batch:
                    break

                updates = [
                    {
                        "id": int(row.id),
                        "entry_id": self._resolve_entry_id(
                            str(row.normalized_title),
                            str(row.wordclass or ""),
                        ),
                    }
                    for row in batch
                ]
                connection.execute(update_stmt, updates)
                processed_rows += len(updates)
                if progress is not None:
                    progress(processed_rows, total_rows)

        return processed_rows

    def _resolve_entry_id(self, normalized_title: str, wordclass: str) -> int | None:
        """
        Resolve one dictionary ``bt_entries.id`` for one stored form row.

        Args:
            normalized_title: Macron-preserving normalized lemma title.
            wordclass: Canonical form part-of-speech code used to narrow the join.

        Returns:
            Matching dictionary entry id when the join policy yields one
            unambiguous result, otherwise ``None``.

        """
        bt_pos = _WORDCLASS_TO_BT_POS.get(wordclass.strip().lower())
        return self._join_index.resolve_one(normalized_title, bt_pos or None)
