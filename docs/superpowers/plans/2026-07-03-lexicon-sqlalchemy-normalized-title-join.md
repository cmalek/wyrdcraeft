# Lexicon SQLAlchemy Rebuild + Normalized Title Join Index Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the lexicon rebuild workflow onto SQLAlchemy Core (matching the rest of the canonical DB stack), then extract one shared morphology↔dictionary join resolver keyed by `normalized_title` so lexicon build, dictionary query, and morphology dictionary joins cannot drift again.

**Session state (2026-07-03):** Slice 1 **complete** — commit `64c6223` on `codex/canonical-db-migration`. Handoff: `docs/superpowers/handoffs/2026-07-03-lexicon-slice1-session-state.md`. Slice 2 **pending**.

**Architecture:** Deliver in **two slices**. Slice 1 replaces the hybrid SQLAlchemy-schema + `sqlite3` rebuild path in `lexicon/build.py` with one SQLAlchemy Core transaction using batched `insert()`/`delete()`/`update()`/`select()` against existing declarative models in `wyrdcraeft/models/sqlalchemy.py`, dropping TEMP staging tables in favor of Python batching. Slice 2 adds `NormalizedTitleJoinIndex` with `resolve_one()` and `resolve_all()` in a small dictionary service module, preloads that index in `BTQueryService`, and uses it from the lexicon form stream while deleting duplicated join SQL and `_select_entry_id`.

**Tech Stack:** SQLAlchemy 2 Core, existing `LexiconEntry`/`LexiconForm`/`LexiconSearchKey`/`LexiconBuildMeta`/`Form`/`BTEntry`/`BTVariant` models, `wyrdcraeft.db.runtime.create_engine`, existing lexicon build progress/event runtime, pytest

---

## Background

Phases 1–8 of the canonical DB migration moved dictionary/morphology persistence and lexicon query/schema to SQLAlchemy. **Slice 1 (2026-07-03, `64c6223`) migrated lexicon rebuild to SQLAlchemy Core** — no `sqlite3`, no TEMP staging, truncate-not-drop, Alembic-owned DDL. `_select_entry_id` remains until Slice 2.

Recent commit `c651f32` added macron-preserving `normalized_title` join keys. The same 3-step join rule now exists in:

- `wyrdcraeft/services/lexicon/build.py` — `_select_entry_id`
- `wyrdcraeft/services/dictionary/query.py` — `_resolve_entry_ids_by_normalized_title`

These implementations are already semantically divergent (POS variant filtering, single vs multi match). This plan fixes that after Slice 1 stabilizes the rebuild path.

---

## File Map

**Slice 1 — create:** none expected

**Slice 1 — modify:**
- `wyrdcraeft/services/lexicon/build.py` — primary rewrite
- `wyrdcraeft/services/lexicon/schema.py` — remove `sqlite3` adapter when no callers remain
- `tests/lexicon/test_build.py` — adjust helpers only if connection type changes
- `tests/lexicon/source_db.py` — only if stale-path assumptions change
- `CONTEXT.md` — optional glossary touch in Slice 2, not required in Slice 1

**Slice 2 — create:**
- `wyrdcraeft/services/dictionary/normalized_title_join.py`
- `tests/dictionary/test_normalized_title_join.py` — pure index/matcher tests with inline row tuples

**Slice 2 — modify:**
- `wyrdcraeft/services/dictionary/query.py` — preload index, delete duplicated SQL
- `wyrdcraeft/services/lexicon/build.py` — preload index, delete `_select_entry_id`
- `tests/dictionary/test_query_service.py` — keep passing; add cases only if gaps found
- `tests/lexicon/test_build.py` — variant join regression (`abbod` → `abbad`)
- `tests/morphology/test_query_service.py` — dictionary join via normalized title
- `CONTEXT.md` — add glossary entries for join index / resolve policies (no implementation detail)

**Avoid unless necessary:**
- `wyrdcraeft/models/sqlalchemy.py` — tables already defined
- Alembic migrations — no schema change required for this plan
- `pyproject.toml`, `uv.lock`

---

## Locked Decisions

### Slice sequencing

- **Slice 1:** Lexicon rebuild → SQLAlchemy Core only. Keep `_select_entry_id` inline temporarily.
- **Slice 2:** Extract join index + wire BT query + lexicon form stream. Delete duplicated join code.

Do not combine slices in one commit boundary unless explicitly requested.

### Lexicon rebuild (Slice 1)

- Use **SQLAlchemy Core only** for reads/writes. No ORM `session.add()` per row.
- **Drop TEMP staging tables** (`temp_lexicon_forms_stage`, `temp_lexicon_search_keys_stage`).
- Keep **Python batching** using existing `_form_stage_batch_size` (and equivalent for search keys).
- Pattern writes after `SqliteIndexSink`: `connection.execute(insert(LexiconForm), batch_of_dicts)`.
- One **`engine.begin()`** (or connect + explicit transaction) owns the full rebuild.
- Preserve stage names, progress events, counter events, and cooperative cancel semantics.
- Wire cancel through SQLAlchemy DBAPI: `connection.connection.dbapi_connection.interrupt` (verify exact attribute against installed SQLAlchemy version in tests).
- Migrate module-level helpers in `build.py` off `sqlite3.Connection`:
  - `read_lexicon_build_meta`
  - `lexicon_read_model_has_data`
  - `check_lexicon_staleness`
  - `_count_table_rows`
- Fix stale docstrings referencing `morphology.sqlite3` → canonical `wyrdcraeft.sqlite3`.
- **Alembic owns lexicon DDL** — `create_lexicon_tables()` **removed**; rebuild must not create or drop tables.
- **`lexicon build` truncates** (`DELETE FROM lexicon_*`) only; table shape comes from Alembic migrations.
- **`SCHEMA_VERSION` removed** from build meta and staleness checks (DDL truth is `alembic_version`).
- Additive DDL changes: backfill in Alembic migration when needed; do not force rebuild for schema bumps.
- Users should **rarely** need `lexicon build` except for source-data drift or first build.

### Normalized title join index (Slice 2)

- New type: `NormalizedTitleJoinIndex` in `wyrdcraeft/services/dictionary/normalized_title_join.py`.
- Factory: `from_entry_variant_rows(entries, variants)` where rows are `(entry_id, normalized_title, pos)`.
- Normalize inputs inside `resolve_*` via `normalize_morphology_title`.
- **Canonical tier order (both methods):**
  1. Direct `bt_entries` hit on `(normalized_title, pos)` when `pos` provided.
  2. Direct `bt_entries` hit on `normalized_title` only when **exactly one** entry across all POS.
  3. `bt_variants.normalized_title` match, **POS-filtered when `pos` given**.
- **`resolve_all(title, pos)`:** tier 1 → all sorted entry ids; tier 2 → single-id list; tier 3 → all matching variant entry ids (deduped, stable order).
- **`resolve_one(title, pos)`:** tier 1 → `min(ids)` when any; tier 2/3 → single id or `None`; tier 3 POS-filtered (fixes current lexicon variant drift vs BT).
- `BTQueryService.lookup_by_normalized_title` → `resolve_all` then existing `_load_entry` per id.
- Lexicon form stream → build index once per rebuild, call `resolve_one` per form row.
- Delete `_select_entry_id` and `_resolve_entry_ids_by_normalized_title` after wiring.

### Explicit non-goals

- No lexicon browse/query rewrite (already SQLAlchemy).
- No dictionary write-path rewrite in this plan.
- No ADR unless human explicitly requests one later.
- Do not route lexicon browse search through `normalize_morphology_title` (see `CONTEXT.md`).

---

## Slice 1: Lexicon Rebuild → SQLAlchemy Core ✅

**Status:** Complete — commit `64c6223` (2026-07-03).

### Task 1: Inventory sqlite3 call sites in lexicon build

**Files:**
- Read: `wyrdcraeft/services/lexicon/build.py`
- Read: `wyrdcraeft/services/lexicon/schema.py`

- [x] **Step 1:** List every method taking `sqlite3.Connection` and every raw SQL string used in rebuild.
- [x] **Step 2:** Note which operations are read vs write vs DDL (TEMP) vs metadata.
- [x] **Step 3:** Confirm existing tests in `tests/lexicon/test_build.py` cover rebuild, POS infer, variant join, staleness, cancel.

### Task 2: Replace rebuild entry transaction

**Files:**
- Modify: `wyrdcraeft/services/lexicon/build.py`

- [ ] **Step 1:** Change `LexiconRebuilder.rebuild()` to open one SQLAlchemy engine/connection for the full rebuild instead of `sqlite3.connect()`.
- [ ] **Step 2:** Replace `BEGIN IMMEDIATE` / commit / rollback with SQLAlchemy transaction boundaries.
- [ ] **Step 3:** Wire cooperative cancel to DBAPI `interrupt` on the SQLAlchemy connection.
- [ ] **Step 4:** Run targeted lexicon build tests; fix transaction/cancel wiring only.

### Task 3: Clear lexicon tables via Core delete

**Files:**
- Modify: `wyrdcraeft/services/lexicon/build.py`

- [ ] **Step 1:** Replace `DELETE FROM lexicon_*` raw SQL with `delete(LexiconSearchKey)`, `delete(LexiconForm)`, `delete(LexiconEntry)`, `delete(LexiconBuildMeta)` in FK-safe order.
- [ ] **Step 2:** Run lexicon build tests.

### Task 4: Source verification and counts via Core select

**Files:**
- Modify: `wyrdcraeft/services/lexicon/build.py`

- [ ] **Step 1:** Rewrite `_ensure_required_sources` using SQLAlchemy inspect or `select` against `sqlite_master` / known tables.
- [ ] **Step 2:** Rewrite source row counts (`forms`, `bt_entries`) with `select(func.count())`.
- [ ] **Step 3:** Run lexicon build tests.

### Task 5: POS inference via Core update

**Files:**
- Modify: `wyrdcraeft/services/lexicon/build.py`

- [ ] **Step 1:** Load POS-empty `bt_entries` rows via `select(BTEntry)` (or Core equivalent).
- [ ] **Step 2:** Load distinct morphology wordclasses per `normalized_title` via `select(Form)`.
- [ ] **Step 3:** Apply `update(BTEntry)` when `infer_bt_pos_from_wordclasses` returns one POS.
- [ ] **Step 4:** Preserve progress/cancel behavior in the loop.
- [ ] **Step 5:** Run lexicon build tests.

### Task 6: Entry load + insert via Core

**Files:**
- Modify: `wyrdcraeft/services/lexicon/build.py`

- [ ] **Step 1:** Rewrite `_load_entry_payloads` reads against `bt_entries`, `bt_senses`, `bt_variants` using Core `select` + mappings.
- [ ] **Step 2:** Replace `_insert_entries` `executemany` with batched `insert(LexiconEntry)` dict payloads.
- [ ] **Step 3:** Run lexicon build tests.

### Task 7: Form stream without TEMP table

**Files:**
- Modify: `wyrdcraeft/services/lexicon/build.py`

- [ ] **Step 1:** Stream `forms` rows via Core `select(Form)` ordered by `id ASC`.
- [ ] **Step 2:** Keep `_select_entry_id` unchanged in this slice; compute `entry_id` per row as today.
- [ ] **Step 3:** Accumulate dict payloads in Python batches sized by `_form_stage_batch_size`.
- [ ] **Step 4:** Flush each batch with `insert(LexiconForm)` inside the same transaction.
- [ ] **Step 5:** Preserve `LOAD_FORMS` / `INSERT_FORMS` progress semantics on batch boundaries.
- [ ] **Step 6:** Remove all TEMP table DDL/DML for forms.
- [ ] **Step 7:** Run lexicon build tests, especially large-form fixtures if present.

### Task 8: Search keys without TEMP table

**Files:**
- Modify: `wyrdcraeft/services/lexicon/build.py`

- [ ] **Step 1:** Keep existing Python search-key generation logic (`normalize_old_english` indexing unchanged).
- [ ] **Step 2:** Replace TEMP staging + `INSERT OR IGNORE SELECT` with batched `insert(LexiconSearchKey)` using dedupe strategy equivalent to current unique index (may use `insert(...).prefix_with("OR IGNORE")` for SQLite or pre-dedupe in Python — match current behavior).
- [ ] **Step 3:** Run lexicon build tests.

### Task 9: Build metadata + module helpers

**Files:**
- Modify: `wyrdcraeft/services/lexicon/build.py`
- Modify: `wyrdcraeft/services/lexicon/schema.py`

- [ ] **Step 1:** Rewrite `_insert_build_meta` via Core `insert(LexiconBuildMeta)` / upsert pattern currently used.
- [ ] **Step 2:** Migrate `read_lexicon_build_meta`, `lexicon_read_model_has_data`, `check_lexicon_staleness`, `_count_table_rows` to accept `Engine | Connection | Path` (prefer Path → engine for callers).
- [ ] **Step 3:** Remove `sqlite3` adapter from `schema.py` if no callers remain.
- [ ] **Step 4:** Run full lexicon test module.

### Task 10: Slice 1 quality gate

**Files:**
- Touched Python from Slice 1

- [ ] **Step 1:** `ruff check` on touched files
- [ ] **Step 2:** `.venv/bin/mypy` on touched files
- [ ] **Step 3:** `make napoleon-gate`
- [ ] **Step 4:** `pytest tests/lexicon/test_build.py tests/lexicon/test_schema.py -q`
- [x] **Step 5:** Commit Slice 1 with message focused on lexicon rebuild SQLAlchemy Core migration (`64c6223`)

---

## Slice 2: Normalized Title Join Index ⏳ NEXT

### Task 11: Pure join index module + tests

**Files:**
- Create: `wyrdcraeft/services/dictionary/normalized_title_join.py`
- Create: `tests/dictionary/test_normalized_title_join.py`

- [ ] **Step 1:** Implement `NormalizedTitleJoinIndex.from_entry_variant_rows`.
- [ ] **Step 2:** Implement `resolve_all` and `resolve_one` per locked tier order and POS-filtered variants.
- [ ] **Step 3:** Write unit tests with inline tuples covering:
  - POS direct hit (single and multiple ids → `resolve_all` vs `resolve_one`)
  - exactly-one title across POS
  - variant match with POS filter
  - variant match without POS
  - no match
  - `abbod`-style variant join case mirroring dictionary fixtures
- [ ] **Step 4:** Run new tests + quality gate on new files

### Task 12: BTQueryService preload + resolve_all

**Files:**
- Modify: `wyrdcraeft/services/dictionary/query.py`
- Test: `tests/dictionary/test_query_service.py`

- [ ] **Step 1:** Preload `NormalizedTitleJoinIndex` in `BTQueryService.__init__` from `bt_entries` + `bt_variants` rows.
- [ ] **Step 2:** Rewrite `lookup_by_normalized_title` to call `index.resolve_all` then `_load_entry` for each id.
- [ ] **Step 3:** Delete `_resolve_entry_ids_by_normalized_title` and its duplicated SQL.
- [ ] **Step 4:** Run dictionary query tests

### Task 13: Lexicon form stream uses resolve_one

**Files:**
- Modify: `wyrdcraeft/services/lexicon/build.py`
- Test: `tests/lexicon/test_build.py`

- [ ] **Step 1:** During form load stage, preload the same join index from source tables once.
- [ ] **Step 2:** Replace `_select_entry_id(...)` calls with `join_index.resolve_one(...)`.
- [ ] **Step 3:** Delete `_select_entry_id` method.
- [ ] **Step 4:** Run lexicon build tests including `test_rebuild_lexicon_joins_abbod_form_via_variant_normalized_title`

### Task 14: Morphology dictionary join regression

**Files:**
- Test: `tests/morphology/test_query_service.py`
- Read: `wyrdcraeft/services/morphology/generation/query.py`

- [ ] **Step 1:** Confirm morphology join still goes through `BTQueryService.lookup_by_normalized_title`.
- [ ] **Step 2:** Run morphology query tests touching dictionary joins; fix only if Slice 2 behavior change surfaced.

### Task 15: CONTEXT glossary update

**Files:**
- Modify: `CONTEXT.md`

- [ ] **Step 1:** Add glossary entries (domain language only):
  - **normalized title join index:** in-memory maps used to match morphology lemma titles to dictionary entries at join time
  - **resolve_one / resolve_all:** singleton vs multi-entry join policies for the same tier order
- [ ] **Step 2:** Do not document file paths or SQL details in `CONTEXT.md`.

### Task 16: Slice 2 quality gate

**Files:**
- Touched Python from Slice 2

- [ ] **Step 1:** `ruff check` on touched files
- [ ] **Step 2:** `.venv/bin/mypy` on touched files
- [ ] **Step 3:** `make napoleon-gate`
- [ ] **Step 4:** `pytest tests/dictionary/test_normalized_title_join.py tests/dictionary/test_query_service.py tests/lexicon/test_build.py tests/morphology/test_query_service.py -q`
- [ ] **Step 5:** Commit Slice 2 with message focused on shared normalized title join index

---

## Verification Checklist (both slices)

- [x] No `sqlite3.connect` in `wyrdcraeft/services/lexicon/build.py` after Slice 1
- [x] No TEMP staging tables in lexicon rebuild after Slice 1
- [x] Alembic owns lexicon DDL; rebuild truncates only (no `create_lexicon_tables`)
- [x] `SCHEMA_VERSION` removed from staleness
- [ ] `_select_entry_id` absent after Slice 2
- [ ] `_resolve_entry_ids_by_normalized_title` absent after Slice 2
- [ ] Lexicon browse search still uses `normalize_old_english` only (no behavior change)
- [ ] Form↔entry linking still uses macron-preserving `normalized_title` at build time
- [ ] Cooperative cancel still interrupts long-running rebuild loops

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| 30-minute rebuild slows after dropping TEMP SQL | Keep batch sizes; compare row counts + wall time on representative DB before/after Slice 1 |
| SQLAlchemy cancel wiring differs by version | Add one test that cancel stops a long loop using runtime controller |
| `INSERT OR IGNORE` dedupe behavior changes for search keys | Assert dedupe counts in existing lexicon build tests |
| Join semantics change when lexicon variants become POS-filtered | Explicit tests in Slice 2; intended fix per design review |

---

## References

- `CONTEXT.md` — `normalized_title`, lexicon browse search normalization, canonical DB terms
- `docs/superpowers/plans/2026-06-30-wyrdcraeft-canonical-db-migration.md` — prior migration phases
- Commit `c651f32` — introduced `normalized_title` columns and join simplification
- `wyrdcraeft/services/morphology/generation/sinks.py` — reference Core bulk insert pattern
