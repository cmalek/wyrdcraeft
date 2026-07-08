# Phase B — Forms Foreign Keys (Legacy Strings Remain)

> **Prerequisites:** Phase A gates passed and committed  
> **REQUIRED SUB-SKILL:** subagent-driven-development  
> **Next phase:** [phase-c-lexicon-shrink.md](./phase-c-lexicon-shrink.md)

**Goal:** Add and populate `forms.wordclass_id`, `forms.inflection_code_id`,
`forms.morph_class_id`, and `forms.entry_id`. Keep all legacy string columns for
verification and parity.

**Architecture:** Morphology sink resolves FKs at insert time using seeded reference
tables, `lemma_morph_classes`, and `NormalizedTitleJoinIndex.resolve_one` (NULL when
ambiguous). Legacy columns still written in parallel for Phase D drop.

**Out of scope:** Dropping legacy `forms` strings; lexicon projection table removal.

---

## Task 1: Alembic migration `20260706_02`

**Files:**
- Create: `wyrdcraeft/db/alembic/versions/20260706_02_forms_foreign_keys.py`
- Modify: `wyrdcraeft/models/sqlalchemy.py` (`Form`)

- [ ] Add nullable columns with indexes:
  - `wordclass_id` INTEGER NULL REFERENCES `parts_of_speech(id)`
  - `inflection_code_id` INTEGER NULL REFERENCES `inflection_codes(id)`
  - `morph_class_id` INTEGER NULL REFERENCES `morph_classes(id)`
  - `entry_id` INTEGER NULL REFERENCES `bt_entries(id)`
- [ ] Indexes: `idx_forms_wordclass_id`, `idx_forms_inflection_code_id`,
  `idx_forms_morph_class_id`, `idx_forms_entry_id`
- [ ] ORM `Form` model: mapped columns + relationships optional
- [ ] **Keep** legacy columns: `wordclass`, `function`, `wright`, `paradigm`, `paraID`,
  `class1`, `class2`, `class3`, all `*_key` columns

---

## Task 2: Form FK resolver service

**Files:**
- Create: `wyrdcraeft/services/morphology/generation/form_fk_resolver.py`
- Test: `tests/morphology/test_form_fk_resolver.py`

- [ ] `FormFkResolver` class (constructor: connection or preloaded id maps)
- [ ] `resolve_wordclass_id(wordclass: str) -> int | None`
- [ ] `resolve_inflection_code_id(function: str, wordclass: str) -> int | None`
  - Empty function → NULL or dedicated seed row (match current behavior)
- [ ] `resolve_morph_class_id(normalized_title: str, wordclass: str, function: str) -> int | None`
  - Verbal participles (`wordclass=verb`, `function` in `PsPt`/`PaPt`): verb lemma assignment
  - Else: `catalog_pos_from_wordclass` → lookup `lemma_morph_classes`
- [ ] `resolve_entry_id(normalized_title: str, wordclass: str) -> int | None`
  - Use `NormalizedTitleJoinIndex.resolve_one`; return NULL when ambiguous or unmatched
- [ ] Unit tests: homograph → NULL entry_id; known lemma → id; unassigned morph class → NULL

---

## Task 3: Sink propagation

**Files:**
- Modify: `wyrdcraeft/services/morphology/generation/sinks.py`
- Test: `tests/morphology/test_morph_catalog.py`, `tests/morphology/test_query_service.py`

- [ ] `SqliteIndexSink` builds `FormFkResolver` once per flush (or per build)
- [ ] `_rows_to_payload` adds FK fields alongside legacy strings
- [ ] On NULL FK: insert NULL — never invent defaults
- [ ] Integration test with `isolated_morphology_app_data`:
  - build small morphology slice
  - assert FK columns populated for known lemma
  - assert ambiguous homograph fixture yields NULL `entry_id`

---

## Task 4: Morphology query — optional FK exposure

**Files:**
- Modify: `wyrdcraeft/services/morphology/generation/query.py`
- Test: `tests/morphology/test_query_service.py`

- [ ] Form lookup responses may include resolved morph class metadata via `morph_class_id`
  join (if not already present from catalog Phase 3 work)
- [ ] Do not remove legacy field names from API yet — add FK-backed fields or join data
- [ ] Tests prove Wright § + class metadata visible when `morph_class_id` set

---

## Task 5: Verification helper (optional but recommended)

**Files:**
- Create: `scripts/morphology/verify_form_fks.py` (or pytest module)
- Test: `tests/morphology/test_form_fk_verification.py`

- [ ] Sample N forms after build: compare `wordclass_id` to legacy `wordclass`,
  `inflection_code_id` to `function`, `morph_class_id` to lemma assignment
- [ ] Report counts of NULL FKs by category (acceptable; document baseline)

---

## Task 6: Model docstrings — mark legacy

**Files:**
- Modify: `wyrdcraeft/models/sqlalchemy.py` (`Form` legacy column docstrings)

- [ ] Mark `wright`, `paradigm`, `para_id`, `wordclass`, `function`, `class1`–`class3`
  as **legacy** in docstrings; note FK replacements

---

## Phase B validation

```bash
.venv/bin/ruff check wyrdcraeft/services/morphology/generation/form_fk_resolver.py wyrdcraeft/services/morphology/generation/sinks.py wyrdcraeft/models/sqlalchemy.py
.venv/bin/mypy wyrdcraeft/services/morphology/generation/form_fk_resolver.py wyrdcraeft/services/morphology/generation/sinks.py wyrdcraeft/models/sqlalchemy.py
make napoleon-gate
.venv/bin/pytest tests/morphology/test_form_fk_resolver.py tests/morphology/test_morph_catalog.py tests/morphology/test_query_service.py -q
.venv/bin/pytest tests/morphology -m "not morphology_full" -q
.venv/bin/pytest tests/morphology -m "morphology_full" -q
git diff --exit-code -- tests/morphology/data/refactor_baseline.json
```

Manual:

```bash
WYRDCRAEFT_APP_DATA_DIR=/tmp/wc-phase-b .venv/bin/wyrdcraeft morphology build --limit 200
sqlite3 /tmp/wc-phase-b/wyrdcraeft.sqlite3 \
  "SELECT COUNT(*), COUNT(wordclass_id), COUNT(inflection_code_id), COUNT(morph_class_id), COUNT(entry_id) FROM forms;"
```

---

## Phase B — Gate A: Spec review checklist

- [ ] All four FK columns exist on `forms`
- [ ] Sink populates FKs at insert time
- [ ] `entry_id` NULL on ambiguous homographs (test proves)
- [ ] `morph_class_id` from lemma assignment, not legacy `wright`/`paradigm`
- [ ] Legacy string columns still present and still written
- [ ] `refactor_baseline.json` unchanged

---

## Phase B — Gate B: Code review checklist

- [ ] No fake defaults for NULL FK paths
- [ ] `isolated_morphology_app_data` used in integration tests
- [ ] morphology_full green
- [ ] Resolver reuses `NormalizedTitleJoinIndex` — no duplicated join logic

---

## Phase B — Commit

```bash
git commit -m "$(cat <<'EOF'
Normalize schema phase B: forms foreign keys at morphology sink.

Add wordclass_id, inflection_code_id, morph_class_id, and entry_id to
forms; populate during build while retaining legacy string columns.
EOF
)"
```
