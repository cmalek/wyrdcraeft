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
- attach mode: writing dictionary tables into an existing morphology SQLite file
- lexicon: combined dictionary-plus-morphology user workflow presented as one
  browse/search surface
- lexicon read model: derived `lexicon_*` tables inside `wyrdcraeft.sqlite3`
  rebuilt from existing `forms` and `bt_*` rows for fast lemma-centric browse/search
- lexicon build: replaces only `lexicon_*` contents; does not regenerate morphology
  or Bosworth-Toller source data
- orphan morphology hit: morphology match that does not join to a real
  dictionary entry and is shown outside the main lemma result list
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
- lexicon schema migration: additive upgrade of existing `lexicon_*` tables
  (for example adding `lexicon_forms.paradigm`) on browse connect and build
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

## Key Flows

### Source conversion

`wyrdcraeft main:main` -> `wyrdcraeft.cli.cli:cli` -> `wyrdcraeft.cli.source:reading_convert` -> `DocumentIngestor.ingest` -> document JSON written to user path

### Morphology generation

`wyrdcraeft.cli.morphology:build` -> session/setup helpers -> generation dispatch -> TSV sink and SQLite sink -> `wyrdcraeft.sqlite3`

### Dictionary indexing

`wyrdcraeft.cli.dictionary:build` -> `BTIndexPipeline.run` -> SQLite sink -> attached `bt_*` tables in `wyrdcraeft.sqlite3`

### Lexicon browse

`wyrdcraeft.cli.lexicon:build` -> `rebuild_lexicon` (optional POS inference,
worker-thread runtime + typed build events -> default Textual build monitor or
plain `--no-tui` renderer -> `lexicon_*` tables in `wyrdcraeft.sqlite3`

`wyrdcraeft.cli.lexicon:browse` -> startup progress -> `LexiconQueryService`
(with `migrate_lexicon_schema`) -> Textual `LexiconBrowseApp` with search bar
at top, results pane left, details plus POS-filtered paradigm grids right

Prerequisite: `forms` and `bt_*` must already exist in target `wyrdcraeft.sqlite3`
(from morphology build plus dictionary build flows).

### OCR workflow

`wyrdcraeft.cli.ocr:old_english_ocr` -> `run_old_english_ocr_pipeline` -> managed proxy / `olmocr` run -> normalized text and unknown-token report

## Sharp Edges

- Morphology generation writes real app-data `wyrdcraeft.sqlite3` by default.
- Dictionary indexing attaches `bt_*` tables to app-data `wyrdcraeft.sqlite3` by
  default and fails clearly when that database is missing.
- Lexicon build defaults to the same `wyrdcraeft.sqlite3` path and fails clearly if
  required `bt_*` tables are missing.
- Lexicon build refuses to overwrite existing lexicon read-model data unless
  `--force` is passed; the build can take ~30 minutes.
- Lexicon build now launches a full-screen Textual monitor by default on an
  interactive terminal; use `--no-tui` for the plain renderer and `--quiet`
  for final-summary-only output.
- Lexicon build stages stream typed progress through a worker-thread runtime.
  Single-step stages such as `verify sources` emit an explicit terminal
  progress event so the monitor does not appear stuck at `0/1`.
- Lexicon browse v1 is read-only; run `wyrdcraeft lexicon build` after morphology or
  dictionary source data changes.
- Opening lexicon browse on an older database auto-migrates missing `lexicon_*`
  columns (for example `lexicon_forms.paradigm`); rebuild to populate derived data.
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

Additional architecture decision records live under `docs/adr/` when this repo
captures durable design decisions that should not be rediscovered from code.
