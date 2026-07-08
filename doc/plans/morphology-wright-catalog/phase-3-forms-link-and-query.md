# Phase 3 — Forms Link, Query, and Lexicon Surfacing

> **Prerequisites:** Phase 2 gates passed  
> **REQUIRED SUB-SKILL:** subagent-driven-development

**Goal:** Propagate lemma-level morph class to `forms` rows; expose classification in morphology query and lexicon browse; begin deprecating legacy string columns.

**Architecture:** Add nullable `forms.morph_class_id` FK; populate during morphology SQLite sink from `(normalized_title, catalog_pos_from_wordclass)` join; extend `MorphologyQueryService` and lexicon read model.

---

## Task 1: Schema migration

**Files:**
- Create: `wyrdcraeft/db/alembic/versions/202607XX_03_forms_morph_class_id.py`
- Modify: `wyrdcraeft/models/sqlalchemy.py` (`Form` model)

- [ ] `forms.morph_class_id INTEGER NULL REFERENCES morph_classes(id)`
- [ ] INDEX `idx_forms_morph_class_id`
- [ ] Nullable — existing rows stay NULL until rebuild

---

## Task 2: Sink propagation

**Files:**
- Modify: `wyrdcraeft/services/morphology/generation/sinks.py`
- Modify: `wyrdcraeft/services/morphology/catalog/query.py`
- Test: `tests/morphology/test_morph_catalog.py`

- [ ] During form row insert, resolve:
  - `normalized_title` from existing sink logic
  - `pos = catalog_pos_from_wordclass(wordclass)`
  - Lookup `lemma_morph_classes` → set `morph_class_id`
- [ ] Verbal participle forms (`wordclass=verb`, `function` in `PsPt`, `PaPt`): use verb lemma assignment
- [ ] When no assignment: leave NULL (do not invent)
- [ ] **Do not remove** legacy `paradigm`/`paraID`/`wright` columns yet

---

## Task 3: Query service

**Files:**
- Modify: `wyrdcraeft/services/morphology/generation/query.py`
- Test: `tests/morphology/test_query_service.py`

- [ ] Join `morph_classes` (+ optional Wright § list) on query by form
- [ ] Response payload fields (names TBD, document in test):
  - `morph_class_key`, `modern_class`, `canonical_name`, `wright_label`
  - `wright_section_numbers: list[int]`
  - `sources: list[{citation_apa, url}]`
- [ ] Works with `isolated_morphology_app_data` + seeded catalog + assignment

---

## Task 4: Lexicon read model (optional in same phase)

**Files:**
- Modify: `wyrdcraeft/services/lexicon/build.py`
- Modify: lexicon projection tables if needed

- [ ] Add morph class summary to `lexicon_entries` or join at browse time
- [ ] POS-filtered paradigm grid unchanged in behavior; enrich with class metadata

---

## Task 5: Deprecation documentation

**Files:**
- Modify: `CONTEXT.md` (glossary only — one line each for morph class assignment)
- Modify: `doc/plans/morphology-wright-catalog/00-design-decisions.md` if status changes

- [ ] Mark `forms.paradigm`, `forms.paraID`, `forms.wright` as **legacy** in model docstrings
- [ ] Do not drop columns in this phase

---

## Phase 3 validation

```bash
.venv/bin/pytest tests/morphology/test_query_service.py tests/morphology/test_morph_catalog.py -q
.venv/bin/pytest tests/morphology -m "not morphology_full" -q
.venv/bin/pytest tests/morphology -m "morphology_full" -q
git diff --exit-code -- tests/morphology/data/refactor_baseline.json
```

Manual check:

```bash
WYRDCRAEFT_APP_DATA_DIR=/tmp/wc-test .venv/bin/wyrdcraeft morphology build --limit 50
# query a known lemma; confirm morph_class fields populated
```

---

## Phase 3 — Gate A: Spec review

Verify:

- `morph_class_id` populated from lemma assignment, not legacy strings
- NULL when unassigned — no fake defaults
- Legacy columns still present
- Query tests prove Wright § + sourcing visible

## Phase 3 — Gate B: Code review

Verify parity baseline unchanged; morphology_full green.

---

## Future (post Phase 3)

- Drop legacy columns after downstream consumers migrated
- UI: dictionary entry panel shows morph class + Wright § text (Phase 4)
