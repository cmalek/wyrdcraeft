# BT source acquisition uses a multi-witness download set

Bosworth-Toller source acquisition will use a small fixed witness set instead of treating `data/oe_bt.txt` as the only input. The default acquisition set is: GLP full corrected text (`https://www.germanic-lexicon-project.org/txt/oe_bosworthtoller.txt`) as a corrected-text witness, GLP abbreviations XML (`https://www.germanic-lexicon-project.org/xml/oe_bosworthtoller/oebt_abbreviations.xml`) as the abbreviation/reference witness, Internet Archive main-volume JP2 images (`https://archive.org/download/anglosaxondictio00bosw/anglosaxondictio00bosw_orig_jp2.tar`) and supplement JP2 images (`https://archive.org/download/anglosaxondictio00tolluoft/anglosaxondictio00tolluoft_raw_jp2.zip`) as the primary scan witnesses for our own OCR, IA `hocr.html` and `abbyy.gz` artifacts as secondary OCR/layout witnesses for disagreement checks and anchor recovery, and IA `djvu.txt` only as a fallback-only rough-recall witness.

We chose this because no single BT source is trustworthy enough on its own: local text is noisy, generic OCR drops structure, PDFs are worse OCR inputs than raw page images, and the IA `djvu.txt` witness is too degraded for trusted spelling or structure recovery. This keeps acquisition simple while still giving us enough witness diversity to build lossless source-grounded entries, preserve attestations, and rank review by witness disagreement rather than by parser confidence alone.

Current prototype note
----------------------

The current in-repo ``wesan`` case bundle at ``data/bt_cases/wesan/`` now
contains witness stub files that make this witness set concrete:

- local ``oe_bt.txt``
- GLP corrected text
- IA JP2 scan
- ``olmOCR`` markdown
- optional IA HOCR
- optional IA ABBYY

The bundle manifest and witness stubs also record that IA ``djvu.txt`` remains
fallback-only and is not a trusted primary witness for structure or spelling.

JP2 scan witness preparation for the primary image family is now implemented
as ``wyrdcraeft.services.ocr.bt_witness_prep.prepare_pages`` (ADR 0006). That
slice turns immutable JP2 pages into overlapping OCR-ready tiles with
provenance manifests and anchor seeds; it does not replace the multi-witness
download set, and it does not promote OCR output to canonical text.
