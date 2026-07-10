.. _runbook__bt_dictionary_structuring_workflow:

BT Dictionary Structuring Workflow
==================================

This runbook is for the Bosworth-Toller parsing workflow we are building in
this slice. It is **not** the same as ``wyrdcraeft dictionary build``.

Use this workflow when the goal is:

- keep raw Bosworth-Toller evidence visible
- compare multiple witnesses for one hard entry
- preserve attestations and unresolved text
- produce a file-first case bundle before any broad parser rewrite

One-Line Model
--------------

Do not parse ``data/oe_bt.txt`` straight into final dictionary rows.

Instead:

1. gather a small witness set for one entry
2. anchor those witnesses to the same page/region/line area
3. split the source into ordered raw fragments
4. preserve leftovers explicitly
5. record human corrections as YAML overlays
6. derive normalized structure later

Current Locked Decisions
------------------------

This workflow follows the current ADRs and handoff plan:

- first product is a **lossless source-grounded AST**
- all source text must be accounted for by typed fragments
- attestations stay in the raw layer
- multiple witnesses are required from the start
- fragment-level provenance is required
- review is witness-first
- first persistence layer is file-first case bundles
- first prototype case is ``wesan``

See:

- ``docs/adr/0004-bt-ocr-parsing-starts-with-lossless-source-grounded-ast.md``
- ``docs/adr/0005-bt-source-acquisition-uses-multi-witness-download-set.md``
- ``docs/superpowers/handoffs/2026-07-09-bt-ocr-structured-data-plan.md``

What Counts As One Unit of Work
-------------------------------

The working unit is one **case bundle**, not one database row and not one
global parser phase.

Right now the starter bundle is:

.. code-block:: text

    data/bt_cases/wesan/

That directory is the canonical place for the current prototype work.

What Each Bundle File Means
---------------------------

Using ``data/bt_cases/wesan/`` as the example:

- ``manifest.yaml``
  - bundle index
  - points at source line and witness list
- ``witnesses/*.yaml``
  - one stub or real metadata file per witness
  - says where the witness came from and how much we trust it
- ``anchors/anchors.yaml``
  - shared page/region/line or source-line anchor ids
- ``entry.raw.yaml``
  - ordered raw fragments
  - this is the lossless source-grounded layer
- ``adjudication.overlay.yaml``
  - append-only human correction layer
  - do not rewrite raw entry in place
- ``entry.normalized.yaml``
  - future derived structure
  - should stay thin until raw evidence is good
- ``review.md``
  - operator instructions and review notes

What You Actually Do
--------------------

For one hard Bosworth-Toller entry, work in this order.

Step 1: Start from a real source block
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pick one ugly entry and point the bundle at the real source text.

For the current prototype:

- source file: ``data/oe_bt.txt``
- entry: ``wesan``
- line: ``55898``

Do not start by inventing clean senses. Start from the messy source block.

Step 2: Gather witness metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Fill or refine the witness stub files under ``witnesses/``.

Preferred witness order:

1. GLP corrected text
2. IA raw page images (JP2) plus our own OCR
3. IA HOCR and ABBYY
4. local ``oe_bt.txt`` as existing text witness
5. IA ``djvu.txt`` only as fallback-only rough recall

Important: ``djvu.txt`` is not trusted primary evidence for spelling,
structure, or citations.

At this stage, you do **not** need full ingestion machinery. You only need
enough metadata to answer:

- what witness is this
- where did it come from
- how trusted is it
- what exact page or line should it line up with

Step 3: Anchor the witnesses
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before you normalize anything, make the witnesses line up.

The preferred alignment scaffold is:

- page
- region
- line

For local text-only witnesses, a source-line anchor is acceptable as an early
placeholder. For scan-backed witnesses, replace placeholders with real
page/region/line anchors as soon as possible.

Do not use headword matching as the primary alignment method. Headword matching
comes later and is too fragile in noisy OCR.

Step 4: Build the raw fragment sequence
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Edit ``entry.raw.yaml`` so it accounts for the source block in order.

The starter fragment types are intentionally small:

- ``headword``
- ``sense_label``
- ``definition_text``
- ``attestation``
- ``unclassified_remainder``

Rules:

- preserve exact diplomatic text in the raw layer
- every fragment needs provenance
- if text is unresolved, keep it as ``unclassified_remainder``
- do not silently drop text
- do not strip attestations

If you cannot safely classify a span yet, keeping it visible as leftover is the
correct move.

Step 5: Review witnesses beside raw fragments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``review.md`` as the operator reminder:

1. inspect the witness files and raw source first
2. compare witness text against fragment text
3. identify disagreements or unresolved leftovers
4. only then add overlay decisions

The review model is **review by exception**, not line-by-line manual rewrite of
the whole entry.

Step 6: Record corrections in the overlay
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Put human decisions in ``adjudication.overlay.yaml``.

Examples of valid overlay-style actions:

- accept fragment as-is
- retag fragment
- split fragment
- attach note

Do not mutate the raw source-grounded layer into a hand-cleaned latest state.
The overlay exists so we preserve machine output plus human judgment.

Step 7: Derive normalized structure later
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Only after the raw bundle is solid should ``entry.normalized.yaml`` start to
carry real structure.

That file is downstream of:

- witness gathering
- anchoring
- raw fragmenting
- adjudication

It is not the starting point.

What "Done" Looks Like For One Case
-----------------------------------

For the current slice, one case is in good shape when:

- the case bundle is understandable by a human without extra chat context
- witnesses are named and trust-ranked
- anchors are explicit
- raw fragments preserve source order
- attestations are still visible
- unresolved text is still present, not erased
- overlay is ready for review-by-exception corrections
- normalized output is still clearly derived, not pretending to be canonical truth

What Not To Do
--------------

Do not do these things in this workflow:

- do not jump straight to final dictionary rows
- do not normalize away unresolved text
- do not strip attestations for convenience
- do not trust one OCR witness by itself
- do not make SQLite the first persistence target for this slice
- do not broaden into a full parser rewrite before one case bundle works end to end

Current Practical Next Step
---------------------------

For ``wesan``, the next useful work is:

1. replace placeholder witness metadata with real acquisition details
2. add real scan-backed anchors for the same entry
3. expand ``entry.raw.yaml`` from demo fragments to the first full lossless pass
4. use ``adjudication.overlay.yaml`` only for true disagreements and uncertain spans

If you keep asking "what file should I touch next?", the answer is usually one
of these:

- ``data/bt_cases/wesan/witnesses/*.yaml``
- ``data/bt_cases/wesan/anchors/anchors.yaml``
- ``data/bt_cases/wesan/entry.raw.yaml``
- ``data/bt_cases/wesan/adjudication.overlay.yaml``
