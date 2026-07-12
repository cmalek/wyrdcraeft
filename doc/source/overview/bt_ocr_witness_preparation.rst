.. _overview__bt_ocr_witness_preparation:

BT OCR Witness Preparation
==========================

This page is the researcher-facing overview for preparing Internet Archive
JP2 scan witnesses of the Bosworth-Toller dictionary before OCR and case-bundle
work.

It documents the library slice in
``wyrdcraeft.services.ocr.bt_witness_prep``. For operator command usage, see
:doc:`/overview/command_ocr_bosworth_toller`. It is **not** the same workflow as
``wyrdcraeft dictionary build``.

What This Slice Does
--------------------

Given a directory of ``.jp2`` page scans, witness preparation:

1. enumerates source pages with stable ids and provenance
2. applies a conservative preprocessing recipe
3. splits standard two-column pages into four OCR tiles with vertical overlap
4. scores tile readability with deterministic quality metrics
5. writes shareable artifacts: page images, tile images, JSONL manifests, and
   anchor seeds

The public entrypoint is:

.. code-block:: python

    from pathlib import Path

    from wyrdcraeft.services.ocr.bt_witness_prep import (
        BTWitnessPrepInput,
        prepare_pages,
    )

    run = prepare_pages(
        BTWitnessPrepInput(
            source_dir=Path("path/to/jp2-pages"),
            output_dir=Path("path/to/prepared-workspace"),
            recipe_id="bt-two-column-v1",
        )
    )

``prepare_pages`` returns a typed ``BTWitnessPrepRun`` manifest. The same run
also writes the on-disk artifact tree described in
:doc:`bt_ocr_witness_preparation_method`.

Who This Is For
---------------

This documentation is for:

- researchers comparing Bosworth-Toller scan witnesses against other sources
- engineers wiring OCR into the witness-first case-bundle workflow
- operators who need reproducible image preparation before olmocr or other OCR

Operators can run :doc:`/overview/command_ocr_bosworth_toller` from the repository
root. Researchers and tests may also import the library directly, point it at
JP2 scans, and inspect the emitted manifests.

Why Witness Preparation Exists
------------------------------

Bosworth-Toller dictionary structuring in this repository is **witness-first**,
not parser-first. See ``CONTEXT.md`` for glossary terms such as **source
witness**, **witness provenance**, **page-region-line anchor**, and **case
bundle**.

The current ADRs lock this direction:

- ``docs/adr/0004-bt-ocr-parsing-starts-with-lossless-source-grounded-ast.md``
- ``docs/adr/0005-bt-source-acquisition-uses-multi-witness-download-set.md``

Witness preparation is the scan-backed front door for one witness type: our own
OCR over IA JP2 page images. It produces image artifacts and alignment seeds
that downstream case bundles can reference without treating OCR output as
canonical truth.

For the operator workflow that consumes prepared witnesses inside a case bundle,
see :doc:`/runbook/bt_dictionary_structuring_workflow`.

High-Level Workflow
-------------------

At a glance, one preparation run walks every JP2 page through the same
deterministic pipeline:

.. mermaid::

   flowchart LR
       JP2["JP2 scan directory"]
       Enum["Enumerate source pages"]
       Prep["Conservative preprocess"]
       Tile["Four-tile split or explicit fallback"]
       Score["Tile quality scoring"]
       Emit["Manifests + anchor seeds"]

       JP2 --> Enum --> Prep --> Tile --> Score --> Emit

Standard dictionary pages become **four tiles**: left column upper/lower and
right column upper/lower, with a midline gutter and vertical overlap between
upper and lower halves.

Non-standard pages do **not** silently receive forced four-tile geometry.
The tiler emits an explicit fallback status and one whole-page tile instead.

Expected Output Tree
--------------------

After ``prepare_pages`` completes, ``output_dir`` contains:

.. code-block:: text

    pages/                      # preprocessed full-page PNGs
    tiles/                      # prepared tile PNGs (four tiles or fallback)
    manifests/
        pages.jsonl             # one row per preprocessed page
        tiles.jsonl             # one row per tile with quality metadata
    anchors/
        anchor_seeds.jsonl      # one region seed per tile for alignment work

Each JSONL row is self-contained provenance. A researcher can diff two runs,
re-run OCR on ``tiles/`` only, or attach manifest rows to case-bundle witness
stubs without opening Python.

What This Slice Does Not Claim
------------------------------

Scope boundaries are intentional:

- **JP2 scan witnesses only.** The enumerator accepts ``.jp2`` files in one flat
  source directory. It does not ingest PDF bundles, HOCR, ABBYY exports, or
  ``data/oe_bt.txt`` directly.
- **OCR text remains a witness, not canonical truth.** Preparation improves the
  image inputs OCR sees. It does not produce final dictionary rows, normalized
  senses, or adjudicated fragments.
- **Fragment extraction and case-bundle integration are downstream.** Anchor
  seeds are geometry placeholders for page/region alignment. Populating
  ``entry.raw.yaml``, witness YAML stubs, and overlay adjudication belongs to
  :doc:`/runbook/bt_dictionary_structuring_workflow`.
- **No silent layout forcing.** Pages that fail layout guardrails keep explicit
  fallback statuses such as ``fallback_whole_page_only`` or
  ``unsupported_layout`` rather than being cropped into invalid four-tile grids.

Validation and Recipe Approval
------------------------------

Image preparation is Stage A. Stage B compares OCR quality on a fixed five-page
validation sample using ``scripts/ocr/benchmark_bt_witness_prep.py`` and helpers
in ``validation.py``.

A candidate preprocessing recipe **passes Stage B** when:

- mean **diacritic-sensitive CER** improves by at least **10% relative** versus
  a raw whole-page OCR baseline, and
- no page records a **small-component guardrail** failure from tile quality
  scoring

See :doc:`bt_ocr_witness_preparation_method` for metric definitions,
reproducibility steps, and architecture detail.

Related Documentation
---------------------

- :doc:`/overview/command_ocr_bosworth_toller` — operator command guide for
  ``wyrdcraeft ocr bosworth-toller``
- :doc:`bt_ocr_witness_preparation_method` — architecture, artifact model,
  preprocessing and tiling rationale, quality metrics, validation methodology,
  limits, and reproducibility
- :doc:`/runbook/bt_dictionary_structuring_workflow` — witness-first case-bundle
  operator workflow
- :doc:`/runbook/old_english_ocr_pipeline` — olmocr-backed OCR execution used
  after tiles are prepared
- ``CONTEXT.md`` — project glossary for witness, anchor, and case-bundle terms
