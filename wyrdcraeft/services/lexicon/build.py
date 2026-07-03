"""Lexicon read-model builder from morphology and dictionary source tables."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final, Protocol, cast

from wyrdcraeft.db.runtime import create_engine as create_sqlalchemy_engine
from wyrdcraeft.models.lexicon_build import (
    BuildCounterUpdated,
    BuildLog,
    BuildStageProgress,
    BuildStageStarted,
    CounterName,
    LexiconBuildEvent,
    LexiconBuildStage,
    LogLevel,
)
from wyrdcraeft.services.dictionary.bt_spelling import BTSpellingNormalizer
from wyrdcraeft.services.markup import normalize_old_english
from wyrdcraeft.services.morphology.text_utils import OENormalizer

from .form_decode import WORDCLASS_TO_BT_POS, infer_bt_pos_from_wordclasses
from .schema import (
    KEY_KIND_FORM,
    KEY_KIND_LEMMA,
    KEY_KIND_STEM,
    KEY_KIND_VARIANT,
    META_KEY_BT_ENTRIES_SOURCE_COUNT,
    META_KEY_BUILT_AT,
    META_KEY_FORMS_SOURCE_COUNT,
    META_KEY_SCHEMA_VERSION,
    RANK_TIER_EXACT_ENTRY,
    RANK_TIER_MORPH_FORM,
    RANK_TIER_MORPH_LEMMA_STEM,
    RANK_TIER_ORPHAN,
    SCHEMA_VERSION,
    TABLE_LEXICON_ENTRIES,
    TABLE_LEXICON_FORMS,
    create_lexicon_tables,
)

if TYPE_CHECKING:
    import threading
    from pathlib import Path

    from .build_runtime import LexiconBuildController

#: Allowed source tables for staleness row-count checks.
_STALENESS_SOURCE_TABLES: Final[tuple[str, ...]] = ("forms", "bt_entries")
#: Source tables required to rebuild ``lexicon_*`` rows.
_REQUIRED_SOURCE_TABLES: Final[tuple[str, ...]] = (
    *_STALENESS_SOURCE_TABLES,
    "bt_senses",
    "bt_variants",
)

#: Projected dictionary entry payload produced from ``bt_entries`` sources.
EntryPayload = dict[str, object]
#: Batched TEMP staging row for ``lexicon_forms`` inserts.
FormStageRow = tuple[
    int,
    int | None,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
]
#: Ranked search-key payload row for staged ``lexicon_search_keys`` inserts.
SearchKeyRow = tuple[str, str, int, int | None, int | None, str]

#: Callback receiving typed build events as they are emitted.
LexiconBuildEventSink = Callable[[LexiconBuildEvent], None]


class MissingLexiconSourceTablesError(RuntimeError):
    """Raised when rebuild prerequisites are absent from the SQLite schema."""


class LexiconBuildCancelledError(RuntimeError):
    """Raised when a cooperative lexicon-build cancellation request is honored."""


class LexiconBuildProgress(Protocol):
    """Progress callback surface used during lexicon rebuild."""

    def begin_stage(self, stage: LexiconBuildStage, *, total: int = 1) -> None:
        """
        Mark one rebuild stage active.

        Args:
            stage: Rebuild stage being entered.

        Keyword Args:
            total: Total work units for the stage.

        """

    def advance_stage(
        self,
        stage: LexiconBuildStage,
        *,
        completed: int | None = None,
        total: int | None = None,
        detail: str = "",
        force: bool = False,
    ) -> None:
        """
        Advance one rebuild stage.

        Args:
            stage: Rebuild stage being advanced.

        Keyword Args:
            completed: Explicit completed count for the stage.
            total: Explicit total count for the stage.
            detail: Optional suffix appended to the stage label.
            force: When ``True``, refresh even if row cadence would skip.

        """

    def finish_stage(self, stage: LexiconBuildStage) -> None:
        """
        Mark one rebuild stage complete.

        Args:
            stage: Rebuild stage that has completed.

        """


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
        pos_inferred: Dictionary entries whose POS was inferred from morphology.

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
    #: Dictionary entries whose POS was inferred from morphology.
    pos_inferred: int


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
        progress: Optional rebuild progress callback.
        event_sink: Optional typed build-event callback.
        cancel_event: Optional cooperative cancellation flag.
        runtime: Optional shared runtime controller owning SQLite interrupts.

    """

    #: Database file containing ``forms``, ``bt_*``, and target ``lexicon_*`` tables.
    _db_path: Path
    #: Spelling normalizer for dictionary headwords and variants.
    _spelling_normalizer: BTSpellingNormalizer
    #: Optional rebuild progress callback.
    _progress: LexiconBuildProgress | None
    #: Optional typed build-event callback.
    _event_sink: LexiconBuildEventSink | None
    #: Optional cooperative cancellation flag.
    _cancel_event: threading.Event | None
    #: Optional shared runtime controller for interrupt wiring.
    _runtime: LexiconBuildController | None
    #: Monotonic sequence number for emitted build events.
    _event_seq: int
    #: Last announced total for each stage, used to emit terminal stage progress.
    _stage_totals: dict[LexiconBuildStage, int]
    #: Row batch size for TEMP form staging inserts.
    _form_stage_batch_size: int = 25000
    #: Minimum staged form rows between high-volume stage log lines.
    _form_log_interval_rows: int = 500_000

    def __init__(
        self,
        db_path: Path,
        *,
        progress: LexiconBuildProgress | None = None,
        event_sink: LexiconBuildEventSink | None = None,
        cancel_event: threading.Event | None = None,
        runtime: LexiconBuildController | None = None,
    ) -> None:
        """
        Initialize a lexicon builder for one SQLite database.

        Args:
            db_path: Path to the canonical ``morphology.sqlite3`` database.

        Keyword Args:
            progress: Optional rebuild progress callback.
            event_sink: Optional typed build-event callback.
            cancel_event: Optional cooperative cancellation flag.
            runtime: Optional shared runtime controller for SQLite interrupts.

        """
        #: Database file containing source and target lexicon tables.
        self._db_path = db_path.expanduser().resolve()
        #: Spelling normalizer for dictionary headwords and variants.
        self._spelling_normalizer = BTSpellingNormalizer()
        #: Optional rebuild progress callback.
        self._progress = progress
        #: Optional typed build-event callback.
        self._event_sink = event_sink or (runtime.emit if runtime is not None else None)
        #: Optional cooperative cancellation flag.
        self._cancel_event = cancel_event or (
            runtime.cancel_event if runtime is not None else None
        )
        #: Optional shared runtime controller for interrupt wiring.
        self._runtime = runtime
        #: Monotonic sequence number for emitted build events.
        self._event_seq = 0
        #: Last announced total for each stage, used to emit terminal stage progress.
        self._stage_totals = {}

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

            Registers and clears the runtime interrupt callback when a runtime
            controller is supplied.

        """
        engine = create_sqlalchemy_engine(self._db_path)
        try:
            create_lexicon_tables(engine)
        finally:
            engine.dispose()

        with sqlite3.connect(str(self._db_path)) as connection:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            report: BuildReport
            if self._runtime is not None:
                self._runtime.set_interrupt_callback(connection.interrupt)
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._stage(
                    LexiconBuildStage.VERIFY_SOURCES,
                    lambda: self._ensure_required_sources(connection),
                )
                self._clear_lexicon_tables(connection)
                report = self._rebuild_into_connection(connection)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                if self._runtime is not None:
                    self._runtime.set_interrupt_callback(None)
        return report

    def _stage(self, stage: LexiconBuildStage, action: Callable[[], None]) -> None:
        """
        Run one rebuild step while updating optional progress output.

        Args:
            stage: Rebuild stage being executed.
            action: Zero-argument callable performing the stage work.

        """
        self._begin_stage(stage)
        action()
        self._finish_stage(stage)

    def _advance_stage(
        self,
        stage: LexiconBuildStage,
        *,
        completed: int,
        total: int,
        detail: str = "",
        current_item: str = "",
    ) -> None:
        """
        Advance optional rebuild progress for one loop iteration.

        Args:
            stage: Active rebuild stage.

        Keyword Args:
            completed: Completed work units in the stage.
            total: Total work units in the stage.
            detail: Optional suffix for the progress banner.
            current_item: Optional active item label for typed events.

        """
        self._check_cancel(stage=stage)
        if self._progress is not None:
            self._progress.advance_stage(
                stage,
                completed=completed,
                total=total,
                detail=detail,
                force=completed in {0, total},
            )
        self._emit_stage_progress(
            stage=stage,
            completed=completed,
            total=total,
            detail=detail,
            current_item=current_item,
        )
        self._check_cancel(stage=stage, current_item=current_item)

    def _begin_stage(
        self,
        stage: LexiconBuildStage,
        *,
        total: int = 1,
        detail: str = "",
    ) -> None:
        """
        Mark one stage active across progress and typed event surfaces.

        Args:
            stage: Rebuild stage being entered.

        Keyword Args:
            total: Total work units expected for the stage.
            detail: Optional detail emitted with the stage start.

        """
        if self._progress is not None:
            self._progress.begin_stage(stage, total=total)
        stage_total = max(total, 1)
        self._stage_totals[stage] = stage_total
        self._emit_event(
            BuildStageStarted(
                seq=self._next_event_seq(),
                at=self._now(),
                stage=stage,
                total=stage_total,
                detail=detail,
            )
        )
        self._emit_log(stage=stage, message=f"stage started: {stage.value}")
        self._check_cancel(stage=stage)

    def _finish_stage(self, stage: LexiconBuildStage) -> None:
        """
        Mark one stage complete across progress and log surfaces.

        Args:
            stage: Rebuild stage that completed.

        """
        if self._progress is not None:
            self._progress.finish_stage(stage)
        total = self._stage_totals.pop(stage, 1)
        self._emit_stage_progress(
            stage=stage,
            completed=total,
            total=total,
        )
        self._emit_log(stage=stage, message=f"stage finished: {stage.value}")

    def _emit_event(self, event: LexiconBuildEvent) -> None:
        """
        Send one typed build event to the configured sink when present.

        Args:
            event: Build event to emit.

        """
        if self._event_sink is not None:
            self._event_sink(event)

    def _emit_stage_progress(
        self,
        *,
        stage: LexiconBuildStage,
        completed: int,
        total: int,
        detail: str = "",
        current_item: str = "",
    ) -> None:
        """
        Emit one typed stage-progress event.

        Keyword Args:
            stage: Stage being advanced.
            completed: Completed work units so far.
            total: Total work units expected for the stage.
            detail: Optional human-readable progress detail.
            current_item: Optional active item label.

        """
        self._emit_event(
            BuildStageProgress(
                seq=self._next_event_seq(),
                at=self._now(),
                stage=stage,
                completed=completed,
                total=max(total, 1),
                detail=detail,
                current_item=current_item,
            )
        )

    def _emit_log(
        self,
        *,
        stage: LexiconBuildStage | None,
        message: str,
        level: LogLevel = "info",
        current_item: str = "",
        counts: tuple[int | None, int | None] | None = None,
    ) -> None:
        """
        Emit one structured log event.

        Keyword Args:
            stage: Stage associated with the log line when known.
            message: Human-readable log message.
            level: Structured log severity.
            current_item: Optional active item label.
            counts: Optional ``(processed, total)`` pair tied to the log.

        """
        processed, total = (None, None) if counts is None else counts
        self._emit_event(
            BuildLog(
                seq=self._next_event_seq(),
                at=self._now(),
                stage=stage,
                level=level,
                message=message,
                current_item=current_item,
                processed=processed,
                total=total,
            )
        )

    def _emit_counter(
        self,
        *,
        counter: CounterName,
        value: int,
        stage: LexiconBuildStage | None = None,
    ) -> None:
        """
        Emit one dedicated counter update event.

        Keyword Args:
            counter: Counter being updated.
            value: New counter value.
            stage: Stage associated with the counter update when known.

        """
        self._emit_event(
            BuildCounterUpdated(
                seq=self._next_event_seq(),
                at=self._now(),
                counter=counter,
                value=value,
                stage=stage,
            )
        )

    def _check_cancel(
        self,
        *,
        stage: LexiconBuildStage,
        current_item: str = "",
    ) -> None:
        """
        Raise the cooperative cancellation error when cancellation is requested.

        Keyword Args:
            stage: Stage currently executing.
            current_item: Optional active item label for the cancellation log.

        Raises:
            LexiconBuildCancelledError: Cooperative cancellation was requested.

        """
        if self._cancel_event is None or not self._cancel_event.is_set():
            return
        self._emit_log(
            stage=stage,
            level="warning",
            message="cancellation requested",
            current_item=current_item,
        )
        msg = "Lexicon build cancelled."
        raise LexiconBuildCancelledError(msg)

    def _next_event_seq(self) -> int:
        """
        Return the next typed-event sequence number.

        Returns:
            Next monotonic typed-event sequence number.

        """
        self._event_seq += 1
        return self._event_seq

    def _now(self) -> str:
        """
        Return the current UTC timestamp in ISO-8601 ``Z`` form.

        Returns:
            Current UTC timestamp formatted for build events.

        """
        return (
            datetime.now(UTC)
            .replace(microsecond=0)
            .isoformat()
            .replace(
                "+00:00",
                "Z",
            )
        )

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
        built_at = (
            datetime.now(UTC)
            .replace(microsecond=0)
            .isoformat()
            .replace(
                "+00:00",
                "Z",
            )
        )

        pos_inferred = self._infer_missing_pos(connection)
        entries = self._load_entry_payloads(connection)
        self._insert_entries(connection, entries)

        forms_written = self._load_form_payloads(connection, entries)
        self._insert_forms(connection, forms_written)

        staged_search_keys = self._build_search_keys(connection, entries, forms_written)
        search_keys_written = self._insert_search_keys(connection, staged_search_keys)

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
            forms_written=forms_written,
            search_keys_written=search_keys_written,
            pos_inferred=pos_inferred,
        )

    def _infer_missing_pos(self, connection: sqlite3.Connection) -> int:
        """
        Fill empty dictionary POS values from unambiguous morphology wordclasses.

        Args:
            connection: Open SQLite connection containing ``bt_entries`` and ``forms``.

        Returns:
            Number of ``bt_entries`` rows updated with inferred POS labels.

        Side Effects:
            Updates ``bt_entries.pos`` for entries with empty POS and one clear
            morphology wordclass.

        """
        rows = connection.execute(
            """
            SELECT id, norm_key
            FROM bt_entries
            WHERE TRIM(COALESCE(pos, '')) = ''
            ORDER BY id ASC
            """
        ).fetchall()
        total = len(rows) or 1
        self._begin_stage(LexiconBuildStage.INFER_POS, total=total)

        updated = 0
        for index, row in enumerate(rows, start=1):
            self._check_cancel(
                stage=LexiconBuildStage.INFER_POS,
                current_item=str(row["norm_key"]),
            )
            norm_key = str(row["norm_key"])
            wordclass_rows = connection.execute(
                """
                SELECT DISTINCT LOWER(TRIM(wordclass)) AS wordclass
                FROM forms
                WHERE bt_key = ?
                   OR title_key = ?
                   OR stem_key = ?
                """,
                (norm_key, norm_key, norm_key),
            ).fetchall()
            inferred_pos = infer_bt_pos_from_wordclasses(
                {str(wordclass_row["wordclass"]) for wordclass_row in wordclass_rows}
            )
            if inferred_pos is not None:
                connection.execute(
                    "UPDATE bt_entries SET pos = ? WHERE id = ?",
                    (inferred_pos, int(row["id"])),
                )
                updated += 1
            self._advance_stage(
                LexiconBuildStage.INFER_POS,
                completed=index,
                total=total,
                detail=f"updated={updated}",
            )

        self._emit_counter(
            counter="pos_inferred",
            value=updated,
            stage=LexiconBuildStage.INFER_POS,
        )
        self._finish_stage(LexiconBuildStage.INFER_POS)
        return updated

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
        self._emit_log(
            stage=LexiconBuildStage.LOAD_ENTRIES,
            message="loading senses",
        )
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

        total_entries = len(entry_rows) or 1
        self._begin_stage(
            LexiconBuildStage.LOAD_ENTRIES,
            total=total_entries,
        )

        payloads: list[EntryPayload] = []
        for index, row in enumerate(entry_rows, start=1):
            self._check_cancel(
                stage=LexiconBuildStage.LOAD_ENTRIES,
                current_item=str(row["norm_key"]),
            )
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
            self._advance_stage(
                LexiconBuildStage.LOAD_ENTRIES,
                completed=index,
                total=total_entries,
            )
        self._finish_stage(LexiconBuildStage.LOAD_ENTRIES)
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
        self._begin_stage(
            LexiconBuildStage.INSERT_ENTRIES,
            total=max(len(entries), 1),
            detail="preparing rows",
        )
        self._advance_stage(
            LexiconBuildStage.INSERT_ENTRIES,
            completed=0,
            total=max(len(entries), 1),
            detail="preparing rows",
        )
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
        self._advance_stage(
            LexiconBuildStage.INSERT_ENTRIES,
            completed=max(len(entries), 1),
            total=max(len(entries), 1),
        )
        self._emit_counter(
            counter="entries_written",
            value=len(entries),
            stage=LexiconBuildStage.INSERT_ENTRIES,
        )
        self._finish_stage(LexiconBuildStage.INSERT_ENTRIES)

    def _load_form_payloads(
        self,
        connection: sqlite3.Connection,
        entries: list[EntryPayload],
    ) -> int:
        """
        Stream ``forms`` rows into a TEMP staging table for final insertion.

        Args:
            connection: Open SQLite connection queried for ``forms`` rows.
            entries: Projected dictionary entry payloads used for joining.

        Returns:
            Number of staged form rows ready for final insertion.

        """
        count_row = connection.execute("SELECT COUNT(*) FROM forms").fetchone()
        total_forms = int(count_row[0]) if count_row is not None else 0
        total_forms = total_forms or 1
        self._begin_stage(
            LexiconBuildStage.LOAD_FORMS,
            total=total_forms,
            detail="fetching forms",
        )
        connection.execute("DROP TABLE IF EXISTS temp_lexicon_forms_stage")
        connection.execute(
            """
            CREATE TEMP TABLE temp_lexicon_forms_stage (
                form_id INTEGER PRIMARY KEY,
                entry_id INTEGER,
                bt TEXT NOT NULL,
                title TEXT NOT NULL,
                stem TEXT NOT NULL,
                form TEXT NOT NULL,
                formi TEXT NOT NULL,
                wordclass TEXT NOT NULL,
                function TEXT NOT NULL,
                probability TEXT NOT NULL,
                class1 TEXT NOT NULL,
                class2 TEXT NOT NULL,
                class3 TEXT NOT NULL,
                paradigm TEXT NOT NULL
            )
            """
        )

        entry_ids_by_norm_pos: dict[tuple[str, str], list[int]] = {}
        entry_ids_by_norm: dict[str, list[int]] = {}
        for entry in entries:
            entry_id = cast("int", entry["entry_id"])
            norm_key = str(entry["norm_key"])
            pos = str(entry["pos"])
            entry_ids_by_norm_pos.setdefault((norm_key, pos), []).append(entry_id)
            entry_ids_by_norm.setdefault(norm_key, []).append(entry_id)

        cursor = connection.execute(
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
                paradigm,
                bt_key,
                title_key,
                stem_key,
                form_key,
                formi_key
            FROM forms
            ORDER BY id ASC
            """
        )

        chunk: list[FormStageRow] = []
        last_logged_row = 0
        staged_rows = 0
        for index, row in enumerate(cursor, start=1):
            current_item = str(row["BT"])
            self._check_cancel(
                stage=LexiconBuildStage.LOAD_FORMS,
                current_item=current_item,
            )
            bt_pos = WORDCLASS_TO_BT_POS.get(str(row["wordclass"]).strip().lower(), "")
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
            chunk.append(
                (
                    int(row["id"]),
                    matched_entry_id,
                    str(row["BT"]),
                    str(row["title"]),
                    str(row["stem"]),
                    str(row["form"]),
                    str(row["formi"]),
                    str(row["wordclass"]),
                    str(row["function"]),
                    str(row["probability"]),
                    str(row["class1"]),
                    str(row["class2"]),
                    str(row["class3"]),
                    str(row["paradigm"]),
                )
            )
            staged_rows = index
            should_emit_heartbeat = (
                index in {1, total_forms} or len(chunk) >= self._form_stage_batch_size
            )
            if len(chunk) >= self._form_stage_batch_size:
                connection.executemany(
                    """
                    INSERT INTO temp_lexicon_forms_stage VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                    """,
                    chunk,
                )
                if (
                    index in {1, total_forms}
                    or index - last_logged_row >= self._form_log_interval_rows
                ):
                    self._emit_log(
                        stage=LexiconBuildStage.LOAD_FORMS,
                        message="staging form rows",
                        current_item=current_item,
                        counts=(index, total_forms),
                    )
                    last_logged_row = index
                chunk.clear()
            if should_emit_heartbeat:
                self._advance_stage(
                    LexiconBuildStage.LOAD_FORMS,
                    completed=index,
                    total=total_forms,
                    current_item=current_item,
                )
        if chunk:
            connection.executemany(
                """
                INSERT INTO temp_lexicon_forms_stage VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                chunk,
            )
            if staged_rows != last_logged_row:
                self._emit_log(
                    stage=LexiconBuildStage.LOAD_FORMS,
                    message="staging form rows",
                    current_item=chunk[-1][2],
                    counts=(staged_rows, total_forms),
                )
        self._finish_stage(LexiconBuildStage.LOAD_FORMS)
        return int(count_row[0]) if count_row is not None else 0

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
        forms_count: int,
    ) -> None:
        """
        Insert projected morphology rows into ``lexicon_forms``.

        Args:
            connection: Open SQLite connection receiving form inserts.
            forms_count: Number of staged form payload rows to insert.

        """
        total = max(forms_count, 1)
        self._begin_stage(
            LexiconBuildStage.INSERT_FORMS,
            total=total,
            detail="inserting rows",
        )
        self._advance_stage(
            LexiconBuildStage.INSERT_FORMS,
            completed=0,
            total=total,
            detail="inserting rows",
        )
        last_form_id = 0
        inserted = 0
        while inserted < forms_count:
            self._check_cancel(stage=LexiconBuildStage.INSERT_FORMS)
            prev_changes = connection.total_changes
            connection.execute(
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
                    class3,
                    paradigm
                )
                SELECT
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
                    class3,
                    paradigm
                FROM temp_lexicon_forms_stage
                WHERE form_id > ?
                ORDER BY form_id
                LIMIT ?
                """,
                (last_form_id, self._form_stage_batch_size),
            )
            batch_inserted = connection.total_changes - prev_changes
            if batch_inserted == 0:
                break
            row = connection.execute(
                """
                SELECT MAX(form_id)
                FROM lexicon_forms
                WHERE form_id > ?
                """,
                (last_form_id,),
            ).fetchone()
            if row is None or row[0] is None:
                break
            last_form_id = int(row[0])
            inserted += batch_inserted
            self._advance_stage(
                LexiconBuildStage.INSERT_FORMS,
                completed=inserted,
                total=total,
                detail="inserting rows",
            )
        final_completed = max(inserted, 1) if forms_count == 0 else inserted
        self._advance_stage(
            LexiconBuildStage.INSERT_FORMS,
            completed=final_completed,
            total=total,
        )
        self._emit_counter(
            counter="forms_written",
            value=forms_count,
            stage=LexiconBuildStage.INSERT_FORMS,
        )
        self._finish_stage(LexiconBuildStage.INSERT_FORMS)

    def _build_search_keys(
        self,
        connection: sqlite3.Connection,
        entries: list[EntryPayload],
        forms_count: int,
    ) -> int:
        """
        Stage ranked search-key rows for dictionary and morphology lookups.

        Args:
            connection: Open SQLite connection queried for inserted form rows.
            entries: Projected dictionary entry payloads.
            forms_count: Number of inserted morphology form rows.

        Returns:
            Number of staged candidate rows for lexicon insertion.

        """
        total = max(len(entries) + forms_count, 1)
        self._begin_stage(
            LexiconBuildStage.BUILD_SEARCH_KEYS,
            total=total,
        )
        connection.execute("DROP TABLE IF EXISTS temp_lexicon_search_keys_stage")
        connection.execute(
            """
            CREATE TEMP TABLE temp_lexicon_search_keys_stage (
                key_text TEXT NOT NULL,
                key_kind TEXT NOT NULL,
                rank_tier INTEGER NOT NULL,
                entry_id INTEGER,
                form_id INTEGER,
                display_text TEXT NOT NULL
            )
            """
        )
        progress_index = 0
        progress_total = total
        staged_count = 0

        def add(row: SearchKeyRow) -> None:
            nonlocal staged_count
            key_text, key_kind, rank_tier, entry_id, form_id, display_text = row
            normalized_key = key_text.strip()
            display = display_text.strip()
            if not normalized_key or not display:
                return
            connection.execute(
                """
                INSERT INTO temp_lexicon_search_keys_stage (
                    key_text,
                    key_kind,
                    rank_tier,
                    entry_id,
                    form_id,
                    display_text
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    normalized_key,
                    key_kind,
                    rank_tier,
                    entry_id,
                    form_id,
                    display,
                ),
            )
            staged_count += 1

        for entry in entries:
            progress_index += 1
            self._check_cancel(
                stage=LexiconBuildStage.BUILD_SEARCH_KEYS,
                current_item=str(entry["headword"]),
            )
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

            self._advance_stage(
                LexiconBuildStage.BUILD_SEARCH_KEYS,
                completed=progress_index,
                total=progress_total,
            )

        form_cursor = connection.execute(
            """
            SELECT
                lf.form_id,
                lf.entry_id,
                lf.bt,
                lf.title,
                lf.stem,
                lf.form,
                lf.formi,
                f.bt_key,
                f.title_key,
                f.stem_key,
                f.form_key,
                f.formi_key
            FROM lexicon_forms AS lf
            JOIN forms AS f ON f.id = lf.form_id
            ORDER BY lf.form_id ASC
            """
        )
        for form in form_cursor:
            progress_index += 1
            self._check_cancel(
                stage=LexiconBuildStage.BUILD_SEARCH_KEYS,
                current_item=str(form["form"]),
            )
            form_id = int(form["form_id"])
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
            self._advance_stage(
                LexiconBuildStage.BUILD_SEARCH_KEYS,
                completed=progress_index,
                total=progress_total,
            )
        self._finish_stage(LexiconBuildStage.BUILD_SEARCH_KEYS)
        return staged_count

    def _insert_search_keys(
        self,
        connection: sqlite3.Connection,
        staged_count: int,
    ) -> int:
        """
        Insert staged ranked search keys into ``lexicon_search_keys``.

        Args:
            connection: Open SQLite connection receiving key inserts.
            staged_count: Number of candidate rows staged in the TEMP table.

        Returns:
            Number of rows written to ``lexicon_search_keys``.

        """
        self._begin_stage(
            LexiconBuildStage.INSERT_SEARCH_KEYS,
            total=max(staged_count, 1),
            detail="writing keys",
        )
        self._advance_stage(
            LexiconBuildStage.INSERT_SEARCH_KEYS,
            completed=0,
            total=max(staged_count, 1),
            detail="writing keys",
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO lexicon_search_keys (
                key_text,
                key_kind,
                rank_tier,
                entry_id,
                form_id,
                display_text
            )
            SELECT
                key_text,
                key_kind,
                rank_tier,
                entry_id,
                form_id,
                display_text
            FROM temp_lexicon_search_keys_stage
            ORDER BY rowid ASC
            """,
        )
        written = int(
            connection.execute("SELECT COUNT(*) FROM lexicon_search_keys").fetchone()[0]
        )
        self._advance_stage(
            LexiconBuildStage.INSERT_SEARCH_KEYS,
            completed=max(staged_count, 1),
            total=max(staged_count, 1),
        )
        self._emit_counter(
            counter="search_keys_written",
            value=written,
            stage=LexiconBuildStage.INSERT_SEARCH_KEYS,
        )
        self._finish_stage(LexiconBuildStage.INSERT_SEARCH_KEYS)
        return written

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
        self._begin_stage(LexiconBuildStage.WRITE_META)
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
        self._finish_stage(LexiconBuildStage.WRITE_META)


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


def lexicon_read_model_has_data(connection: sqlite3.Connection) -> bool:
    """
    Return whether one database already contains populated lexicon read-model rows.

    Args:
        connection: Open SQLite connection to inspect.

    Returns:
        ``True`` when build metadata or non-empty lexicon tables already exist.

    """
    if read_lexicon_build_meta(connection) is not None:
        return True
    for table_name in (TABLE_LEXICON_ENTRIES, TABLE_LEXICON_FORMS):
        try:
            row = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()  # noqa: S608
        except sqlite3.OperationalError:
            continue
        if row is not None and int(row[0]) > 0:
            return True
    return False


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
            reason=("Dictionary `bt_*` tables changed since the last lexicon build."),
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


def rebuild_lexicon(
    db_path: Path,
    *,
    progress: LexiconBuildProgress | None = None,
    event_sink: LexiconBuildEventSink | None = None,
    cancel_event: threading.Event | None = None,
    runtime: LexiconBuildController | None = None,
) -> BuildReport:
    """
    Rebuild lexicon read-model tables in the target morphology database.

    Args:
        db_path: Path to ``morphology.sqlite3`` containing ``forms`` and ``bt_*``.

    Keyword Args:
        progress: Optional rebuild progress callback.
        event_sink: Optional typed build-event callback.
        cancel_event: Optional cooperative cancellation flag.
        runtime: Optional shared runtime controller for SQLite interrupts.

    Returns:
        Build summary report for the completed rebuild.

    """
    return LexiconBuilder(
        db_path,
        progress=progress,
        event_sink=event_sink,
        cancel_event=cancel_event,
        runtime=runtime,
    ).rebuild()
