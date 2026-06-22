"""SQLite persistence for Bosworth-Toller dictionary index entries."""

from __future__ import annotations

import json
import sqlite3
from typing import TYPE_CHECKING

from wyrdcraeft.services.dictionary.bt_spelling import BTSpellingNormalizer

if TYPE_CHECKING:
    from pathlib import Path

    from wyrdcraeft.models.dictionary import BTConsolidatedEntry, BTGender
    from wyrdcraeft.services.dictionary.editorial_merger import BTEditRecord


class BTSqliteSink:
    """
    SQLite sink that persists consolidated Bosworth-Toller dictionary entries.

    In default mode, rebuilds the ``bt_*`` schema on each index run so the
    database reflects one complete source pass. In attach mode, writes ``bt_*``
    tables into an existing morphology database without modifying ``forms``.

    Args:
        db_path: Path to ``dictionary.sqlite3`` or ``morphology.sqlite3`` output.
        attach_mode: When ``True``, preserve non-``bt_*`` tables and reload
            dictionary rows in place.

    """

    #: Resolved SQLite database file path.
    db_path: Path
    #: When ``True``, preserve non-``bt_*`` tables and reload dictionary rows.
    attach_mode: bool
    #: Active SQLite connection.
    _connection: sqlite3.Connection
    #: Display spelling normalizer for variant macronization.
    _spelling_normalizer: BTSpellingNormalizer

    def __init__(self, db_path: Path, *, attach_mode: bool = False) -> None:
        """
        Initialize the dictionary SQLite sink and prepare the ``bt_*`` schema.

        Args:
            db_path: Path to ``dictionary.sqlite3`` or ``morphology.sqlite3``.

        Keyword Args:
            attach_mode: When ``True``, attach ``bt_*`` tables to an existing
                morphology database without altering ``forms``.

        Side Effects:
            In default mode, removes any existing database file at ``db_path``
            and creates a fresh schema with lookup indexes. In attach mode,
            creates the file when missing, ensures ``bt_*`` tables exist, and
            truncates prior ``bt_*`` contents before reload.

        """
        resolved = db_path.expanduser().resolve()
        resolved.parent.mkdir(parents=True, exist_ok=True)
        if not attach_mode and resolved.exists():
            resolved.unlink()
        #: Resolved SQLite database file path.
        self.db_path = resolved
        #: When ``True``, preserve non-``bt_*`` tables and reload dictionary rows.
        self.attach_mode = attach_mode
        #: Active SQLite connection.
        self._connection = sqlite3.connect(str(resolved))
        #: Display spelling normalizer for variant macronization.
        self._spelling_normalizer = BTSpellingNormalizer()
        self._init_schema()

    def _init_schema(self) -> None:
        """Create or refresh dictionary index tables and lookup indexes."""
        if self.attach_mode:
            self._ensure_bt_schema()
            self._truncate_bt_tables()
        else:
            self._create_bt_schema()

    def _create_bt_schema(self) -> None:
        """Create a fresh ``bt_*`` schema for standalone dictionary indexing."""
        self._connection.executescript(
            """
            CREATE TABLE bt_entries (
                id INTEGER PRIMARY KEY,
                norm_key TEXT NOT NULL,
                headword_raw TEXT NOT NULL,
                headword_macronized TEXT NOT NULL,
                pos TEXT NOT NULL,
                genders_json TEXT NOT NULL,
                etymology TEXT NOT NULL,
                see_also_json TEXT NOT NULL,
                source_line_nos_json TEXT NOT NULL,
                UNIQUE(norm_key, pos)
            );

            CREATE TABLE bt_senses (
                id INTEGER PRIMARY KEY,
                entry_id INTEGER NOT NULL REFERENCES bt_entries(id),
                sense_label TEXT NOT NULL,
                gloss_en TEXT NOT NULL,
                order_index INTEGER NOT NULL
            );

            CREATE TABLE bt_variants (
                entry_id INTEGER NOT NULL REFERENCES bt_entries(id),
                spelling_raw TEXT NOT NULL,
                spelling_macronized TEXT NOT NULL
            );

            CREATE TABLE bt_edit_log (
                id INTEGER PRIMARY KEY,
                op TEXT NOT NULL,
                source_line_no INTEGER NOT NULL,
                target_norm_key TEXT NOT NULL,
                target_pos TEXT NOT NULL,
                scope TEXT NOT NULL,
                applied INTEGER NOT NULL,
                note TEXT NOT NULL
            );

            CREATE INDEX idx_bt_entries_norm_key ON bt_entries(norm_key);
            CREATE INDEX idx_bt_variants_spelling ON bt_variants(spelling_macronized);
            """
        )
        self._connection.commit()

    def _ensure_bt_schema(self) -> None:
        """Ensure ``bt_*`` tables and indexes exist without altering ``forms``."""
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS bt_entries (
                id INTEGER PRIMARY KEY,
                norm_key TEXT NOT NULL,
                headword_raw TEXT NOT NULL,
                headword_macronized TEXT NOT NULL,
                pos TEXT NOT NULL,
                genders_json TEXT NOT NULL,
                etymology TEXT NOT NULL,
                see_also_json TEXT NOT NULL,
                source_line_nos_json TEXT NOT NULL,
                UNIQUE(norm_key, pos)
            );

            CREATE TABLE IF NOT EXISTS bt_senses (
                id INTEGER PRIMARY KEY,
                entry_id INTEGER NOT NULL REFERENCES bt_entries(id),
                sense_label TEXT NOT NULL,
                gloss_en TEXT NOT NULL,
                order_index INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS bt_variants (
                entry_id INTEGER NOT NULL REFERENCES bt_entries(id),
                spelling_raw TEXT NOT NULL,
                spelling_macronized TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS bt_edit_log (
                id INTEGER PRIMARY KEY,
                op TEXT NOT NULL,
                source_line_no INTEGER NOT NULL,
                target_norm_key TEXT NOT NULL,
                target_pos TEXT NOT NULL,
                scope TEXT NOT NULL,
                applied INTEGER NOT NULL,
                note TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_bt_entries_norm_key
                ON bt_entries(norm_key);
            CREATE INDEX IF NOT EXISTS idx_bt_variants_spelling
                ON bt_variants(spelling_macronized);
            """
        )
        self._connection.commit()

    def _truncate_bt_tables(self) -> None:
        """Remove prior ``bt_*`` rows while leaving morphology tables untouched."""
        self._connection.executescript(
            """
            DELETE FROM bt_senses;
            DELETE FROM bt_variants;
            DELETE FROM bt_edit_log;
            DELETE FROM bt_entries;
            """
        )
        self._connection.commit()

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
            ``bt_edit_log``.

        """
        entries_written = 0
        senses_written = 0
        variants_written = 0

        for entry in entries:
            cursor = self._connection.execute(
                """
                INSERT INTO bt_entries (
                    norm_key,
                    headword_raw,
                    headword_macronized,
                    pos,
                    genders_json,
                    etymology,
                    see_also_json,
                    source_line_nos_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.norm_key,
                    entry.headword_raw,
                    entry.headword_macronized,
                    entry.pos.value,
                    self._genders_json(entry.genders),
                    entry.etymology,
                    json.dumps(entry.see_also, ensure_ascii=False),
                    json.dumps(entry.source_line_nos),
                ),
            )
            entry_id_raw = cursor.lastrowid
            if entry_id_raw is None:
                msg = "INSERT into bt_entries did not return a row id"
                raise RuntimeError(msg)
            entry_id = int(entry_id_raw)
            entries_written += 1

            for order_index, sense in enumerate(entry.senses):
                self._connection.execute(
                    """
                    INSERT INTO bt_senses (
                        entry_id,
                        sense_label,
                        gloss_en,
                        order_index
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (entry_id, sense.sense_label, sense.gloss_en, order_index),
                )
                senses_written += 1

            for variant_raw in entry.variants:
                variant_macronized = self._spelling_normalizer.normalize(variant_raw)
                self._connection.execute(
                    """
                    INSERT INTO bt_variants (
                        entry_id,
                        spelling_raw,
                        spelling_macronized
                    ) VALUES (?, ?, ?)
                    """,
                    (entry_id, variant_raw, variant_macronized),
                )
                variants_written += 1

        edit_log_written = 0
        for record in edit_records:
            self._connection.execute(
                """
                INSERT INTO bt_edit_log (
                    op,
                    source_line_no,
                    target_norm_key,
                    target_pos,
                    scope,
                    applied,
                    note
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.op.value,
                    record.source_line_no,
                    record.target_norm_key,
                    record.target_pos.value,
                    record.scope,
                    int(record.applied),
                    record.note,
                ),
            )
            edit_log_written += 1

        self._connection.commit()
        return entries_written, senses_written, variants_written, edit_log_written

    def close(self) -> None:
        """Close the SQLite connection."""
        self._connection.close()
