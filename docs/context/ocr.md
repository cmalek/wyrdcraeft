# OCR Context

## What This Capability Does

OCR workflows turn Old English PDFs into normalized text artifacts, using
`olmocr` plus a managed local proxy and post-processing passes.

## Main CLI Entrypoints

- `wyrdcraeft ocr old-english`
- `wyrdcraeft ocr proxy`

## Primary Python Entrypoints

- `wyrdcraeft.cli.ocr`
- `wyrdcraeft.services.ocr:run_old_english_ocr_pipeline`
- `wyrdcraeft.services.ocr_proxy.server`
- `wyrdcraeft.services.ocr_proxy.runtime`

## Key Files

- `wyrdcraeft/cli/ocr.py`
- `wyrdcraeft/services/ocr/old_english_pipeline.py`
- `wyrdcraeft/services/ocr_proxy/config.py`
- `wyrdcraeft/services/ocr_proxy/runtime.py`
- `doc/source/runbook/old_english_ocr_pipeline.rst`

## Inputs And Outputs

Inputs:

- input PDF
- optional output directory
- regex rules TSV
- seed wordlist TXT
- optional local model / proxy tuning flags

Outputs:

- `02_raw.txt`
- `03_normalized.txt`
- `04_unknown_tokens.tsv`
- `olmocr_workspace/` intermediate artifacts

Default output directory:

- `data/ocr/<input-pdf-stem>` under repo root

## Invariants And Sharp Edges

- `--pages` is currently rejected in `olmocr` mode; pre-slice PDF instead.
- OCR pipeline is not ingest pipeline; OCR produces text artifacts, then other
  workflows may consume them.
- Managed proxy behavior matters for completion-token clamping and conservative
  `finish_reason` rewriting.
- `skip_ocr` reuses existing workspace markdown instead of rerunning `olmocr`.
- This path invokes external tools and local services; failures are often
  environment/runtime issues, not pure parsing bugs.

## Related Docs

- [../../CONTEXT.md](../../CONTEXT.md)
- [../context/settings.md](settings.md)
- [../context/ingest.md](ingest.md)

