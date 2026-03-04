.. _runbook__old_english_ocr_pipeline:

Old English OCR Pipeline
========================

This runbook defines a repeatable, repository-local OCR workflow for grammar
sources such as Wright and Tichý PDFs.

Goals
-----

- Produce machine-readable text from PDF scans.
- Apply deterministic, reviewable regex corrections.
- Generate an unknown-token report for manual cleanup.
- Keep all artifacts under ``data/ocr/`` for incremental iteration.

Tooling
-------

Required CLI tools:

- ``ocrmypdf`` (OCR stage)
- ``gs`` (Ghostscript ``txtwrite`` extraction)

The pipeline script:

- ``scripts/ocr/old_english_ocr_pipeline.py``

Configuration files:

- ``data/ocr/rules/old_english_safe.tsv``
- ``data/ocr/wordlists/old_english_seed.txt``

Output layout
-------------

For an input file ``data/OldEnglishGrammar.pdf``, default outputs are:

- ``data/ocr/OldEnglishGrammar/01_ocr.pdf``
- ``data/ocr/OldEnglishGrammar/02_raw.txt``
- ``data/ocr/OldEnglishGrammar/03_normalized.txt``
- ``data/ocr/OldEnglishGrammar/04_unknown_tokens.tsv``

Commands
--------

Run full OCR + extraction + normalization:

.. code-block:: shell

    .venv/bin/python scripts/ocr/old_english_ocr_pipeline.py \
      --input-pdf data/OldEnglishGrammar.pdf

Run on a page subset (recommended for incremental cleanup):

.. code-block:: shell

    .venv/bin/python scripts/ocr/old_english_ocr_pipeline.py \
      --input-pdf data/OldEnglishGrammar.pdf \
      --pages 194-220

Skip OCR stage and only extract/normalize text from an existing PDF:

.. code-block:: shell

    .venv/bin/python scripts/ocr/old_english_ocr_pipeline.py \
      --input-pdf data/OldEnglishGrammar.pdf \
      --skip-ocr

Regex correction rules
----------------------

Rules are loaded from ``data/ocr/rules/old_english_safe.tsv`` and applied in
file order. Current safe baseline rules include:

- long-s replacement (``ſ -> s``)
- section marker normalization at line start (``S 153.`` or ``5 153.`` -> ``§ 153.``)
- carriage-return removal
- whitespace/newline normalization

Add new rules only when they are deterministic and low-risk. Keep aggressive,
content-specific fixes in separate optional rule files.

Incremental review workflow
---------------------------

1. Run the pipeline on a narrow page range.
2. Inspect ``03_normalized.txt`` for high-value sections.
3. Review ``04_unknown_tokens.tsv`` to find OCR errors not covered by current
   regex rules or seed wordlist.
4. Add:

   - deterministic regex fixes to ``old_english_safe.tsv`` when broadly safe
   - accepted lexical forms to ``old_english_seed.txt`` when they are valid

5. Re-run on the same page range and compare output.

Notes for Old English content
-----------------------------

- Tesseract has no dedicated Old English model; ``eng+lat`` is a practical
  baseline.
- Diacritics and graphemes (e.g. thorn/eth/macrons) require post-correction
  and manual verification.
- Use source-grounded checks when OCR text will feed factual documentation.

