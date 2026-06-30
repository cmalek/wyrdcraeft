"""Textual build monitor for lexicon rebuild events."""

from __future__ import annotations

import queue
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from textual.app import App, ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.widgets import Static

if TYPE_CHECKING:
    from textual.binding import BindingType

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
    LexiconBuildEvent,
    LexiconBuildStage,
)

if TYPE_CHECKING:
    from wyrdcraeft.services.lexicon.build_runtime import LexiconBuildController

#: Maximum number of visible log lines retained by the monitor.
_LOG_HISTORY_LIMIT = 50
#: Poll interval used when draining controller events into the Textual app.
_POLL_INTERVAL_SECONDS = 0.1


@dataclass
class _StageState:
    """Mutable display state for one build stage row."""

    #: Stage lifecycle marker shown in the stage pane.
    state: str = "pending"
    #: Completed work units shown for the stage.
    completed: int = 0
    #: Total work units expected for the stage.
    total: int = 0
    #: Optional short detail rendered beside the progress counts.
    detail: str = ""


class LexiconBuildMonitorApp(App[int]):
    """
    Show one full-screen lexicon build monitor driven by typed events.

    Keyword Args:
        controller: Optional shared runtime controller feeding live events.
        db_path: Database path shown in the idle status line.

    """

    #: Minimal full-screen layout for the build monitor panes.
    CSS = """
    Screen {
        layout: vertical;
    }

    #build-body {
        height: 1fr;
        layout: horizontal;
    }

    #build-stage-pane, #build-log-pane {
        border: solid $accent;
        padding: 0 1;
    }

    #build-stage-pane {
        width: 1fr;
    }

    #build-log-pane {
        width: 2fr;
    }

    #build-log-scroll {
        height: 1fr;
    }
    """
    #: Key bindings for cooperative cancel and final-screen exit.
    BINDINGS: ClassVar[list[BindingType]] = [
        ("q", "quit_or_cancel", "Cancel or quit"),
        ("enter", "quit_or_cancel", "Quit"),
    ]

    #: Optional runtime controller feeding live events.
    controller: LexiconBuildController | None
    #: Database path associated with the current build.
    db_path: Path

    def __init__(
        self,
        *,
        controller: LexiconBuildController | None,
        db_path: Path,
    ) -> None:
        """
        Initialize one build monitor app.

        Keyword Args:
            controller: Optional shared runtime controller feeding live events.
            db_path: Database path associated with the current build.

        """
        super().__init__()
        #: Optional runtime controller feeding live events.
        self.controller = controller
        #: Database path associated with the current build.
        self.db_path = db_path
        #: Mutable stage display state keyed by stable stage order.
        self._stage_state = {
            stage: _StageState()
            for stage in LexiconBuildStage
        }
        #: Latest build counters shown in the sidebar.
        self._counters = BuildCounters()
        #: Latest lifecycle snapshot known to the UI.
        self._snapshot = BuildSnapshot(
            status="running",
            status_message=f"Waiting for build events from {db_path}.",
        )
        #: Terminal event held on screen until the user exits.
        self._terminal_event: BuildFinished | BuildCancelled | BuildFailed | None = None
        #: Exit code returned when the user exits after a terminal event.
        self._exit_code = 0
        #: Capped plain-text log history.
        self._log_lines: list[str] = []

    @classmethod
    def fake(cls) -> LexiconBuildMonitorApp:
        """
        Return a monitor with no live runtime for fake-feed tests.

        Returns:
            Test-friendly monitor app without a controller.

        """
        return cls(controller=None, db_path=Path("fake.sqlite3"))

    def compose(self) -> ComposeResult:
        """
        Compose the build monitor layout.

        Returns:
            Textual widget tree for stage summary and log panes.

        """
        yield Static("Lexicon Build Monitor", id="build-title")
        with Horizontal(id="build-body"):
            with Vertical(id="build-stage-pane"):
                yield Static(id="build-status")
                yield Static(id="build-counters")
                yield Static(id="build-stages")
            with Vertical(id="build-log-pane"):
                yield Static("Build Log", id="build-log-title")
                with ScrollableContainer(id="build-log-scroll"):
                    yield Static(id="build-log")

    def on_mount(self) -> None:
        """
        Cache widgets, render the idle view, and start queue polling.

        Side Effects:
            Stores widget references, renders the initial screen, and starts the
            runtime poll timer when a controller is present.

        """
        self._status_widget = self.query_one("#build-status", Static)
        self._counter_widget = self.query_one("#build-counters", Static)
        self._stage_widget = self.query_one("#build-stages", Static)
        self._log_widget = self.query_one("#build-log", Static)
        self._render_state()
        if self.controller is not None:
            self.set_interval(_POLL_INTERVAL_SECONDS, self._poll_events)

    def handle_event(self, event: LexiconBuildEvent, *, render: bool = True) -> None:
        """
        Update monitor state from one typed build event.

        Args:
            event: Build event emitted by the runtime or test feed.

        Keyword Args:
            render: When ``False``, skip an immediate re-render so callers can
                batch updates after draining many queued events.

        Side Effects:
            Mutates stage, counter, snapshot, and log state; may mark the app as
            terminal but does not exit automatically.

        """
        if isinstance(event, BuildStageStarted):
            self._mark_previous_active_done()
            self._snapshot = BuildSnapshot(
                status="running",
                active_stage=event.stage,
                counters=self._counters,
                status_message=event.detail or f"Running {event.stage.value}.",
            )
            self._stage_state[event.stage] = _StageState(
                state="active",
                completed=0,
                total=max(event.total, 1),
                detail=event.detail,
            )
            self._append_log(self._format_stage_start(event))
        elif isinstance(event, BuildStageProgress):
            stage_state = self._stage_state[event.stage]
            stage_state.state = (
                "done" if event.completed >= max(event.total, 1) else "active"
            )
            stage_state.completed = event.completed
            stage_state.total = max(event.total, 1)
            stage_state.detail = event.detail or event.current_item
            self._snapshot = BuildSnapshot(
                status=self._snapshot.status,
                active_stage=event.stage,
                counters=self._counters,
                status_message=stage_state.detail or f"Running {event.stage.value}.",
            )
        elif isinstance(event, BuildCounterUpdated):
            self._counters = BuildCounters(
                entries_written=(
                    event.value
                    if event.counter == "entries_written"
                    else self._counters.entries_written
                ),
                forms_written=(
                    event.value
                    if event.counter == "forms_written"
                    else self._counters.forms_written
                ),
                search_keys_written=(
                    event.value
                    if event.counter == "search_keys_written"
                    else self._counters.search_keys_written
                ),
                pos_inferred=(
                    event.value
                    if event.counter == "pos_inferred"
                    else self._counters.pos_inferred
                ),
            )
            self._snapshot = BuildSnapshot(
                status=self._snapshot.status,
                active_stage=self._snapshot.active_stage,
                counters=self._counters,
                status_message=self._snapshot.status_message,
            )
        elif isinstance(event, BuildLog):
            self._append_log(self._format_log(event))
        elif isinstance(event, BuildFinished):
            self._handle_terminal_event(event, exit_code=0)
        elif isinstance(event, BuildCancelled):
            self._handle_terminal_event(event, exit_code=130)
        elif isinstance(event, BuildFailed):
            self._handle_terminal_event(event, exit_code=1)
        if render:
            self._render_state()

    def action_quit_or_cancel(self) -> None:
        """
        Cancel the running build or exit after a terminal event.

        Side Effects:
            Requests cooperative cancellation from the controller while running,
            or exits the app once a terminal event is present.

        """
        if self._terminal_event is None:
            if self.controller is not None:
                self.controller.request_cancel()
            self._snapshot = BuildSnapshot(
                status="cancelling",
                active_stage=self._snapshot.active_stage,
                counters=self._counters,
                status_message="Cancellation requested. Waiting for worker...",
            )
            self._append_log("[warning] cancellation requested by user")
            self._render_state()
            return
        self.exit(self._exit_code)

    def _poll_events(self) -> None:
        """
        Drain queued runtime events without blocking the UI loop.

        Side Effects:
            Repeatedly consumes controller events and routes them through
            ``handle_event`` until the queue is empty.

        """
        if self.controller is None:
            return
        updated = False
        while True:
            try:
                event = self.controller.get_event_nowait()
            except queue.Empty:
                break
            self.handle_event(event, render=False)
            updated = True
        if updated:
            self._render_state()

    def _handle_terminal_event(
        self,
        event: BuildFinished | BuildCancelled | BuildFailed,
        *,
        exit_code: int,
    ) -> None:
        """
        Store one terminal event and expose its details on screen.

        Args:
            event: Terminal build event to hold on screen.

        Keyword Args:
            exit_code: Exit code returned after the user dismisses the app.

        Side Effects:
            Updates final snapshot state, marks the active stage done or failed,
            and appends any terminal log details including tracebacks.

        """
        self._terminal_event = event
        self._exit_code = exit_code
        self._counters = event.snapshot.counters
        self._snapshot = event.snapshot
        if event.snapshot.active_stage is not None:
            stage_state = self._stage_state[event.snapshot.active_stage]
            stage_state.state = "failed" if isinstance(event, BuildFailed) else "done"
            if stage_state.total and stage_state.completed < stage_state.total:
                stage_state.completed = stage_state.total
        if isinstance(event, BuildFinished):
            self._mark_previous_active_done()
            self._append_log(
                "[info] build complete"
                f" | forms={event.forms_source_count}"
                f" | entries={event.bt_entries_source_count}"
            )
        elif isinstance(event, BuildCancelled):
            self._append_log(f"[warning] {event.message}")
        else:
            self._append_log(f"[error] {event.error_type}: {event.message}")
            if event.traceback_text:
                for line in event.traceback_text.rstrip().splitlines():
                    self._append_log(line)

    def _mark_previous_active_done(self) -> None:
        """Mark any currently active stage as done before the next one starts."""
        for stage_state in self._stage_state.values():
            if stage_state.state == "active":
                stage_state.state = "done"
                if stage_state.total and stage_state.completed < stage_state.total:
                    stage_state.completed = stage_state.total

    def _append_log(self, line: str) -> None:
        """
        Add one line to the capped log history.

        Args:
            line: Plain-text line appended to the visible log history.

        Side Effects:
            Mutates the capped in-memory log buffer.

        """
        self._log_lines.append(line)
        if len(self._log_lines) > _LOG_HISTORY_LIMIT:
            self._log_lines = self._log_lines[-_LOG_HISTORY_LIMIT:]

    def _render_state(self) -> None:
        """
        Re-render the stage, counter, status, and log panes.

        Side Effects:
            Updates the mounted Textual widgets with the latest plain-text view.

        """
        self._status_widget.update(self._render_status())
        self._counter_widget.update(self._render_counters())
        self._stage_widget.update(self._render_stages())
        self._log_widget.update(
            "\n".join(self._log_lines) or "Waiting for log events."
        )

    def _render_status(self) -> str:
        """
        Return the current status block text.

        Returns:
            Plain-text status summary for the top of the left pane.

        """
        status = self._snapshot.status.upper()
        active_stage = (
            self._snapshot.active_stage.value
            if self._snapshot.active_stage is not None
            else "idle"
        )
        tail = (
            "Press q or Enter to exit."
            if self._terminal_event is not None
            else "Press q to cancel."
        )
        message = self._snapshot.status_message or "Waiting for build events."
        return (
            f"Status: {status}\n"
            f"Stage: {active_stage}\n"
            f"{message}\n"
            f"{tail}"
        )

    def _render_counters(self) -> str:
        """
        Return the current counter block text.

        Returns:
            Plain-text counter summary for the left pane.

        """
        return (
            "Counters\n"
            f"entries_written: {self._counters.entries_written}\n"
            f"forms_written: {self._counters.forms_written}\n"
            f"search_keys_written: {self._counters.search_keys_written}\n"
            f"pos_inferred: {self._counters.pos_inferred}"
        )

    def _render_stages(self) -> str:
        """
        Return the current stage list text.

        Returns:
            Plain-text rendering of all nine top-level build stages.

        """
        lines = ["Stages"]
        for stage in LexiconBuildStage:
            stage_state = self._stage_state[stage]
            marker = {
                "pending": "[ ]",
                "active": "[>]",
                "done": "[x]",
                "failed": "[!]",
            }[stage_state.state]
            progress = ""
            if stage_state.total:
                progress = f" {stage_state.completed}/{stage_state.total}"
            detail = f" - {stage_state.detail}" if stage_state.detail else ""
            lines.append(f"{marker} {stage.value}{progress}{detail}")
        return "\n".join(lines)

    def _format_stage_start(self, event: BuildStageStarted) -> str:
        """
        Return one log line for a stage-start event.

        Args:
            event: Stage-start event being logged.

        Returns:
            Plain-text stage-start log line.

        """
        detail = f" - {event.detail}" if event.detail else ""
        return f"[info] stage started: {event.stage.value} ({event.total}){detail}"

    def _format_log(self, event: BuildLog) -> str:
        """
        Return one plain-text line for a structured log event.

        Args:
            event: Structured build log event.

        Returns:
            Plain-text log line including stage and count context when present.

        """
        stage = f"{event.stage.value}: " if event.stage is not None else ""
        counts = ""
        if event.processed is not None and event.total is not None:
            counts = f" ({event.processed}/{event.total})"
        current_item = f" [{event.current_item}]" if event.current_item else ""
        return f"[{event.level}] {stage}{event.message}{counts}{current_item}"
