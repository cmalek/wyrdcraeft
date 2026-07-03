"""Parity-preserving sinks for morphology form emission and indexing."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Protocol, cast

from sqlalchemy import Table, insert

from wyrdcraeft.db.base import Base
from wyrdcraeft.db.runtime import create_engine
from wyrdcraeft.models.morphology import FormRow
from wyrdcraeft.models.sqlalchemy import Form

from ..text_utils import OENormalizer

if TYPE_CHECKING:
    from pathlib import Path
    from typing import TextIO

    from sqlalchemy.engine import Engine

    from ..contracts import FormWriter
    from ..session import GeneratorSession


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
        form_val = form_data["form"]
        formi = OENormalizer.normalize_output(form_val)
        prob = form_data.get("probability")
        prob_str = str(prob) if prob is not None else ""

        rows: list[FormRow] = [
            _row_from_form_data(
                counter=session.output_counter,
                formi=formi,
                form_data=form_data,
                probability=prob_str,
            )
        ]

        reduced_formi, count = re.subn(
            f"({OENormalizer.CONSONANT_REGEX.pattern})\\1", r"\1", formi
        )
        if count > 0:
            prob_val = int(str(prob)) if prob not in {None, ""} else 0
            rows.append(
                _row_from_form_data(
                    counter=session.output_counter + 1,
                    formi=reduced_formi,
                    form_data=form_data,
                    probability=str(prob_val + 1),
                )
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

    """

    #: SQLAlchemy engine bound to the canonical database.
    _engine: Engine

    def __init__(self, db_path: Path) -> None:
        """
        Initialize a SQLAlchemy sink for emitted morphology rows.

        Note:
            Index schema preserves searchable morphology rows grounded in
            ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
            In plain terms, this stores forms for every Part of Speech.

        Args:
            db_path: Path to SQLite database file.

        Side Effects:
            Ensures the canonical ``forms`` table exists in ``db_path`` for
            scratch/test databases that were not created via Alembic.

        """
        #: SQLAlchemy engine bound to the canonical database.
        self._engine = create_engine(db_path)
        self._init_schema()

    def _init_schema(self) -> None:
        """Ensure the canonical ``forms`` table and its indexes exist."""
        with self._engine.begin() as connection:
            Base.metadata.create_all(
                bind=connection,
                tables=[cast("Table", Form.__table__)],
                checkfirst=True,
            )

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

    def emit_rows(self, rows: list[FormRow]) -> None:
        """
        Bulk-insert finalized rows into the canonical database.

        Args:
            rows: Finalized rows in emitted order.

        Side Effects:
            Inserts rows into ``forms`` inside one explicit transaction using
            a single Core bulk insert rather than one ORM object per row.

        """
        if not rows:
            return
        payload = [
            {
                "counter": int(row.counter),
                "formi": row.formi,
                "BT": row.BT,
                "title": row.title,
                "stem": row.stem,
                "form": row.form,
                "formParts": row.formParts,
                "var": row.var,
                "probability": row.probability,
                "function": row.function,
                "wright": row.wright,
                "paradigm": row.paradigm,
                "paraID": row.paraID,
                "wordclass": row.wordclass,
                "class1": row.class1,
                "class2": row.class2,
                "class3": row.class3,
                "comment": row.comment,
                "bt_key": self._normalize_key(row.BT),
                "title_key": self._normalize_key(row.title),
                "stem_key": self._normalize_key(row.stem),
                "form_key": self._normalize_key(row.form),
                "formi_key": self._normalize_key(row.formi),
            }
            for row in rows
        ]
        with self._engine.begin() as connection:
            connection.execute(insert(Form), payload)

    def close(self) -> None:
        """Dispose the SQLAlchemy engine for this sink."""
        self._engine.dispose()


class CompositeSink:
    """
    Fan-out sink that emits parity rows to TSV and additional row sinks.

    Args:
        tsv_sink: Primary parity sink writing canonical TSV output.
        row_sinks: Additional sinks receiving finalized emitted rows.

    """

    #: Primary parity sink writing canonical output.
    _tsv_sink: TsvParitySink
    #: Additional sinks receiving finalized row payloads.
    _row_sinks: tuple[FormSink, ...]

    def __init__(self, tsv_sink: TsvParitySink, *row_sinks: FormSink) -> None:
        """
        Initialize a fan-out sink for parity and projection outputs.

        Note:
            Fan-out keeps parity rows consistent with grammar references
            ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
            In plain terms, this sends each Part-of-Speech row to all outputs.

        Args:
            tsv_sink: Primary parity sink writing canonical TSV output.
            row_sinks: Additional sinks receiving finalized emitted rows.

        """
        #: Primary parity sink writing canonical output.
        self._tsv_sink = tsv_sink
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
        rows = self._tsv_sink.emit_form_data(session, form_data)
        for sink in self._row_sinks:
            sink.emit_rows(rows)
        return rows
