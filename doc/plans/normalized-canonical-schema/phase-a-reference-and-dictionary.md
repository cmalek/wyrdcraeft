# Phase A — Reference Tables and Dictionary POS FKs

> **Prerequisites:** Alembic head `20260704_02`; Wright catalog Phase 2 merged  
> **REQUIRED SUB-SKILL:** subagent-driven-development  
> **Next phase:** [phase-b-forms-foreign-keys.md](./phase-b-forms-foreign-keys.md)

**Goal:** Introduce `parts_of_speech` and `inflection_codes` reference tables; migrate
dictionary and catalog POS columns to FKs; rename `bt_entries.headword_macronized` →
`headword` and drop persisted `headword_raw`.

**Architecture:** One Alembic migration seeds reference data and backfills `pos_id` from
existing text columns. Dictionary pipeline writes FKs on new builds. In-memory parse
paths keep raw headword until sink boundary.

**Out of scope for Phase A:** `forms` FK columns, lexicon table changes, dropping legacy
`forms` string columns.

---

## Task 1: POS + inflection seed fixtures

**Files:**
- Create: `wyrdcraeft/etc/morphology/parts_of_speech_seed.json`
- Create: `wyrdcraeft/etc/morphology/inflection_codes_seed.json`
- Create: `wyrdcraeft/services/morphology/catalog/pos_seed.py`
- Test: `tests/morphology/test_pos_seed.py`

- [ ] `parts_of_speech_seed.json` — one object per row with at minimum:
  `code`, `display_label`, `is_inflectable` (0/1). Required codes:
  `noun`, `verb`, `adjective`, `adverb`, `pronoun`, `numeral`, `unknown`,
  `participle`, `preposition`, `conjunction`, `interjection`, `indeclinable`
- [ ] `inflection_codes_seed.json` — array of `{ "code", "pos_code", "display_json" }`
  covering all function codes emitted today (extract from
  `wyrdcraeft/services/lexicon/form_decode.py` and morphology generators; include
  `If`, `Po`, `Co`, `Su`, noun case codes, verb tense/mood codes, empty-string row
  if still emitted)
- [ ] `pos_seed.py`:
  - `ensure_parts_of_speech(connection) -> dict[str, int]` — upsert by `code`, return code→id map
  - `ensure_inflection_codes(connection, pos_map) -> dict[str, int]` — upsert by `code`, return code→id map
- [ ] Tests: seed is idempotent; every `WORDCLASS_TO_BT_POS` wordclass maps to a POS row;
  sample inflection codes resolve to expected `pos_id`

---

## Task 2: SQLAlchemy reference models

**Files:**
- Create: `wyrdcraeft/models/reference.py`
- Modify: `wyrdcraeft/models/__init__.py` (export if project pattern requires)

- [ ] `PartOfSpeech` model → table `parts_of_speech`
  - `id` PK, `code` unique NOT NULL, `display_label` NOT NULL, `is_inflectable` INT NOT NULL DEFAULT 1
  - Index on `code`
- [ ] `InflectionCode` model → table `inflection_codes`
  - `id` PK, `code` unique NOT NULL, `pos_id` FK → `parts_of_speech.id`, `display_json` NOT NULL DEFAULT `'{}'`
  - Index on `pos_id`, index on `code`
- [ ] Napoleon `#:` on all attrs; class docstrings per AGENTS.md

---

## Task 3: Alembic migration `20260706_01`

**Files:**
- Create: `wyrdcraeft/db/alembic/versions/20260706_01_parts_of_speech_and_dictionary_pos.py`
- Modify: `wyrdcraeft/models/sqlalchemy.py` (`BTEntry`)
- Modify: `wyrdcraeft/models/morph_catalog.py` (`MorphClass`, `LemmaMorphClass`)

- [ ] Create `parts_of_speech`, `inflection_codes`
- [ ] Seed both tables in migration (inline SQL or call shared seed helper)
- [ ] `bt_entries`:
  - Add `pos_id` INTEGER NOT NULL (temporary default 0 forbidden — backfill in same migration)
  - Backfill `pos_id` from text `pos` via mapping (`adj`→adjective, `unknown`→unknown, …)
  - Drop column `pos`
  - Rename `headword_macronized` → `headword`
  - Drop column `headword_raw`
  - Keep `norm_key`, `normalized_title`, JSON cols unchanged
- [ ] `morph_classes`: add `pos_id`, backfill from text `pos`, drop text `pos`
- [ ] `lemma_morph_classes`: add `pos_id`, backfill from text `pos`, drop text `pos`
- [ ] Update ORM models to match; `BTEntry.headword`, `BTEntry.pos_id`, etc.
- [ ] **Do not** touch `forms` yet

---

## Task 4: POS resolver helpers

**Files:**
- Modify: `wyrdcraeft/services/morphology/catalog/pos.py`
- Test: `tests/morphology/test_morph_catalog_pos.py` (extend)

- [ ] Add `pos_id_from_bt_pos(connection, bt_pos: str) -> int`
- [ ] Add `pos_id_from_wordclass(connection, wordclass: str) -> int | None`
- [ ] Add `pos_id_from_catalog_pos(connection, catalog_pos: str) -> int`
- [ ] Keep existing string helpers (`catalog_pos_from_bt_pos`, …) delegating to seeded codes
- [ ] Tests for unmapped wordclass → `None`; unknown BT POS → `ValueError`

---

## Task 5: Dictionary write path

**Files:**
- Modify: `wyrdcraeft/services/dictionary/sinks.py`
- Modify: `wyrdcraeft/services/dictionary/editorial_merger.py`
- Modify: `wyrdcraeft/services/dictionary/query.py`
- Modify: `wyrdcraeft/models/dictionary.py` (if consolidated entry model exposes headword fields)
- Test: `tests/dictionary/test_sinks.py`, `tests/dictionary/test_query_service.py` (extend)

- [ ] Sink resolves `entry.pos.value` → `pos_id` before insert
- [ ] Persist `headword` only (from macronized value); do not write `headword_raw`
- [ ] Query service joins `parts_of_speech` for display; API payloads keep user-facing POS strings
- [ ] Update tests/golden fixtures expecting `headword_raw` / `headword_macronized` column names

---

## Task 6: Catalog assignment write path

**Files:**
- Modify: `wyrdcraeft/services/morphology/catalog/assigner.py`
- Modify: `wyrdcraeft/services/morphology/catalog/query.py`
- Test: `tests/morphology/test_lemma_morph_assignment.py`, `tests/morphology/test_morph_catalog.py`

- [ ] Assigner upserts `lemma_morph_classes` with `pos_id` not text `pos`
- [ ] `lookup_lemma_class` accepts POS string at API boundary, resolves to `pos_id` internally
- [ ] Tests still pass for `stán`, participial lemmas, verb `paraID` assignment

---

## Task 7: Morphology build hook — ensure reference seed

**Files:**
- Modify: `wyrdcraeft/cli/morphology.py` (or catalog loader)
- Test: `tests/test_cli_morphology.py` (extend if needed)

- [ ] Call `ensure_parts_of_speech` + `ensure_inflection_codes` during morphology build
  (after `upgrade_canonical_db`, before assignment) — idempotent
- [ ] Fresh DB after migration has reference rows without manual step

---

## Task 8: Docs + architecture stub

**Files:**
- Modify: `CONTEXT.md` (glossary only — `parts of speech`, `inflection code`)
- Modify: `doc/source/architecture/index.rst` (add `PARTS_OF_SPEECH`, `INFLECTION_CODES` entities;
  note `bt_entries.pos_id` — full ER refresh deferred to Phase D)

- [ ] Glossary entries only; no implementation prose in `CONTEXT.md`

---

## Phase A validation

```bash
.venv/bin/ruff check wyrdcraeft/models/reference.py wyrdcraeft/services/morphology/catalog/pos_seed.py wyrdcraeft/services/morphology/catalog/pos.py wyrdcraeft/services/dictionary/sinks.py wyrdcraeft/models/sqlalchemy.py wyrdcraeft/models/morph_catalog.py
.venv/bin/mypy wyrdcraeft/models/reference.py wyrdcraeft/services/morphology/catalog/pos_seed.py wyrdcraeft/services/morphology/catalog/pos.py wyrdcraeft/services/dictionary/sinks.py wyrdcraeft/models/sqlalchemy.py wyrdcraeft/models/morph_catalog.py
make napoleon-gate
.venv/bin/pytest tests/morphology/test_pos_seed.py tests/morphology/test_morph_catalog_pos.py tests/morphology/test_morph_catalog.py tests/morphology/test_lemma_morph_assignment.py -q
.venv/bin/pytest tests/dictionary -q
.venv/bin/pytest tests/morphology -m "not morphology_full" -q
git diff --exit-code -- tests/morphology/data/refactor_baseline.json
```

Manual:

```bash
WYRDCRAEFT_APP_DATA_DIR=/tmp/wc-phase-a .venv/bin/wyrdcraeft dictionary build --limit 100
sqlite3 /tmp/wc-phase-a/wyrdcraeft.sqlite3 "SELECT code FROM parts_of_speech LIMIT 5;"
sqlite3 /tmp/wc-phase-a/wyrdcraeft.sqlite3 "SELECT headword, pos_id FROM bt_entries LIMIT 5;"
```

---

## Phase A — Gate A: Spec review checklist

- [ ] `parts_of_speech` + `inflection_codes` exist and are seeded
- [ ] No free-text `pos` on `bt_entries`, `morph_classes`, `lemma_morph_classes`
- [ ] `headword_raw` dropped; `headword_macronized` renamed to `headword`
- [ ] `forms` table unchanged
- [ ] Lexicon tables unchanged

---

## Phase A — Gate B: Code review checklist

- [ ] Migrations backfill all existing rows (no NULL `pos_id` on required tables)
- [ ] Dictionary tests green; morphology assignment tests green
- [ ] `refactor_baseline.json` unchanged
- [ ] No real app-data writes in tests without isolation fixture

---

## Phase A — Commit

```bash
git add wyrdcraeft/etc/morphology/parts_of_speech_seed.json \
        wyrdcraeft/etc/morphology/inflection_codes_seed.json \
        wyrdcraeft/models/reference.py \
        wyrdcraeft/services/morphology/catalog/pos_seed.py \
        wyrdcraeft/db/alembic/versions/20260706_01_parts_of_speech_and_dictionary_pos.py \
        <other touched files>
git commit -m "$(cat <<'EOF'
Normalize schema phase A: parts_of_speech and dictionary POS FKs.

Seed reference POS and inflection-code tables; migrate bt_entries,
morph_classes, and lemma_morph_classes to pos_id; rename headword and
drop persisted headword_raw.
EOF
)"
```
