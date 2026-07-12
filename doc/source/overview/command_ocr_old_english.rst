``wyrdcraeft ocr old-english``
==============================

This command runs the Old English OCR pipeline and emits normalized text
artifacts from a PDF or single loose page image.

Command usage
-------------

.. code-block:: bash

    wyrdcraeft ocr old-english --input-path INPUT [OPTIONS]

Inputs
------

- ``--input-path``: required path to one input source.
  Supported for this slice:

  - PDF file
  - single image file (``.jpg``, ``.jpeg``, ``.png``, ``.tif``, ``.tiff``)

  JP2 page scans and flat image directories are Bosworth-Toller witness input.
  Use :doc:`/overview/command_ocr_bosworth_toller` instead.

- ``--input-pdf``: compatibility alias for ``--input-path``.

Options
-------

- ``--output-dir PATH``: optional output directory. Default:
  ``data/ocr/<input-stem>`` under repo root.
- ``--skip-ocr / --no-skip-ocr``: reuse existing ``olmocr_workspace/markdown``
  instead of rerunning ``olmocr``.
- ``--rules-file PATH``: regex correction rules TSV.
- ``--wordlist-file PATH``: seed wordlist for unknown-token reporting.
- proxy / ``olmocr`` tuning flags: forwarded to the existing managed-proxy OCR flow.

Behavior
--------

- PDFs are reused unchanged.
- Single image files are converted to one temporary workspace PDF before
  ``olmocr`` runs.
- ``--pages`` remains unsupported in the ``olmocr`` path; pre-slice the PDF
  before running if needed.

Outputs
-------

- ``02_raw.txt``
- ``03_normalized.txt``
- ``04_unknown_tokens.tsv``
- ``olmocr_workspace/`` intermediate artifacts

Examples
--------

.. code-block:: bash

    wyrdcraeft ocr old-english --input-path tests/fixtures/ocr/wright1.pdf

    wyrdcraeft ocr old-english --input-path scans/page_0001.png

See also
--------

- :doc:`/overview/command_ocr_bosworth_toller` — JP2 scan directories and
  Bosworth-Toller witness preparation
- :doc:`/runbook/old_english_ocr_pipeline`
- :doc:`configuration_cli`
