Status: DONE

Files changed:
- `wyrdcraeft/services/lexicon/query.py`
- `wyrdcraeft/services/lexicon/tui.py`
- `tests/lexicon/test_tui.py`
- `tests/lexicon/test_morph_class_browse.py`
- `doc/sessions/task-phase3-wright-text-pane-report.md`

Implementation summary:
- Added a public `LexiconQueryService.lookup_wright_section_text()` wrapper so the browse TUI reads Wright text through the existing shared catalog query service.
- Reworked the dictionary details pane so Wright citations are selectable `ListView` items rendered in the details column, while the plain metadata block still shows morph class and provenance lines.
- Added `WrightSectionTextScreen`, a modal overlay that opens for any linked Wright section, shows stored SQLite text when present, and shows an actionable missing-ingest message when `section_text` is absent. Escape and the close button dismiss the overlay.
- Kept morphology sidebar behavior unchanged and avoided any runtime markdown reads.

Validation commands and output:

```text
.venv/bin/ruff check wyrdcraeft/services/lexicon/tui.py wyrdcraeft/services/lexicon/query.py
All checks passed!
```

```text
.venv/bin/mypy wyrdcraeft/services/lexicon/tui.py
Success: no issues found in 1 source file
```

```text
PATH=".venv/bin:$PATH" make napoleon-gate
Napoleon gate passed: no new violations (124 total, 191 baseline keys).
```

```text
.venv/bin/pytest tests/lexicon/test_tui.py tests/lexicon/test_morph_class_browse.py -q
37 passed in 9.24s
```

Self-review:
- The browse path now uses SQLite-only Wright text lookup, satisfying the no-markdown-runtime constraint.
- All linked Wright sections remain selectable; there is no invented primary citation.
- The modal is intentionally small and localized to the lexicon TUI, which keeps Phase 3 scoped and avoids sidebar or filter changes.
- Focus/keyboard handling is covered for dismissal via Escape; focused Textual tests cover both ingested-text and missing-text flows.
