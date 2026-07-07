"""Shared dictionary POS inference from morphology forms."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, cast

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError

from wyrdcraeft.models.reference import PartOfSpeech
from wyrdcraeft.models.sqlalchemy import BTEntry, Form
from wyrdcraeft.services.morphology.catalog.pos import pos_id_from_bt_pos

from .wordclass_pos import infer_bt_pos_from_wordclasses

if TYPE_CHECKING:
    import sqlite3

    from sqlalchemy.engine import Connection

#: Optional callback receiving stage progress state.
PosInferenceProgress = Callable[[int, int, int, str], None]
#: Optional callback receiving warning text and current item.
PosInferenceWarningSink = Callable[[str, str], None]
#: Optional callback that raises when cancellation is requested.
PosInferenceCancelCheck = Callable[[str], None]


def _sqlite_connection(connection: Connection) -> sqlite3.Connection:
    """
    Unwrap one SQLAlchemy connection to the underlying SQLite driver.

    Args:
        connection: Open SQLAlchemy connection bound to canonical SQLite.

    Returns:
        Raw ``sqlite3.Connection`` used by POS resolver helpers.

    """
    dbapi_connection = connection.connection
    driver_connection = getattr(dbapi_connection, "driver_connection", None)
    if driver_connection is not None:
        return cast("sqlite3.Connection", driver_connection)
    return cast("sqlite3.Connection", dbapi_connection)


def _unknown_pos_id(connection: Connection) -> int:
    """
    Resolve the seeded ``unknown`` part-of-speech identifier.

    Args:
        connection: Open SQLAlchemy connection bound to canonical SQLite.

    Returns:
        ``parts_of_speech.id`` for the ``unknown`` code row.

    """
    return int(
        connection.execute(
            select(PartOfSpeech.id).where(PartOfSpeech.code == "unknown"),
        ).scalar_one(),
    )


class DictionaryPosInferer:
    """
    Fill missing dictionary POS values from unambiguous morphology wordclasses.

    Note:
        This inference joins morphology forms back to dictionary lemmas using the
        normalized-title data model described by ``data/OldEnglishGrammar.pdf``
        and ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, it looks at the
        wordclasses already present on forms for a lemma and promotes a single
        unambiguous result onto the dictionary entry. Part-of-speech scope:
        ``cross-PoS``.

    """

    def infer_missing_pos(
        self,
        connection: Connection,
        *,
        progress: PosInferenceProgress | None = None,
        warning_sink: PosInferenceWarningSink | None = None,
        cancel_check: PosInferenceCancelCheck | None = None,
    ) -> int:
        """
        Update unknown dictionary POS rows from morphology forms when unambiguous.

        Args:
            connection: Open SQLAlchemy connection containing source tables.

        Keyword Args:
            progress: Optional callback receiving
                ``(completed, total, updated, current_item)``.
            warning_sink: Optional callback receiving warning text plus the active
                normalized title when a uniqueness conflict blocks an update.
            cancel_check: Optional callback that may raise when cooperative
                cancellation has been requested.

        Returns:
            Number of ``bt_entries`` rows updated with inferred POS labels.

        Side Effects:
            Updates ``bt_entries.pos_id`` for entries with unknown POS and one
            clear morphology wordclass, skipping rows that already have a POS
            sibling or would violate the homograph uniqueness constraint.

        """
        unknown_pos_id = _unknown_pos_id(connection)
        rows = connection.execute(
            select(BTEntry.id, BTEntry.normalized_title)
            .where(BTEntry.pos_id == unknown_pos_id)
            .order_by(BTEntry.id.asc())
        ).fetchall()
        total = len(rows) or 1

        updated = 0
        for index, row in enumerate(rows, start=1):
            normalized_title = str(row.normalized_title)
            if cancel_check is not None:
                cancel_check(normalized_title)
            wordclass_rows = connection.execute(
                select(func.lower(func.trim(PartOfSpeech.code)).label("wordclass"))
                .select_from(Form)
                .join(PartOfSpeech, PartOfSpeech.id == Form.wordclass_id)
                .where(Form.normalized_title == normalized_title)
                .distinct()
            ).fetchall()
            inferred_pos = infer_bt_pos_from_wordclasses(
                {str(wordclass_row.wordclass) for wordclass_row in wordclass_rows}
            )
            if inferred_pos is not None and self._try_set_inferred_pos(
                connection,
                entry_id=int(row.id),
                normalized_title=normalized_title,
                inferred_pos=inferred_pos,
                warning_sink=warning_sink,
            ):
                updated += 1
            if progress is not None:
                progress(index, total, updated, normalized_title)

        return updated

    def _try_set_inferred_pos(
        self,
        connection: Connection,
        *,
        entry_id: int,
        normalized_title: str,
        inferred_pos: str,
        warning_sink: PosInferenceWarningSink | None,
    ) -> bool:
        """
        Attempt one inferred POS update, skipping duplicate and homograph rows.

        Args:
            connection: Open SQLAlchemy connection containing ``bt_entries``.

        Keyword Args:
            entry_id: ``bt_entries.id`` of the row being updated.
            normalized_title: Macron-preserving headword used for sibling checks.
            inferred_pos: BT part-of-speech code inferred from morphology.
            warning_sink: Optional callback receiving warning text plus current
                item when an update is skipped.

        Returns:
            ``True`` when the update committed; ``False`` when skipped.

        """
        target_pos_id = pos_id_from_bt_pos(_sqlite_connection(connection), inferred_pos)
        pos_sibling = connection.execute(
            select(BTEntry.id)
            .where(
                BTEntry.normalized_title == normalized_title,
                BTEntry.pos_id == target_pos_id,
                BTEntry.id != entry_id,
            )
            .limit(1)
        ).first()
        if pos_sibling is not None:
            return False

        savepoint = connection.begin_nested()
        try:
            connection.execute(
                update(BTEntry)
                .where(BTEntry.id == entry_id)
                .values(pos_id=target_pos_id)
            )
        except IntegrityError:
            savepoint.rollback()
            if warning_sink is not None:
                warning_sink(
                    (
                        "skipped pos inference: another homograph already uses "
                        "this norm_key with the inferred part of speech"
                    ),
                    normalized_title,
                )
            return False
        savepoint.commit()
        return True
