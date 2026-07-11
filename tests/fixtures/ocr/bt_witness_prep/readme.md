# BT witness-prep test fixtures

Tiny stand-in pages for source enumeration and preprocessing tests.

- Filenames use `.jp2` so the enumerator’s JP2-only filter is exercised.
- File bytes are PNG (OpenJPEG encode unavailable in local Pillow builds).
- Pillow reads dimensions from magic bytes; real JP2 decode is deferred to
  integration / live scan runs.
- `BT 0002.jp2` is all-white for full-frame crop regression.
- `BT 0007.jp2` and `BT 0010.jp2` add gray margins, text-line marks, and dark
  corner markers for conservative margin-crop regression.
- `anglosaxondictio00bosw_0142.jp2` and `anglosaxondictio00bosw_0397.jp2` are
  undersized stand-ins so the five-page Stage B validation manifest can resolve
  every ``source_filename`` without committing full Internet Archive scans.
- Non-JP2 siblings (`BT 0009.tif`, `notes.txt`, this readme) exist so ignore
  behavior can be asserted.
