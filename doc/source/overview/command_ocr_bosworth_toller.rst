``wyrdcraeft ocr bosworth-toller``
====================================

This command prepares Bosworth-Toller Internet Archive JP2 scan witnesses for
OCR and case-bundle work. It is **not** the literary Old English edition
pipeline; use :doc:`/overview/command_ocr_old_english` for edition PDFs and
single loose page images.

Purpose
-------

Given a flat directory of ``.jp2`` dictionary page scans, the command:

1. enumerates source pages with stable ids and provenance
2. applies conservative preprocessing and fixed four-tile column splitting
3. writes shareable prep artifacts: page images, tile images, JSONL manifests,
   and anchor seeds
4. optionally runs tile-level OCR and emits joined page markdown witnesses

Default behavior is **prep-only**. OCR text remains a **witness**, not
canonical dictionary truth. The command stops before case-bundle structuring.

Run from the **repository root** so default paths resolve correctly. Extract
the Bosworth-Toller JP2 archive into ``data/bosworth_toller/jp2`` before the
first run.

Command usage
-------------

.. code-block:: bash

    wyrdcraeft ocr bosworth-toller [OPTIONS]

Options
-------

- ``--source-dir PATH``: flat directory of Bosworth-Toller ``.jp2`` scan pages.
  Default: ``data/bosworth_toller/jp2``.
- ``--output-dir PATH``: witness-prep workspace root.
  Default: ``data/ocr/bosworth-toller/prep``.
- ``--recipe-id TEXT``: preprocessing recipe identifier.
  Default: ``bt-two-column-v1``.
- ``--overlap-px INT``: vertical overlap in pixels between upper and lower
  column halves. Default: ``30``.
- ``--pages TEXT``: comma-separated ``page_id`` slugs to prepare
  (for example ``bt-0002,bt-0007``). Default: all enumerated pages.
- ``--limit INT``: maximum number of pages to prepare after ``--pages``
  filtering. Default: no limit.
- ``--prep-only / --no-prep-only``: explicit prep-only stage flag.
  Default: ``--prep-only`` (no olmocr invocation).
- ``--ocr / --no-ocr``: run tile OCR and write ``witnesses/`` artifacts after
  prep. Default: ``--no-ocr``.
- ``--skip-prep``: with ``--ocr``, require existing ``manifests/`` and
  ``tiles/`` under ``--output-dir`` instead of running prep.
- ``--skip-ocr``: with ``--ocr``, reuse cached
  ``witnesses/tiles/<tile_id>/03_normalized.txt`` files instead of calling
  olmocr.
- ``--olmocr-workers INT``: worker count forwarded to ``olmocr.pipeline``.
  Falls back to ``Settings`` when omitted.
- ``--olmocr-target-longest-image-dim INT``: raster dimension forwarded to
  ``olmocr.pipeline``. Falls back to ``Settings`` when omitted.
- ``--upstream-base-url TEXT``: upstream OpenAI-compatible base URL for the
  managed proxy. Falls back to ``Settings`` when omitted.
- ``--force / --no-force``: overwrite an existing witness-prep workspace that
  already contains ``manifests/`` or ``tiles/``. Default: ``--no-force``.

Other proxy and olmocr tuning continues to come from ``Settings``, environment
variables, or :doc:`/runbook/old_english_ocr_pipeline` proxy setup.

Stage semantics
---------------

+---------------------------+-----------------------------------------------+
| Invocation                | Runs                                          |
+===========================+===============================================+
| default / ``--prep-only`` | ``prepare_pages`` on ``--source-dir``         |
+---------------------------+-----------------------------------------------+
| ``--ocr``                 | prep (unless ``--skip-prep``), then tile OCR  |
+---------------------------+-----------------------------------------------+
| ``--skip-prep --ocr``     | tile OCR + page join only                     |
+---------------------------+-----------------------------------------------+
| ``--skip-ocr`` (with OCR) | page join from cached per-tile OCR text       |
+---------------------------+-----------------------------------------------+

Output safety
-------------

The command refuses to write when ``--output-dir`` already contains
``manifests/`` or ``tiles/`` unless ``--force`` is passed. Use a fresh
``--output-dir`` or pass ``--force`` to reuse the shared dev default
``data/ocr/bosworth-toller/prep``.

Output trees
------------

**Prep stage** (default):

.. code-block:: text

    <output-dir>/
      pages/                      # preprocessed full-page PNGs
      tiles/                      # prepared tile PNGs (four tiles or fallback)
      manifests/
        pages.jsonl               # one row per preprocessed page
        tiles.jsonl               # one row per tile with quality metadata
      anchors/
        anchor_seeds.jsonl        # one region seed per tile for alignment work

**With ``--ocr``** (adds):

.. code-block:: text

    <output-dir>/
      witnesses/
        tiles/<tile_id>/
          olmocr_workspace/
          03_normalized.txt
        pages/<page_id>.md

Joined page markdown uses geometry reading order
(``col-1-part-1``, ``col-2-part-1``, ``col-1-part-2``, ``col-2-part-2``, then
whole-page fallback), not raw manifest iteration order.

Known ceiling
-------------

Current tiling is **geometry-only**, not line-aware:

- upper/lower split at 50% page height
- ``--overlap-px`` overlap band between halves
- ``line_separability_score`` is a post-crop quality metric, not split placement

Dense text exactly on the horizontal midline can still be clipped in both tiles.
Line-aware horizontal snap is a v2 candidate; see
:doc:`/overview/bt_ocr_witness_preparation_method`.

Examples
--------

Defaults (prep-only on canonical repo paths):

.. code-block:: bash

    wyrdcraeft ocr bosworth-toller

Smoke subset:

.. code-block:: bash

    wyrdcraeft ocr bosworth-toller --pages bt-0002,bt-0007 --limit 5

Tune vertical overlap:

.. code-block:: bash

    wyrdcraeft ocr bosworth-toller --overlap-px 40

Add witness text after prep:

.. code-block:: bash

    wyrdcraeft ocr bosworth-toller --ocr

Rerun OCR on an existing prep workspace:

.. code-block:: bash

    wyrdcraeft ocr bosworth-toller --skip-prep --ocr \
      --output-dir data/ocr/bosworth-toller/run-001

Overwrite the shared dev default workspace:

.. code-block:: bash

    wyrdcraeft ocr bosworth-toller --force

See also
--------

- :doc:`/overview/bt_ocr_witness_preparation` — researcher overview and
  witness-first rationale
- :doc:`/overview/bt_ocr_witness_preparation_method` — architecture,
  artifact model, quality metrics, and validation methodology
- :doc:`/runbook/bt_dictionary_structuring_workflow` — case-bundle operator
  workflow downstream of prepared witnesses
- :doc:`/runbook/old_english_ocr_pipeline` — olmocr and managed-proxy setup
  shared by tile OCR
