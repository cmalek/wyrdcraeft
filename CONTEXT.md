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
| lexicon | `wyrdcraeft lexicon build`, `wyrdcraeft lexicon browse` | `wyrdcraeft.services.lexicon.build`, `LexiconQueryService`, `LexiconBrowseApp` |
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

`wyrdcraeft.cli.lexicon:build` -> `rebuild_lexicon` -> `lexicon_*` tables in `morphology.sqlite3`

`wyrdcraeft.cli.lexicon:browse` -> `LexiconQueryService` -> Textual `LexiconBrowseApp`

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
- Lexicon browse v1 is read-only; run `wyrdcraeft lexicon build` after morphology or
  dictionary source data changes.
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
