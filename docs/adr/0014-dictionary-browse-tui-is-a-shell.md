---
status: accepted
---

# Dictionary browse TUI must not touch SQLAlchemy

The Textual browse app must not import or execute SQLAlchemy. SQL, the 12-tier
ranking ladder, and browse readiness belong on `DictionaryBrowseQueryService`.
Function-code decode and paradigm grids belong in `form_decode.py`. This
landing does **not** make the TUI a pure shell: POS row filtering, dedupe, and
`DataTable` painting stay in `browse_tui.py`. Implementation: Trello
https://trello.com/c/zHZpvqfk. This ADR overrides that card where they
conflict (readiness reuse and helper home).

**Readiness.** `DictionaryBrowseQueryService.ensure_ready()` counts
`bt_entries` on the service connection. Missing table or count zero raises
`DictionaryBrowseDataError`, which moves from `browse_tui.py` into
`browse_query.py` so the query module does not import the TUI. The factory
`create_dictionary_browse_app` calls `ensure_ready()`; it must not use
`query_service._connection`. This is not `require_populated_dictionary_index`
(ADR 0013: three `bt_*` tables for `dictionary query`). Unifying those gates
stays a later product decision.

**Ranking.** Keep the in-memory ladder and DIY Levenshtein. Do not add
rapidfuzz. Do not rank in SQL. Loading every `bt_entries` / `bt_variants` row
per search is **deferred**, not solved. Live helpers stay on `browse_query`
(`lexical_distance`, `normalized_query_at_affix`, `filter_display_variants`,
plus `_normalized_affix_match` on pre-normalized keys). Delete the unused
duplicates in `form_decode`. Point `test_form_decode.py` ranking tests and the
TUI `filter_display_variants` import at `browse_query`. Do not add a third
module.

**Grids.** `build_paradigm_sidebar` and POS `_build_*_sidebar` helpers stay in
`form_decode` until https://trello.com/c/OW5yM68o (file move only).

## Considered Options

- **Query owns SQL and ranking helpers; TUI drops the private COUNT (accepted).**
  Production ranking already lives in `browse_query`; `form_decode` copies are
  unused except by tests.
- **Put ranking helpers in `form_decode`.** Makes decode a search junk drawer
  and inverts “query owns the ladder.”
- **Call `require_populated_dictionary_index` from browse.** Tightens browse
  past today’s `bt_entries`-only gate (rejected; Trello “reuse the CLI gate”
  is narrowed here).
- **Rank in SQL / add rapidfuzz.** Rejected; full-table load remains a later
  perf card.
- **Split grids in the same landing.** Deferred to OW5yM68o.
