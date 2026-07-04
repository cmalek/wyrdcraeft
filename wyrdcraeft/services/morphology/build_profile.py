"""Wall-clock profiling helpers for morphology build runs."""

from __future__ import annotations

import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from time import perf_counter
from typing import TYPE_CHECKING

from .progress import MorphologyGenerateProgressCoordinator, MorphologyStage

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from typing import TextIO


@dataclass
class _StageTiming:
    """Accumulated wall time and emitted rows for one generation stage."""

    #: Elapsed wall seconds for the stage.
    seconds: float = 0.0
    #: Emitted morphology rows attributed to the stage.
    rows: int = 0


@dataclass
class MorphologyBuildProfiler:
    """
    Collect morphology build timings and render one stderr summary table.

    Args:
        enabled: Whether timing collection and summary output are active.

    """

    #: Whether timing collection and summary output are active.
    enabled: bool
    #: Monotonic start time for the full build profile window.
    _build_started_at: float = field(init=False)
    #: Accumulated setup-step wall times keyed by label.
    _setup_seconds: dict[str, float] = field(default_factory=dict)
    #: Accumulated generation-stage timings keyed by stage label.
    _stage_timings: dict[str, _StageTiming] = field(default_factory=dict)
    #: Total wall seconds spent in SQLite bulk flushes.
    _sqlite_flush_seconds: float = 0.0
    #: Total rows inserted during SQLite bulk flushes.
    _sqlite_flush_rows: int = 0
    #: Active generation stage, when one is running.
    _active_stage: MorphologyStage | None = field(default=None, init=False)
    #: Monotonic start time for the active generation stage.
    _stage_started_at: float = field(default=0.0, init=False)
    #: Session ``output_counter`` value at active stage entry.
    _forms_at_stage_start: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        """Capture the build start timestamp when profiling is enabled."""
        self._build_started_at = perf_counter() if self.enabled else 0.0

    @contextmanager
    def time_setup(self, label: str) -> Iterator[None]:
        """
        Measure one setup step when profiling is enabled.

        Args:
            label: Setup step label shown in the profile summary.

        Yields:
            Control back to the wrapped setup block.

        """
        if not self.enabled:
            yield
            return
        started_at = perf_counter()
        try:
            yield
        finally:
            elapsed = perf_counter() - started_at
            self._setup_seconds[label] = self._setup_seconds.get(label, 0.0) + elapsed

    def begin_stage(self, stage: MorphologyStage, *, forms_written: int) -> None:
        """
        Start wall-clock timing for one generation stage.

        Args:
            stage: Stage being entered.

        Keyword Args:
            forms_written: Current session output counter at stage entry.

        """
        if not self.enabled:
            return
        self._active_stage = stage
        self._stage_started_at = perf_counter()
        self._forms_at_stage_start = forms_written

    def end_stage(self, stage: MorphologyStage, *, forms_written: int) -> None:
        """
        Finish wall-clock timing for one generation stage.

        Args:
            stage: Stage being exited.

        Keyword Args:
            forms_written: Current session output counter at stage exit.

        """
        if not self.enabled:
            return
        timing = self._stage_timings.setdefault(stage.value, _StageTiming())
        timing.seconds += perf_counter() - self._stage_started_at
        timing.rows += max(forms_written - self._forms_at_stage_start, 0)
        self._active_stage = None

    def record_sqlite_flush(self, seconds: float, row_count: int) -> None:
        """
        Accumulate SQLite bulk-flush timing separately from generation stages.

        Args:
            seconds: Wall seconds spent in one flush transaction.
            row_count: Number of rows inserted in that flush.

        """
        if not self.enabled:
            return
        self._sqlite_flush_seconds += seconds
        self._sqlite_flush_rows += row_count

    def sqlite_flush_observer(self) -> Callable[[float, int], None] | None:
        """
        Return a sink callback for SQLite flush timing, when profiling is enabled.

        Returns:
            Callback accepting ``(seconds, row_count)``, or ``None`` when disabled.

        """
        if not self.enabled:
            return None
        return self.record_sqlite_flush

    def emit_summary(self, *, forms_written: int, file: TextIO | None = None) -> None:
        """
        Render the morphology build profile table.

        Keyword Args:
            forms_written: Final session output counter for the build.
            file: Optional output stream; defaults to ``stderr``.

        Side Effects:
            Writes one formatted timing summary when profiling is enabled.

        """
        if not self.enabled:
            return
        output = file or sys.stderr
        total_seconds = perf_counter() - self._build_started_at
        lines = [
            "Morphology build profile",
            "",
            f"{'stage':<14} {'seconds':>9} {'rows':>10} {'rows/s':>10}",
        ]
        for stage in MorphologyGenerateProgressCoordinator.STAGE_ORDER:
            timing = self._stage_timings.get(stage.value, _StageTiming())
            rows_per_second = _rows_per_second(timing.rows, timing.seconds)
            lines.append(
                f"{stage.value:<14} "
                f"{timing.seconds:9.2f} "
                f"{timing.rows:10d} "
                f"{rows_per_second:10.1f}"
            )
        lines.extend(["", "setup"])
        setup_total = 0.0
        for label, seconds in self._setup_seconds.items():
            lines.append(f"  {label:<28} {seconds:9.2f}")
            setup_total += seconds
        lines.append(f"  {'(total)':<28} {setup_total:9.2f}")
        sqlite_rows_per_second = _rows_per_second(
            self._sqlite_flush_rows,
            self._sqlite_flush_seconds,
        )
        lines.extend(
            [
                "",
                f"{'sqlite_flush':<14} "
                f"{self._sqlite_flush_seconds:9.2f} "
                f"{self._sqlite_flush_rows:10d} "
                f"{sqlite_rows_per_second:10.1f}",
                f"{'total':<14} "
                f"{total_seconds:9.2f} "
                f"{forms_written:10d} "
                f"{_rows_per_second(forms_written, total_seconds):10.1f}",
            ]
        )
        output.write("\n".join(lines) + "\n")


def _rows_per_second(rows: int, seconds: float) -> float:
    """
    Compute a safe rows-per-second rate for profile output.

    Args:
        rows: Row count attributed to the timed slice.
        seconds: Elapsed wall seconds for the slice.

    Returns:
        Rows per second, or ``0.0`` when ``seconds`` is not positive.

    """
    if seconds <= 0:
        return 0.0
    return rows / seconds
