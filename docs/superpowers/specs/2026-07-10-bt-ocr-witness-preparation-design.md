# BT OCR Witness Preparation Design

Date: 2026-07-10
Repo: `/Users/cmalek/src/workspace/wyrdcraeft`
Focus: Build a Bosworth-Toller-specific, library-first JP2 scan
witness-preparation slice that converts raw scan pages into provenance-rich
OCR-ready tiles and anchor seeds without collapsing them into canonical text.

## Purpose

This design defines the first BT-specific OCR preparation slice for one witness
family, the raw JP2 scan witness, that sits before broad OCR parsing or
dictionary normalization.

Target outcome:

- take raw Bosworth-Toller JP2 scan pages as one primary visual witness family
- apply conservative, deterministic preprocessing tuned for dictionary pages
- split pages into OCR-friendly overlapping tiles
- score tile readability with explicit metrics instead of visual guesswork
- emit manifests and anchor seeds that preserve witness provenance
- hand those outputs to downstream OCR and case-bundle workflows without
  pretending the OCR output is canonical truth

This design is intentionally narrower than the full Bosworth-Toller structuring
workflow. It does not replace:

- [CONTEXT.md](/Users/cmalek/src/workspace/wyrdcraeft/CONTEXT.md)
- [docs/adr/0004-bt-ocr-parsing-starts-with-lossless-source-grounded-ast.md](/Users/cmalek/src/workspace/wyrdcraeft/docs/adr/0004-bt-ocr-parsing-starts-with-lossless-source-grounded-ast.md)
- [docs/adr/0005-bt-source-acquisition-uses-multi-witness-download-set.md](/Users/cmalek/src/workspace/wyrdcraeft/docs/adr/0005-bt-source-acquisition-uses-multi-witness-download-set.md)
- [doc/source/runbook/bt_dictionary_structuring_workflow.rst](/Users/cmalek/src/workspace/wyrdcraeft/doc/source/runbook/bt_dictionary_structuring_workflow.rst)

## Current Facts

- Primary raw scan witness for the main volume already exists at:
  - `data/bosworth_toller/anglosaxondictio00bosw_jp2/`
- Sample page `anglosaxondictio00bosw_0609.jp2` is `2424x3368` RGB and shows:
  - dense two-column layout
  - small serif type
  - italics and abbreviations
  - yellowed background
  - historical characters and diacritics
- Current OCR runtime in
  [wyrdcraeft/services/ocr/old_english_pipeline.py](/Users/cmalek/src/workspace/wyrdcraeft/wyrdcraeft/services/ocr/old_english_pipeline.py:1)
  already accepts `.jp2` inputs and image directories, but converts them into a
  single PDF and runs one `olmocr` pass over whole pages.
- Current OCR pipeline outputs text artifacts (`02_raw.txt`, `03_normalized.txt`)
  but does not preserve page-region tile witnesses as first-class artifacts.
- The repo glossary now explicitly centers:
  - source witnesses
  - markdown witnesses
  - witness provenance
  - page-region-line anchors
  - case bundles

Conclusion: current OCR support is useful infrastructure, but too coarse for
the witness-first BT workflow.

## Locked Decisions

- This slice is **library-first**, not CLI-first.
- This slice is **BT-specific**, not a generic OCR framework.
- This slice prepares **image-backed witnesses**, not final dictionary text.
- This slice prepares the **JP2 scan witness family only**. Other witnesses
  such as corrected text, HOCR, ABBYY, and markdown OCR stay out of scope here.
- Raw JP2 pages remain immutable source artifacts.
- Preprocessing must be **conservative**:
  - improve OCR legibility
  - never knowingly erase provenance-bearing glyph detail
- First tiling strategy is:
  - split each page into left/right columns
  - split each column into upper/lower overlapping tiles
- Overlap is required to avoid losing entries or lines at split boundaries.
- Tile-level metadata is required:
  - source page id
  - crop box
  - overlap relationships
  - preprocessing recipe id
  - quality metrics
- `olmocr` remains the primary downstream OCR target for first integration, but
  this slice must keep the OCR engine replaceable.
- OCR output generated later is a **witness**, not canonical truth.

## Problem Statement

Bosworth-Toller scan pages are too dense and too visually noisy to treat
whole-page OCR as the main evidence unit.

Whole-page OCR fails this workflow in two ways:

1. character size becomes too small after model rendering/resizing
2. provenance becomes too coarse because a whole-page witness is a poor anchor
   for later page-region-line comparison and fragment adjudication

The product therefore needs a deterministic preparation layer that improves
both OCR legibility and witness granularity before any text-first structuring
happens.

## Case-Bundle Handoff Contract

This slice must not create a dead-end artifact silo.

Its outputs are not case bundles themselves, but they must be shaped so a later
case-bundle assembly step can consume them directly as first-class inputs.

Required handoff properties:

- each emitted tile can be referenced as a future `source witness`
- each tile has enough provenance to populate bundle witness metadata
- each anchor seed has stable page/region identifiers usable by later
  `page-region-line anchor` workflows
- each run can be traced back to:
  - source scan page
  - preprocessing recipe
  - crop box
  - overlap relationships

In case-bundle terms, this slice should be able to answer:

- which scan-backed witness region produced this OCR-ready tile
- how that region maps back to the original page
- how a reviewer can compare the tile against later OCR markdown and raw source
  fragments

This slice therefore feeds future bundle work as:

```text
JP2 page witness
  -> preprocessed page witness derivative
  -> tile witness derivatives
  -> anchor seed metadata
  -> downstream OCR markdown witness generation
  -> later case-bundle witness import
```

## Recommended Architecture

Create a BT-specific package under:

```text
wyrdcraeft/services/ocr/bt_witness_prep/
```

Recommended unit boundaries:

- `source.py`
  - enumerate source scan pages and normalize page ids
- `preprocess.py`
  - conservative crop, deskew, and background normalization
- `tiling.py`
  - split pages into column and vertical-overlap tiles
- `quality.py`
  - calculate tile readability metrics and recipe scores
- `manifest.py`
  - serialize page/tile provenance and quality records
- `anchors.py`
  - emit page/region/line anchor seed records
- `models.py`
  - typed dataclasses / DTOs for run config and artifact records
- `pipeline.py`
  - orchestrate one full witness-prep run end to end

This package should be independent from:

- dictionary fragment extraction
- case-bundle adjudication logic
- SQLite persistence
- final OCR parsing into structured entries

Those layers consume the outputs of this slice later.

## Canonical Contract

Primary contract:

```text
JP2 source pages
  -> deterministic preprocessing
  -> OCR-oriented tiles
  -> tile quality metrics
  -> provenance manifests
  -> anchor seed data
```

This slice stops there.

It does **not** do these things:

- run dictionary fragment extraction
- emit `bt_entries`
- mutate `data/bt_cases/*` directly
- merge witnesses into canonical text

The required downstream compatibility contract is:

- tile/page ids are stable enough for later case-bundle import
- manifests are rich enough to become witness metadata inputs
- anchor seeds are rich enough to become later alignment scaffolding

## Artifact Model

Recommended output tree:

```text
data/bt_witness_prep/<run_id>/
  pages/
  tiles/
  manifests/
    pages.jsonl
    tiles.jsonl
  anchors/
    anchor_seeds.jsonl
  debug/
```

### Page artifact

One source page record should preserve:

- source path
- stable page id
- source dimensions
- preprocessing recipe id
- derived cropped page path
- derived preprocessed page path

### Tile artifact

One tile record should preserve:

- tile id
- source page id
- column index
- vertical part index
- crop box in source-page coordinates
- overlap links to neighboring tiles
- tile image path
- quality metrics
- OCR target role, e.g. `ocr_tile`

### Anchor seed

One anchor seed record should preserve:

- source page id
- region id
- region type such as `column_half_tile`
- bounding box
- parent-child relation between page and tile
- placeholder line anchoring fields when exact line anchors are not yet known

Anchor seed records are scaffolding, not final alignment truth.

Stable identifier requirement:

- page ids must be deterministic from source-page identity
- tile ids must be deterministic from page id plus split geometry
- region ids must be deterministic from page/tile identity
- rerunning the same source page with the same recipe and same tiling config
  must yield the same ids

These ids are the compatibility bridge into later case-bundle review and
page-region-line anchor workflows.

## Preprocessing Model

Preprocessing must improve readability while preserving small glyph details.

The first recipe family should include:

- border and margin crop
- very light deskew
- background normalization / illumination flattening
- grayscale export
- optional very mild sharpening

Avoid as defaults:

- aggressive adaptive thresholding
- strong denoise passes
- hard binarization as the only retained artifact

Reason:

- macrons, acutes, commas, semicolons, and italic strokes are evidence-bearing
  visual detail
- over-aggressive enhancement can make the image look cleaner while harming
  philological fidelity

## Tiling Strategy

First slice should use a fixed, deterministic strategy:

1. crop to text-bearing page area conservatively
2. split into left and right columns
3. split each column into upper and lower tiles
4. add vertical overlap equivalent to roughly 3-5 lines

This yields four tiles per typical page:

- `col-1-part-1`
- `col-1-part-2`
- `col-2-part-1`
- `col-2-part-2`

Future work may add adaptive tile counts based on detected line density, but
that is not required for the first slice.

Out-of-shape page handling:

- first slice explicitly targets standard two-column Bosworth-Toller dictionary
  pages
- pages that do not satisfy basic two-column assumptions are not silently
  forced through normal tiling
- instead, they must be emitted with explicit status metadata such as:
  - `unsupported_layout`
  - `needs_manual_review`
  - `fallback_whole_page_only`

The slice boundary is therefore clear:

- normal success: deterministic four-tile output
- non-standard layout: explicit fallback status plus preserved page artifact
- not allowed: silent heuristic drift into an undocumented alternate tiling
  regime

## Readability Metrics

This slice should not rely on subjective visual judgment alone.

Use a tile-quality bundle, not one single metric:

### 1. Stroke contrast score

Estimate text-stroke darkness relative to local paper background after
normalization.

Purpose:

- reward clearer foreground/background separation
- avoid global contrast heuristics that ignore local paper shading

### 2. Focus score

Use edge-energy / blur detection such as Laplacian variance.

Purpose:

- detect oversoften preprocessing
- penalize mushy glyph edges

### 3. Small-component preservation score

Estimate whether preprocessing preserves tiny dark components likely to
represent:

- macrons
- acute accents
- punctuation
- fine serif detail

Purpose:

- guard against recipes that improve apparent contrast by deleting evidence

### 4. Line separability score

Use projection-profile or related structure cues to estimate how distinctly
text lines remain separated.

Purpose:

- catch preprocessing that causes line bleed or weak baseline structure

### 5. Column contamination score

Estimate whether a tile includes excessive gutter bleed or neighboring-column
content.

Purpose:

- preserve clean reading-order cues for downstream OCR

### 6. Margin clipping score

Estimate likelihood that the crop removed meaningful edge glyphs or page text.

Purpose:

- prevent over-tight crops that silently lose evidence

### Composite tile readability score

Recommended initial weighting:

```text
tile_readability =
  0.30 stroke_contrast
  0.20 focus
  0.20 small_component_preservation
  0.15 line_separability
  0.10 column_contamination
  0.05 margin_clipping
```

Important guardrail:

Do not pick recipes by total score alone if they materially reduce
small-component preservation.

## Recipe Selection Model

Use a two-stage selection loop.

### Stage A: image-only heuristic scoring

Run multiple preprocessing recipes over a stratified page sample and compare
their quality metrics.

Use this stage to:

- eliminate obviously bad recipes quickly
- choose top candidates without expensive OCR runs

### Stage B: OCR-backed validation

Run `olmocr` only on candidate recipes and compare sample outputs against
better witnesses or corrected text.

Primary downstream evaluation metrics should include:

- CER / WER where possible
- diacritic-sensitive CER
- error counts on representative historical characters
- reading-order sanity on multi-column pages

Conclusion:

The heuristic score chooses promising inputs, but OCR-backed validation decides
the default recipe.

First-slice validation contract:

- use a fixed sample of at least 5 BT pages
- include at least:
  - 3 standard dense dictionary pages
  - 1 page with heavy italics/abbreviations
  - 1 page with visible background/shadow difficulty
- compare candidate recipes against the raw whole-page baseline
- compare OCR output against an existing better witness for the sampled region,
  such as corrected text or curated transcription slices when available
- require at least one candidate recipe to beat the raw baseline on:
  - diacritic-sensitive CER
  - or exact-match rate for a predefined historical-character token set

Recommended initial pass threshold:

- at least 10% relative improvement in diacritic-sensitive CER over raw
  whole-page OCR on the fixed validation sample
- and no page in the sample may show catastrophic small-component loss under
  reviewer inspection

## Integration Boundary With Existing OCR Pipeline

This slice should integrate cleanly with the current OCR runtime without being
trapped inside it.

Recommended integration stance:

- witness-prep library writes tile artifacts and manifests
- existing `olmocr` pipeline consumes those tiles later
- OCR execution may be wrapped by another service or CLI layer later

This keeps the boundary clean:

- witness preparation is deterministic image work
- OCR execution is model-dependent witness generation

## Testing Strategy

Testing should stay deterministic and fixture-driven.

### Unit tests

- crop math
- overlap math
- tile ordering and naming
- manifest serialization
- quality-metric calculations on tiny synthetic images

### Fixture-driven tests

Use a small real BT page sample to assert:

- deterministic page ids
- deterministic tile coordinates
- stable artifact paths
- stable quality metric ranges

### Regression tests

Freeze a few representative BT pages and ensure recipe changes do not silently:

- clip text
- remove small components
- reorder tiles

### Optional benchmark harness

Provide a small benchmark script for sampled recipe comparison over real pages.

This is useful for recipe tuning but should not block ordinary test runs.

## Non-Goals

This design does not commit first-slice work for:

- full OCR-to-fragment parsing
- direct case-bundle mutation
- OCR engine comparison at corpus scale
- adaptive ML-based crop detection
- final page-region-line alignment truth
- broad generic OCR-preprocessing abstractions for unrelated sources

## Researcher Documentation Goal

This slice should also publish a researcher-facing documentation set under:

```text
doc/source/overview/
```

Purpose:

- explain the method clearly to external researchers
- make the rationale legible, not only the code
- document the artifact contracts and validation logic
- make reimplementation and critique possible outside this repository

The documentation set should cover:

- intent and rationale
- high-level workflow
- architecture and artifact model
- preprocessing and tiling rationale
- quality-metric design and tuning logic
- validation method and limits
- explicit scope boundaries and non-goals

Expected presentation:

- narrative overview pages suitable for researchers
- UML or equivalent architecture/process diagrams
- reproducibility-oriented explanation of inputs, outputs, and decisions

This docs work belongs to the same deliverable family because the target
audience includes outside researchers, not only maintainers.

## Recommended Incremental Order

1. define typed models and output contract
2. implement deterministic source-page enumeration
3. implement conservative preprocessing on sampled BT pages
4. implement fixed four-tile page splitting with overlap
5. implement tile quality metrics and recipe scoring
6. implement manifest and anchor-seed writers
7. add sampled regression fixtures and tests
8. add optional downstream `olmocr` benchmark hook for recipe tuning
9. publish researcher-facing overview docs with rationale, diagrams, and
   reproducibility guidance

## Acceptance Criteria

This design is satisfied when all of these are true:

- JP2 source pages can be converted into deterministic BT tile artifacts
- every tile has provenance-rich metadata
- anchor seed records exist for later witness alignment
- page ids, tile ids, and region ids are stable across reruns for the same
  source page and config
- quality metrics are computed and persisted per tile
- at least one preprocessing recipe outperforms raw whole-page OCR on a fixed
  validation sample by the defined OCR-backed criterion
- outputs are shaped so they can become direct inputs to later case-bundle
  witness metadata and anchor workflows
- non-standard pages are emitted with explicit fallback status rather than
  silently forced through undocumented tiling logic
- overview docs exist that explain the rationale, architecture, artifact model,
  validation method, and reproducibility story for external researchers
- no part of the slice claims OCR text is canonical truth
