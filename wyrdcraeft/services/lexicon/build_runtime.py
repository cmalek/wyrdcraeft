"""Shared runtime controller for lexicon build monitoring."""

from __future__ import annotations

import queue
import threading
import traceback
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from wyrdcraeft.models.lexicon_build import (
    BuildCancelled,
    BuildCounters,
    BuildFailed,
    BuildFinished,
    BuildSnapshot,
    BuildStatus,
    LexiconBuildEvent,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


class LexiconBuildController:
    """
    Own the worker-event queue and terminal-event guarantees for one build.

    Args:
        db_path: Lexicon database path for the requested build.
        quiet: Whether live output should be suppressed.

    """

    #: Optional database path associated with the build request.
    db_path: Path | None
    #: Whether live output should stay quiet for this run.
    quiet: bool

    def __init__(self, *, db_path: Path | None, quiet: bool) -> None:
        """
        Initialize one controller for one lexicon build run.

        Keyword Args:
            db_path: Lexicon database path for the requested build.
            quiet: Whether live output should be suppressed.

        """
        #: Optional database path associated with the build request.
        self.db_path = db_path
        #: Whether live output should stay quiet for this run.
        self.quiet = quiet
        #: Cross-thread event queue drained by the main thread.
        self._queue: queue.SimpleQueue[LexiconBuildEvent] = queue.SimpleQueue()
        #: Cooperative cancellation flag shared with the worker.
        self._cancel_event = threading.Event()
        #: Optional callback used to interrupt the active worker operation.
        self._interrupt_callback: Callable[[], None] | None = None
        #: Monotonic sequence counter for emitted events.
        self._seq = 0
        #: Guard ensuring only one terminal event is emitted.
        self._terminal_event_seen = False

    @property
    def cancel_requested(self) -> bool:
        """
        Return whether cooperative cancellation has been requested.

        Returns:
            ``True`` when cancellation has been requested.

        """
        return self._cancel_event.is_set()

    @property
    def cancel_event(self) -> threading.Event:
        """
        Expose the shared cancellation event for worker code.

        Returns:
            Shared cancellation event for cooperative worker checks.

        """
        return self._cancel_event

    def set_interrupt_callback(self, callback: Callable[[], None] | None) -> None:
        """
        Register the callback used to interrupt the active worker operation.

        Args:
            callback: Callable invoked after cancellation is requested.

        """
        self._interrupt_callback = callback

    def request_cancel(self) -> None:
        """Mark the build cancelled and interrupt the worker if possible."""
        self._cancel_event.set()
        if self._interrupt_callback is not None:
            self._interrupt_callback()

    def emit(self, event: LexiconBuildEvent) -> None:
        """
        Queue one event for the main thread to consume.

        Args:
            event: Typed build event to enqueue.

        """
        self._queue.put(event)

    def get_event_nowait(self) -> LexiconBuildEvent:
        """
        Return the next queued event without blocking.

        Returns:
            Next queued build event.

        """
        return self._queue.get_nowait()

    def emit_finished(
        self,
        *,
        built_at: str,
        forms_source_count: int,
        bt_entries_source_count: int,
        snapshot: BuildSnapshot | None = None,
    ) -> None:
        """
        Emit the terminal success event when no terminal event exists yet.

        Keyword Args:
            built_at: UTC build timestamp written to metadata.
            forms_source_count: Source ``forms`` row count.
            bt_entries_source_count: Source ``bt_entries`` row count.
            snapshot: Optional final snapshot override.

        """
        final_snapshot = snapshot or self._snapshot(status="complete")
        self._emit_terminal(
            BuildFinished(
                seq=self._next_seq(),
                at=self._now(),
                snapshot=final_snapshot,
                built_at=built_at,
                forms_source_count=forms_source_count,
                bt_entries_source_count=bt_entries_source_count,
            )
        )

    def emit_cancelled(
        self,
        *,
        message: str = "Build cancelled.",
        snapshot: BuildSnapshot | None = None,
    ) -> None:
        """
        Emit the terminal cancelled event when no terminal event exists yet.

        Keyword Args:
            message: Human-readable cancellation reason.
            snapshot: Optional final snapshot override.

        """
        final_snapshot = snapshot or self._snapshot(
            status="cancelled",
            status_message=message,
        )
        self._emit_terminal(
            BuildCancelled(
                seq=self._next_seq(),
                at=self._now(),
                snapshot=final_snapshot,
                message=message,
            )
        )

    def emit_failed(
        self,
        exc: BaseException,
        *,
        snapshot: BuildSnapshot | None = None,
    ) -> None:
        """
        Emit the terminal failure event when no terminal event exists yet.

        Args:
            exc: Exception raised by the worker.

        Keyword Args:
            snapshot: Optional final snapshot override.

        """
        final_snapshot = snapshot or self._snapshot(
            status="failed",
            status_message=str(exc),
        )
        self._emit_terminal(
            BuildFailed(
                seq=self._next_seq(),
                at=self._now(),
                snapshot=final_snapshot,
                error_type=type(exc).__name__,
                message=str(exc),
                traceback_text="".join(
                    traceback.format_exception(type(exc), exc, exc.__traceback__)
                ),
            )
        )

    def _emit_success_for_test_only(self) -> None:
        """Emit a synthetic success event for unit tests."""
        self.emit_finished(
            built_at="2026-06-28T12:00:00Z",
            forms_source_count=0,
            bt_entries_source_count=0,
        )

    def _emit_failure_for_test_only(self, exc: BaseException) -> None:
        """
        Emit a synthetic failure event for unit tests.

        Args:
            exc: Exception to wrap in a failed terminal event.

        """
        self.emit_failed(exc)

    def _emit_terminal(
        self,
        event: BuildFinished | BuildCancelled | BuildFailed,
    ) -> None:
        """
        Queue exactly one terminal event for the controller lifetime.

        Args:
            event: Terminal build event to enqueue.

        """
        if self._terminal_event_seen:
            return
        self._terminal_event_seen = True
        self.emit(event)

    def _snapshot(
        self,
        *,
        status: BuildStatus,
        status_message: str = "",
    ) -> BuildSnapshot:
        """
        Build a minimal final snapshot for runtime-owned terminal events.

        Keyword Args:
            status: Lifecycle state for the snapshot.
            status_message: Optional human-readable detail.

        Returns:
            Minimal snapshot with zeroed counters.

        """
        return BuildSnapshot(
            status=status,
            counters=BuildCounters(),
            status_message=status_message,
        )

    def _next_seq(self) -> int:
        """
        Return the next monotonic event sequence number.

        Returns:
            Next event sequence number.

        """
        self._seq += 1
        return self._seq

    def _now(self) -> str:
        """
        Return the current UTC timestamp in ISO-8601 ``Z`` form.

        Returns:
            Current UTC timestamp formatted for event payloads.

        """
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace(
            "+00:00",
            "Z",
        )
