# OCR pipeline moves to bochord

The sibling repo this ADR named `bochord` is now `wordwending` (`/Users/cmalek/src/workspace/wordwending`). GitHub already had `bochord`. Same split; new name. This filename stays so existing links keep working.

All OCR work (image acquisition, tiling, witness OCR, olmocr/ocrmypdf integration, OCR proxy server) moves out of wyrdcraeft into that sibling. wyrdcraeft stays focused on Old English grammar, dictionaries, morphology, and diacritics — OCR is an upstream data-acquisition concern, not core domain logic, and its noisy, image-heavy artifacts and heavyweight deps (olmocr, ocrmypdf, appleocr) don't belong in a grammar/dictionary library.

Downstream consumers (dictionary/case-bundle assembly, e.g. `data/bt_cases/wesan/`) keep consuming OCR *output* (witness yaml, manifests, tiles) as plain data/artifacts produced by `wordwending` and dropped into wyrdcraeft's `data/` tree or fetched at build time — not as in-process Python calls into an OCR package living in this repo.

## Removed from wyrdcraeft

Code:
- `wyrdcraeft/services/ocr/` (`bt_tile_ocr.py`, `bt_witness_ocr.py`, `old_english_pipeline.py`, `bt_witness_prep/`)
- `wyrdcraeft/services/ocr_proxy/`
- `wyrdcraeft/cli/ocr.py` + its registration in `wyrdcraeft/cli/cli.py`
- `scripts/ocr/` (incl. `olmocr_hf` entry point in `pyproject.toml`)

Tests:
- `tests/test_cli_ocr*.py`, `tests/test_old_english_ocr_pipeline_olmocr.py`, `tests/test_ocr_live_integration.py`, `tests/ocr/`

Deps (`pyproject.toml`):
- `olmocr`, `ocrmypdf`, `ocrmypdf-appleocr`
- `ocr_integration` pytest marker

Data (already removed from working tree per current `git status`):
- `data/bt_cases/`, `data/ocr/`
- `data/bosworth_toller/` raw scans, PDF, hOCR/OCR text, abbreviations JSON — **but not** the plain-text BT dictionary source itself: `data/bosworth_toller/oe_bosworthtoller.txt.bz2` and `oe_bt.txt.bz2` are being kept (re-added as compressed text) since dictionary/morphology parsing consumes them directly and they aren't OCR-pipeline output.

Docs: ADR 0004/0005/0006 stay as historical record (they document *why* the OCR/witness-prep design looked the way it did) but are marked superseded/relocated; `docs/context/ocr.md` and OCR-specific superpowers plans/specs/handoffs move to `wordwending`.

## Not removed

`wyrdcraeft/settings.py` currently carries a large OCR/olmocr config block (~15 fields: `ocr_upstream_base_url`, `ocr_olmocr_model`, `ocr_olmocr_workers`, `ocr_olmocr_max_concurrent_requests`, `ocr_olmocr_target_longest_image_dim`, `ocr_olmocr_max_page_retries`, `ocr_api_key`, `ocr_legacy_lang`, plus workspace-dirname-style constants). Most of this is pipeline-only and should be deleted alongside the code that reads it; audit at implementation time for any field still referenced by data-consumption code (e.g. case-bundle loaders reading OCR output artifacts) and keep only those.

## Consequence

wyrdcraeft loses the ability to *produce* OCR text/tiles itself; any new witness needs `wordwending` run first, output copied/synced into wyrdcraeft's `data/`. This is acceptable — the split already reflects current practice (OCR data files already deleted from this repo's working tree).
