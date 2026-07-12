# BT OCR Stage B Live Pairing and Clamp Regression Design

Date: 2026-07-10
Repo: `/Users/cmalek/src/workspace/wyrdcraeft`
Status: Draft addendum to the completed BT JP2 witness-preparation slice

## Purpose

Close two narrow follow-up gaps in the BT JP2 witness-preparation slice without
widening scope:

1. make live Stage B OCR compare a true raw whole-page baseline against a true
   recipe-prepared candidate
2. add one deterministic clamp-path regression that proves
   `_clamp_crop_box()` prevents catastrophic over-crop

This addendum stays library-first and benchmark-first. It does not add parser
work, case-bundle mutation, a new OCR framework, or generic preprocessing
machinery.

## Context Carried Forward

- `prepare_pages(BTWitnessPrepInput) -> BTWitnessPrepRun` already emits
  preprocessed pages, prepared tiles, manifests, and anchor seeds.
- `validation.py` already owns Stage B metric and pass-rule logic:
  diacritic-sensitive CER, historical-character exact-match rate, and the
  small-component guardrail veto.
- `scripts/ocr/benchmark_bt_witness_prep.py` already owns Stage B orchestration
  and already supports an offline `--skip-ocr` path.
- ADR 0006 already locks Stage B semantics to candidate recipe versus raw
  whole-page baseline. Current live path is stubby because both OCR arms point
  at the same prepared image directory.

## Non-Goals

- no new OCR stack
- no generic benchmark framework
- no case-bundle import logic
- no CLI product surface beyond tiny benchmark-script changes
- no change to ADR 0004 / 0005 / 0006 intent

## Gap A

### Problem

Live Stage B currently fails contract. In `run_benchmark()`, both baseline and
candidate OCR hypotheses are produced from the same `ocr_input_dir/<page_id>.png`
path. That means live mode cannot answer whether prepared candidate witnesses
actually beat a raw whole-page baseline.

### Options Considered

#### Option 1 — Page-vs-page only

OCR one whole-page raw render for baseline and one whole-page preprocessed page
for candidate.

Why reject:

- cheapest wiring
- but does not validate tiling, which is core value of witness prep
- under-tests actual candidate path users care about

#### Option 2 — Whole-page raw baseline vs stitched tile candidate

OCR one raw full-page witness for baseline. OCR prepared tiles for candidate,
then concatenate tile transcripts in reading order into one page-level witness.

Why choose:

- matches ADR 0006 language: raw whole-page baseline versus candidate recipe
- exercises real `prepare_pages` output
- reuses existing OCR pipeline one image at a time
- keeps Stage B output page-level, so `validation.py` contract barely changes

#### Option 3 — Per-tile metrics only

Compare baseline whole page against per-tile CER and aggregate numerically.

Why reject:

- comparison witness fixtures are page-level, not tile-level
- aggregation rule becomes arbitrary and noisy
- more design surface, no clear gain for current slice

### Recommended Design

Use Option 2.

#### Baseline arm

Baseline input for one validation page is:

- raw whole-page witness image
- rendered directly from the source JP2 page
- no BT candidate preprocessing recipe
- no four-tile split

Practical form:

- benchmark materializes `baseline_pages/<page_id>.png`
- image covers full source page extent
- OCR runs once per page through existing
  `run_old_english_ocr_pipeline(OldEnglishOCRConfig(...))`

This keeps baseline aligned with Stage B wording: raw whole-page baseline.

#### Candidate arm

Candidate input for one validation page is:

- outputs from `prepare_pages(...)` for the candidate recipe
- prefer four prepared tiles when page status is `ready`
- fallback page uses the one emitted whole-page fallback tile when tiling says
  `fallback_whole_page_only` or `unsupported_layout`

Candidate OCR text is built as one page-level witness by:

1. OCR each candidate tile separately through existing OCR pipeline
2. order tiles in reading order:
   - `col-1-part-1`
   - `col-1-part-2`
   - `col-2-part-1`
   - `col-2-part-2`
3. concatenate normalized outputs with `\n\n` separators

This keeps candidate witness page-level for CER scoring while still measuring
the benefit of tiling.

### OCR Invocation Rule

Do not invent a second OCR framework. Reuse the existing single-image OCR path
already wrapped by `run_page_ocr()`.

Minimal new orchestration:

- `run_page_ocr()` stays single-image
- benchmark script adds tiny helpers to:
  - build or locate baseline page images
  - collect candidate tile images by page
  - stitch candidate OCR text from multiple tile calls

No changes needed in `validation.py` metric math beyond optional metadata fields.

### Comparison Witness Use

Current rule remains correct:

- when `comparison_witness_available` is true, compute baseline CER and
  candidate CER against that witness
- when false, keep per-page metrics `None` and still report guardrail status

No new inference layer. OCR text remains witness, not canonical truth.

### Guardrail Source of Truth

Small-component guardrail flags should come from candidate `manifests/tiles.jsonl`
written by `prepare_pages()`.

Aggregation rule:

- page fails guardrail if any tile for that page has
  `quality.small_component_guardrail_failed == true`
- fallback whole-page tile participates exactly the same way

This matches current `collect_guardrail_flags()` intent. Only path fix needed:
it must read `manifests/tiles.jsonl`, not `tiles.jsonl` at workspace root.

### Minimal Smoke Path When Live OCR Unavailable

Keep `--skip-ocr` as primary smoke path.

Required behavior:

- offline path accepts pre-supplied baseline whole-page text files
- offline path accepts pre-supplied candidate stitched page text files
- tests for pairing logic inject fake OCR runners or pre-supplied text; no
  llama-server dependency

Live OCR remains gated integration coverage only.

### Summary Schema

Current summary payload is mostly fine. Add only metadata that explains arm
provenance, not new scoring math.

Recommended additions:

- top-level `baseline_arm`
  - `kind: "raw_whole_page"`
  - `image_dir`
- top-level `candidate_arm`
  - `kind: "prepared_tiles_concatenated"`
  - `workspace_dir`
- per-page optional metadata
  - `baseline_image_path`
  - `candidate_image_paths`
  - `candidate_tile_count`

Keep existing `comparison` metric fields unchanged so current downstream readers
do not need rework.

## Gap B

### Problem

Clamp protection exists in `_clamp_crop_box()`, but current tests never force
an over-crop beyond `max_margin_fraction`. Existing corner-marker fixtures only
prove indirect preservation after realistic cropping. They do not prove clamp
saved content when detection goes bad.

### Options Considered

#### Option 1 — Add more committed image fixtures

Reject. Too heavy for one regression. Binary fixture cost bigger than value.

#### Option 2 — Unit test `_clamp_crop_box()` directly

Good but slightly too narrow alone. Proves arithmetic, not that detection path
feeds it correctly.

#### Option 3 — One synthetic image that forces pathological detection plus one
small direct clamp assertion

Choose. Smallest regression that fails if clamp logic breaks and still exercises
real preprocess flow.

### Recommended Design

Keep clamp regression unit-only with synthetic tmp-path images. No committed
fixture binaries.

#### Synthetic fixture shape

Create one grayscale or RGB page with:

- bright background
- real dark content rectangle near left and top edges, inside the protected
  `max_margin_fraction` band
- sparse enough edge content that an aggressive detector using a higher
  `min_content_pixels_per_line` would miss it and try to crop too deep
- one or more unmistakable dark marker blocks near the soon-to-be-clamped edge

Recipe override for the test:

- `margin_luminance_delta` normal
- `max_margin_fraction = 0.12`
- `min_content_pixels_per_line` deliberately raised so detection undercounts
  sparse edge content and proposes an over-crop

Expected raw detection behavior:

- detector proposes crop deeper than 12% on one or more edges
- clamp truncates trim to 12%

#### Assertions

One preprocess-focused regression should assert all of:

1. crop result lands exactly on clamp boundary for affected edge
2. crop never trims more than `max_margin_fraction` of width/height
3. protected dark markers remain present in prepared output

Add one tiny direct `_clamp_crop_box()` unit assertion for collapse case:

- when clamping would still produce invalid geometry (`left >= right` or
  `top >= bottom`), result is full-frame fallback `(0, 0, width, height)`

This is ponytail path: one real-path regression, one arithmetic guard.

### Interaction With Later Metrics

Do not couple this regression to Stage B or quality scoring.

Reason:

- clamp contract belongs to preprocessing safety
- `margin_clipping_score` can still be mentioned in docs as downstream signal
- but regression should fail before quality-scoring machinery matters

## Recommended File-Level Changes

### Runtime

- `scripts/ocr/benchmark_bt_witness_prep.py`
  - fix live pairing
  - fix `collect_guardrail_flags()` manifest path
  - add tiny helpers for baseline render / candidate tile aggregation

### Tests

- `tests/ocr/test_bt_witness_prep_validation.py`
  - add offline pairing test for page baseline versus stitched candidate
  - add missing-comparison-witness behavior assertion if needed
- `tests/ocr/test_bt_witness_prep_preprocess.py`
  - add synthetic clamp regression through `preprocess_source_page()`
  - add tiny direct clamp/fallback unit assertion
- optional small benchmark-script test file if script wiring already has a test
  home; otherwise keep pairing coverage in existing OCR tests

### Fixtures

- prefer tmp-path synthetic images
- no new committed binary fixtures
- reuse existing validation manifest and text fixtures for offline Stage B

## Open Questions

None blocking for planning.

Assumptions chosen here:

- baseline should stay truly raw whole-page, not preprocessed whole-page
- candidate should validate tiling, not only preprocessed page cleanup
- candidate text aggregation can stay page-level by simple ordered
  concatenation; no tile-overlap de-duplication needed in this slice

If human wants a different baseline semantics later, that is a narrow follow-up,
not a blocker to this implementation slice.
