---
status: accepted
---

# Dictionary browse copies with `c` and previews the definition line

ADR 0025 chose `ctrl+c` and `super+c` for copying a definition line and a pinned Copy button. This ADR supersedes its Copying section and its `ctrl+c` / `super+c` consequence. The reading of the line in ADR 0025 is unchanged. Layout is ADR 0026.

## Copy

- `c` copies the selected entry's definition line. The Copy button in the banner does the same. Both are disabled when the entry has no definition line.
- `ctrl+c` and `super+c` no longer copy. The `ctrl+c` binding that restored Textual's quit hint is deleted, so Textual's default `ctrl+c` notice shows. A mouse selection is still copied by Textual's own screen binding.
- Quit is Ctrl-Q, Textual's default. Whether it needs a second press in practice is observed after implementation, not decided here.

## Focus

The search input has focus at start and takes plain letters, so `c` types a letter while it has focus. The focus model becomes:

- Search input, results list and entry pane are focusable in that order. `tab` and `shift+tab` move between them.
- `escape` in the search input moves focus to the results list. `escape` anywhere else does nothing. `/` from the results list or entry pane returns to the search input.
- `up` and `down` in the search input move the results selection without leaving the input, as typing a query and arrowing down is the common path. In the results list, `down` and `up` move the selection.
- `c` and `←` `→` act in the results list and entry pane and are inert in the search input. The footer shows `c Copy` only when the binding is live.
- The Copy button stays unfocusable and mouse-clickable.

## Results preview

The dim text after the headword in a results row is the entry's definition line, the same text `c` copies. A row whose entry has no definition line shows nothing there. Copy and preview call one function, so they cannot disagree.

## Cached definition line

Computing the line for every row of a long result list is the open cost, and ADR 0014 already defers loading every entry per search.

- `bt_entries` gains a nullable text column `definition_line_cache`. Null means "not computed".
- Browse reads the column in its search query (`e.definition_line_cache AS cached_line`), so a cached line costs nothing. A hit whose column is null carries no line (`BrowseSearchHit.definition_line` is `None`).
- `DefinitionLineCache` shares the browse service's connection. `get` returns the stored line, or on null computes it with `definition_line`, writes it back, commits, and returns it. A row with no senses caches the empty string, so it is not recomputed on every query. `peek` returns the stored value without computing.
- If the write fails, for example `database is locked` while a build holds the database, `get` rolls back and returns the computed line without caching. After the first failure the cache stops trying to write for the rest of the session, so each later miss does not wait out SQLite's busy timeout; lines are still computed and shown. Browse never raises on a cache write. The cache orders senses as the details view does (by sense path, then `order_index`), so preview and details agree.
- Browse computes missing lines only for the rows the results list draws (the visible window plus one screen), not for every hit, and asks for more as the list scrolls. Copy reads the same line through `get`, so preview and copy cannot disagree.
- The migration that adds the column also adds SQLite triggers that set it to null when a `bt_senses` or `bt_variants` row is inserted, updated or deleted (an update clears both the old and the new entry, so moving a sense clears both), and when `bt_entries.pos_id` changes (`AFTER UPDATE OF pos_id`, guarded by `OLD.pos_id IS NOT NEW.pos_id`, so writing the cache itself does not fire it). The triggers catch every write path, including the editorial merger, edit-record operations (ADR 0021), build steps that rewrite senses, and paths nobody remembered. A full `dictionary build` creates rows with the column null.
- A change to the ADR 0025 reading rules ships with a migration that nulls the column.
- The column is derived data and never an input. Nothing but browse reads it, and it is not exported. The stored gloss is untouched (ADR 0025).
- The schema change is an Alembic migration under ADR 0002. Only databases upgraded through Alembic carry the triggers; a table created directly from the models (`BTSqliteSink` without attach mode) has the column but not the triggers, and browse does not run against such a database.
- If drawing the first page is slow, populate the column for a result set in one batch before painting.

## Considered Options

- **Keep `ctrl+c` and `super+c` beside `c`.** The user is the only user and prefers `c`. Two bindings on one key also suppress Textual's quit hint.
- **Compute the line on every search, no cache.** The line reads every sense of every hit, and ADR 0014 already flags the full-table load.
- **A separate table for the cache.** One nullable column on the entry is enough and is cleared with the row's own update.
- **A `y` binding.** Rejected in ADR 0025 for the results list.
- **First sense as the preview.** Two readings of one gloss would disagree on screen.
- **Focus stays in the search input always.** Then `c` never fires. The Copy button alone is not enough.

## Consequences

- A user who has typed a query presses `escape` or `tab` before `c`. The footer and the banner button remain the discoverable paths.
- `browse_tui.py`'s `BINDINGS` loses the two `ctrl+c` entries. The tests that pressed `ctrl+c` or `super+c` press `c` after moving focus.
- The first browse after an edit that clears a row pays one compute for that row.
- A stale cache would need a write that bypasses the triggers, which only a direct schema change could do. Tests assert that inserting, updating and deleting senses and variants, changing the part of speech, and moving a sense between entries each clear the column, and that writing the cache does not. The cost is one extra `UPDATE` per sense or variant insert during a full build.
