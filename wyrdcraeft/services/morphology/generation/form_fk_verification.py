"""Verify normalized foreign keys on morphology ``forms`` rows after build."""

from __future__ import annotations

import random
import sqlite3
from dataclasses import dataclass
from typing import TYPE_CHECKING

from wyrdcraeft.services.morphology.generation.form_fk_resolver import FormFkResolver

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

#: Columns checked against ``FormFkResolver`` during sampled verification.
_FK_COLUMNS: tuple[str, ...] = (
    "wordclass_id",
    "inflection_code_id",
    "morph_class_id",
    "entry_id",
)
#: Maximum mismatch rows included in formatted CLI output.
_MAX_MISMATCH_LINES = 20


@dataclass(frozen=True)
class FormFkNullCounts:
    """
    Counts of NULL normalized foreign keys across all ``forms`` rows.

    Attributes:
        total_forms: Total rows in ``forms``.
        wordclass_id: Rows with NULL ``wordclass_id``.
        inflection_code_id: Rows with NULL ``inflection_code_id``.
        morph_class_id: Rows with NULL ``morph_class_id``.
        entry_id: Rows with NULL ``entry_id``.

    """

    #: Total rows in ``forms``.
    total_forms: int
    #: Rows with NULL ``wordclass_id``.
    wordclass_id: int
    #: Rows with NULL ``inflection_code_id``.
    inflection_code_id: int
    #: Rows with NULL ``morph_class_id``.
    morph_class_id: int
    #: Rows with NULL ``entry_id``.
    entry_id: int


@dataclass(frozen=True)
class FormFkMismatch:
    """
    One sampled form row whose stored FK does not match resolver output.

    Attributes:
        form_id: Canonical ``forms.id``.
        normalized_title: Macron-preserving normalized lemma title.
        wordclass: Legacy generator wordclass label.
        function: Legacy morphology function code.
        column: FK column that failed verification.
        stored: Value persisted on the form row.
        expected: Value recomputed by ``FormFkResolver``.

    """

    #: Canonical ``forms.id``.
    form_id: int
    #: Macron-preserving normalized lemma title.
    normalized_title: str
    #: Legacy generator wordclass label.
    wordclass: str
    #: Legacy morphology function code.
    function: str
    #: FK column that failed verification.
    column: str
    #: Value persisted on the form row.
    stored: int | None
    #: Value recomputed by ``FormFkResolver``.
    expected: int | None


@dataclass(frozen=True)
class FormFkVerificationReport:
    """
    Result of sampling ``forms`` rows and comparing FK columns to legacy strings.

    Attributes:
        null_fk_counts: NULL FK counts across the full ``forms`` table.
        sampled_forms: Number of rows checked in the sample.
        mismatches: FK values that disagree with ``FormFkResolver`` output.

    """

    #: NULL FK counts across the full ``forms`` table.
    null_fk_counts: FormFkNullCounts
    #: Number of rows checked in the sample.
    sampled_forms: int
    #: FK values that disagree with ``FormFkResolver`` output.
    mismatches: tuple[FormFkMismatch, ...]

    @property
    def ok(self) -> bool:
        """
        Report whether sampled FK values all match resolver output.

        Returns:
            ``True`` when the sample contains no FK mismatches.

        """
        return not self.mismatches


class FormFkVerificationService:
    """
    Sample ``forms`` rows and verify FK columns against legacy string fields.

    Note:
        Verification reuses ``FormFkResolver`` semantics from Wright's
        inflection taxonomy in ``data/OldEnglishGrammar.pdf`` and generator
        output conventions in ``data/Ondej_Tich_40-54-1.pdf``. NULL FK counts
        are expected for ambiguous dictionary joins, unassigned lemma classes,
        and unknown generator labels. Part-of-speech scope: ``cross-PoS``.

    Args:
        connection: Open canonical SQLite connection with ``forms`` populated.
        sample_size: Maximum number of form rows to compare.
        rng_seed: Seed for deterministic random sampling.

    """

    #: Open canonical SQLite connection with ``forms`` populated.
    _connection: sqlite3.Connection
    #: Maximum number of form rows to compare.
    _sample_size: int
    #: Seed for deterministic random sampling.
    _rng_seed: int

    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        sample_size: int = 500,
        rng_seed: int = 0,
    ) -> None:
        """
        Initialize verification settings and preload the FK resolver.

        Args:
            connection: Open canonical SQLite connection with ``forms``
                populated.

        Keyword Args:
            sample_size: Maximum number of form rows to compare.
            rng_seed: Seed for deterministic random sampling.

        """
        if sample_size < 1:
            msg = "sample_size must be at least 1"
            raise ValueError(msg)
        #: Open canonical SQLite connection with ``forms`` populated.
        self._connection = connection
        #: Maximum number of form rows to compare.
        self._sample_size = sample_size
        #: Seed for deterministic random sampling.
        self._rng_seed = rng_seed
        #: Preloaded FK resolver sharing the verification connection.
        self._resolver = FormFkResolver(connection=connection)

    @classmethod
    def from_db_path(
        cls,
        db_path: Path,
        *,
        sample_size: int = 500,
        rng_seed: int = 0,
    ) -> FormFkVerificationService:
        """
        Open one canonical database path and construct a verification service.

        Args:
            db_path: Path to ``wyrdcraeft.sqlite3`` with populated ``forms``.

        Keyword Args:
            sample_size: Maximum number of form rows to compare.
            rng_seed: Seed for deterministic random sampling.

        Returns:
            Verification service backed by a new SQLite connection.

        """
        connection = sqlite3.connect(db_path)
        return cls(connection, sample_size=sample_size, rng_seed=rng_seed)

    def verify(self) -> FormFkVerificationReport:
        """
        Compare sampled FK columns to resolver output and count NULL FKs.

        Returns:
            Verification report with full-table NULL counts and sample mismatches.

        """
        null_fk_counts = self._count_null_fks()
        sampled_rows = self._sample_form_rows(null_fk_counts.total_forms)
        mismatches = self._find_mismatches(sampled_rows)
        return FormFkVerificationReport(
            null_fk_counts=null_fk_counts,
            sampled_forms=len(sampled_rows),
            mismatches=tuple(mismatches),
        )

    def close(self) -> None:
        """Close the underlying SQLite connection when owned by this service."""
        self._connection.close()

    def _count_null_fks(self) -> FormFkNullCounts:
        """
        Count NULL FK values across the full ``forms`` table.

        Returns:
            Per-column NULL counts and total row count.

        """
        row = self._connection.execute(
            """
            SELECT
                COUNT(*) AS total_forms,
                SUM(CASE WHEN wordclass_id IS NULL THEN 1 ELSE 0 END),
                SUM(CASE WHEN inflection_code_id IS NULL THEN 1 ELSE 0 END),
                SUM(CASE WHEN morph_class_id IS NULL THEN 1 ELSE 0 END),
                SUM(CASE WHEN entry_id IS NULL THEN 1 ELSE 0 END)
            FROM forms
            """,
        ).fetchone()
        if row is None:
            return FormFkNullCounts(
                total_forms=0,
                wordclass_id=0,
                inflection_code_id=0,
                morph_class_id=0,
                entry_id=0,
            )
        return FormFkNullCounts(
            total_forms=int(row[0]),
            wordclass_id=int(row[1] or 0),
            inflection_code_id=int(row[2] or 0),
            morph_class_id=int(row[3] or 0),
            entry_id=int(row[4] or 0),
        )

    def _sample_form_rows(self, total_forms: int) -> list[sqlite3.Row]:
        """
        Select a deterministic random sample of form rows for FK comparison.

        Args:
            total_forms: Total number of rows currently stored in ``forms``.

        Returns:
            Sampled ``forms`` rows including legacy strings and FK columns.

        """
        if total_forms == 0:
            return []
        form_ids = [
            int(row[0])
            for row in self._connection.execute("SELECT id FROM forms ORDER BY id")
        ]
        sample_count = min(self._sample_size, len(form_ids))
        chosen_ids = random.Random(self._rng_seed).sample(  # noqa: S311
            form_ids,
            sample_count,
        )
        placeholders = ",".join("?" for _ in chosen_ids)
        query = (
            """
            SELECT
                id,
                normalized_title,
                wordclass,
                function,
                wordclass_id,
                inflection_code_id,
                morph_class_id,
                entry_id
            FROM forms
            WHERE id IN ("""
            + placeholders
            + """)
            ORDER BY id
            """
        )
        self._connection.row_factory = sqlite3.Row
        rows = self._connection.execute(query, chosen_ids).fetchall()
        return list(rows)

    def _find_mismatches(
        self,
        sampled_rows: Sequence[sqlite3.Row],
    ) -> list[FormFkMismatch]:
        """
        Compare sampled FK columns to ``FormFkResolver`` output.

        Args:
            sampled_rows: Form rows selected for verification.

        Returns:
            Mismatch records for stored FK values that differ from resolver output.

        """
        mismatches: list[FormFkMismatch] = []
        for row in sampled_rows:
            expected_wordclass_id = self._resolver.resolve_wordclass_id(
                str(row["wordclass"]),
            )
            expected_inflection_code_id = self._resolver.resolve_inflection_code_id(
                str(row["function"]),
                str(row["wordclass"]),
            )
            expected_morph_class_id = self._resolver.resolve_morph_class_id(
                str(row["normalized_title"]),
                str(row["wordclass"]),
                str(row["function"]),
            )
            expected_entry_id = self._resolver.resolve_entry_id(
                str(row["normalized_title"]),
                str(row["wordclass"]),
            )
            expected_by_column = {
                "wordclass_id": expected_wordclass_id,
                "inflection_code_id": expected_inflection_code_id,
                "morph_class_id": expected_morph_class_id,
                "entry_id": expected_entry_id,
            }
            for column in _FK_COLUMNS:
                stored = row[column]
                stored_value = None if stored is None else int(stored)
                expected = expected_by_column[column]
                if stored_value != expected:
                    mismatches.append(
                        FormFkMismatch(
                            form_id=int(row["id"]),
                            normalized_title=str(row["normalized_title"]),
                            wordclass=str(row["wordclass"]),
                            function=str(row["function"]),
                            column=column,
                            stored=stored_value,
                            expected=expected,
                        ),
                    )
        return mismatches


def format_form_fk_verification_report(report: FormFkVerificationReport) -> str:
    """
    Render one verification report as plain text for CLI or test diagnostics.

    Args:
        report: Verification output from ``FormFkVerificationService.verify``.

    Returns:
        Multi-line human-readable summary including NULL FK baseline counts.

    """
    counts = report.null_fk_counts
    lines = [
        "# Form FK verification",
        f"total_forms={counts.total_forms}",
        f"sampled_forms={report.sampled_forms}",
        "null_fk_counts:",
        f"  wordclass_id={counts.wordclass_id}",
        f"  inflection_code_id={counts.inflection_code_id}",
        f"  morph_class_id={counts.morph_class_id}",
        f"  entry_id={counts.entry_id}",
        f"mismatch_count={len(report.mismatches)}",
    ]
    lines.extend(
        [
            "mismatch "
            f"form_id={mismatch.form_id} "
            f"column={mismatch.column} "
            f"stored={mismatch.stored!r} "
            f"expected={mismatch.expected!r} "
            f"title={mismatch.normalized_title!r} "
            f"wordclass={mismatch.wordclass!r} "
            f"function={mismatch.function!r}"
            for mismatch in report.mismatches[:_MAX_MISMATCH_LINES]
        ],
    )
    if len(report.mismatches) > _MAX_MISMATCH_LINES:
        lines.append(
            f"... {len(report.mismatches) - _MAX_MISMATCH_LINES} additional mismatches",
        )
    return "\n".join(lines)
