# BT OCR Witness Preparation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Bosworth-Toller-specific, library-first witness-preparation slice that turns raw JP2 scan pages into deterministic OCR-ready tiles, quality-scored manifests, and anchor seed artifacts for downstream witness-first OCR workflows.

**Architecture:** Keep one deterministic pipeline, but split responsibilities into focused units: source-page enumeration, conservative preprocessing, fixed column/half tiling, tile-quality scoring, and manifest/anchor serialization. Stop at image-backed witness artifacts; do not collapse outputs into canonical text or direct dictionary rows.

**Tech Stack:** Python 3.11+, Pillow, OpenCV (`opencv-python`), NumPy, dataclasses, JSONL/YAML serialization, pytest, `.venv/bin/ruff`, `.venv/bin/mypy`, `make napoleon-gate`.

---

## Spec anchors

- Root glossary: [/Users/cmalek/src/workspace/wyrdcraeft/CONTEXT.md](/Users/cmalek/src/workspace/wyrdcraeft/CONTEXT.md)
- Architecture decision: [/Users/cmalek/src/workspace/wyrdcraeft/docs/adr/0004-bt-ocr-parsing-starts-with-lossless-source-grounded-ast.md](/Users/cmalek/src/workspace/wyrdcraeft/docs/adr/0004-bt-ocr-parsing-starts-with-lossless-source-grounded-ast.md)
- Source acquisition decision: [/Users/cmalek/src/workspace/wyrdcraeft/docs/adr/0005-bt-source-acquisition-uses-multi-witness-download-set.md](/Users/cmalek/src/workspace/wyrdcraeft/docs/adr/0005-bt-source-acquisition-uses-multi-witness-download-set.md)
- Workflow runbook: [/Users/cmalek/src/workspace/wyrdcraeft/doc/source/runbook/bt_dictionary_structuring_workflow.rst](/Users/cmalek/src/workspace/wyrdcraeft/doc/source/runbook/bt_dictionary_structuring_workflow.rst)
- Design doc: [/Users/cmalek/src/workspace/wyrdcraeft/docs/superpowers/specs/2026-07-10-bt-ocr-witness-preparation-design.md](/Users/cmalek/src/workspace/wyrdcraeft/docs/superpowers/specs/2026-07-10-bt-ocr-witness-preparation-design.md)

## Locked decisions (do not re-litigate)

1. This slice is library-first.
2. This slice is BT-specific, not a generic OCR-preprocessing framework.
3. Raw JP2 pages remain immutable source witnesses.
4. First tiling strategy is fixed:
   - left/right columns
   - upper/lower overlapping halves
5. This slice stops at image-backed witness artifacts plus manifests/anchor seeds.
6. OCR text remains downstream witness data, not canonical truth.
7. Recipe scoring is heuristic-first, OCR-validated second.
8. Small-component preservation is a guardrail metric, not an optional nice-to-have.

## File map

### Runtime package

- Create: `wyrdcraeft/services/ocr/bt_witness_prep/__init__.py`
- Create: `wyrdcraeft/services/ocr/bt_witness_prep/models.py`
- Create: `wyrdcraeft/services/ocr/bt_witness_prep/source.py`
- Create: `wyrdcraeft/services/ocr/bt_witness_prep/preprocess.py`
- Create: `wyrdcraeft/services/ocr/bt_witness_prep/tiling.py`
- Create: `wyrdcraeft/services/ocr/bt_witness_prep/quality.py`
- Create: `wyrdcraeft/services/ocr/bt_witness_prep/manifest.py`
- Create: `wyrdcraeft/services/ocr/bt_witness_prep/anchors.py`
- Create: `wyrdcraeft/services/ocr/bt_witness_prep/pipeline.py`

### Tests and fixtures

- Create: `tests/ocr/test_bt_witness_prep_source.py`
- Create: `tests/ocr/test_bt_witness_prep_preprocess.py`
- Create: `tests/ocr/test_bt_witness_prep_tiling.py`
- Create: `tests/ocr/test_bt_witness_prep_quality.py`
- Create: `tests/ocr/test_bt_witness_prep_manifest.py`
- Create: `tests/ocr/test_bt_witness_prep_validation.py`
- Create: `tests/fixtures/ocr/bt_witness_prep/`
- Create: `tests/fixtures/ocr/bt_witness_prep/validation_manifest.json`
- Create: `tests/fixtures/ocr/bt_witness_prep/transcriptions/`

### Optional scripts / docs follow-up

- Create later if needed: `scripts/ocr/benchmark_bt_witness_prep.py`
- Modify later if needed: `wyrdcraeft/services/ocr/__init__.py`
- Modify later if needed: `doc/source/runbook/bt_dictionary_structuring_workflow.rst`
- Create later in docs phase: `doc/source/overview/bt_ocr_witness_preparation.rst`
- Create later in docs phase: `doc/source/overview/bt_ocr_witness_preparation_method.rst`
- Modify later in docs phase: `doc/source/index.rst`

## Execution order

Phases are designed for subagents. Each phase should leave behind passing tests
and a reviewable artifact boundary.

Do not parallelize phases 1-4. Phase 5 can begin after phase 4 lands.

### Task 1: Establish package contract and typed models

**Files:**
- Create: `wyrdcraeft/services/ocr/bt_witness_prep/__init__.py`
- Create: `wyrdcraeft/services/ocr/bt_witness_prep/models.py`
- Test: `tests/ocr/test_bt_witness_prep_manifest.py`

- [ ] **Step 1: Write failing model/contract tests**

Add tests covering:

- stable page id formatting
- tile id formatting
- required provenance fields on page and tile records
- JSON-serializable DTO behavior

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
.venv/bin/pytest tests/ocr/test_bt_witness_prep_manifest.py -q
```

Expected: FAIL because package/models do not exist yet.

- [ ] **Step 3: Implement minimal typed models**

Add dataclasses or equivalent for:

- `BTWitnessPrepInput`
- `BTSourcePage`
- `BTPreprocessedPage`
- `BTTile`
- `BTTileQuality`
- `BTAnchorSeed`
- `BTWitnessPrepRun`

Keep models small and explicit.

- [ ] **Step 4: Run focused tests**

Run:

```bash
.venv/bin/pytest tests/ocr/test_bt_witness_prep_manifest.py -q
```

Expected: PASS

- [ ] **Step 5: Run style/type gates on touched files**

Run:

```bash
.venv/bin/ruff check wyrdcraeft/services/ocr/bt_witness_prep tests/ocr/test_bt_witness_prep_manifest.py
.venv/bin/mypy wyrdcraeft/services/ocr/bt_witness_prep
```

Expected: PASS

### Task 2: Build deterministic source-page enumeration

**Files:**
- Create: `wyrdcraeft/services/ocr/bt_witness_prep/source.py`
- Create: `tests/ocr/test_bt_witness_prep_source.py`
- Test fixture dir: `tests/fixtures/ocr/bt_witness_prep/`

- [ ] **Step 1: Write failing source enumeration tests**

Cover:

- directory scan finds `.jp2` pages in stable sorted order
- unsupported files are ignored
- page ids derive deterministically from filenames
- missing/empty directory raises clear error

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
.venv/bin/pytest tests/ocr/test_bt_witness_prep_source.py -q
```

Expected: FAIL

- [ ] **Step 3: Implement page enumeration**

Add minimal source service that:

- scans a directory
- recognizes BT page files
- reads dimensions via Pillow
- returns typed `BTSourcePage` records

- [ ] **Step 4: Run focused tests**

Run:

```bash
.venv/bin/pytest tests/ocr/test_bt_witness_prep_source.py -q
```

Expected: PASS

- [ ] **Step 5: Run narrow quality gates**

Run:

```bash
.venv/bin/ruff check wyrdcraeft/services/ocr/bt_witness_prep/source.py tests/ocr/test_bt_witness_prep_source.py
.venv/bin/mypy wyrdcraeft/services/ocr/bt_witness_prep/source.py
```

Expected: PASS

### Task 3: Implement conservative preprocessing

**Files:**
- Create: `wyrdcraeft/services/ocr/bt_witness_prep/preprocess.py`
- Create: `tests/ocr/test_bt_witness_prep_preprocess.py`
- Possibly extend: `tests/fixtures/ocr/bt_witness_prep/`

- [ ] **Step 1: Write failing preprocessing tests**

Cover:

- crop box is deterministic for fixture page
- preprocessing preserves output dimensions/contracts
- recipe id recorded on result
- grayscale/background-normalized output path gets produced
- representative regression fixture pages preserve expected crop bounds
- representative regression fixture pages do not show silent catastrophic
  clipping in protected regions

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
.venv/bin/pytest tests/ocr/test_bt_witness_prep_preprocess.py -q
```

Expected: FAIL

- [ ] **Step 3: Implement preprocessing service**

Implement conservative recipe support:

- margin crop
- light deskew hook or no-op placeholder with explicit contract
- background normalization
- grayscale export
- optional mild sharpen

Prefer explicit recipe configuration objects over loose kwargs.

- [ ] **Step 4: Run focused tests**

Run:

```bash
.venv/bin/pytest tests/ocr/test_bt_witness_prep_preprocess.py -q
```

Expected: PASS

- [ ] **Step 5: Run narrow gates**

Run:

```bash
.venv/bin/ruff check wyrdcraeft/services/ocr/bt_witness_prep/preprocess.py tests/ocr/test_bt_witness_prep_preprocess.py
.venv/bin/mypy wyrdcraeft/services/ocr/bt_witness_prep/preprocess.py
```

Expected: PASS

### Task 4: Implement fixed four-tile page splitting with overlap

**Files:**
- Create: `wyrdcraeft/services/ocr/bt_witness_prep/tiling.py`
- Create: `tests/ocr/test_bt_witness_prep_tiling.py`

- [ ] **Step 1: Write failing tiling tests**

Cover:

- page splits into exactly four tiles by default
- tile order is stable:
  - `col-1-part-1`
  - `col-1-part-2`
  - `col-2-part-1`
  - `col-2-part-2`
- overlap coordinates are correct
- neighboring-column contamination guardrails are respected structurally
- non-standard pages emit explicit fallback status instead of pretending to
  produce normal four-tile output

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
.venv/bin/pytest tests/ocr/test_bt_witness_prep_tiling.py -q
```

Expected: FAIL

- [ ] **Step 3: Implement deterministic tiling**

Add tiler that:

- splits preprocessed page into two columns
- splits each column into upper/lower halves
- adds configurable overlap
- emits `BTTile` records plus tile image files
- emits explicit fallback page/tile status metadata when a page fails the
  basic two-column layout assumptions

- [ ] **Step 4: Run focused tests**

Run:

```bash
.venv/bin/pytest tests/ocr/test_bt_witness_prep_tiling.py -q
```

Expected: PASS

- [ ] **Step 5: Run narrow gates**

Run:

```bash
.venv/bin/ruff check wyrdcraeft/services/ocr/bt_witness_prep/tiling.py tests/ocr/test_bt_witness_prep_tiling.py
.venv/bin/mypy wyrdcraeft/services/ocr/bt_witness_prep/tiling.py
```

Expected: PASS

### Task 5: Implement tile quality metrics and composite scoring

**Files:**
- Create: `wyrdcraeft/services/ocr/bt_witness_prep/quality.py`
- Create: `tests/ocr/test_bt_witness_prep_quality.py`

- [ ] **Step 1: Write failing quality tests**

Cover:

- `stroke_contrast_score`
- `focus_score`
- `small_component_preservation_score`
- `line_separability_score`
- `column_contamination_score`
- `margin_clipping_score`
- composite readability score

Use tiny deterministic fixtures or synthetic arrays where possible.
Also add at least one representative regression fixture asserting that a
preprocessing change cannot silently improve composite score while destroying
small components beyond the allowed guardrail.

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
.venv/bin/pytest tests/ocr/test_bt_witness_prep_quality.py -q
```

Expected: FAIL

- [ ] **Step 3: Implement metric calculators**

Keep implementation deterministic and documented.

Guardrail:

- composite score must not hide catastrophic small-component loss

- [ ] **Step 4: Run focused tests**

Run:

```bash
.venv/bin/pytest tests/ocr/test_bt_witness_prep_quality.py -q
```

Expected: PASS

- [ ] **Step 5: Run narrow gates**

Run:

```bash
.venv/bin/ruff check wyrdcraeft/services/ocr/bt_witness_prep/quality.py tests/ocr/test_bt_witness_prep_quality.py
.venv/bin/mypy wyrdcraeft/services/ocr/bt_witness_prep/quality.py
```

Expected: PASS

### Task 6: Implement manifest and anchor-seed writers

**Files:**
- Create: `wyrdcraeft/services/ocr/bt_witness_prep/manifest.py`
- Create: `wyrdcraeft/services/ocr/bt_witness_prep/anchors.py`
- Extend: `tests/ocr/test_bt_witness_prep_manifest.py`

- [ ] **Step 1: Write failing serialization tests**

Cover:

- `pages.jsonl` rows contain source and recipe provenance
- `tiles.jsonl` rows contain crop, overlap, and quality metadata
- `anchor_seeds.jsonl` rows contain page/region hierarchy
- serialization order is deterministic

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
.venv/bin/pytest tests/ocr/test_bt_witness_prep_manifest.py -q
```

Expected: FAIL

- [ ] **Step 3: Implement writers**

Add JSONL writers for:

- page manifest
- tile manifest
- anchor seed manifest

Do not add database persistence in this task.

- [ ] **Step 4: Run focused tests**

Run:

```bash
.venv/bin/pytest tests/ocr/test_bt_witness_prep_manifest.py -q
```

Expected: PASS

- [ ] **Step 5: Run narrow gates**

Run:

```bash
.venv/bin/ruff check wyrdcraeft/services/ocr/bt_witness_prep/manifest.py wyrdcraeft/services/ocr/bt_witness_prep/anchors.py tests/ocr/test_bt_witness_prep_manifest.py
.venv/bin/mypy wyrdcraeft/services/ocr/bt_witness_prep/manifest.py wyrdcraeft/services/ocr/bt_witness_prep/anchors.py
```

Expected: PASS

### Task 7: Add fixed validation sample contract and comparison-witness fixtures

**Files:**
- Create: `tests/fixtures/ocr/bt_witness_prep/validation_manifest.json`
- Create: `tests/fixtures/ocr/bt_witness_prep/transcriptions/`
- Create: `tests/ocr/test_bt_witness_prep_validation.py`

- [ ] **Step 1: Write the validation-sample contract**

Create `validation_manifest.json` defining the fixed 5-page sample required by
the approved spec. It must include:

- 3 standard dense dictionary pages
- 1 page heavy in italics/abbreviations
- 1 page with visible background/shadow difficulty

For each page, record:

- source filename
- page classification
- whether a comparison witness exists
- comparison witness path when available

- [ ] **Step 2: Add minimal comparison-witness fixtures**

Create small curated transcription slices or other better-witness text files
for the sampled regions where OCR-backed comparison is required.

- [ ] **Step 3: Write failing validation-fixture tests**

Assert:

- exactly 5 pages are declared
- category coverage matches the approved spec
- referenced comparison witness files exist when marked available

- [ ] **Step 4: Run tests to verify failure**

Run:

```bash
.venv/bin/pytest tests/ocr/test_bt_witness_prep_validation.py -q
```

Expected: FAIL until the manifest and fixtures are complete.

- [ ] **Step 5: Make tests pass**

Run:

```bash
.venv/bin/pytest tests/ocr/test_bt_witness_prep_validation.py -q
```

Expected: PASS

- [ ] **Step 6: Run narrow gates**

Run:

```bash
.venv/bin/ruff check tests/ocr/test_bt_witness_prep_validation.py
```

Expected: PASS

### Task 8: Wire end-to-end pipeline orchestration

**Files:**
- Create: `wyrdcraeft/services/ocr/bt_witness_prep/pipeline.py`
- Modify: `wyrdcraeft/services/ocr/bt_witness_prep/__init__.py`
- Possibly modify: `wyrdcraeft/services/ocr/__init__.py`

- [ ] **Step 1: Write failing end-to-end pipeline test**

Add a focused test that:

- enumerates fixture page(s)
- preprocesses them
- tiles them
- scores tiles
- writes manifests
- returns a typed run result
- returns explicit fallback status for non-standard layout pages

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
.venv/bin/pytest tests/ocr -q
```

Expected: FAIL

- [ ] **Step 3: Implement pipeline orchestrator**

Expose one main entrypoint, e.g.:

```python
def prepare_pages(input_config: BTWitnessPrepInput) -> BTWitnessPrepRun:
    ...
```

Keep orchestration readable; do not push all behavior into one file.

- [ ] **Step 4: Run focused OCR prep test suite**

Run:

```bash
.venv/bin/pytest tests/ocr -q
```

Expected: PASS

- [ ] **Step 5: Run repo-required Python gates**

Run:

```bash
.venv/bin/ruff check wyrdcraeft/services/ocr/bt_witness_prep tests/ocr
.venv/bin/mypy wyrdcraeft/services/ocr/bt_witness_prep
make napoleon-gate
```

Expected: PASS, or report unrelated/pre-existing failures separately.

### Task 9: Implement Stage B OCR-backed recipe validation

**Files:**
- Create: `scripts/ocr/benchmark_bt_witness_prep.py`
- Extend or create helpers in: `wyrdcraeft/services/ocr/bt_witness_prep/quality.py`
- Extend: `tests/ocr/test_bt_witness_prep_validation.py`

- [ ] **Step 1: Write failing OCR-validation tests for the contract layer**

Add tests for helper logic that:

- loads the fixed validation sample manifest
- pairs candidate recipes with raw whole-page baseline runs
- loads comparison witness text when available
- records diacritic-sensitive comparison metrics deterministically from supplied
  text inputs

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
.venv/bin/pytest tests/ocr/test_bt_witness_prep_validation.py -q
```

Expected: FAIL

- [ ] **Step 3: Implement OCR-backed validation harness**

Make `scripts/ocr/benchmark_bt_witness_prep.py` able to:

- run the fixed 5-page sample
- compare candidate recipes against the raw whole-page baseline
- call downstream `olmocr` using prepared page/tile inputs
- read comparison witness text where available
- compute and emit:
  - diacritic-sensitive CER
  - exact-match rate for predefined historical-character token set
- rank candidate recipes against the approved pass rule

- [ ] **Step 4: Document pass/fail rule in emitted summary**

Ensure summary output records whether a recipe meets:

- at least 10% relative improvement in diacritic-sensitive CER over the raw
  whole-page baseline
- and no catastrophic reviewer-visible small-component loss flags

- [ ] **Step 5: Run a smoke benchmark on a tiny subset if feasible**

If local OCR runtime is available, run a reduced smoke check and confirm:

- harness runs
- summary file emitted
- baseline vs candidate comparison recorded

If live OCR runtime is not available, document that explicitly and keep helper
tests passing.

### Task 10: Optional sampled recipe-tuning ergonomics

This task is optional and non-blocking after tasks 1-9 are complete.

**Files:**
- Modify: `scripts/ocr/benchmark_bt_witness_prep.py`
- Possibly add tests if harness has deterministic helper functions

- [ ] **Step 1: Write smallest useful harness contract**

Decide and document:

- input page subset selection
- recipe list input
- output summary JSON path
- optional debug image export

- [ ] **Step 2: Implement harness**

Make it able to:

- run a few recipes over a sample set
- emit metric summaries
- rank candidates by heuristic score

Do not widen scope beyond the already-required validation harness.

- [ ] **Step 3: Add optional ergonomics improvements**

Document or add usability improvements such as:

- easier recipe selection flags
- better summary formatting
- optional debug-image browsing outputs

### Task 11: Publish researcher-facing overview documentation

This task is part of the same slice and should land after the core library and
required validation work are complete.

**Files:**
- Create: `doc/source/overview/bt_ocr_witness_preparation.rst`
- Create: `doc/source/overview/bt_ocr_witness_preparation_method.rst`
- Modify: `doc/source/index.rst`

- [ ] **Step 1: Draft the overview page structure**

Create one reader-oriented landing page and one method/architecture page.

Recommended split:

- `bt_ocr_witness_preparation.rst`
  - what this workflow is
  - who it is for
  - why it exists
  - high-level workflow
  - links to deeper method details
- `bt_ocr_witness_preparation_method.rst`
  - architecture
  - artifact model
  - preprocessing rationale
  - tiling rationale
  - quality metrics
  - validation methodology
  - limits and non-goals

- [ ] **Step 2: Add UML / workflow diagrams**

Include at least:

- one component/architecture diagram
- one process/workflow diagram

Use repo-supported Sphinx diagram tooling already present in the docs stack.

- [ ] **Step 3: Write rationale and reproducibility sections**

Document clearly:

- why whole-page OCR is insufficient for this source
- why witness-first artifacts matter
- why tile quality metrics exist
- how another researcher could reproduce the workflow
- what outputs they should expect

- [ ] **Step 4: Document scope boundaries and claims**

State explicitly:

- this slice prepares JP2 scan witnesses only
- OCR text remains a witness, not canonical truth
- later fragment extraction and case-bundle integration are downstream work

- [ ] **Step 5: Wire pages into Sphinx navigation**

Update `doc/source/index.rst` so the new pages appear in the published docs in
one explicit destination. For this slice, place them under the `Development`
documentation tree alongside workflow/runbook material rather than under CLI
usage pages.

- [ ] **Step 6: Build or inspect docs if feasible**

Run the repo’s normal docs validation/build command if available, or at least
check for obvious Sphinx/reStructuredText errors in the touched pages.

- [ ] **Step 7: Run narrow quality gates on touched docs**

Run any docs-specific validation the repo normally uses, plus:

```bash
make napoleon-gate
```

Expected: PASS, or report unrelated/pre-existing failures separately.

- [ ] **Step 4: Run script smoke check if feasible**

Run a tiny sample invocation and confirm:

- summary file emitted
- no crash on fixture pages

## Subagent dispatch recommendation

Recommended subagent sequence:

1. `models-contract` subagent
2. `source-enumeration` subagent
3. `preprocess` subagent
4. `tiling` subagent
5. `quality-metrics` subagent
6. `manifest-anchors` subagent
7. `validation-fixtures` subagent
8. `pipeline-integration` subagent
9. `ocr-validation` subagent
10. `benchmark-ergonomics` subagent (optional)
11. `researcher-docs` subagent

Each subagent should receive:

- exact task section from this plan
- exact file list
- exact tests/commands to run
- reminder that this slice stops before OCR text parsing

## Review checkpoints

After each task:

- inspect file boundaries stayed cohesive
- inspect tests prove one responsibility cleanly
- verify no task drifted into parser/case-bundle mutation work
- verify provenance fields remain explicit

After tasks 4, 5, 8, and 9:

- do a human sanity check on actual tile outputs and manifests
- confirm readability tuning did not erase small visual evidence

## Final verification bundle

Before calling the slice complete, run:

```bash
.venv/bin/pytest tests/ocr -q
.venv/bin/ruff check wyrdcraeft/services/ocr/bt_witness_prep tests/ocr scripts/ocr/benchmark_bt_witness_prep.py
.venv/bin/mypy wyrdcraeft/services/ocr/bt_witness_prep
make napoleon-gate
```

Then perform one manual artifact inspection on a real BT sample page:

- source JP2
- preprocessed page
- four tiles
- `tiles.jsonl`
- `anchor_seeds.jsonl`

## Expected first-slice outcome

When this plan is complete, the repo should have:

- a reusable BT witness-prep library
- deterministic tile artifacts from JP2 pages
- quality-scored manifests
- anchor seed outputs for downstream witness alignment
- explicit fallback metadata for non-standard pages
- a fixed OCR-backed validation sample and comparison-witness contract
- one required Stage B OCR-backed validation run path that compares candidate
  recipes to the raw whole-page baseline
- overview docs that explain rationale, UML/workflow, artifact contracts,
  validation method, and reproducibility for external researchers
- no false claim that OCR text or normalized text is canonical truth
