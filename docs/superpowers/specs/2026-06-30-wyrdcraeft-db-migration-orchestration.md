# Orchestration: Wyrdcraeft Canonical DB Migration

Use this prompt in a **single orchestrator thread**. Dispatch **one fresh implementation subagent per phase**. Never run phase workers in parallel — phases share files and DB state.

**Plan:** `docs/superpowers/plans/2026-06-30-wyrdcraeft-canonical-db-migration.md`  
**Branch:** `codex/canonical-db-migration` (or a successor branch that preserves phase commits)  
**Repo:** `/Users/cmalek/src/workspace/wyrdcraeft`

## Operating modes (mandatory for every subagent)

- **/caveman** — terse reports
- **/using-superpowers** — invoke relevant skills before acting
- **/ponytail** — shortest correct diff; docs only where the phase requires

## Shell commands

Use **`rtk`** for all shell commands when possible:

```bash
rtk .venv/bin/pytest tests/... -q
rtk .venv/bin/ruff check wyrdcraeft tests
rtk .venv/bin/mypy wyrdcraeft
PATH="/Users/cmalek/src/workspace/wyrdcraeft/.venv/bin:$PATH" rtk make napoleon-gate
```

## Model tiers

| Phase | Tier | Rationale |
|-------|------|-----------|
| 1 | cheap or standard | path/settings rename, minimal package |
| 2 | standard (most capable for review) | Alembic runtime, backup/restore, gate wiring |
| 3 | **most capable** | initial declarative schema + first migration |
| 4 | cheap (if spec explicit) or standard | CLI rename, flag removal, help/docs |
| 5 | standard | lexicon SQLAlchemy slice |
| 6 | standard | dictionary SQLAlchemy slice |
| 7 | standard (most capable for perf review) | morphology bulk insert + query |
| 8 | cheap (docs) + standard (verification) | docs sweep, e2e tests, orchestration handoff |

Schema/runtime reviews for phases **2, 3, 7** should use the **most capable** model.

## Phase order (1 → 8)

Execute strictly in order. Each phase ends with **one commit** before the next phase starts.

1. **Persistence skeleton and canonical path** — `wyrdcraeft.sqlite3` path, `wyrdcraeft/db/base.py`
2. **Alembic scaffold, startup runtime, backup sidecar** — runtime gate, backup/restore, narration
3. **Initial declarative schema and first migration** — `wyrdcraeft/models/sqlalchemy.py`, Alembic revision
4. **CLI contract cleanup and command rename** — `build` commands; remove `--index-db`, `--index-dir`, `--standalone`
5. **Lexicon vertical slice** — SQLAlchemy-backed lexicon persistence
6. **Dictionary vertical slice** — SQLAlchemy-backed `bt_*` persistence
7. **Morphology vertical slice** — SQLAlchemy/Core bulk `forms` writes and queries
8. **Full verification, docs sweep, orchestration handoff** — this file, README, plan checkboxes, e2e gates

## Per-phase workflow (mandatory)

For each phase:

1. **Dispatch** one fresh subagent with the phase section from the plan + this orchestration doc.
2. Subagent implements, runs **phase-targeted tests**, then **ruff**, **mypy**, **napoleon-gate** on touched Python.
3. **Orchestrator: spec-compliance review** — verify deliverables match the plan phase (files, behavior, locked decisions).
4. **Orchestrator: code-quality review** — architecture, test coverage, no scope creep.
5. Subagent fixes review findings.
6. Subagent creates **exactly one commit** with the plan's suggested message (or a close variant).
7. Proceed to next phase only after commit lands.

**Do not commit** unrelated files (`pyproject.toml`, `uv.lock`, `.aidex/index.db`) unless a phase truly requires them.

## Locked decisions (do not re-litigate)

- Canonical DB filename: **`wyrdcraeft.sqlite3`**
- Legacy **`morphology.sqlite3`** is input only — backup, fresh Alembic DB, stop, print rebuild recipe
- Fresh DB via **Alembic**, not `Base.metadata.create_all()` for production bootstrap
- Rebuild recipe (in order):
  1. `wyrdcraeft morphology build`
  2. `wyrdcraeft dictionary build`
  3. `wyrdcraeft lexicon build`
- Old command names removed (`generate`, `index-bt`); no compatibility aliases
- No per-command `--index-db`, `--index-dir`, or dictionary standalone DB mode
- Keep **`dictionary lookup`** as read-only inspection on canonical DB
- Every DB-using CLI command runs the **startup readiness gate** once before dispatch
- Backup retention default **1**; JSON sidecar beside `wyrdcraeft.sqlite3`
- Locked interactive delete prompt:
  `Found backup database from ${date}, caused by migration to ${version}. Delete it? Answer \`y\` if you have used wyrdcraeft successfully since the last migration. [y/N]`
- Locked startup narration stages: `checking canonical database` → `found legacy database` / `found canonical database` → `checking alembic revision` → `creating backup` → `applying migrations` → `restoring backup after migration failure` → `migration complete` → `rebuild required`

## Phase 8 verification commands

```bash
rtk .venv/bin/pytest \
  tests/test_db_runtime.py \
  tests/test_db_backup.py \
  tests/test_db_legacy_reset.py \
  tests/test_cli_morphology.py \
  tests/test_cli_dictionary.py \
  tests/test_cli_lexicon.py \
  tests/lexicon/test_schema.py \
  tests/lexicon/test_query_service.py \
  tests/dictionary/test_query_service.py \
  tests/morphology/test_query_service.py -q

rtk .venv/bin/ruff check wyrdcraeft tests
rtk .venv/bin/mypy wyrdcraeft
PATH="/Users/cmalek/src/workspace/wyrdcraeft/.venv/bin:$PATH" rtk make napoleon-gate
```

Suggested final commit: `Document and verify canonical DB migration flow`

## Completion checklist

Mark all items in the plan when Phase 8 finishes:

- [x] Canonical DB is `wyrdcraeft.sqlite3`
- [x] Old `morphology.sqlite3` treated as legacy input
- [x] Fresh DB created via Alembic
- [x] Startup gate narrates decision path and progress
- [x] Failed migration restores backup and prints traceback
- [x] Successful migration preserves one backup and stores sidecar prompt state
- [x] Next interactive invocation asks locked delete question
- [x] Build commands renamed and old names removed
- [x] No per-command DB path flags remain
- [x] `dictionary lookup` still works on canonical DB
- [x] Morphology, dictionary, lexicon persistence all use SQLAlchemy-owned schema
- [x] Required gates pass or unrelated failures documented separately

## Preflight (every subagent)

Before plan/code:

1. `memory_search` for prior migration context
2. `aidex_session` + at least one `aidex_query` / signature call
3. At least one `code-index` search
4. `context7` / package-registry only for external library behavior

Report tool names and one-line results in an early update.

## Post-implementation gate (touched Python)

```bash
rtk .venv/bin/ruff check <touched files or wyrdcraeft tests>
rtk .venv/bin/mypy <touched package>
PATH="/Users/cmalek/src/workspace/wyrdcraeft/.venv/bin:$PATH" rtk make napoleon-gate
```

Fix introduced failures. Report pre-existing failures separately.
