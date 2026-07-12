# Orchestration Guide

How to build the Bosworth-Toller dictionary index using an **orchestrator agent** and **phase subagents**. Chat history is not the system of record — the filesystem is.

**Product spec:** [00-overview.md](./00-overview.md)

---

## 1. Architecture

```
Orchestrator (this chat)
  │  reads state + log + checkpoint
  │  picks phase + model
  │  dispatches Task subagent
  ▼
Subagent (one phase only)
  │  reads phase-NN spec
  │  implements + runs gates
  │  appends log events
  ▼
Filesystem
  orchestrator.state.json   ← current phase status
  orchestrator.log          ← append-only JSONL audit trail
  orchestrator.checkpoint.md ← pre-compact resume snapshot
  phase specs               ← subagent briefs
```

**Orchestrator never implements product code.** Subagents never start the next phase on their own.

---

## 2. Files

| Path | Owner | Purpose |
|------|-------|---------|
| `docs/superpowers/specs/2026-06-21-bosworth-toller-dictionary-index/00-overview.md` | human | Locked product decisions |
| `docs/superpowers/specs/2026-06-21-bosworth-toller-dictionary-index/phase-NN-*.md` | human | Self-contained subagent brief per phase |
| `docs/superpowers/bt-dictionary/orchestrator.state.json` | orchestrator | Machine-readable phase status + policy |
| `docs/superpowers/bt-dictionary/orchestrator.log` | all agents | Append-only JSONL event log |
| `docs/superpowers/bt-dictionary/orchestrator.checkpoint.md` | orchestrator | Human-readable resume snapshot before `/summarize` |

---

## 3. Phase order

Strict dependency chain:

```
01 → 02 → 03 → 04 → 05 → 06 ─┐
                  └→ 07 → 08 ─┘
                  └→ 09 (optional, after 05)
```

| Phase | Spec | Delivers |
|-------|------|----------|
| 01 | `phase-01-models-and-pos.md` | Models, POS/gender extractor |
| 02 | `phase-02-line-parser.md` | Raw line parser |
| 03 | `phase-03-sense-segmentation.md` | Sense split + attestation stripper |
| 04 | `phase-04-editorial-merger.md` | Add/Substitute/Dele → consolidated entries |
| 05 | `phase-05-sqlite-and-index-cli.md` | `dictionary.sqlite3` + `dictionary index-bt` |
| 06 | `phase-06-attach-morphology-db.md` | Optional single-file attach mode |
| 07 | `phase-07-dictionary-lookup.md` | `dictionary lookup` |
| 08 | `phase-08-morphology-join.md` | `morphology query --with-dictionary` |
| 09 | `phase-09-llm-fix-pass-optional.md` | Optional local LLM on parse warnings |

Do not skip phases. Do not parallelize phases with dependencies.

---

## 4. Orchestrator workflow

Each turn, the orchestrator:

1. Read `orchestrator.state.json`.
2. Tail `orchestrator.log` (last ~20 events enough).
3. If context ring ≥ **60%**, run [§6 Context compaction](#6-context-compaction) before dispatching.
4. Find the lowest-numbered phase with `status` not in `{complete, skipped}`.
5. Choose subagent model per [§7 Model selection](#7-model-selection).
6. Append a `dispatch` event to the log.
7. Set phase `status: in_progress` in state.json.
8. Spawn Task subagent with:
   - phase spec path
   - log path
   - chosen `model` slug
   - instruction: read `00-overview.md` locked decisions; do not implement other phases
9. On subagent `complete` with all gates `pass`:
   - set phase `status: complete`, record `model_used`
   - dispatch next phase
10. On `failed` or `blocked`:
    - set phase `status: failed` or leave `in_progress`
    - append `decision` event
    - apply [§9 Failure handling](#9-failure-handling); do not dispatch downstream phases

---

## 5. Subagent workflow

1. Read assigned `phase-NN-*.md` end-to-end.
2. Skim `00-overview.md` — do not contradict locked decisions.
3. Append `started` to log (include `model`).
4. Implement deliverables listed in phase spec only.
5. Run quality gates listed in phase spec:
   - `ruff check` on touched files
   - `.venv/bin/mypy` on touched files
   - `make napoleon-gate`
   - phase `pytest` paths
6. Append `complete` or `failed` with `artifacts[]` and `gates{}`.
7. Stop. Do not start the next phase.

### Context rules for subagents

- Load one phase spec + files you create or modify + that phase's test fixtures.
- Never load `data/oe_bt.txt` into the prompt (read from disk in code/tests).
- Never load orchestrator checkpoint or full log history.

---

## 6. Context compaction

Long orchestrator sessions degrade before the window fills. Compact **proactively at ~60%**, not at 100%.

### Human operator (Cursor)

| Action | How |
|--------|-----|
| Check usage | Click the **context ring** on the chat input |
| Compact manually | Run **`/summarize`** in Agent chat |
| Auto compact | Cursor also summarizes near 100% — avoid relying on this |

`/summarize` is lossy. **Always write a checkpoint before summarizing.**

### Orchestrator compact protocol

Trigger when context ring ≥ `context_compact_threshold` (default **0.60**), or before dispatching reasoning-tier phases 03–04 if already >50%.

**Never compact while a subagent is running.** Wait for `complete` or `failed`.

```
1. Write orchestrator.checkpoint.md  (template §6.1)
2. Append log: event=checkpoint
3. Update orchestrator.state.json
4. Run /summarize  (or ask human to run it)
5. Re-read ONLY:
     - orchestrator.state.json
     - orchestrator.checkpoint.md
     - last 20 lines of orchestrator.log
6. Append log: event=compact
7. Resume dispatch from checkpoint — do not re-read old phase specs or subagent output
```

### 6.1 Checkpoint template

Path: `docs/superpowers/bt-dictionary/orchestrator.checkpoint.md`

```markdown
# Orchestrator Checkpoint
Updated: <ISO8601>

## Resume here
- Next phase: NN
- Next action: dispatch | retry_phase_NN | wait_human
- Model policy: cost_aware

## Phase status
| Phase | Status | Model used | Notes |
...

## Active blockers

## Last 3 log events

## Locked decisions (do not re-litigate)
- dictionary.sqlite3 alongside morphology.sqlite3 in app-data
- Editorial lines merged into consolidated entries
- Homograph key: (norm_key, pos)
- Query: dictionary lookup + morphology query --with-dictionary
```

---

## 7. Model selection

Orchestrator picks the **cheapest model that can pass the phase gates**. Pass model via Task tool `model` parameter. Log every choice.

### 7.1 Tiers

| Tier | Models | Cost | Use for |
|------|--------|------|---------|
| **fast** | `composer-2.5-fast`, `gemini-3-flash` | lowest | schemas, glue, docs, small diffs |
| **standard** | `gpt-5.3-codex`, `gpt-5.4-medium` | medium | parsers, CLI, SQLite, query services |
| **reasoning** | `claude-4.6-sonnet-medium-thinking` | higher | heuristics, editorial merge, golden tuning |
| **heavy** | `gpt-5.5-medium`, `claude-opus-4-8-thinking-high` | highest | retry only |

Phase 09's **local Ollama model** (`qwen2.5:14b-instruct`) is runtime config for `index-bt --llm-fix-pass`, not a coding subagent model.

### 7.2 Default model per phase (first dispatch)

| Phase | Model | Tier |
|-------|-------|------|
| 01 | `composer-2.5-fast` | fast |
| 02 | `gpt-5.3-codex` | standard |
| 03 | `claude-4.6-sonnet-medium-thinking` | reasoning |
| 04 | `claude-4.6-sonnet-medium-thinking` | reasoning |
| 05 | `gpt-5.3-codex` | standard |
| 06 | `composer-2.5-fast` | fast |
| 07 | `gpt-5.4-medium` | standard |
| 08 | `gpt-5.4-medium` | standard |
| 09 | `gpt-5.3-codex` | standard |

### 7.3 Retry upgrades

| Failure type | Action |
|--------------|--------|
| ruff / mypy / napoleon | Re-dispatch **same model** |
| pytest / golden regression | Re-dispatch **+1 tier** |
| Second logic failure | Third dispatch → **heavy** (03–04) or `blocked` + human |

Tier upgrade path: fast → standard → reasoning → heavy.

### 7.4 Cost guardrails

- Never use **heavy** on first dispatch for phases 01, 02, 05, 06, 07, 08, 09.
- Cap **heavy** at **2 dispatches** project-wide unless human sets `model_policy: quality_first`.
- Phases 03–04 may start on **reasoning**; all others start **fast** or **standard** only.

### 7.5 `model_policy` (in state.json)

| Value | Behavior |
|-------|----------|
| `cost_aware` | Default table above; upgrade only on retry |
| `minimum_cost` | Downgrade one tier where safe; 03–04 floor = standard |
| `quality_first` | 03–04 first dispatch on heavy; others unchanged |

---

## 8. Log protocol (JSONL)

Append one JSON object per line to `docs/superpowers/bt-dictionary/orchestrator.log`.

### Required fields

```json
{
  "ts": "2026-06-21T12:00:00Z",
  "actor": "orchestrator",
  "event": "dispatch",
  "phase": "03",
  "status": "in_progress",
  "model": "claude-4.6-sonnet-medium-thinking",
  "model_tier": "reasoning",
  "model_reason": "first dispatch per phase table",
  "retry": 0,
  "message": "human-readable summary",
  "artifacts": ["wyrdcraeft/services/dictionary/sense_segmenter.py"],
  "gates": {"ruff": "pass", "mypy": "pass", "napoleon": "pass", "pytest": "pass"},
  "blockers": []
}
```

### Events

| event | actor | when |
|-------|-------|------|
| `dispatch` | orchestrator | Subagent spawned; include `model`, `model_tier`, `model_reason`, `retry` |
| `started` | subagent | Work begun |
| `complete` | subagent | Gates pass; list `artifacts` |
| `failed` | subagent | Stopped; include error summary |
| `blocked` | subagent | Needs human/orchestrator decision |
| `decision` | orchestrator | Retry, skip, abort, or policy change |
| `checkpoint` | orchestrator | Pre-`/summarize` snapshot written |
| `compact` | orchestrator | Context reset; resuming from checkpoint |

Subagents echo `model` on `started`, `complete`, and `failed`.

---

## 9. State file

Path: `docs/superpowers/bt-dictionary/orchestrator.state.json`

Orchestrator updates after every log event.

```json
{
  "project": "bosworth-toller-dictionary-index",
  "spec_dir": "docs/superpowers/specs/2026-06-21-bosworth-toller-dictionary-index",
  "log_path": "docs/superpowers/bt-dictionary/orchestrator.log",
  "model_policy": "cost_aware",
  "context_compact_threshold": 0.60,
  "context_last_compact_at": null,
  "context_checkpoint_path": "docs/superpowers/bt-dictionary/orchestrator.checkpoint.md",
  "current_phase": null,
  "phases": {
    "01": {
      "status": "pending",
      "spec": "phase-01-models-and-pos.md",
      "recommended_model": "composer-2.5-fast",
      "model_tier": "fast",
      "model_used": null,
      "retry_count": 0
    }
  },
  "blockers": [],
  "cost_guardrails": {
    "max_heavy_dispatches": 2,
    "never_heavy_on_first_dispatch_phases": ["01","02","05","06","07","08","09"],
    "lint_fail_retry_same_model": true,
    "golden_fail_upgrade_tier": true
  }
}
```

Phase `status` values: `pending`, `in_progress`, `complete`, `failed`, `skipped`.

---

## 10. Failure handling

| Situation | Orchestrator action |
|-----------|---------------------|
| Lint gate fail | Re-dispatch same phase, **same model** |
| pytest / golden fail | Re-dispatch same phase, **+1 tier** |
| Failed twice | Third try → heavy (03–04 only) or `blocked` |
| Design ambiguity | `blocked`; pause for human |
| Phase 09 not wanted | Mark `skipped`; does not block done |

Never dispatch phase N+1 while phase N is not `complete` or `skipped`.

---

## 11. Subagent dispatch prompt

```text
Implement wyrdcraeft BT dictionary Phase NN only.

Model: <slug> — do not switch mid-phase.

Read:
- docs/superpowers/specs/2026-06-21-bosworth-toller-dictionary-index/00-overview.md
- docs/superpowers/specs/2026-06-21-bosworth-toller-dictionary-index/phase-NN-<name>.md

Log:
- Append JSONL to docs/superpowers/bt-dictionary/orchestrator.log
- started → complete|failed with gates

Do not implement other phases.
```

Orchestrator passes `model` via Task tool `model` parameter.

---

## 12. Definition of done

Phases **01–08** are `complete` (09 `complete` or `skipped`). These commands work:

```bash
wyrdcraeft dictionary index-bt --source data/oe_bt.txt --report /tmp/dict_report.json
# → ~/Library/Application Support/wyrdcraeft/dictionary.sqlite3

wyrdcraeft dictionary lookup abbod --pos noun
wyrdcraeft morphology query abbod --with-dictionary
```

Acceptance checks:

- [ ] No separate Add/Substitute/Dele rows in lookup output
- [ ] Homograph `a` splits by POS, merges within POS
- [ ] Sense glosses contain no attestations
- [ ] `dictionary.sqlite3` sits beside `morphology.sqlite3` by default

---

## 13. New session kickoff

Paste into a fresh orchestrator Agent chat:

```text
You are the orchestrator for the wyrdcraeft Bosworth-Toller dictionary index.
Do NOT implement code — dispatch one phase at a time to subagents.

Read:
- docs/superpowers/specs/2026-06-21-bosworth-toller-dictionary-index/ORCHESTRATION.md
- docs/superpowers/specs/2026-06-21-bosworth-toller-dictionary-index/00-overview.md
- docs/superpowers/bt-dictionary/orchestrator.state.json
- docs/superpowers/bt-dictionary/orchestrator.checkpoint.md
- tail docs/superpowers/bt-dictionary/orchestrator.log

Dispatch Phase 01 on composer-2.5-fast when approved. Log every event. Checkpoint + /summarize at 60% context.
```
