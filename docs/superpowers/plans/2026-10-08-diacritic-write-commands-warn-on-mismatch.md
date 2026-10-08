# Diacritic Write Commands Warn on Mismatched Forms Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `diacritic add` and the `diacritic disambiguate` actions "replace unique" and "add attested form" warn and ask for confirmation when the form they are about to store does not normalize to its own key.

**Architecture:** One helper in `wyrdcraeft/cli/diacritic.py`, `_confirm_form_matches_key(key, form, *, yes=False) -> bool`, compares `normalize_old_english(form)` with the key. `add` calls it before storing and gets a `--yes/-y` flag; `disambiguate` already imports from `diacritic.py` and calls it at the two store points. A decline leaves the index file untouched. The check is a single comparison, so it stays in the CLI module beside the other index helpers.

**Tech Stack:** click, rich `Prompt`, pytest with click's `CliRunner` (the `runner` and `temp_dir` fixtures).

**Spec:** [ADR 0018](../../adr/0018-diacritic-write-commands-warn-on-non-normalizing-forms.md). Decision 4 (tests for `add`/`delete`) is already done: `tests/test_cli_diacritic.py` has 13 tests.

## Global Constraints

- Compare with `normalize_old_english` (lowercase, ð→þ, strip marks, drop internal hyphens). No other rule.
- Warn and confirm; never hard-reject. `blac` → `blæc` must remain storable.
- `--yes` skips the prompt (`add`). `delete` already has `--yes/-y`; leave it alone.
- Methods ≤ 60 lines; Napoleon docstrings. `make napoleon-gate` must stay at the 94-violation baseline; `mypy` keeps its one pre-existing error at `wyrdcraeft/cli/cli.py:107`.
- Do not stage `doc/source/changelog.rst`, `uv.lock`, or `wyrdcraeft/etc/dictionary/oe_bt.json`.
- Do not touch `wyrdcraeft/etc/diacritic/oe_bt_macron_index.json`.

## Rulings to confirm (made while planning)

- **No `--yes` on `disambiguate`.** ADR decision 1 says "`--yes` skips the prompt" but `disambiguate` is an interactive session with no flags for its other prompts. Only `add` gets `--yes`. If you want one on `disambiguate` too, it is a one-line addition per call site.
- **The "choose a candidate" action (`c`) is checked too** (reversed after review: four packaged ambiguous candidates do not normalize to their key). The ADR's Implementation notes record this.
- **A decline returns to the action menu** (`continue`) rather than ending the key, so the user can retype the form.

## Review Focus

- A form that differs from its key only by hyphens, case, ð/þ or marks must NOT warn (`ðæt-sum` for `þætsum`, `āċ` for `ac`). Tested in Task 1 and Task 2.
- A form in decomposed (NFD) input, such as `āc`, must not warn for key `ac`. Task 1.
- Declining must leave the file byte-identical, including the counts in `meta`. Tasks 1 and 2.
- `--force` and `--yes` are independent: `--force` allows overwriting an existing key, `--yes` answers the mismatch prompt. Task 1.
- Declining "add attested form" must not start the annotation prompts. Task 2.

---

### Task 1: `_confirm_form_matches_key` and `diacritic add`

**Files:**
- Modify: `wyrdcraeft/cli/diacritic.py` (helper after `_write_macron_index_payload`, `from rich.markup import escape` import, `--yes` option and the call in `diacritic_add`)
- Test: `tests/test_cli_diacritic.py`

**Interfaces:**
- Consumes: `normalize_old_english(text: str | None) -> str | None` (already imported), `Prompt`, `print_info` (already imported).
- Produces: `_confirm_form_matches_key(key: str, form: str, *, yes: bool = False) -> bool`. `True` means "go ahead and store". Task 2 imports it.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_cli_diacritic.py`:

```python
def test_add_mismatching_form_prompts_and_declines_by_default(runner, index_path):
    before = index_path.read_text(encoding="utf-8")

    result = runner.invoke(
        cli,
        ["diacritic", "add", "blac", "blǣc", "--index-path", str(index_path)],
        input="\n",
    )

    assert result.exit_code == 0, result.output
    assert "does not match its key" in result.output
    assert index_path.read_text(encoding="utf-8") == before


def test_add_mismatching_form_is_stored_when_confirmed(runner, index_path):
    result = runner.invoke(
        cli,
        ["diacritic", "add", "blac", "blǣc", "--index-path", str(index_path)],
        input="y\n",
    )

    assert result.exit_code == 0, result.output
    assert "does not match its key" in result.output
    assert _read(index_path)["unique"]["blac"] == "blǣc"


def test_add_mismatching_form_with_yes_skips_the_prompt(runner, index_path):
    result = _run(
        runner, "add", "blac", "blǣc", "--yes", "--index-path", str(index_path)
    )

    assert result.exit_code == 0, result.output
    assert "Store it anyway" not in result.output
    assert _read(index_path)["unique"]["blac"] == "blǣc"


@pytest.mark.parametrize(
    ("key", "form"),
    [
        ("þætsum", "ðæt-sum"),
        ("lac", "l\u0101\u010b"),
        ("lac", "la\u0304c"),
        ("hlaford", "Hlāford"),
    ],
)
def test_add_form_that_normalizes_to_its_key_does_not_prompt(
    runner, index_path, key, form
):
    result = _run(runner, "add", key, form, "--index-path", str(index_path))

    assert result.exit_code == 0, result.output
    assert "does not match its key" not in result.output
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_cli_diacritic.py -k "mismatching or normalizes_to_its_key" -v`
Expected: the three `mismatching` tests FAIL (no prompt appears; `--yes` is an unknown option); the parametrized tests PASS already (nothing prompts yet). A parametrized test that passes now is correct; it guards against over-warning in Step 4.

- [ ] **Step 3: Write the helper and wire it into `add`**

In `wyrdcraeft/cli/diacritic.py`, after `_write_macron_index_payload`:

```python
def _confirm_form_matches_key(key: str, form: str, *, yes: bool = False) -> bool:
    """
    Check that a form to be stored belongs to its key, asking when it does not.

    A form belongs to its key when it normalizes to it (case, ``ð``/``þ``,
    marks and internal hyphens ignored). A mismatch is allowed, for example a
    curated variant such as ``blac`` stored as ``blǣc``, but the entry cannot
    be applied to text and only appears in the ``.unaligned`` report.

    Side Effects:
        Prints a notice when ``yes`` is set; otherwise reads one answer.

    Args:
        key: Normalized index key.
        form: Display form about to be stored under the key.

    Keyword Args:
        yes: If True, accept a mismatch without prompting.

    Returns:
        True when the form matches the key or the mismatch is accepted.

    """
    normalized = normalize_old_english(form)
    if normalized == key:
        return True
    message = (
        f"Form {escape(repr(form))} does not match its key {escape(repr(key))}: "
        f"it normalizes to {escape(repr(normalized))}. Text matching "
        f"{escape(repr(key))} cannot be aligned to it, so it will only appear "
        "in the .unaligned report."
    )
    if yes:
        print_info(message)
        return True
    answer = Prompt.ask(f"{message} Store it anyway?", choices=["y", "n"], default="n")
    return answer == "y"
```

Add the option to `diacritic_add` (after `--force`):

```python
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Store a form that does not match its key without asking.",
)
```

Change the signature and docstring: add `yes: bool,` after `force: bool,` and `yes: If True, skip the prompt for a form that does not match its key.` after the `force` arg line. Replace `payload.unique[key] = macron_form` with:

```python
    if not _confirm_form_matches_key(key, macron_form, yes=yes):
        print_info("Add cancelled.")
        return
    payload.unique[key] = macron_form
```

Wrap the long `Prompt.ask(...)` line so ruff passes (`ruff format` will do it).

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_cli_diacritic.py -v`
Expected: all pass (13 old plus 7 new).

- [ ] **Step 5: Quality gate and commit**

Run: `.venv/bin/ruff format wyrdcraeft/cli/diacritic.py tests/test_cli_diacritic.py && .venv/bin/ruff check wyrdcraeft/cli/diacritic.py tests/test_cli_diacritic.py && .venv/bin/mypy wyrdcraeft/cli/diacritic.py`
Expected: clean (mypy may still report the one pre-existing `cli.py:107` error).

```bash
git add wyrdcraeft/cli/diacritic.py tests/test_cli_diacritic.py
git commit -m "feat: diacritic add asks before storing a form that does not match its key"
```

(End the message with the Co-Authored-By line from the session's attribution rule.)

---

### Task 2: `disambiguate` "replace unique" and "add attested form"

**Files:**
- Modify: `wyrdcraeft/cli/diacritic_disambiguate.py` (import line 26; action `r` near line 558; action `a` near line 610)
- Test: `tests/test_cli_diacritic_disambiguate.py`

**Interfaces:**
- Consumes: `_confirm_form_matches_key(key, form, *, yes=False) -> bool` from Task 1.
- Produces: nothing later tasks use.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_cli_diacritic_disambiguate.py` (reuse `_write_index`; the `ac` payload is the same one the neighbouring tests use):

```python
def _ac_index(path):
    _write_index(
        path,
        {
            "meta": {"unique_count": 0, "ambiguous_count": 1},
            "unique": {},
            "ambiguous": {"ac": ["ac", "āc"]},
            "ambiguous_metadata": {},
        },
    )


def _disambiguate(runner, index_path, text):
    return runner.invoke(
        cli,
        ["diacritic", "disambiguate", "ac", "--index-path", str(index_path)],
        input=text,
    )


def test_diacritic_disambiguate_replace_mismatch_declined_keeps_state(
    runner, temp_dir
):
    index_path = temp_dir / "index.json"
    _ac_index(index_path)
    before = index_path.read_text(encoding="utf-8")

    result = _disambiguate(runner, index_path, "r\nax\nn\nq\n")

    assert result.exit_code == 0, result.output
    assert "does not match its key" in result.output
    assert index_path.read_text(encoding="utf-8") == before


def test_diacritic_disambiguate_replace_mismatch_confirmed_commits(runner, temp_dir):
    index_path = temp_dir / "index.json"
    _ac_index(index_path)

    result = _disambiguate(runner, index_path, "r\nax\ny\ny\n")

    assert result.exit_code == 0, result.output
    assert "does not match its key" in result.output
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert payload["unique"]["ac"] == "ax"
    assert "ac" not in payload["ambiguous"]


def test_diacritic_disambiguate_add_mismatch_declined_starts_no_annotation(
    runner, temp_dir
):
    index_path = temp_dir / "index.json"
    _ac_index(index_path)
    before = index_path.read_text(encoding="utf-8")

    result = _disambiguate(runner, index_path, "a\nax\nn\nq\n")

    assert result.exit_code == 0, result.output
    assert "does not match its key" in result.output
    assert index_path.read_text(encoding="utf-8") == before


def test_diacritic_disambiguate_add_matching_form_does_not_warn(runner, temp_dir):
    index_path = temp_dir / "index.json"
    _ac_index(index_path)

    result = _disambiguate(
        runner, index_path, "a\n\u0101\u010b\n2\ngloss\nn\n6\nbut\nn\n1\noak\nn\nq\n"
    )

    assert result.exit_code == 0, result.output
    assert "does not match its key" not in result.output
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert payload["ambiguous"]["ac"] == ["ac", "\u0101c", "\u0101\u010b"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_cli_diacritic_disambiguate.py -k "mismatch or matching_form" -v`
Expected: the two `declined` tests and the `confirmed` test FAIL (the confirmed one on the missing warning text); the `matching_form` test PASSES already.

- [ ] **Step 3: Wire the check into both actions**

Change the import (line 26) to:

```python
from .diacritic import (
    _confirm_form_matches_key,
    _load_macron_index_payload,
    _write_macron_index_payload,
)
```

In action `r`, directly after `if replacement_form is None: continue`:

```python
                if not _confirm_form_matches_key(key, replacement_form):
                    continue
```

In action `a`, directly after `if new_form is None: continue`:

```python
                if not _confirm_form_matches_key(key, new_form):
                    continue
```

- [ ] **Step 4: Run the new tests, then fix the older tests that now see a prompt**

Run: `.venv/bin/python -m pytest tests/test_cli_diacritic_disambiguate.py -v`
Expected: the new tests pass. Older tests fail (three at first; a fourth once action `c` is also checked, see the rulings) because they add the mismatching form `ax` or `ā` for key `ac` and have no answer for the new prompt: `test_diacritic_disambiguate_add_entry_and_annotate_all_forms`, `test_diacritic_disambiguate_add_stays_on_same_key_after_save`, `test_diacritic_disambiguate_add_entry_accepts_unicode_form`. In each, insert `y\n` right after the new-form line (for example `a\nax\ny\n2\n…`, and `a\n{combining_a_macron}\ny\n2\n…`). `…accepts_option_escape_sequence` uses `ā-flian` for key `aflian`, which matches, so it needs no change. If the run shows other failures, fix them the same way only when the form really does not match its key; otherwise stop and investigate.

Run again: `.venv/bin/python -m pytest tests/test_cli_diacritic_disambiguate.py tests/test_cli_diacritic.py -v`
Expected: all pass.

- [ ] **Step 5: Docs, quality gate, full suite, commit**

Run: `grep -rn "diacritic add\|diacritic delete" doc/source docs/context CONTEXT.md | head`. If a command doc lists `add` options, add `--yes/-y` and one sentence on the mismatch prompt there. Skip any file that does not describe `add`'s options.

Run:
```bash
.venv/bin/ruff format wyrdcraeft/cli tests/test_cli_diacritic.py tests/test_cli_diacritic_disambiguate.py
.venv/bin/ruff check wyrdcraeft/cli tests
.venv/bin/mypy wyrdcraeft/cli/diacritic.py wyrdcraeft/cli/diacritic_disambiguate.py
make napoleon-gate
.venv/bin/python -m pytest -q
```
Expected: ruff clean; mypy only the pre-existing `cli.py:107` error; napoleon gate at the 94 baseline; full suite green (1,152 before plus the new tests (15 as shipped, so 1,167 passed); report the real number).

```bash
git add wyrdcraeft/cli/diacritic_disambiguate.py tests/test_cli_diacritic_disambiguate.py
git add -u doc/source docs/context CONTEXT.md -- ':!doc/source/changelog.rst'
git commit -m "feat: disambiguate asks before replacing or adding a form that does not match its key"
```

(End the message with the Co-Authored-By line from the session's attribution rule.)

After both tasks, update ADR 0018's intro ("Nothing here is implemented yet" → describe what shipped, including the three rulings above) and commit it with `docs:`. The ADR status stays `proposed`; that is the user's call.
