``wyrdcraeft ocr old-english``
==============================

This command runs the Old English OCR pipeline and emits normalized text
artifacts from a PDF or page-image witness set.

Command usage
-------------

.. code-block:: bash

    wyrdcraeft ocr old-english --input-path INPUT [OPTIONS]

Inputs
------

- ``--input-path``: required path to one input source.
  Supported for this slice:

  - PDF file
  - single image file (``.jp2``, ``.jpg``, ``.jpeg``, ``.png``, ``.tif``, ``.tiff``)
  - flat image directory with supported image files in lexicographic filename order

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
- Image files and image directories are converted to one temporary workspace PDF
  before ``olmocr`` runs.
- Image directories are non-recursive.
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

    wyrdcraeft ocr old-english --input-path scans/page_0001.jp2

    wyrdcraeft ocr old-english --input-path scans/wright_main_volume/

See also
--------

- :doc:`/runbook/old_english_ocr_pipeline`
- :doc:`configuration_cli`
