# wyrdcraeft Context

## Mission

`wyrdcraeft` is a Python toolkit for processing Old English source material into
structured outputs and supporting reference workflows around that text.

Primary capabilities:

- ingest and convert source texts into structured document JSON
- restore and disambiguate diacritics
- build and query Old English morphology
- index and query Bosworth-Toller dictionary data
- browse dictionary entries with linked morphology via `dictionary browse`
- run Old English OCR workflows for source PDFs
- prepare Bosworth-Toller JP2 scan witnesses into OCR-ready tiles and
  provenance manifests (library-first)
- load configuration for CLI and service behavior

## Boundary

This repo is one product context: Old English text-processing workflows.

In scope:

- source ingestion from text, TEI, and OCR-derived text
- morphology generation and lookup
- dictionary indexing and lookup
- dictionary browse: query-time headword and variant search over Bosworth-Toller with morphology sidebar
- diacritic restoration and curation
- OCR pipeline support for Old English PDFs
- BT-specific JP2 witness preparation for dense dictionary scans
- CLI-first workflows with Python entrypoints underneath

Out of scope:

- general-purpose NLP platform work
- generic OCR framework design
- broad lexicography tooling beyond Bosworth-Toller integration
- arbitrary document-conversion support with no Old English focus

## Capability Map

| Capability | Main CLI surface | Primary Python entrypoints |
|-------|----------|----------|
| ingest | `wyrdcraeft source convert` | `wyrdcraeft.ingest.pipeline.DocumentIngestor` |
| diacritic | `wyrdcraeft source mark-diacritics`, `wyrdcraeft diacritic`, `wyrdcraeft diacritic-disambiguate` | `wyrdcraeft.services.markup.DiacriticRestorer` |
| morphology | `wyrdcraeft morphology query` | `MorphologyQueryService`, `MorphologyCatalogQueryService` |
| dictionary | `wyrdcraeft dictionary build` (unified), `wyrdcraeft dictionary query`, `wyrdcraeft dictionary browse`, `wyrdcraeft dictionary ingest-wright-text`, `wyrdcraeft dictionary audit-wright` | `wyrdcraeft.services.dictionary.pipeline.BTIndexPipeline`, `BTQueryService`, `DictionaryBuildPipeline`, `DictionaryBrowseQueryService`, `DictionaryBrowseApp`, `WrightSectionTextScreen`, `WrightSectionTextIngester`, `WrightAuditService`, `form_decode`, `OldEnglishSearchInput` |
| ocr | `wyrdcraeft ocr old-english`, `wyrdcraeft ocr proxy` | `wyrdcraeft.services.ocr.run_old_english_ocr_pipeline` |
| bt witness prep | library-first (no dedicated CLI yet) | `wyrdcraeft.services.ocr.bt_witness_prep.prepare_pages` |
| settings | `wyrdcraeft settings` plus global CLI flags | `wyrdcraeft.settings.Settings` |

## Canonical Terms

- source text: raw input text, local file or supported remote source
- lossless source-grounded AST: first-pass Bosworth-Toller parse output that
  preserves source order, source text, and fragment boundaries before any
  normalization or cleanup; later views may derive normalized dictionary data
  from it
- typed source fragment: one contiguous span from a dictionary source block
  classified as a concrete source role such as headword, grammar, sense label,
  gloss, attestation, editorial note, etymology, cross-reference, or explicit
  unclassified remainder; together these fragments must account for all source
  text in order
- source witness: one concrete textual or image-backed source for a
  Bosworth-Toller entry, such as current OCR text, corrected digital text,
  scanned page image, or human correction layer
- markdown witness: verbatim OCR output retained in Markdown form as a source
  witness, with any block or span structure derived from it stored separately
  so model-emitted formatting cues do not become canonical facts by accident
- witness provenance: metadata attached to a source witness recording where it
  came from, how it was produced, and how it maps to entry fragments, so built
  entries retain raw supporting text instead of only normalized fields
- witness-first review: human adjudication workflow that shows raw source
  witnesses before or alongside parsed output, so reviewers can validate parser
  claims against evidence instead of trusting normalized fields alone
- page-region-line anchor: primary alignment scaffold for Bosworth-Toller
  witness comparison, where scans, OCR outputs, and derived text blocks are
  first tied to page, region, and line coordinates before headword or sense
  extraction
- case bundle: file-first prototype package for one difficult dictionary case,
  containing source images, raw witnesses, anchor data, fragment adjudications,
  and exported entry output without requiring database storage
- starter case bundle: current in-repo prototype bundle under
  `data/bt_cases/wesan/`, seeded to make the first Bosworth-Toller
  lossless-first workflow concrete before broader parser work
- shareable structured data: output and intermediate artifacts designed so
  engineers and researchers can inspect, diff, reuse, and cite them outside the
  product runtime; file-first bundles are preferred early because they travel
  well across tools and institutions
- adjudication overlay: human-authored YAML layer applied on top of machine
  generated witness and parse JSON, preserving original output while recording
  corrections, accept/reject decisions, fragment edits, and review notes in a
  diffable form
- BT dictionary structuring workflow: operator workflow for Bosworth-Toller
  OCR structuring that starts from witness gathering, anchoring, raw fragment
  sequencing, and overlay-based review inside a case bundle rather than going
  straight to final dictionary rows; documented in
  `doc/source/runbook/bt_dictionary_structuring_workflow.rst`
- BT JP2 witness preparation: library-first Bosworth-Toller slice that turns
  immutable JP2 scan pages into conservative preprocessed pages, overlapping
  four-tile OCR witnesses, quality-scored manifests, and page-region anchor
  seeds; stops before OCR text becomes canonical truth; entrypoint
  `wyrdcraeft.services.ocr.bt_witness_prep.prepare_pages`; docs in
  `doc/source/overview/bt_ocr_witness_preparation.rst` and
  `doc/source/overview/bt_ocr_witness_preparation_method.rst`
- document JSON: normalized structured output produced by ingestion
- deterministic ingest: heuristic extraction path that does not call an LLM
- TEI ingest: direct TEI/XML parsing path
- LLM ingest: extraction path using configured LLM settings
- macron index: JSON payload used by diacritic tools for normalized-to-display mappings
- morphology generation: SQLite lookup index production workflow for inflected
  forms (optional TSV via `--output`); typically triggered by
  `dictionary build --with-morphology` or automatically when `forms` is empty
- build command: standard subcommand name for long-running database-producing
  workflows; `dictionary build` is the primary entrypoint for unified indexing
- canonical database: the one app-data `wyrdcraeft.sqlite3` file that holds
  morphology (`forms`), attached dictionary (`bt_*`), and Wright morph catalog
  tables for the product's lookup workflows
- morphology index: morphology data stored inside canonical `wyrdcraeft.sqlite3`
  database rather than a standalone morphology-only file
- dictionary index: attached `bt_*` tables inside canonical `wyrdcraeft.sqlite3`
- dictionary SQLAlchemy slice: Phase 6 migration that moved `bt_*` writes and
  reads from direct `sqlite3` code to SQLAlchemy-backed persistence/query paths
- morphology SQLAlchemy slice: Phase 7 migration that moved `forms` writes and
  reads from direct `sqlite3` code to SQLAlchemy Core bulk insert plus
  SQLAlchemy query paths while preserving emitted ordering semantics
- dictionary browse: Textual shell for query-time dictionary search plus
  morphology sidebar details for the selected entry
- dictionary browse search: 12-tier headword-and-variant ranking ladder
  implemented by `DictionaryBrowseQueryService` querying `bt_entries` and
  `bt_variants` directly; no derived search-index tables
- normalized forms schema: Phase D (Alembic `20260706_04`) dropped legacy
  denormalized string columns from `forms` (`wordclass`, `function`, `wright`,
  `paradigm`, `paraID`, `class1`–`class3`). Persisted morphology metadata uses
  foreign keys (`wordclass_id`, `inflection_code_id`, `morph_class_id`,
  `entry_id`) plus materialized `*_key` lookup columns; product read paths join
  `parts_of_speech`, `inflection_codes`, and `morph_classes` for labels
- dictionary build: primary unified build command that rebuilds `bt_*`
  tables, relinks `forms.entry_id`, and optionally regenerates morphology
  when requested or when the `forms` table is empty
- dictionary source block: one contiguous Bosworth-Toller headword entry in
  source order, including its main text and any uniquely targetable editorial
  follow-ons; this is canonical identity for one `bt_entries` row
- dictionary homograph entry: distinct Bosworth-Toller entry sharing spelling
  and part of speech with another entry but preserving a different meaning set;
  homographs stay as separate dictionary source blocks rather than being merged
- sense path: machine-only hierarchical identifier for one dictionary sense
  such as `1`, `1.2`, or `2.1`; preserves parent/child sense structure while
  dropping literal Bosworth-Toller labels like `I.` or `IVa.` from canonical
  product output
- source label raw: original Bosworth-Toller sense marker such as `I.` or
  `IVa.` retained only for debugging and provenance; not canonical product
  output and not used for normal query display
- source fragment raw: exact raw source substring for one parsed sense before
  attestation stripping and cleanup; retained for debugging and provenance
- prefix fragment raw: raw leading fragment for one sense before the core gloss,
  used to classify modifiers, grammatical context, and usage notes
- sense modifier: controlled-vocabulary qualifier attached to one sense, such
  as `intransitive`, `transitive`, `weak`, `indeclinable`, or
  `interrogative`; modifiers stay separate from `gloss_en`, and grammatical
  debris like gender or case markers should be dropped rather than stored as
  modifiers
- usage note: free-text note attached to one sense for longer construction or
  scope phrases such as `with dative of person`, `in the phrase`, `of persons`,
  or `as ecclesiastical term`; this stays outside the controlled modifier
  vocabulary
- entry_id relink: post-build step in the unified dictionary pipeline that
  populates `forms.entry_id` foreign keys by joining morphology lemmas to
  newly indexed dictionary entries
- norm_key: diacritic-stripped normalized Old English key used for generic
  dictionary lookup and deduplication
- normalized_title: macron- and dot-preserving normalized lemma/headword title
  used to join morphology ``forms`` rows with Bosworth-Toller ``bt_entries``
  and ``bt_variants`` at dictionary build / relink time; distinct from ``norm_key``, which
  strips combining marks
- normalized title join index: in-memory maps built at join time to match
  morphology lemma titles to dictionary entries using macron-preserving
  normalized titles, direct entry hits, and POS-aware variant fallbacks
- resolve_one / resolve_all: shared join policies over the same tier order;
  ``resolve_one`` picks a single dictionary entry when the tier policy yields
  one unambiguous match, while ``resolve_all`` returns every matching entry id
  for dictionary browse and multi-hit lookups
- dictionary browse search normalization: user queries use
  ``normalize_old_english``, ``normalize_morphology_title``, and
  ``BTSpellingNormalizer`` consistently with dictionary indexing so
  undiacritized input like ``abbod`` matches macronized headwords; form-to-entry
  linking uses ``forms.entry_id`` (populated after dictionary build via
  ``FormsEntryRelinker``), and browse resolves entry and morphology details from
  ``bt_*``, ``forms``, and reference joins at query time
- parts of speech: canonical reference row naming the grammatical class of a
  lemma or dictionary entry (noun, verb, adjective, and related closed classes)
- parts of speech: canonical `parts_of_speech` reference table; single POS
  source of truth; product tables store `pos_id` / `wordclass_id` foreign keys
- morphology function code: compact generator tag (for example `PaInSg2`,
  `PlNeAc`) naming tense, mood, case, gender, number, degree, or other
  inflectional dimensions depending on part of speech; persisted on `forms` as
  `inflection_code_id`, not as a free-text column
- inflection code: normalized `inflection_codes` lookup row pairing one
  morphology function code with its part-of-speech class; resolved at morphology
  build and joined at query time via `forms.inflection_code_id`
- Wright morph catalog: reference tables in canonical SQLite seeded from
  `wyrdcraeft/etc/morphology/wright_paradigms.json` (113 morph classes, Wright
  § links, bibliographic sources); auto-seeded during dictionary build morphology
  regeneration when empty
- morph class: reusable Wright inflection class row in `morph_classes` keyed by
  dot-id `class_key` (for example `noun.masculine.a_stem`)
- lemma morph assignment: `lemma_morph_classes` row mapping
  `(normalized_title, pos_id)` to `morph_classes.id`; produced during morphology
  build after paradigm assigners
- ParadigmClassMapper: resolves generator paradigm labels and verb `paraID`
  values to catalog `class_key` via fixture exemplars and `para_vb.txt`
- MorphClassView: read-only DTO from `lookup_lemma_class()` with class metadata,
  ordered Wright § numbers, and source citations
- LemmaMorphClassSummary: browse-oriented morph-class payload on
  `EntryDetails.morph_class` (display label, provenance, Wright § list, or
  explicit `Unclassified`)
- Wright section text ingest: explicit `dictionary ingest-wright-text` command
  that parses `§ N` headings from markdown into `wright_sections.section_text`
  (idempotent; `--force` overwrites); not run automatically on build
- Wright legacy audit: report-only `dictionary audit-wright` command comparing
  bundled source `wright` fields to deterministic `lemma_morph_classes`
  assignments; optional `--json`; never rewrites source files
- browse morph-class block: dictionary detail pane shows catalog class label,
  assignment provenance, and selectable Wright § citations via join-at-read-time
  lookup
- morphology table: browse sidebar view that expands function codes into
  POS-aware paradigm grids (verb/noun/adjective/pronoun) filtered to the
  headword's part of speech; falls back to a flat table when no grid applies
- paradigm grid: case-by-number or person-by-number table built from morphology
  function codes; instrumental forms use code `Is` displayed as `Inst`
- lexical distance: Levenshtein distance between normalized query and candidate
  text; dictionary browse uses it to sort search results after rank tier
- Old English search bar: dictionary browse input (`OldEnglishSearchInput`) with
  keyboard entry as the primary path; optional character bar below the field
  inserts æ/þ/ð, macrons, and dotted letters when the terminal cannot type them
- dictionary query: CLI name for consolidated Bosworth-Toller lookup by lemma
  or variant; `dictionary lookup` remains a hidden deprecated alias
- editorial target warning: build-time diagnostic emitted when an Add / Dele /
  Substitute line cannot be attached to one unique dictionary source block; the
  product should write the miss to `parse_warnings.jsonl` and `bt_edit_log`
  rather than guessing across ambiguous homographs
- startup database readiness: mandatory startup step that ensures canonical
  `wyrdcraeft.sqlite3` exists at expected schema before any DB-using command
  reads or writes it
- pre-migration backup: one retained full-copy backup of the canonical
  `wyrdcraeft.sqlite3` created immediately before Alembic upgrades or
  destructive legacy resets
- migration backup prompt: next-invocation interactive cleanup prompt for a
  retained migration backup, asking whether to delete it only after the user
  has successfully used `wyrdcraeft` since the last migration
- migration decision path: clear startup narration showing why migrations are
  or are not being applied, what legacy condition was detected, and what stage
  is currently running
- legacy pre-Alembic database: older canonical SQLite database with product
  tables but no `alembic_version`; current policy may back it up, delete it,
  recreate it from migrations, and require rebuild commands for generated data
- legacy morphology filename: older `morphology.sqlite3` file from before the
  canonical rename to `wyrdcraeft.sqlite3`; current policy treats it as legacy
  input, backs it up, resets to fresh canonical DB, stops, and prints rebuild
  commands instead of trying in-place rename or migration
- POS inference: dictionary build step that fills empty dictionary POS from
  unambiguous morphology `wordclass_id` when one clear mapping exists
- dictionary browse startup progress: live stderr progress while opening browse
  tables before the Textual shell appears
- OCR proxy: local OpenAI-compatible proxy used to clamp and normalize OCR model traffic
- app-data directory: OS-specific writable directory for default SQLite outputs

## Current Migration Progress

- canonical DB migration plan completed under
  `docs/superpowers/plans/2026-06-30-wyrdcraeft-canonical-db-migration.md`
  with orchestration handoff at
  `docs/superpowers/specs/2026-06-30-wyrdcraeft-db-migration-orchestration.md`
- **Phases 1–8 complete** as of 2026-07-03
- **Follow-on lexicon work on `codex/canonical-db-migration`:**
  - Slice 1 **complete** (`64c6223`): lexicon rebuild on SQLAlchemy Core,
    Alembic-owned lexicon DDL, truncate-not-drop rebuild, `SCHEMA_VERSION`
    staleness removed; handoff at
    `docs/superpowers/handoffs/2026-07-03-lexicon-slice1-session-state.md`
  - Slice 2 **complete** (`564e927`): shared `NormalizedTitleJoinIndex`
    unifies morphology↔dictionary joins; removed duplicated join SQL from
    dictionary build paths and `BTQueryService`; plan at
    `docs/superpowers/plans/2026-07-03-lexicon-sqlalchemy-normalized-title-join.md`
- Phase 1 (`fa34e5f`): canonical `wyrdcraeft.sqlite3` path and shared DB base
- Phase 2 (`b21d0a4`): Alembic startup runtime, backup/restore, readiness gate
- Phase 3 (`914a4bb`): initial Alembic-managed canonical schema (includes
  search-index tables; `lexicon_entries` / `lexicon_forms` removed in Phase C)
- Phase 4 (`7b07991`): renamed DB-producing commands to `build`; removed old
  per-command DB-path overrides and standalone dictionary mode
- Phase 5 (`82b1479`): moved lexicon query/bootstrap helpers to SQLAlchemy
  models against Alembic-managed tables; removed old lexicon-only ad hoc schema
  migration path (lexicon **rebuild** still used raw `sqlite3` until Slice 1)
- Phase 6 (`81e2db4`): moved dictionary persistence/query to SQLAlchemy,
  removed stale standalone dictionary fallout from tests, kept canonical DB
  product behavior, and preserved direct non-CLI scratch sink behavior for
  pipeline/tests
- Phase 7 (`f805b46`): moved morphology persistence/query to SQLAlchemy,
  replaced raw `sqlite3` in `SqliteIndexSink` and `MorphologyQueryService`
  with Core bulk insert and SQLAlchemy `text()` lookups, preserved
  `ORDER BY counter ASC, id ASC`, and kept dictionary attach/join behavior
  inside canonical `wyrdcraeft.sqlite3`
- Phase 8 (`86ec4ac`): documented and verified the full canonical DB migration
  flow, added orchestration handoff spec, refreshed README/command docs, and
  passed focused end-to-end migration tests plus mypy and napoleon-gate
- Post–Phase 8 (`c651f32`): added macron-preserving `normalized_title` join
  columns on `forms`, `bt_entries`, and `bt_variants` (Alembic
  `20260703_01`); join logic now centralized in `NormalizedTitleJoinIndex`
- **Morphology build performance** (`2515ab8`, 2026-07-03/04): batched
  SQLAlchemy Core inserts (25K rows) with bulk-load PRAGMAs; O(n) adj/noun
  paradigm assignment; SQLite-only default build (`--output` optional for TSV);
  `--profile` stage timing via `MorphologyBuildProfiler`; refactored
  comparative/superlative adj emission hot path; adj-only cProfile script at
  `scripts/morphology/profile_adj_stage.py`; handoff at
  `doc/sessions/2026-07-03-morphology-build-performance.md`. Full build wall
  time reduced from ~45m toward ~10–11m (user-measured; run variance applies).
  Deferred index drop/recreate was tried and reverted (regression). Remaining
  bottlenecks: adj-stage CPU (`print_one_form`/FormRow validation,
  `normalize_output`) and SQLite flush time during bulk insert.
- **Wright morph catalog Phase 1** (2026-07-04, commits `6249788`–`6e5ec18`):
  Alembic `20260704_01` catalog tables; `MorphologyCatalogLoader`; auto-seed
  on build; `--refresh-catalog`; session at
  `doc/sessions/2026-07-04-morphology-wright-catalog-phase1.md`
- **Wright morph catalog Phase 2** (2026-07-04, commits `0a66a51`–`b9b1d65`):
  `lemma_morph_classes` + `recognition_hints_json`; POS helpers; paradigm mapper;
  `LemmaMorphClassAssigner`; `MorphologyCatalogQueryService.lookup_lemma_class`;
  Gates A/B passed; session at
  `doc/sessions/2026-07-04-morphology-wright-catalog-phase2.md`.
- **Morph-class browse + Wright audit plan** (2026-07-04, commits
  `790785c`–`f126c38`; plan at
  `docs/superpowers/plans/2026-07-04-morph-class-browse-audit-implementation.md`):
  - **Phase 1** (`790785c`): dictionary browse detail shows catalog
    morph class, provenance, and Wright § list (or explicit `Unclassified`) via
    join-at-read-time; `LemmaMorphClassSummary` + shared display formatter
  - **Phase 2** (`06d9b92`): `WrightSectionTextIngester` +
    `dictionary ingest-wright-text`; `lookup_wright_section_text()` on catalog
    query service
  - **Phase 3** (`cba8785`): selectable Wright § list in browse detail;
    `WrightSectionTextScreen` modal reads SQLite text or shows ingest-needed
    message
  - **Phase 4** (`f126c38`): `WrightAuditService` +
    `dictionary audit-wright` (malformed legacy Wright, contradictions,
    unclassified, blank-but-classified); report-only v1
  - Session reports under `doc/sessions/task-phase{1,2,3,4}-*.md`
  - **Coverage gap:** bundled `data/sources/wright.md` currently has phonology
    §1–58 only; browse cites inflection §330+ until a fuller markdown corpus is
    ingested
- **Normalized canonical schema Phase C** (2026-07-06, through `a65e4a0`):
  dropped `lexicon_entries` / `lexicon_forms`; renamed `lexicon_search_keys` →
  `search_keys` and `lexicon_build_meta` → `search_build_meta` (later removed in
  Phase B). Plan at `doc/plans/normalized-canonical-schema/phase-c-lexicon-shrink.md`.
- **Unified dictionary workflow Phase B** (2026-07-07): dropped
  `search_keys` / `search_build_meta`; moved browse to `dictionary browse` with
  query-time 12-tier search; removed `lexicon` CLI group; moved Wright ingest/audit
  to dictionary; renamed `dictionary lookup` → `dictionary query`. Plan at
  `doc/plans/unified-dictionary-workflow/phase-b-dictionary-browse-and-cli.md`.
- **Normalized canonical schema Phase D** (2026-07-06, through `e686c74`):
  Alembic `20260706_04` dropped legacy `forms` string columns; morphology sink,
  query, dictionary build, and browse read POS, inflection, morph-class, and
  dictionary metadata via foreign keys and reference joins only. Architecture ER
  refreshed in `doc/source/architecture/index.rst`. Plan at
  `doc/plans/normalized-canonical-schema/phase-d-legacy-column-drop.md`.

## Key Flows

### Source conversion

`wyrdcraeft main:main` -> `wyrdcraeft.cli.cli:cli` -> `wyrdcraeft.cli.source:reading_convert` -> `DocumentIngestor.ingest` -> document JSON written to user path

### Morphology generation

`wyrdcraeft.cli.dictionary:build` (with `--with-morphology` or when `forms` is
empty) -> session/setup helpers -> paradigm assigners -> Wright catalog seed
(`MorphologyCatalogLoader.ensure_seeded`) -> lemma morph class assignment
(`LemmaMorphClassAssigner.assign_all`) -> generation dispatch -> optional TSV
sink and SQLAlchemy-backed batched `SqliteIndexSink` -> `forms` plus catalog
tables in `wyrdcraeft.sqlite3`. Default build is SQLite-only; pass `--output` for
TSV. Use `--profile` for stderr stage/setup/sqlite_flush timings. Use
`--refresh-catalog` to reload `wright_paradigms.json` into catalog tables.
Wright paragraph text is **not** ingested during build; run
`dictionary ingest-wright-text` separately when markdown corpus is ready.

### Dictionary indexing

`wyrdcraeft.cli.dictionary:build` -> `DictionaryBuildPipeline` or `BTIndexPipeline.run`
-> SQLAlchemy-backed dictionary sink -> attached `bt_*` tables in
`wyrdcraeft.sqlite3` -> `FormsEntryRelinker` repopulates `forms.entry_id`

### Dictionary browse

`wyrdcraeft.cli.dictionary:browse` -> startup progress ->
`DictionaryBrowseQueryService` (composes shared-engine
`MorphologyCatalogQueryService` for morph-class and Wright § text lookup) ->
Textual `DictionaryBrowseApp` with search bar at top, results pane left,
details plus POS-filtered paradigm grids right. Dictionary detail shows catalog
morph class / provenance / selectable Wright § citations; selecting a § opens
`WrightSectionTextScreen` modal from stored `wright_sections.section_text` or
an explicit ingest-needed message.

Prerequisite: canonical `wyrdcraeft.sqlite3` at Alembic head with populated
`bt_*` tables (from dictionary build) and `forms` rows (from
`dictionary build --with-morphology` or automatic regen when `forms` is empty).

### OCR workflow

`wyrdcraeft.cli.ocr:old_english_ocr` -> `run_old_english_ocr_pipeline` -> managed proxy / `olmocr` run -> normalized text and unknown-token report

### BT JP2 witness preparation

`prepare_pages(BTWitnessPrepInput)` -> enumerate JP2 pages -> conservative
preprocess -> fixed four-tile split (or explicit fallback) -> tile quality
scoring -> `manifests/pages.jsonl`, `manifests/tiles.jsonl`,
`anchors/anchor_seeds.jsonl`

Stage B recipe checks use
`scripts/ocr/benchmark_bt_witness_prep.py` plus helpers in
`wyrdcraeft.services.ocr.bt_witness_prep.validation`.

- Morphology generation writes real app-data `wyrdcraeft.sqlite3` by default
  through batched SQLAlchemy-backed `forms` persistence (25K-row bulk inserts
  with WAL/synchronous=OFF tuning); tests must use
  `isolated_morphology_app_data` or explicit temp paths.
- Morphology build no longer writes TSV unless `--output` is passed; the
  default artifact is the canonical SQLite index only.
- Use `wyrdcraeft dictionary build --with-morphology --profile` to print stage
  wall times, setup steps, and cumulative `sqlite_flush` seconds to stderr.
- Wright morph catalog seeds on first build when catalog tables are empty;
  `--refresh-catalog` forces reload from `wright_paradigms.json`.
- Lemma morph class assignment runs on dictionary-loaded lemmas before form
  generation; verb-generated participles added to `session.adjectives` during
  generation are not assigned until a later phase.
- Canonical morph-class truth is `lemma_morph_classes`, not legacy source
  `wright` cells; use `dictionary audit-wright` to report source-field quality.
- Wright section paragraph text requires explicit
  `dictionary ingest-wright-text`; bundled `data/sources/wright.md` currently
  covers phonology §1–58 only, so inflection §330+ citations show an ingest-needed
  message in browse until a fuller corpus is ingested.
- Morphology form rows store `morph_class_id` when assigned at build time;
  browse and query join `morph_classes` (and fall back to
  `lemma_morph_classes` lookup when the FK is NULL).
- Dictionary indexing now writes `bt_*` through SQLAlchemy-backed persistence
  into app-data `wyrdcraeft.sqlite3`; CLI/product flows still fail clearly when
  that canonical database is missing.
- Dictionary browse v1 is read-only; run `wyrdcraeft dictionary build` after
  dictionary source changes and ensure `forms` is current via
  `dictionary build --with-morphology`.
- Dictionary browse and build expect the canonical Alembic-managed schema;
  startup database readiness applies migrations before DB-using commands run.
- Dictionary browse search accepts direct keyboard entry of æ/þ/ð, macrons, and
  dotted letters when the search field is focused; the character bar below the
  field is a fallback for terminals that cannot emit those keys.
- Dictionary browse search results sort by rank tier, then lexical distance from
  the query string.
- Morphology sidebar shows only forms matching the headword POS and renders
  paradigm grids from inflection codes (via `inflection_code_id` joins);
  scrollable details and morphology panes share the right column below the
  search bar.
- OCR `--pages` is currently not supported in `olmocr` mode.
- BT JP2 witness prep is library-first and JP2-only; it does not mutate case
  bundles and does not treat OCR text as canonical truth. Non-standard pages
  must emit explicit fallback status instead of silent forced tiling.
- Diacritic workflows use packaged JSON/TXT data under `wyrdcraeft/etc/diacritic`.
- Settings docs in Sphinx are not always current; prefer code in `wyrdcraeft/settings.py` and CLI wiring in `wyrdcraeft/cli/cli.py`.
- TODO: add a real primary key or uniqueness constraint to `bt_variants` in a
  future schema migration; the initial canonical migration preserves the legacy
  table shape, which has no declared primary key.

## Context Docs

- [docs/context/ingest.md](docs/context/ingest.md)
- [docs/context/diacritic.md](docs/context/diacritic.md)
- [docs/context/morphology.md](docs/context/morphology.md)
- [docs/context/dictionary.md](docs/context/dictionary.md)
- [docs/context/ocr.md](docs/context/ocr.md)
- [docs/context/settings.md](docs/context/settings.md)

## ADRs

- [0001: Lexicon data lives in morphology.sqlite3](docs/adr/0001-lexicon-data-lives-in-morphology-db.md)
  — **historical**; superseded by the canonical `wyrdcraeft.sqlite3` migration
  (Phases 1–8) and the unified dictionary workflow (Phase B).
- [0004: BT OCR parsing starts with lossless source-grounded AST](docs/adr/0004-bt-ocr-parsing-starts-with-lossless-source-grounded-ast.md)
- [0005: BT source acquisition uses multi-witness download set](docs/adr/0005-bt-source-acquisition-uses-multi-witness-download-set.md)
- [0006: BT JP2 witness preparation is library-first](docs/adr/0006-bt-jp2-witness-preparation-is-library-first.md)

Additional architecture decision records live under `docs/adr/` when this repo
captures durable design decisions that should not be rediscovered from code.
