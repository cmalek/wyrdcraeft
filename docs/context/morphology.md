# Morphology Context

## What This Capability Does

Morphology generates inflected Old English forms, writes lookup artifacts to the
canonical SQLite database, and supports query-time retrieval of those forms.
Since Phase 1–2 of the Wright catalog work (2026-07), morphology build also
seeds a reference morph-class catalog and assigns each inflectable lemma to a
Wright inflection class.

## Main CLI Entrypoints

- `wyrdcraeft morphology build`
- `wyrdcraeft morphology query`
- `wyrdcraeft morphology ingest-wright-text`
- `wyrdcraeft morphology audit-wright`

## Primary Python Entrypoints

- `wyrdcraeft.cli.morphology`
- `wyrdcraeft.services.morphology.session:GeneratorSession`
- `wyrdcraeft.services.morphology.processors`
- `wyrdcraeft.services.morphology.generation.dispatch`
- `wyrdcraeft.services.morphology.generation.query:MorphologyQueryService`
- `wyrdcraeft.services.morphology.build_profile:MorphologyBuildProfiler`
- `wyrdcraeft.services.morphology.catalog` — Wright reference catalog (loader,
  assigner, query, paradigm mapper, POS helpers)
- `wyrdcraeft.paths:get_canonical_db_path`

## Key Files

- `wyrdcraeft/cli/morphology.py`
- `wyrdcraeft/paths.py`
- `wyrdcraeft/models/morph_catalog.py`
- `wyrdcraeft/services/morphology/processors.py`
- `wyrdcraeft/services/morphology/session.py`
- `wyrdcraeft/services/morphology/generation/dispatch.py`
- `wyrdcraeft/services/morphology/generation/query.py`
- `wyrdcraeft/services/morphology/catalog/loader.py`
- `wyrdcraeft/services/morphology/catalog/assigner.py`
- `wyrdcraeft/services/morphology/catalog/query.py`
- `wyrdcraeft/services/morphology/catalog/wright_text.py`
- `wyrdcraeft/services/morphology/catalog/wright_audit.py`
- `wyrdcraeft/services/morphology/catalog/paradigm_map.py`
- `wyrdcraeft/etc/morphology/wright_paradigms.json`
- `doc/source/overview/command_morphology_generate.rst`
- `doc/source/overview/command_morphology_query.rst`
- `doc/source/overview/morphology_perl_quirks_ledger.rst`

## Inputs And Outputs

Inputs:

- bundled morphology source files under `wyrdcraeft/etc/morphology`
- optional overrides via `--data-dir`, `--dictionary`, `--manual-forms`,
  `--verbal-paradigms`, `--prefixes`
- Wright catalog fixture `wright_paradigms.json` (under data dir or packaged)

Outputs:

- SQLite lookup DB `wyrdcraeft.sqlite3` in app data (default; holds `forms`,
  morph catalog tables, and `lemma_morph_classes` assignment rows)
- optional TSV form output when `--output` is passed
- optional query results in text or JSON

## Wright Morph Catalog (Phase 1–2)

Reference tables in canonical SQLite, seeded from
`wyrdcraeft/etc/morphology/wright_paradigms.json`:

- `morph_classes`, `morph_sources`, `wright_sections`, junction tables
- `lemma_morph_classes` — `(normalized_title, pos)` → assigned morph class

Build pipeline (after paradigm assigners, before form generation):

1. `MorphologyCatalogLoader.ensure_seeded()` — idempotent; `--refresh-catalog`
   forces reload
2. `LemmaMorphClassAssigner.assign_all(session.words)` — priority: paradigm /
   `paraID` → POS features → Wright § intersection (≥330) → skip (no row)

Read API: `MorphologyCatalogQueryService.lookup_lemma_class()` returns
`MorphClassView` (class metadata, Wright § numbers, source citations).
`lookup_wright_section_text(section_no)` returns stored paragraph text from
`wright_sections.section_text` after ingest.

Paradigm resolution uses `ParadigmClassMapper` with `wright_paradigms.json`
exemplars and `para_vb.txt` for verb `paraID` lookup. Legacy
`wright_*_paradigm_mapping.json` files are not used.

## Wright Section Text Ingest (browse support)

Explicit command — **not** run on `morphology build`:

- `wyrdcraeft morphology ingest-wright-text --source PATH [--force]`
- `WrightSectionTextIngester` parses `§ N` / `§ N.` headings from markdown
- Upserts `wright_sections.section_text` (NULL rows only; `--force` overwrites)
- Reports coverage gaps (`markdown_not_in_catalog`, `catalog_still_null`)

**Coverage note:** bundled `data/sources/wright.md` currently contains phonology
§1–58 only. Inflection sections cited by the catalog (§330+) require a fuller
markdown corpus pointed at `--source` before browse can show paragraph text.

## Legacy Wright Audit (report-only v1)

- `wyrdcraeft morphology audit-wright [--json] [--db PATH] [--data-dir …]`
- `WrightAuditService` compares bundled source `wright` fields to deterministic
  `lemma_morph_classes` rows
- Categories: malformed legacy Wright, contradiction vs assigned class §,
  unclassified lemma+POS, blank legacy but classified
- Never rewrites source files; exit code 0 in v1 (report-only)

## Lexicon Browse Integration

Browse dictionary detail (via `LexiconQueryService` + `LexiconBrowseApp`):

- Join-at-read-time morph-class block: label, provenance, explicit
  `Unclassified` when no assignment
- Selectable Wright § list opens `WrightSectionTextScreen` modal
- Reads SQLite `section_text` only (no runtime markdown parsing)
- Morphology sidebar paradigm grids unchanged

Plan: `docs/superpowers/plans/2026-07-04-morph-class-browse-audit-implementation.md`

## Invariants And Sharp Edges

- Default build writes real app-data `wyrdcraeft.sqlite3`; tests must use
  `isolated_morphology_app_data` or explicit temp paths.
- TSV is optional (`--output`); default artifact is SQLite only.
- `--profile` prints stage and SQLite flush timings to stderr.
- `--data-dir` and `--verbal-paradigms` apply to catalog seeding, paradigm
  mapping, and generation inputs consistently.
- Generation-derived participles appended to `session.adjectives` during verb
  generation are not assigned at build time (assignment runs before generation).
- Wright paragraph text is not ingested during build; run
  `morphology ingest-wright-text` when markdown corpus is ready.
- Legacy source `wright` is audit input only; canonical classification is
  `lemma_morph_classes`. Use `morphology audit-wright` for quality reports.
- `forms.morph_class_id` FK propagation remains deferred (see
  `doc/plans/morphology-wright-catalog/phase-3-forms-link-and-query.md`).
- Current generation code is parity-sensitive with historical Perl behavior.
- Query behavior can optionally attach dictionary data; morphology and
  dictionary share the canonical DB but remain separate capabilities.

## Related Docs

- [../../CONTEXT.md](../../CONTEXT.md)
- [../context/dictionary.md](dictionary.md)
- [../context/settings.md](settings.md)
- [../../doc/plans/morphology-wright-catalog/README.md](../../doc/plans/morphology-wright-catalog/README.md)
