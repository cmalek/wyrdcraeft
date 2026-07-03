# wyrdcraeft Context

## Mission

`wyrdcraeft` is a Python toolkit for processing Old English source material into
structured outputs and supporting reference workflows around that text.

Primary capabilities:

- ingest and convert source texts into structured document JSON
- restore and disambiguate diacritics
- build and query Old English morphology
- index and query Bosworth-Toller dictionary data
- browse dictionary and morphology together via the lexicon workflow
- run Old English OCR workflows for source PDFs
- load configuration for CLI and service behavior

## Boundary

This repo is one product context: Old English text-processing workflows.

In scope:

- source ingestion from text, TEI, and OCR-derived text
- morphology generation and lookup
- dictionary indexing and lookup
- lexicon browse: unified lemma/stem/form search over morphology plus Bosworth-Toller
- diacritic restoration and curation
- OCR pipeline support for Old English PDFs
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
| morphology | `wyrdcraeft morphology build`, `wyrdcraeft morphology query` | `wyrdcraeft.services.morphology.generation.dispatch`, `MorphologyQueryService` |
| dictionary | `wyrdcraeft dictionary build`, `wyrdcraeft dictionary lookup` | `wyrdcraeft.services.dictionary.pipeline.BTIndexPipeline`, `BTQueryService` |
| lexicon | `wyrdcraeft lexicon build`, `wyrdcraeft lexicon browse` | `rebuild_lexicon`, `LexiconQueryService`, `LexiconBrowseApp`, `form_decode`, `OldEnglishSearchInput` |
| ocr | `wyrdcraeft ocr old-english`, `wyrdcraeft ocr proxy` | `wyrdcraeft.services.ocr.run_old_english_ocr_pipeline` |
| settings | `wyrdcraeft settings` plus global CLI flags | `wyrdcraeft.settings.Settings` |

## Canonical Terms

- source text: raw input text, local file or supported remote source
- document JSON: normalized structured output produced by ingestion
- deterministic ingest: heuristic extraction path that does not call an LLM
- TEI ingest: direct TEI/XML parsing path
- LLM ingest: extraction path using configured LLM settings
- macron index: JSON payload used by diacritic tools for normalized-to-display mappings
- morphology generation: TSV and SQLite production workflow for inflected forms
- build command: standard subcommand name for long-running database-producing
  workflows; morphology, dictionary, and lexicon should all use `build`, but
  each build remains explicit and separate
- canonical database: the one app-data `wyrdcraeft.sqlite3` file that holds
  morphology (`forms`), attached dictionary (`bt_*`), and derived lexicon
  (`lexicon_*`) data for the product's lookup workflows
- morphology index: morphology data stored inside canonical `wyrdcraeft.sqlite3`
  database rather than a standalone morphology-only file
- dictionary index: attached `bt_*` tables inside canonical `wyrdcraeft.sqlite3`
- dictionary SQLAlchemy slice: Phase 6 migration that moved `bt_*` writes and
  reads from direct `sqlite3` code to SQLAlchemy-backed persistence/query paths
- morphology SQLAlchemy slice: Phase 7 migration that moved `forms` writes and
  reads from direct `sqlite3` code to SQLAlchemy Core bulk insert plus
  SQLAlchemy query paths while preserving emitted ordering semantics
- lexicon: combined dictionary-plus-morphology user workflow presented as one
  browse/search surface
- lexicon read model: derived `lexicon_*` tables inside `wyrdcraeft.sqlite3`
  rebuilt from existing `forms` and `bt_*` rows for fast lemma-centric browse/search
- lexicon SQLAlchemy rebuild slice: post–Phase 8 work (commit `64c6223`) that moved
  `lexicon build` to SQLAlchemy Core batched reads/writes with no raw `sqlite3`,
  no TEMP staging tables, and cooperative cancel via DBAPI `interrupt`; join
  resolver extraction remains pending in Slice 2
- lexicon table DDL: Alembic-owned only (`20260630_01` initial schema plus later
  revisions); `lexicon build` **truncates** existing `lexicon_*` rows and
  repopulates them — it does not drop, recreate, or patch table shape
- lexicon staleness: compares stored source row counts (`forms`, `bt_entries`)
  against current counts; **no** lexicon `schema_version` meta key — app DDL
  changes are handled by startup Alembic migrations, often with in-migration
  backfill, without forcing a full read-model rebuild
- lexicon build: replaces only `lexicon_*` row contents; does not regenerate morphology
  or Bosworth-Toller source data; requires Alembic-managed lexicon tables to
  already exist (startup readiness or `upgrade_canonical_db`)
- orphan morphology hit: morphology match that does not join to a real
  dictionary entry and is shown outside the main lemma result list
- norm_key: diacritic-stripped normalized Old English key used for generic
  dictionary lookup and deduplication
- normalized_title: macron- and dot-preserving normalized lemma/headword title
  used to join morphology ``forms`` rows with Bosworth-Toller ``bt_entries``
  and ``bt_variants`` at lexicon build time; distinct from ``norm_key``, which
  strips combining marks
- normalized title join index: in-memory maps built at join time to match
  morphology lemma titles to dictionary entries using macron-preserving
  normalized titles, direct entry hits, and POS-aware variant fallbacks
- resolve_one / resolve_all: shared join policies over the same tier order;
  ``resolve_one`` picks a single dictionary entry when the tier policy yields
  one unambiguous match, while ``resolve_all`` returns every matching entry id
  for dictionary browse and multi-hit lookups
- lexicon browse search normalization: user queries and dictionary search-key
  indexing use ``normalize_old_english`` (diacritic-stripped) so undiacritized
  input like ``abbod`` matches macronized headwords; form-to-entry linking still
  uses ``normalized_title`` during ``lexicon build``, and browse reads the
  pre-joined ``lexicon_forms.entry_id`` at query time
- morphology function code: compact tag on a generated form row (for example
  `PaInSg2`, `PlNeAc`) naming tense, mood, case, gender, number, degree, or
  other inflectional dimensions depending on part of speech
- morphology table: browse sidebar view that expands function codes into
  POS-aware paradigm grids (verb/noun/adjective/pronoun) filtered to the
  headword's part of speech; falls back to a flat table when no grid applies
- paradigm grid: case-by-number or person-by-number table built from morphology
  function codes; instrumental forms use code `Is` displayed as `Inst`
- lexical distance: Levenshtein distance between normalized query and candidate
  text; lexicon browse uses it to sort search results after rank tier and key kind
- Old English search bar: lexicon browse input (`OldEnglishSearchInput`) with
  keyboard entry as the primary path; optional character bar below the field
  inserts æ/þ/ð, macrons, and dotted letters when the terminal cannot type them
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
- POS inference: lexicon build step that fills empty dictionary POS from
  unambiguous morphology wordclass when one clear mapping exists
- lexicon build progress: live stderr stage progress during `lexicon build`
- lexicon build monitor: default full-screen Textual monitor for `lexicon build`
  showing typed stage progress, counters, structured logs, and cooperative
  cancel state
- lexicon browse startup progress: live stderr progress while opening browse
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
  - Slice 2 **complete** (pending commit): shared `NormalizedTitleJoinIndex`
    unifies morphology↔dictionary joins; removed duplicated join SQL from
    lexicon build and `BTQueryService`; plan at
    `docs/superpowers/plans/2026-07-03-lexicon-sqlalchemy-normalized-title-join.md`
- Phase 1 (`fa34e5f`): canonical `wyrdcraeft.sqlite3` path and shared DB base
- Phase 2 (`b21d0a4`): Alembic startup runtime, backup/restore, readiness gate
- Phase 3 (`914a4bb`): initial Alembic-managed canonical schema (includes
  `lexicon_*` tables)
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

## Key Flows

### Source conversion

`wyrdcraeft main:main` -> `wyrdcraeft.cli.cli:cli` -> `wyrdcraeft.cli.source:reading_convert` -> `DocumentIngestor.ingest` -> document JSON written to user path

### Morphology generation

`wyrdcraeft.cli.morphology:build` -> session/setup helpers -> generation dispatch
-> TSV sink and SQLAlchemy-backed `SqliteIndexSink` -> `forms` in
`wyrdcraeft.sqlite3`

### Dictionary indexing

`wyrdcraeft.cli.dictionary:build` -> `BTIndexPipeline.run` -> SQLAlchemy-backed
dictionary sink -> attached `bt_*` tables in `wyrdcraeft.sqlite3`

### Lexicon browse

`wyrdcraeft.cli.lexicon:build` -> startup Alembic-managed schema must already
exist -> `rebuild_lexicon` truncates and repopulates `lexicon_*` via
SQLAlchemy Core (optional POS inference, worker-thread runtime + typed build
events -> default Textual build monitor or plain `--no-tui` renderer)

`wyrdcraeft.cli.lexicon:browse` -> startup progress -> `LexiconQueryService`
-> Textual `LexiconBrowseApp` with search bar at top, results pane left,
details plus POS-filtered paradigm grids right

Prerequisite: canonical `wyrdcraeft.sqlite3` at Alembic head with `forms`,
`bt_*`, and empty or populated `lexicon_*` tables (from morphology build,
dictionary build, and startup readiness).

### OCR workflow

`wyrdcraeft.cli.ocr:old_english_ocr` -> `run_old_english_ocr_pipeline` -> managed proxy / `olmocr` run -> normalized text and unknown-token report

## Sharp Edges

- Morphology generation writes real app-data `wyrdcraeft.sqlite3` by default
  through SQLAlchemy-backed `forms` persistence; tests must use
  `isolated_morphology_app_data` or explicit temp paths.
- Dictionary indexing now writes `bt_*` through SQLAlchemy-backed persistence
  into app-data `wyrdcraeft.sqlite3`; CLI/product flows still fail clearly when
  that canonical database is missing.
- Lexicon build defaults to the same `wyrdcraeft.sqlite3` path and fails clearly if
  required source or Alembic-managed `lexicon_*` tables are missing.
- Lexicon build refuses to overwrite existing lexicon read-model data unless
  `--force` is passed; the build can take ~30 minutes when source data is large.
- Lexicon build truncates `lexicon_*` rows in place; table DDL comes from Alembic,
  not from the rebuild job. App upgrades should migrate schema via Alembic
  (often with backfill) without requiring a full lexicon rebuild for additive DDL.
- Lexicon staleness is based on source table row counts only, not a lexicon
  schema version constant.
- Lexicon build now launches a full-screen Textual monitor by default on an
  interactive terminal; use `--no-tui` for the plain renderer and `--quiet`
  for final-summary-only output.
- Lexicon build stages stream typed progress through a worker-thread runtime.
  Single-step stages such as `verify sources` emit an explicit terminal
  progress event so the monitor does not appear stuck at `0/1`.
- Lexicon browse v1 is read-only; run `wyrdcraeft lexicon build` after morphology or
  dictionary **source data** changes, not after routine Alembic DDL upgrades.
- Lexicon browse and build expect the canonical Alembic-managed schema; startup
  database readiness applies migrations before DB-using commands run.
- Lexicon build may infer missing dictionary POS from morphology when wordclass is
  unambiguous; ambiguous lemmas stay POS-empty.
- Lexicon browse search accepts direct keyboard entry of æ/þ/ð, macrons, and
  dotted letters when the search field is focused; the character bar below the
  field is a fallback for terminals that cannot emit those keys.
- Lexicon browse search results sort by rank tier and key kind, then lexical
  distance from the query string.
- Morphology sidebar shows only forms matching the headword POS and renders
  paradigm grids from function codes; scrollable details and morphology panes
  share the right column below the search bar.
- OCR `--pages` is currently not supported in `olmocr` mode.
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
  (Phases 1–8). Lexicon read-model tables now live in the same canonical DB and
  are Alembic-managed.

Additional architecture decision records live under `docs/adr/` when this repo
captures durable design decisions that should not be rediscovered from code.
