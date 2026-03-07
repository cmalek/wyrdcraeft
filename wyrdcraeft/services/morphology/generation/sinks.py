"""Parity-preserving sinks for morphology form emission and indexing."""

from __future__ import annotations

import re
import sqlite3
from typing import TYPE_CHECKING, Protocol

from wyrdcraeft.models.morphology import FormRow

from ..text_utils import OENormalizer

if TYPE_CHECKING:
    from pathlib import Path
    from typing import TextIO

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
    SQLite sink that persists emitted rows for ad-hoc morphology lookup.

    Args:
        db_path: Path to SQLite database file.

    """

    #: Active SQLite connection.
    _connection: sqlite3.Connection

    def __init__(self, db_path: Path) -> None:
        """
        Initialize a SQLite sink for emitted morphology rows.

        Note:
            Index schema preserves searchable morphology rows grounded in
            ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
            In plain terms, this stores forms for every Part of Speech.

        Args:
            db_path: Path to SQLite database file.

        """
        #: Active SQLite connection.
        self._connection = sqlite3.connect(str(db_path))
        self._connection.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        """Create index schema and lookup indexes when missing."""
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS forms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                counter INTEGER NOT NULL,
                formi TEXT NOT NULL,
                BT TEXT NOT NULL,
                title TEXT NOT NULL,
                stem TEXT NOT NULL,
                form TEXT NOT NULL,
                formParts TEXT NOT NULL,
                var TEXT NOT NULL,
                probability TEXT NOT NULL,
                function TEXT NOT NULL,
                wright TEXT NOT NULL,
                paradigm TEXT NOT NULL,
                paraID TEXT NOT NULL,
                wordclass TEXT NOT NULL,
                class1 TEXT NOT NULL,
                class2 TEXT NOT NULL,
                class3 TEXT NOT NULL,
                comment TEXT NOT NULL,
                bt_key TEXT NOT NULL,
                title_key TEXT NOT NULL,
                stem_key TEXT NOT NULL,
                form_key TEXT NOT NULL,
                formi_key TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_forms_bt_key ON forms(bt_key);
            CREATE INDEX IF NOT EXISTS idx_forms_title_key ON forms(title_key);
            CREATE INDEX IF NOT EXISTS idx_forms_stem_key ON forms(stem_key);
            CREATE INDEX IF NOT EXISTS idx_forms_form_key ON forms(form_key);
            CREATE INDEX IF NOT EXISTS idx_forms_formi_key ON forms(formi_key);
            """
        )
        self._connection.commit()

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
        Persist finalized rows to SQLite, preserving emitted order.

        Args:
            rows: Finalized rows in emitted order.

        """
        payload = [
            (
                int(row.counter),
                row.formi,
                row.BT,
                row.title,
                row.stem,
                row.form,
                row.formParts,
                row.var,
                row.probability,
                row.function,
                row.wright,
                row.paradigm,
                row.paraID,
                row.wordclass,
                row.class1,
                row.class2,
                row.class3,
                row.comment,
                self._normalize_key(row.BT),
                self._normalize_key(row.title),
                self._normalize_key(row.stem),
                self._normalize_key(row.form),
                self._normalize_key(row.formi),
            )
            for row in rows
        ]
        self._connection.executemany(
            """
            INSERT INTO forms (
                counter,
                formi,
                BT,
                title,
                stem,
                form,
                formParts,
                var,
                probability,
                function,
                wright,
                paradigm,
                paraID,
                wordclass,
                class1,
                class2,
                class3,
                comment,
                bt_key,
                title_key,
                stem_key,
                form_key,
                formi_key
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            payload,
        )
        self._connection.commit()

    def close(self) -> None:
        """Close the SQLite connection."""
        self._connection.close()


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
