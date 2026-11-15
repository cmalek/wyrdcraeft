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
- Browse reads the column. On null it computes the line with `definition_line`, writes it back, and returns it. A row with no senses caches the empty string, so it is not recomputed on every query.
- Anything that changes an entry's senses, variants or part of speech sets the column to null in the same transaction: the editorial merger and edit-record operations (ADR 0021), and any build step that rewrites senses. A full `dictionary build` creates rows with the column null.
- A change to the ADR 0025 reading rules ships with a migration that nulls the column.
- The column is derived data and never an input. Nothing but browse reads it, and it is not exported. The stored gloss is untouched (ADR 0025).
- The schema change is an Alembic migration under ADR 0002.
- Start by computing lazily for the rows the list actually draws. If the first page is slow, populate the column for a result set in one batch before painting.

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
- A stale cache is possible if a write path forgets to clear it. A test lists every write path to `bt_senses`, `bt_variants` and `bt_entries` and asserts each clears the column.
