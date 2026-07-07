"""Parity-preserving sinks for morphology form emission and indexing."""

from __future__ import annotations

import re
import sqlite3
from time import perf_counter
from typing import TYPE_CHECKING, Protocol, cast

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path
    from typing import TextIO

    from sqlalchemy.engine import Connection, Engine

    from ..contracts import FormWriter
    from ..session import GeneratorSession

from sqlalchemy import Table, insert, text

from wyrdcraeft.db.base import Base
from wyrdcraeft.db.runtime import create_engine
from wyrdcraeft.models.morphology import FormRow
from wyrdcraeft.models.sqlalchemy import Form
from wyrdcraeft.services.dictionary.join_index_loader import (
    load_normalized_title_join_index,
)
from wyrdcraeft.services.dictionary.normalized_title_join import (
    NormalizedTitleJoinIndex,
)
from wyrdcraeft.services.markup import normalize_morphology_title
from wyrdcraeft.services.morphology.catalog.pos_seed import (
    ensure_inflection_codes,
    ensure_parts_of_speech,
)

from ..text_utils import OENormalizer
from .form_fk_resolver import FormFkResolver, _load_morph_class_ids

#: Default row buffer size before flushing one bulk SQLite insert.
_SQLITE_BATCH_SIZE = 25000


class FormSink(Protocol):
    """Sink contract for finalized emitted form rows."""

    def emit_rows(self, rows: list[FormRow]) -> None:
        """
        Consume finalized form rows in emitted order.

        Note:
            Emitted row semantics follow morphology contracts from
            ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
            In plain terms, this receives finalized rows for any Part of Speech.

        Args:
            rows: Finalized rows in emitted order.

        """


def _build_form_rows_from_form_data(
    *, counter: int, form_data: dict[str, str]
) -> list[FormRow]:
    """
    Build parity form rows from legacy ``form_data`` without writing output.

    Note:
        Row construction follows grammar-driven outputs from
        ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
        In plain terms, this materializes inflected rows for any Part of Speech.

    Keyword Args:
        counter: Row counter value for the primary emitted row.
        form_data: Legacy mutable row payload.

    Returns:
        One or two finalized rows in emitted order.

    """
    form_val = form_data["form"]
    formi = OENormalizer.normalize_output(form_val)
    prob = form_data.get("probability")
    prob_str = str(prob) if prob is not None else ""

    rows: list[FormRow] = [
        _row_from_form_data(
            counter=counter,
            formi=formi,
            form_data=form_data,
            probability=prob_str,
        )
    ]

    reduced_formi, duplicate_count = re.subn(
        f"({OENormalizer.CONSONANT_REGEX.pattern})\\1", r"\1", formi
    )
    if duplicate_count > 0:
        prob_val = int(str(prob)) if prob not in {None, ""} else 0
        rows.append(
            _row_from_form_data(
                counter=counter + 1,
                formi=reduced_formi,
                form_data=form_data,
                probability=str(prob_val + 1),
            )
        )
    return rows


def _row_from_form_data(
    *, counter: int, formi: str, form_data: dict[str, str], probability: str
) -> FormRow:
    """
    Materialize one finalized output row from legacy ``form_data`` fields.

    Note:
        Field mapping keeps parity with grammar-driven outputs from
        ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
        In plain terms, this packages one inflected row for its Part of Speech.

    Keyword Args:
        counter: Row counter value for this emitted row.
        formi: Normalized ``formi`` value for this emitted row.
        form_data: Legacy mutable row payload.
        probability: String probability field to persist.

    Returns:
        Finalized form row compatible with emitted TSV columns.

    """
    return FormRow(
        counter=str(counter),
        formi=formi,
        BT=form_data["BT"],
        title=form_data["title"],
        normalized_title=normalize_morphology_title(form_data["title"]),
        stem=form_data["stem"],
        form=form_data["form"],
        formParts=form_data.get("formParts", ""),
        var=form_data["var"],
        probability=probability,
        function=form_data["function"],
        wright=form_data["wright"],
        paradigm=form_data["paradigm"],
        paraID=form_data["paraID"],
        wordclass=form_data["wordclass"],
        class1=form_data["class1"],
        class2=form_data["class2"],
        class3=form_data["class3"],
        comment=form_data["comment"],
    )


class TsvParitySink:
    """
    Parity sink that reproduces legacy ``print_one_form`` row behavior.

    Args:
        output: Output stream receiving tab-separated rows.

    """

    #: Underlying output stream for TSV serialization.
    _output: TextIO | FormWriter

    def __init__(self, output: TextIO | FormWriter) -> None:
        """
        Initialize a parity TSV sink.

        Note:
            TSV row layout is aligned with outputs derived from
            ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
            In plain terms, this prepares the writer for all Parts of Speech.

        Args:
            output: Output stream receiving tab-separated rows.

        """
        #: Underlying output stream for TSV serialization.
        self._output = output

    def emit_form_data(
        self, session: GeneratorSession, form_data: dict[str, str]
    ) -> list[FormRow]:
        """
        Emit parity rows from legacy ``form_data`` and update session counter.

        Args:
            session: Active generation session tracking output counter.
            form_data: Legacy mutable row payload.

        Returns:
            Emitted rows in output order.

        """
        rows = _build_form_rows_from_form_data(
            counter=session.output_counter,
            form_data=form_data,
        )
        self.emit_rows(rows)
        session.output_counter += len(rows)
        return rows

    def emit_rows(self, rows: list[FormRow]) -> None:
        """
        Serialize finalized rows to the output stream.

        Args:
            rows: Finalized rows in emitted order.

        """
        for row in rows:
            line = (
                f"{row.counter}\t"
                f"{row.formi}\t"
                f"{row.BT}\t"
                f"{row.title}\t"
                f"{row.stem}\t"
                f"{row.form}\t"
                f"{row.formParts}\t"
                f"{row.var}\t"
                f"{row.probability}\t"
                f"{row.function}\t"
                f"{row.wright}\t"
                f"{row.paradigm}\t"
                f"{row.paraID}\t"
                f"{row.wordclass}\t"
                f"{row.class1}\t"
                f"{row.class2}\t"
                f"{row.class3}\t"
                f"{row.comment}\n"
            )
            self._output.write(line)


class SqliteIndexSink:
    """
    SQLAlchemy sink that persists emitted rows for ad-hoc morphology lookup.

    Args:
        db_path: Path to SQLite database file.
        batch_size: Number of buffered rows before one bulk insert transaction.
        sqlite_flush_observer: Optional callback receiving ``(seconds, row_count)``.

    """

    #: SQLAlchemy engine bound to the canonical database.
    _engine: Engine
    #: Buffered rows waiting for the next bulk insert.
    _pending_rows: list[FormRow]
    #: Maximum buffered rows before flushing to SQLite.
    _batch_size: int
    #: Optional callback invoked after each SQLite bulk flush completes.
    _sqlite_flush_observer: Callable[[float, int], None] | None

    def __init__(
        self,
        db_path: Path,
        *,
        batch_size: int = _SQLITE_BATCH_SIZE,
        sqlite_flush_observer: Callable[[float, int], None] | None = None,
    ) -> None:
        """
        Initialize a SQLAlchemy sink for emitted morphology rows.

        Note:
            Index schema preserves searchable morphology rows grounded in
            ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
            In plain terms, this stores forms for every Part of Speech.

        Args:
            db_path: Path to SQLite database file.

        Keyword Args:
            batch_size: Number of buffered rows before one bulk insert transaction.
            sqlite_flush_observer: Optional callback receiving ``(seconds, row_count)``.

        Side Effects:
            Ensures the canonical ``forms`` table exists in ``db_path`` for
            scratch/test databases that were not created via Alembic.

        """
        if batch_size < 1:
            msg = "batch_size must be positive"
            raise ValueError(msg)
        #: SQLAlchemy engine bound to the canonical database.
        self._engine = create_engine(db_path)
        #: Buffered rows waiting for the next bulk insert.
        self._pending_rows = []
        #: Maximum buffered rows before flushing to SQLite.
        self._batch_size = batch_size
        #: Optional callback invoked after each SQLite bulk flush completes.
        self._sqlite_flush_observer = sqlite_flush_observer
        self._init_schema()
        self._configure_bulk_load()

    def _init_schema(self) -> None:
        """Ensure the canonical ``forms`` table and its indexes exist."""
        with self._engine.begin() as connection:
            Base.metadata.create_all(
                bind=connection,
                tables=[cast("Table", Form.__table__)],
                checkfirst=True,
            )

    def _configure_bulk_load(self) -> None:
        """
        Tune SQLite for bulk morphology index writes.

        Side Effects:
            Sets WAL mode and relaxed durability PRAGMAs on the build connection.

        """
        with self._engine.begin() as connection:
            connection.execute(text("PRAGMA journal_mode=WAL"))
            connection.execute(text("PRAGMA synchronous=OFF"))
            connection.execute(text("PRAGMA temp_store=MEMORY"))
            connection.execute(text("PRAGMA cache_size=-64000"))

    @staticmethod
    def _normalize_key(value: str) -> str:
        """
        Normalize a lookup token for deterministic morphology queries.

        Args:
            value: Raw lookup token.

        Returns:
            Canonicalized lookup key.

        """
        return OENormalizer.normalize_output(value).casefold()

    @staticmethod
    def _sqlite_connection(connection: Connection) -> sqlite3.Connection:
        """
        Unwrap SQLAlchemy's DB-API connection to the underlying SQLite driver.

        Args:
            connection: Active SQLAlchemy connection bound to the canonical database.

        Returns:
            Raw ``sqlite3.Connection`` used by ``FormFkResolver`` preload helpers.

        """
        dbapi_connection = connection.connection
        driver_connection = getattr(dbapi_connection, "driver_connection", None)
        if driver_connection is not None:
            return cast("sqlite3.Connection", driver_connection)
        return cast("sqlite3.Connection", dbapi_connection)

    def _build_fk_resolver(
        self, sqlite_connection: sqlite3.Connection
    ) -> FormFkResolver:
        """
        Build one resolver per flush using canonical reference data when present.

        Note:
            Scratch databases that only contain ``forms`` still resolve POS and
            inflection-code ids from seeded reference tables while leaving
            absent dictionary or lemma-assignment tables as empty lookups per
            ``data/Ondej_Tich_40-54-1.pdf``. Part-of-speech scope: ``cross-PoS``.

        Args:
            sqlite_connection: Raw SQLite connection for the active flush
                transaction.

        Returns:
            Resolver with preloaded lookup maps for this flush batch.

        """
        pos_map = ensure_parts_of_speech(sqlite_connection)
        inflection_map = ensure_inflection_codes(sqlite_connection, pos_map)
        try:
            morph_class_ids = _load_morph_class_ids(sqlite_connection)
        except sqlite3.OperationalError:
            morph_class_ids = {}
        try:
            join_index = load_normalized_title_join_index(sqlite_connection)
        except sqlite3.OperationalError:
            join_index = NormalizedTitleJoinIndex.from_entry_variant_rows([], [])
        return FormFkResolver(
            join_index=join_index,
            inflection_code_ids=inflection_map,
            morph_class_ids=morph_class_ids,
            pos_ids_by_code=pos_map,
        )

    def _rows_to_payload(
        self,
        rows: list[FormRow],
        resolver: FormFkResolver,
    ) -> list[dict[str, object]]:
        """
        Convert finalized form rows into SQLAlchemy Core insert payloads.

        Note:
            Foreign-key fields are resolved from canonical reference tables per
            ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
            In plain terms, unresolved lookups insert ``NULL`` for every
            Part of Speech rather than inventing placeholder ids. Legacy
            string fields (``function``, ``wright``, ``paradigm``, ``paraID``,
            ``wordclass``, ``class1``-``class3``) are read from ``row`` to
            resolve foreign keys but are not persisted; those columns were
            dropped from ``forms`` in Phase D.

        Args:
            rows: Finalized rows in emitted order.
            resolver: Preloaded resolver built once per flush batch.

        Returns:
            Insert payloads for the canonical ``forms`` table.

        """
        return [
            {
                "counter": int(row.counter),
                "formi": row.formi,
                "BT": row.BT,
                "title": row.title,
                "normalized_title": row.normalized_title,
                "stem": row.stem,
                "form": row.form,
                "formParts": row.formParts,
                "var": row.var,
                "probability": row.probability,
                "comment": row.comment,
                "bt_key": self._normalize_key(row.BT),
                "title_key": self._normalize_key(row.title),
                "stem_key": self._normalize_key(row.stem),
                "form_key": self._normalize_key(row.form),
                "formi_key": self._normalize_key(row.formi),
                "wordclass_id": resolver.resolve_wordclass_id(row.wordclass),
                "inflection_code_id": resolver.resolve_inflection_code_id(
                    row.function,
                    row.wordclass,
                ),
                "morph_class_id": resolver.resolve_morph_class_id(
                    row.normalized_title,
                    row.wordclass,
                    row.function,
                ),
                "entry_id": resolver.resolve_entry_id(
                    row.normalized_title,
                    row.wordclass,
                ),
            }
            for row in rows
        ]

    def _flush_rows(self, rows: list[FormRow]) -> None:
        """
        Insert one finalized row batch into the canonical database.

        Args:
            rows: Finalized rows in emitted order.

        Side Effects:
            Inserts rows into ``forms`` inside one explicit transaction using
            a single Core bulk insert rather than one ORM object per row.

        """
        if not rows:
            return
        started_at = perf_counter()
        with self._engine.begin() as connection:
            sqlite_connection = self._sqlite_connection(connection)
            resolver = self._build_fk_resolver(sqlite_connection)
            payload = self._rows_to_payload(rows, resolver)
            connection.execute(insert(Form), payload)
        if self._sqlite_flush_observer is not None:
            self._sqlite_flush_observer(perf_counter() - started_at, len(rows))

    def emit_form_data(
        self, session: GeneratorSession, form_data: dict[str, str]
    ) -> list[FormRow]:
        """
        Build parity rows from legacy ``form_data`` and persist them to SQLite.

        Args:
            session: Active generation session tracking output counter.
            form_data: Legacy mutable row payload.

        Returns:
            Emitted rows in output order.

        """
        rows = _build_form_rows_from_form_data(
            counter=session.output_counter,
            form_data=form_data,
        )
        self.emit_rows(rows)
        session.output_counter += len(rows)
        return rows

    def emit_rows(self, rows: list[FormRow]) -> None:
        """
        Buffer finalized rows and flush full batches to SQLite.

        Args:
            rows: Finalized rows in emitted order.

        Side Effects:
            Appends rows to an in-memory buffer and bulk-inserts when the buffer
            reaches ``batch_size``.

        """
        if not rows:
            return
        self._pending_rows.extend(rows)
        while len(self._pending_rows) >= self._batch_size:
            batch = self._pending_rows[: self._batch_size]
            del self._pending_rows[: self._batch_size]
            self._flush_rows(batch)

    def close(self) -> None:
        """
        Flush buffered rows and dispose the SQLAlchemy engine.

        Side Effects:
            Inserts any remaining buffered rows before closing the engine.

        """
        if self._pending_rows:
            self._flush_rows(self._pending_rows)
            self._pending_rows.clear()
        self._engine.dispose()


class CompositeSink:
    """
    Fan-out sink that builds parity rows once and emits to multiple row sinks.

    Args:
        primary_sink: Sink that builds rows and updates the session counter.
        row_sinks: Additional sinks receiving finalized emitted rows.

    """

    #: Primary sink that builds rows and updates the session counter.
    _primary_sink: TsvParitySink
    #: Additional sinks receiving finalized row payloads.
    _row_sinks: tuple[FormSink, ...]

    def __init__(self, primary_sink: TsvParitySink, *row_sinks: FormSink) -> None:
        """
        Initialize a fan-out sink for parity and projection outputs.

        Note:
            Fan-out keeps parity rows consistent with grammar references
            ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
            In plain terms, this sends each Part-of-Speech row to all outputs.

        Args:
            primary_sink: Sink that builds rows and updates the session counter.
            row_sinks: Additional sinks receiving finalized emitted rows.

        """
        #: Primary sink that builds rows and updates the session counter.
        self._primary_sink = primary_sink
        #: Additional sinks receiving finalized row payloads.
        self._row_sinks = row_sinks

    def emit_form_data(
        self, session: GeneratorSession, form_data: dict[str, str]
    ) -> list[FormRow]:
        """
        Emit parity rows and fan them out to all attached row sinks.

        Args:
            session: Active generation session tracking output counter.
            form_data: Legacy mutable row payload.

        Returns:
            Emitted rows in output order.

        """
        rows = self._primary_sink.emit_form_data(session, form_data)
        for sink in self._row_sinks:
            sink.emit_rows(rows)
        return rows
