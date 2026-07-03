"""SQLAlchemy-backed Bosworth-Toller dictionary query service."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sqlalchemy import text

from wyrdcraeft.db.runtime import create_engine as create_sqlalchemy_engine
from wyrdcraeft.models.dictionary import (
    BTConsolidatedEntry,
    BTGender,
    BTPos,
    BTSense,
)
from wyrdcraeft.services.markup import normalize_old_english

if TYPE_CHECKING:
    from pathlib import Path

    from sqlalchemy.engine import Connection, Engine


#: CLI POS aliases mapped to stored ``bt_entries.pos`` values.
_POS_ALIASES: dict[str, str] = {
    "n": BTPos.NOUN.value,
    "v": BTPos.VERB.value,
    "a": BTPos.ADJ.value,
    "adjective": BTPos.ADJ.value,
    "adverb": BTPos.ADV.value,
    "num": BTPos.NUMERAL.value,
}


def _normalize_lookup_key(value: str) -> str:
    """
    Normalize a lookup token for deterministic dictionary queries.

    Args:
        value: Raw lookup token.

    Returns:
        Canonicalized lookup key.

    """
    normalized = normalize_old_english(value)
    if normalized is None:
        return ""
    return normalized


def _normalize_pos_filter(pos: str | None) -> str | None:
    """
    Normalize an optional CLI POS filter to stored ``bt_entries.pos`` values.

    Args:
        pos: Optional part-of-speech filter from CLI or API callers.

    Returns:
        Stored POS string, or ``None`` when no filter is requested.

    """
    if pos is None:
        return None
    candidate = pos.strip().lower()
    if not candidate:
        return None
    candidate = _POS_ALIASES.get(candidate, candidate)
    try:
        return BTPos(candidate).value
    except ValueError:
        return candidate


def _genders_from_json(payload: str) -> list[BTGender]:
    """
    Deserialize stored gender markers into enum values.

    Args:
        payload: JSON array of gender strings from ``bt_entries.genders_json``.

    Returns:
        Parsed gender markers.

    """
    raw_values = json.loads(payload)
    return [BTGender(value) for value in raw_values]


def _entry_to_dict(entry: BTConsolidatedEntry) -> dict[str, object]:
    """
    Serialize one consolidated entry for JSON CLI output.

    Args:
        entry: Consolidated dictionary record.

    Returns:
        JSON-serializable mapping.

    """
    return {
        "norm_key": entry.norm_key,
        "headword_raw": entry.headword_raw,
        "headword_macronized": entry.headword_macronized,
        "pos": entry.pos.value,
        "genders": [gender.value for gender in entry.genders],
        "variants": list(entry.variants),
        "senses": [
            {"sense_label": sense.sense_label, "gloss_en": sense.gloss_en}
            for sense in entry.senses
        ],
        "etymology": entry.etymology,
        "see_also": list(entry.see_also),
        "source_line_nos": list(entry.source_line_nos),
    }


class BTQueryService:
    """
    Query interface over consolidated Bosworth-Toller entries in the canonical DB.

    Args:
        db_path: Path to ``wyrdcraeft.sqlite3`` containing ``bt_*`` tables.

    """

    #: SQLAlchemy engine bound to the canonical dictionary database.
    _engine: Engine
    #: Active SQLAlchemy connection for dictionary lookups.
    _connection: Connection

    def __init__(self, db_path: Path) -> None:
        """
        Initialize a query service for canonical dictionary tables.

        Args:
            db_path: Path to SQLite database file containing ``bt_*`` tables.

        """
        #: SQLAlchemy engine bound to the canonical dictionary database.
        self._engine = create_sqlalchemy_engine(db_path)
        #: Active SQLAlchemy connection for dictionary lookups.
        self._connection = self._engine.connect()

    def lookup_lemma(
        self,
        lemma: str,
        pos: str | None = None,
    ) -> list[BTConsolidatedEntry]:
        """
        Look up consolidated entries by lemma or alternate variant spelling.

        Args:
            lemma: Headword or variant spelling to resolve.
            pos: Optional POS filter (for example ``noun`` or ``adv``).

        Returns:
            Matching consolidated entries ordered by ``norm_key`` and POS.

        """
        return self.lookup_by_norm_key(_normalize_lookup_key(lemma), pos=pos)

    def lookup_by_norm_key(
        self,
        norm_key: str,
        pos: str | None = None,
    ) -> list[BTConsolidatedEntry]:
        """
        Look up consolidated entries by normalized Old English key.

        Args:
            norm_key: Normalized lookup key (callers may pass raw text; it is
                normalized again for safety).
            pos: Optional POS filter (for example ``noun`` or ``adv``).

        Returns:
            Matching consolidated entries ordered by ``norm_key`` and POS.

        """
        lookup_key = _normalize_lookup_key(norm_key)
        if not lookup_key:
            return []

        pos_filter = _normalize_pos_filter(pos)
        entry_ids = self._resolve_entry_ids(lookup_key, pos_filter=pos_filter)
        return [self._load_entry(entry_id) for entry_id in entry_ids]

    def _resolve_entry_ids(
        self,
        lookup_key: str,
        *,
        pos_filter: str | None,
    ) -> list[int]:
        """
        Resolve matching entry ids from ``norm_key`` and variant spellings.

        Args:
            lookup_key: Normalized lookup key.

        Keyword Args:
            pos_filter: Optional stored POS value filter.

        Returns:
            Distinct entry ids in stable lookup order.

        """
        if pos_filter is not None:
            direct_rows = self._connection.execute(
                text(
                    """
                    SELECT e.id
                    FROM bt_entries e
                    WHERE e.norm_key = :lookup_key AND e.pos = :pos_filter
                    ORDER BY e.norm_key, e.pos, e.id
                    """
                ),
                {"lookup_key": lookup_key, "pos_filter": pos_filter},
            ).mappings().all()
        else:
            direct_rows = self._connection.execute(
                text(
                    """
                    SELECT e.id
                    FROM bt_entries e
                    WHERE e.norm_key = :lookup_key
                    ORDER BY e.norm_key, e.pos, e.id
                    """
                ),
                {"lookup_key": lookup_key},
            ).mappings().all()
        entry_ids = [int(row["id"]) for row in direct_rows]
        if entry_ids:
            return entry_ids

        has_norm_key_row = self._connection.execute(
            text(
                """
                SELECT 1
                FROM bt_entries
                WHERE norm_key = :lookup_key
                LIMIT 1
                """
            ),
            {"lookup_key": lookup_key},
        ).first()
        if has_norm_key_row is not None:
            return []

        if pos_filter is not None:
            variant_rows = self._connection.execute(
                text(
                    """
                    SELECT v.entry_id, v.spelling_raw
                    FROM bt_variants v
                    JOIN bt_entries e ON e.id = v.entry_id
                    WHERE e.pos = :pos_filter
                    ORDER BY v.entry_id
                    """
                ),
                {"pos_filter": pos_filter},
            ).mappings().all()
        else:
            variant_rows = self._connection.execute(
                text(
                    """
                    SELECT v.entry_id, v.spelling_raw
                    FROM bt_variants v
                    ORDER BY v.entry_id
                    """
                )
            ).mappings().all()

        matched: list[int] = []
        seen: set[int] = set()
        for row in variant_rows:
            variant_key = _normalize_lookup_key(str(row["spelling_raw"]))
            if variant_key != lookup_key:
                continue
            entry_id = int(row["entry_id"])
            if entry_id in seen:
                continue
            seen.add(entry_id)
            matched.append(entry_id)
        return matched

    def _load_entry(self, entry_id: int) -> BTConsolidatedEntry:
        """
        Reconstruct one consolidated entry from persisted dictionary rows.

        Args:
            entry_id: Primary key in ``bt_entries``.

        Returns:
            Consolidated dictionary record with ordered senses and variants.

        """
        row = self._connection.execute(
            text(
                """
                SELECT
                    norm_key,
                    headword_raw,
                    headword_macronized,
                    pos,
                    genders_json,
                    etymology,
                    see_also_json,
                    source_line_nos_json
                FROM bt_entries
                WHERE id = :entry_id
                """
            ),
            {"entry_id": entry_id},
        ).mappings().first()
        if row is None:
            msg = f"bt_entries row {entry_id} not found"
            raise LookupError(msg)

        sense_rows = self._connection.execute(
            text(
                """
                SELECT sense_label, gloss_en
                FROM bt_senses
                WHERE entry_id = :entry_id
                ORDER BY order_index ASC, id ASC
                """
            ),
            {"entry_id": entry_id},
        ).mappings().all()
        variant_rows = self._connection.execute(
            text(
                """
                SELECT spelling_raw
                FROM bt_variants
                WHERE entry_id = :entry_id
                ORDER BY spelling_raw ASC, rowid ASC
                """
            ),
            {"entry_id": entry_id},
        ).mappings().all()

        return BTConsolidatedEntry(
            norm_key=str(row["norm_key"]),
            headword_raw=str(row["headword_raw"]),
            headword_macronized=str(row["headword_macronized"]),
            pos=BTPos(str(row["pos"])),
            genders=_genders_from_json(str(row["genders_json"])),
            variants=[str(variant_row["spelling_raw"]) for variant_row in variant_rows],
            senses=[
                BTSense(
                    sense_label=str(sense_row["sense_label"]),
                    gloss_en=str(sense_row["gloss_en"]),
                )
                for sense_row in sense_rows
            ],
            etymology=str(row["etymology"]),
            see_also=json.loads(str(row["see_also_json"])),
            source_line_nos=json.loads(str(row["source_line_nos_json"])),
        )

    def close(self) -> None:
        """Close the SQLAlchemy connection and dispose the engine."""
        self._connection.close()
        self._engine.dispose()


__all__ = ["BTQueryService", "entry_to_dict"]


def entry_to_dict(entry: BTConsolidatedEntry) -> dict[str, object]:
    """
    Serialize one consolidated entry for JSON CLI output.

    Args:
        entry: Consolidated dictionary record.

    Returns:
        JSON-serializable mapping.

    """
    return _entry_to_dict(entry)
