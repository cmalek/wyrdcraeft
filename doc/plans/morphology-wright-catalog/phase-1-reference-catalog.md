# Phase 1 — Reference Catalog Tables

> **REQUIRED SUB-SKILL:** superpowers:subagent-driven-development  
> **Prerequisites:** Read [00-design-decisions.md](./00-design-decisions.md) and [README.md](./README.md)  
> **Do not start Phase 2 until both phase completion gates pass.**

**Goal:** Add normalized Wright/morph-class catalog tables to canonical SQLite, load from `wright_paradigms.json`, auto-seed on first morphology build.

**Architecture:** New SQLAlchemy models in dedicated module; Alembic revision; `MorphologyCatalogLoader` class upserts fixture; build CLI checks row count and seeds when empty.

---

## Task 1: Alembic migration

**Files:**
- Create: `wyrdcraeft/db/alembic/versions/20260704_01_morph_catalog_tables.py`
- Modify: none

- [ ] **Step 1: Write migration**

Create revision `20260704_01` with `down_revision = "20260703_01"`.

Tables (match names exactly):

```python
# morph_sources
#   id INTEGER PK autoincrement
#   source_key TEXT NOT NULL UNIQUE
#   citation_apa, url, retrieved_date, notes TEXT NOT NULL (notes default '')

# morph_classes
#   id INTEGER PK autoincrement
#   class_key TEXT NOT NULL UNIQUE
#   pos, canonical_name, modern_class, traditional_class TEXT NOT NULL
#   wright_label, mapping_rationale, notes TEXT NOT NULL (defaults '')
#   is_assignable INTEGER NOT NULL DEFAULT 1
#   paradigmatic_words_json, aliases_json, features_json TEXT NOT NULL DEFAULT '[]'/'[]'/'{}'
#   INDEX idx_morph_classes_pos (pos)
#   INDEX idx_morph_classes_class_key (class_key)  # redundant with UNIQUE but matches repo style

# wright_sections
#   section_no INTEGER PK
#   section_text TEXT NULL
#   work TEXT NOT NULL DEFAULT 'Wright & Wright, Old English Grammar'
#   notes TEXT NOT NULL DEFAULT ''

# morph_class_wright_sections
#   id INTEGER PK autoincrement
#   morph_class_id INTEGER FK morph_classes.id NOT NULL
#   section_no INTEGER FK wright_sections.section_no NOT NULL
#   sort_order INTEGER NOT NULL DEFAULT 0
#   UNIQUE (morph_class_id, section_no)
#   INDEX idx_morph_class_wright_sections_section_no (section_no)

# morph_class_sources
#   id INTEGER PK autoincrement
#   morph_class_id INTEGER FK morph_classes.id NOT NULL
#   source_id INTEGER FK morph_sources.id NOT NULL
#   UNIQUE (morph_class_id, source_id)
```

- [ ] **Step 2: Verify migration applies**

```bash
python3 - <<'PY'
from pathlib import Path
from wyrdcraeft.db.runtime import upgrade_canonical_db
p = Path("/tmp/wyrdcraeft_phase1_test.sqlite3")
if p.exists():
    p.unlink()
upgrade_canonical_db(p)
import sqlite3
conn = sqlite3.connect(p)
tables = {r[0] for r in conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()}
for t in ["morph_sources","morph_classes","wright_sections",
          "morph_class_wright_sections","morph_class_sources"]:
    assert t in tables, t
print("OK", sorted(tables & {"morph_classes","wright_sections"}))
PY
```

Expected: `OK ['morph_classes', 'wright_sections']`

- [ ] **Step 3: Commit**

```bash
git add wyrdcraeft/db/alembic/versions/20260704_01_morph_catalog_tables.py
git commit -m "feat(db): add morph catalog reference tables"
```

---

## Task 2: SQLAlchemy models

**Files:**
- Create: `wyrdcraeft/models/morph_catalog.py`
- Modify: `wyrdcraeft/models/__init__.py` (export public models if pattern exists)

- [ ] **Step 1: Write failing import test**

Create `tests/morphology/test_morph_catalog.py`:

```python
from wyrdcraeft.models.morph_catalog import (
    MorphClass,
    MorphClassSource,
    MorphClassWrightSection,
    MorphSource,
    WrightSection,
)


def test_morph_catalog_models_importable() -> None:
    assert MorphClass.__tablename__ == "morph_classes"
    assert WrightSection.__tablename__ == "wright_sections"
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
.venv/bin/pytest tests/morphology/test_morph_catalog.py::test_morph_catalog_models_importable -q
```

- [ ] **Step 3: Implement models**

`wyrdcraeft/models/morph_catalog.py`:

- Use `from wyrdcraeft.db.base import Base`
- `Mapped`, `mapped_column`, `relationship` with TYPE_CHECKING imports
- Class docstrings per AGENTS.md Napoleon contract
- Morphology-related classes need `Note:` citing `data/OldEnglishGrammar.pdf` and `data/Ondej_Tich_40-54-1.pdf` with PoS scope
- **`MorphClass.id`**: int PK autoincrement
- **`MorphClass.class_key`**: unique Text, not PK
- Relationships: `MorphClass.wright_section_links`, `MorphClass.source_links`; cascade `all, delete-orphan` on owned links
- **Do not** add `BTEntryMorphClass`, `parent_id`, `recognition_hints_json`

- [ ] **Step 4: Run test — expect PASS**

```bash
.venv/bin/pytest tests/morphology/test_morph_catalog.py::test_morph_catalog_models_importable -q
```

- [ ] **Step 5: ruff + mypy + napoleon-gate on touched files**

- [ ] **Step 6: Commit**

```bash
git add wyrdcraeft/models/morph_catalog.py tests/morphology/test_morph_catalog.py
git commit -m "feat(models): add morph catalog SQLAlchemy models"
```

---

## Task 3: Fixture loader

**Files:**
- Create: `wyrdcraeft/services/morphology/catalog/__init__.py`
- Create: `wyrdcraeft/services/morphology/catalog/loader.py`
- Test: `tests/morphology/test_morph_catalog.py`

- [ ] **Step 1: Write failing loader test**

Add to `tests/morphology/test_morph_catalog.py`:

```python
import json
from pathlib import Path

import pytest
from sqlalchemy import func, select

from wyrdcraeft.db.runtime import create_engine, upgrade_canonical_db
from wyrdcraeft.models.morph_catalog import MorphClass, MorphSource, WrightSection
from importlib.resources import files

from wyrdcraeft.services.morphology.catalog.loader import MorphologyCatalogLoader

FIXTURE = Path(str(files("wyrdcraeft").joinpath("etc/morphology/wright_paradigms.json")))


@pytest.fixture
def catalog_db(tmp_path: Path):
    db_path = tmp_path / "wyrdcraeft.sqlite3"
    upgrade_canonical_db(db_path)
    engine = create_engine(db_path)
    yield engine
    engine.dispose()


def test_catalog_loader_seeds_fixture(catalog_db) -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    expected_classes = len(fixture["morph_classes"])
    expected_sources = len(fixture["sources"])

    MorphologyCatalogLoader(catalog_db).load_fixture(FIXTURE)

    with catalog_db.connect() as conn:
        assert conn.execute(select(func.count()).select_from(MorphSource)).scalar_one() == expected_sources
        assert conn.execute(select(func.count()).select_from(MorphClass)).scalar_one() == expected_classes
        assert conn.execute(select(func.count()).select_from(WrightSection)).scalar_one() >= 1
```

Adjust path helper to match repo (`wyrdcraeft.paths` or `importlib.resources` — grep existing morphology path resolution in `wyrdcraeft/cli/morphology.py`).

- [ ] **Step 2: Run test — expect FAIL**

- [ ] **Step 3: Implement `MorphologyCatalogLoader`**

Cohesive class in `loader.py`:

```python
class MorphologyCatalogLoader:
    """Load wright_paradigms.json into morph catalog tables."""

    def __init__(self, engine: Engine) -> None: ...

    def is_catalog_populated(self) -> bool:
        """Return True when morph_classes has at least one row."""

    def load_fixture(self, path: Path, *, refresh: bool = False) -> LoadResult:
        """Upsert catalog from fixture JSON. If refresh=True, clear catalog tables first."""

    def ensure_seeded(self, path: Path, *, refresh: bool = False) -> bool:
        """Load when empty or refresh requested. Return True if load ran."""
```

Load order:

1. Optional clear (child tables → parents) when `refresh=True`
2. Upsert `morph_sources` by `source_key`
3. Upsert `morph_classes` by `class_key`; serialize lists/objects to JSON strings
4. Upsert `wright_sections` by `section_no` (text NULL)
5. Replace junction rows per class from `wright_sections` array (preserve order in `sort_order`)
6. Replace `morph_class_sources` from `source_keys`

Validate fixture minimally:

- Required top-level keys: `schema_version`, `sources`, `morph_classes`
- Each class `id` becomes `class_key`
- Skip unknown `source_keys` → raise `ValueError` with clear message

Use SQLAlchemy Core or ORM session; follow patterns in `wyrdcraeft/services/dictionary/sinks.py` for bulk writes.

- [ ] **Step 4: Run test — expect PASS**

- [ ] **Step 5: Add idempotency test**

```python
def test_catalog_loader_is_idempotent(catalog_db) -> None:
    loader = MorphologyCatalogLoader(catalog_db)
    loader.load_fixture(FIXTURE)
    count1 = ...
    loader.load_fixture(FIXTURE)
    count2 = ...
    assert count1 == count2
```

- [ ] **Step 6: Quality gates + commit**

---

## Task 4: Build integration

**Files:**
- Modify: `wyrdcraeft/cli/morphology.py`
- Modify: `wyrdcraeft/services/morphology/generation/sinks.py` or build path where SQLite flush happens (grep `upgrade_canonical_db` / `ensure_database_ready` in morphology build)
- Test: `tests/test_cli_morphology.py`

- [ ] **Step 1: Write failing CLI test**

In `tests/test_cli_morphology.py` (use `isolated_morphology_app_data`):

```python
def test_morphology_build_seeds_catalog_when_empty(isolated_morphology_app_data, ...):
    # run minimal morphology build (limit=1 or existing fast fixture path)
    # assert morph_classes count == 113 (or fixture length)
```

Use smallest build path already in test suite — read `tests/test_cli_morphology.py` for pattern.

- [ ] **Step 2: Add `--refresh-catalog` flag**

On `morphology build` command:

```python
@click.option(
    "--refresh-catalog",
    is_flag=True,
    default=False,
    help="Re-load Wright morph catalog from packaged fixture.",
)
```

- [ ] **Step 3: Hook seeding after DB ready**

After canonical DB upgrade, before or after form generation (prefer **before** — catalog is independent):

```python
catalog_loader.ensure_seeded(default_fixture_path, refresh=refresh_catalog)
```

Default fixture path: packaged `wyrdcraeft/etc/morphology/wright_paradigms.json`.

- [ ] **Step 4: Run CLI test — expect PASS**

- [ ] **Step 5: Run full morphology test subset**

```bash
.venv/bin/pytest tests/test_cli_morphology.py tests/morphology/test_morph_catalog.py -q
.venv/bin/pytest tests/morphology -m "not morphology_full" -q
git diff --exit-code -- tests/morphology/data/refactor_baseline.json
```

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(morphology): auto-seed Wright catalog on build"
```

---

## Task 5: Schema validation test

**Files:**
- Test: `tests/morphology/test_morph_catalog.py`

- [ ] **Step 1: Add fixture structure test**

Without adding `jsonschema` dependency unless already present — validate structurally:

```python
def test_wright_paradigms_fixture_matches_expected_counts() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert len(data["sources"]) >= 1
    assert len(data["morph_classes"]) == 113
    ids = {c["id"] for c in data["morph_classes"]}
    assert len(ids) == 113
    for c in data["morph_classes"]:
        assert c["pos"] in {"noun", "verb", "adjective", "adverb", "pronoun"}
```

- [ ] **Step 2: Run + commit**

---

## Phase 1 completion checklist

- [ ] Migration applies cleanly on empty DB
- [ ] 113 morph classes + sources + Wright § rows load from fixture
- [ ] Build auto-seeds empty DB; skips populated DB
- [ ] `--refresh-catalog` re-loads
- [ ] All tests use `isolated_morphology_app_data` / tmp DB — never default app-data path
- [ ] `refactor_baseline.json` unchanged
- [ ] ruff, mypy, napoleon-gate green on touched Python

---

## Phase 1 — Gate A: Spec review

Dispatch **code-reviewer** with:

- Plan: this file
- Design: `00-design-decisions.md`
- Verify checklist above + no Phase 2 scope (`lemma_morph_classes`, `recognition_hints`, `forms.morph_class_id`)

## Phase 1 — Gate B: Code review

Dispatch **bugbot** on branch diff. Fix blockers before Phase 2.
