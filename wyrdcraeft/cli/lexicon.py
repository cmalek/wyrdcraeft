"""Lexicon browse workflow CLI commands."""

from __future__ import annotations

import queue
import sqlite3
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import click

from wyrdcraeft.models.lexicon_build import (
    BuildCancelled,
    BuildCounters,
    BuildCounterUpdated,
    BuildFailed,
    BuildFinished,
    BuildLog,
    BuildSnapshot,
    BuildStageProgress,
    BuildStageStarted,
    BuildStatus,
    LexiconBuildEvent,
    LexiconBuildStage,
)
from wyrdcraeft.paths import resolve_morphology_index_db_path
from wyrdcraeft.services.lexicon.build import (
    BuildReport,
    LexiconBuildCancelledError,
    MissingLexiconSourceTablesError,
    lexicon_read_model_has_data,
    rebuild_lexicon,
)
from wyrdcraeft.services.lexicon.build_monitor import LexiconBuildMonitorApp
from wyrdcraeft.services.lexicon.build_runtime import LexiconBuildController
from wyrdcraeft.services.lexicon.tui import (
    LexiconBrowseDataError,
    run_lexicon_browse,
)

if TYPE_CHECKING:
    from wyrdcraeft.settings import Settings


@dataclass
class _BuildState:
    """Track the latest live build state for summary snapshots."""

    #: Latest counters observed from the worker.
    counters: BuildCounters = field(default_factory=BuildCounters)
    #: Latest active stage observed from the worker.
    active_stage: LexiconBuildStage | None = None


@click.group(
    name="lexicon",
    help="Lexicon browse workflow commands.",
)
def lexicon_group() -> None:
    """Lexicon command group."""


@lexicon_group.command(
    name="build",
    help="Rebuild lexicon read-model tables from morphology and dictionary sources.",
)
@click.option(
    "--index-db",
    type=click.Path(path_type=Path),
    default=None,
    help=(
        "SQLite index file path (overrides --index-dir and the OS app-data default)."
    ),
)
@click.option(
    "--index-dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help=(
        "Directory for morphology.sqlite3 (overrides the OS app-data default)."
    ),
)
@click.option(
    "--no-tui",
    is_flag=True,
    default=False,
    help="Disable the Textual build monitor.",
)
@click.option(
    "--quiet",
    is_flag=True,
    default=False,
    help="Suppress live build output and keep only the final summary.",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Rebuild even when lexicon read-model data already exists.",
)
@click.pass_context
def build(  # noqa: PLR0912, PLR0913, PLR0915
    ctx: click.Context,
    index_db: Path | None,
    index_dir: Path | None,
    no_tui: bool,
    quiet: bool,
    force: bool,
) -> None:
    """
    Rebuild ``lexicon_*`` tables from ``forms`` and ``bt_*`` source tables.

    Args:
        ctx: Click context carrying loaded settings and global flags.
        index_db: Optional SQLite index file path override.
        index_dir: Optional SQLite index directory override.
        no_tui: When set, skip the full-screen Textual build monitor.
        quiet: When set, suppress live build output and keep the final summary.
        force: When set, rebuild even when lexicon read-model data already exists.

    Side Effects:
        Replaces ``lexicon_*`` rows in the target morphology SQLite database.

    Raises:
        click.ClickException: Required source tables are missing or rebuild fails.

    """
    settings: Settings | None = ctx.obj.get("settings")
    app_data_dir = settings.app_data_dir if settings is not None else None
    resolved_index_db = resolve_morphology_index_db_path(
        index_db=index_db,
        index_dir=index_dir,
        app_data_dir=app_data_dir,
    )

    if not force:
        with sqlite3.connect(str(resolved_index_db)) as connection:
            if lexicon_read_model_has_data(connection):
                msg = (
                    "Lexicon read-model already contains data in "
                    f"{resolved_index_db}. Pass --force to rebuild and replace it."
                )
                raise click.ClickException(msg)

    quiet = quiet or bool(ctx.obj.get("quiet"))
    use_tui = sys.stdout.isatty() and sys.stderr.isatty() and not no_tui and not quiet
    controller = LexiconBuildController(db_path=resolved_index_db, quiet=quiet)
    state = _BuildState()
    terminal_event: BuildFinished | BuildCancelled | BuildFailed | None = None
    build_report: BuildReport | None = None

    def record_event(event: LexiconBuildEvent) -> None:
        """Update the shared live state from one build event."""
        nonlocal terminal_event
        if isinstance(event, (BuildStageStarted, BuildStageProgress)):
            state.active_stage = event.stage
        if isinstance(event, BuildCounterUpdated):
            state.counters = BuildCounters(
                entries_written=(
                    event.value
                    if event.counter == "entries_written"
                    else state.counters.entries_written
                ),
                forms_written=(
                    event.value
                    if event.counter == "forms_written"
                    else state.counters.forms_written
                ),
                search_keys_written=(
                    event.value
                    if event.counter == "search_keys_written"
                    else state.counters.search_keys_written
                ),
                pos_inferred=(
                    event.value
                    if event.counter == "pos_inferred"
                    else state.counters.pos_inferred
                ),
            )
        if isinstance(event, (BuildFinished, BuildCancelled, BuildFailed)):
            terminal_event = event

    def event_sink(event: LexiconBuildEvent) -> None:
        """Record one event and forward it to the shared controller."""
        record_event(event)
        controller.emit(event)

    def terminal_snapshot(status: BuildStatus, message: str) -> BuildSnapshot:
        """Return one final snapshot built from the latest live state."""
        return BuildSnapshot(
            status=status,
            active_stage=state.active_stage,
            counters=state.counters,
            status_message=message,
        )

    def worker() -> None:
        """Run the lexicon rebuild and publish one terminal event."""
        nonlocal build_report
        try:
            build_report = rebuild_lexicon(
                resolved_index_db,
                event_sink=event_sink,
                runtime=controller,
            )
        except LexiconBuildCancelledError:
            controller.emit_cancelled(
                message="Lexicon build cancelled.",
                snapshot=terminal_snapshot("cancelled", "Lexicon build cancelled."),
            )
            return
        except MissingLexiconSourceTablesError as exc:
            controller.emit_failed(
                exc,
                snapshot=terminal_snapshot("failed", str(exc)),
            )
            return
        except OSError as exc:
            controller.emit_failed(
                exc,
                snapshot=terminal_snapshot("failed", str(exc)),
            )
            return
        except Exception as exc:  # noqa: BLE001
            controller.emit_failed(
                exc,
                snapshot=terminal_snapshot("failed", str(exc)),
            )
            return

        controller.emit_finished(
            built_at=build_report.built_at,
            forms_source_count=build_report.forms_source_count,
            bt_entries_source_count=build_report.bt_entries_source_count,
            snapshot=terminal_snapshot("complete", "Lexicon build complete."),
        )

    thread = threading.Thread(target=worker, name="lexicon-build", daemon=True)
    thread.start()
    exit_code = 0
    try:
        if use_tui:
            app = LexiconBuildMonitorApp(
                controller=controller,
                db_path=resolved_index_db,
            )
            exit_code = app.run() or 0
        else:
            exit_code = 0
            while True:
                while True:
                    try:
                        event = controller.get_event_nowait()
                    except queue.Empty:
                        break
                    record_event(event)
                    if not quiet:
                        _render_plain_event(event)
                if terminal_event is not None and not thread.is_alive():
                    break
                if not thread.is_alive():
                    break
                if thread.is_alive():
                    thread.join(0.05)
    except KeyboardInterrupt:
        controller.request_cancel()
        exit_code = 130
    finally:
        thread.join()
        while True:
            try:
                event = controller.get_event_nowait()
            except queue.Empty:
                break
            record_event(event)
            if not quiet and not use_tui:
                _render_plain_event(event)

    if isinstance(terminal_event, BuildFinished) and build_report is not None:
        click.echo(
            "\n".join(
                [
                    "Lexicon build complete.",
                    f"index_db={resolved_index_db}",
                    f"built_at={build_report.built_at}",
                    f"forms_source_count={build_report.forms_source_count}",
                    f"bt_entries_source_count={build_report.bt_entries_source_count}",
                    f"entries_written={build_report.entries_written}",
                    f"forms_written={build_report.forms_written}",
                    f"search_keys_written={build_report.search_keys_written}",
                    f"pos_inferred={build_report.pos_inferred}",
                ]
            )
        )
        ctx.exit(exit_code)

    if isinstance(terminal_event, BuildCancelled):
        if quiet:
            click.echo("Lexicon build cancelled.", err=True)
        ctx.exit(130)

    if isinstance(terminal_event, BuildFailed):
        if quiet:
            click.echo(terminal_event.message, err=True)
        ctx.exit(1)

    ctx.exit(exit_code)


@lexicon_group.command(
    name="browse",
    help="Open the lexicon browse Textual shell.",
)
@click.option(
    "--index-db",
    type=click.Path(path_type=Path),
    default=None,
    help=(
        "SQLite index file path (overrides --index-dir and the OS app-data default)."
    ),
)
@click.option(
    "--index-dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help=(
        "Directory for morphology.sqlite3 (overrides the OS app-data default)."
    ),
)
@click.pass_context
def browse(
    ctx: click.Context,
    index_db: Path | None,
    index_dir: Path | None,
) -> None:
    """
    Launch the lexicon browse shell against the resolved morphology SQLite path.

    Args:
        ctx: Click context carrying loaded settings and global flags.
        index_db: Optional SQLite index file path override.
        index_dir: Optional SQLite index directory override.

    Raises:
        click.ClickException: Path resolution or browse app startup fails.

    """
    settings: Settings | None = ctx.obj.get("settings")
    app_data_dir = settings.app_data_dir if settings is not None else None
    resolved_index_db = resolve_morphology_index_db_path(
        index_db=index_db,
        index_dir=index_dir,
        app_data_dir=app_data_dir,
    )

    try:
        run_lexicon_browse(resolved_index_db)
    except LexiconBrowseDataError as exc:
        raise click.ClickException(str(exc)) from exc
    except OSError as exc:
        msg = f"Failed to launch lexicon browse from {resolved_index_db}: {exc}"
        raise click.ClickException(msg) from exc


def _render_plain_event(event: LexiconBuildEvent) -> None:
    """
    Render one lexicon build event to stderr in plain text.

    Args:
        event: Build event emitted by the shared runtime controller.

    """
    if isinstance(event, BuildStageStarted):
        detail = f" - {event.detail}" if event.detail else ""
        click.echo(
            f"[info] stage started: {event.stage.value} ({event.total}){detail}",
            err=True,
        )
    elif isinstance(event, BuildStageProgress):
        detail = f" - {event.detail}" if event.detail else ""
        current_item = f" [{event.current_item}]" if event.current_item else ""
        click.echo(
            f"[info] stage progress: {event.stage.value} "
            f"{event.completed}/{event.total}{detail}{current_item}",
            err=True,
        )
    elif isinstance(event, BuildCounterUpdated):
        click.echo(f"[info] {event.counter}={event.value}", err=True)
    elif isinstance(event, BuildLog):
        stage = f"{event.stage.value}: " if event.stage is not None else ""
        counts = ""
        if event.processed is not None and event.total is not None:
            counts = f" ({event.processed}/{event.total})"
        current_item = f" [{event.current_item}]" if event.current_item else ""
        click.echo(
            f"[{event.level}] {stage}{event.message}{counts}{current_item}",
            err=True,
        )
    elif isinstance(event, BuildFinished):
        click.echo(
            f"[info] build complete | forms={event.forms_source_count} "
            f"| entries={event.bt_entries_source_count}",
            err=True,
        )
    elif isinstance(event, BuildCancelled):
        click.echo(f"[warning] {event.message}", err=True)
    elif isinstance(event, BuildFailed):
        click.echo(f"[error] {event.error_type}: {event.message}", err=True)
