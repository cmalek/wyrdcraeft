"""Typed stage and event models for unified dictionary builds."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal


class DictionaryBuildStage(StrEnum):
    """Stable stage labels emitted during one unified dictionary build."""

    #: Canonical-schema migration stage label.
    ENSURE_SCHEMA = "ensure schema"
    #: Bosworth-Toller rebuild stage label.
    REBUILD_DICTIONARY = "rebuild dictionary"
    #: Existing morphology form relink stage label.
    RELINK_FORMS = "relink forms"
    #: Optional morphology regeneration stage label.
    REBUILD_MORPHOLOGY = "rebuild morphology"
    #: Missing dictionary POS inference stage label.
    INFER_POS = "infer pos"


#: Allowed build lifecycle states for emitted snapshots.
DictionaryBuildStatus = Literal["running", "failed", "complete"]
#: Structured log severity values emitted by the build.
DictionaryBuildLogLevel = Literal["info", "warning", "error"]


@dataclass(frozen=True)
class DictionaryBuildCounters:
    """Monotonic counters accumulated while one build runs."""

    #: Number of Bosworth-Toller entries written in the rebuild stage.
    bt_entries_written: int = 0
    #: Number of stale ``forms.entry_id`` values cleared pre-rebuild.
    entry_ids_cleared: int = 0
    #: Number of form rows processed by the relink stage.
    entry_ids_linked: int = 0
    #: Number of dictionary rows whose POS was inferred from morphology.
    pos_inferred: int = 0


@dataclass(frozen=True)
class DictionaryBuildSnapshot:
    """Summary state captured alongside terminal build events."""

    #: Current lifecycle state for the build.
    status: DictionaryBuildStatus
    #: Current active stage when the snapshot was captured.
    active_stage: DictionaryBuildStage | None = None
    #: Counters accumulated so far.
    counters: DictionaryBuildCounters = field(default_factory=DictionaryBuildCounters)
    #: Human-readable status detail for the current state.
    status_message: str = ""


@dataclass(frozen=True)
class DictionaryBuildEvent:
    """Base event metadata common to every dictionary-build event."""

    #: Monotonic event sequence emitted by one worker run.
    seq: int
    #: UTC timestamp in ISO-8601 ``Z`` form.
    at: str


@dataclass(frozen=True)
class DictionaryBuildStageStarted(DictionaryBuildEvent):
    """Stage-entered event with the known total for that stage."""

    #: Stage that just became active.
    stage: DictionaryBuildStage
    #: Total work units expected for the stage.
    total: int
    #: Optional human-readable detail about the stage start.
    detail: str = ""


@dataclass(frozen=True)
class DictionaryBuildStageProgress(DictionaryBuildEvent):
    """Per-stage progress event for visible work advancement."""

    #: Stage receiving the progress update.
    stage: DictionaryBuildStage
    #: Completed work units so far.
    completed: int
    #: Total work units expected for the stage.
    total: int
    #: Optional human-readable progress detail.
    detail: str = ""
    #: Optional active item being processed.
    current_item: str = ""


@dataclass(frozen=True)
class DictionaryBuildLog(DictionaryBuildEvent):
    """Structured log line associated with the build timeline."""

    #: Stage associated with the log line when known.
    stage: DictionaryBuildStage | None
    #: Severity level for the log line.
    level: DictionaryBuildLogLevel
    #: Human-readable log message.
    message: str
    #: Current item being processed when known.
    current_item: str = ""


@dataclass(frozen=True)
class DictionaryBuildFinished(DictionaryBuildEvent):
    """Successful terminal event for one completed dictionary build."""

    #: Final build snapshot.
    snapshot: DictionaryBuildSnapshot
    #: UTC timestamp recorded in build metadata.
    built_at: str


#: Closed union of all dictionary-build event dataclasses.
AnyDictionaryBuildEvent = (
    DictionaryBuildStageStarted
    | DictionaryBuildStageProgress
    | DictionaryBuildLog
    | DictionaryBuildFinished
)
