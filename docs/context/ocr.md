# OCR Context

## What This Capability Does

OCR workflows turn Old English PDFs into normalized text artifacts, using
`olmocr` plus a managed local proxy and post-processing passes.

Separately, Bosworth-Toller JP2 witness preparation is a library-first slice
that turns immutable scan pages into overlapping OCR-ready tiles, quality
manifests, and anchor seeds without collapsing OCR text into canonical
dictionary truth.

## Main CLI Entrypoints

- `wyrdcraeft ocr old-english`
- `wyrdcraeft ocr proxy`

BT JP2 witness preparation has no dedicated CLI yet; call the library
entrypoint directly.

## Primary Python Entrypoints

- `wyrdcraeft.cli.ocr`
- `wyrdcraeft.services.ocr:run_old_english_ocr_pipeline`
- `wyrdcraeft.services.ocr.bt_witness_prep:prepare_pages`
- `wyrdcraeft.services.ocr_proxy.server`
- `wyrdcraeft.services.ocr_proxy.runtime`

## Key Files

- `wyrdcraeft/cli/ocr.py`
- `wyrdcraeft/services/ocr/old_english_pipeline.py`
- `wyrdcraeft/services/ocr/bt_witness_prep/`
- `scripts/ocr/benchmark_bt_witness_prep.py`
- `wyrdcraeft/services/ocr_proxy/config.py`
- `wyrdcraeft/services/ocr_proxy/runtime.py`
- `doc/source/runbook/old_english_ocr_pipeline.rst`
- `doc/source/overview/bt_ocr_witness_preparation.rst`
- `doc/source/overview/bt_ocr_witness_preparation_method.rst`
- `docs/adr/0006-bt-jp2-witness-preparation-is-library-first.md`

## Inputs And Outputs

PDF / general OCR path inputs:

- input PDF
- optional output directory
- regex rules TSV
- seed wordlist TXT
- optional local model / proxy tuning flags

PDF / general OCR path outputs:

- `02_raw.txt`
- `03_normalized.txt`
- `04_unknown_tokens.tsv`
- `olmocr_workspace/` intermediate artifacts

Default output directory for that path:

- `data/ocr/<input-pdf-stem>` under repo root

BT JP2 witness-prep path inputs:

- directory of `.jp2` scan pages
- preprocessing recipe id / config
- output workspace directory

BT JP2 witness-prep path outputs:

- `pages/` preprocessed page images
- `tiles/` overlapping column-half tiles
- `manifests/pages.jsonl`
- `manifests/tiles.jsonl`
- `anchors/anchor_seeds.jsonl`

## Invariants And Sharp Edges

- `--pages` is currently rejected in `olmocr` mode; pre-slice PDF instead.
- OCR pipeline is not ingest pipeline; OCR produces text artifacts, then other
  workflows may consume them.
- Managed proxy behavior matters for completion-token clamping and conservative
  `finish_reason` rewriting.
- `skip_ocr` reuses existing workspace markdown instead of rerunning `olmocr`.
- This path invokes external tools and local services; failures are often
  environment/runtime issues, not pure parsing bugs.
- BT witness prep is JP2-only and library-first; non-standard pages emit
  explicit fallback status instead of silent forced tiling.
- OCR text from later stages remains a witness, not canonical dictionary truth.
- Stage B recipe validation requires at least 10% relative diacritic-sensitive
  CER improvement over the raw whole-page baseline and no catastrophic
  small-component guardrail failure.

## Related Docs

- [../../CONTEXT.md](../../CONTEXT.md)
- [../context/settings.md](settings.md)
- [../context/ingest.md](ingest.md)
- [../adr/0004-bt-ocr-parsing-starts-with-lossless-source-grounded-ast.md](../adr/0004-bt-ocr-parsing-starts-with-lossless-source-grounded-ast.md)
- [../adr/0005-bt-source-acquisition-uses-multi-witness-download-set.md](../adr/0005-bt-source-acquisition-uses-multi-witness-download-set.md)
- [../adr/0006-bt-jp2-witness-preparation-is-library-first.md](../adr/0006-bt-jp2-witness-preparation-is-library-first.md)
