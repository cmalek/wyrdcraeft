# BT OCR Stage B Live Pairing and Clamp Regression Plan

Goal: close two narrow witness-prep follow-ups without widening product scope:

1. true live Stage B baseline-vs-candidate OCR pairing
2. one deterministic clamp-path preprocess regression

Keep diff small. Reuse existing benchmark, validation, and preprocess code.

## Task 1 — Make Stage B live mode pair real baseline and candidate arms

Files:

- `scripts/ocr/benchmark_bt_witness_prep.py`
- maybe small touch in `wyrdcraeft/services/ocr/bt_witness_prep/models.py` only
  if summary metadata wants typed helpers

Steps:

- [ ] add helper to materialize raw whole-page baseline images from validation
      source pages
- [ ] make baseline source selection explicit:
      use `validation_manifest.json` `source_filename` as source of truth for
      each page's raw JP2 input, then map result back to manifest `page_id`
- [ ] add helper to discover candidate tile images from `prepare_pages()`
      output by page id in reading order
- [ ] add helper to OCR many candidate tiles and concatenate normalized text
      with blank-line separators
- [ ] change live benchmark path so:
      - baseline arm OCRs raw whole-page images
      - candidate arm OCRs prepared tiles or fallback whole-page tile
- [ ] fix `collect_guardrail_flags()` to read
      `manifests/tiles.jsonl`
- [ ] add minimal summary metadata for arm provenance if useful

Why first:

- root product gap lives here
- no metric math changes required if page-level text stays page-level

## Task 2 — Cover pairing logic offline

Files:

- `tests/ocr/test_bt_witness_prep_validation.py`
- add `tests/ocr/test_benchmark_bt_witness_prep.py`

Steps:

- [ ] keep `validation.py` tests metric-only:
      prove page baseline text and stitched candidate text feed
      `evaluate_stage_b_recipe()` as intended
- [ ] add benchmark-script seam tests for actual orchestration behavior:
      tile discovery, candidate ordering, and baseline/candidate arm separation
- [ ] add test for candidate ordering in script-level helpers:
      `col-1-part-1`, `col-1-part-2`, `col-2-part-1`, `col-2-part-2`
- [ ] add script-level test that guardrail aggregation is page-level OR across
      candidate tiles and reads `manifests/tiles.jsonl`
- [ ] add script-level test that baseline page selection comes from manifest
      `source_filename`, not inferred `page_id` PNG naming
- [ ] add test that pages without comparison witness still emit `None` metrics
      but keep guardrail state

Verification:

```bash
rtk .venv/bin/pytest tests/ocr/test_bt_witness_prep_validation.py -q
rtk .venv/bin/pytest tests/ocr/test_benchmark_bt_witness_prep.py -q
```

## Task 3 — Add synthetic clamp regression

Files:

- `tests/ocr/test_bt_witness_prep_preprocess.py`
- maybe tiny direct import/use of `_clamp_crop_box` from
  `wyrdcraeft/services/ocr/bt_witness_prep/preprocess.py`

Steps:

- [ ] build one synthetic image in test via Pillow
- [ ] choose recipe override with high `min_content_pixels_per_line` so detector
      proposes over-crop beyond `max_margin_fraction`
- [ ] assert preprocess result clamps affected edge to max allowed trim
- [ ] assert protected dark markers survive in output
- [ ] add tiny direct `_clamp_crop_box()` collapse test for full-frame fallback

Verification:

```bash
rtk .venv/bin/pytest tests/ocr/test_bt_witness_prep_preprocess.py -q
```

## Task 4 — Add one live integration seam, keep it gated

Files:

- likely `tests/test_ocr_live_integration.py`
- maybe no new file if existing OCR integration home already fits better

Steps:

- [ ] add or extend one gated integration test under existing OCR integration
      marker
- [ ] live test should verify only smallest end-to-end contract:
      baseline arm and candidate arm hit different image inputs
- [ ] do not make live test assert exact OCR strings; assert artifact routing and
      non-empty outputs instead

Why gated:

- llama-server / olmocr availability unstable by design
- offline tests should carry behavior confidence

## Task 5 — Refresh docs if implementation changed observable contract

Files:

- `doc/source/overview/bt_ocr_witness_preparation.rst`
- `doc/source/overview/bt_ocr_witness_preparation_method.rst`
- maybe ADR 0006 only if wording drift discovered; probably skip

Steps:

- [ ] update Stage B wording to say candidate live path OCRs stitched prepared
      tiles while baseline stays raw whole page
- [ ] mention clamp regression exists only if docs already discuss clamp safety

Skip if runtime wording already stays true enough.

## Ordered Test Strategy

1. write or extend offline pairing tests first
2. make benchmark live-path changes until offline tests pass
3. add synthetic clamp regression
4. run focused OCR test files
5. run required repo gates if Python touched
6. run gated live test only if environment available

## Verification Commands

Focused:

```bash
rtk .venv/bin/pytest tests/ocr/test_bt_witness_prep_validation.py -q
rtk .venv/bin/pytest tests/ocr/test_benchmark_bt_witness_prep.py -q
rtk .venv/bin/pytest tests/ocr/test_bt_witness_prep_preprocess.py -q
```

Broader OCR safety:

```bash
rtk .venv/bin/pytest tests/ocr -q
```

Required Python gates after edits:

```bash
rtk .venv/bin/ruff check scripts/ocr/benchmark_bt_witness_prep.py tests/ocr/test_bt_witness_prep_validation.py tests/ocr/test_benchmark_bt_witness_prep.py tests/ocr/test_bt_witness_prep_preprocess.py
rtk .venv/bin/mypy scripts/ocr/benchmark_bt_witness_prep.py wyrdcraeft/services/ocr/bt_witness_prep/preprocess.py
rtk make napoleon-gate
```

Optional gated live check when environment exists:

```bash
rtk .venv/bin/pytest tests/test_ocr_live_integration.py -q -k bt_witness_prep --run-ocr-integration
```

## Review Notes For Later Implementer

- shortest diff likely lives almost entirely in
  `scripts/ocr/benchmark_bt_witness_prep.py`
- benchmark-script behavior needs benchmark-script tests; validation-layer tests
  alone are not enough to catch live pairing mistakes
- do not push pairing logic down into generic OCR pipeline code unless a helper
  already exists there
- keep `validation.py` mostly metric-only
- keep clamp regression synthetic and tiny; no binary fixture sprawl
- docs under `docs/superpowers/` are tracked here, but confirm staging scope if
  a later commit uses narrow `git add`
