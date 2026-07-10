# BT OCR parsing starts with lossless source-grounded AST

Bosworth-Toller OCR parsing will first produce a lossless source-grounded AST instead of directly producing normalized dictionary senses. We chose this because the source is messy, editorially layered, and OCR-noisy enough that early normalization drops information and hides parser mistakes; every character must therefore be accounted for by ordered typed source fragments, with uncertain text preserved as explicit unclassified fragments rather than discarded.

Current prototype note
----------------------

The current concrete starter artifact for this decision is the file-first
``wesan`` case bundle under ``data/bt_cases/wesan/``.

In that scaffold:

- ``entry.raw.yaml`` is the lossless-first layer
- fragments are ordered and provenance-carrying
- unresolved text is preserved explicitly as ``unclassified_remainder``
- ``entry.normalized.yaml`` remains intentionally skeletal and downstream

This keeps the ADR grounded in a real repository artifact instead of a purely
abstract parser target.

Upstream JP2 witness preparation for that workflow now exists as a
library-first package under ``wyrdcraeft/services/ocr/bt_witness_prep/``
(see ADR 0006). It emits image-backed tiles, manifests, and anchor seeds that
later case-bundle assembly can consume without treating OCR text as canonical
truth.
