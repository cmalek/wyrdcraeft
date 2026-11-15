# Dictionary Browse UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the dictionary browse TUI as one sectioned entry column with wrapping forms, a `c` copy key, a definition-line results preview, and a cached definition line.

**Architecture:** Presentation rules become small pure functions in a new `entry_view.py`, so they are testable without Textual. The cache is a nullable column kept honest by SQLite triggers. `browse_tui.py` keeps the query, ranking and sidebar logic from ADR 0014 and only changes how an entry is drawn and which keys act.

**Tech Stack:** Python 3.13, Textual 8.2.8 (`DataTable`, `Theme`, TCSS), SQLAlchemy, Alembic, pytest with `app.run_test()` pilots.

**Spec:** `docs/adr/0026-dictionary-browse-shows-an-entry-as-one-sectioned-column.md`, `docs/adr/0027-dictionary-browse-forms-wrap-and-never-truncate.md`, `docs/adr/0028-dictionary-browse-copy-key-and-results-preview.md`. Mockup: `doc/source/_images/interface.jpg`; the other parts of speech are boards 4 to 6 of https://claude.ai/artifact/Vsj7L8U2CpPdWsoNmXtdVP.

## Global Constraints

- Palette (dark), defined once as a Textual `Theme`; widgets use theme variables, never hex: ground `#101319`, panel `#151922`, selected row `#232a38`, border `#2a3140`, text `#dbe0ea`, label `#8c95a8`, accent `#e6b36a`, Old English forms `#8fd0c4`.
- Focused pane: accent border **and** accent title. Unfocused border stays `#2a3140`.
- Keys: `↑↓` Move, `⏎` Open, `/` Search, `tab` Switch pane, `[ ]` secondary switch, `←→` primary switch, `c` Copy, `ctrl+q` Quit (Textual default; no `q` binding, it would break typing). `ctrl+c` and `super+c` no longer copy.
- Before implementing, show the project's tooling preflight evidence (graphify query, a code-index call, context7 for Textual) in a progress update.
- No `…` and no "show all" anywhere in a forms table. No horizontal scrollbar in the entry pane.
- Class row only for verb, noun and adjective. A verb, noun or adjective with no class shows `unclassified` dimmed. A leading `verb, ` is stripped from the label.
- Methods and functions are 60 lines or fewer. Napoleon docstrings. `#:` comments on attributes. Service logic in `wyrdcraeft/services`, no business logic in `wyrdcraeft/cli`.
- After every Python task, run `ruff` on touched files, `.venv/bin/mypy` on touched files, `make napoleon-gate`, then `graphify update .`. Fix everything reported, and report pre-existing failures separately.
- Commits end with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- Out of scope: pronoun feature generation, preposition case government (boslexicon), a person tab for pronouns.

## Review Focus

- A `wā`-like entry (POS `unknown`, no morph class) shows no Class row and no Forms section. Pinned in Task 3 and Task 5b.
- An entry with no senses caches `""`, is not recomputed on the next read, and has Copy disabled. Pinned in Task 2 and Task 7.
- A pronoun where only some rows carry case, gender and number falls back to the flat list and does not crash. Pinned in Task 4.
- A 60-column terminal wraps a long verb row with no `…` and no horizontal scrollbar. Pinned in Task 6.
- Typing `c` in the search input inserts the letter and copies nothing. Pinned in Task 7.

---

### Task 0: Baseline

- [ ] **Step 1: On a clean `master`, run `.venv/bin/pytest -q`, `ruff check`, and `.venv/bin/mypy` and record the counts** in the first progress update. Task 2 Step 7 and Task 8 compare against these. Success is zero new failures.

---

### Task 1: Etymology source labels go in the Lang column

**Files:**
- Modify: `wyrdcraeft/services/dictionary/etymology_display.py` (`_parse_reference_block`, italic branch near line 487)
- Modify: `docs/adr/0026-dictionary-browse-shows-an-entry-as-one-sectioned-column.md` (Etymology bullet)
- Test: `tests/dictionary/test_etymology_display.py`

**Interfaces:**
- Produces: `_source_label_spellings() -> frozenset[str]` (cached, normalized with `_normalize_lang_label`, read from `wyrdcraeft/etc/dictionary/bosworth_and_toller_abbreviations.json` via `importlib.resources`); `_split_leading_label(span: str) -> tuple[str, str] | None` returning `(label, remainder)`.

Cause found by running the parser on the real `for` entry: `_looks_like_lang_label`'s regex has no room for a space or a trailing comma. `Piers P. Chauc.` fails on the spaces, `Laym. for,` fails because the span also carries a word, and `Plat,` fails on the comma.

- [ ] **Step 1: Write the failing tests.** `test_for_entry_puts_source_labels_in_lang_column` parses the stored `for` etymology (`<I>Piers P. Chauc.</I> for: <I>Laym. for,</I> uor: <I>Orm.</I> forr: <I>Plat,</I> för, vör: <I>O. Frs.</I> fori, fore, for: ...`) and asserts the first five `(lang_source, word, meaning)` triples are `("Piers P. Chauc.", "for", "")`, `("Laym.", "for, uor", "")`, `("Orm.", "forr", "")`, `("Plat.", "för, vör", "")`, `("O. Frs.", "fori, fore, for", "")`, and `unparsed == ()`. `test_split_leading_label_longest_run` asserts `_split_leading_label("Piers P. Chauc.") == ("Piers P. Chauc.", "")`, `_split_leading_label("Laym. for,") == ("Laym.", "for")` and `_split_leading_label("for") is None`.
- [ ] **Step 2: Run `.venv/bin/pytest tests/dictionary/test_etymology_display.py -v`.** Expected: the two new tests FAIL; the existing tests PASS.
- [ ] **Step 3: Implement `_source_label_spellings` and `_split_leading_label` in `etymology_display.py`.** The label is the longest run of consecutive known spellings from the start of the span, tolerating a trailing comma; the remainder is the rest, stripped of `, `. In `_parse_reference_block`, try `_split_leading_label` first on each italic span: flush the row, set `pending_lang` to the label (with `Plat,` normalized to `Plat.`), and set `pending_word` to the remainder. When a remainder word is open, the next plain chunk, up to its `:`, is appended to the word with `", "` (so `Laym. for,` plus `uor` gives `for, uor`).
- [ ] **Step 4: Run the same pytest command.** Expected: all PASS, including the older etymology tests.
- [ ] **Step 5: Corpus check.** In a scratch script (not committed), run `parse_etymology_text` over every `bt_entries` etymology before and after the change. Expected: the total `unparsed` count does not rise, and the set of new `lang_source` values is all spellings from the abbreviations file. Review the diff for a plain word wrongly taken as a label; if one appears, narrow `_split_leading_label` and add a test for it.
- [ ] **Step 6: Trim the ADR 0026 Etymology bullet** to the decision only: a Bosworth-Toller source abbreviation (`Piers P. Chauc.`, `Laym.`, `Orm.`, `Plat.`) stands in for Middle English, goes in the language column, and the form after it goes in the word column; labels come from `bosworth_and_toller_abbreviations.json`. Drop the "today the parser returns" sentences and the `_looks_like_proper_name` claim, which names the wrong function.
- [ ] **Step 7: Commit** `fix: read etymology source labels from the abbreviations file` with the trailer.

---

### Task 2: Cached definition line

**Files:**
- Create: `wyrdcraeft/db/alembic/versions/20261115_01_bt_entries_definition_line_cache.py`
- Create: `wyrdcraeft/services/dictionary/definition_cache.py`
- Modify: `wyrdcraeft/models/sqlalchemy.py` (`bt_entries` model, line 105)
- Modify: `wyrdcraeft/services/dictionary/browse_query.py` (`BrowseSearchHit`, search path)
- Modify: `docs/adr/0028-dictionary-browse-copy-key-and-results-preview.md`
- Test: `tests/dictionary/test_definition_line_cache.py`

**Interfaces:**
- Consumes: `definition_line(pos: str, glosses: Sequence[str]) -> str` from `definition_line.py:57`.
- Produces: `DefinitionLineCache(connection: Connection)` sharing the browse service's connection, with `get(entry_id: int) -> str` (computes, stores and returns on null; `""` for an entry with no senses; if the write fails, for example `database is locked` during a build, it returns the computed line without caching and does not raise) and `peek(entry_id: int) -> str | None`. `BrowseSearchHit.definition_line: str | None = None` (`None` means not yet computed). Column `bt_entries.definition_line_cache` (nullable Text).

Browse facts (checked): `DictionaryBrowseQueryService.search` returns every hit with no limit, over one long-lived writable connection, so the cache write needs a `commit()`. The search `SELECT` gains `e.definition_line_cache AS cached_line`, so cached lines cost nothing. Missing lines are computed only for the rows the list draws (the visible window plus one screen), not for every hit; the results list asks for more as it scrolls. The copy key reads the same `definition_line` the row shows (via `get`), so preview and copy cannot disagree.

Deviation from ADR 0028, to be written into it in Step 6: instead of a test that lists every write path, the migration adds SQLite triggers that null the column when `bt_senses` or `bt_variants` rows are inserted, updated or deleted, and when `bt_entries.pos_id` changes (`AFTER UPDATE OF pos_id` only, so writing the cache does not fire it). That catches write paths nobody remembered, including the editorial merger and ADR 0021 ops. Ceiling: one extra `UPDATE` per sense insert during a full build.

- [ ] **Step 1: Run `.venv/bin/alembic -c alembic.ini heads`** and set `down_revision` to the head it prints. Confirm the sense and variant tables' entry foreign-key column names in `models/sqlalchemy.py`. Check that nothing exports or `SELECT *`s `bt_entries` (`cli/dictionary.py`, `services/dictionary/query.py`, `sinks.py`, `models/dictionary_build.py`); ADR 0028 says the column is never exported.
- [ ] **Step 2: Write the failing tests** in `test_definition_line_cache.py`, using `upgrade_canonical_db` and the sample-lines fixture as in `test_browse_tui.py`: `test_first_get_computes_and_stores`; `test_second_get_does_not_recompute` (monkeypatch `definition_line` with a counter); `test_entry_without_senses_caches_empty_string_once`; `test_sense_insert_update_delete_clear_cache`; `test_variant_change_clears_cache`; `test_pos_change_clears_cache`; `test_writing_the_cache_does_not_clear_it`; `test_moving_a_sense_to_another_entry_clears_both`; `test_failed_cache_write_returns_computed_line` (make the write raise `OperationalError`; `get` still returns the line).
- [ ] **Step 3: Run them.** Expected: FAIL (no column).
- [ ] **Step 4: Add the column to the model, write the migration (column plus triggers, with a downgrade that drops both), and implement `DefinitionLineCache`.**
- [ ] **Step 5: Fill `BrowseSearchHit.definition_line`** from the `cached_line` column in the search `SELECT`; the TUI calls `DefinitionLineCache.get` only for drawn rows whose cached line is null (hits carry `definition_line=None` until then). Add `test_search_hits_carry_cached_line` and `test_search_leaves_uncached_hits_unset` to `test_browse_query.py`.
- [ ] **Step 6: Amend ADR 0028's "Cached definition line" bullets and its last Consequence** to describe the triggers instead of the write-path test. Also record in the ADR that browse reads the column in the search query, computes only for drawn rows, and returns the computed line without caching when the write fails (locked database).
- [ ] **Step 7: Run `.venv/bin/pytest tests/dictionary -q`.** Expected: PASS, no new failures against the pre-change baseline recorded before Step 1.
- [ ] **Step 8: Commit** `feat: cache the definition line on bt_entries` with the trailer.

---

### Task 3: Entry presentation rules

**Files:**
- Create: `wyrdcraeft/services/dictionary/entry_view.py`
- Test: `tests/dictionary/test_entry_view.py`

**Interfaces:**
- Consumes: `EntryDetails`, `EntrySense` (`browse_query.py`); `details.morph_class.display_label` and `.is_unclassified`.
- Produces:
  - `class_row_value(pos: str, morph_class: LemmaMorphClassSummary | None) -> str | None` (`None` means no Class row; the string `"unclassified"` means draw it dimmed)
  - `strip_pos_prefix(label: str) -> str`
  - `show_summary(details: EntryDetails) -> bool`
  - `key_value_rows(details: EntryDetails) -> list[tuple[str, str]]` in the order Variants, Class, Gender, Source, omitting rows with no value
  - `drop_empty_columns(columns: Sequence[str], rows: Sequence[Sequence[str]]) -> tuple[tuple[str, ...], tuple[tuple[str, ...], ...]]`

- [ ] **Step 1: Write the failing tests** with these assertions: `class_row_value("verb", <label "verb, weak class 2">) == "weak class 2"`; `class_row_value("noun", None) == "unclassified"`; `class_row_value("adjective", <summary with is_unclassified True>) == "unclassified"`; `class_row_value("unknown", None) is None`; `class_row_value("adverb", <any>) is None`; the same `None` for preposition, pronoun, conjunction and interjection. `strip_pos_prefix("verb, strong class 7") == "strong class 7"` and `strip_pos_prefix("strong a-/ō-stem") == "strong a-/ō-stem"`. `show_summary` is `False` when the summary equals sense 1 after `definition_line` or the summary is empty, and `True` otherwise (including a summary with no senses). `key_value_rows` labels the provenance row `Source`. `drop_empty_columns` removes a column whose cells are all empty and keeps the others in order.
- [ ] **Step 2: Run `.venv/bin/pytest tests/dictionary/test_entry_view.py -v`.** Expected: FAIL (module missing).
- [ ] **Step 3: Implement the functions in `entry_view.py`.** `show_summary` compares `definition_line(pos, [summary])` with `definition_line(pos, [first sense gloss])`.
- [ ] **Step 4: Run the same command.** Expected: PASS.
- [ ] **Step 5: Commit** `feat: add pure entry presentation rules` with the trailer.

---

### Task 4: Paradigm sections for the new switches

**Files:**
- Modify: `wyrdcraeft/services/dictionary/paradigm_sidebar.py` (`ParadigmTableSection`, `_build_pronoun_sidebar` at line 604, verb and adjective builders)
- Test: `tests/lexicon/test_paradigm_sidebar.py` (replace the pronoun test at line 244; keep `test_blank_pronoun_surface_keeps_flat_pronoun_table`'s intent)

**Interfaces:**
- Consumes: `drop_empty_columns` (Task 3).
- Produces: `ParadigmTableSection.primary: str = ""`, `.secondary: str = ""`, `.flat: bool = False` (a flat section holds one row of deduplicated forms and no feature columns). The visible table is the section whose `primary` equals the primary selection and whose `secondary` equals the secondary selection; a section with both empty is in no switch and is always shown.

Section shapes (checked against the current builders):
- **Verb.** Today one `Verb` section with columns `("", "Person", "Present", "Past")` and a header row `("", "Present", "Past")` inside `rows`. Replace it with two sections titled `Present` and `Past`, `primary` set to the title, columns `("", "Person", "Forms")`, no embedded header row. Both carry every row; a row with no form in that tense is dropped, so Infinitive, Imperative and Inflected Infin appear only where they have forms.
- **Adjective.** Keep the six sections `Strong · Positive` through `Weak · Superlative` (`paradigm_sidebar.py` ~line 521). `primary` is `Strong` or `Weak`; `secondary` is the degree. Columns stay Masc. sg., Fem. sg., Neut. sg., Plural.
- **Pronoun.** `Singular` and `Plural`, `primary` set to the title.
- **Noun, adverb, anything else.** No `primary` or `secondary`.

- [ ] **Step 1: Write the failing tests.**
  - `test_pronoun_with_features_splits_singular_and_plural`: reusing the row helper at line 244's rows, the sections are titled `("Singular", "Plural")`, with `primary` equal to the title. The Singular columns are `("", "Masc.", "Fem.", "Neut.")`, the Plural columns are `("", "Plural")`, and `Inst` appears only when some form has it.
  - `test_pronoun_without_features_is_one_flat_section`: rows whose `function` carries no case, gender or number give one section with `flat is True`, with forms deduplicated and in first-seen order.
  - `test_pronoun_with_partial_features_falls_back_to_flat`: one row with a case but no number gives a flat section and no exception.
  - `test_adjective_sections_carry_both_axes`: six sections, `(primary, secondary)` pairs cover Strong/Weak × Positive/Comparative/Superlative, and the columns are Masc. sg., Fem. sg., Neut. sg., Plural.
  - `test_verb_splits_into_present_and_past_sections`: two sections, `primary` `Present` and `Past`, no row whose first cells are `("", "Present", "Past")`, and the Infinitive row is in Present only.
  - `test_empty_section_is_omitted`: a section with no rows, or with only empty feature columns and no forms, is absent from `sections`.
  - `test_noun_and_adverb_have_no_switch_axes`.
- [ ] **Step 2: Run `.venv/bin/pytest tests/lexicon/test_paradigm_sidebar.py -v`.** Expected: new tests FAIL, old pronoun test replaced.
- [ ] **Step 3: Implement.** Add the three fields, split the verb and pronoun builders as described above, and add the flat fallback. Existing verb tests that read the single `Verb` section are rewritten to the two-section shape, not weakened. Apply `drop_empty_columns` (Task 3) when a section is built. A section with no rows or no non-empty cell is omitted from `sections`.
- [ ] **Step 4: Run the same command plus `.venv/bin/pytest tests/lexicon -q`.** Expected: PASS.
- [ ] **Step 5: Commit** `feat: group paradigm sections for tab switching` with the trailer.

---

### Task 5a: Theme, pane borders and results rows

**Files:**
- Create: `wyrdcraeft/services/dictionary/browse_theme.py` (the `Theme`, named `wyrdcraeft`)
- Create: `wyrdcraeft/services/dictionary/browse.tcss` (confirm it ships as package data in `pyproject.toml`)
- Create: `docs/superpowers/plans/browse-tcss-skeleton.tcss`: copy the TCSS skeleton from the Spec board (`.../scratchpad/wyrd/project/Spec.dc.html`, "TCSS skeleton" block) so it survives the scratch directory. Do this first.
- Modify: `wyrdcraeft/services/dictionary/browse_tui.py` (`CSS` at line 722, `compose` at 963, `_MainResultItem` at 228)
- Test: `tests/dictionary/test_browse_tui.py`

**Interfaces:**
- Consumes: `BrowseSearchHit.definition_line` and `DefinitionLineCache` (Task 2).
- Produces: the `wyrdcraeft` theme, `CSS_PATH`, rounded titled pane borders with an accent title class on the focused pane, and results rows of headword, dim definition line, POS tag (class `pos-<code>`, one rule per POS code in the tcss, differing in lightness). Keep the existing diacritic insert chips row and header.

- [ ] **Step 1: Write the failing tests** (pilot, `lexicon_source_db` fixture): `test_theme_wyrdcraeft_is_active`; `test_results_row_shows_arrow_headword_when_variant_matched` (the row text starts with the matched text and then contains `→ <headword>`); `test_results_row_dims_headword_hyphen`; `test_results_row_is_three_cells_tall`; `test_results_row_shows_definition_line`; `test_focused_pane_has_accent_title_class`.
- [ ] **Step 2: Run `.venv/bin/pytest tests/dictionary/test_browse_tui.py -k "theme or results_row or focused_pane" -v`.** Expected: FAIL.
- [ ] **Step 3: Implement the theme and TCSS** from the Global Constraints palette and the saved skeleton. Replace the inline `CSS` string with `CSS_PATH`.
- [ ] **Step 4: Rewrite `_MainResultItem`** as headword, dim definition line, then POS tag, with one cell of padding above and below. Missing lines are filled for drawn rows only (Task 2 Interfaces).
- [ ] **Step 5: Run `.venv/bin/pytest tests/dictionary/test_browse_tui.py -q`.** Expected: PASS. Rewrite, never weaken, any test that asserted the old `matched (headword, pos)` text.
- [ ] **Step 6: Commit** `feat: add the wyrdcraeft theme and results row layout` with the trailer.

---

### Task 5b: Sectioned entry column

**Files:**
- Modify: `wyrdcraeft/services/dictionary/browse_tui.py` (`compose` at 963, `_format_entry_*` at 606-715)
- Test: `tests/dictionary/test_browse_tui.py`

**Interfaces:**
- Consumes: `key_value_rows`, `show_summary`, `class_row_value` (Task 3); `parse_etymology_text` (Task 1); `drop_empty_columns` (Task 3).
- Produces: widgets with ids `#entry-banner`, `#entry-keyvalues`, `#entry-senses`, `#entry-etymology`, `#entry-forms` inside one scrolling `#entry-column`. A section widget is not mounted when it has no content, label included. The banner is outside the scroll region. Each section label is dim caps with a hairline rule. `#entry-forms` holds the existing single `DataTable#morphology-table` (Task 6 repopulates it).

- [ ] **Step 1: Write the failing tests** (pilot, `lexicon_source_db` fixture):
  - `test_entry_column_sections_in_order` (Senses, Etymology, Forms ids appear in that order for a verb).
  - `test_entry_without_etymology_has_no_etymology_section`.
  - `test_unknown_pos_entry_has_no_class_row_and_no_forms_section`.
  - `test_preposition_has_no_forms_section_or_label`.
  - `test_unclassified_class_row_is_dim`.
  - `test_sub_senses_are_indented_with_dim_number` and `test_main_sense_number_is_accent_bold`.
  - `test_summary_is_first_senses_line_when_it_differs_from_sense_one`, `test_summary_dropped_when_equal_to_sense_one`, `test_summary_shown_when_entry_has_no_senses`.
  - `test_etymology_table_drops_empty_columns` (the `for` entry shows only language and word) and `test_etymology_note_line_under_table`.
- [ ] **Step 2: Run `.venv/bin/pytest tests/dictionary/test_browse_tui.py -k "entry_column or etymology or class_row or sub_senses or summary or preposition or unknown_pos" -v`.** Expected: FAIL.
- [ ] **Step 3: Replace `_format_entry_details` and the morph-class lines with the section widgets,** building their content from `entry_view`. Mark `Source` where the old `Provenance:` text was.
- [ ] **Step 4: Rewrite the old tests that assert the plain-text detail lines** (`_details_text` users) to assert the section widgets instead. Do not weaken an assertion to get green; if one is disputed, stop and ask.
- [ ] **Step 5: Run `.venv/bin/pytest tests/dictionary/test_browse_tui.py -q`.** Expected: PASS.
- [ ] **Step 6: Commit** `feat: draw a dictionary entry as one sectioned column` with the trailer.

---

### Task 6: Wrapping forms and switching

**Files:**
- Modify: `wyrdcraeft/services/dictionary/browse_tui.py` (`_populate_morphology_table*` at 518-590, the `#entry-forms` widget from Task 5b, `#entry-column` becomes `EntryColumn`)
- Test: `tests/dictionary/test_browse_tui.py`

**Interfaces:**
- Consumes: `ParadigmTableSection.primary`, `.secondary`, `.flat` (Task 4).
- Produces: `EntryColumn(VerticalScroll)`, the `#entry-column` widget, whose own `BINDINGS` map `left`/`right` to `switch('primary', -1/+1)` and `[`/`]` to `switch('secondary', -1/+1)`. They live on the widget because a focused `VerticalScroll` consumes `left` and `right` as scroll keys before app-level bindings run. `check_action` lets them act only when the entry has more than one value on that axis. The app keeps one primary and one secondary selection index, reset when the entry changes, and repopulates the single `DataTable#morphology-table` with the matching section. The table has `can_focus = False` so Tab does not stop on it.

- [ ] **Step 1: Check `DataTable`'s wrapping in Textual 8.2.8 via context7** (`add_row(height=None)` and column width) before writing code, and record the exact call in the commit body.
- [ ] **Step 2: Write the failing tests.**
  - `test_long_verb_forms_wrap_without_ellipsis`: the app runs at `size=(60, 40)`, a verb with many variants is selected, `"…" not in _table_text(table)`, every form string from the sidebar appears, and the table's horizontal scrollbar is not shown.
  - `test_citation_form_is_bold`: the first form in a cell has a bold style span.
  - `test_present_past_switch_with_arrow_keys`: with the entry pane focused, `right` shows the Past table and `left` shows Present.
  - `test_adjective_degree_switch_with_brackets`: `]` moves Positive to Comparative.
  - `test_switch_keys_inert_in_search_input_and_results_list`: the visible table does not change.
  - `test_adjective_two_axis_selection`: `right` then `]` shows `Weak · Comparative`; the other combinations show their own section.
  - `test_forms_table_is_not_a_tab_stop`.
  - `test_flat_section_shows_one_wrapped_list_and_no_headers`.
  - `test_pronoun_singular_plural_switch`.
- [ ] **Step 3: Run `.venv/bin/pytest tests/dictionary/test_browse_tui.py -k "wrap or switch or flat or citation" -v`.** Expected: FAIL.
- [ ] **Step 4: Implement.** Rows are added with `height=None`; the forms column width is set from the pane width on mount and on resize. Only the active table of a switch group is visible. The footer shows the switch keys while a switch exists.
- [ ] **Step 5: Run `.venv/bin/pytest tests/dictionary/test_browse_tui.py -q`.** Expected: PASS. Update `_table_text` expectations that change because cells now wrap.
- [ ] **Step 6: Commit** `feat: wrap paradigm forms and switch tables with the arrow keys` with the trailer.

---

### Task 7: Copy key, focus model and results preview

**Files:**
- Modify: `wyrdcraeft/services/dictionary/browse_tui.py` (`BINDINGS` at 925-929, `action_copy_definition` at 1030, `on_key` at 1080)
- Test: `tests/dictionary/test_browse_tui.py` (rewrite the tests that press `ctrl+c` or `super+c`)

**Interfaces:**
- Produces: bindings `c` to `copy_definition`, `escape` to `focus_results`, `slash` to `focus_search`. Focus order: `#search-input`, `#results-list`, `#entry-column`. `check_action` returns `False` for `copy_definition` while the search input is focused or when `_definition_line` is empty, so the footer shows `c Copy` only when it is live.

- [ ] **Step 1: Write the failing tests.**
  - `test_c_copies_definition_line_from_results_list`.
  - `test_c_in_search_input_types_the_letter_and_copies_nothing` and `test_slash_in_search_input_types_a_slash`.
  - `test_ctrl_c_shows_textual_default_notice` (no custom `help_quit` binding remains).
  - `test_copy_button_copies_the_same_line`.
  - `test_copy_disabled_without_definition_line`.
  - `test_ctrl_c_and_super_c_do_not_copy`.
  - `test_escape_in_search_moves_focus_to_results` and `test_escape_elsewhere_does_nothing`.
  - `test_slash_returns_to_search`.
  - `test_tab_order_search_results_entry`.
  - `test_down_in_search_moves_selection_without_leaving_input`.
  - `test_results_preview_equals_copied_line` (the dim text in the row equals `_definition_line` after selecting that row).
  - `test_footer_lists_only_live_keys`.
- [ ] **Step 2: Run `.venv/bin/pytest tests/dictionary/test_browse_tui.py -k "copy or escape or slash or tab_order or preview or footer" -v`.** Expected: FAIL.
- [ ] **Step 3: Implement.** Delete both `ctrl+c` bindings and the `SkipAction` path. Make Tab focus the three regions in order. Keep the Copy button `can_focus = False`.
- [ ] **Step 4: Run `.venv/bin/pytest tests/dictionary -q`.** Expected: PASS.
- [ ] **Step 5: Commit** `feat: copy with c, add a focus model and a results preview` with the trailer.

---

### Task 8: Verification

- [ ] **Step 1: Compare against the Task 0 baseline.** Success is zero new failures.
- [ ] **Step 2: Run the full gate** after the last edit: `ruff check` and `ruff format --check` on touched files, `.venv/bin/mypy` on touched files, `make napoleon-gate`, `.venv/bin/pytest -q`.
- [ ] **Step 3: Real execution.** Launch the browse app against the canonical database and look at `for`, `scild`, `wislice`, `nǣnig`, `forþon`, `wā` and a verb with many variants, at the normal terminal width and at 80 columns. Capture screenshots.
- [ ] **Step 4: Observe the two open questions from the ADRs** and write the result into ADR 0028: how many presses Ctrl-Q needs, and whether the first results page is slow enough to need the batch fill (Task 2's cache).
- [ ] **Step 5: Run the gauntlet skill** and report its evidence table. Then run `graphify update .`.
- [ ] **Step 6: Open the follow-ups** that were deliberately left out: pronoun feature generation, and preposition case government in boslexicon.
