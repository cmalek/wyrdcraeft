# Wyrdcraeft Canonical DB Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Replace ad hoc SQLite handling with one canonical `wyrdcraeft.sqlite3` database managed by SQLAlchemy + Alembic, with safe startup migrations, pre-migration backups, explicit rebuild flow, and renamed build commands.

**Architecture:** Add one small persistence package that owns engine/session setup, Alembic integration, backup/restore, and startup readiness checks, while keeping all SQLAlchemy declarative models under `wyrdcraeft/models/`. Keep one canonical app-data DB, route every DB-using CLI entrypoint through the same readiness gate, and migrate service code in vertical slices so behavior stays testable and commit boundaries stay clear.

**Tech Stack:** `sqlalchemy`, `alembic`, `click`, existing `Settings`, existing CLI/service/test layout, SQLite file copy backups, JSON sidecar state

---

## File Map

**Create:**
- `wyrdcraeft/db/__init__.py`
- `wyrdcraeft/db/base.py`
- `wyrdcraeft/models/sqlalchemy.py`
- `wyrdcraeft/db/runtime.py`
- `wyrdcraeft/db/backup.py`
- `wyrdcraeft/db/state.py`
- `wyrdcraeft/db/alembic/env.py`
- `wyrdcraeft/db/alembic/script.py.mako`
- `wyrdcraeft/db/alembic/versions/<revision>_initial_canonical_schema.py`
- `alembic.ini`
- `tests/test_db_runtime.py`
- `tests/test_db_backup.py`
- `tests/test_db_legacy_reset.py`
- `tests/db_fixtures.py`
- `docs/superpowers/specs/2026-06-30-wyrdcraeft-db-migration-orchestration.md`

**Modify:**
- `wyrdcraeft/paths.py`
- `wyrdcraeft/settings.py`
- `wyrdcraeft/cli/cli.py`
- `wyrdcraeft/cli/morphology.py`
- `wyrdcraeft/cli/dictionary.py`
- `wyrdcraeft/cli/lexicon.py`
- `wyrdcraeft/services/morphology/generation/sinks.py`
- `wyrdcraeft/services/morphology/generation/query.py`
- `wyrdcraeft/services/dictionary/sinks.py`
- `wyrdcraeft/services/dictionary/query.py`
- `wyrdcraeft/services/lexicon/schema.py`
- `wyrdcraeft/services/lexicon/build.py`
- `wyrdcraeft/services/lexicon/query.py`
- `wyrdcraeft/services/lexicon/tui.py`
- `wyrdcraeft/__init__.py`
- `wyrdcraeft/models/__init__.py`
- `tests/conftest.py`
- `tests/test_paths.py`
- `tests/test_cli_morphology.py`
- `tests/test_cli_dictionary.py`
- `tests/test_cli_lexicon.py`
- `tests/dictionary/test_attach_morphology_db.py`
- `tests/dictionary/test_index_pipeline.py`
- `tests/dictionary/test_query_service.py`
- `tests/lexicon/test_schema.py`
- `tests/lexicon/source_db.py`
- `doc/source/overview/command_morphology_generate.rst`
- `doc/source/overview/command_dictionary_index_bt.rst`
- `doc/source/overview/command_dictionary_lookup.rst`
- `doc/source/overview/command_lexicon_build.rst`
- `doc/source/overview/command_lexicon_browse.rst`
- `doc/source/overview/using_cli.rst`
- `README.md`
- `CONTEXT.md`
- `docs/adr/0002-canonical-morphology-db-uses-startup-alembic-migrations.md`

**Avoid touching unless clearly necessary:**
- `pyproject.toml`
- `uv.lock`

Reason: both already dirty in working tree. Do not mix unrelated dependency edits into this branch unless the phase truly needs them.

## Locked Decisions

- Canonical DB filename is `wyrdcraeft.sqlite3`.
- Old `morphology.sqlite3` is legacy input, not renamed in place.
- Legacy pre-Alembic DB gets one backup copy, then reset to fresh Alembic-managed canonical DB, then command stops and prints rebuild recipe.
- Rebuild recipe is explicit and separate:
  1. `wyrdcraeft morphology build`
  2. `wyrdcraeft dictionary build`
  3. `wyrdcraeft lexicon build`
- Old command names die fast. No compatibility aliases.
- Remove per-command `--index-db`, `--index-dir`, and dictionary standalone DB mode.
- Keep `dictionary lookup` as thin read-only inspection command on canonical DB.
- Fresh DB creation uses real Alembic migration path, not `Base.metadata.create_all()`.
- Every DB-using CLI command runs startup readiness gate before touching DB.
- Pre-migration backup retention is configurable, default `1`.
- Backup delete prompt state lives in a JSON sidecar beside `wyrdcraeft.sqlite3`.
- Next interactive invocation prompt text is locked:
  `Found backup database from ${date}, caused by migration to ${version}. Delete it? Answer \`y\` if you have used wyrdcraeft successfully since the last migration. [y/N]`
- Startup migration narration stages are locked:
  1. `checking canonical database`
  2. `found legacy database` or `found canonical database`
  3. `checking alembic revision`
  4. `creating backup`
  5. `applying migrations`
  6. `restoring backup after migration failure`
  7. `migration complete`
  8. `rebuild required`

## Orchestrator Strategy

- One orchestrator agent owns sequencing, review, and commit boundaries.
- One fresh implementation subagent per phase.
- No parallel implementation subagents: phases share files and state.
- After each phase:
  1. implementation subagent runs targeted tests + required gates for touched Python
  2. orchestrator runs spec review
  3. orchestrator runs code quality review
  4. implementation subagent fixes review issues
  5. implementation subagent creates one commit for the phase

### Recommended model cost tiers

- **Cheap model:** mechanical doc/test rename, help text, file name swaps, fixture cleanup
- **Standard model:** CLI wiring, settings/path changes, SQLAlchemy query rewrites, migration runtime
- **Most capable model:** initial declarative schema design, Alembic initial migration, legacy reset decision tree review

## Phase 1: Persistence Skeleton and Canonical Path

**Intent:** Create minimal shared persistence package and rename canonical DB path without changing full service internals yet.

**Suggested subagent tier:** standard model

**Files:**
- Create: `wyrdcraeft/db/__init__.py`, `wyrdcraeft/db/base.py`
- Modify: `wyrdcraeft/paths.py`, `wyrdcraeft/settings.py`, `tests/test_paths.py`, `tests/conftest.py`, `wyrdcraeft/__init__.py`

- [x] **Step 1: Write failing path/settings tests for canonical filename**

Add tests covering:
- default canonical filename is `wyrdcraeft.sqlite3`
- app-data override still works
- isolated test fixture points to new filename
- no helper exposes per-command DB path overrides anymore

- [x] **Step 2: Run targeted tests and confirm failure**

Run:

```bash
rtk .venv/bin/pytest tests/test_paths.py tests/conftest.py -q
```

Expected: failures referencing old `morphology.sqlite3` assumptions or missing new helpers.

- [x] **Step 3: Add minimal DB package and rename path constants**

Implement:
- one declarative `Base` in `wyrdcraeft/db/base.py`
- canonical filename constant in `wyrdcraeft/paths.py`
- one canonical-path resolver using only settings/app-data root
- keep default app-data override support for tests/power users

- [x] **Step 4: Run targeted tests until green**

Run:

```bash
rtk .venv/bin/pytest tests/test_paths.py -q
```

- [x] **Step 5: Run Python gates for touched files**

Run:

```bash
rtk .venv/bin/ruff check wyrdcraeft/paths.py wyrdcraeft/settings.py wyrdcraeft/db tests/test_paths.py tests/conftest.py
rtk .venv/bin/mypy wyrdcraeft/paths.py wyrdcraeft/settings.py wyrdcraeft/db
rtk make napoleon-gate
```

Suggested commit: `Add canonical wyrdcraeft.sqlite3 path and DB base`

## Phase 2: Alembic Scaffold, Startup Runtime, Backup Sidecar

**Intent:** Add real Alembic bootstrap, startup decision tree, backup/restore, prompt sidecar, and progress narration.

**Suggested subagent tier:** standard model for implementation, most capable for review

**Files:**
- Create: `alembic.ini`, `wyrdcraeft/db/runtime.py`, `wyrdcraeft/db/backup.py`, `wyrdcraeft/db/state.py`, `wyrdcraeft/db/alembic/env.py`, `wyrdcraeft/db/alembic/script.py.mako`
- Modify: `wyrdcraeft/cli/cli.py`, `tests/test_db_runtime.py`, `tests/test_db_backup.py`, `tests/test_db_legacy_reset.py`

- [x] **Step 1: Write failing runtime tests for startup decision tree**

Add tests for:
- fresh missing DB -> Alembic bootstrap path
- canonical DB with stale revision -> backup then migrate
- migration failure -> restore backup and surface traceback
- legacy `morphology.sqlite3` present -> backup, create fresh canonical DB, stop, print rebuild recipe
- non-interactive invocation keeps backup and prints reminder
- interactive prompt text matches locked wording

- [x] **Step 2: Run targeted tests and confirm failure**

Run:

```bash
rtk .venv/bin/pytest tests/test_db_runtime.py tests/test_db_backup.py tests/test_db_legacy_reset.py -q
```

- [x] **Step 3: Implement minimal runtime services**

Implement:
- SQLAlchemy engine/session factory
- Alembic config helper
- startup narration with locked stage names
- backup file copy + retention
- JSON sidecar read/write
- typed exception carrying traceback text and rebuild instructions

- [x] **Step 4: Wire root CLI through readiness gate**

Requirement:
- root CLI loads settings
- before dispatching any DB-using subcommand, gate runs once
- non-DB commands (`version`, `settings show/create`, maybe source-only commands) skip gate

- [x] **Step 5: Run targeted tests until green**

Run:

```bash
rtk .venv/bin/pytest tests/test_db_runtime.py tests/test_db_backup.py tests/test_db_legacy_reset.py tests/test_main.py -q
```

- [x] **Step 6: Run Python gates**

Run:

```bash
rtk .venv/bin/ruff check wyrdcraeft/db wyrdcraeft/cli/cli.py tests/test_db_runtime.py tests/test_db_backup.py tests/test_db_legacy_reset.py
rtk .venv/bin/mypy wyrdcraeft/db wyrdcraeft/cli/cli.py
rtk make napoleon-gate
```

Suggested commit: `Add Alembic startup runtime with backup and restore`

## Phase 3: Initial Declarative Schema and First Migration

**Intent:** Capture current canonical schema in SQLAlchemy declarative models under `wyrdcraeft/models/` and generate the initial Alembic migration for fresh `wyrdcraeft.sqlite3`.

**Suggested subagent tier:** most capable model

**Files:**
- Create: `wyrdcraeft/models/sqlalchemy.py`, `wyrdcraeft/db/alembic/versions/<revision>_initial_canonical_schema.py`
- Modify: `wyrdcraeft/models/__init__.py`, `wyrdcraeft/db/alembic/env.py`, `tests/lexicon/source_db.py`, `tests/lexicon/test_schema.py`, `tests/dictionary/test_attach_morphology_db.py`

- [x] **Step 1: Inventory current live tables and columns from service code**

Source of truth for first cut:
- `forms`
- `bt_entries`, `bt_senses`, `bt_variants`, `bt_edit_log`
- `lexicon_entries`, `lexicon_forms`, `lexicon_search_keys`, `lexicon_build_meta`
- `alembic_version`

- [x] **Step 2: Write failing schema tests for fresh DB creation via Alembic**

Add tests asserting:
- fresh canonical DB created by runtime has all expected tables
- lexicon columns include `paradigm`
- expected indexes exist

- [x] **Step 3: Implement declarative models and initial Alembic migration**

Rules:
- use “fat models” only where behavior truly belongs on row/table concepts
- avoid speculative relationships if no caller needs them yet
- prefer explicit table/index definitions over clever mixins

- [x] **Step 4: Run targeted schema tests**

Run:

```bash
rtk .venv/bin/pytest tests/lexicon/test_schema.py tests/test_db_runtime.py tests/dictionary/test_attach_morphology_db.py -q
```

- [x] **Step 5: Run Python gates**

Run:

```bash
rtk .venv/bin/ruff check wyrdcraeft/db tests/lexicon/test_schema.py tests/dictionary/test_attach_morphology_db.py
rtk .venv/bin/mypy wyrdcraeft/db
rtk make napoleon-gate
```

Suggested commit: `Add initial Alembic schema for canonical DB`

## Phase 4: CLI Contract Cleanup and Command Rename

**Intent:** Rename long-running commands to `build`, remove obsolete path flags, and standardize rebuild messaging.

**Suggested subagent tier:** cheap model if spec very explicit, otherwise standard model

**Files:**
- Modify: `wyrdcraeft/cli/morphology.py`, `wyrdcraeft/cli/dictionary.py`, `wyrdcraeft/cli/lexicon.py`, `tests/test_cli_morphology.py`, `tests/test_cli_dictionary.py`, `tests/test_cli_lexicon.py`, docs command pages

- [x] **Step 1: Write failing CLI tests for renamed commands**

Cover:
- `morphology build --help`
- `dictionary build --help`
- old `generate` and `index-bt` commands now fail
- removed `--index-db`, `--index-dir`, `--standalone`
- rebuild recipe text uses three `build` commands

- [x] **Step 2: Run targeted CLI tests and confirm failure**

Run:

```bash
rtk .venv/bin/pytest tests/test_cli_morphology.py tests/test_cli_dictionary.py tests/test_cli_lexicon.py -q
```

- [x] **Step 3: Implement CLI rename and flag removal**

Keep:
- `dictionary lookup`
- canonical DB resolution from settings/app-data only

- [x] **Step 4: Update docs/help text**

Touch:
- command docs for morphology, dictionary, lexicon
- any quickstart/usage snippets that mention old commands or old file names

- [x] **Step 5: Run targeted tests and docs-adjacent checks**

Run:

```bash
rtk .venv/bin/pytest tests/test_cli_morphology.py tests/test_cli_dictionary.py tests/test_cli_lexicon.py tests/test_paths.py -q
```

- [x] **Step 6: Run Python gates**

Run:

```bash
rtk .venv/bin/ruff check wyrdcraeft/cli tests/test_cli_morphology.py tests/test_cli_dictionary.py tests/test_cli_lexicon.py
rtk .venv/bin/mypy wyrdcraeft/cli
rtk make napoleon-gate
```

Suggested commit: `Rename DB-producing commands to build`

## Phase 5: Lexicon Vertical Slice to SQLAlchemy

**Intent:** Replace lexicon schema/create/query paths first, since lexicon already acts like a semi-isolated read model.

**Suggested subagent tier:** standard model

**Files:**
- Modify: `wyrdcraeft/services/lexicon/schema.py`, `wyrdcraeft/services/lexicon/build.py`, `wyrdcraeft/services/lexicon/query.py`, `wyrdcraeft/services/lexicon/tui.py`, `tests/lexicon/test_build.py`, `tests/lexicon/test_query_service.py`, `tests/lexicon/test_schema.py`

- [x] **Step 1: Write failing lexicon tests for SQLAlchemy-backed schema/query path**

Cover:
- schema create path uses Alembic-managed tables, not bespoke `executescript`
- query service still returns same browse semantics
- startup no longer performs lexicon-only ad hoc column migration

- [x] **Step 2: Run targeted tests and confirm failure**

Run:

```bash
rtk .venv/bin/pytest tests/lexicon/test_schema.py tests/lexicon/test_build.py tests/lexicon/test_query_service.py tests/test_cli_lexicon.py -q
```

- [x] **Step 3: Implement minimal SQLAlchemy lexicon persistence**

Prefer:
- SQLAlchemy Core/ORM queries where it reduces code
- keep existing TUI contracts stable
- delete ad hoc `migrate_lexicon_schema(...)` path once replacement proven

- [x] **Step 4: Run targeted tests until green**

Run same command as step 2.

- [x] **Step 5: Run Python gates**

Run:

```bash
rtk .venv/bin/ruff check wyrdcraeft/services/lexicon tests/lexicon
rtk .venv/bin/mypy wyrdcraeft/services/lexicon
rtk make napoleon-gate
```

Suggested commit: `Move lexicon persistence to SQLAlchemy`

## Phase 6: Dictionary Vertical Slice to SQLAlchemy

**Intent:** Move `bt_*` writes and reads to canonical SQLAlchemy persistence while preserving attach-style behavior inside the one DB.

**Suggested subagent tier:** standard model

**Files:**
- Modify: `wyrdcraeft/services/dictionary/sinks.py`, `wyrdcraeft/services/dictionary/query.py`, `tests/dictionary/test_index_pipeline.py`, `tests/dictionary/test_query_service.py`, `tests/test_cli_dictionary.py`

- [x] **Step 1: Write failing dictionary tests for SQLAlchemy-backed writes/reads**

Cover:
- build writes `bt_*` into canonical DB
- lookup reads same rows and output shape unchanged
- no standalone DB mode remains

- [x] **Step 2: Run targeted tests and confirm failure**

Run:

```bash
rtk .venv/bin/pytest tests/dictionary/test_index_pipeline.py tests/dictionary/test_query_service.py tests/test_cli_dictionary.py -q
```

- [x] **Step 3: Implement minimal SQLAlchemy dictionary persistence**

Prefer:
- bulk insert helpers for senses/variants
- explicit transactions
- no extra abstraction layer unless repeated twice

- [x] **Step 4: Run targeted tests until green**

Run same command as step 2.

- [x] **Step 5: Run Python gates**

Run:

```bash
rtk .venv/bin/ruff check wyrdcraeft/services/dictionary tests/dictionary tests/test_cli_dictionary.py
rtk .venv/bin/mypy wyrdcraeft/services/dictionary
rtk make napoleon-gate
```

Suggested commit: `Move dictionary persistence to SQLAlchemy`

## Phase 7: Morphology Vertical Slice to SQLAlchemy

**Intent:** Move `forms` sink/query path last, preserving bulk-write performance and query behavior.

**Suggested subagent tier:** standard model for implementation, most capable review for performance sanity

**Files:**
- Modify: `wyrdcraeft/services/morphology/generation/sinks.py`, `wyrdcraeft/services/morphology/generation/query.py`, `tests/morphology/test_query_service.py`, `tests/test_cli_morphology.py`, `tests/dictionary/test_attach_morphology_db.py`

- [x] **Step 1: Write failing morphology persistence/query tests**

Cover:
- build writes forms to canonical DB
- query service returns same rows/order
- dictionary join resolution still works inside canonical DB

- [x] **Step 2: Run targeted tests and confirm failure**

Run:

```bash
rtk .venv/bin/pytest tests/morphology/test_query_service.py tests/test_cli_morphology.py tests/dictionary/test_attach_morphology_db.py -q
```

- [x] **Step 3: Implement minimal SQLAlchemy/Core bulk insert path**

Important:
- do not instantiate ORM row objects per emitted form if bulk Core insert is simpler/faster
- query path may still use ORM/Core mix
- preserve emitted ordering semantics

- [x] **Step 4: Run targeted tests until green**

Run same command as step 2.

- [x] **Step 5: Run Python gates**

Run:

```bash
rtk .venv/bin/ruff check wyrdcraeft/services/morphology tests/morphology tests/test_cli_morphology.py
rtk .venv/bin/mypy wyrdcraeft/services/morphology
rtk make napoleon-gate
```

Suggested commit: `Move morphology persistence to SQLAlchemy`

## Phase 8: Full Verification, Docs Sweep, Orchestration Handoff

**Intent:** Finish docs, verify migration/backup UX end-to-end, and leave a native Codex orchestration prompt in-repo.

**Suggested subagent tier:** cheap model for docs, standard for verification/debug

**Files:**
- Create: `docs/superpowers/specs/2026-06-30-wyrdcraeft-db-migration-orchestration.md`
- Modify: `README.md`, command docs, any touched runbook text, plan checkbox progress

- [x] **Step 1: Write orchestration prompt file**

Include:
- branch recommendation
- phase order
- subagent model guidance
- mandatory commit after each phase
- mandatory review loop after each phase

- [x] **Step 2: Run focused end-to-end tests**

Run:

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
```

- [x] **Step 3: Run broad required gates**

Run:

```bash
rtk .venv/bin/ruff check wyrdcraeft tests
rtk .venv/bin/mypy wyrdcraeft
rtk make napoleon-gate
```

- [x] **Step 4: If broad failures are pre-existing, separate them clearly from introduced failures**

- [x] **Step 5: Create final verification commit**

Suggested commit: `Document and verify canonical DB migration flow`

## Native Codex Execution Notes

- Use one orchestrator thread for this whole plan.
- Orchestrator should dispatch one fresh subagent per phase, never parallel phase workers.
- Cheapest safe tier:
  - phases 1, 4, 8: cheap/fast model acceptable
  - phases 2, 5, 6, 7: standard model
  - phase 3 and reviews of phases 2/3/7: most capable model
- Each phase must end with:
  1. tests for that phase
  2. `ruff`
  3. `mypy`
  4. `make napoleon-gate`
  5. one commit

## Completion Checklist

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
- [x] Required gates pass or unrelated failures are documented separately
