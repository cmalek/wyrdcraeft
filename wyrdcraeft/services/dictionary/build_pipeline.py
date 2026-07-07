"""Unified dictionary build orchestration for canonical dictionary workflows."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib import import_module
from typing import TYPE_CHECKING, Protocol

from sqlalchemy import func, select, text

from wyrdcraeft.db.runtime import create_engine, upgrade_canonical_db
from wyrdcraeft.models.dictionary_build import (
    AnyDictionaryBuildEvent,
    DictionaryBuildCounters,
    DictionaryBuildFinished,
    DictionaryBuildLog,
    DictionaryBuildLogLevel,
    DictionaryBuildSnapshot,
    DictionaryBuildStage,
    DictionaryBuildStageProgress,
    DictionaryBuildStageStarted,
    DictionaryBuildStatus,
)
from wyrdcraeft.models.sqlalchemy import BTEntry, Form
from wyrdcraeft.services.dictionary.forms_entry_relinker import FormsEntryRelinker
from wyrdcraeft.services.dictionary.pipeline import BTIndexPipeline
from wyrdcraeft.services.dictionary.pos_inference import DictionaryPosInferer
from wyrdcraeft.services.dictionary.sinks import BTSqliteSink

#: Callback receiving typed build events as they are emitted.
DictionaryBuildEventSink = Callable[[AnyDictionaryBuildEvent], None]

if TYPE_CHECKING:
    import threading
    from pathlib import Path

    from sqlalchemy.engine import Connection

    from wyrdcraeft.services.dictionary.llm_fix_pass import BTLLMFixPass


class DictionaryBuildProgress(Protocol):
    """Progress callback surface used during unified dictionary builds."""

    def begin_stage(self, stage: DictionaryBuildStage, *, total: int = 1) -> None:
        """
        Mark one build stage active.

        Args:
            stage: Stage being entered.

        Keyword Args:
            total: Total work units expected for the stage.

        """
        ...

    def advance_stage(
        self,
        stage: DictionaryBuildStage,
        *,
        completed: int | None = None,
        total: int | None = None,
        detail: str = "",
        force: bool = False,
    ) -> None:
        """
        Advance one build stage.

        Args:
            stage: Stage being advanced.

        Keyword Args:
            completed: Completed work units for the stage.
            total: Total work units expected for the stage.
            detail: Optional human-readable progress detail.
            force: Whether the sink should emit immediately.

        """
        ...

    def finish_stage(self, stage: DictionaryBuildStage) -> None:
        """
        Mark one build stage complete.

        Args:
            stage: Stage that has completed.

        """
        ...


@dataclass(frozen=True)
class MorphBuildOptions:
    """Configuration for optional morphology regeneration within a dictionary build."""

    #: Optional cap for non-full morphology generation mode.
    limit: int | None = None
    #: Enables full morphology generation mode.
    full: bool = False
    #: Optional base directory containing morphology source fixtures.
    data_dir: Path | None = None
    #: Optional TSV parity output path for regenerated forms.
    output: Path | None = None
    #: Optional visible-lemma progress cadence override.
    progress_every: int | None = None
    #: Enables opt-in non-parity r-stem noun generation.
    enable_r_stem_nouns: bool = False
    #: Enables morphology profiler summary output.
    profile: bool = False
    #: Forces packaged Wright catalog reload before generation.
    refresh_catalog: bool = False
    #: Optional dictionary input path override.
    dictionary: Path | None = None
    #: Optional manual-forms input path override.
    manual_forms: Path | None = None
    #: Optional verbal paradigms input path override.
    verbal_paradigms: Path | None = None
    #: Optional prefixes input path override.
    prefixes: Path | None = None


def run_morphology_generation(*, db_path: Path, options: MorphBuildOptions) -> int:
    """
    Forward pipeline morphology options to the shared build runner.

    Keyword Args:
        db_path: Canonical SQLite database receiving regenerated forms.
        options: Morphology regeneration options chosen by the caller.

    Returns:
        Number of forms written by the shared morphology runner.

    """
    module = import_module("wyrdcraeft.services.morphology.build_runner")
    runner = module.run_morphology_generation

    return runner(
        db_path=db_path,
        quiet=True,
        data_dir=options.data_dir,
        dictionary=options.dictionary,
        manual_forms=options.manual_forms,
        verbal_paradigms=options.verbal_paradigms,
        prefixes=options.prefixes,
        output=options.output,
        limit=options.limit,
        progress_every=options.progress_every,
        enable_r_stem_nouns=options.enable_r_stem_nouns,
        full=options.full,
        profile=options.profile,
        refresh_catalog=options.refresh_catalog,
    )


@dataclass(frozen=True)
class DictionaryBuildReport:
    """Summary of one unified dictionary build run."""

    #: UTC timestamp recorded when the build finished.
    built_at: str
    #: Number of dictionary entries written by the rebuild stage.
    bt_entries_written: int
    #: Number of forms present before optional regeneration logic ran.
    forms_source_count: int
    #: Whether morphology rows were regenerated during this run.
    forms_regenerated: bool
    #: Number of form rows carrying a non-null ``entry_id`` after relinking.
    entry_ids_linked: int
    #: Number of stale ``forms.entry_id`` values cleared before dictionary reload.
    entry_ids_cleared: int
    #: Number of dictionary rows whose POS was inferred from morphology.
    pos_inferred: int


class DictionaryBuildPipeline:
    """
    Orchestrate canonical dictionary rebuild, form relink, and follow-on refreshes.

    Args:
        db_path: Path to the canonical ``wyrdcraeft.sqlite3`` database.

    Keyword Args:
        progress: Optional build-progress collaborator.
        event_sink: Optional typed build-event callback.
        cancel_event: Optional cooperative cancellation flag.

    """

    #: Canonical database path used for schema, dictionary, and forms work.
    _db_path: Path
    #: Optional progress collaborator notified at stage boundaries.
    _progress: DictionaryBuildProgress | None
    #: Optional typed event sink receiving build events.
    _event_sink: DictionaryBuildEventSink | None
    #: Optional cooperative cancellation flag.
    _cancel_event: threading.Event | None
    #: Monotonic sequence number for emitted events.
    _event_seq: int
    #: Currently active top-level stage.
    _active_stage: DictionaryBuildStage | None
    #: Accumulated counters captured in terminal events.
    _counters: DictionaryBuildCounters

    def __init__(
        self,
        db_path: Path,
        *,
        progress: DictionaryBuildProgress | None = None,
        event_sink: DictionaryBuildEventSink | None = None,
        cancel_event: threading.Event | None = None,
    ) -> None:
        """
        Initialize the build pipeline for one canonical database.

        Args:
            db_path: Path to the canonical ``wyrdcraeft.sqlite3`` database.

        Keyword Args:
            progress: Optional build-progress collaborator.
            event_sink: Optional typed build-event callback.
            cancel_event: Optional cooperative cancellation flag.

        """
        #: Canonical database path used for schema, dictionary, and forms work.
        self._db_path = db_path.expanduser().resolve()
        #: Optional progress collaborator notified at stage boundaries.
        self._progress = progress
        #: Optional typed event sink receiving build events.
        self._event_sink = event_sink
        #: Optional cooperative cancellation flag.
        self._cancel_event = cancel_event
        #: Monotonic sequence number for emitted events.
        self._event_seq = 0
        #: Currently active top-level stage.
        self._active_stage = None
        #: Accumulated counters captured in terminal events.
        self._counters = DictionaryBuildCounters()

    def run(  # noqa: PLR0913
        self,
        *,
        source: Path,
        with_morphology: bool,
        morph_options: MorphBuildOptions,
        warnings_path: Path | None = None,
        llm_fix_pass: BTLLMFixPass | None = None,
        report_path: Path | None = None,
    ) -> DictionaryBuildReport:
        """
        Run the unified dictionary build pipeline against one source file.

        Keyword Args:
            source: Bosworth-Toller source path consumed by the rebuild stage.
            with_morphology: Forces morphology regeneration when ``True``.
            morph_options: Optional regeneration settings used when stage 4 runs.
            warnings_path: Optional parse warnings JSONL path for the dictionary
                rebuild stage.
            llm_fix_pass: Optional LLM repair pass collaborator for warning lines.
            report_path: Optional JSON report path for parse and merge statistics.

        Returns:
            Build report summarizing dictionary writes, relinks, and POS inference.

        Raises:
            RuntimeError: Morphology regeneration was requested without dictionary
                entries or cooperative cancellation was requested.

        """
        source = source.expanduser().resolve()
        self._run_single_step_stage(
            DictionaryBuildStage.ENSURE_SCHEMA,
            lambda: upgrade_canonical_db(self._db_path),
        )

        self._rebuild_dictionary(
            source,
            warnings_path=warnings_path,
            llm_fix_pass=llm_fix_pass,
            report_path=report_path,
        )

        engine = create_engine(self._db_path)
        try:
            with engine.begin() as connection:
                entry_ids_linked, forms_source_count = self._relink_forms(connection)

            forms_regenerated = False
            if forms_source_count == 0 or with_morphology:
                forms_regenerated = True
                with engine.begin() as connection:
                    if self._count_bt_entries(connection) == 0:
                        msg = (
                            "Morphology regeneration requires bt_entries rows. "
                            "Dictionary rebuild produced no entries."
                        )
                        raise RuntimeError(msg)
                    connection.execute(text("DELETE FROM forms"))
                self._run_morphology_regeneration(morph_options)

            with engine.begin() as connection:
                forms_after_build = self._count_forms(connection)
                entry_ids_linked = self._count_linked_forms(connection)
                pos_inferred = (
                    self._infer_pos(connection) if forms_after_build > 0 else 0
                )
        finally:
            engine.dispose()

        built_at = self._now()
        report = DictionaryBuildReport(
            built_at=built_at,
            bt_entries_written=self._counters.bt_entries_written,
            forms_source_count=forms_source_count,
            forms_regenerated=forms_regenerated,
            entry_ids_linked=entry_ids_linked,
            entry_ids_cleared=self._counters.entry_ids_cleared,
            pos_inferred=pos_inferred,
        )
        self._emit_event(
            DictionaryBuildFinished(
                seq=self._next_event_seq(),
                at=built_at,
                snapshot=self._snapshot(status="complete", detail="build complete"),
                built_at=built_at,
            )
        )
        return report

    def _rebuild_dictionary(
        self,
        source: Path,
        *,
        warnings_path: Path | None,
        llm_fix_pass: BTLLMFixPass | None,
        report_path: Path | None,
    ) -> None:
        """
        Clear stale form links and rebuild the canonical dictionary slice.

        Args:
            source: Bosworth-Toller source path consumed by the rebuild stage.

        Keyword Args:
            warnings_path: Optional parse warnings JSONL path for the rebuild
                stage.
            llm_fix_pass: Optional LLM repair pass collaborator for warning lines.
            report_path: Optional JSON report path for parse and merge statistics.

        """
        engine = create_engine(self._db_path)
        try:
            with engine.begin() as connection:
                self._check_cancel()
                relinker = FormsEntryRelinker(connection)
                cleared = relinker.clear_all_entry_ids()
                self._counters = DictionaryBuildCounters(
                    bt_entries_written=self._counters.bt_entries_written,
                    entry_ids_cleared=cleared,
                    entry_ids_linked=self._counters.entry_ids_linked,
                    pos_inferred=self._counters.pos_inferred,
                )

            def action() -> None:
                sink = BTSqliteSink(self._db_path)
                try:
                    report = BTIndexPipeline().run(
                        source,
                        sink,
                        warnings_path=warnings_path,
                        llm_fix_pass=llm_fix_pass,
                    )
                finally:
                    sink.close()
                if report_path is not None:
                    report.write_json(report_path.resolve())
                self._counters = DictionaryBuildCounters(
                    bt_entries_written=report.merged,
                    entry_ids_cleared=self._counters.entry_ids_cleared,
                    entry_ids_linked=self._counters.entry_ids_linked,
                    pos_inferred=self._counters.pos_inferred,
                )

            self._run_single_step_stage(DictionaryBuildStage.REBUILD_DICTIONARY, action)
        finally:
            engine.dispose()

    def _relink_forms(self, connection: Connection) -> tuple[int, int]:
        """
        Relink every stored form row against the rebuilt dictionary tables.

        Args:
            connection: Open SQLAlchemy connection bound to canonical SQLite.

        Returns:
            Tuple of linked-form count plus forms-source count.

        """
        forms_source_count = self._count_forms(connection)
        stage_total = max(forms_source_count, 1)
        self._begin_stage(DictionaryBuildStage.RELINK_FORMS, total=stage_total)
        relinker = FormsEntryRelinker(connection)
        relinker.relink_all(
            progress=lambda processed, total: self._advance_stage(
                DictionaryBuildStage.RELINK_FORMS,
                completed=processed,
                total=total,
                detail=f"linked={self._count_linked_forms(connection)}",
            )
        )
        entry_ids_linked = self._count_linked_forms(connection)
        self._counters = DictionaryBuildCounters(
            bt_entries_written=self._counters.bt_entries_written,
            entry_ids_cleared=self._counters.entry_ids_cleared,
            entry_ids_linked=entry_ids_linked,
            pos_inferred=self._counters.pos_inferred,
        )
        self._finish_stage(DictionaryBuildStage.RELINK_FORMS)
        return entry_ids_linked, forms_source_count

    def _run_morphology_regeneration(self, options: MorphBuildOptions) -> None:
        """
        Run the optional morphology regeneration stage.

        Args:
            options: Morphology regeneration options chosen by the caller.

        """
        self._run_single_step_stage(
            DictionaryBuildStage.REBUILD_MORPHOLOGY,
            lambda: run_morphology_generation(db_path=self._db_path, options=options),
        )

    def _infer_pos(self, connection: Connection) -> int:
        """
        Infer missing dictionary POS values from stored morphology forms.

        Args:
            connection: Open SQLAlchemy connection bound to canonical SQLite.

        Returns:
            Number of dictionary rows updated with inferred POS values.

        """
        inferer = DictionaryPosInferer()
        total = self._count_unknown_pos_entries(connection)
        self._begin_stage(DictionaryBuildStage.INFER_POS, total=max(total, 1))
        updated = inferer.infer_missing_pos(
            connection,
            progress=lambda completed, total_rows, updated_rows, current_item: (
                self._advance_stage(
                    DictionaryBuildStage.INFER_POS,
                    completed=completed,
                    total=total_rows,
                    detail=f"updated={updated_rows}",
                    current_item=current_item,
                )
            ),
            warning_sink=lambda message, current_item: self._emit_log(
                stage=DictionaryBuildStage.INFER_POS,
                level="warning",
                message=message,
                current_item=current_item,
            ),
            cancel_check=self._check_cancel,
        )
        self._counters = DictionaryBuildCounters(
            bt_entries_written=self._counters.bt_entries_written,
            entry_ids_cleared=self._counters.entry_ids_cleared,
            entry_ids_linked=self._counters.entry_ids_linked,
            pos_inferred=updated,
        )
        self._finish_stage(DictionaryBuildStage.INFER_POS)
        return updated

    @staticmethod
    def _count_forms(connection: Connection) -> int:
        """
        Return the current ``forms`` row count.

        Args:
            connection: Open SQLAlchemy connection bound to canonical SQLite.

        Returns:
            Number of rows currently stored in ``forms``.

        """
        return int(
            connection.execute(select(func.count()).select_from(Form)).scalar_one()
        )

    @staticmethod
    def _count_linked_forms(connection: Connection) -> int:
        """
        Return the number of forms carrying a linked dictionary entry.

        Args:
            connection: Open SQLAlchemy connection bound to canonical SQLite.

        Returns:
            Number of ``forms`` rows whose ``entry_id`` is non-null.

        """
        return int(
            connection.execute(
                select(func.count()).select_from(Form).where(Form.entry_id.is_not(None))
            ).scalar_one()
        )

    @staticmethod
    def _count_bt_entries(connection: Connection) -> int:
        """
        Return the current ``bt_entries`` row count.

        Args:
            connection: Open SQLAlchemy connection bound to canonical SQLite.

        Returns:
            Number of dictionary rows currently stored in ``bt_entries``.

        """
        return int(
            connection.execute(select(func.count()).select_from(BTEntry)).scalar_one()
        )

    @staticmethod
    def _count_unknown_pos_entries(connection: Connection) -> int:
        """
        Return the number of dictionary rows currently carrying unknown POS.

        Args:
            connection: Open SQLAlchemy connection bound to canonical SQLite.

        Returns:
            Number of ``bt_entries`` rows joined to the ``unknown`` POS code.

        """
        return int(
            connection.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM bt_entries
                    JOIN parts_of_speech ON parts_of_speech.id = bt_entries.pos_id
                    WHERE parts_of_speech.code = 'unknown'
                    """
                )
            ).scalar_one()
        )

    def _run_single_step_stage(
        self,
        stage: DictionaryBuildStage,
        action: Callable[[], object],
    ) -> None:
        """
        Run one single-step stage with begin and finish hooks.

        Args:
            stage: Top-level build stage being executed.
            action: Zero-argument callable performing the stage work.

        """
        self._begin_stage(stage, total=1)
        action()
        self._finish_stage(stage)

    def _begin_stage(
        self,
        stage: DictionaryBuildStage,
        *,
        total: int,
    ) -> None:
        """
        Mark one stage active across progress and typed event surfaces.

        Args:
            stage: Stage being entered.

        Keyword Args:
            total: Total work units expected for the stage.

        """
        self._check_cancel()
        self._active_stage = stage
        if self._progress is not None:
            self._progress.begin_stage(stage, total=total)
        self._emit_event(
            DictionaryBuildStageStarted(
                seq=self._next_event_seq(),
                at=self._now(),
                stage=stage,
                total=max(total, 1),
            )
        )
        self._emit_log(stage=stage, message=f"stage started: {stage.value}")

    def _advance_stage(
        self,
        stage: DictionaryBuildStage,
        *,
        completed: int,
        total: int,
        detail: str = "",
        current_item: str = "",
    ) -> None:
        """
        Advance optional build progress for one stage update.

        Args:
            stage: Stage being advanced.

        Keyword Args:
            completed: Completed work units for the stage.
            total: Total work units expected for the stage.
            detail: Optional human-readable progress detail.
            current_item: Optional active item label for logs and events.

        """
        self._check_cancel(current_item)
        if self._progress is not None:
            self._progress.advance_stage(
                stage,
                completed=completed,
                total=total,
                detail=detail,
                force=completed in {0, total},
            )
        self._emit_event(
            DictionaryBuildStageProgress(
                seq=self._next_event_seq(),
                at=self._now(),
                stage=stage,
                completed=completed,
                total=max(total, 1),
                detail=detail,
                current_item=current_item,
            )
        )

    def _finish_stage(self, stage: DictionaryBuildStage) -> None:
        """
        Mark one stage complete across progress and log surfaces.

        Args:
            stage: Stage that has completed.

        """
        if self._progress is not None:
            self._progress.finish_stage(stage)
        self._emit_event(
            DictionaryBuildStageProgress(
                seq=self._next_event_seq(),
                at=self._now(),
                stage=stage,
                completed=1,
                total=1,
            )
        )
        self._emit_log(stage=stage, message=f"stage finished: {stage.value}")
        self._active_stage = None

    def _emit_log(
        self,
        *,
        stage: DictionaryBuildStage | None,
        message: str,
        level: DictionaryBuildLogLevel = "info",
        current_item: str = "",
    ) -> None:
        """
        Emit one structured log event.

        Keyword Args:
            stage: Stage associated with the log line when known.
            message: Human-readable log message.
            level: Structured log severity.
            current_item: Optional active item label.

        """
        self._emit_event(
            DictionaryBuildLog(
                seq=self._next_event_seq(),
                at=self._now(),
                stage=stage,
                level=level,
                message=message,
                current_item=current_item,
            )
        )

    def _emit_event(self, event: AnyDictionaryBuildEvent) -> None:
        """
        Send one typed build event to the configured sink.

        Args:
            event: Build event payload to emit.

        """
        if self._event_sink is not None:
            self._event_sink(event)

    def _check_cancel(self, current_item: str = "") -> None:
        """
        Raise when cooperative cancellation was requested.

        Args:
            current_item: Optional active item label tied to the cancellation log.

        """
        if self._cancel_event is None or not self._cancel_event.is_set():
            return
        self._emit_log(
            stage=self._active_stage,
            level="warning",
            message="cancellation requested",
            current_item=current_item,
        )
        msg = "Dictionary build cancelled."
        raise RuntimeError(msg)

    def _snapshot(
        self,
        *,
        status: DictionaryBuildStatus,
        detail: str,
    ) -> DictionaryBuildSnapshot:
        """
        Return the current build snapshot payload.

        Keyword Args:
            status: Lifecycle state to encode in the snapshot.
            detail: Human-readable status text for the snapshot.

        Returns:
            Snapshot payload describing the pipeline's current state.

        """
        return DictionaryBuildSnapshot(
            status=status,
            active_stage=self._active_stage,
            counters=self._counters,
            status_message=detail,
        )

    def _next_event_seq(self) -> int:
        """
        Return the next typed-event sequence number.

        Returns:
            Next monotonic event sequence number.

        """
        self._event_seq += 1
        return self._event_seq

    @staticmethod
    def _now() -> str:
        """
        Return the current UTC timestamp in ISO-8601 ``Z`` form.

        Returns:
            Current UTC timestamp formatted for build events.

        """
        return (
            datetime.now(UTC)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )
