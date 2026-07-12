# Normalized canonical schema with unified parts of speech

Status: accepted

The canonical `wyrdcraeft.sqlite3` schema grew from legacy morphology TSV columns
and a derived lexicon read model that duplicated dictionary and morphology rows.
We decided to normalize product tables around reference lookups
(`parts_of_speech`, `inflection_codes`), declare real foreign keys on `forms`
and `bt_entries`, shrink the lexicon layer to a search index only, and drop
free-text POS and inflection labels from persisted tables.

**Considered options**

- Keep three parallel POS vocabularies (`bt_entries.pos`, `forms.wordclass`,
  `morph_classes.pos`) with Python mapping at query time only.
- Replace `lexicon_search_keys` with SQLite FTS5 in the same migration.
- Store morph class only on `lemma_morph_classes` and join at read time for
  every `forms` query.
- One-shot migration that drops legacy `forms` string columns immediately.

**Decision**

- **`parts_of_speech`** is the single POS source of truth. Product tables store
  `pos_id` / `wordclass_id` foreign keys only; legacy strings are mapped at
  build/ingest boundaries.
- **`inflection_codes`** is a flat lookup keyed by compact function codes
  (`SgFeNo`, `PaInSg2`, …) scoped by `pos_id`. `forms` stores
  `inflection_code_id`, not a column named `pos`.
- **`forms.entry_id`** links to `bt_entries` when the normalized-title join is
  unambiguous; **NULL** when homographs remain ambiguous.
- **`forms.morph_class_id`** denormalizes lemma assignment at morphology build;
  NULL when unassigned.
- **Keep** materialized `*_key` columns on `forms` for indexed morphology lookup.
- **Drop** `lexicon_entries` and `lexicon_forms`; **rename**
  `lexicon_search_keys` → `search_keys` and `lexicon_build_meta` →
  `search_build_meta`. Keep the CLI command `wyrdcraeft lexicon build`, but it
  rebuilds the search index only.
- **`bt_entries`**: rename `headword_macronized` → `headword`, drop persisted
  `headword_raw` (parse-time only).
- **Two-step** `forms` migration: add FK columns and populate first; drop legacy
  string columns (`wright`, `paradigm`, `paraID`, `wordclass`, `function`,
  `class1`–`class3`) only after consumers switch.

**Consequences**

- Alembic migrations and build pipelines must land together; there is no
  production backwards-compatibility requirement, but morphology parity tests
  and `refactor_baseline.json` still constrain generation output until legacy
  columns are removed.
- Generator source files (`dict_*.txt`, `para_vb.txt`, `manual_forms.txt`) keep
  legacy columns for now; Wright assignment continues to use dict `wright` and
  verb `paraID` at the ingest boundary until catalog assignment fully replaces
  them.
- `class1`–`class3` are generator subclass parameters, not morph-class keys;
  they do not become foreign keys to `morph_classes`.
- Browse and query services read dictionary and morphology source tables directly;
  only ranked search keys remain as a derived artifact.

See `doc/plans/morphology-wright-catalog/00-design-decisions.md` for glossary
terms and phased rollout (Phases A–D). Subagent plan:
`doc/plans/normalized-canonical-schema/README.md`.
