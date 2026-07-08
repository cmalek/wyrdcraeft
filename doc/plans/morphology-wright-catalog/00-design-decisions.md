# Morphology Wright Catalog — Design Decisions

Glossary-only domain terms. Implementation details live in phase plans and
`docs/adr/0002-normalized-canonical-schema.md`.

## Problem

Dictionary and morphology workflows need stable linguistic classification:

- Paradigm / morph class (modern label)
- Wright § mapping and (eventually) § text
- Bibliographic sourcing
- Lemma-level assignment independent of unreliable legacy `forms.paradigm`, `forms.paraID`, `forms.wright`

Legacy `forms.wright` copies Bosworth-Toller dictionary cross-refs; **~87% of inflectable dict entries have NULL Wright**. Assignment cannot depend on that column.

The canonical schema also duplicated data: free-text POS labels in multiple
vocabularies, denormalized Wright/paradigm strings on every form row, and
lexicon read-model tables that copied `bt_*` and `forms` rows for browse.

## Canonical terms

| Term | Meaning |
|------|---------|
| **morph class** | Reusable Old English inflection class (e.g. masculine a-stem noun, strong verb class 3) |
| **class_key** | Stable dot-id string (`noun.masculine.a_stem`); business key, not DB PK |
| **wright section** | Numbered paragraph in Wright & Wright (*Old English Grammar*) |
| **lemma assignment** | Mapping `(normalized_title, pos)` → one assignable morph class |
| **catalog** | Reference tables loaded from `wright_paradigms.json`; no lemma links in Phase 1 |
| **parts of speech** | Single reference table; canonical POS codes (`noun`, `verb`, `adjective`, …) used by all product FKs |
| **inflection code** | Compact morphology function tag on a form row (`SgFeNo`, `PaInSg2`, `Po`, …); scoped to one POS |
| **search index** | Derived `search_keys` rows for ranked lemma/stem/form browse lookup; not a duplicate of dictionary or morphology tables |
| **orphan form** | Morphology form whose `entry_id` is NULL because the normalized-title join is ambiguous or unmatched |
| **legacy form strings** | Denormalized generator columns on `forms` (`wright`, `paradigm`, `paraID`, `wordclass`, `function`, `class1`–`class3`) scheduled for removal after FK migration |

### Legacy column meanings (do not conflate)

| Legacy field | Meaning |
|--------------|---------|
| **`forms.wright`** | Bosworth-Toller cross-ref § numbers from the dict file; not a morph-class FK |
| **`forms.paraID`** | Verb paradigm template id from `para_vb.txt`; generation mechanic, not Wright catalog |
| **`forms.paradigm`** | Noun declension exemplar or verb paradigm label string from the generator |
| **`forms.class1`–`class3`** | Generator subclass parameters (verb class, noun pattern, adjective strong/weak); not `morph_classes` |

## Entity model (reference + dictionary + morphology)

```text
parts_of_speech ──< bt_entries
                ──< forms (wordclass_id)
                ──< morph_classes
                ──< lemma_morph_classes
                ──< inflection_codes

inflection_codes ──< forms (inflection_code_id)

morph_sources ──< morph_class_sources >── morph_classes ──< morph_class_wright_sections >── wright_sections

lemma_morph_classes (normalized_title, pos_id) → morph_classes.id
forms (morph_class_id, entry_id) → denormalized / optional dictionary link

bt_entries ──< bt_senses
           ──< bt_variants
           ──< forms.entry_id (nullable)

bt_entries ──< search_keys
forms      ──< search_keys
```

- **`parts_of_speech`**: int PK, unique canonical `code` (`noun`, `verb`, `adjective`, `adverb`, `pronoun`, `numeral`, `unknown`, closed-class rows, …). All product POS columns are FKs to this table; no alias columns on other tables.
- **`inflection_codes`**: int PK, unique `code`, `pos_id` FK, optional `display_json` for browse grids.
- **`morph_classes`**: int PK, unique `class_key`, `pos_id` FK, display fields, JSON for `paradigmatic_words`, `aliases`, `features`.
- **`wright_sections`**: PK = `section_no`; `section_text` nullable until Phase 4.
- **`bt_entries`**: `headword` (macronized display), `normalized_title`, `pos_id` FK; no persisted `headword_raw`.
- **`forms`**: linguistic surface fields plus FKs (`wordclass_id`, `inflection_code_id`, `morph_class_id`, `entry_id`); materialized `*_key` search columns kept at insert time.

## Assignment model (Phase 2+)

```text
lemma_morph_classes (normalized_title, pos_id) → morph_classes.id
```

- **POS on assignment rows** = `parts_of_speech.id` referencing the same canonical codes as `morph_classes.pos_id`.
- Map at build/ingest edges only: BT `adj` → `adjective`; generator `participle` → **`adjective`** for participial morph-class assignment.
- **Verbal participles** (`wordclass=verb`, inflection `PsPt`/`PaPt`) inherit verb lemma assignment.
- **Declined participial lemmas** (separate title from `build_participle_adjective`, e.g. `berende`) get `(title, adjective)` → `adj.present_participle` or `adj.past_participle`.
- **`forms.morph_class_id`**: copy lemma assignment during morphology build; NULL when unassigned (denormalization for query performance, not a second source of truth).

## Dictionary ↔ morphology link

- **`forms.entry_id`**: FK to `bt_entries.id`, populated at morphology build using the same normalized-title join policy as today's lexicon build.
- **NULL when ambiguous**: multiple dictionary entries match `(normalized_title, pos)` — homographs stay explicit; browse may still surface all matches via search keys.
- Not a composite FK on `(normalized_title, pos_id)` — join policy and POS mapping remain application concerns.

## Search / lexicon read model

- **Eliminate** `lexicon_entries` and `lexicon_forms` (duplicates of `bt_*` and `forms`).
- **Keep** a slim derived **`search_keys`** table (renamed from `lexicon_search_keys`) with rank tiers and key kinds.
- **Rename** `lexicon_build_meta` → `search_build_meta`.
- **Keep CLI** `wyrdcraeft lexicon build`; it rebuilds the search index only. `wyrdcraeft lexicon browse` reads source tables plus catalog joins directly.
- FTS5 remains a future option if profiling shows benefit; not part of the initial normalization migration.

## Normalized schema decisions (locked, 2026-07-06)

| # | Decision |
|---|----------|
| 1 | `parts_of_speech` is the single POS source of truth; all product POS columns are FKs |
| 2 | `forms.entry_id` NULL when homograph join is ambiguous |
| 3 | Flat `inflection_codes` + `forms.inflection_code_id` (not a column named `pos`) |
| 4 | Drop `lexicon_entries` / `lexicon_forms`; keep slim `search_keys` |
| 5 | `forms.morph_class_id` denormalized at morphology build |
| 6 | Keep materialized `*_key` columns on `forms` |
| 7 | Two-step `forms` migration: FKs first, legacy strings dropped later |
| 8 | Keep `wyrdcraeft lexicon build` command; scope = search index only |
| 9 | Rename `lexicon_search_keys` → `search_keys`, `lexicon_build_meta` → `search_build_meta` |
| 10 | `bt_entries` headword rename + `pos_id` in the same migration as `parts_of_speech` seed |

ADR: `docs/adr/0002-normalized-canonical-schema.md`

## Normalized schema rollout (Phases A–D)

Implementation plan (subagent orchestration, gates, commits):
[`doc/plans/normalized-canonical-schema/README.md`](../normalized-canonical-schema/README.md)

| Phase | Delivers |
|-------|----------|
| **A — Reference + dictionary** | Seed `parts_of_speech`, `inflection_codes`; `bt_entries.pos_id`, `headword` rename, drop `headword_raw`; `lemma_morph_classes` and `morph_classes` use `pos_id` |
| **B — Forms FKs (legacy strings remain)** | Add `wordclass_id`, `inflection_code_id`, `morph_class_id`, `entry_id`; populate in morphology sink; verify against legacy columns |
| **C — Lexicon shrink** | Drop `lexicon_entries` / `lexicon_forms`; rename search tables; rewrite `rebuild_lexicon()` to search-keys-only; browse reads `bt_*` + `forms` |
| **D — Legacy string drop** | Drop legacy `forms` string columns; refresh snapshots and architecture ER diagram |

Phases 1–4 of the Wright catalog plan (reference catalog, lemma assignment,
form link, Wright text ingest) remain valid; Phase B above aligns with catalog
Phase 3 (`forms.morph_class_id` and related FK work).

## Gap-fill priority (Phase 2 assignment)

1. Paradigm exemplar map (`stán` → class)
2. Verb `paraID` → `class_key`
3. Dict POS/gender/class flags + `features` on morph class
4. Wright § intersection (inflection § only; tie-break)
5. Manual curation (`assignment_source=manual`, `confidence=100`)

## Explicit non-goals

- `BTEntryMorphClass` table (use `lemma_morph_classes` instead)
- FK from `class1`–`class3` to `morph_classes` (generator params, not catalog class)
- `paradigm_templates` table in the initial normalization migration (verb `paraID` stays generator input)
- Replacing `search_keys` with FTS5 in the first normalization pass
- Changing morphology generation parity / `refactor_baseline.json` until Phase D
- Reformatting bundled morphology input files (`dict_*.txt`, `manual_forms.txt`) — mapping stays at build boundary

## Catalog load behavior

- On `morphology build`, after `upgrade_canonical_db`: if catalog empty → seed from packaged fixture.
- If populated → skip (idempotent).
- `--refresh-catalog` → delete catalog rows (or upsert) and reload fixture.

## References

- ADR: `docs/adr/0002-normalized-canonical-schema.md`
- Fixture: `wyrdcraeft/etc/morphology/wright_paradigms.json` (113 classes, 196 unique §)
- JSON Schema: `wyrdcraeft/etc/morphology/wright-morphology-fixture.schema.json`
- Wright text source: `data/sources/wright.md`
- Prior per-PoS JSON (to retire): `wyrdcraeft/etc/morphology/wright_*_paradigm_mapping.json`
