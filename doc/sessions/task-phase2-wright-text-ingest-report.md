# Phase 2 — Wright § Text Ingest Report

**Status:** DONE  
**BASE commit:** `790785ce20209176ff80c8de251d6b8381488555`  
**Date:** 2026-07-04

## Summary

Implemented Wright section text ingest for Phase 2 of the morph-class browse surfacing plan. Markdown `§ N` headings are parsed into `wright_sections.section_text` via an explicit `morphology ingest-wright-text` CLI command. Ingest is idempotent by default; `--force` overwrites populated rows. Browse/query reads stored SQLite text only — no runtime markdown parsing.

## Files changed

| Action | Path |
|--------|------|
| Create | `wyrdcraeft/services/morphology/catalog/wright_text.py` |
| Modify | `wyrdcraeft/services/morphology/catalog/query.py` |
| Modify | `wyrdcraeft/cli/morphology.py` |
| Create | `tests/morphology/test_wright_section_text.py` |
| Modify | `doc/source/overview/command_morphology_generate.rst` |

## Implementation notes

### Task 2.1 — Markdown § parser

- `parse_wright_sections()` matches `^§\s+(\d+)\.?(?:\s|$)` at line start.
- Body runs from the heading line until the next `§` heading.
- Whitespace normalized via strip + collapse runs; OE Unicode preserved.
- §334 tests use `tests/fixtures/ocr/wright_nouns.md` (repo markdown corpus). Note: `data/sources/wright.md` currently contains phonology sections 1–58 only; catalog sections 334–558 are not present in that file yet.

### Task 2.2 — WrightSectionTextIngester

- `ingest(engine, md_path, *, force=False) -> IngestResult`
- Upsert policy: update when `section_text IS NULL`; `--force` overwrites non-null.
- `IngestResult` reports `updated`, `skipped`, `markdown_not_in_catalog`, `catalog_still_null`, `coverage_percent`, and `warnings`.
- Warns on extra markdown § and catalog § still NULL after ingest.

### Task 2.3 — CLI subcommand

- `wyrdcraeft morphology ingest-wright-text --source PATH [--force]`
- Uses canonical DB via `get_canonical_db_path`; DB readiness gate handled by root CLI (`ensure_database_ready`).
- Not hooked into `morphology build`.

### Task 2.4 — Query helper

- `MorphologyCatalogQueryService.lookup_wright_section_text(section_no) -> str | None`

## Validation output

```text
$ .venv/bin/pytest tests/morphology/test_wright_section_text.py tests/morphology/test_morph_catalog_query.py -q
14 passed in 1.06s

$ .venv/bin/ruff check wyrdcraeft/services/morphology/catalog/wright_text.py wyrdcraeft/services/morphology/catalog/query.py wyrdcraeft/cli/morphology.py
All checks passed!

$ .venv/bin/mypy wyrdcraeft/services/morphology/catalog/wright_text.py wyrdcraeft/services/morphology/catalog/query.py wyrdcraeft/cli/morphology.py
Success: no issues found in 3 source files

$ PATH=".venv/bin:$PATH" make napoleon-gate
Napoleon gate passed: no new violations (124 total, 191 baseline keys).
```

## Manual spot-check

CliRunner smoke against `data/sources/wright.md` with seeded catalog:

```text
updated=0
markdown_not_in_catalog=58
catalog_still_null=196
coverage_percent=0.0
```

Expected: bundled `wright.md` has no catalog-range sections (334–558). Full coverage requires a complete Wright markdown corpus.

## Self-review

**Strengths**

- Text stored on `wright_sections` only; junction rows untouched.
- Idempotent default + documented `--force` overwrite.
- Cohesive `WrightSectionTextIngester` class with frozen `IngestResult`.
- Tests use `tmp_path` only; no default app-data writes.
- Napoleon doc contract on new public types; morphology `Note:` cites grammar PDFs.

**Risks / follow-ups**

- `data/sources/wright.md` is incomplete for catalog §334–558; browse Phase 3 will show “not ingested” until corpus is extended or a fuller source is pointed at `--source`.
- Installed `wyrdcraeft` console script in `.venv` may be stale until editable reinstall; source tree and pytest CliRunner reflect the new subcommand correctly.

**Constraints honored**

- No auto-ingest on morphology build.
- No `section_text` on junction table.
- No runtime markdown read from browse/audit paths.
- No commits; `.aidex/index.db` untouched.
