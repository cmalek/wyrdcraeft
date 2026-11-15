# Definition Line Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Copy one dictionary entry's definition line to the clipboard from dictionary browse, using the reading in ADR 0025.

**Architecture:** `definition_line(pos, glosses)` in a new module owns the reading and returns `""` when nothing remains. `DictionaryBrowseApp` calls it with `details.pos` and the glosses from `details.senses` sorted by `order_index`. The pinned title row and the `Copy` button live in the existing details pane, above `#details-content-scroll`. Clipboard writes go through `App.copy_to_clipboard`.

**Tech Stack:** Python 3.13, Textual 8.2, pytest, ruff, mypy, `make napoleon-gate`.

**Spec:** [docs/adr/0025-definition-lines-join-senses-with-semicolons.md](../../adr/0025-definition-lines-join-senses-with-semicolons.md). Trello: https://trello.com/c/K6lah6MZ.

## Global Constraints

- Do not rewrite `bt_senses`. Do not append gender, usage notes, modifiers, or etymology.
- Do not change Ænglisc Toolkit. The field stays a paste target.
- `definition_line` keeps the sequence it is given. The browse caller sorts `details.senses` by `order_index` before passing the glosses. Do not use the `sense_path` order `get_details` returns.
- Join finished senses with `"; "` (semicolon, one space).
- A verb is `pos.strip().casefold() == "verb"`. Other parts of speech keep a leading infinitive marker.
- A semicolon boundary is ` or ` only when the trimmed right-hand piece is one word, a space, and a complement word, and that complement is not already a word in the left-hand piece. Split words on whitespace. A comma in the right-hand piece before the complement keeps the boundary a comma. Complement words: `of to for in on at with from by into upon over under after before against through than as unto towards toward without within about between among across`.
- Abbreviation words, the first whitespace word of the right-hand piece: `pp pl fut t p`. Those boundaries are commas.
- A right-hand piece whose stripped text starts with `to `, `a `, `an `, or `the ` (case-insensitive) is a list, judged before the complement rule.
- On a verb, after that judgment, strip a leading `to ` or `To ` from each comma-separated sense part. `ought to be done` keeps the `to` inside the complement.
- Button text is `Copy`. Title text is `Details` or `Details: {headword}`. Keys are `ctrl+c,super+c`, `show=False`, not `priority`.
- `browse_tui.py` still must not import SQLAlchemy. `definition_line.py` imports neither `browse_tui` nor SQLAlchemy.
- Napoleon docstrings on the new public function. No empty sections. Methods stay ≤ 60 lines.
- Do not run the commit steps unless the user has asked for commits in that session.

## File map

| File | Role |
|------|------|
| `wyrdcraeft/services/dictionary/definition_line.py` | `definition_line(pos, glosses) -> str`. |
| `wyrdcraeft/services/dictionary/browse_tui.py` | Pinned title row, `Copy` button, key binding, header without the bare headword. |
| `tests/dictionary/test_definition_line.py` | Reading cases from ADR 0025. |
| `tests/dictionary/test_browse_tui.py` | Button, title, clipboard, and the two assertions that currently expect the headword inside `#details-content`. |

## Review Focus

- Left piece already contains the complement (`the refuse of things; things of no value`): stay a comma. Task 1.
- A comma sits before the complement (`nymph, of elfin beauty`): stay a comma, not ` or `. Task 1.
- Right piece starts with an abbreviation (`brought forth; pp. of`): stay a comma. Task 1.
- The same item in the next sense stays (`["time; time", "time; date"]` → `time; time, date`). Task 1.
- A word inside a longer item is not that item (`a proper time, time` stays). Task 1.
- Ctrl-C while the search box has a selection copies that selection. The definition line waits. Task 2.
- Two senses whose `sense_path` order and `order_index` order disagree: the clipboard follows `order_index`. Task 2.
- Ctrl-C with no definition line leaves the clipboard empty and Textual's quit notification appears. Task 2.

---

### Task 1: Definition-line reading

**Files:**
- Create: `wyrdcraeft/services/dictionary/definition_line.py`
- Test: `tests/dictionary/test_definition_line.py`

**Interfaces:**
- Consumes: nothing
- Produces: `definition_line(pos: str, glosses: Sequence[str]) -> str`

- [ ] **Step 1: Write the failing test**

```python
@pytest.mark.parametrize(
    ("pos", "glosses", "expected"),
    [
        ("noun", ["time; time; date"], "time, date"),
        (
            "noun",
            ["a proper time, time at which a thing can; ought to be done, time; time"],
            "a proper time, time at which a thing can or ought to be done, time",
        ),
        ("noun", ["The state; dignity of an abbot"], "The state or dignity of an abbot"),
        ("noun", ["The corn; fruit of an oak"], "The corn or fruit of an oak"),
        ("verb", ["to ward off; to guard; to save"], "ward off, guard, save"),
        ("verb", ["To ward off; To guard; To save"], "ward off, guard, save"),
        (
            "noun",
            ["Beautiful, like an elf; nymph, of elfin beauty"],
            "Beautiful, like an elf, nymph, of elfin beauty",
        ),
        ("noun", ["to ward off; to guard; to save"], "to ward off, to guard, to save"),
        ("verb", ["ward off, guard, ward off"], "ward off, guard"),
        ("noun", ["Time, time, date"], "Time, date"),
        ("noun", ["a proper time, time"], "a proper time, time"),
        ("noun", ["the refuse of things; things of no value"], "the refuse of things, things of no value"),
        ("verb", ["brought forth; pp. of"], "brought forth, pp. of"),
        ("noun", ["time; time", "time; date"], "time; time, date"),
        ("noun", ["time;; date"], "time, date"),
        ("noun", [" time ; date "], "time, date"),
        ("noun", ["", "  "], ""),
        ("noun", [], ""),
    ],
)
def test_definition_line(pos: str, glosses: list[str], expected: str) -> None:
    assert definition_line(pos, glosses) == expected
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/dictionary/test_definition_line.py::test_definition_line -v`
Expected: FAIL with `definition_line` not importable.

- [ ] **Step 3: Implement `definition_line(pos: str, glosses: Sequence[str]) -> str` in `wyrdcraeft/services/dictionary/definition_line.py`**

Per gloss, in ADR order: split on `;`, drop empty pieces, join each boundary with ` or ` or `, ` using the Global Constraints (whitespace words, comma-before-complement stays a comma), then strip a leading `to ` or `To ` from each comma-separated piece when `pos` is a verb, then drop repeated comma-separated items case-insensitively keeping the first spelling. Join the non-empty sense strings with `"; "` in the order given. Return `""` when none remain. Do not add the function to `services/dictionary/__init__.py`. Do not sort by `sense_path`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/dictionary/test_definition_line.py::test_definition_line -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/dictionary/test_definition_line.py wyrdcraeft/services/dictionary/definition_line.py
git commit -m "feat: read a dictionary entry as one definition line"
```

Skip this step unless the user asked for commits.

### Task 2: Pinned Copy control

**Files:**
- Modify: `wyrdcraeft/services/dictionary/browse_tui.py` (compose around the details title, `_format_entry_header_text`, `DictionaryBrowseApp`)
- Modify: `tests/dictionary/test_browse_tui.py` (`test_browse_single_main_result_auto_shows_details`, `test_build_then_browse_integration_smoke`, new copy tests)
- Test: `tests/dictionary/test_browse_tui.py`

**Interfaces:**
- Consumes: `definition_line(pos: str, glosses: Sequence[str]) -> str`
- Produces: widget `#details-title-bar` containing `#details-title` and `#copy-definition`; action `copy_definition` on `DictionaryBrowseApp`

- [ ] **Step 1: Write the failing tests**

In `test_browse_single_main_result_auto_shows_details`, stop requiring `"browseonly"` inside `_details_text`. Assert `"Details: browseonly" in _static_text(app.query_one("#details-title", Static))`, and keep the `POS: noun` and gloss assertions on `_details_text`.

In `test_build_then_browse_integration_smoke`, stop requiring `"abbad"` inside `_details_text`. Assert `"Details: abbad" in _static_text(app.query_one("#details-title", Static))`.

Add:

```python
async def test_copy_definition_button_copies_selected_entry(...):
    # insert headword "copyme", pos noun, summary_sense "time; time; date"
    # search, then:
    assert app.query_one("#copy-definition", Button).disabled is False
    await pilot.click("#copy-definition")
    await pilot.pause()
    assert app.clipboard == "time, date"

async def test_copy_definition_super_c_copies_the_same_line(...):
    # same "copyme" entry, search box focused, no selection
    await pilot.press("super+c")
    await pilot.pause()
    assert app.clipboard == "time, date"

async def test_copy_definition_follows_order_index_not_sense_path(...):
    # one entry, two senses inserted directly (not via _insert_entry):
    # order_index 0, sense_path "2", gloss_en "second"
    # order_index 1, sense_path "1", gloss_en "first"
    # search that headword, then:
    assert app.clipboard == ""  # before the click
    await pilot.click("#copy-definition")
    await pilot.pause()
    assert app.clipboard == "second; first"

async def test_copy_definition_stays_disabled_without_a_gloss(...):
    # insert headword "emptygloss", pos noun, summary_sense ""
    # search the single hit
    assert "Details: emptygloss" in _static_text(app.query_one("#details-title", Static))
    assert app.query_one("#copy-definition", Button).disabled is True
    await pilot.press("ctrl+c")
    await pilot.pause()
    assert app.clipboard == ""
    assert any("quit" in notification.message.casefold() for notification in app._notifications)

async def test_ctrl_c_in_search_selection_does_not_copy_the_definition(...):
    # after "copyme" is showing and its line is "time, date"
    from textual.selection import Selection
    search = app.query_one("#search-input", Input)
    search.selection = Selection(0, len(search.value))
    await pilot.press("ctrl+c")
    await pilot.pause()
    assert app.clipboard == search.value
```

In `test_browse_shows_connect_message_before_search`, assert `#copy-definition` is disabled, `"Details" in _static_text(...)` for `#details-title`, the button's ancestors include `#details-title-bar`, and they do not include `#details-content-scroll`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/dictionary/test_browse_tui.py::test_copy_definition_button_copies_selected_entry tests/dictionary/test_browse_tui.py::test_copy_definition_super_c_copies_the_same_line tests/dictionary/test_browse_tui.py::test_copy_definition_follows_order_index_not_sense_path tests/dictionary/test_browse_tui.py::test_copy_definition_stays_disabled_without_a_gloss tests/dictionary/test_browse_tui.py::test_ctrl_c_in_search_selection_does_not_copy_the_definition tests/dictionary/test_browse_tui.py::test_browse_single_main_result_auto_shows_details tests/dictionary/test_browse_tui.py::test_build_then_browse_integration_smoke tests/dictionary/test_browse_tui.py::test_browse_shows_connect_message_before_search -v`
Expected: FAIL because `#copy-definition` is absent and the headword is still inside `#details-content`.

- [ ] **Step 3: Wire the pane in `browse_tui.py`**

Replace the details-pane `Static("Details", id="details-title")` with a `Horizontal(id="details-title-bar")` that yields `Static("Details", id="details-title")` and `Button("Copy", id="copy-definition", disabled=True)`. Keep that bar outside `#details-content-scroll`. Give the bar `height: auto` and put the button on the right.

Drop the bare `details.headword` line from `_format_entry_header_text`. Leave POS, variants, morph class, gender, person, and number.

On `DictionaryBrowseApp`, store the current line. `_show_entry_details` sets the title to `Details: {headword}`, sorts `details.senses` by `order_index`, computes `definition_line(details.pos, [sense.gloss_en for sense in that order])`, and sets `disabled` on `#copy-definition` from whether that line is empty. `_show_idle_details` sets the title back to `Details`, clears the line, and disables the button.

Bind `ctrl+c,super+c` to `copy_definition` with `show=False` and without `priority`. `action_copy_definition` calls `self.copy_to_clipboard(line)` when the line is non-empty and raises `SkipAction` otherwise. The button's press handler calls that same action.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/dictionary/test_definition_line.py tests/dictionary/test_browse_tui.py -v`
Expected: PASS

- [ ] **Step 5: Quality gate**

Run: `.venv/bin/ruff check wyrdcraeft/services/dictionary/definition_line.py wyrdcraeft/services/dictionary/browse_tui.py tests/dictionary/test_definition_line.py tests/dictionary/test_browse_tui.py`
Run: `.venv/bin/mypy wyrdcraeft/services/dictionary/definition_line.py wyrdcraeft/services/dictionary/browse_tui.py`
Run: `make napoleon-gate`
Run: `graphify update .`
Expected: ruff and mypy clean on the touched files, napoleon-gate at the baseline, graphify update finishes.

- [ ] **Step 6: Commit**

```bash
git add wyrdcraeft/services/dictionary/browse_tui.py tests/dictionary/test_browse_tui.py
git commit -m "feat: copy a definition line from dictionary browse"
```

Skip this step unless the user asked for commits.
