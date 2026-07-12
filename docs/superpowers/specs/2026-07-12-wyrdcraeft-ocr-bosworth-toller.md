# wyrdcraeft OCR Bosworth-Toller Command Spec

**Date:** 2026-07-12  
**Status:** locked for implementation  
**Parent context:** split BT dictionary witness OCR from literary `old-english` OCR  
**Related ADRs:** 0004, 0005, 0006  
**Related handoff:** `docs/superpowers/handoffs/2026-07-09-bt-ocr-structured-data-plan.md`

---

## Problem

The Bosworth-Toller PDF/JP2 → structured-data pipeline reused the
`wyrdcraeft ocr old-english` command surface. That command was designed for a
simpler job: OCR a literary Old English edition (for example *Beowulf* or *The
Story of Cædmon*) into continuous prose with diacritics and readable structure.

Bosworth-Toller dictionary scans need a different workflow:

- JP2 page directories, not edition PDFs
- two-column dense layout requiring tile witnesses
- provenance-first manifests and anchor seeds
- OCR text as a **witness**, not canonical dictionary truth

BT witness preparation already exists as a library (`bt_witness_prep`). This spec
adds a dedicated CLI command and narrows `old-english` back to its original
intent.

---

## Goal

Introduce `wyrdcraeft ocr bosworth-toller` for BT scan witness preparation and
optional tile OCR, while keeping `wyrdcraeft ocr old-english` focused on
literary edition PDFs.

---

## Non-goals (v1)

- lossless AST parsing or case-bundle mutation (ADR 0004 downstream)
- line-aware horizontal split placement (v2 candidate; see Known ceiling)
- full olmocr/proxy flag parity with `old-english`
- automatic JP2 zip extraction
- SQLite dictionary indexing (`wyrdcraeft dictionary build`)

---

## Target command tree

```text
wyrdcraeft ocr
├── old-english        # literary editions — narrowed in phase 3
├── bosworth-toller    # NEW — BT scan witness pipeline
└── proxy              # shared infra (unchanged)
```

---

## `wyrdcraeft ocr bosworth-toller`

### Purpose

Turn a flat directory of Bosworth-Toller `.jp2` scan pages into shareable
image-backed witness artifacts. Optionally run tile-level OCR and emit joined
page-level markdown witnesses.

The command stops before case-bundle work. OCR output remains a source witness,
not canonical dictionary data.

### Default behavior

**Prep-only.** No olmocr invocation unless `--ocr` is passed.

### Examples

```bash
# defaults: prep-only, canonical repo paths
wyrdcraeft ocr bosworth-toller

# explicit workspace
wyrdcraeft ocr bosworth-toller \
  --source-dir data/bosworth_toller/jp2 \
  --output-dir data/ocr/bosworth-toller/run-001

# smoke subset
wyrdcraeft ocr bosworth-toller --pages bt-0002,bt-0007 --limit 5

# tune horizontal overlap without code changes
wyrdcraeft ocr bosworth-toller --overlap-px 40

# add witness text
wyrdcraeft ocr bosworth-toller --ocr

# rerun OCR on an existing prep workspace
wyrdcraeft ocr bosworth-toller --skip-prep --ocr \
  --output-dir data/ocr/bosworth-toller/run-001
```

### Flags

| Flag | Default | Notes |
|------|---------|-------|
| `--source-dir` | `data/bosworth_toller/jp2` | flat `.jp2` directory |
| `--output-dir` | `data/ocr/bosworth-toller/prep` | workspace root |
| `--recipe-id` | `bt-two-column-v1` | preprocessing recipe identity |
| `--overlap-px` | `30` | vertical overlap for upper/lower column halves |
| `--pages` | all | comma-separated `page_id` slugs (`bt-0002`) |
| `--limit` | none | first *N* pages in stable filename order; applied after `--pages` |
| `--prep-only` | implicit default | explicit no-op when used alone |
| `--ocr` | off | run tile OCR and write `witnesses/` artifacts |
| `--skip-prep` | off | require existing prep tree; use with `--ocr` |
| `--force` | off | allow overwrite when output already contains prep artifacts |
| `--skip-ocr` | off | with `--ocr`, reuse cached per-tile OCR text when present |

**`--ocr` minimal runtime overrides** (fall back to `Settings` when omitted):

- `--olmocr-workers`
- `--olmocr-target-longest-image-dim`
- `--upstream-base-url`

All other proxy/olmocr tuning continues to come from `Settings`, environment
variables, or `wyrdcraeft ocr proxy`.

### Stage semantics

| Stage flag | Runs | Requires |
|------------|------|----------|
| default / `--prep-only` | `prepare_pages` | `.jp2` source dir |
| `--ocr` | tile OCR + page join | prep artifacts in `--output-dir` |
| `--skip-prep --ocr` | tile OCR + page join only | existing `manifests/`, `tiles/` |
| `--skip-ocr` | no olmocr calls | cached `witnesses/tiles/*/03_normalized.txt` |

`--ocr` without `--skip-prep` runs prep first, then OCR.

### Output layout

**Prep stage** (unchanged `prepare_pages` contract):

```text
<output-dir>/
  pages/
  tiles/
  manifests/pages.jsonl
  manifests/tiles.jsonl
  anchors/anchor_seeds.jsonl
```

**`--ocr` stage adds:**

```text
<output-dir>/
  witnesses/
    tiles/<tile_id>/
      olmocr_workspace/
      03_normalized.txt
    pages/<page_id>.md
```

Rules:

- `tile_id` uses the existing geometry slug (`bt-0002:col-1-part-2`)
- per-tile OCR reuses the `old_english` olmocr stack internally
- page join uses the same geometry reading order as
  `discover_candidate_tile_images()` (`col-1-part-1`, `col-2-part-1`,
  `col-1-part-2`, `col-2-part-2`, then whole-page fallback) — not raw JSONL
  iteration order
- joined page text is stored as `.md` for witness packaging; v1 content is
  plain joined OCR text with blank-line separators between tiles
- structure derived later, not embedded as canonical facts in filenames

### Output safety

Refuse to write when `--output-dir` already contains `manifests/` or `tiles/`
unless `--force` is passed. Error text must suggest a fresh `--output-dir` or
`--force`.

This protects the shared dev default `data/ocr/bosworth-toller/prep`.

### Input rules

- source directory must contain one or more `.jp2` files
- non-JP2 inputs are rejected by the existing enumerator contract
- fallback pages (`fallback_whole_page_only`, `unsupported_layout`) pass through
  unchanged from `bt_witness_prep`

### Horizontal split (known ceiling)

Current tiling is **geometry-only**, not line-aware:

- upper/lower split at 50% page height
- `--overlap-px` overlap band between halves
- `line_separability_score` is a post-crop quality metric, not split placement

Lines on the horizontal midline should appear intact in at least one tile because
of overlap, but dense text exactly on the midpoint can still be clipped.

**v2 candidate:** projection-profile snap to the largest horizontal whitespace
gap near page center. Out of v1 scope; document in method docs when
implemented.

---

## `wyrdcraeft ocr old-english` narrowing (phase 3)

Restore the original literary-edition intent.

| Accept | Reject |
|--------|--------|
| `.pdf` | `.jp2` (any path) |
| single loose image (`.png`, `.jpg`, `.tif`, etc.) | image **directories** |

Rejection message for BT-shaped input:

```text
JP2 scans and image directories are Bosworth-Toller witness input.
Use: wyrdcraeft ocr bosworth-toller --source-dir <jp2-dir>
```

---

## Architecture

### New / moved code

| Piece | Location | Responsibility |
|-------|----------|----------------|
| CLI command | `wyrdcraeft/cli/ocr.py` | click options, defaults, stage dispatch |
| BT OCR orchestrator | `wyrdcraeft/services/ocr/bt_witness_ocr.py` (proposed) | page filter, overlap config, prep guard, OCR stage |
| Tile OCR collaborator | promote from `scripts/ocr/benchmark_bt_witness_prep.py` | per-tile olmocr, page join, `witnesses/` writer |
| Shared olmocr options helper | `wyrdcraeft/cli/ocr.py` or small shared module | minimal override flags for both OCR commands |

### Existing code reused

- `wyrdcraeft.services.ocr.bt_witness_prep.prepare_pages`
- `BTWitnessPrepPipeline` with injected `BTTilingConfig(overlap_px=...)`
- `run_old_english_ocr_pipeline` for per-tile olmocr
- managed proxy runtime (`ocr_proxy`)

### Required library adjustments (phase 1)

`prepare_pages()` currently constructs `BTWitnessPrepPipeline(recipe=recipe)`
without tiling overrides. Phase 1 must add one of:

1. extend `BTWitnessPrepInput` with optional tiling fields, or
2. add `prepare_pages_with_config(..., tiling_config=...)`, or
3. call `BTWitnessPrepPipeline(recipe=..., tiling_config=...)` from the new
   orchestrator instead of the module-level `prepare_pages` helper

The CLI `--overlap-px` value must reach `BTTilingConfig.overlap_px`.

Page filtering (`--pages`, `--limit`) is not in the enumerator today. The new
orchestrator filters the enumerated `BTSourcePage` list **in memory** before
preprocessing. Do not copy JP2s into a temporary subset directory.

When filtering yields zero pages, fail with a clear error naming the requested
`page_id` values.

Default paths are cwd-relative, matching existing `wyrdcraeft ocr old-english`
convention. Document that operators should run from the repo root.

---

## Implementation phases

| Phase | Deliverable | Depends on |
|-------|-------------|------------|
| **1** | CLI + orchestrator: defaults, filters, `--overlap-px`, `--force`, prep-only | library tiling hook |
| **2** | `--ocr` / `--skip-prep` / `--skip-ocr`, `witnesses/` writer | phase 1 |
| **3** | narrow `old-english` input validation | none |
| **4** | Sphinx CLI docs, `docs/context/ocr.md`, `CONTEXT.md` capability map | phases 1–3 |

Phase 1 is independently shippable.

---

## Tests

### Phase 1

- CLI registration and `--help` surface
- default path resolution (`data/bosworth_toller/jp2`, `data/ocr/bosworth-toller/prep`)
- `--pages` and `--limit` filtering
- `--overlap-px` reaches tiling config (mock pipeline)
- non-empty output dir blocked without `--force`
- `--force` allows overwrite

### Phase 2

- promote `discover_candidate_tile_images`, `run_page_ocr`,
  `run_candidate_page_ocr`, and `concatenate_candidate_ocr_texts` from
  `scripts/ocr/benchmark_bt_witness_prep.py` into product code
- mocked tile OCR writes `witnesses/tiles/<tile_id>/03_normalized.txt`
- page join writes `witnesses/pages/<page_id>.md`
- `--skip-prep --ocr` requires existing manifests
- `--skip-ocr` reuses cached tile text

### Phase 3

- `old-english` rejects `.jp2`
- `old-english` rejects image directories with actionable error text

Use existing fixtures under `tests/fixtures/ocr/bt_witness_prep/`.

---

## Documentation updates

- add `doc/source/commands/ocr_bosworth_toller.rst` (or section in existing OCR docs)
- update `docs/context/ocr.md` CLI entrypoints
- update `CONTEXT.md` capability map: BT witness prep gets a CLI surface
- add ADR 0006 amendment note: CLI exists; witness-not-truth boundary unchanged

---

## Decision log

| # | Decision |
|---|----------|
| 1 | Command name: `bosworth-toller` |
| 2 | One command with stage flags, not subcommands |
| 3 | Default stage: prep-only |
| 4 | `old-english` accepts PDF + loose images only |
| 5 | OCR witness layout: `witnesses/` subtree |
| 6 | Expose `--overlap-px` on CLI |
| 7 | Support `--pages` and `--limit` |
| 8 | Defaults: `data/bosworth_toller/jp2` / `data/ocr/bosworth-toller/prep` |
| 9 | Non-empty output: refuse unless `--force` |
| 10 | `--ocr` exposes minimal olmocr/proxy overrides only |

---

## Acceptance criteria

- `wyrdcraeft ocr --help` lists `bosworth-toller`
- `wyrdcraeft ocr bosworth-toller` with defaults runs prep on JP2 source dir
- prep output matches existing `prepare_pages` artifact tree
- `--overlap-px`, `--pages`, `--limit`, and `--force` behave as specified
- `--ocr` emits `witnesses/` artifacts without mutating case bundles
- `old-english` no longer accepts JP2 directories as literary input
- quality gates pass on touched Python: `ruff`, `mypy`, `make napoleon-gate`
