# Unified Dictionary Workflow — Phased Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development.
> One implementer subagent **per task** within a phase. **Do not start the next phase
> until Gate A, Gate B, and the phase commit all pass.** Reviews and commit happen
> **once per phase**, not per task.

**Goal:** Replace the split morphology/dictionary/lexicon build triangle with one
`wyrdcraeft dictionary build` pipeline, drop the 62M-row `search_keys` read model, and
serve dictionary-only browse search directly from `bt_*` tables with variant-aware ranking.

**Architecture:** Phase A lands the canonical build pipeline (dictionary rebuild, optional
morphology regen, `forms.entry_id` relink, POS inference). Phase B removes search-index
tables, rewrites browse search, and consolidates CLI surfaces under `dictionary` (plus
`morphology query` only).

**Tech stack:** Python 3.12+, SQLAlchemy 2.x, Alembic, SQLite, Click, Textual, pytest,
`isolated_morphology_app_data`, `make napoleon-gate`.

**Origin:** Design grill session 2026-07-07 (search_keys analysis + build-order fixes).

---

## Locked decisions (do not re-litigate)

| # | Decision |
|---|----------|
| 1 | `lexicon browse` search returns **dictionary entries only** (no morph-form hits in results) |
| 2 | Drop `search_keys` and `search_build_meta` (Phase B migration) |
| 3 | Delete `wyrdcraeft lexicon build` |
| 4 | Delete `wyrdcraeft morphology build` — generation moves under `dictionary build` |
| 5 | **`dictionary build` always** rebuilds `bt_*` and **relinks all** `forms.entry_id` |
| 6 | Morphology regen when `forms` is empty **or** `--with-morphology` is passed |
| 7 | Truncate `forms` before morphology regen |
| 8 | `dictionary build` bootstraps full canonical schema (Alembic) on greenfield |
| 9 | POS inference runs at end of `dictionary build` (not morphology-only command) |
| 10 | Morph-only CLI flags apply **only** when morphology stage runs; silently ignored otherwise |
| 11 | Keep **`morphology query`** under `morphology` group |
| 12 | Move `ingest-wright-text`, `audit-wright` to `dictionary` group |
| 13 | Rename `dictionary lookup` → **`dictionary query`** |
| 14 | Move `lexicon browse` → **`dictionary browse`**; remove `lexicon` group |
| 15 | Remove orphan morphology section from browse TUI |
| 16 | Browse search: 12-tier rank (headword + variant × exact / normalized_title / norm_key / affix) at query time |
| 17 | Shared relink logic: one service used by dictionary-build relink and morphology sink insert |
| 18 | **`forms.entry_id` relink required after every dictionary rebuild** (PK ids change; entries may disappear) |

---

## Phases

| Phase | Document | Delivers |
|-------|----------|----------|
| **A** | [phase-a-unified-dictionary-build.md](./phase-a-unified-dictionary-build.md) | Unified `dictionary build`, relink, POS inference, remove morph/lexicon build commands |
| **B** | [phase-b-dictionary-browse-and-cli.md](./phase-b-dictionary-browse-and-cli.md) | Drop search tables, query-time browse search, CLI/TUI moves, docs |

**Prerequisite:** Alembic head at `20260706_04` (Phase D legacy column drop on branch).

---

## Subagent orchestration (every phase)

```text
1. Coordinator reads phase doc + this README locked decisions
2. Coordinator creates TodoWrite from phase task list
3. For each task in the phase:
   a. Dispatch implementer subagent (generalPurpose) with:
      - Full task text from phase doc (do not summarize)
      - AGENTS.md constraints (napoleon-gate, isolated_morphology_app_data)
   b. Implementer runs task-level quality gates listed in the task
   c. Implementer does NOT commit (phase commit is coordinator-only after gates)
4. After ALL tasks in the phase:
   a. Coordinator runs phase validation commands
   b. Gate A — Spec review (code-reviewer, readonly)
   c. Gate B — Code review (bugbot, readonly)
   d. Single phase commit (coordinator) — only if A and B pass
5. Start next phase
```

---

## Gate A — Spec review (required once per phase)

Dispatch **`code-reviewer`** subagent (`readonly: true`):

```text
Full Repository Path: /Users/cmalek/src/workspace/wyrdcraeft
Plan: doc/plans/unified-dictionary-workflow/phase-<a|b>-*.md
Design: doc/plans/unified-dictionary-workflow/README.md (locked decisions)
Diff: branch changes (uncommitted + commits since phase start)

Verify implementation matches the phase spec and locked decisions.
Report: missing requirements, wrong CLI names, search_keys still required when
        phase should drop it, morphology build resurrected, entry_id relink skipped
        on dictionary rebuild, POS inference on wrong command.
```

**Pass criteria:** Zero unresolved spec deviations, or explicit user-approved waivers.

---

## Gate B — Code review (required once per phase)

Dispatch **`bugbot`** subagent (`readonly: true`):

```text
Full Repository Path: /Users/cmalek/src/workspace/wyrdcraeft
Diff: branch changes (uncommitted + commits since phase start)
Custom Instructions: Follow AGENTS.md. Flag morphology tests writing real app-data
  DB without isolated_morphology_app_data. Flag dictionary build that deletes
  bt_entries while forms.entry_id still set (FK violation). Flag silent loss of
  --with-morphology behavior. Flag napoleon/doc-contract regressions.
```

**Pass criteria:** No blocking issues; phase validation commands all green.

---

## Phase commit (required after Gates A and B)

Coordinator runs:

```bash
git status
git diff
git log -3 --oneline
```

Stage only files touched in the phase. **One commit per phase** via HEREDOC message from
the phase doc. Do not batch phases into one commit.

---

## Global validation

After all tasks in a phase, coordinator runs:

```bash
.venv/bin/ruff check <touched-py-files>
.venv/bin/mypy <touched-py-files>
make napoleon-gate
```

Phase A additionally:

```bash
.venv/bin/pytest tests/dictionary tests/morphology/test_cli_morphology.py -q
.venv/bin/pytest tests/test_cli_dictionary.py -q
git diff --exit-code -- tests/morphology/data/refactor_baseline.json
```

Phase B additionally:

```bash
.venv/bin/pytest tests/lexicon tests/test_cli_lexicon.py tests/test_cli_dictionary.py -q
```

---

## Execution options

**1. Subagent-driven (recommended)** — one implementer subagent per task; gates + **one
commit per phase**.

**2. Inline** — parent agent executes phase tasks sequentially with same gates and
commits.

Start with **Phase A** only.
