# Orchestration Guide

How to build the `wyrdcraeft lexicon` browse workflow using an **orchestrator
agent** and **phase subagents**. Chat history is not the system of record; this
file and the repo are.

This plan covers the new browse-only lexicon workflow, not the older
Bosworth-Toller indexing project.

---

## 1. Architecture

```
Orchestrator (this chat)
  │  reads this file + state + log + checkpoint
  │  picks next phase + model
  │  dispatches one phase subagent
  ▼
Subagent (one phase only)
  │  implements only listed files/deliverables
  │  runs listed gates
  │  appends log events
  ▼
Canonical working DB
  morphology.sqlite3
    ├─ forms         ← live morphology rows
    ├─ bt_*          ← curated Bosworth-Toller tables
    └─ lexicon_*     ← derived browse/read-model tables
```

**Orchestrator does not implement product code.** Subagents do one phase and
stop. No subagent starts the next phase on its own.

---

## 2. Locked decisions

Do not re-litigate these during execution unless the human explicitly asks.

- User-facing commands are `wyrdcraeft lexicon build` and
  `wyrdcraeft lexicon browse`.
- `morphology.sqlite3` is the canonical working lexicon database.
- `bt_*` tables live in that same database and are curated in-database.
- `lexicon build` rebuilds only `lexicon_*` tables from existing `forms` and
  existing `bt_*`. It does **not** regenerate Bosworth-Toller data.
- Bootstrap of `bt_*` into `morphology.sqlite3` remains a prerequisite handled
  by existing dictionary attach/index flows, not by `lexicon build`.
- TUI v1 is **browse only**. No editing UI. No provenance editing UI.
- Search is unified first: one search box, Enter to search, optional mode
  filter can arrive later if cheap.
- Main results show only real dictionary entries. Morphology-only matches show
  in a separate orphan section.
- If there is exactly one main result, the app opens/focuses that result's
  details.
- Details show first non-empty sense as summary, then full senses list.
- First-cut morphology display is grouped raw rows, not custom paradigm tables.
- Do not change existing dictionary or morphology product code without explicit
  human approval. New lexicon code, tests, docs, and CLI wiring are fine.

---

## 3. Files

| Path | Owner | Purpose |
|------|-------|---------|
| `docs/superpowers/specs/2026-06-28-lexicon-browse/ORCHESTRATION.md` | human | Locked design + subagent phase briefs |
| `docs/superpowers/lexicon/orchestrator.state.json` | orchestrator | Machine-readable phase status |
| `docs/superpowers/lexicon/orchestrator.log` | all agents | Append-only JSONL audit trail |
| `docs/superpowers/lexicon/orchestrator.checkpoint.md` | orchestrator | Resume snapshot before compaction |

Expected product-code area for subagents:

- `wyrdcraeft/cli/lexicon.py`
- `wyrdcraeft/services/lexicon/`
- `tests/lexicon/`
- `tests/test_cli_lexicon.py`
- small wiring changes in `wyrdcraeft/cli/cli.py`

Prefer additive lexicon files over edits to existing dictionary/morphology
modules.

---

## 4. Phase order

Strict dependency chain:

```
01 → 02 → 03 → 04 → 05 → 06 → 07
                     \
                      └→ 08 (optional, human approval required)
```

| Phase | Name | Delivers |
|------|------|---------|
| 01 | Lexicon schema | `lexicon_*` table contract + schema helpers + fixtures |
| 02 | Lexicon builder | Rebuild service from `forms` + `bt_*` into `lexicon_*` |
| 03 | Lexicon query service | Unified search, ranking, orphan handling, details payload |
| 04 | Lexicon CLI build | `wyrdcraeft lexicon build` + command registration |
| 05 | Textual shell | Browse app scaffold + `wyrdcraeft lexicon browse` shell |
| 06 | Results and details UX | Search flow, single-hit focus, detail/sidebar rendering |
| 07 | Polish and docs | Integration tests, docs, staleness/build metadata polish |
| 08 | Core-service changes | Optional edits to existing dictionary/morphology code only if human approves |

Do not skip phases. Do not parallelize dependent phases.

---

## 5. Orchestrator workflow

Each turn, the orchestrator:

1. Read this file.
2. Read `docs/superpowers/lexicon/orchestrator.state.json` if it exists.
3. Tail `docs/superpowers/lexicon/orchestrator.log` (last ~20 events enough).
4. If context ring is above `context_compact_threshold`, compact per §7.
5. Find the lowest-numbered phase whose status is not `complete` or `skipped`.
6. Check whether that phase is approval-gated.
7. Choose a subagent model per §8.
8. Append `dispatch` event to the log.
9. Set phase status to `in_progress` in state.
10. Dispatch subagent with:
    - this file path
    - assigned phase number
    - instruction: implement only that phase, do not start next phase
11. On `complete` with all required gates passing:
    - mark phase `complete`
    - record `model_used`
    - dispatch next phase
12. On `failed` or `blocked`:
    - record failure in state/log
    - apply §10 failure handling
    - do not dispatch downstream phases

---

## 6. Subagent workflow

1. Read this file end-to-end.
2. Read only the assigned phase brief in §11 closely enough to execute it.
3. Append `started` event to the log with chosen model.
4. Implement only the listed deliverables.
5. Run required quality gates for touched files:
   - `ruff check` on touched Python files or targeted package
   - `.venv/bin/mypy` on touched Python files or targeted package
   - `make napoleon-gate`
   - targeted `pytest` listed in the phase brief
6. Append `complete` or `failed` with `artifacts[]` and `gates{}`.
7. Stop.

### Context rules for subagents

- Load only files relevant to the assigned phase.
- Prefer existing query/index helpers before reading large source corpora.
- Never load `data/oe_bt.txt` into prompt context.
- Never change existing dictionary/morphology product code unless the phase is
  08 and the human has explicitly approved it.
- If a lower phase can be solved by additive lexicon code, do that instead of
  touching legacy services.

---

## 7. Context compaction

Compact proactively at ~60%, not at 100%.

### Compact protocol

1. Write `docs/superpowers/lexicon/orchestrator.checkpoint.md`
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
- morphology.sqlite3 is canonical working lexicon DB
- bt_* curated in DB; lexicon build never rewrites bt_*
- TUI v1 is browse only
- no dictionary/morphology product-code edits without human approval
```

---

## 8. Model selection

Pick the cheapest model likely to pass the gates.

| Tier | Models | Use for |
|------|--------|---------|
| fast | `composer-2.5-fast`, `gemini-3-flash` | docs, simple schema/tests, tiny wiring |
| standard | `gpt-5.3-codex`, `gpt-5.4-medium` | SQLite, query services, CLI, Textual code |
| reasoning | `claude-4.6-sonnet-medium-thinking` | tricky ranking, view-model shaping, blocked retries |
| heavy | `gpt-5.5-medium`, `claude-opus-4-8-thinking-high` | last-resort retries only |

### Default first-dispatch model

| Phase | Model | Tier |
|------|-------|------|
| 01 | `composer-2.5-fast` | fast |
| 02 | `gpt-5.3-codex` | standard |
| 03 | `gpt-5.4-medium` | standard |
| 04 | `composer-2.5-fast` | fast |
| 05 | `gpt-5.3-codex` | standard |
| 06 | `gpt-5.4-medium` | standard |
| 07 | `composer-2.5-fast` | fast |
| 08 | `claude-4.6-sonnet-medium-thinking` | reasoning |

### Retry policy

- lint/type/doc gate failure: retry same tier
- logic/test failure: retry one tier higher
- second logic failure on same phase: one more retry only, then block
- phase 08 cannot start without human approval even if earlier phase blocks

---

## 9. Log protocol

Append one JSON object per line to
`docs/superpowers/lexicon/orchestrator.log`.

Required shape:

```json
{
  "ts": "2026-06-28T12:00:00Z",
  "actor": "orchestrator",
  "event": "dispatch",
  "phase": "03",
  "status": "in_progress",
  "model": "gpt-5.4-medium",
  "model_tier": "standard",
  "retry": 0,
  "message": "Dispatch lexicon query service phase",
  "artifacts": [],
  "gates": {},
  "blockers": []
}
```

Useful event kinds:

- `dispatch`
- `started`
- `complete`
- `failed`
- `checkpoint`
- `compact`
- `decision`
- `blocked_waiting_human`

---

## 10. Failure handling

Stop and surface to the human when any of these happen:

- a subagent believes existing dictionary or morphology product code must change
- acceptance criteria cannot be met from additive lexicon code alone
- Textual testing turns out to require unsupported harness changes
- a phase fails twice on logic/tests
- data in `forms` or `bt_*` is insufficient to render a required field cleanly

When blocked:

1. append `blocked_waiting_human`
2. record exact blocker in state/checkpoint
3. do not dispatch downstream phases

---

## 11. Phase briefs

### Phase 01: Lexicon schema

**Goal:** define minimal `lexicon_*` tables and reusable test fixtures without
touching current dictionary/morphology code.

**Preferred files:**

- Create: `wyrdcraeft/services/lexicon/__init__.py`
- Create: `wyrdcraeft/services/lexicon/schema.py`
- Create: `tests/lexicon/conftest.py`
- Create: `tests/lexicon/test_schema.py`

**Notes:**

- Reuse existing morphology/dictionary test helpers where practical.
- Keep schema lean. Favor a few useful tables over many normalized tables.
- Expected minimal tables:
  - `lexicon_entries`
  - `lexicon_search_keys`
  - `lexicon_forms`
  - `lexicon_build_meta`

**Locked semantics:**

- `lexicon_entries` is one row per real dictionary entry.
- `lexicon_forms` may include rows with no matching entry; those are orphans.
- `lexicon_search_keys` powers bare/normalized/full-form search and ranking.

**Targeted tests:**

- `pytest -q tests/lexicon/test_schema.py`

---

### Phase 02: Lexicon builder

**Goal:** rebuild `lexicon_*` tables from current `forms` and current `bt_*`
inside `morphology.sqlite3`.

**Preferred files:**

- Create: `wyrdcraeft/services/lexicon/build.py`
- Modify: `wyrdcraeft/services/lexicon/schema.py`
- Create: `tests/lexicon/test_build.py`

**Notes:**

- Builder must run in a transaction and replace only `lexicon_*` contents.
- Builder must not modify `forms` or `bt_*`.
- Builder should derive:
  - summary sense = first non-empty gloss
  - variants from dictionary entry data
  - search keys for lemma, variant, morphology lemma/stem/form
  - orphan form rows when a morphology row does not join to a dictionary entry

**Targeted tests:**

- `pytest -q tests/lexicon/test_build.py`

---

### Phase 03: Lexicon query service

**Goal:** expose unified search and details payloads for the TUI.

**Preferred files:**

- Create: `wyrdcraeft/services/lexicon/query.py`
- Create: `tests/lexicon/test_query_service.py`

**Notes:**

- Search ranking is locked:
  1. exact dictionary lemma/variant hits
  2. morphology lemma/stem hits that join to dictionary
  3. morphology form hits that join to dictionary
  4. orphan morphology hits in separate section
- Main results return one row per dictionary entry, not one row per spelling.
- Details payload should include:
  - lemma/headword
  - variants
  - part of speech
  - class summary from existing morphology row metadata
  - gender/person/number when derivable from existing data
  - summary sense + ordered full senses
  - etymology
  - grouped morphology rows for sidebar rendering

**Targeted tests:**

- `pytest -q tests/lexicon/test_query_service.py`

---

### Phase 04: Lexicon CLI build

**Goal:** add `wyrdcraeft lexicon build` using default morphology DB path.

**Preferred files:**

- Create: `wyrdcraeft/cli/lexicon.py`
- Modify: `wyrdcraeft/cli/cli.py`
- Create: `tests/test_cli_lexicon.py`

**Notes:**

- `lexicon build` should default to the normal morphology app-data DB path.
- It should fail clearly if required `bt_*` tables are missing.
- Reuse existing path resolution instead of inventing a new lexicon DB path.

**Targeted tests:**

- `pytest -q tests/test_cli_lexicon.py -k build`

---

### Phase 05: Textual shell

**Goal:** create browse app scaffold and wire `wyrdcraeft lexicon browse`.

**Preferred files:**

- Create: `wyrdcraeft/services/lexicon/tui.py`
- Modify: `wyrdcraeft/cli/lexicon.py`
- Create: `tests/lexicon/test_tui.py`

**Notes:**

- Use a simple two-pane layout:
  - top search input
  - left results pane
  - right details pane
- Browse command should default to the normal morphology DB path.
- TUI should load through the lexicon query service, not direct widget SQL.

**Targeted tests:**

- `pytest -q tests/lexicon/test_tui.py -k shell`

---

### Phase 06: Results and details UX

**Goal:** implement actual browse behavior that satisfies acceptance criteria.

**Preferred files:**

- Modify: `wyrdcraeft/services/lexicon/query.py`
- Modify: `wyrdcraeft/services/lexicon/tui.py`
- Modify: `tests/lexicon/test_tui.py`
- Modify: `tests/lexicon/test_query_service.py`

**Notes:**

- Search on Enter only.
- Unified search first; optional mode filter can be skipped unless cheap.
- If one main result exists, focus/show that details payload immediately.
- Main result rows should show headword and POS to disambiguate homographs.
- Orphans stay visible in a separate lower section.
- First-cut morphology sidebar groups rows by `wordclass` and `function`.

**Targeted tests:**

- `pytest -q tests/lexicon/test_query_service.py`
- `pytest -q tests/lexicon/test_tui.py -k browse`

---

### Phase 07: Polish and docs

**Goal:** finish integration tests, docs, and build metadata behavior.

**Preferred files:**

- Modify: `wyrdcraeft/services/lexicon/build.py`
- Modify: `wyrdcraeft/services/lexicon/tui.py`
- Modify: `tests/lexicon/test_build.py`
- Modify: `tests/lexicon/test_tui.py`
- Create or modify docs under `doc/source/overview/` if needed

**Notes:**

- Add build metadata/staleness info only if it stays small and local.
- Document bootstrap expectation: `bt_*` must already exist in morphology DB.
- Keep browse-only scope. Do not add edit flows.

**Targeted tests:**

- `pytest -q tests/lexicon`
- `pytest -q tests/test_cli_lexicon.py`

---

### Phase 08: Core-service changes (optional, approval-gated)

**Goal:** only if blocked, make minimal approved changes to existing
dictionary/morphology code that unlock required browse behavior.

**Allowed only after human approval.**

**Possible files:**

- `wyrdcraeft/services/morphology/generation/query.py`
- `wyrdcraeft/services/dictionary/query.py`
- `wyrdcraeft/models/morphology.py`
- `wyrdcraeft/models/dictionary.py`

**Notes:**

- Prefer read-only helper additions over schema churn.
- If a helper in additive lexicon code can solve the problem, do that instead.
- Any approved phase-08 change must include targeted regression tests and the
  full Python gates required by repo policy.

---

## 12. Definition of done

This plan is complete when phases 01 through 07 have been executed and produce:

- `wyrdcraeft lexicon build`
- `wyrdcraeft lexicon browse`
- `lexicon_*` tables rebuilt inside `morphology.sqlite3`
- unified lemma/stem/form browse with orphan section
- details pane covering agreed metadata and grouped morphology rows
- targeted tests and required Python gates passing

Phase 08 is not part of definition-of-done unless the human explicitly approves
core-service changes.
