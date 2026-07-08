"""SQLAlchemy-backed Bosworth-Toller dictionary query service."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sqlalchemy import func, select, text

from wyrdcraeft.db.runtime import create_engine as create_sqlalchemy_engine
from wyrdcraeft.models.dictionary import (
    BTConsolidatedEntry,
    BTGender,
    BTPos,
    BTSense,
    sense_path_sort_key,
)
from wyrdcraeft.models.reference import PartOfSpeech
from wyrdcraeft.models.sqlalchemy import BTEntry, BTVariant
from wyrdcraeft.services.dictionary.normalized_title_join import (
    NormalizedTitleJoinIndex,
)
from wyrdcraeft.services.markup import normalize_morphology_title, normalize_old_english

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from sqlalchemy.engine import Connection, Engine


#: BT POS values and CLI aliases mapped to canonical ``parts_of_speech.code`` values.
_BT_POS_TO_CODE: dict[str, str] = {
    BTPos.NOUN.value: "noun",
    BTPos.VERB.value: "verb",
    BTPos.ADJ.value: "adjective",
    BTPos.ADV.value: "adverb",
    BTPos.PRON.value: "pronoun",
    BTPos.NUMERAL.value: "numeral",
    BTPos.PREP.value: "preposition",
    BTPos.CONJ.value: "conjunction",
    BTPos.INTERJ.value: "interjection",
    BTPos.INDECL.value: "indeclinable",
    BTPos.UNKNOWN.value: "unknown",
    "n": "noun",
    "v": "verb",
    "a": "adjective",
    "adjective": "adjective",
    "adverb": "adverb",
    "num": "numeral",
}

#: Canonical ``parts_of_speech.code`` values mapped back to BT enum values.
_CODE_TO_BT_POS: dict[str, BTPos] = {
    "noun": BTPos.NOUN,
    "verb": BTPos.VERB,
    "adjective": BTPos.ADJ,
    "adverb": BTPos.ADV,
    "pronoun": BTPos.PRON,
    "numeral": BTPos.NUMERAL,
    "preposition": BTPos.PREP,
    "conjunction": BTPos.CONJ,
    "interjection": BTPos.INTERJ,
    "indeclinable": BTPos.INDECL,
    "unknown": BTPos.UNKNOWN,
}


def _normalize_title_key(value: str) -> str:
    """
    Normalize a macron-preserving dictionary join title.

    Args:
        value: Raw headword or lemma title text.

    Returns:
        Canonicalized ``normalized_title`` lookup key.

    """
    return normalize_morphology_title(value)


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
    Normalize an optional CLI POS filter to canonical POS codes.

    Args:
        pos: Optional part-of-speech filter from CLI or API callers.

    Returns:
        Canonical ``parts_of_speech.code`` string, or ``None`` when no filter is
        requested.

    """
    if pos is None:
        return None
    candidate = pos.strip().lower()
    if not candidate:
        return None
    return _BT_POS_TO_CODE.get(candidate, candidate)


def _bt_pos_from_code(code: str) -> BTPos:
    """
    Convert a canonical POS code back to the BT enum used by CLI payloads.

    Args:
        code: Canonical ``parts_of_speech.code`` value loaded from SQLite.

    Returns:
        Matching Bosworth-Toller part-of-speech enum.

    Raises:
        LookupError: The canonical code has no BT-facing representation.

    """
    pos = _CODE_TO_BT_POS.get(code.strip().lower())
    if pos is None:
        msg = f"unsupported bt_entries POS code {code!r}"
        raise LookupError(msg)
    return pos


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


def _json_tuple(payload: str | None) -> tuple[str, ...]:
    """
    Deserialize a JSON string array into an immutable tuple.

    Args:
        payload: JSON array text or ``None`` when the column is absent.

    Returns:
        Parsed string tuple; empty when payload is missing or blank.

    """
    if payload is None or not str(payload).strip():
        return ()
    raw_values = json.loads(payload)
    return tuple(str(value) for value in raw_values)


def _sense_from_row(sense_row: Mapping[str, object]) -> BTSense:
    """
    Reconstruct one ``BTSense`` from a persisted ``bt_senses`` row mapping.

    Args:
        sense_row: Row mapping returned by SQLAlchemy execution.

    Returns:
        Consolidated sense with defaults for legacy rows missing rich columns.

    """
    gloss_en = str(sense_row["gloss_en"])
    source_label_raw = str(
        sense_row.get("source_label_raw") or sense_row.get("sense_label") or ""
    )
    order_index_raw = sense_row.get("order_index")
    order_index = int(order_index_raw) if isinstance(order_index_raw, int) else 0
    fallback_path = source_label_raw or str(order_index + 1)
    sense_path = str(sense_row.get("sense_path") or fallback_path)
    parent_path_raw = sense_row.get("parent_path")
    parent_path = None if parent_path_raw in (None, "") else str(parent_path_raw)
    return BTSense(
        gloss_en=gloss_en,
        sense_path=sense_path,
        parent_path=parent_path,
        source_label_raw=source_label_raw,
        source_fragment_raw=str(
            sense_row.get("source_fragment_raw") or gloss_en
        ),
        prefix_fragment_raw=str(sense_row.get("prefix_fragment_raw") or ""),
        modifiers=_json_tuple(
            None
            if sense_row.get("modifiers_json") is None
            else str(sense_row["modifiers_json"])
        ),
        grammatical_context=_json_tuple(
            None
            if sense_row.get("grammatical_context_json") is None
            else str(sense_row["grammatical_context_json"])
        ),
        usage_note=str(sense_row.get("usage_note") or ""),
    )


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
        "normalized_title": entry.normalized_title,
        "pos": entry.pos.value,
        "genders": [gender.value for gender in entry.genders],
        "variants": list(entry.variants),
        "entry_order": entry.entry_order,
        "senses": [
            {
                "sense_label": sense.display_label,
                "gloss_en": sense.gloss_en,
                "sense_path": sense.sense_path,
                "parent_path": sense.parent_path,
                "source_fragment_raw": sense.source_fragment_raw,
                "prefix_fragment_raw": sense.prefix_fragment_raw,
                "modifiers": list(sense.modifiers),
                "grammatical_context": list(sense.grammatical_context),
                "usage_note": sense.usage_note,
            }
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
    #: Preloaded normalized-title join resolver for morphology dictionary joins.
    _normalized_title_index: NormalizedTitleJoinIndex

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
        #: Preloaded normalized-title join resolver for morphology dictionary joins.
        self._normalized_title_index = self._load_normalized_title_index()

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

    def lookup_by_normalized_title(
        self,
        normalized_title: str,
        pos: str | None = None,
    ) -> list[BTConsolidatedEntry]:
        """
        Look up consolidated entries by macron-preserving normalized title.

        Matching order:
            1) ``normalized_title`` with optional POS filter on ``bt_entries``.
            2) Exactly one ``bt_entries`` row for the title across all POS values.
            3) ``bt_variants.normalized_title`` spelling match.

        Args:
            normalized_title: Macron/dot-preserving normalized headword title.
            pos: Optional POS filter (for example ``noun`` or ``adv``).

        Returns:
            Matching consolidated entries ordered by entry id.

        """
        title_key = _normalize_title_key(normalized_title)
        if not title_key:
            return []

        pos_filter = _normalize_pos_filter(pos)
        entry_ids = self._normalized_title_index.resolve_all(
            title_key,
            pos_filter,
        )
        return [self._load_entry(entry_id) for entry_id in entry_ids]

    def _load_normalized_title_index(self) -> NormalizedTitleJoinIndex:
        """
        Preload normalized-title join maps from canonical dictionary tables.

        Returns:
            Join index built from ``bt_entries`` and ``bt_variants`` rows.

        """
        entry_rows = self._connection.execute(
            select(BTEntry.id, BTEntry.normalized_title, PartOfSpeech.code).join(
                PartOfSpeech,
                PartOfSpeech.id == BTEntry.pos_id,
            )
        ).all()
        variant_rows = self._connection.execute(
            select(
                BTVariant.entry_id,
                BTVariant.normalized_title,
                PartOfSpeech.code,
            )
            .join(BTEntry, BTEntry.id == BTVariant.entry_id)
            .join(PartOfSpeech, PartOfSpeech.id == BTEntry.pos_id)
            .where(func.trim(func.coalesce(BTVariant.normalized_title, "")) != "")
        ).all()
        return NormalizedTitleJoinIndex.from_entry_variant_rows(
            [
                (int(row.id), str(row.normalized_title), str(row.code))
                for row in entry_rows
            ],
            [
                (int(row.entry_id), str(row.normalized_title), str(row.code))
                for row in variant_rows
            ],
        )

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
                    JOIN parts_of_speech p ON p.id = e.pos_id
                    WHERE e.norm_key = :lookup_key AND p.code = :pos_filter
                    ORDER BY e.norm_key, p.code, e.entry_order, e.id
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
                    JOIN parts_of_speech p ON p.id = e.pos_id
                    WHERE e.norm_key = :lookup_key
                    ORDER BY e.norm_key, p.code, e.entry_order, e.id
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
                    JOIN parts_of_speech p ON p.id = e.pos_id
                    WHERE p.code = :pos_filter
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
                    e.norm_key,
                    e.headword,
                    e.normalized_title,
                    p.code AS pos_code,
                    e.genders_json,
                    e.etymology,
                    e.see_also_json,
                    e.source_line_nos_json,
                    e.entry_order
                FROM bt_entries e
                JOIN parts_of_speech p ON p.id = e.pos_id
                WHERE e.id = :entry_id
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
                SELECT
                    sense_label,
                    gloss_en,
                    order_index,
                    sense_path,
                    parent_path,
                    source_label_raw,
                    source_fragment_raw,
                    prefix_fragment_raw,
                    modifiers_json,
                    grammatical_context_json,
                    usage_note
                FROM bt_senses
                WHERE entry_id = :entry_id
                ORDER BY order_index ASC, id ASC
                """
            ),
            {"entry_id": entry_id},
        ).mappings().all()
        senses = [_sense_from_row(dict(sense_row)) for sense_row in sense_rows]
        senses.sort(key=lambda sense: sense_path_sort_key(sense.sense_path))
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

        headword = str(row["headword"])
        pos = _bt_pos_from_code(str(row["pos_code"]))
        return BTConsolidatedEntry(
            norm_key=str(row["norm_key"]),
            # Raw headwords are no longer persisted separately; expose the stored
            # display headword for backward-compatible consolidated-entry reads.
            headword_raw=headword,
            headword_macronized=headword,
            normalized_title=str(row["normalized_title"]),
            pos=pos,
            genders=_genders_from_json(str(row["genders_json"])),
            variants=[str(variant_row["spelling_raw"]) for variant_row in variant_rows],
            senses=senses,
            etymology=str(row["etymology"]),
            see_also=json.loads(str(row["see_also_json"])),
            source_line_nos=json.loads(str(row["source_line_nos_json"])),
            entry_order=int(row["entry_order"]),
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
