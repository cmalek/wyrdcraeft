# Phase 1 Morph-Class Browse Report

- Status: DONE

## What I implemented

- Extended `MorphClassView` with `assignment_source`.
- Added `LemmaMorphClassSummary` plus shared
  `format_morph_class_display_label()` in the catalog query layer.
- Composed `MorphologyCatalogQueryService` into `LexiconQueryService` so
  browse details now resolve catalog morph-class metadata at read time using
  normalized headword plus mapped catalog POS.
- Added `EntryDetails.morph_class` with these semantics:
  - assigned class -> populated summary
  - mapped POS with no assignment -> explicit `Unclassified` summary
  - unmappable POS -> `None`
- Replaced details-pane class rendering with catalog-driven lines:
  - `Morph class: ...`
  - `Provenance: ...` when classified
  - `Wright §: ...` when sections exist
  - `Morph class: Unclassified` when lookup misses
- Added focused tests for:
  - catalog `assignment_source`
  - formatter rule for compact vs canonical labels
  - lexicon browse detail enrichment
  - explicit unclassified rendering
  - `pos='adj'` mapping to catalog `adjective`

## Files changed

- `wyrdcraeft/services/morphology/catalog/query.py`
- `wyrdcraeft/services/morphology/catalog/__init__.py`
- `wyrdcraeft/services/lexicon/query.py`
- `wyrdcraeft/services/lexicon/tui.py`
- `tests/morphology/test_morph_catalog_query.py`
- `tests/lexicon/test_morph_class_browse.py`
- `tests/lexicon/test_query_service.py`
- `doc/sessions/task-phase1-morph-class-browse-report.md`

## Test commands and output summary

- `.venv/bin/ruff check wyrdcraeft/services/morphology/catalog/query.py wyrdcraeft/services/lexicon/query.py wyrdcraeft/services/lexicon/tui.py tests/lexicon/test_morph_class_browse.py tests/lexicon/test_query_service.py tests/morphology/test_morph_catalog_query.py`
  - Passed.
- `.venv/bin/mypy wyrdcraeft/services/morphology/catalog/query.py wyrdcraeft/services/lexicon/query.py wyrdcraeft/services/lexicon/tui.py`
  - Passed: no issues found in 3 source files.
- `make napoleon-gate`
  - Passed after exporting `.venv/bin` onto `PATH` so `python` resolved for `make`.
- `.venv/bin/pytest tests/morphology/test_morph_catalog_query.py tests/lexicon/test_morph_class_browse.py tests/lexicon/test_query_service.py tests/lexicon/test_tui.py -q`
  - Passed: `49 passed in 9.20s`.
- `git diff --exit-code -- tests/morphology/data/refactor_baseline.json`
  - Passed: no diff.

## Self-review findings

- The new browse path stays within Phase 1 scope: no schema changes to
  lexicon tables, no `forms.morph_class_id`, no browse filters, no sidebar
  Wright-text work, and no audit command.
- The shared formatter now locks one explicit rule in tests:
  prefer `pos, modern_class` when `modern_class` differs from
  `canonical_name`; otherwise fall back to `canonical_name`.
- While running the required focused pytest set, `tests/lexicon/test_query_service.py`
  had a stale variant-order expectation unrelated to morph-class surfacing.
  I updated that expectation to match the current rebuilt lexicon output
  ordering (`abbod`, `abbot`, `abbud`) so the required validation suite passes.
