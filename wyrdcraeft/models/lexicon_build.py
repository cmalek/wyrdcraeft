"""Typed event models for lexicon build monitoring."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal


class LexiconBuildStage(StrEnum):
    """Stable stage labels emitted during one search-index rebuild."""

    #: Source-table verification stage label.
    VERIFY_SOURCES = "verify sources"
    #: POS inference stage label.
    INFER_POS = "infer pos"
    #: Dictionary search-key build stage label.
    BUILD_DICTIONARY_KEYS = "build dictionary keys"
    #: Morphology search-key build stage label.
    BUILD_MORPHOLOGY_KEYS = "build morphology keys"
    #: Search-key insert stage label.
    INSERT_SEARCH_KEYS = "insert search keys"
    #: Build-metadata write stage label.
    WRITE_META = "write metadata"


#: Allowed build lifecycle states for snapshots.
BuildStatus = Literal[
    "running",
    "cancelling",
    "cancelled",
    "failed",
    "complete",
]
#: Structured log severity values emitted by the build.
LogLevel = Literal["info", "warning", "error"]
#: Counter names tracked by typed counter events.
CounterName = Literal[
    "search_keys_written",
    "pos_inferred",
]


@dataclass(frozen=True)
class BuildCounters:
    """Monotonic counters accumulated while a build runs."""

    #: Number of rows inserted into ``search_keys``.
    search_keys_written: int = 0
    #: Number of dictionary entries whose POS was inferred.
    pos_inferred: int = 0


@dataclass(frozen=True)
class BuildSnapshot:
    """Summary state captured alongside terminal build events."""

    #: Current lifecycle state for the build.
    status: BuildStatus
    #: Current active stage when the snapshot was captured.
    active_stage: LexiconBuildStage | None = None
    #: Counters accumulated so far.
    counters: BuildCounters = field(default_factory=BuildCounters)
    #: Human-readable status detail for the current state.
    status_message: str = ""


@dataclass(frozen=True)
class BuildEvent:
    """Base event metadata common to every build event."""

    #: Monotonic event sequence emitted by one worker run.
    seq: int
    #: UTC timestamp in ISO-8601 ``Z`` form.
    at: str


@dataclass(frozen=True)
class BuildStageStarted(BuildEvent):
    """Stage-entered event with the known total for that stage."""

    #: Stage that just became active.
    stage: LexiconBuildStage
    #: Total work units expected for the stage.
    total: int
    #: Optional human-readable detail about the stage start.
    detail: str = ""


@dataclass(frozen=True)
class BuildStageProgress(BuildEvent):
    """Per-stage progress event for visible work advancement."""

    #: Stage receiving the progress update.
    stage: LexiconBuildStage
    #: Completed work units so far.
    completed: int
    #: Total work units expected for the stage.
    total: int
    #: Optional human-readable detail about the update.
    detail: str = ""
    #: Current item being processed when known.
    current_item: str = ""


@dataclass(frozen=True)
class BuildCounterUpdated(BuildEvent):
    """Dedicated counter update event for long-running stages."""

    #: Counter being updated.
    counter: CounterName
    #: New counter value.
    value: int
    #: Stage associated with the counter update when known.
    stage: LexiconBuildStage | None = None


@dataclass(frozen=True)
class BuildLog(BuildEvent):
    """Structured log line associated with the build timeline."""

    #: Stage associated with the log line when known.
    stage: LexiconBuildStage | None
    #: Severity level for the log line.
    level: LogLevel
    #: Human-readable log message.
    message: str
    #: Current item being processed when known.
    current_item: str = ""
    #: Processed count tied to the log line when known.
    processed: int | None = None
    #: Total count tied to the log line when known.
    total: int | None = None


@dataclass(frozen=True)
class BuildFinished(BuildEvent):
    """Successful terminal event for one completed build."""

    #: Final build snapshot.
    snapshot: BuildSnapshot
    #: UTC timestamp recorded in build metadata.
    built_at: str
    #: Source ``forms`` row count consumed by the build.
    forms_source_count: int
    #: Source ``bt_entries`` row count consumed by the build.
    bt_entries_source_count: int


@dataclass(frozen=True)
class BuildCancelled(BuildEvent):
    """Cancelled terminal event for one interrupted build."""

    #: Final build snapshot.
    snapshot: BuildSnapshot
    #: Human-readable cancellation reason.
    message: str


@dataclass(frozen=True)
class BuildFailed(BuildEvent):
    """Failed terminal event for one build exception."""

    #: Final build snapshot.
    snapshot: BuildSnapshot
    #: Exception type name.
    error_type: str
    #: Human-readable exception message.
    message: str
    #: Rendered traceback text when available.
    traceback_text: str = ""


#: Closed union of all build event dataclasses.
LexiconBuildEvent = (
    BuildStageStarted
    | BuildStageProgress
    | BuildCounterUpdated
    | BuildLog
    | BuildFinished
    | BuildCancelled
    | BuildFailed
)
