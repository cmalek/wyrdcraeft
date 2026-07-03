"""Lexicon read-model builder from morphology and dictionary source tables."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Final, Protocol, cast

from sqlalchemy import delete, func, insert, select, text, update
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import OperationalError

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
from wyrdcraeft.models.sqlalchemy import (
    BTEntry,
    BTSense,
    BTVariant,
    Form,
    LexiconEntry,
    LexiconForm,
    LexiconSearchKey,
)
from wyrdcraeft.models.sqlalchemy import (
    LexiconBuildMeta as LexiconBuildMetaTable,
)
from wyrdcraeft.services.dictionary.bt_spelling import BTSpellingNormalizer
from wyrdcraeft.services.dictionary.normalized_title_join import (
    NormalizedTitleJoinIndex,
)
from wyrdcraeft.services.markup import normalize_old_english
from wyrdcraeft.services.morphology.text_utils import OENormalizer

from .form_decode import WORDCLASS_TO_BT_POS, infer_bt_pos_from_wordclasses
from .schema import (
    KEY_KIND_FORM,
    KEY_KIND_LEMMA,
    KEY_KIND_STEM,
    KEY_KIND_VARIANT,
    LEXICON_TABLE_NAMES,
    META_KEY_BT_ENTRIES_SOURCE_COUNT,
    META_KEY_BUILT_AT,
    META_KEY_FORMS_SOURCE_COUNT,
    RANK_TIER_EXACT_ENTRY,
    RANK_TIER_MORPH_FORM,
    RANK_TIER_MORPH_LEMMA_STEM,
    RANK_TIER_ORPHAN,
)

if TYPE_CHECKING:
    import threading

    from .build_runtime import LexiconBuildController

#: Supported database targets for lexicon helper reads.
DbTarget = Engine | Connection | Path

#: Allowed source tables for staleness row-count checks.
_STALENESS_SOURCE_TABLES: Final[tuple[str, ...]] = ("forms", "bt_entries")
#: Source tables required to rebuild ``lexicon_*`` rows.
_REQUIRED_SOURCE_TABLES: Final[tuple[str, ...]] = (
    *_STALENESS_SOURCE_TABLES,
    "bt_senses",
    "bt_variants",
)
#: Lexicon read-model tables that Alembic must create before rebuild.
_REQUIRED_LEXICON_TABLES: Final[tuple[str, ...]] = LEXICON_TABLE_NAMES

#: Projected dictionary entry payload produced from ``bt_entries`` sources.
EntryPayload = dict[str, object]
#: Ranked search-key payload row for ``lexicon_search_keys`` inserts.
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
        built_at: UTC timestamp (ISO-8601) of the last rebuild.
        forms_source_count: ``forms`` row count observed during rebuild.
        bt_entries_source_count: ``bt_entries`` row count observed during rebuild.

    """

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
        built_at: UTC timestamp (ISO-8601) recorded for this rebuild.
        forms_source_count: Source ``forms`` row count consumed by rebuild.
        bt_entries_source_count: Source ``bt_entries`` row count consumed.
        entries_written: ``lexicon_entries`` rows written.
        forms_written: ``lexicon_forms`` rows written.
        search_keys_written: ``lexicon_search_keys`` rows written.
        pos_inferred: Dictionary entries whose POS was inferred from morphology.

    """

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
        db_path: Path to the canonical ``wyrdcraeft.sqlite3`` database.
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
    #: Row batch size for lexicon form bulk inserts.
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
            db_path: Path to the canonical ``wyrdcraeft.sqlite3`` database.

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
            Truncates all rows in ``lexicon_*`` tables within one transaction.
            Table DDL is owned by Alembic; rebuild does not drop or recreate tables.

            Registers and clears the runtime interrupt callback when a runtime
            controller is supplied.

        """
        engine = create_sqlalchemy_engine(self._db_path)
        try:
            with engine.begin() as connection:
                connection.execute(text("PRAGMA foreign_keys = ON"))
                if self._runtime is not None:
                    dbapi_connection = connection.connection.dbapi_connection
                    if dbapi_connection is not None:
                        self._runtime.set_interrupt_callback(dbapi_connection.interrupt)
                try:
                    self._stage(
                        LexiconBuildStage.VERIFY_SOURCES,
                        lambda: self._ensure_required_sources(connection),
                    )
                    self._clear_lexicon_tables(connection)
                    report = self._rebuild_into_connection(connection)
                finally:
                    if self._runtime is not None:
                        self._runtime.set_interrupt_callback(None)
        finally:
            engine.dispose()
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

    def _ensure_required_sources(self, connection: Connection) -> None:
        """
        Raise an error when source tables needed by rebuild are missing.

        Args:
            connection: Open SQLAlchemy connection to inspect for source tables.

        Raises:
            MissingLexiconSourceTablesError: Required source or lexicon tables are
                missing.

        """
        rows = connection.execute(
            text(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            )
        ).fetchall()
        available = {str(row[0]) for row in rows}
        missing_sources = sorted(set(_REQUIRED_SOURCE_TABLES) - available)
        if missing_sources:
            missing_csv = ", ".join(missing_sources)
            msg = f"Lexicon rebuild requires source tables: {missing_csv}"
            raise MissingLexiconSourceTablesError(msg)
        missing_lexicon = sorted(set(_REQUIRED_LEXICON_TABLES) - available)
        if missing_lexicon:
            missing_csv = ", ".join(missing_lexicon)
            msg = (
                "Lexicon rebuild requires Alembic-managed lexicon tables: "
                f"{missing_csv}. Run startup database readiness or "
                "`wyrdcraeft` once so migrations apply before `lexicon build`."
            )
            raise MissingLexiconSourceTablesError(msg)

    def _clear_lexicon_tables(self, connection: Connection) -> None:
        """
        Truncate prior ``lexicon_*`` rows while preserving table DDL and sources.

        Args:
            connection: Open SQLAlchemy connection receiving the delete statements.

        Side Effects:
            Deletes all rows from ``lexicon_*`` tables without dropping them.

        """
        connection.execute(delete(LexiconSearchKey))
        connection.execute(delete(LexiconForm))
        connection.execute(delete(LexiconEntry))
        connection.execute(delete(LexiconBuildMetaTable))

    def _rebuild_into_connection(self, connection: Connection) -> BuildReport:
        """
        Insert derived lexicon entries, forms, keys, and build metadata.

        Args:
            connection: Open SQLAlchemy connection with source and lexicon tables.

        Returns:
            Build report for inserted entry, form, and search-key rows.

        """
        forms_source_count = int(
            connection.execute(select(func.count()).select_from(Form)).scalar_one()
        )
        bt_entries_source_count = int(
            connection.execute(select(func.count()).select_from(BTEntry)).scalar_one()
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

        form_batches, forms_written = self._load_form_payloads(connection, entries)
        self._insert_forms(connection, form_batches, forms_written)

        search_key_rows = self._build_search_keys(connection, entries, forms_written)
        search_keys_written = self._insert_search_keys(connection, search_key_rows)

        self._insert_build_meta(
            connection,
            built_at=built_at,
            forms_source_count=forms_source_count,
            bt_entries_source_count=bt_entries_source_count,
        )
        return BuildReport(
            built_at=built_at,
            forms_source_count=forms_source_count,
            bt_entries_source_count=bt_entries_source_count,
            entries_written=len(entries),
            forms_written=forms_written,
            search_keys_written=search_keys_written,
            pos_inferred=pos_inferred,
        )

    def _infer_missing_pos(self, connection: Connection) -> int:
        """
        Fill empty dictionary POS values from unambiguous morphology wordclasses.

        Args:
            connection: Open SQLAlchemy connection containing source tables.

        Returns:
            Number of ``bt_entries`` rows updated with inferred POS labels.

        Side Effects:
            Updates ``bt_entries.pos`` for entries with empty POS and one clear
            morphology wordclass.

        """
        rows = connection.execute(
            select(BTEntry.id, BTEntry.norm_key, BTEntry.normalized_title)
            .where(func.trim(func.coalesce(BTEntry.pos, "")) == "")
            .order_by(BTEntry.id.asc())
        ).fetchall()
        total = len(rows) or 1
        self._begin_stage(LexiconBuildStage.INFER_POS, total=total)

        updated = 0
        for index, row in enumerate(rows, start=1):
            self._check_cancel(
                stage=LexiconBuildStage.INFER_POS,
                current_item=str(row.normalized_title),
            )
            normalized_title = str(row.normalized_title)
            wordclass_rows = connection.execute(
                select(func.lower(func.trim(Form.wordclass)).label("wordclass"))
                .where(Form.normalized_title == normalized_title)
                .distinct()
            ).fetchall()
            inferred_pos = infer_bt_pos_from_wordclasses(
                {str(wordclass_row.wordclass) for wordclass_row in wordclass_rows}
            )
            if inferred_pos is not None:
                connection.execute(
                    update(BTEntry)
                    .where(BTEntry.id == int(row.id))
                    .values(pos=inferred_pos)
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
        connection: Connection,
    ) -> list[EntryPayload]:
        """
        Load and project dictionary rows into ``lexicon_entries`` payloads.

        Args:
            connection: Open SQLAlchemy connection queried for ``bt_*`` rows.

        Returns:
            Projected dictionary entry payloads for lexicon inserts.

        """
        self._emit_log(
            stage=LexiconBuildStage.LOAD_ENTRIES,
            message="loading senses",
        )
        sense_rows = connection.execute(
            select(
                BTSense.entry_id,
                BTSense.sense_label,
                BTSense.gloss_en,
                BTSense.order_index,
            ).order_by(
                BTSense.entry_id.asc(),
                BTSense.order_index.asc(),
                BTSense.id.asc(),
            )
        ).fetchall()
        senses_by_entry: dict[int, list[dict[str, object]]] = {}
        for sense_row in sense_rows:
            entry_id = int(sense_row.entry_id)
            senses_by_entry.setdefault(entry_id, []).append(
                {
                    "sense_label": str(sense_row.sense_label),
                    "gloss_en": str(sense_row.gloss_en),
                    "order_index": int(sense_row.order_index),
                }
            )

        variant_rows = connection.execute(
            select(BTVariant.entry_id, BTVariant.spelling_macronized).order_by(
                BTVariant.entry_id.asc(),
                BTVariant.spelling_raw.asc(),
            )
        ).fetchall()
        variants_by_entry: dict[int, list[str]] = {}
        for variant_row in variant_rows:
            entry_id = int(variant_row.entry_id)
            variant = str(variant_row.spelling_macronized).strip()
            if not variant:
                continue
            variants = variants_by_entry.setdefault(entry_id, [])
            if variant not in variants:
                variants.append(variant)

        entry_rows = connection.execute(
            select(
                BTEntry.id,
                BTEntry.norm_key,
                BTEntry.normalized_title,
                BTEntry.pos,
                BTEntry.headword_macronized,
                BTEntry.etymology,
                BTEntry.genders_json,
            ).order_by(BTEntry.id.asc())
        ).fetchall()

        total_entries = len(entry_rows) or 1
        self._begin_stage(
            LexiconBuildStage.LOAD_ENTRIES,
            total=total_entries,
        )

        payloads: list[EntryPayload] = []
        for index, entry_row in enumerate(entry_rows, start=1):
            self._check_cancel(
                stage=LexiconBuildStage.LOAD_ENTRIES,
                current_item=str(entry_row.norm_key),
            )
            entry_id = int(entry_row.id)
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
                    "norm_key": str(entry_row.norm_key),
                    "normalized_title": str(entry_row.normalized_title),
                    "pos": str(entry_row.pos),
                    "headword": str(entry_row.headword_macronized),
                    "summary_sense": summary_sense,
                    "etymology": str(entry_row.etymology),
                    "variants": variants_by_entry.get(entry_id, []),
                    "genders_json": str(entry_row.genders_json),
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
        connection: Connection,
        entries: list[EntryPayload],
    ) -> None:
        """
        Insert projected dictionary entries into ``lexicon_entries``.

        Args:
            connection: Open SQLAlchemy connection receiving entry inserts.
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
        if entries:
            payload = [
                {
                    "entry_id": entry["entry_id"],
                    "norm_key": entry["norm_key"],
                    "pos": entry["pos"],
                    "headword": entry["headword"],
                    "summary_sense": entry["summary_sense"],
                    "etymology": entry["etymology"],
                    "variants_json": json.dumps(entry["variants"], ensure_ascii=False),
                    "genders_json": entry["genders_json"],
                    "senses_json": json.dumps(entry["senses"], ensure_ascii=False),
                }
                for entry in entries
            ]
            connection.execute(insert(LexiconEntry), payload)
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
        connection: Connection,
        entries: list[EntryPayload],
    ) -> tuple[list[list[dict[str, object]]], int]:
        """
        Stream ``forms`` rows into batched lexicon form insert payloads.

        Args:
            connection: Open SQLAlchemy connection queried for ``forms`` rows.
            entries: Projected dictionary entry payloads used for joining.

        Returns:
            Tuple of batched form payloads and the total source ``forms`` row count.

        """
        total_forms = int(
            connection.execute(select(func.count()).select_from(Form)).scalar_one()
        )
        progress_total = total_forms or 1
        self._begin_stage(
            LexiconBuildStage.LOAD_FORMS,
            total=progress_total,
            detail="fetching forms",
        )

        variant_rows = connection.execute(
            select(BTVariant.entry_id, BTVariant.normalized_title, BTEntry.pos)
            .join(BTEntry, BTEntry.id == BTVariant.entry_id)
            .where(func.trim(func.coalesce(BTVariant.normalized_title, "")) != "")
            .order_by(BTVariant.entry_id.asc(), BTVariant.spelling_raw.asc())
        ).fetchall()
        join_index = NormalizedTitleJoinIndex.from_entry_variant_rows(
            [
                (
                    cast("int", entry["entry_id"]),
                    str(entry["normalized_title"]),
                    str(entry["pos"]),
                )
                for entry in entries
            ],
            [
                (int(row.entry_id), str(row.normalized_title), str(row.pos))
                for row in variant_rows
            ],
        )

        form_rows = connection.execute(
            select(
                Form.id,
                Form.BT,
                Form.title,
                Form.stem,
                Form.form,
                Form.formi,
                Form.wordclass,
                Form.function,
                Form.probability,
                Form.class1,
                Form.class2,
                Form.class3,
                Form.paradigm,
                Form.normalized_title,
            ).order_by(Form.id.asc())
        ).fetchall()

        chunk: list[dict[str, object]] = []
        form_batches: list[list[dict[str, object]]] = []
        last_logged_row = 0
        for index, row in enumerate(form_rows, start=1):
            current_item = str(row.BT)
            self._check_cancel(
                stage=LexiconBuildStage.LOAD_FORMS,
                current_item=current_item,
            )
            bt_pos = WORDCLASS_TO_BT_POS.get(str(row.wordclass).strip().lower(), "")
            matched_entry_id = join_index.resolve_one(
                str(row.normalized_title),
                bt_pos or None,
            )
            chunk.append(
                {
                    "form_id": int(row.id),
                    "entry_id": matched_entry_id,
                    "bt": str(row.BT),
                    "title": str(row.title),
                    "stem": str(row.stem),
                    "form": str(row.form),
                    "formi": str(row.formi),
                    "wordclass": str(row.wordclass),
                    "function": str(row.function),
                    "probability": str(row.probability),
                    "class1": str(row.class1),
                    "class2": str(row.class2),
                    "class3": str(row.class3),
                    "paradigm": str(row.paradigm),
                }
            )
            should_emit_heartbeat = index in {1, progress_total} or len(
                chunk
            ) >= self._form_stage_batch_size
            if len(chunk) >= self._form_stage_batch_size:
                form_batches.append(chunk)
                if (
                    index in {1, progress_total}
                    or index - last_logged_row >= self._form_log_interval_rows
                ):
                    self._emit_log(
                        stage=LexiconBuildStage.LOAD_FORMS,
                        message="staging form rows",
                        current_item=current_item,
                        counts=(index, progress_total),
                    )
                    last_logged_row = index
                chunk = []
            if should_emit_heartbeat:
                self._advance_stage(
                    LexiconBuildStage.LOAD_FORMS,
                    completed=index,
                    total=progress_total,
                    current_item=current_item,
                )
        if chunk:
            form_batches.append(chunk)
            if total_forms != last_logged_row:
                self._emit_log(
                    stage=LexiconBuildStage.LOAD_FORMS,
                    message="staging form rows",
                    current_item=str(chunk[-1]["bt"]),
                    counts=(total_forms, progress_total),
                )
        self._finish_stage(LexiconBuildStage.LOAD_FORMS)
        return form_batches, total_forms

    def _insert_forms(
        self,
        connection: Connection,
        form_batches: list[list[dict[str, object]]],
        forms_count: int,
    ) -> None:
        """
        Insert projected morphology rows into ``lexicon_forms``.

        Args:
            connection: Open SQLAlchemy connection receiving form inserts.
            form_batches: Batched form payload rows to insert.
            forms_count: Number of source ``forms`` rows being projected.

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
        inserted = 0
        for batch in form_batches:
            self._check_cancel(stage=LexiconBuildStage.INSERT_FORMS)
            if not batch:
                continue
            connection.execute(insert(LexiconForm), batch)
            inserted += len(batch)
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
        connection: Connection,
        entries: list[EntryPayload],
        forms_count: int,
    ) -> list[dict[str, object]]:
        """
        Build ranked search-key rows for dictionary and morphology lookups.

        Note:
            Keys index diacritic-stripped ``normalize_old_english`` shapes so
            lexicon browse accepts undiacritized queries. Form-to-entry joins
            use macron-preserving ``normalized_title`` via
            ``NormalizedTitleJoinIndex.resolve_one``.

        Args:
            connection: Open SQLAlchemy connection queried for inserted form rows.
            entries: Projected dictionary entry payloads.
            forms_count: Number of inserted morphology form rows.

        Returns:
            Candidate search-key payload rows ready for lexicon insertion.

        """
        total = max(len(entries) + forms_count, 1)
        self._begin_stage(
            LexiconBuildStage.BUILD_SEARCH_KEYS,
            total=total,
        )
        progress_index = 0
        progress_total = total
        search_key_rows: list[dict[str, object]] = []

        def add(row: SearchKeyRow) -> None:
            key_text, key_kind, rank_tier, entry_id, form_id, display_text = row
            normalized_key = key_text.strip()
            display = display_text.strip()
            if not normalized_key or not display:
                return
            search_key_rows.append(
                {
                    "key_text": normalized_key,
                    "key_kind": key_kind,
                    "rank_tier": rank_tier,
                    "entry_id": entry_id,
                    "form_id": form_id,
                    "display_text": display,
                }
            )

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

        form_rows = connection.execute(
            select(
                LexiconForm.form_id,
                LexiconForm.entry_id,
                LexiconForm.bt,
                LexiconForm.title,
                LexiconForm.stem,
                LexiconForm.form,
                LexiconForm.formi,
                Form.bt_key,
                Form.title_key,
                Form.stem_key,
                Form.form_key,
                Form.formi_key,
            )
            .join(Form, Form.id == LexiconForm.form_id)
            .order_by(LexiconForm.form_id.asc())
        ).fetchall()
        for form in form_rows:
            progress_index += 1
            self._check_cancel(
                stage=LexiconBuildStage.BUILD_SEARCH_KEYS,
                current_item=str(form.form),
            )
            form_id = int(form.form_id)
            form_entry_id = cast("int | None", form.entry_id)
            if form_entry_id is None:
                rank_tier = RANK_TIER_ORPHAN
            else:
                rank_tier = RANK_TIER_MORPH_LEMMA_STEM

            add(
                (
                    str(form.bt_key) or _normalize_morph_key(str(form.bt)),
                    KEY_KIND_LEMMA,
                    rank_tier,
                    form_entry_id,
                    form_id,
                    str(form.bt),
                )
            )
            add(
                (
                    str(form.title_key) or _normalize_morph_key(str(form.title)),
                    KEY_KIND_LEMMA,
                    rank_tier,
                    form_entry_id,
                    form_id,
                    str(form.title),
                )
            )
            add(
                (
                    str(form.stem_key) or _normalize_morph_key(str(form.stem)),
                    KEY_KIND_STEM,
                    rank_tier,
                    form_entry_id,
                    form_id,
                    str(form.stem),
                )
            )

            form_rank_tier = (
                RANK_TIER_ORPHAN if form_entry_id is None else RANK_TIER_MORPH_FORM
            )
            add(
                (
                    str(form.form_key) or _normalize_morph_key(str(form.form)),
                    KEY_KIND_FORM,
                    form_rank_tier,
                    form_entry_id,
                    form_id,
                    str(form.form),
                )
            )
            add(
                (
                    str(form.formi_key) or _normalize_morph_key(str(form.formi)),
                    KEY_KIND_FORM,
                    form_rank_tier,
                    form_entry_id,
                    form_id,
                    str(form.formi),
                )
            )
            self._advance_stage(
                LexiconBuildStage.BUILD_SEARCH_KEYS,
                completed=progress_index,
                total=progress_total,
            )
        self._finish_stage(LexiconBuildStage.BUILD_SEARCH_KEYS)
        return search_key_rows

    def _insert_search_keys(
        self,
        connection: Connection,
        search_key_rows: list[dict[str, object]],
    ) -> int:
        """
        Insert ranked search keys into ``lexicon_search_keys``.

        Args:
            connection: Open SQLAlchemy connection receiving key inserts.
            search_key_rows: Candidate search-key payload rows to insert.

        Returns:
            Number of rows written to ``lexicon_search_keys``.

        """
        staged_count = len(search_key_rows)
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
        if search_key_rows:
            for offset in range(0, len(search_key_rows), self._form_stage_batch_size):
                batch = search_key_rows[offset : offset + self._form_stage_batch_size]
                connection.execute(
                    insert(LexiconSearchKey).prefix_with("OR IGNORE"),
                    batch,
                )
        written = int(
            connection.execute(
                select(func.count()).select_from(LexiconSearchKey)
            ).scalar_one()
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
        connection: Connection,
        *,
        built_at: str,
        forms_source_count: int,
        bt_entries_source_count: int,
    ) -> None:
        """
        Write build metadata rows for timestamp and source table sizes.

        Args:
            connection: Open SQLAlchemy connection receiving metadata inserts.

        Keyword Args:
            built_at: ISO-8601 UTC rebuild timestamp.
            forms_source_count: Source ``forms`` row count observed at rebuild.
            bt_entries_source_count: Source ``bt_entries`` row count observed.

        """
        self._begin_stage(LexiconBuildStage.WRITE_META)
        connection.execute(
            insert(LexiconBuildMetaTable),
            [
                {"key": META_KEY_BUILT_AT, "value": built_at},
                {"key": META_KEY_FORMS_SOURCE_COUNT, "value": str(forms_source_count)},
                {
                    "key": META_KEY_BT_ENTRIES_SOURCE_COUNT,
                    "value": str(bt_entries_source_count),
                },
            ],
        )
        self._finish_stage(LexiconBuildStage.WRITE_META)


def _open_db_connection(
    target: DbTarget,
) -> tuple[Connection, Engine | None, bool]:
    """
    Resolve one SQLAlchemy connection from a supported database target.

    Args:
        target: Engine, connection, or database path.

    Returns:
        Tuple of ``(connection, owned_engine, should_close_connection)``.

    """
    if isinstance(target, Path):
        engine = create_sqlalchemy_engine(target.expanduser().resolve())
        return engine.connect(), engine, True
    if isinstance(target, Engine):
        return target.connect(), None, True
    return target, None, False


def read_lexicon_build_meta(target: DbTarget) -> LexiconBuildMeta | None:
    """
    Read persisted lexicon build metadata from one database target.

    Args:
        target: Engine, connection, or database path with ``lexicon_build_meta`` rows.

    Returns:
        Parsed build metadata, or ``None`` when metadata rows are absent.

    """
    connection, owned_engine, close_connection = _open_db_connection(target)
    try:
        try:
            rows = connection.execute(
                select(
                    LexiconBuildMetaTable.key,
                    LexiconBuildMetaTable.value,
                )
            ).fetchall()
        except OperationalError:
            return None

        values = {str(row.key): str(row.value) for row in rows}
        required = (
            META_KEY_BUILT_AT,
            META_KEY_FORMS_SOURCE_COUNT,
            META_KEY_BT_ENTRIES_SOURCE_COUNT,
        )
        if not all(key in values for key in required):
            return None

        return LexiconBuildMeta(
            built_at=values[META_KEY_BUILT_AT],
            forms_source_count=int(values[META_KEY_FORMS_SOURCE_COUNT]),
            bt_entries_source_count=int(values[META_KEY_BT_ENTRIES_SOURCE_COUNT]),
        )
    finally:
        if close_connection:
            connection.close()
        if owned_engine is not None:
            owned_engine.dispose()


def lexicon_read_model_has_data(target: DbTarget) -> bool:
    """
    Return whether one database already contains populated lexicon read-model rows.

    Args:
        target: Engine, connection, or database path to inspect.

    Returns:
        ``True`` when build metadata or non-empty lexicon tables already exist.

    """
    connection, owned_engine, close_connection = _open_db_connection(target)
    try:
        if read_lexicon_build_meta(connection) is not None:
            return True
        for table in (LexiconEntry, LexiconForm):
            try:
                count = connection.execute(
                    select(func.count()).select_from(table)
                ).scalar_one()
            except OperationalError:
                continue
            if int(count) > 0:
                return True
        return False
    finally:
        if close_connection:
            connection.close()
        if owned_engine is not None:
            owned_engine.dispose()


def check_lexicon_staleness(target: DbTarget) -> LexiconStalenessReport:
    """
    Compare stored lexicon build metadata against current source table sizes.

    Args:
        target: Engine, connection, or path to ``wyrdcraeft.sqlite3`` with source and
            lexicon tables.

    Returns:
        Staleness report describing whether ``lexicon build`` should be rerun.

    """
    connection, owned_engine, close_connection = _open_db_connection(target)
    try:
        current_forms_count = _count_table_rows(connection, "forms")
        current_bt_entries_count = _count_table_rows(connection, "bt_entries")
        meta = read_lexicon_build_meta(connection)
    finally:
        if close_connection:
            connection.close()
        if owned_engine is not None:
            owned_engine.dispose()

    if meta is None:
        return LexiconStalenessReport(
            is_stale=True,
            reason="Lexicon read-model has not been built yet.",
            meta=None,
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


def _count_table_rows(connection: Connection, table_name: str) -> int:
    """
    Count rows in one known source table when the table exists.

    Args:
        connection: Open SQLAlchemy connection to inspect.
        table_name: Target source table name.

    Returns:
        Row count, or ``0`` when the table is missing.

    Raises:
        ValueError: ``table_name`` is not an allowed staleness source table.

    """
    if table_name not in _STALENESS_SOURCE_TABLES:
        msg = f"Unsupported staleness source table: {table_name}"
        raise ValueError(msg)
    table = Form.__table__ if table_name == "forms" else BTEntry.__table__
    try:
        count = connection.execute(select(func.count()).select_from(table)).scalar_one()
    except OperationalError:
        return 0
    return int(count)


def rebuild_lexicon(
    db_path: Path,
    *,
    progress: LexiconBuildProgress | None = None,
    event_sink: LexiconBuildEventSink | None = None,
    cancel_event: threading.Event | None = None,
    runtime: LexiconBuildController | None = None,
) -> BuildReport:
    """
    Rebuild lexicon read-model tables in the target canonical database.

    Args:
        db_path: Path to ``wyrdcraeft.sqlite3`` containing ``forms`` and ``bt_*``.

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
