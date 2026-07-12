# Lexicon Build Monitor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `wyrdcraeft lexicon build` launch a full-screen Textual build monitor by default, with live stage progress, structured logs, and reliable cancel/interrupt behavior.

**Architecture:** Keep `rebuild_lexicon(...)` as the single build entrypoint, but expand it to emit typed build events and honor cooperative cancellation. Run that build inside one shared worker-thread controller used by both the Textual monitor and a plain non-TUI fallback. Stream large `forms` and `search_keys` stages through SQLite TEMP staging tables so progress remains visible, cancellation stays responsive, and Python does not hold giant intermediate lists.

**Tech Stack:** `click`, `textual`, `sqlite3`, `threading`, `queue.SimpleQueue`, existing lexicon build service layer, existing lexicon browse TUI test patterns

---

## File Map

**Create:**
- `wyrdcraeft/models/lexicon_build.py`
- `wyrdcraeft/services/lexicon/build_runtime.py`
- `wyrdcraeft/services/lexicon/build_monitor.py`
- `tests/lexicon/test_build_runtime.py`

**Modify:**
- `wyrdcraeft/cli/lexicon.py`
- `wyrdcraeft/models/__init__.py`
- `wyrdcraeft/services/lexicon/__init__.py`
- `wyrdcraeft/services/lexicon/build.py`
- `wyrdcraeft/services/lexicon/progress.py`
- `wyrdcraeft/services/lexicon/schema.py`
- `tests/test_cli_lexicon.py`
- `tests/lexicon/test_build.py`
- `tests/lexicon/test_progress.py`
- `tests/lexicon/test_tui.py`
- `doc/source/overview/command_lexicon_build.rst`

**Avoid touching unless clearly necessary:**
- `wyrdcraeft/services/lexicon/tui.py`
  Keep browse shell stable. Do not mix build-monitor threading/runtime logic into browse shell code.

## Locked Decisions

- Use one shared `threading.Thread` runtime for both TUI and `--no-tui`.
- Use `queue.SimpleQueue` for cross-thread event delivery.
- Keep current 9 top-level build stages.
- Put event models in `wyrdcraeft/models/lexicon_build.py`.
- Use closed union dataclasses, not one optional-field event bag.
- Use dedicated typed counter events.
- Use structured log events, not preformatted strings.
- Stamp events in worker thread with `seq` and `at`.
- Keep `entries` path mostly in Python memory.
- Stream `forms` and `search_keys` via SQLite TEMP staging tables.
- Build search keys from inserted lexicon tables / staging state, not giant Python lists.
- Move search-key dedupe to SQLite with expression unique indexes plus `INSERT OR IGNORE`.
- Keep `SCHEMA_VERSION` unchanged.
- Main thread owns cancel requests and calls runtime `request_cancel()`.
- Service raises `LexiconBuildCancelledError` for cooperative cancel.
- Cancel/fail rolls back whole rebuild transaction.
- Default TTY path launches TUI.
- `--no-tui` forces plain stderr/stdout renderer.
- `--quiet` suppresses live output only; keep final summary on `stdout`.
- Exit codes: success `0`, cancel `130`, failure `1`.
- Keep current final summary field names/order.
- TUI holds final screen until exit keypress.
- `q` during run requests cancel; `q`/Enter on final screen exits.
- Right log pane retains fixed capped history and drops oldest lines.
- TUI tests use fake event feeds; worker/runtime behavior lives in service tests.
- No ADR for this change.
- No `CONTEXT.md` update for this change.

## Task 1: Define Build Event Models

**Files:**
- Create: `wyrdcraeft/models/lexicon_build.py`
- Modify: `wyrdcraeft/models/__init__.py`
- Test: `tests/lexicon/test_progress.py`

- [ ] **Step 1: Rewrite progress tests around typed event models**

```python
from wyrdcraeft.models.lexicon_build import (
    BuildCounters,
    BuildFailed,
    BuildFinished,
    BuildLog,
    BuildSnapshot,
    BuildStageProgress,
    BuildStageStarted,
    LexiconBuildStage,
)


def test_stage_order_remains_stable() -> None:
    assert list(LexiconBuildStage) == [
        LexiconBuildStage.VERIFY_SOURCES,
        LexiconBuildStage.INFER_POS,
        LexiconBuildStage.LOAD_ENTRIES,
        LexiconBuildStage.INSERT_ENTRIES,
        LexiconBuildStage.LOAD_FORMS,
        LexiconBuildStage.INSERT_FORMS,
        LexiconBuildStage.BUILD_SEARCH_KEYS,
        LexiconBuildStage.INSERT_SEARCH_KEYS,
        LexiconBuildStage.WRITE_META,
    ]


def test_terminal_events_carry_final_snapshot() -> None:
    snapshot = BuildSnapshot(
        status="failed",
        active_stage=LexiconBuildStage.LOAD_FORMS,
        counters=BuildCounters(forms_written=0, search_keys_written=0),
    )
    event = BuildFailed(
        seq=10,
        at="2026-06-28T12:00:00Z",
        snapshot=snapshot,
        error_type="RuntimeError",
        message="boom",
        traceback_text="Traceback...",
    )
    assert event.snapshot.status == "failed"
    assert event.error_type == "RuntimeError"


def test_log_event_keeps_structured_current_work() -> None:
    event = BuildLog(
        seq=3,
        at="2026-06-28T12:00:00Z",
        stage=LexiconBuildStage.LOAD_FORMS,
        level="info",
        message="heartbeat",
        current_item="abbad",
        processed=5000,
        total=420000,
    )
    assert event.current_item == "abbad"
    assert event.processed == 5000
```

- [ ] **Step 2: Run targeted tests to confirm they fail before model code exists**

Run:

```bash
rtk test /Users/cmalek/src/workspace/wyrdcraeft/.venv/bin/pytest /Users/cmalek/src/workspace/wyrdcraeft/tests/lexicon/test_progress.py -q
```

Expected: FAIL with import errors or missing symbols from `wyrdcraeft.models.lexicon_build`.

- [ ] **Step 3: Create minimal event model module**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal, TypeAlias


class LexiconBuildStage(StrEnum):
    VERIFY_SOURCES = "verify sources"
    INFER_POS = "infer pos"
    LOAD_ENTRIES = "load entries"
    INSERT_ENTRIES = "insert entries"
    LOAD_FORMS = "load forms"
    INSERT_FORMS = "insert forms"
    BUILD_SEARCH_KEYS = "build search keys"
    INSERT_SEARCH_KEYS = "insert search keys"
    WRITE_META = "write metadata"


BuildStatus: TypeAlias = Literal["running", "cancelling", "cancelled", "failed", "complete"]
LogLevel: TypeAlias = Literal["info", "warning", "error"]
CounterName: TypeAlias = Literal[
    "entries_written",
    "forms_written",
    "search_keys_written",
    "pos_inferred",
]


@dataclass(frozen=True)
class BuildCounters:
    entries_written: int = 0
    forms_written: int = 0
    search_keys_written: int = 0
    pos_inferred: int = 0


@dataclass(frozen=True)
class BuildSnapshot:
    status: BuildStatus
    active_stage: LexiconBuildStage | None = None
    counters: BuildCounters = field(default_factory=BuildCounters)
    status_message: str = ""


@dataclass(frozen=True)
class BuildEvent:
    seq: int
    at: str


@dataclass(frozen=True)
class BuildStageStarted(BuildEvent):
    stage: LexiconBuildStage
    total: int
    detail: str = ""


@dataclass(frozen=True)
class BuildStageProgress(BuildEvent):
    stage: LexiconBuildStage
    completed: int
    total: int
    detail: str = ""
    current_item: str = ""


@dataclass(frozen=True)
class BuildCounterUpdated(BuildEvent):
    counter: CounterName
    value: int
    stage: LexiconBuildStage | None = None


@dataclass(frozen=True)
class BuildLog(BuildEvent):
    stage: LexiconBuildStage | None
    level: LogLevel
    message: str
    current_item: str = ""
    processed: int | None = None
    total: int | None = None


@dataclass(frozen=True)
class BuildFinished(BuildEvent):
    snapshot: BuildSnapshot
    built_at: str
    forms_source_count: int
    bt_entries_source_count: int


@dataclass(frozen=True)
class BuildCancelled(BuildEvent):
    snapshot: BuildSnapshot
    message: str


@dataclass(frozen=True)
class BuildFailed(BuildEvent):
    snapshot: BuildSnapshot
    error_type: str
    message: str
    traceback_text: str = ""


LexiconBuildEvent: TypeAlias = (
    BuildStageStarted
    | BuildStageProgress
    | BuildCounterUpdated
    | BuildLog
    | BuildFinished
    | BuildCancelled
    | BuildFailed
)
```

- [ ] **Step 4: Export model symbols used outside the module**

```python
from .lexicon_build import (
    BuildCancelled,
    BuildCounterUpdated,
    BuildCounters,
    BuildEvent,
    BuildFailed,
    BuildFinished,
    BuildLog,
    BuildSnapshot,
    BuildStageProgress,
    BuildStageStarted,
    LexiconBuildEvent,
    LexiconBuildStage,
)
```

- [ ] **Step 5: Re-run event-model tests**

Run:

```bash
rtk test /Users/cmalek/src/workspace/wyrdcraeft/.venv/bin/pytest /Users/cmalek/src/workspace/wyrdcraeft/tests/lexicon/test_progress.py -q
```

Expected: PASS.

Suggested commit: `Add lexicon build event models`

### Task 2: Build Shared Runtime Controller

**Files:**
- Create: `wyrdcraeft/services/lexicon/build_runtime.py`
- Test: `tests/lexicon/test_build_runtime.py`

- [ ] **Step 1: Write failing runtime tests for terminal-event guarantee and cancel hook**

```python
from __future__ import annotations

from wyrdcraeft.models.lexicon_build import BuildCancelled, BuildFailed, BuildFinished
from wyrdcraeft.services.lexicon.build_runtime import LexiconBuildController


def test_controller_emits_finished_terminal_event(tmp_path) -> None:
    controller = LexiconBuildController(db_path=tmp_path / "demo.sqlite3", quiet=True)
    controller._emit_success_for_test_only()
    event = controller.get_event_nowait()
    assert isinstance(event, BuildFinished)


def test_controller_request_cancel_sets_flag_and_calls_interrupt() -> None:
    controller = LexiconBuildController(db_path=None, quiet=True)
    called: list[str] = []
    controller.set_interrupt_callback(lambda: called.append("interrupt"))
    controller.request_cancel()
    assert controller.cancel_requested is True
    assert called == ["interrupt"]


def test_controller_wraps_unhandled_exception_into_failed_event(tmp_path) -> None:
    controller = LexiconBuildController(db_path=tmp_path / "demo.sqlite3", quiet=True)
    controller._emit_failure_for_test_only(RuntimeError("boom"))
    event = controller.get_event_nowait()
    assert isinstance(event, BuildFailed)
    assert event.error_type == "RuntimeError"
```

- [ ] **Step 2: Run runtime tests and confirm they fail before controller exists**

Run:

```bash
rtk test /Users/cmalek/src/workspace/wyrdcraeft/.venv/bin/pytest /Users/cmalek/src/workspace/wyrdcraeft/tests/lexicon/test_build_runtime.py -q
```

Expected: FAIL with missing module or symbols.

- [ ] **Step 3: Implement the controller skeleton**

```python
from __future__ import annotations

import queue
import threading
import traceback
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

from wyrdcraeft.models.lexicon_build import (
    BuildCancelled,
    BuildCounters,
    BuildFailed,
    BuildFinished,
    BuildSnapshot,
    LexiconBuildEvent,
)


class LexiconBuildController:
    def __init__(self, *, db_path: Path | None, quiet: bool) -> None:
        self.db_path = db_path
        self.quiet = quiet
        self._queue: queue.SimpleQueue[LexiconBuildEvent] = queue.SimpleQueue()
        self._cancel_event = threading.Event()
        self._interrupt_callback: Callable[[], None] | None = None
        self._seq = 0
        self._terminal_event_seen = False

    @property
    def cancel_requested(self) -> bool:
        return self._cancel_event.is_set()

    @property
    def cancel_event(self) -> threading.Event:
        return self._cancel_event

    def set_interrupt_callback(self, callback: Callable[[], None] | None) -> None:
        self._interrupt_callback = callback

    def request_cancel(self) -> None:
        self._cancel_event.set()
        if self._interrupt_callback is not None:
            self._interrupt_callback()

    def emit(self, event: LexiconBuildEvent) -> None:
        self._queue.put(event)

    def get_event_nowait(self) -> LexiconBuildEvent:
        return self._queue.get_nowait()
```

- [ ] **Step 4: Implement worker wrapper methods that always emit exactly one terminal event**

```python
    def _now(self) -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    def emit_failed(self, exc: BaseException, snapshot: BuildSnapshot) -> None:
        if self._terminal_event_seen:
            return
        self._terminal_event_seen = True
        self.emit(
            BuildFailed(
                seq=self._next_seq(),
                at=self._now(),
                snapshot=snapshot,
                error_type=type(exc).__name__,
                message=str(exc),
                traceback_text="".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
            )
        )
```

- [ ] **Step 5: Re-run runtime tests**

Run:

```bash
rtk test /Users/cmalek/src/workspace/wyrdcraeft/.venv/bin/pytest /Users/cmalek/src/workspace/wyrdcraeft/tests/lexicon/test_build_runtime.py -q
```

Expected: PASS.

Suggested commit: `Add shared lexicon build runtime controller`

### Task 3: Expand `rebuild_lexicon(...)` Contract for Events and Cancel

**Files:**
- Modify: `wyrdcraeft/services/lexicon/build.py`
- Modify: `wyrdcraeft/services/lexicon/__init__.py`
- Test: `tests/lexicon/test_build.py`

- [ ] **Step 1: Add failing tests for structured events and cooperative cancel**

```python
from __future__ import annotations

import threading

import pytest

from wyrdcraeft.models.lexicon_build import BuildCounterUpdated, BuildStageStarted, LexiconBuildStage
from wyrdcraeft.services.lexicon.build import LexiconBuildCancelledError, rebuild_lexicon


def test_rebuild_lexicon_emits_structured_stage_and_counter_events(lexicon_source_db) -> None:
    events = []
    report = rebuild_lexicon(lexicon_source_db, event_sink=events.append)
    assert report.entries_written > 0
    assert any(isinstance(event, BuildStageStarted) for event in events)
    assert any(
        isinstance(event, BuildCounterUpdated)
        and event.counter == "search_keys_written"
        for event in events
    )


def test_rebuild_lexicon_raises_cancelled_error_when_cancel_requested(lexicon_source_db) -> None:
    cancel_event = threading.Event()
    events = []

    def sink(event) -> None:
        events.append(event)
        if getattr(event, "stage", None) == LexiconBuildStage.LOAD_FORMS:
            cancel_event.set()

    with pytest.raises(LexiconBuildCancelledError):
        rebuild_lexicon(
            lexicon_source_db,
            event_sink=sink,
            cancel_event=cancel_event,
        )
```

- [ ] **Step 2: Run build tests to confirm the new contract is not implemented yet**

Run:

```bash
rtk test /Users/cmalek/src/workspace/wyrdcraeft/.venv/bin/pytest /Users/cmalek/src/workspace/wyrdcraeft/tests/lexicon/test_build.py -q
```

Expected: FAIL because `rebuild_lexicon(...)` does not accept `event_sink` / `cancel_event`, and `LexiconBuildCancelledError` does not exist.

- [ ] **Step 3: Introduce worker-safe cancel exception and event sink types**

```python
from collections.abc import Callable
import threading

from wyrdcraeft.models.lexicon_build import (
    BuildCounterUpdated,
    BuildLog,
    BuildStageProgress,
    BuildStageStarted,
    LexiconBuildEvent,
    LexiconBuildStage,
)

LexiconBuildEventSink = Callable[[LexiconBuildEvent], None]


class LexiconBuildCancelledError(RuntimeError):
    """Raised when a cooperative build cancellation request is honored."""
```

- [ ] **Step 4: Expand `LexiconBuilder` and `rebuild_lexicon(...)` signatures**

```python
def rebuild_lexicon(
    db_path: Path,
    *,
    event_sink: LexiconBuildEventSink | None = None,
    cancel_event: threading.Event | None = None,
    runtime: LexiconBuildController | None = None,
) -> BuildReport:
    return LexiconBuilder(
        db_path,
        event_sink=event_sink,
        cancel_event=cancel_event,
        runtime=runtime,
    ).rebuild()
```

- [ ] **Step 5: Remove `signal.signal(...)` ownership from build core**

```python
with sqlite3.connect(str(self._db_path)) as connection:
    if self._runtime is not None:
        self._runtime.set_interrupt_callback(connection.interrupt)
    try:
        ...
    finally:
        if self._runtime is not None:
            self._runtime.set_interrupt_callback(None)
```

- [ ] **Step 6: Add central cooperative cancel check used by all long stages**

```python
def _check_cancel(self, *, stage: LexiconBuildStage, current_item: str = "") -> None:
    if self._cancel_event is None or not self._cancel_event.is_set():
        return
    self._emit_log(
        stage=stage,
        level="warning",
        message="cancellation requested",
        current_item=current_item,
    )
    raise LexiconBuildCancelledError("Lexicon build cancelled.")
```

- [ ] **Step 7: Re-run build tests**

Run:

```bash
rtk test /Users/cmalek/src/workspace/wyrdcraeft/.venv/bin/pytest /Users/cmalek/src/workspace/wyrdcraeft/tests/lexicon/test_build.py -q
```

Expected: PASS for new contract tests. Some later tests may still fail until streaming work lands.

Suggested commit: `Add lexicon build event sink and cancel contract`

### Task 4: Stream `forms` Into TEMP Staging With Live Heartbeats

**Files:**
- Modify: `wyrdcraeft/services/lexicon/build.py`
- Test: `tests/lexicon/test_build.py`

- [ ] **Step 1: Add failing tests for live `LOAD_FORMS` progress and rollback-on-cancel**

```python
def test_rebuild_lexicon_emits_load_forms_progress_with_current_item(lexicon_source_db) -> None:
    events = []
    rebuild_lexicon(lexicon_source_db, event_sink=events.append)
    load_form_events = [
        event
        for event in events
        if getattr(event, "stage", None) == LexiconBuildStage.LOAD_FORMS
    ]
    assert load_form_events
    assert any(getattr(event, "current_item", "") for event in load_form_events)


def test_rebuild_lexicon_cancel_rolls_back_partial_form_work(lexicon_source_db) -> None:
    cancel_event = threading.Event()

    def sink(event) -> None:
        if (
            getattr(event, "stage", None) == LexiconBuildStage.LOAD_FORMS
            and getattr(event, "completed", 0) >= 1
        ):
            cancel_event.set()

    with pytest.raises(LexiconBuildCancelledError):
        rebuild_lexicon(lexicon_source_db, event_sink=sink, cancel_event=cancel_event)

    with sqlite3.connect(lexicon_source_db) as connection:
        assert connection.execute("SELECT COUNT(*) FROM lexicon_forms").fetchone()[0] == 0
```

- [ ] **Step 2: Replace giant `forms` list with TEMP staging table**

```python
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
        class3 TEXT NOT NULL
    )
    """
)
```

- [ ] **Step 3: Stream source rows into stage table in chunks**

```python
chunk: list[tuple[object, ...]] = []
for index, row in enumerate(cursor, start=1):
    self._check_cancel(stage=LexiconBuildStage.LOAD_FORMS, current_item=str(row["BT"]))
    matched_entry_id = self._select_entry_id(...)
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
        )
    )
    if len(chunk) >= self._chunk_size:
        connection.executemany(
            "INSERT INTO temp_lexicon_forms_stage VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            chunk,
        )
        chunk.clear()
```

- [ ] **Step 4: Emit heartbeats on chunk milestones and wall-clock fallback**

```python
self._emit_stage_progress(
    stage=LexiconBuildStage.LOAD_FORMS,
    completed=index,
    total=total_forms,
    detail=f"staged={index}",
    current_item=str(row["BT"]),
)
self._emit_log(
    stage=LexiconBuildStage.LOAD_FORMS,
    level="info",
    message="staging form rows",
    current_item=str(row["BT"]),
    processed=index,
    total=total_forms,
)
```

- [ ] **Step 5: Keep `INSERT_FORMS` as a separate stage copying from TEMP into final table**

```python
connection.execute(
    """
    INSERT INTO lexicon_forms (
        form_id, entry_id, bt, title, stem, form, formi,
        wordclass, function, probability, class1, class2, class3
    )
    SELECT
        form_id, entry_id, bt, title, stem, form, formi,
        wordclass, function, probability, class1, class2, class3
    FROM temp_lexicon_forms_stage
    ORDER BY form_id
    """
)
```

- [ ] **Step 6: Emit counter updates when final insert count is known**

```python
self._emit_counter(
    counter="forms_written",
    value=inserted_forms,
    stage=LexiconBuildStage.INSERT_FORMS,
)
```

- [ ] **Step 7: Re-run build tests**

Run:

```bash
rtk test /Users/cmalek/src/workspace/wyrdcraeft/.venv/bin/pytest /Users/cmalek/src/workspace/wyrdcraeft/tests/lexicon/test_build.py -q
```

Expected: PASS for form-streaming and rollback tests.

Suggested commit: `Stream lexicon form staging with cooperative cancel`

### Task 5: Build Search Keys From Inserted Tables and Let SQLite Dedupe

**Files:**
- Modify: `wyrdcraeft/services/lexicon/build.py`
- Modify: `wyrdcraeft/services/lexicon/schema.py`
- Test: `tests/lexicon/test_build.py`

- [ ] **Step 1: Add failing tests for duplicate-key suppression and live key progress**

```python
def test_rebuild_lexicon_dedupes_duplicate_search_keys_in_sqlite(lexicon_source_db) -> None:
    report = rebuild_lexicon(lexicon_source_db)
    assert report.search_keys_written > 0
    with sqlite3.connect(lexicon_source_db) as connection:
        duplicates = connection.execute(
            """
            SELECT key_text, key_kind, rank_tier, COALESCE(entry_id, -1), COALESCE(form_id, -1), display_text, COUNT(*)
            FROM lexicon_search_keys
            GROUP BY 1, 2, 3, 4, 5, 6
            HAVING COUNT(*) > 1
            """
        ).fetchall()
    assert duplicates == []


def test_rebuild_lexicon_emits_search_key_progress_from_inserted_rows(lexicon_source_db) -> None:
    events = []
    rebuild_lexicon(lexicon_source_db, event_sink=events.append)
    assert any(
        getattr(event, "stage", None) == LexiconBuildStage.BUILD_SEARCH_KEYS
        for event in events
    )
```

- [ ] **Step 2: Add expression unique index to final schema**

```python
CREATE UNIQUE INDEX IF NOT EXISTS uq_lexicon_search_keys_dedupe
    ON lexicon_search_keys(
        key_text,
        key_kind,
        rank_tier,
        COALESCE(entry_id, -1),
        COALESCE(form_id, -1),
        display_text
    );
```

- [ ] **Step 3: Replace Python `seen` set with TEMP key staging table**

```python
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
connection.execute(
    """
    CREATE UNIQUE INDEX temp_uq_lexicon_search_keys_stage
        ON temp_lexicon_search_keys_stage(
            key_text,
            key_kind,
            rank_tier,
            COALESCE(entry_id, -1),
            COALESCE(form_id, -1),
            display_text
        )
    """
)
```

- [ ] **Step 4: Build keys from `lexicon_entries` and `temp_lexicon_forms_stage` / `lexicon_forms`**

```python
entry_cursor = connection.execute(
    """
    SELECT entry_id, headword, variants_json
    FROM lexicon_entries
    ORDER BY entry_id ASC
    """
)
form_cursor = connection.execute(
    """
    SELECT form_id, entry_id, bt, title, stem, form, formi
    FROM lexicon_forms
    ORDER BY form_id ASC
    """
)
```

- [ ] **Step 5: Insert staged key rows with `INSERT OR IGNORE`**

```python
connection.executemany(
    """
    INSERT OR IGNORE INTO temp_lexicon_search_keys_stage (
        key_text, key_kind, rank_tier, entry_id, form_id, display_text
    ) VALUES (?, ?, ?, ?, ?, ?)
    """,
    chunk,
)
```

- [ ] **Step 6: Keep `INSERT_SEARCH_KEYS` as explicit copy into final table**

```python
connection.execute(
    """
    INSERT OR IGNORE INTO lexicon_search_keys (
        key_text, key_kind, rank_tier, entry_id, form_id, display_text
    )
    SELECT key_text, key_kind, rank_tier, entry_id, form_id, display_text
    FROM temp_lexicon_search_keys_stage
    ORDER BY key_text, key_kind, rank_tier, entry_id, form_id, display_text
    """
)
```

- [ ] **Step 7: Emit final `search_keys_written` counter from database count**

```python
search_keys_written = int(
    connection.execute("SELECT COUNT(*) FROM lexicon_search_keys").fetchone()[0]
)
self._emit_counter(
    counter="search_keys_written",
    value=search_keys_written,
    stage=LexiconBuildStage.INSERT_SEARCH_KEYS,
)
```

- [ ] **Step 8: Re-run build tests**

Run:

```bash
rtk test /Users/cmalek/src/workspace/wyrdcraeft/.venv/bin/pytest /Users/cmalek/src/workspace/wyrdcraeft/tests/lexicon/test_build.py -q
```

Expected: PASS for duplicate suppression and key-progress tests.

Suggested commit: `Stream lexicon search keys with SQLite dedupe`

### Task 6: Build the Textual Monitor App

**Files:**
- Create: `wyrdcraeft/services/lexicon/build_monitor.py`
- Test: `tests/lexicon/test_tui.py`

- [ ] **Step 1: Add failing TUI tests with fake event feed**

```python
from wyrdcraeft.models.lexicon_build import (
    BuildCounters,
    BuildFinished,
    BuildLog,
    BuildSnapshot,
    BuildStageProgress,
    BuildStageStarted,
    LexiconBuildStage,
)
from wyrdcraeft.services.lexicon.build_monitor import LexiconBuildMonitorApp


@pytest.mark.anyio
async def test_build_monitor_layout_has_stage_and_log_panes() -> None:
    app = LexiconBuildMonitorApp.fake()
    async with app.run_test():
        assert app.query_one("#build-stage-pane")
        assert app.query_one("#build-log-pane")


@pytest.mark.anyio
async def test_build_monitor_renders_progress_and_final_state() -> None:
    app = LexiconBuildMonitorApp.fake()
    async with app.run_test() as pilot:
        app.handle_event(
            BuildStageStarted(
                seq=1,
                at="2026-06-28T12:00:00Z",
                stage=LexiconBuildStage.LOAD_FORMS,
                total=10,
            )
        )
        app.handle_event(
            BuildStageProgress(
                seq=2,
                at="2026-06-28T12:00:01Z",
                stage=LexiconBuildStage.LOAD_FORMS,
                completed=5,
                total=10,
                current_item="abbad",
            )
        )
        app.handle_event(
            BuildFinished(
                seq=3,
                at="2026-06-28T12:00:02Z",
                snapshot=BuildSnapshot(status="complete", counters=BuildCounters(forms_written=10)),
                built_at="2026-06-28T12:00:02Z",
                forms_source_count=10,
                bt_entries_source_count=1,
            )
        )
        await pilot.pause()
        assert "complete" in str(app.query_one("#build-status").render()).lower()
```

- [ ] **Step 2: Implement app layout and fake constructor**

```python
class LexiconBuildMonitorApp(App[int]):
    CSS = """
    Screen {
        layout: horizontal;
    }

    #build-stage-pane {
        width: 1fr;
        border: solid $accent;
    }

    #build-log-pane {
        width: 2fr;
        border: solid $accent;
    }
    """

    @classmethod
    def fake(cls) -> "LexiconBuildMonitorApp":
        return cls(controller=None, db_path=Path("fake.sqlite3"))
```

- [ ] **Step 3: Add stateful event handler and capped log buffer**

```python
def handle_event(self, event: LexiconBuildEvent) -> None:
    if isinstance(event, BuildStageStarted):
        self._stage_state[event.stage] = {"completed": 0, "total": event.total, "detail": event.detail}
    elif isinstance(event, BuildStageProgress):
        self._stage_state[event.stage] = {
            "completed": event.completed,
            "total": event.total,
            "detail": event.detail or event.current_item,
        }
    elif isinstance(event, BuildLog):
        self._append_log(self._format_log(event))
    elif isinstance(event, (BuildFinished, BuildCancelled, BuildFailed)):
        self._terminal_event = event
```

- [ ] **Step 4: Implement key behavior**

```python
def action_quit_or_cancel(self) -> None:
    if self._terminal_event is None and self.controller is not None:
        self.controller.request_cancel()
        self._status = "cancelling"
        return
    self.exit(self._exit_code)
```

- [ ] **Step 5: Poll runtime queue on timer and auto-render traceback in logs**

```python
def on_mount(self) -> None:
    self.set_interval(0.2, self._poll_events)

def _poll_events(self) -> None:
    if self.controller is None:
        return
    while True:
        event = self.controller.try_get_event()
        if event is None:
            break
        self.handle_event(event)
```

- [ ] **Step 6: Re-run TUI tests**

Run:

```bash
rtk test /Users/cmalek/src/workspace/wyrdcraeft/.venv/bin/pytest /Users/cmalek/src/workspace/wyrdcraeft/tests/lexicon/test_tui.py -q
```

Expected: PASS for new build-monitor tests and existing browse tests.

Suggested commit: `Add lexicon build monitor TUI`

### Task 7: Wire Plain Renderer and CLI Entry Point

**Files:**
- Modify: `wyrdcraeft/cli/lexicon.py`
- Modify: `tests/test_cli_lexicon.py`

- [ ] **Step 1: Add failing CLI tests for new flags and default dispatch**

```python
def test_lexicon_build_help_shows_no_tui_and_quiet(runner) -> None:
    result = runner.invoke(cli, ["lexicon", "build", "--help"])
    assert result.exit_code == 0
    assert "--no-tui" in result.output
    assert "--quiet" in result.output
    assert "--no-progress" not in result.output


def test_lexicon_build_no_tui_smoke(runner, lexicon_source_db) -> None:
    result = runner.invoke(
        cli,
        ["lexicon", "build", "--index-db", str(lexicon_source_db), "--no-tui"],
    )
    assert result.exit_code == 0
    assert "Lexicon build complete." in result.output
```

- [ ] **Step 2: Add `--no-tui` and `--quiet` flags; remove `--no-progress`**

```python
@click.option(
    "--no-tui",
    is_flag=True,
    default=False,
    help="Disable the full-screen Textual monitor and use plain stderr/stdout output.",
)
@click.option(
    "--quiet",
    is_flag=True,
    default=False,
    help="Suppress live output and print only the final summary or failure line.",
)
```

- [ ] **Step 3: Add one plain renderer loop around the shared controller**

```python
def _run_plain_build(controller: LexiconBuildController, *, quiet: bool) -> int:
    try:
        while True:
            event = controller.get_event(timeout=0.2)
            if event is None:
                continue
            if not quiet:
                _render_plain_event(event)
            if controller.is_terminal_event(event):
                return controller.exit_code_for_event(event)
    except KeyboardInterrupt:
        controller.request_cancel()
        return _drain_after_cancel(controller, quiet=quiet)
```

- [ ] **Step 4: Dispatch default TUI only when interactive**

```python
interactive = sys.stdin.isatty() and sys.stdout.isatty() and sys.stderr.isatty()
use_tui = interactive and not no_tui and not quiet
```

- [ ] **Step 5: Keep current final summary shape on `stdout`**

```python
click.echo(
    "\n".join(
        [
            "Lexicon build complete.",
            f"index_db={resolved_index_db}",
            f"built_at={report.built_at}",
            f"forms_source_count={report.forms_source_count}",
            f"bt_entries_source_count={report.bt_entries_source_count}",
            f"entries_written={report.entries_written}",
            f"forms_written={report.forms_written}",
            f"search_keys_written={report.search_keys_written}",
            f"pos_inferred={report.pos_inferred}",
        ]
    )
)
```

- [ ] **Step 6: Map terminal outcomes to exit codes**

```python
if cancelled:
    raise click.exceptions.Exit(130)
if failed:
    raise click.ClickException(short_message)
return
```

- [ ] **Step 7: Re-run CLI tests**

Run:

```bash
rtk test /Users/cmalek/src/workspace/wyrdcraeft/.venv/bin/pytest /Users/cmalek/src/workspace/wyrdcraeft/tests/test_cli_lexicon.py -q
```

Expected: PASS.

Suggested commit: `Wire lexicon build CLI to monitored runtime`

### Task 8: Clean Up Legacy Progress Wiring and Update Docs

**Files:**
- Modify: `wyrdcraeft/services/lexicon/progress.py`
- Modify: `wyrdcraeft/services/lexicon/__init__.py`
- Modify: `doc/source/overview/command_lexicon_build.rst`

- [ ] **Step 1: Strip build-specific Rich coordinator from `progress.py`**

```python
"""Browse startup progress helpers for lexicon TUI startup."""

from enum import StrEnum


class LexiconBrowseStartupStage(StrEnum):
    CONNECT = "connect database"
    VALIDATE = "validate lexicon tables"
    READY = "ready"
```

- [ ] **Step 2: Export new build symbols instead of old Rich progress types**

```python
from .build import (
    BuildReport,
    LexiconBuildCancelledError,
    LexiconBuilder,
    rebuild_lexicon,
)
```

- [ ] **Step 3: Update command docs for default TUI behavior and new flags**

```rst
Live monitor behavior
---------------------

When ``stdout`` and ``stderr`` are attached to an interactive terminal,
``wyrdcraeft lexicon build`` launches a full-screen Textual monitor by default.

- ``q`` or ``Ctrl+C`` requests cooperative cancellation
- ``--no-tui`` forces plain stderr/stdout rendering
- ``--quiet`` suppresses live output and still prints the final summary
```

- [ ] **Step 4: Rebuild focused docs page if local docs workflow is available**

Run:

```bash
rtk python -m compileall /Users/cmalek/src/workspace/wyrdcraeft/wyrdcraeft
```

Expected: PASS. If repo has a preferred docs check later, use it during full verification.

Suggested commit: `Document lexicon build monitor behavior`

### Task 9: Full Verification and Smoke Checks

**Files:**
- Test: `tests/lexicon/test_build.py`
- Test: `tests/lexicon/test_build_runtime.py`
- Test: `tests/lexicon/test_progress.py`
- Test: `tests/lexicon/test_tui.py`
- Test: `tests/test_cli_lexicon.py`

- [ ] **Step 1: Run focused lexicon test suite**

Run:

```bash
rtk test /Users/cmalek/src/workspace/wyrdcraeft/.venv/bin/pytest /Users/cmalek/src/workspace/wyrdcraeft/tests/lexicon/ -q
```

Expected: PASS.

- [ ] **Step 2: Run CLI lexicon tests**

Run:

```bash
rtk test /Users/cmalek/src/workspace/wyrdcraeft/.venv/bin/pytest /Users/cmalek/src/workspace/wyrdcraeft/tests/test_cli_lexicon.py -q
```

Expected: PASS.

- [ ] **Step 3: Run `ruff` on touched Python files**

Run:

```bash
rtk ruff check \
  /Users/cmalek/src/workspace/wyrdcraeft/wyrdcraeft/cli/lexicon.py \
  /Users/cmalek/src/workspace/wyrdcraeft/wyrdcraeft/models/__init__.py \
  /Users/cmalek/src/workspace/wyrdcraeft/wyrdcraeft/models/lexicon_build.py \
  /Users/cmalek/src/workspace/wyrdcraeft/wyrdcraeft/services/lexicon/__init__.py \
  /Users/cmalek/src/workspace/wyrdcraeft/wyrdcraeft/services/lexicon/build.py \
  /Users/cmalek/src/workspace/wyrdcraeft/wyrdcraeft/services/lexicon/build_monitor.py \
  /Users/cmalek/src/workspace/wyrdcraeft/wyrdcraeft/services/lexicon/build_runtime.py \
  /Users/cmalek/src/workspace/wyrdcraeft/wyrdcraeft/services/lexicon/progress.py \
  /Users/cmalek/src/workspace/wyrdcraeft/wyrdcraeft/services/lexicon/schema.py \
  /Users/cmalek/src/workspace/wyrdcraeft/tests/test_cli_lexicon.py \
  /Users/cmalek/src/workspace/wyrdcraeft/tests/lexicon/test_build.py \
  /Users/cmalek/src/workspace/wyrdcraeft/tests/lexicon/test_build_runtime.py \
  /Users/cmalek/src/workspace/wyrdcraeft/tests/lexicon/test_progress.py \
  /Users/cmalek/src/workspace/wyrdcraeft/tests/lexicon/test_tui.py
```

Expected: PASS.

- [ ] **Step 4: Run `mypy` on touched Python files**

Run:

```bash
/Users/cmalek/src/workspace/wyrdcraeft/.venv/bin/mypy --follow-imports=skip \
  /Users/cmalek/src/workspace/wyrdcraeft/wyrdcraeft/cli/lexicon.py \
  /Users/cmalek/src/workspace/wyrdcraeft/wyrdcraeft/models/lexicon_build.py \
  /Users/cmalek/src/workspace/wyrdcraeft/wyrdcraeft/services/lexicon/build.py \
  /Users/cmalek/src/workspace/wyrdcraeft/wyrdcraeft/services/lexicon/build_monitor.py \
  /Users/cmalek/src/workspace/wyrdcraeft/wyrdcraeft/services/lexicon/build_runtime.py \
  /Users/cmalek/src/workspace/wyrdcraeft/wyrdcraeft/services/lexicon/progress.py \
  /Users/cmalek/src/workspace/wyrdcraeft/wyrdcraeft/services/lexicon/schema.py
```

Expected: PASS.

- [ ] **Step 5: Run Napoleon gate**

Run:

```bash
rtk make napoleon-gate
```

Expected: PASS with no new baseline violations.

- [ ] **Step 6: Manual smoke test on real database**

Run:

```bash
rtk wyrdcraeft lexicon build
```

Check:

- TUI opens in interactive terminal
- left pane keeps 9 stable stages
- right pane logs move during `LOAD_FORMS` and `BUILD_SEARCH_KEYS`
- `q` requests cancel, status flips to `cancelling`, build rolls back cleanly
- final success summary still prints same fields on `stdout`

- [ ] **Step 7: Manual non-TUI smoke**

Run:

```bash
rtk wyrdcraeft lexicon build --no-tui
```

Check:

- live milestones go to `stderr`
- final summary goes to `stdout`
- `Ctrl+C` yields exit code `130`

## Notes for Implementer

- Keep browse-shell code in `wyrdcraeft/services/lexicon/tui.py` unchanged unless a tiny shared style helper clearly removes duplication.
- Do not reintroduce `signal.signal(...)` into worker-thread build code.
- Prefer small helper methods in `build.py` over one giant rewrite. The goal is observability plus cancellation, not a fresh architecture.
- Keep TEMP staging table names private to the build implementation.
- Emit structured log fields first; let TUI/plain renderers format user-facing text.
- If a test becomes flaky because of real threads, move more assertions down into `test_build_runtime.py` and keep `test_tui.py` fake-feed only.
- If `mypy` path is missing locally, fix environment first; do not silently skip the gate.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-28-lexicon-build-monitor.md`.

Two execution options:

1. **Subagent-Driven (recommended)** - dispatch a fresh subagent per task, review between tasks, fast iteration
2. **Inline Execution** - execute tasks in this session using executing-plans, batch execution with checkpoints
