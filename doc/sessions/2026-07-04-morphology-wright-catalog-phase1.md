# Morphology Wright catalog — Phase 1 session (2026-07-04)

Handoff note for continuing subagent-driven implementation of the Wright morph
reference catalog. Safe to feed to summarize / next agent.

## Branch and commits

- **Branch:** `codex/canonical-db-migration`
- **Base context:** Prior work on morphology build performance (see
  `doc/sessions/2026-07-03-morphology-build-performance.md`)

### Commits this session (Phase 1 Tasks 1–4)

| SHA | Message |
|-----|---------|
| `6249788` | feat(db): add morph catalog reference tables |
| `48a9c23` | feat(models): add morph catalog SQLAlchemy models |
| `784db30` | feat(morphology): add Wright catalog fixture loader |
| `7a9223a` | fix(morphology): match catalog loader upsert order to spec |
| `8720f46` | feat(morphology): auto-seed Wright catalog on build |
| `8cb7b89` | fix(morphology): harden catalog seed errors and test skip/refresh |

## Goal (locked design)

Replace ad-hoc Wright/paradigm strings with a normalized morphology reference
catalog seeded from `wyrdcraeft/etc/morphology/wright_paradigms.json`.

**Plan docs (untracked):** `doc/plans/morphology-wright-catalog/`

- `README.md` — orchestration, gates, validation commands
- `00-design-decisions.md` — grilling outcomes (do not re-litigate)
- `phase-1-reference-catalog.md` through `phase-4-*.md`

## Phase 1 progress

| Task | Status | Notes |
|------|--------|-------|
| 1. Alembic migration | ✅ Done | `20260704_01_morph_catalog_tables.py` |
| 2. SQLAlchemy models | ✅ Done | `wyrdcraeft/models/morph_catalog.py` |
| 3. Fixture loader | ✅ Done | `MorphologyCatalogLoader` + tests |
| 4. Build integration | ✅ Done | `--refresh-catalog`, auto-seed on build |
| 5. Schema validation test | ⏳ Pending | Fixture count/POS structural test |
| Gate A (spec review) | ⏳ Pending | After Task 5 |
| Gate B (code review / bugbot) | ⏳ Pending | After Task 5 |

**Do not start Phase 2 (lemma assignment)** until Phase 1 gates pass.

## Schema delivered (Phase 1)

Tables (integer PKs except `wright_sections.section_no`):

- `morph_sources` — bibliographic sources
- `morph_classes` — `class_key` unique slug (e.g. `noun.masculine.a_stem`), not PK
- `wright_sections` — `section_no` PK, `section_text` NULL until Phase 4
- `morph_class_wright_sections` — junction + `sort_order`
- `morph_class_sources` — junction

**Explicitly out of Phase 1 scope:** `parent_id`, `recognition_hints_json`,
`lemma_morph_classes`, `BTEntryMorphClass`, `forms.morph_class_id`.

## Key files

| Path | Role |
|------|------|
| `wyrdcraeft/db/alembic/versions/20260704_01_morph_catalog_tables.py` | Migration |
| `wyrdcraeft/models/morph_catalog.py` | ORM models |
| `wyrdcraeft/services/morphology/catalog/loader.py` | Fixture → SQLite upsert |
| `wyrdcraeft/services/morphology/catalog/__init__.py` | Exports loader + LoadResult |
| `wyrdcraeft/cli/morphology.py` | `--refresh-catalog`; seed before form gen |
| `wyrdcraeft/etc/morphology/wright_paradigms.json` | 113 morph classes, 3 sources |
| `tests/morphology/test_morph_catalog.py` | Model + loader tests (5 tests) |
| `tests/test_cli_morphology.py` | Build seed/skip/refresh CLI tests |

## Loader behavior

`MorphologyCatalogLoader` (`loader.py`):

- `is_catalog_populated()` — any row in `morph_classes`
- `load_fixture(path, refresh=False)` — upsert order: sources → classes →
  sections → junction rows
- `ensure_seeded(path, refresh=False)` — load when empty or refresh requested
- Ignores fixture `parent_id` and `recognition_hints` (Phase 2)
- Unknown `source_keys` → `ValueError`

## Build integration

`morphology build`:

1. CLI startup runs `ensure_database_ready` (Alembic → catalog tables exist)
2. After paradigm assignment, before `SqliteIndexSink` / form generation:
   - `ensure_seeded(resolved_data_dir / "wright_paradigms.json", refresh=...)`
3. `--refresh-catalog` forces reload via loader `refresh=True`
4. Catalog seed errors → `click.ClickException` + `progress.stop()`

## Tests passing (verified)

```bash
.venv/bin/pytest tests/test_cli_morphology.py tests/morphology/test_morph_catalog.py -q
# 26 passed
```

`tests/morphology/data/refactor_baseline.json` — **unchanged**.

## Known issues / blockers

### 1. Circular import on full morphology test collection

```bash
.venv/bin/pytest tests/morphology -m "not morphology_full" -q
# ERROR at collection: test_build_profile.py
# build_profile → progress → cli.utils → cli → morphology → build_profile
```

Pre-existing on branch; **not introduced by catalog work**. Targeted CLI + catalog
tests pass. Fix before Phase 1 gate validation if full morphology suite required.

### 2. Untracked plan directory

`doc/plans/` is still `??` in git — commit when ready (not done this session).

### 3. Package data

`pyproject.toml` package-data includes `etc/morphology/*.txt` only; confirm
`wright_paradigms.json` is included in wheel if install-time seeding matters
(dev/tests use repo path via `--data-dir` or `importlib.resources`).

## Next steps (in order)

1. **Task 5** — Add `test_wright_paradigms_fixture_matches_expected_counts` in
   `tests/morphology/test_morph_catalog.py` (113 classes, POS enum, unique ids)
2. **Phase 1 Gate A** — Spec review vs `phase-1-reference-catalog.md` +
   `00-design-decisions.md`
3. **Phase 1 Gate B** — Bugbot on branch diff
4. Run full validation from plan README:

```bash
.venv/bin/ruff check <touched-py-files>
.venv/bin/mypy <touched-py-files>
make napoleon-gate
.venv/bin/pytest tests/morphology/test_morph_catalog.py -q
.venv/bin/pytest tests/test_cli_morphology.py -q
# resolve circular import before:
.venv/bin/pytest tests/morphology -m "not morphology_full" -q
git diff --exit-code -- tests/morphology/data/refactor_baseline.json
```

5. **Phase 2** — Lemma assignment (`lemma_morph_classes`, recognition hints,
   assigner, read API) — **complete** 2026-07-04; see
   `doc/sessions/2026-07-04-morphology-wright-catalog-phase2.md`

6. **Phase 3** — `forms.morph_class_id` FK and query integration — next

## Subagent workflow used

Subagent-driven development per task:

1. Dispatch implementer (composer-2.5-fast)
2. Spec compliance review
3. Code quality review
4. Fix loops when reviewers block (load order, error handling, skip/refresh tests)

User dispatch commands used: "dispatch phase 1 task", "dispatch task 3", "dispatch task 4".

## Parity / safety constraints (unchanged)

- Morphology tests writing SQLite: use `isolated_morphology_app_data` fixture
- Napoleon gate on touched Python
- Morphology logic docstrings cite `data/OldEnglishGrammar.pdf` and
  `data/Ondej_Tich_40-54-1.pdf` with PoS scope
