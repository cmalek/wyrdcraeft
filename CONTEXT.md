# wyrdcraeft Context

## Mission

`wyrdcraeft` is a Python toolkit for processing Old English source material into
structured outputs and supporting reference workflows around that text.

Primary capabilities:

- ingest and convert source texts into structured document JSON
- restore and disambiguate diacritics
- generate and query Old English morphology
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
| morphology | `wyrdcraeft morphology generate`, `wyrdcraeft morphology query` | `wyrdcraeft.services.morphology.generation.dispatch`, `MorphologyQueryService` |
| dictionary | `wyrdcraeft dictionary index-bt`, `wyrdcraeft dictionary lookup` | `wyrdcraeft.services.dictionary.pipeline.BTIndexPipeline`, `BTQueryService` |
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
- morphology index: `morphology.sqlite3` lookup database
- dictionary index: `dictionary.sqlite3` Bosworth-Toller lookup database
- attach mode: writing dictionary tables into an existing morphology SQLite file
- lexicon: combined dictionary-plus-morphology user workflow presented as one
  browse/search surface
- lexicon read model: derived `lexicon_*` tables inside `morphology.sqlite3`
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

`wyrdcraeft.cli.morphology:generate` -> session/setup helpers -> generation dispatch -> TSV sink and SQLite sink -> `morphology.sqlite3`

### Dictionary indexing

`wyrdcraeft.cli.dictionary:index_bt` -> `BTIndexPipeline.run` -> SQLite sink -> attached `bt_*` tables in `morphology.sqlite3` by default, or `dictionary.sqlite3` with `--standalone`

### Lexicon browse

`wyrdcraeft.cli.lexicon:build` -> `rebuild_lexicon` (optional POS inference,
worker-thread runtime + typed build events -> default Textual build monitor or
plain `--no-tui` renderer -> `lexicon_*` tables in `morphology.sqlite3`

`wyrdcraeft.cli.lexicon:browse` -> startup progress -> `LexiconQueryService`
(with `migrate_lexicon_schema`) -> Textual `LexiconBrowseApp` with search bar
at top, results pane left, details plus POS-filtered paradigm grids right

Prerequisite: `forms` and `bt_*` must already exist in the target `morphology.sqlite3`
(from morphology generation plus dictionary attach/index flows).

### OCR workflow

`wyrdcraeft.cli.ocr:old_english_ocr` -> `run_old_english_ocr_pipeline` -> managed proxy / `olmocr` run -> normalized text and unknown-token report

## Sharp Edges

- Morphology generation writes real app-data `morphology.sqlite3` by default.
- Dictionary indexing attaches `bt_*` tables to app-data `morphology.sqlite3` by
  default and fails clearly when that database is missing; use `--standalone` for
  a separate `dictionary.sqlite3`.
- Lexicon build defaults to the same `morphology.sqlite3` path and fails clearly if
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
