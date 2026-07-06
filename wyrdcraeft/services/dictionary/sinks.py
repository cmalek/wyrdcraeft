"""SQLAlchemy persistence for canonical Bosworth-Toller dictionary entries."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast

from sqlalchemy import Table, delete, insert
from sqlalchemy.orm import sessionmaker

from wyrdcraeft.db.base import Base
from wyrdcraeft.db.runtime import create_engine
from wyrdcraeft.models.sqlalchemy import BTEditLog, BTEntry, BTSense, BTVariant
from wyrdcraeft.services.dictionary.bt_spelling import BTSpellingNormalizer
from wyrdcraeft.services.markup import normalize_morphology_title
from wyrdcraeft.services.morphology.catalog.pos import pos_id_from_bt_pos
from wyrdcraeft.services.morphology.catalog.pos_seed import ensure_parts_of_speech

if TYPE_CHECKING:
    import sqlite3
    from pathlib import Path

    from sqlalchemy.engine import Engine
    from sqlalchemy.orm import Session

    from wyrdcraeft.models.dictionary import BTConsolidatedEntry, BTGender
    from wyrdcraeft.services.dictionary.editorial_merger import BTEditRecord


class BTSqliteSink:
    """
    SQLAlchemy sink that persists consolidated Bosworth-Toller dictionary entries.

    Dictionary writes reload the ``bt_*`` slice in place. Product attach-style
    usage preserves non-``bt_*`` tables inside an existing canonical database,
    while direct non-attach usage may bootstrap a scratch SQLite file for tests
    and pipeline-only callers.

    Args:
        db_path: Path to the canonical ``wyrdcraeft.sqlite3`` output.

    Keyword Args:
        attach_mode: Legacy compatibility flag retained for callers that still
            pass it. Standalone dictionary mode no longer exists.

    """

    #: Resolved SQLite database file path.
    db_path: Path
    #: Compatibility flag preserved for legacy callers.
    attach_mode: bool
    #: SQLAlchemy engine bound to the canonical database.
    _engine: Engine
    #: SQLAlchemy session factory for dictionary writes.
    _session_factory: sessionmaker[Session]
    #: Display spelling normalizer for variant macronization.
    _spelling_normalizer: BTSpellingNormalizer

    def __init__(self, db_path: Path, *, attach_mode: bool = False) -> None:
        """
        Initialize the dictionary sink for canonical or direct pipeline usage.

        Args:
            db_path: Path to the canonical SQLite database file.

        Keyword Args:
            attach_mode: Legacy compatibility flag. Standalone mode has been
                removed from product flows. When ``True``, the target database
                must already exist.

        Side Effects:
            Ensures ``bt_*`` tables exist in the target database and truncates
            prior ``bt_*`` contents before reload.

        Raises:
            FileNotFoundError: ``attach_mode`` was requested but the target
                database does not exist yet.

        """
        resolved = db_path.expanduser().resolve()
        resolved.parent.mkdir(parents=True, exist_ok=True)
        if attach_mode and not resolved.is_file():
            msg = f"Canonical database not found: {resolved}"
            raise FileNotFoundError(msg)
        #: Resolved SQLite database file path.
        self.db_path = resolved
        #: Compatibility flag preserved for legacy callers.
        self.attach_mode = attach_mode
        #: SQLAlchemy engine bound to the canonical database.
        self._engine = create_engine(resolved)
        #: SQLAlchemy session factory for dictionary writes.
        self._session_factory = sessionmaker(bind=self._engine, future=True)
        #: Display spelling normalizer for variant macronization.
        self._spelling_normalizer = BTSpellingNormalizer()
        self._init_schema()

    def _init_schema(self) -> None:
        """Ensure ``bt_*`` tables exist and clear prior dictionary rows."""
        with self._engine.begin() as connection:
            Base.metadata.create_all(
                bind=connection,
                tables=[
                    cast("Table", BTEntry.__table__),
                    cast("Table", BTSense.__table__),
                    cast("Table", BTVariant.__table__),
                    cast("Table", BTEditLog.__table__),
                ],
                checkfirst=True,
            )
            connection.execute(delete(BTSense))
            connection.execute(delete(BTVariant))
            connection.execute(delete(BTEditLog))
            connection.execute(delete(BTEntry))

    @staticmethod
    def _genders_json(genders: list[BTGender]) -> str:
        """
        Serialize noun gender markers to JSON.

        Args:
            genders: Parsed gender markers for one entry.

        Returns:
            JSON array of gender enum values.

        """
        return json.dumps([gender.value for gender in genders], ensure_ascii=False)

    @staticmethod
    def _sqlite_connection(session: Session) -> sqlite3.Connection:
        """
        Unwrap SQLAlchemy's DB-API connection to the underlying SQLite driver.

        Args:
            session: Active SQLAlchemy write session.

        Returns:
            Raw ``sqlite3.Connection`` used by POS seed and resolver helpers.

        """
        dbapi_connection = session.connection().connection
        driver_connection = getattr(dbapi_connection, "driver_connection", None)
        if driver_connection is not None:
            return cast("sqlite3.Connection", driver_connection)
        return cast("sqlite3.Connection", dbapi_connection)

    def write_entries(
        self,
        entries: list[BTConsolidatedEntry],
        edit_records: list[BTEditRecord],
    ) -> tuple[int, int, int, int]:
        """
        Persist consolidated entries, senses, variants, and edit audit rows.

        Args:
            entries: Consolidated dictionary records to store.
            edit_records: Editorial audit records from the merge pass.

        Returns:
            Tuple ``(entries_written, senses_written, variants_written,
            edit_log_written)``.

        Side Effects:
            Inserts rows into ``bt_entries``, ``bt_senses``, ``bt_variants``, and
            ``bt_edit_log`` inside one explicit transaction.

        """
        entries_written = 0
        sense_rows: list[dict[str, object]] = []
        variant_rows: list[dict[str, object]] = []

        with self._session_factory.begin() as session:
            sqlite_connection = self._sqlite_connection(session)
            ensure_parts_of_speech(sqlite_connection)
            for entry in entries:
                entry_row = BTEntry(
                    norm_key=entry.norm_key,
                    headword=entry.headword_macronized,
                    normalized_title=entry.normalized_title,
                    pos_id=pos_id_from_bt_pos(sqlite_connection, entry.pos.value),
                    genders_json=self._genders_json(entry.genders),
                    etymology=entry.etymology,
                    see_also_json=json.dumps(entry.see_also, ensure_ascii=False),
                    source_line_nos_json=json.dumps(entry.source_line_nos),
                )
                session.add(entry_row)
                session.flush()
                entry_id = int(entry_row.id)
                entries_written += 1

                sense_rows.extend(
                    {
                        "entry_id": entry_id,
                        "sense_label": sense.sense_label,
                        "gloss_en": sense.gloss_en,
                        "order_index": order_index,
                    }
                    for order_index, sense in enumerate(entry.senses)
                )
                variant_rows.extend(
                    {
                        "entry_id": entry_id,
                        "spelling_raw": variant_raw,
                        "spelling_macronized": macronized,
                        "normalized_title": normalize_morphology_title(macronized),
                    }
                    for variant_raw in entry.variants
                    for macronized in [
                        self._spelling_normalizer.normalize(variant_raw)
                    ]
                )

            if sense_rows:
                session.execute(insert(BTSense), sense_rows)
            if variant_rows:
                session.execute(insert(BTVariant), variant_rows)

            edit_rows = [
                {
                    "op": record.op.value,
                    "source_line_no": record.source_line_no,
                    "target_norm_key": record.target_norm_key,
                    "target_pos": record.target_pos.value,
                    "scope": record.scope,
                    "applied": int(record.applied),
                    "note": record.note,
                }
                for record in edit_records
            ]
            if edit_rows:
                session.execute(insert(BTEditLog), edit_rows)

        return (
            entries_written,
            len(sense_rows),
            len(variant_rows),
            len(edit_records),
        )

    def close(self) -> None:
        """Dispose the SQLAlchemy engine for this sink."""
        self._engine.dispose()
