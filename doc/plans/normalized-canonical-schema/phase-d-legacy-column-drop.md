# Phase D — Drop Legacy Form String Columns

> **Prerequisites:** Phase C gates passed and committed  
> **REQUIRED SUB-SKILL:** subagent-driven-development

**Goal:** Remove legacy denormalized string columns from `forms`; switch all readers to FKs
and reference joins; refresh architecture ER diagram.

**Architecture:** Final Alembic migration drops columns listed in ADR-0002. Generation
pipeline still builds legacy strings in memory for parity/debug if needed, but sink persists
FKs only. Update snapshots/reference exports if they assert dropped column names.

**Out of scope:** `paradigm_templates` table; FTS5; input file reformatting.

---

## Task 1: Alembic migration `20260706_04`

**Files:**
- Create: `wyrdcraeft/db/alembic/versions/20260706_04_drop_forms_legacy_strings.py`
- Modify: `wyrdcraeft/models/sqlalchemy.py` (`Form`)
- Modify: `wyrdcraeft/models/morphology.py` (`FormRow`, `GeneratedForm`, `ManualForm` — keep
  in-memory fields for generator; document which are sink-persisted)

- [ ] Drop columns from `forms`:
  - `wright`, `paradigm`, `paraID`, `wordclass`, `function`, `class1`, `class2`, `class3`
- [ ] **Keep:** `*_key` columns, surface fields (`form`, `formi`, `title`, `BT`, `stem`, …),
  all FK columns from Phase B
- [ ] ORM `Form` model aligned; remove dropped mapped columns

---

## Task 2: Sink + query path cleanup

**Files:**
- Modify: `wyrdcraeft/services/morphology/generation/sinks.py`
- Modify: `wyrdcraeft/services/morphology/generation/query.py`
- Modify: `wyrdcraeft/services/morphology/reference_snapshots.py`
- Modify: `wyrdcraeft/services/lexicon/build.py` (search key emission)
- Modify: `wyrdcraeft/services/lexicon/query.py`
- Modify: `wyrdcraeft/services/lexicon/form_decode.py` (accept inflection code string from join)
- Test: all morphology + lexicon tests

- [ ] Sink payload omits dropped DB columns
- [ ] Query paths join `parts_of_speech`, `inflection_codes`, `morph_classes` for labels
- [ ] Search key build reads `forms.wordclass_id` / `inflection_code_id` not legacy strings
- [ ] `form_decode` entry point accepts resolved code + pos from joins

---

## Task 3: Lexicon form display

**Files:**
- Modify: `wyrdcraeft/services/lexicon/query.py`
- Modify: `wyrdcraeft/services/lexicon/tui.py`
- Test: `tests/lexicon/test_form_decode.py`, browse tests

- [ ] Morphology table/grid uses FK joins for wordclass + function display
- [ ] No references to dropped column names in SQL or row accessors

---

## Task 4: Snapshot + baseline guardrails

**Files:**
- Modify: `wyrdcraeft/services/morphology/reference_snapshots.py` (if DB snapshot lists columns)
- Modify: `tests/morphology/test_query_service.py` (index assertions)
- Modify: `tests/lexicon/test_schema.py`

- [ ] Update expected schema column lists
- [ ] Run full parity gate:

```bash
.venv/bin/pytest tests/morphology -m "morphology_full" -q
git diff --exit-code -- tests/morphology/data/refactor_baseline.json
```

- [ ] If `refactor_baseline.json` changes: verify generator **TSV/output** parity only —
  DB column drop must not change emitted TSV field set unless intentional (document in commit)

---

## Task 5: Wright audit + catalog (read paths)

**Files:**
- Modify: `wyrdcraeft/services/morphology/catalog/wright_audit.py` (if reads `forms.wright`)
- Test: `tests/morphology/test_wright_audit.py`

- [ ] Audit compares dict source `wright` to assignments — not dropped `forms.wright`
- [ ] Or: audit reads legacy from generator session only — document chosen approach in test

---

## Task 6: Architecture ER + CONTEXT

**Files:**
- Modify: `doc/source/architecture/index.rst` (full normalized ER)
- Modify: `CONTEXT.md` (remove/update lexicon read model glossary; note legacy columns removed)

- [ ] ER diagram shows FK model from ADR-0002
- [ ] Remove `LEXICON_ENTRIES` / `LEXICON_FORMS` entities
- [ ] Update `FORMS` entity field list

---

## Phase D validation

```bash
.venv/bin/ruff check wyrdcraeft/services/morphology/generation/sinks.py wyrdcraeft/services/morphology/generation/query.py wyrdcraeft/services/lexicon/build.py wyrdcraeft/services/lexicon/query.py wyrdcraeft/models/sqlalchemy.py
.venv/bin/mypy wyrdcraeft/services/morphology/generation/sinks.py wyrdcraeft/services/morphology/generation/query.py wyrdcraeft/services/lexicon/build.py wyrdcraeft/services/lexicon/query.py wyrdcraeft/models/sqlalchemy.py
make napoleon-gate
.venv/bin/pytest tests/morphology -m "not morphology_full" -q
.venv/bin/pytest tests/morphology -m "morphology_full" -q
.venv/bin/pytest tests/lexicon -q
git diff --exit-code -- tests/morphology/data/refactor_baseline.json
```

Manual end-to-end:

```bash
WYRDCRAEFT_APP_DATA_DIR=/tmp/wc-phase-d .venv/bin/wyrdcraeft morphology build --limit 500
WYRDCRAEFT_APP_DATA_DIR=/tmp/wc-phase-d .venv/bin/wyrdcraeft lexicon build --no-tui
sqlite3 /tmp/wc-phase-d/wyrdcraeft.sqlite3 "PRAGMA table_info(forms);"
# confirm legacy string cols gone; FK cols present
```

---

## Phase D — Gate A: Spec review checklist

- [ ] All legacy `forms` string columns listed in ADR-0002 are dropped
- [ ] `*_key` columns retained
- [ ] All product read paths use FKs / joins
- [ ] `search_keys` rebuild still works
- [ ] Architecture ER updated

---

## Phase D — Gate B: Code review checklist

- [ ] No SQL selecting dropped columns
- [ ] morphology_full + refactor baseline green (or baseline change explicitly justified)
- [ ] Lexicon browse smoke paths covered by tests
- [ ] Wright audit behavior documented if data source changed

---

## Phase D — Commit

```bash
git commit -m "$(cat <<'EOF'
Normalize schema phase D: drop legacy forms string columns.

Remove denormalized wright, paradigm, paraID, wordclass, function, and
class columns from forms; serve morphology and browse from FK joins only.
EOF
)"
```

---

## Post-phase checklist (coordinator)

- [ ] All four phase commits on branch
- [ ] Open PR with link to `doc/plans/normalized-canonical-schema/README.md`
- [ ] Note any deferred items: `paradigm_templates`, `bt_variants` PK, FTS5
