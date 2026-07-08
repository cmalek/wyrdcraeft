# Phase B — Dictionary Browse, Search, and CLI Consolidation

> **Prerequisites:** Phase A gates passed and committed  
> **REQUIRED SUB-SKILL:** subagent-driven-development  
> **Prior phase:** [phase-a-unified-dictionary-build.md](./phase-a-unified-dictionary-build.md)

**Goal:** Drop `search_keys`, implement query-time dictionary browse search with
variant-aware 12-tier ranking, move browse to `dictionary browse`, consolidate CLI groups,
remove lexicon workflow surface.

**Architecture:** Replace `LexiconQueryService.search()` with
`DictionaryBrowseQueryService` querying `bt_entries` + `bt_variants` directly. Move TUI
from `wyrdcraeft/services/lexicon/tui.py` to dictionary package (or rename module).
Alembic migration drops search-index tables. Delete lexicon build/query infrastructure.

---

## Acceptance criteria (phase)

- [ ] Alembic migration drops `search_keys` and `search_build_meta`
- [ ] `dictionary browse` opens Textual UI (formerly `lexicon browse`)
- [ ] Browse search returns dictionary entries only; **no orphan section**
- [ ] Search ranking implements 12-tier headword + variant ladder (below)
- [ ] `dictionary query` replaces `dictionary lookup` (alias deprecated one release or remove outright in same phase)
- [ ] `dictionary ingest-wright-text` and `dictionary audit-wright` work (moved from morphology)
- [ ] `morphology` group retains **`query` only**
- [ ] `lexicon` CLI group removed
- [ ] Deleted: `wyrdcraeft/services/lexicon/build.py`, `build_monitor.py`, `build_runtime.py`, `schema.py` search constants, `models/lexicon_build.py` if unused
- [ ] CONTEXT.md and architecture docs updated

---

## Browse search rank ladder (locked)

Lower `rank_tier` = higher priority. Within tier: lexical distance, then headword sort.

| Tier | Match |
|------|--------|
| 1 | Exact headword (`bt_entries.headword`) |
| 2 | Exact variant (`bt_variants.spelling_macronized`) |
| 3 | Headword `normalized_title` |
| 4 | Variant `normalized_title` |
| 5 | Headword `norm_key` (diacritic-stripped) |
| 6 | Variant norm key (normalize variant spelling same as builder) |
| 7 | Headword prefix/suffix on display headword |
| 8 | Variant prefix/suffix on display spelling |
| 9 | Headword prefix/suffix on `normalized_title` |
| 10 | Variant prefix/suffix on `normalized_title` |
| 11 | Headword prefix/suffix on `norm_key` |
| 12 | Variant prefix/suffix on variant norm key |

**Query normalization:** reuse `BTSpellingNormalizer`, `normalize_old_english`,
`normalize_morphology_title` consistently with dictionary indexing.

**Dedup:** one hit per `(entry_id, pos_id)` keeping best (lowest) tier.

**Affix match:** case/diacritic-insensitive via `normalized_query_at_affix` logic from
`form_decode.py` (move to shared search util if needed).

---

## Task 1: Alembic migration — drop search index tables

**Files:**
- Create: `wyrdcraeft/db/alembic/versions/20260707_01_drop_search_keys.py`
- Modify: `wyrdcraeft/models/sqlalchemy.py` — remove `SearchKey`, `SearchBuildMeta` models
- Modify: `tests/lexicon/test_schema.py` — remove search_keys expectations (or relocate test file)

**Migration:**
- `DROP TABLE search_keys`
- `DROP TABLE search_build_meta`
- Downgrade recreates empty tables (copy shape from `20260706_03` for reversibility)

---

## Task 2: `DictionaryBrowseQueryService`

**Files:**
- Create: `wyrdcraeft/services/dictionary/browse_query.py`
- Test: `tests/dictionary/test_browse_query.py` (port cases from `tests/lexicon/test_query_service.py`)

**API:**

```python
@dataclass(frozen=True)
class BrowseSearchHit:
    entry_id: int
    headword: str
    pos: str
    summary_sense: str
    rank_tier: int
    matched_text: str  # headword or variant spelling that matched

class DictionaryBrowseQueryService:
    def search(self, query: str) -> list[BrowseSearchHit]: ...
    def get_details(self, entry_id: int) -> EntryDetails | None: ...  # port from LexiconQueryService
```

- Port `get_details`, `_load_entry_senses`, morph-class lookup, morphology sidebar grouping from `wyrdcraeft/services/lexicon/query.py`
- **Remove** `SearchResults.orphans`, `OrphanHit`, `get_orphan_details`
- SQL: single query or UNION across headword + variant candidate sets with computed `rank_tier`; filter affix tiers in SQL or Python post-filter mirroring current `_hit_matches_query_intent` behavior
- Subquery for `summary_sense`: first `bt_senses.gloss_en` by `order_index`

**Tests to port/adapt:**
- Exact headword hit
- Variant spelling hit (`ABBOD` / macron variants)
- Undiacritized query matches macron headword
- Dedup homograph entries by `(norm_key, pos)`
- Affix search (`mōd` matches `acol-mōd` entry via suffix tier)
- Tier ordering: exact headword beats variant exact beats normalized

---

## Task 3: Browse TUI move + orphan removal

**Files:**
- Move: `wyrdcraeft/services/lexicon/tui.py` → `wyrdcraeft/services/dictionary/browse_tui.py` (or keep path, update imports — prefer dictionary package)
- Move: `wyrdcraeft/services/lexicon/form_decode.py` → shared location if used by browse + morphology (`wyrdcraeft/services/dictionary/form_decode.py` or `wyrdcraeft/services/search/form_decode.py`)
- Modify: remove orphan results pane, orphan selection handlers, orphan CSS/layout
- Modify: `DictionaryBrowseQueryService` wiring
- Test: `tests/dictionary/test_browse_tui.py` (port from `tests/lexicon/test_tui.py`; drop orphan tests)

---

## Task 4: CLI consolidation

**Files:**
- Modify: `wyrdcraeft/cli/dictionary.py` — add `browse` command (from lexicon.py browse)
- Modify: `wyrdcraeft/cli/dictionary.py` — rename `lookup` → `query`; remove `lookup` or keep hidden alias with deprecation warning
- Modify: `wyrdcraeft/cli/morphology.py` — move `ingest-wright-text`, `audit-wright` to dictionary.py
- Delete: `wyrdcraeft/cli/lexicon.py`
- Modify: `wyrdcraeft/cli/cli.py` — remove `lexicon_group` registration
- Modify: `tests/test_cli_lexicon.py` → migrate browse tests to `tests/test_cli_dictionary.py`
- Modify: `tests/test_cli_morphology.py` — update paths for moved commands

**Browse prerequisites:** populated `bt_entries`; no search_keys check. Staleness messaging removed or simplified to "run dictionary build".

---

## Task 5: Delete lexicon build / search-index code

**Files:**
- Delete: `wyrdcraeft/services/lexicon/build.py`
- Delete: `wyrdcraeft/services/lexicon/build_monitor.py`
- Delete: `wyrdcraeft/services/lexicon/build_runtime.py`
- Delete: `wyrdcraeft/services/lexicon/progress.py` (if only used by lexicon build)
- Delete: `wyrdcraeft/services/lexicon/schema.py`
- Delete: `wyrdcraeft/services/lexicon/query.py` (replaced by browse_query)
- Delete: `wyrdcraeft/models/lexicon_build.py`
- Delete: `tests/lexicon/test_build.py`, `test_build_runtime.py`, `test_progress.py`, `test_query_service.py`
- Modify: `wyrdcraeft/services/lexicon/__init__.py` — remove or delete package if empty

Keep `form_decode` if moved; delete empty `lexicon` package when nothing remains.

---

## Task 6: Documentation

**Files:**
- Modify: `CONTEXT.md` — remove search_keys / lexicon read model / lexicon build glossary; add unified dictionary build + browse search
- Modify: `doc/source/architecture/lexicon.rst` → update or merge into dictionary architecture
- Modify: `doc/source/architecture/index.rst` — ER diagram without search_keys
- Modify: `doc/source/overview/command_lexicon_build.rst` — remove or redirect
- Modify: `doc/source/overview/command_lexicon_browse.rst` → `command_dictionary_browse.rst`
- Modify: `doc/source/overview/using_cli.rst`
- Modify: `README.md` if it references lexicon build/browse

---

## Phase B validation

```bash
.venv/bin/ruff check wyrdcraeft/services/dictionary wyrdcraeft/cli wyrdcraeft/models/sqlalchemy.py
.venv/bin/mypy wyrdcraeft/services/dictionary/browse_query.py wyrdcraeft/services/dictionary/browse_tui.py
make napoleon-gate
.venv/bin/pytest tests/dictionary tests/test_cli_dictionary.py -q
# After test file migration:
.venv/bin/pytest tests/lexicon/test_morph_class_browse.py -q  # update imports/paths first
```

Manual:

```bash
export WYRDCRAEFT_APP_DATA_DIR=/tmp/wc-unified-b
.venv/bin/wyrdcraeft dictionary build --source tests/fixtures/dictionary/sample_lines.txt
.venv/bin/wyrdcraeft dictionary browse --no-tui
# smoke: search headword, variant spelling, undiacritized query; confirm no orphan pane
sqlite3 "$WYRDCRAEFT_APP_DATA_DIR/wyrdcraeft.sqlite3" "SELECT name FROM sqlite_master WHERE name LIKE 'search%';"
# expect empty
```

---

## Phase B — Gate A checklist

- [ ] `search_keys` / `search_build_meta` dropped in migration and code
- [ ] 12-tier search ranking with variants
- [ ] No orphan section in browse
- [ ] `dictionary browse`, `dictionary query` CLI names
- [ ] `morphology query` only under morphology
- [ ] `lexicon` group removed
- [ ] Docs match locked decisions

---

## Phase B — Gate B checklist

- [ ] Browse tests cover variant + affix tiers
- [ ] No dangling imports of deleted lexicon build modules
- [ ] Napoleon gate clean
- [ ] Migration downgrade recreates search tables

---

## Phase B commit message

```bash
git add <phase-b files>
git commit -m "$(cat <<'EOF'
Dictionary browse: drop search_keys and query bt_* directly.

Remove search index tables; implement variant-aware 12-tier browse search;
move browse to dictionary browse; rename lookup to dictionary query; consolidate
Wright commands under dictionary; keep morphology query only; delete lexicon CLI
and build infrastructure.
EOF
)"
git status
```
