# Session State: Lexicon SQLAlchemy Slice 1 Complete

**Date:** 2026-07-03  
**Branch:** `codex/canonical-db-migration`  
**Slice 1 commit:** `64c6223` — *Migrate lexicon rebuild to SQLAlchemy Core with Alembic-owned DDL.*  
**Parent plan:** `docs/superpowers/plans/2026-07-03-lexicon-sqlalchemy-normalized-title-join.md`

---

## Where we are

| Slice | Status | Commit |
|-------|--------|--------|
| **Slice 1** — Lexicon rebuild → SQLAlchemy Core | **Done** | `64c6223` |
| **Slice 2** — `NormalizedTitleJoinIndex` + wiring | **Not started** | — |

**Next action when resuming:** Implement Slice 2 (Tasks 11–16) with subagent-driven development; review after phase.

---

## Slice 1 deliverables (shipped)

- Lexicon rebuild uses **SQLAlchemy Core only** (`engine.begin()`, batched `insert`/`delete`/`select`/`update`).
- **No `sqlite3.connect()`** in rebuild path; **no TEMP staging tables**.
- **`lexicon build` truncates** (`DELETE FROM lexicon_*`) — does not drop/recreate tables.
- **`create_lexicon_tables()` removed** — lexicon DDL is **Alembic-only** (initial schema in `20260630_01`, migrations at startup).
- **`upgrade_canonical_db()`** added to `wyrdcraeft/db/runtime.py` for tests and programmatic Alembic upgrade.
- Rebuild **requires Alembic-managed lexicon tables**; clear error if missing.
- **`SCHEMA_VERSION` removed** from staleness, build metadata, `BuildReport`, `LexiconBuildMeta`.
- Module helpers accept `Engine | Connection | Path` via `DbTarget`.
- **`_select_entry_id` kept unchanged** (Slice 2 extracts join index).
- Tests/fixtures use `upgrade_canonical_db()` instead of `create_lexicon_tables()`.
- **36/36** lexicon tests pass (`test_build.py`, `test_schema.py`).

---

## Locked decisions (human, this session)

### Alembic owns lexicon DDL

- App upgrade → Alembic `upgrade head` (seconds).
- **Additive DDL:** OK to backfill in migration; do not force full lexicon rebuild.
- **Goal:** Users should **rarely** need `lexicon build` for schema changes.
- **`SCHEMA_VERSION` staleness:** **Removed** — DDL truth is `alembic_version`, not lexicon build meta.

### When `lexicon build` is still required

- First build (no read-model metadata / empty lexicon tables).
- Source data drift: `forms` or `bt_entries` row counts changed since last build.
- Future read-model **logic** changes (not covered by Alembic backfill) — no separate version constant yet.

### Rebuild semantics

- Truncate rows in place; preserve table DDL from Alembic.

### Slice 2 (unchanged from plan)

- `NormalizedTitleJoinIndex` with `resolve_one` / `resolve_all`.
- Wire `BTQueryService` + lexicon form stream; delete `_select_entry_id` and `_resolve_entry_ids_by_normalized_title`.
- Update `CONTEXT.md` glossary (domain language only).

---

## Code review notes (Slice 1, not blocking commit)

Spec and quality reviews flagged **non-blockers** for follow-up (optional before or during Slice 2):

1. **Memory:** forms `fetchall()` + in-memory search keys vs old TEMP streaming — monitor at full corpus scale.
2. **Cancel gap:** `_insert_search_keys` batch loop lacks `_check_cancel`.
3. **Rollback test:** cancel test on empty DB is weak; should pre-populate lexicon then cancel mid-rebuild.
4. **Staleness tests:** only `forms` count drift covered; not `bt_entries` or missing-meta edge cases.
5. **Minor:** stale log names (“staging”), duplicated connect helpers, `query.py` docstring still says `morphology.sqlite3`.

---

## Files changed in Slice 1 commit

```
wyrdcraeft/services/lexicon/build.py
wyrdcraeft/services/lexicon/schema.py
wyrdcraeft/services/lexicon/__init__.py
wyrdcraeft/db/runtime.py
wyrdcraeft/cli/lexicon.py
tests/lexicon/conftest.py
tests/lexicon/source_db.py
tests/lexicon/test_build.py
tests/lexicon/test_schema.py
```

**Uncommitted (intentionally excluded):** `.aidex/index.db`

---

## Verification checklist

| Item | Slice 1 |
|------|---------|
| No `sqlite3.connect` in `build.py` rebuild | ✅ |
| No TEMP staging tables | ✅ |
| Cooperative cancel wired | ✅ |
| `_select_entry_id` still present | ✅ (Slice 2) |
| `_resolve_entry_ids_by_normalized_title` absent | — (Slice 2) |
| Lexicon browse uses `normalize_old_english` only | ✅ (unchanged) |
| Alembic owns lexicon DDL; rebuild truncates only | ✅ |

---

## Workflow

- Execution model: **subagent-driven development** — implement per slice, **review after each phase**.
- Slice 1 committed; **paused** for human context summary before Slice 2.

---

## References

- Plan: `docs/superpowers/plans/2026-07-03-lexicon-sqlalchemy-normalized-title-join.md`
- Prior normalized_title work: `c651f32`
- Morphology Core bulk insert pattern: `wyrdcraeft/services/morphology/generation/sinks.py`
- Alembic initial lexicon tables: `wyrdcraeft/db/alembic/versions/20260630_01_initial_canonical_schema.py`
