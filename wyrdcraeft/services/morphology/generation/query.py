"""SQLite-backed morphology query service."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from wyrdcraeft.models.morphology import QueryFormRow

from ..text_utils import OENormalizer

if TYPE_CHECKING:
    from pathlib import Path


def _normalize_key(value: str) -> str:
    """
    Normalize a lookup token for deterministic morphology queries.

    Args:
        value: Raw lookup token.

    Returns:
        Canonicalized lookup key.

    """
    return OENormalizer.normalize_output(value).casefold()


def _project_query_rows(rows: list[sqlite3.Row]) -> list[QueryFormRow]:
    """
    Convert raw SQLite rows into typed morphology query rows.

    Args:
        rows: Raw SQLite rows returned from lookup queries.

    Returns:
        Validated query rows with counter values projected as strings.

    """
    projected: list[QueryFormRow] = []
    for row in rows:
        payload = dict(row)
        payload["counter"] = str(payload["counter"])
        projected.append(QueryFormRow.model_validate(payload))
    return projected


class MorphologyQueryService:
    """
    Query interface over emitted morphology rows persisted in SQLite.

    Args:
        db_path: Path to SQLite database file produced by generation.

    """

    #: Active SQLite connection.
    _connection: sqlite3.Connection

    def __init__(self, db_path: Path) -> None:
        """
        Initialize a SQLite query service for a generated morphology index.

        Note:
            Query semantics follow normalization expectations documented in
            ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
            In plain terms, this opens one index used across all Parts of Speech.

        Args:
            db_path: Path to SQLite database file produced by generation.

        """
        #: Active SQLite connection.
        self._connection = sqlite3.connect(str(db_path))
        self._connection.row_factory = sqlite3.Row

    def lookup_by_lemma(self, lemma: str, limit: int = 200) -> list[QueryFormRow]:
        """
        Look up emitted rows by normalized lemma/root token.

        Note:
            Lemma matching aligns with headword conventions in
            ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
            In plain terms, this finds inflected rows for any Part of Speech
            sharing the same base lexeme.

        Args:
            lemma: Lemma/root token matching BT, title, or stem keys.
            limit: Maximum result count.

        Returns:
            Ordered query rows matching the lemma key.

        """
        lemma_key = _normalize_key(lemma)
        rows = self._connection.execute(
            """
            SELECT
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
                COALESCE(bt_key, '') || '|'
                    || COALESCE(title_key, '') || '|'
                    || COALESCE(stem_key, '') AS lemma_key,
                form_key
            FROM forms
            WHERE bt_key = ? OR title_key = ? OR stem_key = ?
            ORDER BY counter ASC, id ASC
            LIMIT ?
            """,
            (lemma_key, lemma_key, lemma_key, max(1, limit)),
        ).fetchall()
        return _project_query_rows(rows)

    def lookup_by_form(self, form: str, limit: int = 200) -> list[QueryFormRow]:
        """
        Look up emitted rows by normalized surface form token.

        Note:
            Surface-form matching aligns with orthographic conventions in
            ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
            In plain terms, this finds rows by written form across Parts of Speech.

        Args:
            form: Surface form token matching emitted ``form`` or ``formi`` keys.
            limit: Maximum result count.

        Returns:
            Ordered query rows matching the form key.

        """
        form_key = _normalize_key(form)
        rows = self._connection.execute(
            """
            SELECT
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
                COALESCE(bt_key, '') || '|'
                    || COALESCE(title_key, '') || '|'
                    || COALESCE(stem_key, '') AS lemma_key,
                form_key
            FROM forms
            WHERE form_key = ? OR formi_key = ?
            ORDER BY counter ASC, id ASC
            LIMIT ?
            """,
            (form_key, form_key, max(1, limit)),
        ).fetchall()
        return _project_query_rows(rows)

    def close(self) -> None:
        """
        Close the SQLite query connection.

        Note:
            Closing is shared infrastructure for all Part-of-Speech queries
            generated from ``data/OldEnglishGrammar.pdf`` and
            ``data/Ondej_Tich_40-54-1.pdf`` aligned outputs.

        """
        self._connection.close()
