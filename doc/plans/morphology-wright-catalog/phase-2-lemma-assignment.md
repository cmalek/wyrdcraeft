# Phase 2 — Lemma Morph Class Assignment

> **Prerequisites:** Phase 1 gates passed  
> **REQUIRED SUB-SKILL:** subagent-driven-development

**Goal:** Assign each inflectable lemma `(normalized_title, pos)` to one `morph_classes` row using existing assigner output + new mapping tables; store provenance and confidence.

**Architecture:** New `lemma_morph_classes` table; extend morph catalog with `recognition_hints_json`; `MorphologyClassAssigner` (cohesive class) runs after existing noun/adj/verb assigners during build; paradigm exemplar + `paraID` maps in JSON or Python registries.

---

## Task 1: Schema + migration

**Files:**
- Create: `wyrdcraeft/db/alembic/versions/202607XX_02_lemma_morph_classes.py`
- Modify: `wyrdcraeft/models/morph_catalog.py`

- [ ] Add column `morph_classes.recognition_hints_json TEXT NOT NULL DEFAULT '{}'`
- [ ] Create `lemma_morph_classes`:
  - `id` INTEGER PK
  - `normalized_title` TEXT NOT NULL
  - `pos` TEXT NOT NULL — **`morph_classes.pos` vocabulary**
  - `morph_class_id` INTEGER FK → `morph_classes.id`
  - `assignment_source` TEXT NOT NULL DEFAULT `'rule'`
  - `confidence` INTEGER NOT NULL DEFAULT 100 (0–100)
  - `features_json` TEXT NOT NULL DEFAULT `'{}'`
  - `notes` TEXT NOT NULL DEFAULT `''`
  - UNIQUE (`normalized_title`, `pos`)
  - INDEX on `morph_class_id`, `normalized_title`

- [ ] Update fixture loader to populate `recognition_hints_json` from fixture

---

## Task 2: POS normalization helper

**Files:**
- Create: `wyrdcraeft/services/morphology/catalog/pos.py`
- Test: `tests/morphology/test_morph_catalog_pos.py`

- [ ] `catalog_pos_from_bt_pos(bt_pos: str) -> str` — map `adj`→`adjective`, `pron`→`pronoun`, etc.
- [ ] `catalog_pos_from_wordclass(wordclass: str) -> str | None` — map generator values; `participle`→`adjective`; return None for unmapped
- [ ] Tests for all generator `wordclass` values and all `BTPos` values used in joins

---

## Task 3: Paradigm exemplar registry

**Files:**
- Create: `wyrdcraeft/services/morphology/catalog/paradigm_map.py`
- Create: `wyrdcraeft/etc/morphology/paradigm_exemplar_map.json` (or derive from fixture `paradigmatic_words` + generator paradigm strings)
- Test: `tests/morphology/test_paradigm_map.py`

- [ ] Map generator paradigm strings → `class_key`:
  - Nouns: `stán`, `guma`, `word`, …
  - Verbs: `paraID` / `VerbParadigm.ID` → `class_key`
  - Adjectives: `glæd`, `blind`, `wilde`, …
  - Participial: title heuristics → `adj.present_participle` / `adj.past_participle`
- [ ] Document unmappable paradigms; return None (no assignment)

---

## Task 4: Assignment engine

**Files:**
- Create: `wyrdcraeft/services/morphology/catalog/assigner.py`
- Modify: `wyrdcraeft/cli/morphology.py` (invoke after assigners, before generation)
- Test: `tests/morphology/test_lemma_morph_assignment.py`

- [ ] `LemmaMorphClassAssigner` class:
  - Input: `list[Word]` post assigners, catalog DB connection
  - Output: rows in `lemma_morph_classes` (upsert by `(normalized_title, pos)`)
- [ ] Priority pipeline (design doc):
  1. Paradigm exemplar / `paraID`
  2. POS + gender + dict flags vs `morph_classes.features`
  3. Wright § intersect when `word.wright` not NULL (filter § ≥ 330)
  4. Skip if no match (`confidence=0` or no row — pick one strategy, document in test)
- [ ] Participles:
  - `(verb_lemma, verb)` from verb assignment
  - `(participle_title, adjective)` for adjective-sink lemmas with `pspart`/`papart`
- [ ] Use `normalize_morphology_title()` for keys

---

## Task 5: Read API

**Files:**
- Modify: `wyrdcraeft/services/morphology/catalog/query.py`

- [ ] `lookup_lemma_class(normalized_title, pos) -> MorphClassView | None`
- [ ] Include Wright § numbers, sources, `modern_class`, `wright_label`
- [ ] No lexicon UI yet (Phase 3)

---

## Phase 2 validation

```bash
.venv/bin/pytest tests/morphology/test_morph_catalog.py tests/morphology/test_lemma_morph_assignment.py -q
.venv/bin/pytest tests/morphology -m "not morphology_full" -q
git diff --exit-code -- tests/morphology/data/refactor_baseline.json
make napoleon-gate
```

Spot-check assignments:

- `stān` noun → `noun.masculine.a_stem`
- Strong verb with known `paraID` → expected verb class
- `berende`-style participle lemma → `adj.present_participle`

---

## Phase 2 — Gate A: Spec review

Verify:

- Assignment key is `(normalized_title, pos)` with catalog POS vocab
- No `forms.morph_class_id` yet
- Participles not collapsed into generic adjective without participial class
- `recognition_hints_json` loaded from fixture
- No `BTEntryMorphClass` table

## Phase 2 — Gate B: Code review

Standard bugbot + morphology test safety audit.

---

## Cleanup (optional same PR or follow-up)

- [ ] Mark `wright_*_paradigm_mapping.json` deprecated in module comment
- [ ] Add numeral morph classes to fixture when Wright mapping exists
