# Standard Elements, Ambiguity Policy and Acceptance Fixture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish ADR 0019. `source mark-diacritics` standardizes prefix and compound-element marks before comparing options (decision 3), resolves still-ambiguous keys with `--ambiguity-policy auto|leave|union` (decision 4) and keeps every guessed token visible in the ambiguity report (decision 6). A fixture of the user's past decisions measures the `auto` rule (decision 8). The four minors deferred from the first slice are fixed first.

**Architecture:** A new `StandardElements` service (hand-edited data file under `wyrdcraeft/etc/diacritic/`) rewrites the marks of listed elements in a reference form. `DiacriticTransfer.same_marks` takes an optional `StandardElements`, so the applicator and the `diacritic-disambiguate` queue share one collapse predicate. `DiacriticTransfer` gains `union_form` and `differs_only_before_hyphen`; `MacronApplicator` gains a `policy` and applies the union through the normal additive transfer. `MacronAmbiguity` gains `applied_form` and `policy`.

**Tech Stack:** Python dataclasses, pydantic, click `CliRunner`, pytest, `git` (fixture extraction only).

**Spec:** [ADR 0019](../../adr/0019-ambiguity-is-judged-on-marks-and-resolved-by-policy.md) decisions 1, 3, 4, 6, 7 (the standard-element part), 8, and its Open question (file location). Builds on the first slice (`docs/superpowers/plans/2026-10-08-ambiguity-collapses-on-marks.md`, commits 662103c..e1113c3) and [ADR 0020](../../adr/0020-diacritic-transfer-treats-a-diphthong-as-one-unit.md).

## Scope: what this plan does not do

- **ADR 0017** (BT variant importer for `diacritic add`) is a different feature, blocked on a junk filter and a collision policy. It gets its own plan when those are decided.
- ADR statuses (0018, 0019, 0020) stay `proposed`; accepting them is the user's call.
- No CLI to edit the standard-element file (ADR 0019 Open question: hand-edited, like the `c` and `g` lists).

## Addendum: Task 5

Task 5 was added after the final review of Tasks 1 to 4 (commits 7e95069..cc022bd). It fixes five minors the review deferred: a guessed token that cannot be aligned loses its unaligned diagnostic; `standard_elements.txt` fails silently on conflicting duplicates and inline comments; a missing list file raises instead of warning like the `c`/`g` lists; the `MacronApplicator` class docstring lacks the new keyword arguments; the `.rst` overstates `union` and `auto`. Three further review minors stay deferred (see the end of Task 5).

## Global Constraints

- Additive only (ADR 0015): nothing is removed or replaced in the source. A source that writes `ā-`, `fōr-`, `gē-` or `oþ-` keeps it.
- Never rewrite the `ambiguous` list or any data in `wyrdcraeft/etc/diacritic/oe_bt_macron_index.json` (ADR 0016). Everything here is a runtime rule.
- A key in `ambiguous_completed` is never collapsed, never resolved by `auto` or `union` (decision 5).
- Hyphen evidence comes from the BT form only: an element counts where BT writes a hyphen directly after it (prefix entry `x-`) or around it (compound entry `x`). BT forms with no such hyphen (`fōr`, `fōrþ`, `gēon`, `gēan`) are never standardized.
- Ambiguity report rows keep their existing fields; new fields are optional with default `None` (consumers of `.anomalies` JSON must tolerate them).
- Methods ≤ 60 lines. Napoleon docstrings (`Keyword Args:` for kw-only), `#:` comments on attributes and module globals. `make napoleon-gate` must stay at the 94 baseline; `mypy` keeps its one pre-existing error at `wyrdcraeft/cli/cli.py:107`; ruff clean on touched files (43 pre-existing errors elsewhere).
- Do not stage `doc/source/changelog.rst`, `uv.lock`, `wyrdcraeft/etc/dictionary/oe_bt.json` or `graphify-out/`. Do not `ruff format` the whole `wyrdcraeft/cli` directory; name files.
- Before editing, run `graphify query` on the symbol; after code edits run `graphify update .`.
- Test command: `.venv/bin/python -m pytest`. Baseline before this plan: 1189 passed.

## Rulings to confirm (made while planning)

- **Service default policy is `leave`; the CLI default is `auto`.** ADR 0019 makes `auto` the CLI default. Library callers and the ~10 existing tests that build `MacronApplicator` directly keep today's behavior until they opt in. Cost if wrong: one default flipped.
- **Keys resolved by `auto`/`union` stay in the `diacritic-disambiguate` queue.** Only keys that collapse (decisions 2 and 3) are skipped. A guess is exactly what the user may want to rule on. Cost if wrong: a longer queue.
- **A conflict is two or more of macron, breve and diaeresis on one letter across the options.** Dot-above does not conflict with them (`ġ` + macron is a union). On a conflicting letter `union` adds no marks. Cost if wrong: a letter left unmarked.
- **Standardization applies to the first hyphen segment for prefix entries (`for-`) and to any hyphen-bounded segment for compound entries (`bonde`)**, and only when the form has at least two segments.
- **`auto` leaves `ge-an`/`gēan` (and any pair whose marks differ only before a BT hyphen) even when the element is on the standard list.** ADR decision 4 words the exception as "...and that prefix or first element is not on the standard-element list". Read literally, a listed element that did not collapse (because one option has no hyphen) would be guessed. Decision 3 says a `gē` in an unhyphenated word is a different word on purpose, so the plan leaves it. Cost if wrong: `gēan` stays in the report instead of being marked; `--ambiguity-policy union` still marks it.
- **When several options of an ambiguous key collapse, the form transferred is the one with the most diphthongs** (Task 1 minor 1), ties go to the first option.
- **The fixture's `same_word` label includes keys where the user chose one option, not the union.** The test counts any mark added to such a key as a hit, so coverage is slightly optimistic. It is a regression floor, not a precision claim. Cost if wrong: the pinned coverage is a few points high.
- **Fixture counts will not equal the ADR's 86/77.** The ADR counted by hand from history; the script (Task 4) applies a stated rule. The test pins the measured numbers and says so.

## Review Focus

- **A source word that already carries `ā-`/`fōr-` marks** must come out unchanged, not re-marked to the standard form (additive).
- **`ge-an` vs `gēan`** (hyphen in one option only) must stay ambiguous under `leave` and be left by `auto` (marks differ only before a BT hyphen).
- **A decomposed (NFD) source** with a union-resolved key must keep its source letters byte-for-byte except for added marks.
- **A `union` over options with different letter counts** (hand-edited bad data) must not crash the run; the token stays in the report.
- **A key in both `unique` and `ambiguous`** keeps the ambiguity row (and under `auto` follows the policy), never silently takes the unique form.
- **A hand-edited standard-element file with blank lines, comments, a BOM or duplicate entries** loads without error.

---

### Task 1: Deferred minors from the first slice

**Files:**
- Modify: `wyrdcraeft/services/markup.py` (`DiacriticTransfer`: new `diphthong_count`; `MacronApplicator._collapsed_form`)
- Modify: `wyrdcraeft/cli/diacritic_disambiguate.py:471-490`
- Modify: `docs/adr/0020-diacritic-transfer-treats-a-diphthong-as-one-unit.md` (intro)
- Test: `tests/test_markup.py`, `tests/test_cli_diacritic_disambiguate.py`

**Interfaces:**
- Produces: `DiacriticTransfer.diphthong_count(form: str) -> int` (classmethod); `_collapsed_form` returns the option with the most diphthongs. Task 2 keeps this rule when it standardizes options.

The four minors: (1) the first option can double-mark a diphthong: options `stē-ap`/`stēap` collapse, the first (`stē-ap`, no diphthong) transferred onto source `steāp` gives `stēāp`; (2) the queue prints "Skipped N" and then a misleading "No unresolved" when everything collapsed; (3) no test pins that a key in both `unique` and `ambiguous` keeps its ambiguity row; (4) ADR 0020's intro says nothing is implemented.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_markup.py`:

```python
def test_apply_collapse_does_not_double_mark_a_diphthong(tmp_path: Path):
    index_path = tmp_path / "index.json"
    # "stē-ap" sorts before "stēap"; only the second treats ēa as one unit.
    _write_index(index_path, unique={}, ambiguous={"steap": ["stē-ap", "stēap"]})

    transformed, ambiguity, _, _ = MacronApplicator(index_path).apply("steāp", 1, 1)

    assert ambiguity is None
    assert transformed == "steāp"


def test_apply_keeps_ambiguity_when_key_is_in_unique_and_ambiguous(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(index_path, unique={"ac": "ac"}, ambiguous={"ac": ["ac", "āc"]})

    transformed, ambiguity, is_unknown, _ = MacronApplicator(index_path).apply("ac", 1, 1)

    assert transformed == "ac"
    assert ambiguity is not None
    assert not is_unknown
```

Append to `tests/test_cli_diacritic_disambiguate.py` (after the existing queue tests):

```python
def test_diacritic_disambiguate_queue_says_nothing_is_left_when_all_collapse(
    runner, temp_dir, monkeypatch
):
    index_path = temp_dir / "index.json"
    _write_index(
        index_path,
        {
            "meta": {"unique_count": 0, "ambiguous_count": 1},
            "unique": {},
            "ambiguous": {"cuslyppe": ["cū-slyppe", "cūslyppe"]},
            "ambiguous_completed": [],
            "ambiguous_metadata": {},
        },
    )

    result, messages = _run_queue(runner, index_path, monkeypatch)

    assert result.exit_code == 0, result.output
    assert any(m.startswith("Skipped 1 entries") for m in messages)
    assert any(m.startswith("No ambiguous entries need a decision") for m in messages)
    assert not any(m.startswith("No unresolved") for m in messages)
```

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_markup.py::test_apply_collapse_does_not_double_mark_a_diphthong tests/test_markup.py::test_apply_keeps_ambiguity_when_key_is_in_unique_and_ambiguous tests/test_cli_diacritic_disambiguate.py::test_diacritic_disambiguate_queue_says_nothing_is_left_when_all_collapse -v`
Expected: the double-mark test FAILS with `'stēāp' == 'steāp'`; the queue test FAILS (no "No ambiguous entries need a decision" message); the unique+ambiguous test PASSES (it pins existing behavior, grade it as such; it is the only one allowed to pass first).

- [ ] **Step 3: Implement**

In `DiacriticTransfer` (next to `mark_pattern`) add:

```python
    @classmethod
    def diphthong_count(cls, form: str) -> int:
        """
        Count the diphthongs of a form.

        Args:
            form: An index display form.

        Returns:
            The number of diphthong units (see :meth:`_diphthong_starts`).

        """
        return len(cls._diphthong_starts(cls._parse(form)))
```

In `MacronApplicator._collapsed_form` replace `return options[0]` with:

```python
        # A form that already reads ea/eo/ie/io as one unit cannot double-mark a
        # source that put the macron on the second vowel; ties go to the first.
        return max(options, key=DiacriticTransfer.diphthong_count)
```

and update its docstring `Returns:` to "The option with the most diphthongs (first on ties) when the options agree on marks, else ``None``."

In `wyrdcraeft/cli/diacritic_disambiguate.py` replace the `if not target_keys:` block with:

```python
        if not target_keys:
            if pending:
                print_info(
                    "No ambiguous entries need a decision "
                    f"in {index_path} (completed={len(payload.ambiguous_completed)})."
                )
            else:
                print_info(
                    "No unresolved ambiguous entries found "
                    f"in {index_path} (completed={len(payload.ambiguous_completed)})."
                )
            return
```

In `docs/adr/0020-...md` replace "Nothing here is implemented yet." with "Implemented in `DiacriticTransfer` (`mark_pattern`, diphthong-aware `transfer`); see ADR 0019 for how the applicator uses it."

- [ ] **Step 4: Run to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_markup.py tests/test_cli_diacritic_disambiguate.py -q`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add wyrdcraeft/services/markup.py wyrdcraeft/cli/diacritic_disambiguate.py docs/adr/0020-diacritic-transfer-treats-a-diphthong-as-one-unit.md tests/test_markup.py tests/test_cli_diacritic_disambiguate.py
git commit -m "fix: collapse prefers the diphthong form; clearer queue message when all keys collapse"
```

---

### Task 2: Standard element forms (ADR 0019 decision 3)

**Files:**
- Create: `wyrdcraeft/services/standard_elements.py`
- Create: `wyrdcraeft/etc/diacritic/standard_elements.txt`
- Modify: `wyrdcraeft/services/markup.py` (`DiacriticTransfer.same_marks` gains `elements`; `MacronApplicator.__init__`, `_collapsed_form`, `apply`)
- Modify: `wyrdcraeft/cli/diacritic_disambiguate.py` (queue filter)
- Modify docs: `doc/source/overview/command_convert_mark_diacritics.rst`, `doc/source/overview/command_diacritic_disambiguate.rst`, `docs/context/diacritic.md`, `CONTEXT.md` (term "standard element")
- Test: `tests/test_standard_elements.py` (new), `tests/test_markup.py`, `tests/test_cli_diacritic_disambiguate.py`

**Interfaces:**
- Produces: `StandardElements(entries: Iterable[str])`; `StandardElements.load(path: Path = DEFAULT_STANDARD_ELEMENTS_PATH) -> StandardElements`; `StandardElements.standardize(form: str) -> str`; `DEFAULT_STANDARD_ELEMENTS_PATH: Path`. `DiacriticTransfer.same_marks(forms, elements: StandardElements | None = None) -> bool`. `MacronApplicator(index_path=..., *, standard_elements: StandardElements | None = None)` (`None` loads the packaged file) with attribute `standard_elements`. Task 3 consumes `MacronApplicator._standardized_options(normalized) -> list[str]`, defined here.
- Consumes: Task 1's `_collapsed_form` diphthong rule (keep it, applied to the standardized options).

Data file `wyrdcraeft/etc/diacritic/standard_elements.txt` (`pyproject.toml` already packages `etc/diacritic/*.txt`). One standard spelling per line; `#` comments and blank lines ignored. A trailing hyphen marks a prefix (first segment, `for-`); an entry without hyphens is a compound element matched as any hyphen-bounded segment (`bonde`). A form needs at least two segments, so a bare `fōr` or `gēan` never matches.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_standard_elements.py`:

```python
from __future__ import annotations

from pathlib import Path

import pytest

from wyrdcraeft.services.standard_elements import (
    DEFAULT_STANDARD_ELEMENTS_PATH,
    StandardElements,
)

ELEMENTS = StandardElements(
    ["a-", "for-", "fore-", "ge-", "bonde", "hīrēd-", "bēacen-", "ōþ-"]
)


@pytest.mark.parametrize(
    ("form", "expected"),
    [
        ("ā-bacan", "a-bacan"),
        ("fōr-beran", "for-beran"),
        ("fōre-beran", "fore-beran"),
        ("gē-bindan", "ge-bindan"),
        ("ge-bēd-man", "ge-bēd-man"),
        ("gē-bēd-man", "ge-bēd-man"),
        ("hūs-bōnde", "hūs-bonde"),
        ("bōnde-land", "bonde-land"),
        ("hīred-mann", "hīrēd-mann"),
        ("beacen-fȳr", "bēacen-fȳr"),
        ("oð-feolan", "ōþ-feolan"),
        # No BT hyphen after the element: never standardized.
        ("gēan", "gēan"),
        ("fōr", "fōr"),
        ("fōrþ", "fōrþ"),
        ("bōnde", "bōnde"),
        ("gēon", "gēon"),
        # Different element, same start.
        ("foran-weard", "foran-weard"),
        ("gebed-tīd", "gebed-tīd"),
        # A prefix entry only matches the first segment.
        ("hūs-fōr-beran", "hūs-fōr-beran"),
    ],
)
def test_standardize(form: str, expected: str):
    assert ELEMENTS.standardize(form) == expected


def test_load_ignores_comments_blanks_bom_and_duplicates(tmp_path: Path):
    path = tmp_path / "elements.txt"
    path.write_text("﻿# editorial\n\nfor-\nfor-\nbonde\n", encoding="utf-8")

    elements = StandardElements.load(path)

    assert elements.standardize("fōr-beran") == "for-beran"
    assert elements.standardize("hūs-bōnde") == "hūs-bonde"


def test_packaged_file_lists_the_adr_elements():
    elements = StandardElements.load(DEFAULT_STANDARD_ELEMENTS_PATH)

    assert elements.standardize("ā-bacan") == "a-bacan"
    assert elements.standardize("fōre-beran") == "fore-beran"
    assert elements.standardize("hīred-mann") == "hīrēd-mann"
    assert elements.standardize("ōþ-feolan") == "ōþ-feolan"
    assert elements.standardize("gebed-tīd") == "gebed-tīd"
```

Append to `tests/test_markup.py`:

```python
def test_same_marks_standardizes_elements_first():
    elements = StandardElements(["hīrēd-", "for-"])

    assert not DiacriticTransfer.same_marks(["hīred-mann", "hīrēd-mann"])
    assert DiacriticTransfer.same_marks(["hīred-mann", "hīrēd-mann"], elements)
    assert DiacriticTransfer.same_marks(["for-beran", "fōr-beran"], elements)
    # No BT hyphen in one option, so the pair stays ambiguous.
    assert not DiacriticTransfer.same_marks(["ge-an", "gēan"], StandardElements(["ge-"]))


@pytest.mark.parametrize(
    ("ambiguous", "word", "expected"),
    [
        ({"hiredmann": ["hīred-mann", "hīrēd-mann"]}, "hiredmann", "hīrēdmann"),
        ({"foreberan": ["fore-beran", "fōre-beran"]}, "foreberan", "foreberan"),
    ],
)
def test_apply_collapses_options_that_differ_only_in_a_standard_element(
    tmp_path: Path, ambiguous: dict[str, list[str]], word: str, expected: str
):
    index_path = tmp_path / "index.json"
    _write_index(index_path, unique={}, ambiguous=ambiguous)

    transformed, ambiguity, _, _ = MacronApplicator(index_path).apply(word, 1, 1)

    assert ambiguity is None
    assert transformed == expected


def test_apply_keeps_ge_an_and_gean_apart(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(index_path, unique={}, ambiguous={"gean": ["ge-an", "gēan"]})

    transformed, ambiguity, _, _ = MacronApplicator(index_path).apply("gean", 1, 1)

    assert transformed == "gean"
    assert ambiguity is not None


@pytest.mark.parametrize(
    ("unique", "word", "expected"),
    [
        ({"abacan": "ā-bacan"}, "abacan", "abacan"),
        ({"oþfeolan": "oþ-feolan"}, "oþfeolan", "ōþfeolan"),
        # Source keeps its own marks (additive, ADR 0015).
        ({"abacan": "ā-bacan"}, "ābacan", "ābacan"),
    ],
)
def test_apply_standardizes_unique_forms_too(
    tmp_path: Path, unique: dict[str, str], word: str, expected: str
):
    index_path = tmp_path / "index.json"
    _write_index(index_path, unique=unique, ambiguous={})

    assert MacronApplicator(index_path).apply(word, 1, 1)[0] == expected


def test_apply_never_collapses_a_completed_key_even_through_elements(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(
        index_path,
        unique={},
        ambiguous={"foreberan": ["fore-beran", "fōre-beran"]},
        ambiguous_completed=["foreberan"],
    )

    _, ambiguity, _, _ = MacronApplicator(index_path).apply("foreberan", 1, 1)

    assert ambiguity is not None
```

Add to the imports at the top of `tests/test_markup.py` (match the file's existing import style): `from wyrdcraeft.services.standard_elements import StandardElements`; `DiacriticTransfer` is already imported.

Append to `tests/test_cli_diacritic_disambiguate.py`:

```python
def test_diacritic_disambiguate_queue_skips_keys_that_differ_only_in_a_standard_element(
    runner, temp_dir, monkeypatch
):
    index_path = temp_dir / "index.json"
    _write_index(
        index_path,
        {
            "meta": {"unique_count": 0, "ambiguous_count": 2},
            "unique": {},
            "ambiguous": {
                "foreberan": ["fore-beran", "fōre-beran"],
                "þa": ["þa", "þā"],
            },
            "ambiguous_completed": [],
            "ambiguous_metadata": {},
        },
    )

    result, messages = _run_queue(runner, index_path, monkeypatch)

    assert result.exit_code == 0, result.output
    assert "fore-beran" not in result.output
    assert any(m.startswith("Skipped 1 entries") for m in messages)
```

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_standard_elements.py tests/test_markup.py tests/test_cli_diacritic_disambiguate.py -q`
Expected: collection ERROR `ModuleNotFoundError: wyrdcraeft.services.standard_elements`.

- [ ] **Step 3: Write the module and data file**

`wyrdcraeft/etc/diacritic/standard_elements.txt`:

```text
# Prefixes and compound elements with one standard spelling (ADR 0019).
# A trailing hyphen marks a prefix; no hyphen marks a compound element.
# Write each entry as it should be spelled; marks are matched ignoring case,
# eth/thorn and diacritics. BT's mark variants of these are an editorial choice.
a-
for-
fore-
ge-
bonde
hīrēd-
bēacen-
ōþ-
```

`wyrdcraeft/services/standard_elements.py`:

```python
"""Standard spellings for prefixes and compound elements (ADR 0019)."""

from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Iterable

#: Packaged, hand-edited list of standard element spellings.
DEFAULT_STANDARD_ELEMENTS_PATH: Final[Path] = (
    Path(__file__).resolve().parents[1] / "etc" / "diacritic" / "standard_elements.txt"
)


class StandardElements:
    """
    Rewrite the marks of listed prefixes and compound elements in index forms.

    An element counts only where the form writes a hyphen after it (a prefix
    entry such as ``for-``, first segment only) or around it (a compound entry
    such as ``bonde``). A form with no hyphen is never changed.

    Args:
        entries: Standard spellings; a trailing hyphen marks a prefix.

    """

    def __init__(self, entries: Iterable[str]):
        """
        Index the entries by their unmarked key.

        Args:
            entries: Standard spellings; a trailing hyphen marks a prefix.

        """
        #: Unmarked key -> standard spelling, for first-segment prefixes.
        self.prefixes: dict[str, str] = {}
        #: Unmarked key -> standard spelling, for any hyphen-bounded segment.
        self.compounds: dict[str, str] = {}
        for entry in entries:
            text = unicodedata.normalize("NFC", entry.strip())
            if text.endswith("-"):
                self.prefixes[self._key(text[:-1])] = text[:-1]
            elif text:
                self.compounds[self._key(text)] = text

    @staticmethod
    def _key(text: str) -> str:
        """
        Drop case, diacritics and eth/thorn.

        Args:
            text: One hyphen segment.

        Returns:
            Lowercase text without combining marks, with ``ð`` as ``þ``.

        """
        decomposed = unicodedata.normalize("NFD", text.lower())
        stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
        return stripped.replace("ð", "þ")

    @classmethod
    def load(cls, path: Path = DEFAULT_STANDARD_ELEMENTS_PATH) -> StandardElements:
        """
        Read a standard-element file.

        Args:
            path: File with one entry per line; blank lines and ``#`` lines skipped.

        Returns:
            The loaded elements.

        """
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        return cls(
            line for line in lines if line.strip() and not line.lstrip().startswith("#")
        )

    def standardize(self, form: str) -> str:
        """
        Replace the marks of listed elements in an index form.

        Args:
            form: An index display form.

        Returns:
            The form with listed elements spelled as their standard form.

        """
        segments = form.split("-")
        if len(segments) < 2:  # noqa: PLR2004
            return form
        out: list[str] = []
        for position, segment in enumerate(segments):
            key = self._key(segment)
            standard = self.compounds.get(key)
            if position == 0:
                standard = self.prefixes.get(key, standard)
            out.append(segment if standard is None else standard)
        return "-".join(out)
```

(If ruff objects to the `noqa`, use a named constant `MIN_SEGMENTS: Final = 2` with a `#:` comment instead, matching how `BT_SPLIT_PART_COUNT` is done in `markup.py`.)

- [ ] **Step 4: Wire it into `markup.py`**

1. `from wyrdcraeft.services.standard_elements import StandardElements` (match the module's import style).
2. `DiacriticTransfer.same_marks(cls, forms, elements: StandardElements | None = None)`: when `elements` is given, build the pattern set from `elements.standardize(form)`. Update the docstring (`Args: elements:` "Standard element list applied to each form first, or ``None``").
3. `MacronApplicator.__init__(self, index_path=DEFAULT_MACRON_INDEX_PATH, *, standard_elements: StandardElements | None = None)`; add the `Keyword Args:` docstring entry and `#: Standard element spellings applied to reference forms.` `self.standard_elements = standard_elements or StandardElements.load()`.
4. Add:

```python
    def _standardized_options(self, normalized: str) -> list[str]:
        """
        Return an ambiguous key's options with standard elements applied.

        Args:
            normalized: Normalized key, present in ``index.ambiguous``.

        Returns:
            The options, in index order, each passed through
            :meth:`StandardElements.standardize`.

        """
        return [
            self.standard_elements.standardize(option)
            for option in self.index.ambiguous[normalized]
        ]
```

5. `_collapsed_form`: `options = self._standardized_options(normalized)`; `same_marks(options)` (already standardized, no `elements` argument); return `max(options, key=DiacriticTransfer.diphthong_count)`.
6. In `apply`, standardize a unique form before the transfer: after the ambiguity block and the `marked is None` return, add `marked = self.standard_elements.standardize(marked)`. (A collapsed form is already standardized; applying it twice is harmless.) Keep `apply` ≤ 60 lines: if it grows past the limit, move the `transfer` tail (debug logs, unaligned handling) into `_transfer_token(word, marked, line_number, word_number)` returning the same 4-tuple.
7. Docstring of `apply`: note standardization.

In `wyrdcraeft/cli/diacritic_disambiguate.py`: `elements = StandardElements.load()` before building `target_keys`, and pass `elements` as the second argument to `DiacriticTransfer.same_marks(...)`. Update the skip message to "...differ only in hyphens, case, eth/thorn, diphthong marking or standard prefixes."  (Update the three existing queue tests if they assert the old wording exactly: they use `startswith("Skipped 1 entries")`, so they should not need it.)

- [ ] **Step 5: Run to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_standard_elements.py tests/test_markup.py tests/test_cli_diacritic_disambiguate.py -q`
Expected: all PASS. Then the full suite: `.venv/bin/python -m pytest -q` (all green; any pre-existing test whose assertion encoded an unstandardized unique form must be updated and ledgered as a ruling).

- [ ] **Step 6: Real-index measurement and docs**

Run, and record the numbers in the ADR notes (Task 4):

```bash
.venv/bin/python - <<'E'
import json
from wyrdcraeft.services.markup import DiacriticTransfer
from wyrdcraeft.services.standard_elements import StandardElements
from wyrdcraeft.services.markup import DEFAULT_MACRON_INDEX_PATH as P
d = json.loads(P.read_text(encoding="utf-8"))
done = set(d["ambiguous_completed"]); el = StandardElements.load()
todo = [k for k in d["ambiguous"] if k not in done]
print(len(todo), sum(DiacriticTransfer.same_marks(d["ambiguous"][k]) for k in todo),
      sum(DiacriticTransfer.same_marks(d["ambiguous"][k], el) for k in todo))
E
```

Expected: `889 143 N` with N well above 143 (ADR estimate: 166 keys differ only before a BT hyphen, 83 of them editorial pairs, so roughly 143 + 83 minus overlap). If N − 143 is below ~50 or above ~110, stop and investigate before continuing (ledger a ruling).

Docs: describe standard elements in the two command `.rst` files and `docs/context/diacritic.md` (what is listed, hyphen evidence, "source keeps its own", where the file lives and that it is hand-edited); add `CONTEXT.md` glossary term "standard element".

- [ ] **Step 7: Quality gate and commit**

Run `ruff check` and `.venv/bin/mypy` on the touched Python files, `make napoleon-gate` (94), then:

```bash
git add wyrdcraeft/services/standard_elements.py wyrdcraeft/etc/diacritic/standard_elements.txt wyrdcraeft/services/markup.py wyrdcraeft/cli/diacritic_disambiguate.py tests/test_standard_elements.py tests/test_markup.py tests/test_cli_diacritic_disambiguate.py doc/source/overview/command_convert_mark_diacritics.rst doc/source/overview/command_diacritic_disambiguate.rst docs/context/diacritic.md CONTEXT.md
git commit -m "feat: mark-diacritics standardizes prefix and compound-element marks"
```

---

### Task 3: Ambiguity policy and visible guesses (ADR 0019 decisions 4, 5, 6)

**Files:**
- Modify: `wyrdcraeft/models/diacritics.py` (`AmbiguityPolicy`, `MacronAmbiguity.applied_form`, `.policy`)
- Modify: `wyrdcraeft/services/markup.py` (`DiacriticTransfer.union_form`, `.differs_only_before_hyphen`; `MacronApplicator.policy`, `_policy_form`, `apply`)
- Modify: `wyrdcraeft/cli/source.py` (`--ambiguity-policy`, summary line)
- Modify docs: `doc/source/overview/command_convert_mark_diacritics.rst`, `docs/context/diacritic.md`, `CONTEXT.md` (term "ambiguity policy")
- Test: `tests/test_markup.py`, `tests/test_cli_mark_diacritics.py`

**Interfaces:**
- Consumes: Task 2's `_standardized_options`, `standard_elements`, and the collapse path in `apply`.
- Produces: `AmbiguityPolicy = Literal["auto", "leave", "union"]` in `wyrdcraeft.models.diacritics`; `MacronAmbiguity.applied_form: str | None = None`; `MacronAmbiguity.policy: Literal["auto", "union"] | None = None`; `MacronApplicator(index_path=..., *, standard_elements=None, policy: AmbiguityPolicy = "leave")`; `DiacriticTransfer.union_form(forms: Iterable[str]) -> str | None`; `DiacriticTransfer.differs_only_before_hyphen(forms: Iterable[str]) -> bool`.

Behavior (decision 4), applied to an ambiguous key that did not collapse and is not completed:
- `leave`: report, token unchanged (today).
- `union`: apply the union of the options' marks, except letters where options conflict.
- `auto`: apply the union only when some option has a hyphen or the key has 8+ letters, and not when the marks differ only before a BT hyphen (`an-`/`ān-`, `ge-an`/`gēan`, other first elements). Otherwise report, token unchanged.
- A guessed token still gets a row, with `applied_form` (the token as written) and `policy`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_markup.py`:

```python
@pytest.mark.parametrize(
    ("forms", "expected"),
    [
        (["ac", "āc"], "āc"),
        (["lufigende", "lūfigende"], "lūfigende"),
        # macron vs breve on one letter conflict: no mark on that letter
        (["lŭfigende", "lūfigende", "lufigende"], "lufigende"),
        # dot-above does not conflict with a macron
        (["ġē", "ge", "gē"], "ġē"),
        # letters that cannot be lined up: no union
        (["ac", "acc"], None),
    ],
)
def test_union_form(forms: list[str], expected: str | None):
    assert DiacriticTransfer.union_form(forms) == expected


@pytest.mark.parametrize(
    ("forms", "expected"),
    [
        (["weg-fara", "wēg-fara"], True),
        (["an-weald", "ānweald"], True),
        (["ge-an", "gēan"], True),
        (["gold-hord", "gold-hōrd"], False),
        (["ac", "āc"], False),
        (["ac", "ac"], False),
    ],
)
def test_differs_only_before_hyphen(forms: list[str], expected: bool):
    assert DiacriticTransfer.differs_only_before_hyphen(forms) is expected


def _policy_index(tmp_path: Path, completed: list[str] | None = None) -> Path:
    index_path = tmp_path / "index.json"
    _write_index(
        index_path,
        unique={},
        ambiguous={
            "ac": ["ac", "āc"],
            "wundorlic": ["wundorlic", "wundōrlic"],
            "goldhord": ["gold-hord", "gold-hōrd"],
            "wegfara": ["weg-fara", "wēg-fara"],
            "gean": ["ge-an", "gēan"],
        },
        ambiguous_completed=completed,
    )
    return index_path


@pytest.mark.parametrize(
    ("policy", "word", "written", "guessed"),
    [
        ("leave", "ac", "ac", None),
        ("leave", "goldhord", "goldhord", None),
        ("auto", "ac", "ac", None),  # short, no hyphen
        ("auto", "wundorlic", "wundōrlic", "auto"),  # 8+ letters
        ("auto", "goldhord", "goldhōrd", "auto"),  # hyphenated
        ("auto", "wegfara", "wegfara", None),  # differs only before the hyphen
        ("auto", "gean", "gean", None),  # ge-an / gēan stay apart (Review Focus)
        ("union", "ac", "āc", "union"),
        ("union", "wegfara", "wēgfara", "union"),
    ],
)
def test_apply_policy(
    tmp_path: Path, policy: str, word: str, written: str, guessed: str | None
):
    applicator = MacronApplicator(_policy_index(tmp_path), policy=policy)

    transformed, ambiguity, is_unknown, unaligned = applicator.apply(word, 1, 1)

    assert transformed == written
    assert ambiguity is not None  # guessed tokens stay in the report (decision 6)
    assert ambiguity.policy == guessed
    assert ambiguity.applied_form == (transformed if guessed else None)
    assert not is_unknown
    assert unaligned is None


def test_apply_policy_never_touches_a_completed_key(tmp_path: Path):
    applicator = MacronApplicator(
        _policy_index(tmp_path, completed=["ac"]), policy="union"
    )

    transformed, ambiguity, _, _ = applicator.apply("ac", 1, 1)

    assert transformed == "ac"
    assert ambiguity is not None
    assert ambiguity.policy is None


def test_apply_union_keeps_decomposed_source_letters(tmp_path: Path):
    applicator = MacronApplicator(_policy_index(tmp_path), policy="union")
    source = unicodedata.normalize("NFD", "wundorlic")

    transformed, _, _, _ = applicator.apply(source, 1, 1)

    assert unicodedata.normalize("NFD", transformed).replace("̄", "") == source


def test_apply_union_with_unalignable_options_leaves_token_reported(tmp_path: Path):
    index_path = tmp_path / "index.json"
    # Hand-edited bad data: same key, different letter counts.
    _write_index(index_path, unique={}, ambiguous={"acc": ["ac", "ācc"]})

    transformed, ambiguity, _, _ = MacronApplicator(index_path, policy="union").apply(
        "acc", 1, 1
    )

    assert transformed == "acc"
    assert ambiguity is not None
    assert ambiguity.policy is None


def test_apply_policy_applies_to_a_key_that_is_also_unique(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(index_path, unique={"ac": "ac"}, ambiguous={"ac": ["ac", "āc"]})

    transformed, ambiguity, _, _ = MacronApplicator(index_path, policy="union").apply(
        "ac", 1, 1
    )

    assert transformed == "āc"
    assert ambiguity is not None
    assert ambiguity.policy == "union"


def test_restorer_reports_guessed_tokens_with_policy(tmp_path: Path):
    restorer = DiacriticRestorer(
        macron_applicator=MacronApplicator(_policy_index(tmp_path), policy="union")
    )

    result = restorer.restore_text("ac goldhord\n")

    assert result.marked_text == "āc goldhōrd\n"
    assert [(a.word, a.applied_form, a.policy) for a in result.ambiguities] == [
        ("ac", "āc", "union"),
        ("goldhord", "goldhōrd", "union"),
    ]
```

(`DiacriticRestorer` and `unicodedata` are already imported in `tests/test_markup.py`; add `DiacriticRestorer` only if it is not.)

Append to `tests/test_cli_mark_diacritics.py`:

```python
@patch("wyrdcraeft.cli.source.MacronApplicator")
@patch("wyrdcraeft.cli.source.DiacriticRestorer")
def test_source_mark_diacritics_passes_ambiguity_policy(
    mock_restorer_cls, mock_applicator_cls, runner, temp_dir
):
    source_file = temp_dir / "source.txt"
    source_file.write_text("raw", encoding="utf-8")
    mock_restorer_cls.return_value.restore_text.return_value = (
        DiacriticRestorationResult(marked_text="raw")
    )

    default = runner.invoke(cli, ["source", "mark-diacritics", str(source_file)])
    chosen = runner.invoke(
        cli,
        ["source", "mark-diacritics", str(source_file), "--ambiguity-policy", "union"],
    )
    bad = runner.invoke(
        cli,
        ["source", "mark-diacritics", str(source_file), "--ambiguity-policy", "maybe"],
    )

    assert default.exit_code == 0, default.output
    assert chosen.exit_code == 0, chosen.output
    policies = [c.kwargs["policy"] for c in mock_applicator_cls.call_args_list]
    assert policies == ["auto", "union"]
    assert bad.exit_code == 2
```

```python
@patch("wyrdcraeft.cli.source.MacronApplicator")
@patch("wyrdcraeft.cli.source.DiacriticRestorer")
def test_source_mark_diacritics_counts_guessed_tokens(
    mock_restorer_cls, mock_applicator_cls, runner, temp_dir, monkeypatch
):
    import wyrdcraeft.cli.source as source_module

    source_file = temp_dir / "source.txt"
    source_file.write_text("ac", encoding="utf-8")
    guessed = MacronAmbiguity(
        line_number=1,
        word_number=1,
        word="ac",
        options=[AmbiguityOption(form="ac"), AmbiguityOption(form="āc")],
        applied_form="āc",
        policy="union",
    )
    mock_restorer_cls.return_value.restore_text.return_value = (
        DiacriticRestorationResult(marked_text="āc", ambiguities=[guessed])
    )
    # print_info writes to a stderr console CliRunner does not capture.
    messages: list[str] = []
    monkeypatch.setattr(source_module, "print_info", messages.append)

    result = runner.invoke(cli, ["source", "mark-diacritics", str(source_file)])

    assert result.exit_code == 0, result.output
    assert any("Guessed: 1" in m for m in messages)
```

Check the command group path used by the existing tests in that file (`["source", ...]` vs `["reading", ...]`) and copy it exactly.

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_markup.py tests/test_cli_mark_diacritics.py -q`
Expected: FAIL / ERROR: `union_form` and `differs_only_before_hyphen` missing, `MacronApplicator()` got an unexpected keyword `policy`, no `--ambiguity-policy` option.

- [ ] **Step 3: Models**

In `wyrdcraeft/models/diacritics.py` add, near `POSCodeLiteral`:

```python
#: How ``mark-diacritics`` treats ambiguous keys that do not collapse (ADR 0019).
AmbiguityPolicy = Literal["auto", "leave", "union"]
```

and on `MacronAmbiguity`:

```python
    #: Form written to the output when a policy resolved this token, else None.
    applied_form: str | None = None
    #: Policy that wrote ``applied_form``, else None (token left unchanged).
    policy: Literal["auto", "union"] | None = None
```

Before moving on, `graphify query "MacronAmbiguity"` / grep for code that parses `.anomalies` JSON back into `MacronAmbiguity`; new optional fields keep those readers working, but confirm and note it in the ledger.

- [ ] **Step 4: `DiacriticTransfer` helpers**

Add to `DiacriticTransfer` (after `same_marks`). Module global near the other constants, with a `#:` comment: `EXCLUSIVE_MARKS: Final[frozenset[str]] = frozenset({"̄", "̆", "̈"})` (macron, breve, diaeresis).

```python
    @classmethod
    def union_form(cls, forms: Iterable[str]) -> str | None:
        """
        Combine the marks of several forms of one word.

        A letter gets every mark any form puts on it, unless the forms put two
        of macron, breve and diaeresis on it, in which case it gets none.

        Args:
            forms: Index display forms for one key.

        Returns:
            A hyphen-free form carrying the union, or ``None`` when the forms
            do not have the same number of letters.

        """
        patterns = [cls.mark_pattern(form) for form in forms]
        if not patterns or len({len(p) for p in patterns}) != 1:
            return None
        out: list[str] = []
        for column in zip(*patterns, strict=True):
            marks: frozenset[str] = frozenset().union(*(m for _, m in column))
            if len(marks & EXCLUSIVE_MARKS) > 1:
                marks = frozenset()
            out.append(
                unicodedata.normalize("NFC", column[0][0] + "".join(sorted(marks)))
            )
        return "".join(out)

    @classmethod
    def differs_only_before_hyphen(cls, forms: Iterable[str]) -> bool:
        """
        Tell whether every mark difference sits before a hyphen of some form.

        Such a difference is on a prefix or first compound element
        (``an-weald``/``ānweald``), which may be a real lexical distinction.

        Args:
            forms: Index display forms for one key.

        Returns:
            ``True`` when the forms differ in marks and all differing letters
            come before the first hyphen of at least one form.

        """
        forms = list(forms)
        patterns = [cls.mark_pattern(form) for form in forms]
        if len({len(p) for p in patterns}) != 1:
            return False
        differing = [
            n
            for n, column in enumerate(zip(*patterns, strict=True))
            if len({marks for _, marks in column}) > 1
        ]
        if not differing:
            return False
        for form in forms:
            letters = cls._parse(form)
            cut = next(
                (n for n, letter in enumerate(letters) if n and not letter.joined),
                None,
            )
            if cut is not None and max(differing) < cut:
                return True
        return False
```

- [ ] **Step 5: `MacronApplicator`**

- `__init__(..., *, standard_elements=None, policy: AmbiguityPolicy = "leave")`, `#: How ambiguous keys that do not collapse are treated.` `self.policy = policy`; docstring `Keyword Args:` entry.
- Module constant: `#: Keys of at least this many letters are guessed by the auto policy.` `AUTO_MIN_KEY_LENGTH: Final[int] = 8`.
- Add:

```python
    def _policy_form(self, normalized: str) -> str | None:
        """
        Pick the form to write for an ambiguous key under the active policy.

        Args:
            normalized: Normalized key, present in ``index.ambiguous``.

        Returns:
            A hyphen-free form carrying the union of the options' marks, or
            ``None`` when the policy is ``leave``, the key is completed, the
            ``auto`` rule does not apply, or the options cannot be lined up.

        """
        if self.policy == "leave" or normalized in self.index.ambiguous_completed:
            return None
        options = self._standardized_options(normalized)
        if self.policy == "auto":
            guessable = len(normalized) >= AUTO_MIN_KEY_LENGTH or any(
                "-" in option for option in options
            )
            if not guessable or DiacriticTransfer.differs_only_before_hyphen(options):
                return None
        return DiacriticTransfer.union_form(options)
```

- In `apply`, replace the ambiguous block with this flow (keeping the method ≤ 60 lines; extract `_transfer_token` if needed):

```python
        marked = self.index.unique.get(normalized)
        guessed: Literal["auto", "union"] | None = None
        if normalized in self.index.ambiguous:
            marked = self._collapsed_form(normalized)
            if marked is None:
                marked = self._policy_form(normalized)
                if marked is None:
                    row = self._ambiguity_row(word, normalized, line_number, word_number)
                    return word, row, False, None
                guessed = "auto" if self.policy == "auto" else "union"
```

  and after the existing transfer: if `guessed` and the transfer returned `None`, return the unresolved row (`policy` and `applied_form` left `None`); if `guessed` and it succeeded:

```python
        if guessed is not None:
            row = self._ambiguity_row(word, normalized, line_number, word_number)
            row = row.model_copy(update={"applied_form": transformed, "policy": guessed})
            return transformed, row, False, None
```

  (`policy == "union"` gives `"union"`; `policy == "auto"` gives `"auto"`; `leave` never reaches here.) Standardization of the unique form from Task 2 must still run before the transfer for the non-guessed path. Update the docstring of `apply`.

- [ ] **Step 6: CLI**

In `wyrdcraeft/cli/source.py`: `from wyrdcraeft.services.markup import ... MacronApplicator` (match the existing import), add

```python
@click.option(
    "--ambiguity-policy",
    type=click.Choice(["auto", "leave", "union"]),
    default="auto",
    show_default=True,
    help=(
        "How to treat ambiguous words. auto: mark the likely ones (hyphenated or "
        "long words) and report them; leave: change nothing; union: mark every "
        "one with all the marks its options have (a guess)."
    ),
)
```

add the `ambiguity_policy: str` parameter and docstring line, and build `restorer = DiacriticRestorer(macron_applicator=MacronApplicator(policy=ambiguity_policy))`. Extend the success message with `Guessed: {n}` where `n = sum(1 for a in result.ambiguities if a.policy)`.

- [ ] **Step 7: Run to verify they pass, then the full suite**

Run: `.venv/bin/python -m pytest tests/test_markup.py tests/test_cli_mark_diacritics.py -q` then `.venv/bin/python -m pytest -q`
Expected: all PASS; if an existing CLI test fails because the real `MacronApplicator` is now built inside the command, patch it in that test (ledger a ruling).

- [ ] **Step 8: Real-index smoke, docs, gate, commit**

Run on a sample text containing `ac`, `foreberan`, `hiredmann` with `--ambiguity-policy leave|auto|union` and read the three outputs and the `.anomalies` file (guessed tokens carry `applied_form` and `policy`). Document the option and the report fields in `command_convert_mark_diacritics.rst`, `docs/context/diacritic.md` and `CONTEXT.md` (term "ambiguity policy"; note how to veto a key: edit the index file, ADR 0019 decision 6).

Run `ruff check`, `.venv/bin/mypy` on touched files, `make napoleon-gate` (94), `graphify update .`, then:

```bash
git add wyrdcraeft/models/diacritics.py wyrdcraeft/services/markup.py wyrdcraeft/cli/source.py tests/test_markup.py tests/test_cli_mark_diacritics.py doc/source/overview/command_convert_mark_diacritics.rst docs/context/diacritic.md CONTEXT.md
git commit -m "feat: mark-diacritics --ambiguity-policy auto|leave|union with visible guesses"
```

---

### Task 4: Acceptance fixture and ADR notes (ADR 0019 decision 8)

**Files:**
- Create: `scripts/diacritic/extract_ambiguity_labels.py`
- Create: `tests/fixtures/ambiguity_labels.json` (generated by the script)
- Create: `tests/test_ambiguity_policy_acceptance.py`
- Modify: `docs/adr/0019-ambiguity-is-judged-on-marks-and-resolved-by-policy.md`

**Interfaces:**
- Consumes: Task 3's `MacronApplicator(index_path, policy="auto")` and `MacronAmbiguity.policy`; Task 2's standardization (the measurement includes it).
- Produces: the labeled fixture, a regression floor for the `auto` rule, and the final ADR notes.

Labeling rule (stated so it can be re-run): walk the index file's git history; a key is **`same_word`** if it was ambiguous and not completed in one revision and a later revision has it only in `unique` with a form whose letter count equals its options' (the user resolved it to one word); **`homograph`** if it was ambiguous and not completed and a later revision has it in `ambiguous_completed` and still ambiguous (the user kept two words). The fixture stores the options as they were then. A prototype of this rule on the current history found 78 homographs and 136 same-word keys that keep their letter count (190 before that filter); the ADR's 86/77 were hand counts, so the pinned numbers below are the script's.

- [ ] **Step 1: Write the extraction script**

`scripts/diacritic/extract_ambiguity_labels.py`:

```python
"""Recover the user's ambiguity decisions from the macron index's git history.

Usage: python scripts/diacritic/extract_ambiguity_labels.py OUTPUT.json
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from wyrdcraeft.services.markup import DiacriticTransfer

INDEX = "wyrdcraeft/etc/diacritic/oe_bt_macron_index.json"


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True
    ).stdout


def load(sha: str) -> dict:
    return json.loads(git("show", f"{sha}:{INDEX}"))


def main(output: Path) -> None:
    shas = git("log", "--follow", "--format=%H", "--reverse", "--", INDEX).split()
    labels: dict[str, dict] = {}
    prev = load(shas[0])
    for sha in shas[1:]:
        cur = load(sha)
        done_prev = set(prev.get("ambiguous_completed", []))
        done_cur = set(cur.get("ambiguous_completed", []))
        for key, options in prev["ambiguous"].items():
            if key in done_prev or key in labels:
                continue
            chosen = cur["unique"].get(key)
            if key in done_cur and key in cur["ambiguous"]:
                labels[key] = {"options": options, "label": "homograph"}
            elif (
                chosen is not None
                and key not in cur["ambiguous"]
                and len(DiacriticTransfer.mark_pattern(chosen))
                == len(DiacriticTransfer.mark_pattern(options[0]))
            ):
                labels[key] = {"options": options, "label": "same_word"}
        prev = cur
    counts = {
        name: sum(v["label"] == name for v in labels.values())
        for name in ("same_word", "homograph")
    }
    payload = {"meta": {"source": INDEX, "revisions": len(shas), **counts}, "labels": labels}
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True),
        encoding="utf-8",
    )
    print(payload["meta"])


if __name__ == "__main__":
    main(Path(sys.argv[1]))
```

- [ ] **Step 2: Generate the fixture**

Run: `.venv/bin/python scripts/diacritic/extract_ambiguity_labels.py tests/fixtures/ambiguity_labels.json`
Expected: prints `{'source': ..., 'revisions': 6, 'same_word': ~136, 'homograph': ~78}` (within 10% of those; if far off, stop and investigate, ledger a ruling). Check `ls tests/fixtures` exists first; create the directory if not.

- [ ] **Step 3: Write the acceptance test (RED against a deliberately wrong floor first)**

`tests/test_ambiguity_policy_acceptance.py`:

```python
"""Measure the ``auto`` ambiguity policy against the user's past decisions.

The labels are the user's own resolutions recovered from the index's git history
(ADR 0019 decision 8; scripts/diacritic/extract_ambiguity_labels.py). The floors
below are the measured values; tighten them when the rule improves and re-run the
script when more keys have been curated.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from wyrdcraeft.services.markup import MacronApplicator

FIXTURE = Path(__file__).parent / "fixtures" / "ambiguity_labels.json"

#: Most homograph keys the ``auto`` policy may wrongly mark (measured).
MAX_WRONGLY_MARKED = 0
#: Fewest same-word keys the ``auto`` policy must mark (measured).
MIN_CORRECTLY_MARKED = 0


@pytest.fixture(scope="module")
def marked_by_label(tmp_path_factory: pytest.TempPathFactory) -> dict[str, list[str]]:
    labels = json.loads(FIXTURE.read_text(encoding="utf-8"))["labels"]
    index_path = tmp_path_factory.mktemp("labels") / "index.json"
    index_path.write_text(
        json.dumps(
            {
                "unique": {},
                "ambiguous": {k: v["options"] for k, v in labels.items()},
                "ambiguous_completed": [],
                "ambiguous_metadata": {},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    applicator = MacronApplicator(index_path, policy="auto")
    marked: dict[str, list[str]] = {"same_word": [], "homograph": []}
    for key, entry in labels.items():
        transformed, _, _, _ = applicator.apply(key, 1, 1)
        if transformed != key:
            marked[entry["label"]].append(key)
    return marked


def test_auto_policy_rarely_marks_a_homograph(marked_by_label):
    assert len(marked_by_label["homograph"]) <= MAX_WRONGLY_MARKED, sorted(
        marked_by_label["homograph"]
    )


def test_auto_policy_still_covers_same_word_keys(marked_by_label):
    assert len(marked_by_label["same_word"]) >= MIN_CORRECTLY_MARKED
```

- [ ] **Step 4: Measure and pin**

Run: `.venv/bin/python -m pytest tests/test_ambiguity_policy_acceptance.py -v`
Expected: `test_auto_policy_rarely_marks_a_homograph` FAILS and prints the wrongly marked keys (RED proves the test can fail). Read the numbers, then run:

```bash
.venv/bin/python -m pytest tests/test_ambiguity_policy_acceptance.py -v --tb=line 2>&1 | tail -5
```

Set `MAX_WRONGLY_MARKED` to the measured homograph count and `MIN_CORRECTLY_MARKED` to the measured same-word count (read them by temporarily printing `len(...)` in the fixture, then remove the print). Re-run: both PASS. Ledger the two numbers and the resulting precision (`correct / (correct + wrong)`); the ADR prints about 64% on its own sample, so a precision far from that is a finding to rule on, not to hide.

- [ ] **Step 5: ADR 0019 notes**

In `docs/adr/0019-...md`: update the intro ("Decisions 2 to 8 are implemented"), resolve the Open question ("`wyrdcraeft/etc/diacritic/standard_elements.txt`, hand-edited, no CLI"), and extend "Implementation notes" with: the standard-element file and loader; the per-form standardization; the collapse form chosen by diphthong count; `union_form` conflict rule (two of macron/breve/diaeresis); the `leave` service default versus `auto` CLI default; guessed keys staying in the `diacritic-disambiguate` queue; the real-index numbers from Task 2 Step 6 and the measured fixture result from Step 4; the deferred-minor fixes. Leave `status: proposed`.

- [ ] **Step 6: Full verification and commit**

Run `.venv/bin/python -m pytest -q` (all green), `ruff check` on `scripts/diacritic/extract_ambiguity_labels.py` and the new test, `make napoleon-gate` (94), `graphify update .`, then:

```bash
git add scripts/diacritic tests/fixtures/ambiguity_labels.json tests/test_ambiguity_policy_acceptance.py docs/adr/0019-ambiguity-is-judged-on-marks-and-resolved-by-policy.md
git commit -m "test: acceptance fixture for the auto ambiguity policy; ADR 0019 notes"
```

(If `scripts/diacritic/` needs an `__init__.py` to match `scripts/morphology`, add one; check first.)

---

### Task 5: Fixes for deferred review minors 1 to 5

**Files:**
- Modify: `wyrdcraeft/services/standard_elements.py` (`__init__`, `load`; new `_add`, `LOGGER`)
- Modify: `wyrdcraeft/etc/diacritic/standard_elements.txt` (header comment)
- Modify: `wyrdcraeft/services/markup.py` (`MacronApplicator._transfer_token`, class docstring)
- Modify: `doc/source/overview/command_convert_mark_diacritics.rst` (the "Ambiguity policy" section), `docs/context/diacritic.md` (one line on inline comments)
- Test: `tests/test_markup.py`, `tests/test_standard_elements.py`

**Interfaces:**
- Consumes: Task 2's `StandardElements`, Task 3's `_transfer_token` and `apply` 4-tuple.
- Produces: no new public names. Behavior changes: `apply` returns the ambiguity row **and** the unaligned index form for a guess it cannot align; `StandardElements.load` of a missing file returns an empty list and logs a warning; `StandardElements` logs a warning for a conflicting duplicate; `load` strips `#` inline comments.

The five fixes (numbers match the review):

1. A guess whose union form cannot be transferred (source letters differ from the options, i.e. a hand-edited bad index) returns the plain ambiguity row but dropped the unaligned diagnostic that a non-guessed unaligned key gets. Return both: the row and the unaligned form.
2. `standard_elements.txt` is hand-edited. A conflicting duplicate (`for-` then `fōr-`) is silently last-wins, and an inline comment (`ge-  # note`) turns the entry into a compound that never matches. Warn on a conflicting duplicate (keep last-wins) and accept inline comments.
3. A missing `standard_elements.txt` raised `FileNotFoundError`; the `c`/`g` lists log a warning and continue. Match them.
4. The `MacronApplicator` class docstring omits `standard_elements` and `policy`.
5. The `.rst` says `union` applies "everywhere" (it leaves keys whose options cannot be lined up) and that `auto` leaves keys whose marks "differ only before a hyphen" (the code means before the first hyphen of at least one option).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_markup.py`:

```python
def test_apply_guess_that_cannot_be_aligned_is_also_reported_as_unaligned(
    tmp_path: Path,
):
    index_path = tmp_path / "index.json"
    # Hand-edited bad data: the options do not spell the key.
    _write_index(index_path, unique={}, ambiguous={"ab": ["ac", "āc"]})
    applicator = MacronApplicator(index_path, policy="union")

    transformed, ambiguity, is_unknown, unaligned = applicator.apply("ab", 1, 1)

    assert transformed == "ab"
    assert ambiguity is not None
    assert ambiguity.policy is None
    assert not is_unknown
    assert unaligned == "āc"

    result = DiacriticRestorer(macron_applicator=applicator).restore_text("ab\n")
    assert [(u.word, u.index_form) for u in result.unaligned] == [("ab", "āc")]
    assert len(result.ambiguities) == 1
```

Append to `tests/test_standard_elements.py`:

```python
def test_load_accepts_inline_comments(tmp_path: Path):
    path = tmp_path / "elements.txt"
    path.write_text("ge-  # always plain\nbonde#compound\n", encoding="utf-8")

    elements = StandardElements.load(path)

    assert elements.standardize("gē-bindan") == "ge-bindan"
    assert elements.standardize("hūs-bōnde") == "hūs-bonde"


def test_conflicting_duplicate_entries_log_a_warning(caplog: pytest.LogCaptureFixture):
    with caplog.at_level("WARNING"):
        elements = StandardElements(["for-", "fōr-"])

    assert any("fōr-" in record.message for record in caplog.records)
    # The later entry wins, as documented.
    assert elements.standardize("for-beran") == "fōr-beran"


def test_identical_duplicate_entries_do_not_warn(caplog: pytest.LogCaptureFixture):
    with caplog.at_level("WARNING"):
        StandardElements(["for-", "for-"])

    assert not caplog.records


def test_missing_file_logs_a_warning_and_standardizes_nothing(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
):
    with caplog.at_level("WARNING"):
        elements = StandardElements.load(tmp_path / "missing.txt")

    assert any("missing.txt" in record.message for record in caplog.records)
    assert elements.standardize("ā-bacan") == "ā-bacan"
```

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_markup.py tests/test_standard_elements.py -q`
Expected: 4 FAIL, the rest PASS. The failures: `assert None == 'āc'` (fix 1); `FileNotFoundError` (fix 3); `assert False` on the conflicting-duplicate warning and `'gē-bindan' == 'ge-bindan'` (fix 2). `test_identical_duplicate_entries_do_not_warn` passes already (it guards against over-warning).

- [ ] **Step 3: Fix 1, in `MacronApplicator._transfer_token`**

Replace the tail that returns for a guess with an unaligned result:

```python
        if guessed is None:
            if transformed is None:
                return word, None, False, marked
            return transformed, None, False, None
        row = self._ambiguity_row(word, normalized, line_number, word_number)
        if transformed is None:
            # Report the row and why the guess could not be written.
            return word, row, False, marked
        row = row.model_copy(update={"applied_form": transformed, "policy": guessed})
        return transformed, row, False, None
```

Update the `Returns:` of `_transfer_token` and `apply` ("a guess that cannot be aligned returns its plain ambiguity row and the unaligned index form"). `_restore_line` already appends both a row and an unaligned entry when both are present; confirm with the restorer assertion in the test.

- [ ] **Step 4: Fixes 2 and 3, in `standard_elements.py`**

Add `import logging` and, next to `DEFAULT_STANDARD_ELEMENTS_PATH`, a module logger written the way `markup.py` writes its `LOGGER` (copy its form and `#:` comment). Replace the entry loop in `__init__` and the body of `load`:

```python
        for entry in entries:
            text = unicodedata.normalize("NFC", entry.strip())
            if text.endswith("-"):
                self._add(self.prefixes, text[:-1], text)
            elif text:
                self._add(self.compounds, text, text)

    def _add(self, table: dict[str, str], spelling: str, entry: str) -> None:
        """
        Record one standard spelling, warning when it replaces a different one.

        Side Effects:
            Logs a warning on a conflicting duplicate; the later entry wins.

        Args:
            table: ``prefixes`` or ``compounds``.
            spelling: The standard spelling without a trailing hyphen.
            entry: The entry as written, for the warning.

        """
        key = self._key(spelling)
        if table.get(key, spelling) != spelling:
            LOGGER.warning(
                "Standard element %r conflicts with %r; using the later one",
                entry,
                table[key],
            )
        table[key] = spelling
```

```python
        if not path.exists():
            LOGGER.warning("Standard element list missing: %s", path)
            return cls([])
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        entries = (line.split("#", maxsplit=1)[0] for line in lines)
        return cls(entry for entry in entries if entry.strip())
```

Update the `load` docstring (`#` starts a comment anywhere on a line; a missing file logs a warning and gives an empty list) and the header of `wyrdcraeft/etc/diacritic/standard_elements.txt` ("A `#` starts a comment, also after an entry."). Add one line to `docs/context/diacritic.md` next to the standard-element note: inline `#` comments are allowed, a conflicting duplicate logs a warning and the later entry wins.

- [ ] **Step 5: Fixes 4 and 5, docstring and docs**

`MacronApplicator` class docstring: add under `Args:` `index_path`, then a `Keyword Args:` block for `standard_elements` ("Standard element spellings; the packaged list when omitted.") and `policy` ("How ambiguous keys that do not collapse are treated: ``leave`` (default), ``auto`` or ``union``.").

`command_convert_mark_diacritics.rst`, "Ambiguity policy": change the `union` bullet to "apply the union of the marks to every key it can; a key whose options cannot be lined up letter for letter stays reported and unchanged", and the `auto` exception to "when the marks differ only before the first hyphen of at least one option".

- [ ] **Step 6: Run to verify they pass, then the full suite**

Run: `.venv/bin/python -m pytest tests/test_markup.py tests/test_standard_elements.py tests/test_cli_mark_diacritics.py -q` then `.venv/bin/python -m pytest -q`
Expected: all PASS (1252 before this task plus 5 new).

- [ ] **Step 7: Quality gate and commit**

`ruff check` and `.venv/bin/mypy` on the touched Python files, `make napoleon-gate` (94), `graphify update .`, then:

```bash
git add wyrdcraeft/services/standard_elements.py wyrdcraeft/etc/diacritic/standard_elements.txt wyrdcraeft/services/markup.py tests/test_markup.py tests/test_standard_elements.py doc/source/overview/command_convert_mark_diacritics.rst docs/context/diacritic.md
git commit -m "fix: guessed-but-unalignable tokens stay unaligned; harden the standard-element file; doc wording"
```

**Still deferred after this task (not in scope):** the acceptance test counts collapses through standard elements as `auto` hits (so 74% precision is slightly generous and the ADR wording claims a little more than is measured); `auto`'s "hyphenated" check tests ASCII `-` only, not en/em dashes (no effect on the packaged index).
