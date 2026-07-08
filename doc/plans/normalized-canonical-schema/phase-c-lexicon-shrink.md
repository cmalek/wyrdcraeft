# Phase C — Lexicon Shrink (Search Index Only)

> **Prerequisites:** Phase B gates passed and committed  
> **REQUIRED SUB-SKILL:** subagent-driven-development  
> **Next phase:** [phase-d-legacy-column-drop.md](./phase-d-legacy-column-drop.md)

**Goal:** Drop `lexicon_entries` and `lexicon_forms`; rename search tables to
`search_keys` and `search_build_meta`; rewrite lexicon build and browse to read
`bt_*` and `forms` directly.

**Architecture:** `rebuild_lexicon()` becomes search-index rebuild only — emit keys from
source tables using existing rank tiers. `LexiconQueryService` joins `search_keys` to
`bt_entries` / `forms` / `parts_of_speech` at query time.

**Out of scope:** Dropping legacy `forms` string columns (Phase D).

---

## Task 1: Schema constants + migration `20260706_03`

**Files:**
- Modify: `wyrdcraeft/services/lexicon/schema.py`
- Create: `wyrdcraeft/db/alembic/versions/20260706_03_lexicon_shrink_search_keys.py`
- Modify: `wyrdcraeft/models/sqlalchemy.py` (rename models)

- [ ] Constants:
  - `TABLE_SEARCH_KEYS = "search_keys"` (was `lexicon_search_keys`)
  - `TABLE_SEARCH_BUILD_META = "search_build_meta"`
  - `SEARCH_TABLE_NAMES` = `(search_keys, search_build_meta)` only
  - Deprecate/remove `TABLE_LEXICON_ENTRIES`, `TABLE_LEXICON_FORMS` constants
- [ ] Migration:
  - `ALTER TABLE lexicon_search_keys RENAME TO search_keys`
  - `ALTER TABLE lexicon_build_meta RENAME TO search_build_meta`
  - Rename indexes to match (`idx_search_keys_*`)
  - `DROP TABLE lexicon_forms`
  - `DROP TABLE lexicon_entries`
- [ ] ORM: rename `LexiconSearchKey` → `SearchKey`, `LexiconBuildMeta` → `SearchBuildMeta`
  (or keep class names with new `__tablename__` — pick one pattern, apply consistently)
- [ ] Update FK targets on `search_keys`: `entry_id` → `bt_entries.id`, `form_id` → `forms.id`
  (may already be logical; enforce in migration if needed)

---

## Task 2: Lexicon build — search keys only

**Files:**
- Modify: `wyrdcraeft/services/lexicon/build.py`
- Modify: `wyrdcraeft/models/lexicon_build.py` (stage names / counters if needed)
- Test: `tests/lexicon/test_build.py`

- [ ] Remove stages that insert into `lexicon_entries` / `lexicon_forms`
- [ ] Truncate only `search_keys` + `search_build_meta`
- [ ] Emit search keys from:
  - `bt_entries` + `bt_variants` (lemma/variant tiers)
  - `forms` (stem/form tiers) using `forms.entry_id` when set, else orphan tier
- [ ] POS inference: if still needed, update `bt_entries.pos_id` in place (not lexicon projection)
- [ ] `LexiconBuildResult`: drop `entries_written` / `forms_written`; keep key counts + timing
- [ ] Staleness check unchanged (`forms`, `bt_entries` row counts)
- [ ] Update build monitor stage labels ("search index" not "lexicon entries")

---

## Task 3: Lexicon query — source table joins

**Files:**
- Modify: `wyrdcraeft/services/lexicon/query.py`
- Test: `tests/lexicon/test_query_service.py`, `tests/lexicon/test_morph_class_browse.py`

- [ ] Replace `LEFT JOIN lexicon_entries` → `LEFT JOIN bt_entries` (+ `bt_senses` for details)
- [ ] Replace `LEFT JOIN lexicon_forms` → `LEFT JOIN forms` (+ `parts_of_speech`, `inflection_codes`)
- [ ] Entry details: load senses/variants from normalized `bt_*` tables (not `senses_json`)
- [ ] Morphology sidebar: read `forms` filtered by `wordclass_id` matching entry POS
- [ ] Form decode: use `inflection_codes.code` or legacy `function` during transition
- [ ] Search ranking unchanged (rank_tier, key_kind, lexical distance)

---

## Task 4: Lexicon TUI + CLI

**Files:**
- Modify: `wyrdcraeft/services/lexicon/tui.py`
- Modify: `wyrdcraeft/cli/lexicon.py` (help text only)
- Test: `tests/lexicon/test_browse.py` if present

- [ ] Remove raw SQL referencing `lexicon_entries` (e.g. entry counts → `bt_entries`)
- [ ] Help text: `lexicon build` rebuilds **search index** from dictionary + morphology
- [ ] Browse behavior unchanged from user perspective

---

## Task 5: Test fixture updates

**Files:**
- Modify: `tests/lexicon/conftest.py`
- Modify: `tests/lexicon/test_schema.py`
- Modify: `tests/lexicon/test_morph_class_browse.py`
- Modify: `tests/lexicon/test_query_service.py`

- [ ] Fixtures seed `bt_*` + `forms` instead of `lexicon_entries` / `lexicon_forms`
- [ ] `test_schema.py`: expect `search_keys`, not `lexicon_*` data tables
- [ ] All lexicon tests green without projection tables

---

## Task 6: Docs

**Files:**
- Modify: `CONTEXT.md` (glossary: search index, update lexicon read model definition)
- Modify: `doc/source/architecture/index.rst` (remove LEXICON_ENTRIES/FORMS; rename search tables)
- Modify: `docs/context/` lexicon doc if present

- [ ] Document that `lexicon build` scope is search index only

---

## Phase C validation

```bash
.venv/bin/ruff check wyrdcraeft/services/lexicon/build.py wyrdcraeft/services/lexicon/query.py wyrdcraeft/services/lexicon/schema.py wyrdcraeft/models/sqlalchemy.py
.venv/bin/mypy wyrdcraeft/services/lexicon/build.py wyrdcraeft/services/lexicon/query.py wyrdcraeft/services/lexicon/schema.py wyrdcraeft/models/sqlalchemy.py
make napoleon-gate
.venv/bin/pytest tests/lexicon -q
.venv/bin/pytest tests/morphology/test_query_service.py -q
```

Manual:

```bash
WYRDCRAEFT_APP_DATA_DIR=/tmp/wc-phase-c .venv/bin/wyrdcraeft lexicon build --no-tui
sqlite3 /tmp/wc-phase-c/wyrdcraeft.sqlite3 \
  "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%lexicon%' OR name LIKE 'search%';"
WYRDCRAEFT_APP_DATA_DIR=/tmp/wc-phase-c .venv/bin/wyrdcraeft lexicon browse --no-tui
# smoke: search abbod, open entry, morphology pane
```

---

## Phase C — Gate A: Spec review checklist

- [ ] `lexicon_entries` and `lexicon_forms` dropped
- [ ] `search_keys` + `search_build_meta` renamed and used everywhere
- [ ] `lexicon build` does not recreate projection tables
- [ ] Browse reads `bt_*` + `forms` directly
- [ ] Legacy `forms` string columns still present
- [ ] CLI command name still `wyrdcraeft lexicon build`

---

## Phase C — Gate B: Code review checklist

- [ ] No dangling references to `lexicon_entries` / `lexicon_forms` in product code or tests
- [ ] Search key dedupe index preserved
- [ ] Orphan tier still works for forms without `entry_id`
- [ ] Lexicon tests green

---

## Phase C — Commit

```bash
git commit -m "$(cat <<'EOF'
Normalize schema phase C: shrink lexicon to search index only.

Drop lexicon projection tables, rename search_keys, and read dictionary
and morphology source tables directly in browse and query paths.
EOF
)"
```
