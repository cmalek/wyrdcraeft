"""Lexicon read-model builder from morphology and dictionary source tables."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final, cast

from wyrdcraeft.services.dictionary.bt_spelling import BTSpellingNormalizer
from wyrdcraeft.services.markup import normalize_old_english
from wyrdcraeft.services.morphology.text_utils import OENormalizer

from .schema import (
    KEY_KIND_FORM,
    KEY_KIND_LEMMA,
    KEY_KIND_STEM,
    KEY_KIND_VARIANT,
    LEXICON_SCHEMA_DDL,
    META_KEY_BT_ENTRIES_SOURCE_COUNT,
    META_KEY_BUILT_AT,
    META_KEY_FORMS_SOURCE_COUNT,
    META_KEY_SCHEMA_VERSION,
    RANK_TIER_EXACT_ENTRY,
    RANK_TIER_MORPH_FORM,
    RANK_TIER_MORPH_LEMMA_STEM,
    RANK_TIER_ORPHAN,
    SCHEMA_VERSION,
)

if TYPE_CHECKING:
    from pathlib import Path

#: Allowed source tables for staleness row-count checks.
_STALENESS_SOURCE_TABLES: Final[tuple[str, ...]] = ("forms", "bt_entries")
#: Source tables required to rebuild ``lexicon_*`` rows.
_REQUIRED_SOURCE_TABLES: Final[tuple[str, ...]] = (
    *_STALENESS_SOURCE_TABLES,
    "bt_senses",
    "bt_variants",
)

#: Morphology ``wordclass`` values mapped to dictionary ``bt_entries.pos`` labels.
_WORDCLASS_TO_BT_POS: Final[dict[str, str]] = {
    "noun": "noun",
    "verb": "verb",
    "adjective": "adj",
    "adverb": "adv",
    "numeral": "numeral",
    "pronoun": "pron",
    "preposition": "prep",
    "conjunction": "conj",
    "interjection": "interj",
    "indeclinable": "indecl",
}


#: Projected dictionary entry payload produced from ``bt_entries`` sources.
EntryPayload = dict[str, object]
#: Projected morphology form payload produced from ``forms`` sources.
FormPayload = dict[str, object]
#: Ranked search-key payload row for ``lexicon_search_keys`` inserts.
SearchKeyRow = tuple[str, str, int, int | None, int | None, str]


class MissingLexiconSourceTablesError(RuntimeError):
    """Raised when rebuild prerequisites are absent from the SQLite schema."""


@dataclass(frozen=True)
class LexiconBuildMeta:
    """
    Build metadata persisted in ``lexicon_build_meta`` after a rebuild.

    Attributes:
        schema_version: Lexicon schema version recorded at rebuild time.
        built_at: UTC timestamp (ISO-8601) of the last rebuild.
        forms_source_count: ``forms`` row count observed during rebuild.
        bt_entries_source_count: ``bt_entries`` row count observed during rebuild.

    """

    #: Lexicon schema version recorded at rebuild time.
    schema_version: int
    #: UTC timestamp (ISO-8601) of the last rebuild.
    built_at: str
    #: ``forms`` row count observed during rebuild.
    forms_source_count: int
    #: ``bt_entries`` row count observed during rebuild.
    bt_entries_source_count: int


@dataclass(frozen=True)
class LexiconStalenessReport:
    """
    Staleness summary comparing stored build metadata to current source tables.

    Attributes:
        is_stale: ``True`` when rebuild metadata is missing or source counts differ.
        reason: Human-readable explanation of the staleness state.
        meta: Stored build metadata when present.
        current_forms_count: Current ``forms`` row count in the database.
        current_bt_entries_count: Current ``bt_entries`` row count in the database.

    """

    #: ``True`` when rebuild metadata is missing or source counts differ.
    is_stale: bool
    #: Human-readable explanation of the staleness state.
    reason: str
    #: Stored build metadata when present.
    meta: LexiconBuildMeta | None
    #: Current ``forms`` row count in the database.
    current_forms_count: int
    #: Current ``bt_entries`` row count in the database.
    current_bt_entries_count: int


@dataclass(frozen=True)
class BuildReport:
    """
    Result summary for one lexicon rebuild.

    Attributes:
        schema_version: Lexicon schema version written to metadata.
        built_at: UTC timestamp (ISO-8601) recorded for this rebuild.
        forms_source_count: Source ``forms`` row count consumed by rebuild.
        bt_entries_source_count: Source ``bt_entries`` row count consumed.
        entries_written: ``lexicon_entries`` rows written.
        forms_written: ``lexicon_forms`` rows written.
        search_keys_written: ``lexicon_search_keys`` rows written.

    """

    #: Lexicon schema version written to metadata.
    schema_version: int
    #: UTC timestamp (ISO-8601) recorded for this rebuild.
    built_at: str
    #: Source ``forms`` row count consumed by rebuild.
    forms_source_count: int
    #: Source ``bt_entries`` row count consumed by rebuild.
    bt_entries_source_count: int
    #: Number of rows inserted into ``lexicon_entries``.
    entries_written: int
    #: Number of rows inserted into ``lexicon_forms``.
    forms_written: int
    #: Number of rows inserted into ``lexicon_search_keys``.
    search_keys_written: int


def _normalize_morph_key(value: str) -> str:
    """
    Normalize a morphology token to the canonical lookup key shape.

    Args:
        value: Surface token from ``forms`` data.

    Returns:
        Canonical key string suitable for search-key lookup.

    """
    return OENormalizer.normalize_output(value).casefold()


def _normalize_dictionary_key(
    value: str,
    spelling_normalizer: BTSpellingNormalizer,
) -> str:
    """
    Normalize dictionary display text for unified search keys.

    Args:
        value: Headword or variant display spelling.
        spelling_normalizer: Dictionary display spelling normalizer.

    Returns:
        Old-English normalized key text or an empty string when unavailable.

    """
    normalized_display = spelling_normalizer.normalize(value)
    return normalize_old_english(normalized_display) or ""


class LexiconBuilder:
    """
    Rebuild ``lexicon_*`` read-model tables from ``forms`` and ``bt_*`` sources.

    Args:
        db_path: Path to the canonical ``morphology.sqlite3`` database.

    """

    #: Database file containing ``forms``, ``bt_*``, and target ``lexicon_*`` tables.
    _db_path: Path
    #: Spelling normalizer for dictionary headwords and variants.
    _spelling_normalizer: BTSpellingNormalizer

    def __init__(self, db_path: Path) -> None:
        """
        Initialize a lexicon builder for one SQLite database.

        Args:
            db_path: Path to the canonical ``morphology.sqlite3`` database.

        """
        #: Database file containing source and target lexicon tables.
        self._db_path = db_path.expanduser().resolve()
        #: Spelling normalizer for dictionary headwords and variants.
        self._spelling_normalizer = BTSpellingNormalizer()

    def rebuild(self) -> BuildReport:
        """
        Rebuild all ``lexicon_*`` contents from current source tables.

        Returns:
            Build report with source counts, write counts, and metadata fields.

        Raises:
            MissingLexiconSourceTablesError: Required source tables are missing.

        Side Effects:
            Replaces all rows in ``lexicon_entries``, ``lexicon_forms``,
            ``lexicon_search_keys``, and ``lexicon_build_meta`` within one
            transaction.

        """
        with sqlite3.connect(str(self._db_path)) as connection:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            report: BuildReport
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._ensure_required_sources(connection)
                connection.executescript(LEXICON_SCHEMA_DDL)
                self._clear_lexicon_tables(connection)
                report = self._rebuild_into_connection(connection)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return report

    def _ensure_required_sources(self, connection: sqlite3.Connection) -> None:
        """
        Raise an error when source tables needed by rebuild are missing.

        Args:
            connection: Open SQLite connection to inspect for source tables.

        Raises:
            MissingLexiconSourceTablesError: Required source tables are missing.

        """
        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        ).fetchall()
        available = {str(row["name"]) for row in rows}
        missing = sorted(set(_REQUIRED_SOURCE_TABLES) - available)
        if missing:
            missing_csv = ", ".join(missing)
            msg = f"Lexicon rebuild requires source tables: {missing_csv}"
            raise MissingLexiconSourceTablesError(msg)

    def _clear_lexicon_tables(self, connection: sqlite3.Connection) -> None:
        """
        Delete prior ``lexicon_*`` rows while preserving source tables.

        Args:
            connection: Open SQLite connection receiving the delete statements.

        Side Effects:
            Removes rows from all ``lexicon_*`` tables.

        """
        connection.execute("DELETE FROM lexicon_search_keys")
        connection.execute("DELETE FROM lexicon_forms")
        connection.execute("DELETE FROM lexicon_entries")
        connection.execute("DELETE FROM lexicon_build_meta")

    def _rebuild_into_connection(self, connection: sqlite3.Connection) -> BuildReport:
        """
        Insert derived lexicon entries, forms, keys, and build metadata.

        Args:
            connection: Open SQLite connection with source and lexicon tables.

        Returns:
            Build report for inserted entry, form, and search-key rows.

        """
        forms_source_count = int(
            connection.execute("SELECT COUNT(*) FROM forms").fetchone()[0]
        )
        bt_entries_source_count = int(
            connection.execute("SELECT COUNT(*) FROM bt_entries").fetchone()[0]
        )
        built_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace(
            "+00:00",
            "Z",
        )

        entries = self._load_entry_payloads(connection)
        self._insert_entries(connection, entries)

        forms = self._load_form_payloads(connection, entries)
        self._insert_forms(connection, forms)

        search_keys = self._build_search_keys(entries, forms)
        self._insert_search_keys(connection, search_keys)

        self._insert_build_meta(
            connection,
            built_at=built_at,
            forms_source_count=forms_source_count,
            bt_entries_source_count=bt_entries_source_count,
        )
        return BuildReport(
            schema_version=SCHEMA_VERSION,
            built_at=built_at,
            forms_source_count=forms_source_count,
            bt_entries_source_count=bt_entries_source_count,
            entries_written=len(entries),
            forms_written=len(forms),
            search_keys_written=len(search_keys),
        )

    def _load_entry_payloads(
        self,
        connection: sqlite3.Connection,
    ) -> list[EntryPayload]:
        """
        Load and project dictionary rows into ``lexicon_entries`` payloads.

        Args:
            connection: Open SQLite connection queried for ``bt_*`` rows.

        Returns:
            Projected dictionary entry payloads for lexicon inserts.

        """
        sense_rows = connection.execute(
            """
            SELECT entry_id, sense_label, gloss_en, order_index
            FROM bt_senses
            ORDER BY entry_id ASC, order_index ASC, id ASC
            """
        ).fetchall()
        senses_by_entry: dict[int, list[dict[str, object]]] = {}
        for row in sense_rows:
            entry_id = int(row["entry_id"])
            senses_by_entry.setdefault(entry_id, []).append(
                {
                    "sense_label": str(row["sense_label"]),
                    "gloss_en": str(row["gloss_en"]),
                    "order_index": int(row["order_index"]),
                }
            )

        variant_rows = connection.execute(
            """
            SELECT entry_id, spelling_macronized
            FROM bt_variants
            ORDER BY entry_id ASC, rowid ASC
            """
        ).fetchall()
        variants_by_entry: dict[int, list[str]] = {}
        for row in variant_rows:
            entry_id = int(row["entry_id"])
            variant = str(row["spelling_macronized"]).strip()
            if not variant:
                continue
            variants = variants_by_entry.setdefault(entry_id, [])
            if variant not in variants:
                variants.append(variant)

        entry_rows = connection.execute(
            """
            SELECT id, norm_key, pos, headword_macronized, etymology, genders_json
            FROM bt_entries
            ORDER BY id ASC
            """
        ).fetchall()

        payloads: list[EntryPayload] = []
        for row in entry_rows:
            entry_id = int(row["id"])
            senses = senses_by_entry.get(entry_id, [])
            summary_sense = ""
            for sense in senses:
                gloss = str(sense["gloss_en"]).strip()
                if gloss:
                    summary_sense = gloss
                    break
            payloads.append(
                {
                    "entry_id": entry_id,
                    "norm_key": str(row["norm_key"]),
                    "pos": str(row["pos"]),
                    "headword": str(row["headword_macronized"]),
                    "summary_sense": summary_sense,
                    "etymology": str(row["etymology"]),
                    "variants": variants_by_entry.get(entry_id, []),
                    "genders_json": str(row["genders_json"]),
                    "senses": senses,
                }
            )
        return payloads

    def _insert_entries(
        self,
        connection: sqlite3.Connection,
        entries: list[EntryPayload],
    ) -> None:
        """
        Insert projected dictionary entries into ``lexicon_entries``.

        Args:
            connection: Open SQLite connection receiving entry inserts.
            entries: Projected dictionary payload rows to insert.

        """
        payload = [
            (
                entry["entry_id"],
                entry["norm_key"],
                entry["pos"],
                entry["headword"],
                entry["summary_sense"],
                entry["etymology"],
                json.dumps(entry["variants"], ensure_ascii=False),
                entry["genders_json"],
                json.dumps(entry["senses"], ensure_ascii=False),
            )
            for entry in entries
        ]
        connection.executemany(
            """
            INSERT INTO lexicon_entries (
                entry_id,
                norm_key,
                pos,
                headword,
                summary_sense,
                etymology,
                variants_json,
                genders_json,
                senses_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            payload,
        )

    def _load_form_payloads(
        self,
        connection: sqlite3.Connection,
        entries: list[EntryPayload],
    ) -> list[FormPayload]:
        """
        Project ``forms`` rows into ``lexicon_forms`` payloads with joins.

        Args:
            connection: Open SQLite connection queried for ``forms`` rows.
            entries: Projected dictionary entry payloads used for joining.

        Returns:
            Projected morphology form payloads with optional entry joins.

        """
        entry_ids_by_norm_pos: dict[tuple[str, str], list[int]] = {}
        entry_ids_by_norm: dict[str, list[int]] = {}
        for entry in entries:
            entry_id = cast("int", entry["entry_id"])
            norm_key = str(entry["norm_key"])
            pos = str(entry["pos"])
            entry_ids_by_norm_pos.setdefault((norm_key, pos), []).append(entry_id)
            entry_ids_by_norm.setdefault(norm_key, []).append(entry_id)

        rows = connection.execute(
            """
            SELECT
                id,
                BT,
                title,
                stem,
                form,
                formi,
                wordclass,
                function,
                probability,
                class1,
                class2,
                class3,
                bt_key,
                title_key,
                stem_key,
                form_key,
                formi_key
            FROM forms
            ORDER BY id ASC
            """
        ).fetchall()

        payloads: list[FormPayload] = []
        for row in rows:
            bt_pos = _WORDCLASS_TO_BT_POS.get(str(row["wordclass"]).strip().lower(), "")
            keys_in_priority = (
                normalize_old_english(str(row["BT"])) or "",
                normalize_old_english(str(row["title"])) or "",
                normalize_old_english(str(row["stem"])) or "",
                str(row["bt_key"]),
                str(row["title_key"]),
                str(row["stem_key"]),
            )
            matched_entry_id = self._select_entry_id(
                keys_in_priority,
                bt_pos,
                entry_ids_by_norm_pos,
                entry_ids_by_norm,
            )
            payloads.append(
                {
                    "form_id": int(row["id"]),
                    "entry_id": matched_entry_id,
                    "bt": str(row["BT"]),
                    "title": str(row["title"]),
                    "stem": str(row["stem"]),
                    "form": str(row["form"]),
                    "formi": str(row["formi"]),
                    "wordclass": str(row["wordclass"]),
                    "function": str(row["function"]),
                    "probability": str(row["probability"]),
                    "class1": str(row["class1"]),
                    "class2": str(row["class2"]),
                    "class3": str(row["class3"]),
                    "bt_key": str(row["bt_key"]),
                    "title_key": str(row["title_key"]),
                    "stem_key": str(row["stem_key"]),
                    "form_key": str(row["form_key"]),
                    "formi_key": str(row["formi_key"]),
                }
            )
        return payloads

    def _select_entry_id(
        self,
        keys_in_priority: tuple[str, ...],
        bt_pos: str,
        entry_ids_by_norm_pos: dict[tuple[str, str], list[int]],
        entry_ids_by_norm: dict[str, list[int]],
    ) -> int | None:
        """
        Select the best dictionary entry match for one morphology form row.

        Matching order:
        1) First key with POS-constrained match.
        2) First key with exactly one entry across all POS values.

        Args:
            keys_in_priority: Candidate normalized morphology keys by match priority.
            bt_pos: Optional dictionary POS filter derived from morphology class.
            entry_ids_by_norm_pos: Entry IDs keyed by ``(norm_key, pos)``.
            entry_ids_by_norm: Entry IDs keyed by ``norm_key`` only.

        Returns:
            Matching entry ID when joinable, otherwise ``None``.

        """
        for key in keys_in_priority:
            if key and bt_pos:
                pos_matches = entry_ids_by_norm_pos.get((key, bt_pos), [])
                if pos_matches:
                    return min(pos_matches)
        for key in keys_in_priority:
            if not key:
                continue
            matches = entry_ids_by_norm.get(key, [])
            if len(matches) == 1:
                return matches[0]
        return None

    def _insert_forms(
        self,
        connection: sqlite3.Connection,
        forms: list[FormPayload],
    ) -> None:
        """
        Insert projected morphology rows into ``lexicon_forms``.

        Args:
            connection: Open SQLite connection receiving form inserts.
            forms: Projected form payload rows to insert.

        """
        payload = [
            (
                form["form_id"],
                form["entry_id"],
                form["bt"],
                form["title"],
                form["stem"],
                form["form"],
                form["formi"],
                form["wordclass"],
                form["function"],
                form["probability"],
                form["class1"],
                form["class2"],
                form["class3"],
            )
            for form in forms
        ]
        connection.executemany(
            """
            INSERT INTO lexicon_forms (
                form_id,
                entry_id,
                bt,
                title,
                stem,
                form,
                formi,
                wordclass,
                function,
                probability,
                class1,
                class2,
                class3
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            payload,
        )

    def _build_search_keys(
        self,
        entries: list[EntryPayload],
        forms: list[FormPayload],
    ) -> list[SearchKeyRow]:
        """
        Build ranked search-key rows for dictionary and morphology lookups.

        Args:
            entries: Projected dictionary entry payloads.
            forms: Projected morphology form payloads.

        Returns:
            Ranked search-key payload rows for lexicon insertion.

        """
        rows: list[SearchKeyRow] = []
        seen: set[SearchKeyRow] = set()

        def add(row: SearchKeyRow) -> None:
            key_text, key_kind, rank_tier, entry_id, form_id, display_text = row
            normalized_key = key_text.strip()
            display = display_text.strip()
            if not normalized_key or not display:
                return
            normalized_row = (
                normalized_key,
                key_kind,
                rank_tier,
                entry_id,
                form_id,
                display,
            )
            if normalized_row not in seen:
                seen.add(normalized_row)
                rows.append(normalized_row)

        for entry in entries:
            entry_id = cast("int", entry["entry_id"])
            headword = str(entry["headword"])
            headword_key = _normalize_dictionary_key(
                headword,
                self._spelling_normalizer,
            )
            add(
                (
                    headword_key,
                    KEY_KIND_LEMMA,
                    RANK_TIER_EXACT_ENTRY,
                    entry_id,
                    None,
                    headword,
                )
            )
            for variant in cast("list[str]", entry["variants"]):
                variant_text = str(variant)
                variant_key = _normalize_dictionary_key(
                    variant_text,
                    self._spelling_normalizer,
                )
                add(
                    (
                        variant_key,
                        KEY_KIND_VARIANT,
                        RANK_TIER_EXACT_ENTRY,
                        entry_id,
                        None,
                        variant_text,
                    )
                )

        for form in forms:
            form_id = cast("int", form["form_id"])
            form_entry_id = cast("int | None", form["entry_id"])
            if form_entry_id is None:
                rank_tier = RANK_TIER_ORPHAN
            else:
                rank_tier = RANK_TIER_MORPH_LEMMA_STEM

            add(
                (
                    str(form["bt_key"]) or _normalize_morph_key(str(form["bt"])),
                    KEY_KIND_LEMMA,
                    rank_tier,
                    form_entry_id,
                    form_id,
                    str(form["bt"]),
                )
            )
            add(
                (
                    str(form["title_key"]) or _normalize_morph_key(str(form["title"])),
                    KEY_KIND_LEMMA,
                    rank_tier,
                    form_entry_id,
                    form_id,
                    str(form["title"]),
                )
            )
            add(
                (
                    str(form["stem_key"]) or _normalize_morph_key(str(form["stem"])),
                    KEY_KIND_STEM,
                    rank_tier,
                    form_entry_id,
                    form_id,
                    str(form["stem"]),
                )
            )

            form_rank_tier = (
                RANK_TIER_ORPHAN if form_entry_id is None else RANK_TIER_MORPH_FORM
            )
            add(
                (
                    str(form["form_key"]) or _normalize_morph_key(str(form["form"])),
                    KEY_KIND_FORM,
                    form_rank_tier,
                    form_entry_id,
                    form_id,
                    str(form["form"]),
                )
            )
            add(
                (
                    str(form["formi_key"]) or _normalize_morph_key(str(form["formi"])),
                    KEY_KIND_FORM,
                    form_rank_tier,
                    form_entry_id,
                    form_id,
                    str(form["formi"]),
                )
            )
        return rows

    def _insert_search_keys(
        self,
        connection: sqlite3.Connection,
        search_keys: list[SearchKeyRow],
    ) -> None:
        """
        Insert ranked search keys into ``lexicon_search_keys``.

        Args:
            connection: Open SQLite connection receiving key inserts.
            search_keys: Ranked key payload rows to insert.

        """
        connection.executemany(
            """
            INSERT INTO lexicon_search_keys (
                key_text,
                key_kind,
                rank_tier,
                entry_id,
                form_id,
                display_text
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            search_keys,
        )

    def _insert_build_meta(
        self,
        connection: sqlite3.Connection,
        *,
        built_at: str,
        forms_source_count: int,
        bt_entries_source_count: int,
    ) -> None:
        """
        Write build metadata rows for schema version, timestamp, and source sizes.

        Args:
            connection: Open SQLite connection receiving metadata inserts.

        Keyword Args:
            built_at: ISO-8601 UTC rebuild timestamp.
            forms_source_count: Source ``forms`` row count observed at rebuild.
            bt_entries_source_count: Source ``bt_entries`` row count observed.

        """
        connection.executemany(
            """
            INSERT INTO lexicon_build_meta (key, value)
            VALUES (?, ?)
            """,
            [
                (META_KEY_SCHEMA_VERSION, str(SCHEMA_VERSION)),
                (META_KEY_BUILT_AT, built_at),
                (META_KEY_FORMS_SOURCE_COUNT, str(forms_source_count)),
                (META_KEY_BT_ENTRIES_SOURCE_COUNT, str(bt_entries_source_count)),
            ],
        )


def read_lexicon_build_meta(connection: sqlite3.Connection) -> LexiconBuildMeta | None:
    """
    Read persisted lexicon build metadata from one SQLite connection.

    Args:
        connection: Open SQLite connection with ``lexicon_build_meta`` rows.

    Returns:
        Parsed build metadata, or ``None`` when metadata rows are absent.

    """
    try:
        rows = connection.execute(
            "SELECT key, value FROM lexicon_build_meta"
        ).fetchall()
    except sqlite3.OperationalError:
        return None

    values = {str(row[0]): str(row[1]) for row in rows}
    required = (
        META_KEY_SCHEMA_VERSION,
        META_KEY_BUILT_AT,
        META_KEY_FORMS_SOURCE_COUNT,
        META_KEY_BT_ENTRIES_SOURCE_COUNT,
    )
    if not all(key in values for key in required):
        return None

    return LexiconBuildMeta(
        schema_version=int(values[META_KEY_SCHEMA_VERSION]),
        built_at=values[META_KEY_BUILT_AT],
        forms_source_count=int(values[META_KEY_FORMS_SOURCE_COUNT]),
        bt_entries_source_count=int(values[META_KEY_BT_ENTRIES_SOURCE_COUNT]),
    )


def check_lexicon_staleness(db_path: Path) -> LexiconStalenessReport:
    """
    Compare stored lexicon build metadata against current source table sizes.

    Args:
        db_path: Path to ``morphology.sqlite3`` containing source and lexicon tables.

    Returns:
        Staleness report describing whether ``lexicon build`` should be rerun.

    """
    resolved_path = db_path.expanduser().resolve()
    with sqlite3.connect(str(resolved_path)) as connection:
        current_forms_count = _count_table_rows(connection, "forms")
        current_bt_entries_count = _count_table_rows(connection, "bt_entries")
        meta = read_lexicon_build_meta(connection)

    if meta is None:
        return LexiconStalenessReport(
            is_stale=True,
            reason="Lexicon read-model has not been built yet.",
            meta=None,
            current_forms_count=current_forms_count,
            current_bt_entries_count=current_bt_entries_count,
        )

    if meta.schema_version != SCHEMA_VERSION:
        return LexiconStalenessReport(
            is_stale=True,
            reason=(
                "Lexicon schema version changed; rebuild to refresh read-model tables."
            ),
            meta=meta,
            current_forms_count=current_forms_count,
            current_bt_entries_count=current_bt_entries_count,
        )

    if meta.forms_source_count != current_forms_count:
        return LexiconStalenessReport(
            is_stale=True,
            reason="Morphology `forms` table changed since the last lexicon build.",
            meta=meta,
            current_forms_count=current_forms_count,
            current_bt_entries_count=current_bt_entries_count,
        )

    if meta.bt_entries_source_count != current_bt_entries_count:
        return LexiconStalenessReport(
            is_stale=True,
            reason=(
                "Dictionary `bt_*` tables changed since the last lexicon build."
            ),
            meta=meta,
            current_forms_count=current_forms_count,
            current_bt_entries_count=current_bt_entries_count,
        )

    return LexiconStalenessReport(
        is_stale=False,
        reason="Lexicon read-model matches current source table sizes.",
        meta=meta,
        current_forms_count=current_forms_count,
        current_bt_entries_count=current_bt_entries_count,
    )


def _count_table_rows(connection: sqlite3.Connection, table_name: str) -> int:
    """
    Count rows in one known source table when the table exists.

    Args:
        connection: Open SQLite connection to inspect.
        table_name: Target source table name.

    Returns:
        Row count, or ``0`` when the table is missing.

    Raises:
        ValueError: ``table_name`` is not an allowed staleness source table.

    """
    if table_name not in _STALENESS_SOURCE_TABLES:
        msg = f"Unsupported staleness source table: {table_name}"
        raise ValueError(msg)
    try:
        row = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()  # noqa: S608
    except sqlite3.OperationalError:
        return 0
    if row is None:
        return 0
    return int(row[0])


def rebuild_lexicon(db_path: Path) -> BuildReport:
    """
    Rebuild lexicon read-model tables in the target morphology database.

    Args:
        db_path: Path to ``morphology.sqlite3`` containing ``forms`` and ``bt_*``.

    Returns:
        Build summary report for the completed rebuild.

    """
    return LexiconBuilder(db_path).rebuild()

