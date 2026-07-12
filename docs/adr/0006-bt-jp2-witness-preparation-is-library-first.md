# BT JP2 witness preparation is library-first

Bosworth-Toller JP2 scan witness preparation is a library-first, BT-specific
slice that stops at image-backed witness artifacts. It does not collapse OCR
text into canonical dictionary truth, and it is not a generic OCR framework.

We chose this because whole-page OCR on dense two-column BT scans is too coarse
for witness-first review: character scale collapses under model rendering, and
page-level provenance is too weak for later page-region-line anchoring. The
product therefore needs a deterministic preparation layer that turns immutable
JP2 pages into overlapping OCR-ready tiles with explicit provenance before any
text-first structuring.

Locked consequences
-------------------

- Primary entrypoint:
  ``wyrdcraeft.services.ocr.bt_witness_prep.prepare_pages``
- Package:
  ``wyrdcraeft/services/ocr/bt_witness_prep/``
- Scope is JP2 scan witnesses only for this slice
- Raw JP2 pages remain immutable source artifacts
- Default tiling is fixed four-tile geometry:
  left/right columns, upper/lower overlapping halves
- Non-standard layouts emit explicit fallback status such as
  ``fallback_whole_page_only`` or ``unsupported_layout``; silent forced tiling
  is not allowed
- Outputs are preprocessed pages, tiles, quality-scored manifests, and anchor
  seeds under a run workspace
- OCR text produced later remains a witness, not canonical truth
- Stage B recipe validation compares candidate prep against a raw whole-page
  baseline using diacritic-sensitive CER and small-component guardrails
- Case-bundle mutation, fragment extraction, and CLI-first packaging stay
  downstream

Current prototype note
----------------------

Implemented on branch ``cmalek/bt-parsing`` (commit ``1d81cd7f``):

- library package with source enumeration, conservative preprocessing, tiling,
  quality scoring, manifest/anchor writers, and pipeline orchestration
- Stage B helpers in ``validation.py`` plus
  ``scripts/ocr/benchmark_bt_witness_prep.py``
- researcher docs under
  ``doc/source/overview/bt_ocr_witness_preparation.rst`` and
  ``doc/source/overview/bt_ocr_witness_preparation_method.rst``
- tests under ``tests/ocr/test_bt_witness_prep_*.py``

This ADR sits between ADR 0005 (multi-witness acquisition, JP2 as primary scan
witness) and ADR 0004 (lossless source-grounded AST / case-bundle structuring).

CLI follow-up
-------------

A dedicated operator CLI now exists as ``wyrdcraeft ocr bosworth-toller``.
Documented in ``doc/source/overview/command_ocr_bosworth_toller.rst``.

This does not change the library-first primary entrypoint
(``prepare_pages``) or the witness-not-truth boundary: OCR text produced by
the command remains a source witness, not canonical dictionary data.
