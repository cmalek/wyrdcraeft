# Orchestration Guide

How to implement lexicon build monitor work using an **orchestrator agent** and
**phase subagents**. Chat history is not system of record; this file, state,
checkpoint, and log are.

This orchestration covers `wyrdcraeft lexicon build` monitor work only. It does
not re-open lexicon browse feature design.

Related detailed plan:
- `docs/superpowers/plans/2026-06-28-lexicon-build-monitor.md`

---

## 1. Architecture

```text
Orchestrator (this chat)
  | reads this file + state + checkpoint + log
  | picks next phase + model
  | dispatches one phase subagent
  v
Subagent (one phase only)
  | implements only listed files/deliverables
  | runs listed gates
  | appends log events
  v
Build runtime
  main thread: cancel + render
  worker thread: rebuild_lexicon(...)
  queue.SimpleQueue: typed build events
  sqlite TEMP tables: streamed forms/search keys
```

**Orchestrator does not implement product code.** Subagents do one phase and
stop. No subagent starts next phase alone.

---

## 2. Locked decisions

Do not re-litigate these during execution unless human explicitly asks.

- `rebuild_lexicon(...)` stays core build entrypoint.
- Worker runtime uses plain `threading.Thread`.
- Cross-thread event delivery uses `queue.SimpleQueue`.
- Event models live in `wyrdcraeft/models/lexicon_build.py`.
- `LexiconBuildStage` moves into event-model module.
- Build event contract uses closed union dataclasses.
- Logs are structured events, not preformatted strings.
- Counters use dedicated typed counter events.
- Worker stamps `seq` and `at` on events.
- Keep current 9 top-level build stages.
- `entries` path stays mostly in Python memory.
- `forms` and `search_keys` stream through SQLite TEMP staging tables.
- Search keys build from inserted lexicon tables / staging state, not giant
  Python lists.
- Search-key dedupe moves to SQLite with expression unique indexes plus
  `INSERT OR IGNORE`.
- `SCHEMA_VERSION` stays unchanged.
- Main thread owns cancel requests and calls runtime `request_cancel()`.
- Cooperative cancel raises `LexiconBuildCancelledError`.
- Cancel/fail rolls back whole rebuild transaction.
- Default TTY path launches full-screen Textual monitor.
- `--no-tui` forces plain stderr/stdout renderer.
- `--quiet` suppresses live output only; final summary still prints.
- Exit codes: success `0`, cancel `130`, failure `1`.
- Final summary keeps current field names/order.
- TUI holds final screen until `q` or Enter after terminal event.
- `q` during run requests cancel, same as `Ctrl+C`.
- Right log pane keeps capped history and drops oldest lines.
- TUI tests use fake event feed only.
- Worker/runtime tests live outside TUI tests.
- No ADR for this work.
- No `CONTEXT.md` update for this work.

---

## 3. Files

| Path | Owner | Purpose |
|------|-------|---------|
| `docs/superpowers/specs/2026-06-28-lexicon-build-monitor/ORCHESTRATION.md` | human/orchestrator | Locked design + phase briefs |
| `docs/superpowers/plans/2026-06-28-lexicon-build-monitor.md` | human/orchestrator | Detailed task-level implementation plan |
| `docs/superpowers/lexicon-build-monitor/orchestrator.state.json` | orchestrator | Machine-readable phase status |
| `docs/superpowers/lexicon-build-monitor/orchestrator.log` | all agents | Append-only JSONL audit log |
| `docs/superpowers/lexicon-build-monitor/orchestrator.checkpoint.md` | orchestrator | Resume snapshot before/after compaction |

Expected product-code area for subagents:

- `wyrdcraeft/models/`
- `wyrdcraeft/cli/lexicon.py`
- `wyrdcraeft/services/lexicon/`
- `tests/lexicon/`
- `tests/test_cli_lexicon.py`
- `doc/source/overview/command_lexicon_build.rst`

Avoid broad edits outside lexicon build path unless phase brief explicitly
allows it.

---

## 4. Phase order

Strict dependency chain:

```text
01 -> 02 -> 03 -> 04 -> 05 -> 06 -> 07
```

| Phase | Name | Delivers |
|------|------|---------|
| 01 | Event models and runtime skeleton | typed build events, controller shell, base tests |
| 02 | Builder event/cancel contract | expanded `rebuild_lexicon(...)`, runtime hook, cancel semantics |
| 03 | Stream forms | TEMP form staging, live form heartbeats, rollback tests |
| 04 | Stream search keys | SQLite dedupe, TEMP key staging, counter events |
| 05 | Build monitor TUI | full-screen app, fake-feed tests, final-state UX |
| 06 | CLI and plain renderer | default TUI launch, `--no-tui`, `--quiet`, exit-code mapping |
| 07 | Docs and verification | cleanup, docs, focused tests, required gates, smoke checks |

Do not skip phases. Do not parallelize dependent phases.

---

## 5. Orchestrator workflow

Each turn, orchestrator:

1. Read this file.
2. Read `docs/superpowers/lexicon-build-monitor/orchestrator.state.json`.
3. Tail `docs/superpowers/lexicon-build-monitor/orchestrator.log`.
4. If context ring is above `context_compact_threshold`, compact per §7.
5. Find lowest-numbered phase whose status is not `complete` or `skipped`.
6. Choose subagent model per §8.
7. Append `dispatch` event to log.
8. Set phase status to `in_progress` in state.
9. Dispatch subagent with:
   - this file path
   - detailed plan path
   - assigned phase number
   - instruction: implement only that phase, do not start next one
10. On successful completion with required gates passing:
   - mark phase `complete`
   - record `model_used`
   - update checkpoint
   - dispatch next phase
11. On failure/block:
   - record failure in state/log
   - apply §10 failure handling
   - do not dispatch downstream phases

---

## 6. Subagent workflow

1. Read this file end-to-end.
2. Read detailed plan file only for assigned phase scope.
3. Append `started` event to log.
4. Implement only listed deliverables.
5. Run required gates for touched files:
   - `ruff check` on touched Python files or targeted package
   - `.venv/bin/mypy --follow-imports=skip` on touched Python files or targeted package
   - `make napoleon-gate`
   - targeted `pytest` listed in phase brief
6. Append `complete` or `failed` with `artifacts[]` and `gates{}`.
7. Stop.

### Context rules for subagents

- Load only files relevant to assigned phase.
- Prefer additive lexicon build files over touching browse shell files.
- Do not move on to next phase.
- Do not invent new config knobs unless phase brief requires one.
- Do not change existing dictionary/morphology product code for this project.

---

## 7. Context compaction

Compact proactively at ~60%, not at 100%.

### Compact protocol

1. Update `docs/superpowers/lexicon-build-monitor/orchestrator.checkpoint.md`
2. Append log event `checkpoint`
3. Update `orchestrator.state.json`
4. Run `/summarize`
5. Re-read only:
   - this file
   - `orchestrator.state.json`
   - `orchestrator.checkpoint.md`
   - last 20 log lines
6. Append log event `compact`
7. Resume

### Checkpoint template

```markdown
# Orchestrator Checkpoint
Updated: <ISO8601>

## Resume here
- Next phase: NN
- Next action: dispatch | retry_phase_NN | wait_human
- Model policy: cost_aware

## Phase status
| Phase | Status | Model used | Notes |
|------|--------|------------|-------|

## Active blockers

## Last 3 log events

## Locked decisions
- worker thread + queue.SimpleQueue runtime
- forms/search keys stream through TEMP tables
- cancel => rollback => exit 130
- default interactive path uses Textual monitor
```

---

## 8. Model selection

Pick cheapest model likely to pass gates.

| Tier | Models | Use for |
|------|--------|---------|
| fast | `composer-2.5-fast`, `gemini-3-flash` | docs, state/log upkeep, tiny wiring |
| standard | `gpt-5.3-codex`, `gpt-5.4-medium` | Python build/runtime/CLI/Textual work |
| reasoning | `claude-4.6-sonnet-medium-thinking` | blocked retries only |

### Default first-dispatch model

| Phase | Model | Tier |
|------|-------|------|
| 01 | `gpt-5.3-codex` | standard |
| 02 | `gpt-5.3-codex` | standard |
| 03 | `gpt-5.3-codex` | standard |
| 04 | `gpt-5.4-medium` | standard |
| 05 | `gpt-5.3-codex` | standard |
| 06 | `composer-2.5-fast` | fast |
| 07 | `composer-2.5-fast` | fast |

### Retry policy

- lint/type/doc gate failure: retry same tier once
- logic/test failure: retry one tier higher once
- second logic failure on same phase: block and surface to human

---

## 9. Log protocol

Append one JSON object per line to
`docs/superpowers/lexicon-build-monitor/orchestrator.log`.

Required shape:

```json
{
  "ts": "2026-06-28T23:20:00Z",
  "actor": "orchestrator",
  "event": "dispatch",
  "phase": "03",
  "status": "in_progress",
  "model": "gpt-5.3-codex",
  "model_tier": "standard",
  "retry": 0,
  "message": "Dispatch stream-forms phase",
  "artifacts": [],
  "gates": {},
  "blockers": []
}
```

Useful event kinds:

- `decision`
- `checkpoint`
- `compact`
- `dispatch`
- `started`
- `complete`
- `failed`
- `blocked_waiting_human`

---

## 10. Failure handling

Stop and surface to human when any of these happen:

- worker-thread cancel path cannot cleanly distinguish cancel from failure
- SQLite TEMP staging cannot preserve required semantics without broad refactor
- Textual harness needs unsupported threading/test changes
- a phase fails twice on logic/tests
- implementation seems to require new product config/settings knobs

When blocked:

1. append `blocked_waiting_human`
2. record exact blocker in state/checkpoint
3. do not dispatch downstream phases

---

## 11. Phase briefs

### Phase 01: Event models and runtime skeleton

**Goal:** define typed build events and shared controller skeleton.

**Preferred files:**

- Create: `wyrdcraeft/models/lexicon_build.py`
- Modify: `wyrdcraeft/models/__init__.py`
- Create: `wyrdcraeft/services/lexicon/build_runtime.py`
- Create: `tests/lexicon/test_build_runtime.py`
- Modify: `tests/lexicon/test_progress.py`

**Notes:**

- Move `LexiconBuildStage` into models.
- Keep runtime minimal: queue, cancel event, interrupt callback, terminal-event guarantee.
- Do not wire product build code yet beyond imports/types.

**Targeted tests:**

- `pytest -q tests/lexicon/test_progress.py`
- `pytest -q tests/lexicon/test_build_runtime.py`

---

### Phase 02: Builder event/cancel contract

**Goal:** expand `rebuild_lexicon(...)` to emit typed events and honor cooperative cancel.

**Preferred files:**

- Modify: `wyrdcraeft/services/lexicon/build.py`
- Modify: `wyrdcraeft/services/lexicon/__init__.py`
- Modify: `tests/lexicon/test_build.py`

**Notes:**

- Add `LexiconBuildCancelledError`.
- Remove main-thread-only signal ownership from build core.
- Runtime owns SQLite interrupt callback registration.
- Builder emits stage, log, and counter events.

**Targeted tests:**

- `pytest -q tests/lexicon/test_build.py -k "event or cancel"`

---

### Phase 03: Stream forms

**Goal:** replace giant in-memory form payload list with TEMP staging and live heartbeats.

**Preferred files:**

- Modify: `wyrdcraeft/services/lexicon/build.py`
- Modify: `tests/lexicon/test_build.py`

**Notes:**

- Keep existing Python `_select_entry_id(...)` logic.
- Stream source cursor rows into TEMP table in chunks.
- `INSERT_FORMS` remains separate stage copying into final table.
- Cancel during this phase must roll back fully.

**Targeted tests:**

- `pytest -q tests/lexicon/test_build.py -k "load_forms or rollback"`

---

### Phase 04: Stream search keys

**Goal:** build search keys from inserted/staged tables and dedupe in SQLite.

**Preferred files:**

- Modify: `wyrdcraeft/services/lexicon/build.py`
- Modify: `wyrdcraeft/services/lexicon/schema.py`
- Modify: `tests/lexicon/test_build.py`

**Notes:**

- No giant Python `seen` set.
- Use expression unique index plus `INSERT OR IGNORE`.
- Emit `search_keys_written` counter from DB truth.

**Targeted tests:**

- `pytest -q tests/lexicon/test_build.py -k "search_keys or dedupe"`

---

### Phase 05: Build monitor TUI

**Goal:** add full-screen Textual monitor fed by typed events.

**Preferred files:**

- Create: `wyrdcraeft/services/lexicon/build_monitor.py`
- Modify: `tests/lexicon/test_tui.py`

**Notes:**

- Left pane: 9 stages, status, counters.
- Right pane: capped log history, auto-visible traceback on failure.
- Use fake event feed in tests.
- `q` while running requests cancel; `q` or Enter after terminal event exits.

**Targeted tests:**

- `pytest -q tests/lexicon/test_tui.py -k build_monitor`

---

### Phase 06: CLI and plain renderer

**Goal:** wire default TUI path, plain fallback, `--quiet`, and exit-code mapping.

**Preferred files:**

- Modify: `wyrdcraeft/cli/lexicon.py`
- Modify: `tests/test_cli_lexicon.py`

**Notes:**

- Default interactive terminal launches TUI.
- `--no-tui` uses shared runtime plus plain stderr/stdout renderer.
- `--quiet` suppresses live output only.
- Keep final summary shape unchanged.

**Targeted tests:**

- `pytest -q tests/test_cli_lexicon.py -k build`

---

### Phase 07: Docs and verification

**Goal:** finish docs, cleanup, and required gates.

**Preferred files:**

- Modify: `wyrdcraeft/services/lexicon/progress.py`
- Modify: `wyrdcraeft/services/lexicon/__init__.py`
- Modify: `doc/source/overview/command_lexicon_build.rst`
- Modify: tests touched as needed

**Notes:**

- `progress.py` should end as browse-startup helper, not build-progress home.
- Keep browse shell stable.
- Run focused lexicon tests first, then required repo gates.

**Targeted tests:**

- `pytest -q tests/lexicon`
- `pytest -q tests/test_cli_lexicon.py`

---

## 12. Definition of done

This orchestration is complete when phases 01 through 07 produce:

- default interactive `wyrdcraeft lexicon build` Textual monitor
- live stage progress and structured logs
- responsive cooperative cancel with rollback
- `--no-tui` plain renderer
- `--quiet` final-summary-only live-output suppression
- passing focused lexicon tests and required Python gates
