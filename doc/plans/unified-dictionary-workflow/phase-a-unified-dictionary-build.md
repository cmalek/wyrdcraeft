# Phase A — Unified Dictionary Build

> **Prerequisites:** Alembic head at `20260706_04`; read
> [README.md](./README.md) locked decisions  
> **REQUIRED SUB-SKILL:** subagent-driven-development  
> **Next phase:** [phase-b-dictionary-browse-and-cli.md](./phase-b-dictionary-browse-and-cli.md)

**Goal:** Make `wyrdcraeft dictionary build` the single canonical database build command:
bootstrap schema, rebuild Bosworth-Toller tables, relink `forms.entry_id`, optionally
regenerate morphology forms, run POS inference.

**Architecture:** Extract a cohesive `DictionaryBuildPipeline` class that orchestrates
existing `BTIndexPipeline` + morphology generation dispatch + shared
`FormsEntryRelinker`. Remove `morphology build` and `lexicon build` CLI entrypoints.
Phase A **does not** drop `search_keys` or change browse search (Phase B).

**Out of scope:** Browse search rewrite, `search_keys` migration, CLI group renames
(`lookup`→`query`, `lexicon browse`→`dictionary browse`) — Phase B.

---

## Acceptance criteria (phase)

- [ ] `dictionary build` on empty app-data dir creates canonical DB via Alembic and rebuilds `bt_*`
- [ ] `dictionary build` on DB with existing `forms` rebuilds `bt_*` and **relinks all** `forms.entry_id` without `--with-morphology`
- [ ] `dictionary build --with-morphology` truncates `forms` and runs full morphology generation when `forms` was non-empty
- [ ] `dictionary build` on DB with **empty** `forms` auto-runs morphology generation (no flag)
- [ ] POS inference runs at end of `dictionary build` when `forms` has rows
- [ ] Morphology-only flags (`--limit`, `--full`, `--data-dir`, `--profile`, `--refresh-catalog`, etc.) apply only when morphology stage runs
- [ ] `wyrdcraeft morphology build` command removed
- [ ] `wyrdcraeft lexicon build` command removed
- [ ] No new writes to `search_keys` required for product flows (lexicon build code may remain until Phase B deletion)

---

## Task 1: `FormsEntryRelinker` service

**Files:**
- Create: `wyrdcraeft/services/dictionary/forms_entry_relinker.py`
- Test: `tests/dictionary/test_forms_entry_relinker.py`

**Behavior:**
- Class `FormsEntryRelinker` with constructor taking SQLAlchemy `Connection` or `Engine`
- Preload `NormalizedTitleJoinIndex` from current `bt_entries` + `bt_variants` (reuse
  `FormFkResolver._load_join_index` pattern or extract shared loader to avoid duplication)
- `clear_all_entry_ids()` → `UPDATE forms SET entry_id = NULL`
- `relink_all(*, batch_size: int = 25000, progress callback optional)`:
  - Read `forms.id`, `forms.normalized_title`, `wordclass_id` → resolve wordclass code via join
  - Call same join policy as `FormFkResolver.resolve_entry_id(normalized_title, wordclass)`
  - Batch `UPDATE forms SET entry_id = :entry_id WHERE id = :id`
  - Set `entry_id` NULL when join ambiguous or no match
- Document in class docstring: must run after every `bt_entries` wipe/reload because PK ids change

**Tests:**
- Empty forms → no-op relink, zero updates
- Single form + single matching `bt_entries` row → `entry_id` set
- Homograph ambiguous join → `entry_id` NULL
- Dictionary entry removed on rebuild → relink clears stale id (simulate delete + re-insert with new id)

---

## Task 2: `DictionaryBuildPipeline` orchestrator

**Files:**
- Create: `wyrdcraeft/services/dictionary/build_pipeline.py`
- Create: `wyrdcraeft/models/dictionary_build.py` (stages/events if needed; may adapt lexicon_build stage enums)
- Test: `tests/dictionary/test_build_pipeline.py`

**Pipeline stages (ordered):**

1. **`ensure_schema`** — call `upgrade_canonical_db(db_path)`; fail clearly on migration error
2. **`rebuild_dictionary`** — existing `BTIndexPipeline` + `BTSqliteSink`
   - Before delete: `FormsEntryRelinker.clear_all_entry_ids()` to avoid FK violations
3. **`relink_forms`** — `FormsEntryRelinker.relink_all()` always
4. **`maybe_rebuild_morphology`** — run when `forms` count == 0 OR `with_morphology=True`:
   - `DELETE FROM forms` (truncate)
   - Run morphology generation (extract body from `wyrdcraeft/cli/morphology.py` `build` command into callable `run_morphology_generation(...)` in e.g. `wyrdcraeft/services/morphology/build_runner.py`)
   - New form rows get `entry_id` from sink `FormFkResolver` at insert time
   - Skip when `forms` non-empty and not `with_morphology`
5. **`infer_pos`** — move logic from `LexiconBuilder._infer_missing_pos` into pipeline or shared helper; run when `forms` count > 0

**Public API:**

```python
@dataclass(frozen=True)
class DictionaryBuildReport:
    built_at: str
    bt_entries_written: int
    forms_source_count: int
    forms_regenerated: bool
    entry_ids_linked: int
    entry_ids_cleared: int
    pos_inferred: int

class DictionaryBuildPipeline:
    def __init__(self, db_path: Path, *, progress=..., event_sink=..., cancel_event=...) -> None: ...
    def run(self, *, source: Path, with_morphology: bool, morph_options: MorphBuildOptions) -> DictionaryBuildReport: ...
```

**`MorphBuildOptions`:** dataclass holding `--limit`, `--full`, `--data-dir`, `--profile`, `--refresh-catalog`, morphology input path overrides.

---

## Task 3: Dictionary CLI integration

**Files:**
- Modify: `wyrdcraeft/cli/dictionary.py`
- Modify: `tests/test_cli_dictionary.py`

**Changes:**
- Remove `_require_non_empty_tables(..., ("forms",))` guard on `build`
- Remove `_missing_canonical_index_message` reference to morphology build; point to `dictionary build` / startup readiness
- Replace inline `BTIndexPipeline` wiring with `DictionaryBuildPipeline.run(...)`
- Add `--with-morphology` flag (bool, default False)
- Add morphology flags migrated from deleted morph build command:
  `--data-dir`, `--dictionary` (morph lemma list file), `--manual-forms`, `--verbal-paradigms`,
  `--prefixes`, `--output` (TSV), `--limit`, `--progress-every`, `--enable-r-stem-nouns`,
  `--full/--no-full`, `--profile`, `--refresh-catalog`
- When morphology stage skipped, ignore morph flags (no error)
- Emit summary lines: `bt_entries_written`, `forms_regenerated`, `entry_ids_linked`, `pos_inferred`

**Tests:**
- `dictionary build` on temp empty dir (with `isolated_morphology_app_data`) succeeds
- With seeded empty `forms` table post-Alembic → morphology stage runs
- With seeded non-empty `forms` → morphology skipped unless `--with-morphology`
- Relink updates `entry_id` after dictionary rebuild (use small fixture DB)

---

## Task 4: Remove `morphology build` and `lexicon build`

**Files:**
- Modify: `wyrdcraeft/cli/morphology.py` — delete `build` command and helpers only used by it; keep `query`, `ingest-wright-text`, `audit-wright`, etc.
- Delete or gut: `wyrdcraeft/cli/lexicon.py` — remove `build` command (Phase B removes entire file when browse moves)
- Modify: `wyrdcraeft/cli/cli.py` — keep groups as-is for Phase A (lexicon group may still expose browse until Phase B)
- Modify: `tests/test_cli_lexicon.py` — remove build tests (or mark deleted)
- Modify: `tests/test_cli_morphology.py` — remove build smoke tests; add note that build moved to dictionary

**Do not delete yet:** `wyrdcraeft/services/lexicon/build.py`, search_keys schema — Phase B removes after browse rewrite.

**User-facing errors:** Any remaining references to `morphology build` or `lexicon build` in error strings updated to `dictionary build`.

---

## Task 5: Wire `FormFkResolver` to shared join loader

**Files:**
- Modify: `wyrdcraeft/services/morphology/generation/form_fk_resolver.py`
- Modify: `wyrdcraeft/services/dictionary/forms_entry_relinker.py` (if loader extracted)

Extract `_load_join_index` to shared module (e.g. `wyrdcraeft/services/dictionary/join_index_loader.py`) used by both `FormFkResolver` and `FormsEntryRelinker`. No behavior change — refactor only.

---

## Task 6: Phase A docs (minimal)

**Files:**
- Modify: `CONTEXT.md` — update glossary entries for lexicon build, dictionary build scope, entry_id relink
- Modify: `doc/source/overview/command_lexicon_build.rst` — add deprecation banner pointing to Phase B removal OR stub "superseded by dictionary build" note

Full CLI doc renames deferred to Phase B.

---

## Phase A validation

```bash
.venv/bin/ruff check wyrdcraeft/services/dictionary wyrdcraeft/cli/dictionary.py wyrdcraeft/cli/morphology.py
.venv/bin/mypy wyrdcraeft/services/dictionary/build_pipeline.py wyrdcraeft/services/dictionary/forms_entry_relinker.py
make napoleon-gate
.venv/bin/pytest tests/dictionary/test_forms_entry_relinker.py tests/dictionary/test_build_pipeline.py tests/test_cli_dictionary.py -q
```

Manual smoke (isolated app-data):

```bash
export WYRDCRAEFT_APP_DATA_DIR=/tmp/wc-unified-a
rm -rf "$WYRDCRAEFT_APP_DATA_DIR"
.venv/bin/wyrdcraeft dictionary build --source data/oe_bt.txt --no-tui 2>/dev/null || \
  .venv/bin/wyrdcraeft dictionary build --source tests/fixtures/dictionary/sample_lines.txt
sqlite3 "$WYRDCRAEFT_APP_DATA_DIR/wyrdcraeft.sqlite3" "SELECT COUNT(*) FROM bt_entries;"
# Optional long run:
# .venv/bin/wyrdcraeft dictionary build --with-morphology --limit 50 ...
```

---

## Phase A — Gate A checklist

- [ ] `FormsEntryRelinker` exists and matches relink semantics
- [ ] Dictionary rebuild clears `entry_id` before `bt_entries` delete
- [ ] Relink always runs after dictionary rebuild
- [ ] `--with-morphology` and empty-`forms` auto-morph behavior correct
- [ ] POS inference on `dictionary build` tail only
- [ ] `morphology build` and `lexicon build` CLI commands gone
- [ ] `search_keys` unchanged (Phase B)

---

## Phase A — Gate B checklist

- [ ] Tests use `isolated_morphology_app_data` for DB writes
- [ ] No FK violation path on dictionary rebuild with populated `forms.entry_id`
- [ ] Napoleon gate clean on touched files
- [ ] No duplicate join-index loader logic left unshared

---

## Phase A commit message

```bash
git add <phase-a files>
git commit -m "$(cat <<'EOF'
Unified dictionary build: relink forms.entry_id and optional morphology regen.

Add DictionaryBuildPipeline with FormsEntryRelinker; dictionary build always
rebuilds bt_* and relinks entry_id; --with-morphology or empty forms triggers
morph regen; POS inference moves here. Remove morphology build and lexicon build
CLI commands.
EOF
)"
git status
```
