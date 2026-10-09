# BT Variant Importer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A repeatable `wyrdcraeft diacritic import-variants` command reads `oe_bt.txt`, filters junk, adds each real BT variant spelling as its own entry in the macron index's `unique` list, and writes a review report for everything it will not decide itself. Dry run by default.

**Architecture:** `BTLineParser.raw_variants` exposes the raw (un-normalized) headword and variants. `BTVariantFilter` rejects junk and applies the similarity gate. `BTVariantImporter` reads the source, screens and classifies each variant against the index (new key, same, fewer marks, collision) and returns a `VariantImportReport`; `apply` adds only the new keys. `DiacriticTransfer.mark_relation` compares marks. The CLI command in `cli/diacritic.py` writes the report and, with `--apply`, the index through the existing atomic writer.

**Tech Stack:** Python, pydantic models, click `CliRunner`, pytest.

**Spec:** [ADR 0017](../../adr/0017-diacritic-cli-imports-bt-variants.md) decisions 1 to 6 (decisions 4 and 6 were decided in this session and are written into the ADR), plus ADR 0015/0016 (additive, curated index), ADR 0018 (a stored form must normalize to its key) and ADR 0019/0020 (`mark_pattern`, standard elements).

## Scope: what this plan does not do

- It does **not** run `--apply` on the packaged index. That adds about 2,440 keys to a 1.2 MB curated file; the user runs it and reviews the diff. Task 4 only runs a dry run and records the numbers.
- No headword link in the index and no `--variant-of` flag (ADR 0017 decision 5).
- No second-option, upgrade or auto-merge behavior for collisions: the policy is report only (decision 6).
- Inflected forms and English words below the similarity gate are reported, never imported.

## Global Constraints

- **Dry run by default**; `--apply` is the only thing that writes the index, through `_write_macron_index_payload` (atomic).
- **Never change an existing key.** Only keys absent from both `unique` and `ambiguous` are added. A key in `ambiguous_completed` is never touched or proposed.
- **A variant's spelling is what BT prints, lowercased.** Marks are never copied from the headword; BT capitalization is not kept. The stored form must normalize to its key (`normalize_old_english(form) == key`).
- **Junk filter, in this order, first match counted:** all-caps token (2+ letters, `str.isupper`), truncated fragment (`-\w$` after NFC), stoplist entry, key listed under 3 or more different headwords. Then the **similarity gate**: edit distance between the normalized variant key and the normalized headword key is at most `max(2, len(headword key) // 3)`. Variants that fail the gate and whose key is not in the index go to the report's `below_gate` list.
- **Mark comparison** uses `DiacriticTransfer.mark_pattern` after standard elements (hyphens, case, eth/thorn never count).
- Methods ≤ 60 lines; Napoleon docstrings (`Keyword Args:` for kw-only); `#:` comments on attributes and module globals. `make napoleon-gate` stays at the 94 baseline; `mypy` keeps its one pre-existing error at `wyrdcraeft/cli/cli.py:107`; ruff clean on touched files.
- Project structure: models in `wyrdcraeft/models/`, business logic in `wyrdcraeft/services/`, CLI/display only in `wyrdcraeft/cli/`.
- Do not stage `doc/source/changelog.rst`, `uv.lock`, `wyrdcraeft/etc/dictionary/oe_bt.json` or `graphify-out/`. Do not `ruff format` the whole `wyrdcraeft/cli` directory; name files.
- Before editing, `graphify query` the symbol; after code edits `graphify update .`.
- Test command: `.venv/bin/python -m pytest`. Baseline before this plan: 1252 passed (1257 once Task 5 of the previous plan is done).

## Rulings to confirm (made while planning)

- **A stoplist file is kept next to the frequency rule.** Frequency needs the whole corpus; on a small fixture or a trimmed source the sigla (`v`, `Cf`, `Ps`) would otherwise get through. Initial entries are Roman numerals and the sigla measured on the real source. Cost if wrong: one small data file.
- **No "affix" reject rule** (`-ness`, `un-`): a measurement of the real source found none, so it would be dead code.
- **Edit distance is a 10-line stdlib dynamic-programming function, not `rapidfuzz`.** AGENTS.md asks to weigh a package: `rapidfuzz` is well maintained, but this runs once over about 20,000 short strings, so a new dependency buys nothing. Cost if wrong: swap one function.
- **`below_gate` lists only variants whose key is not already in the index.** An existing entry always wins, so a below-gate variant of an existing key is noise.
- **Variants are de-duplicated by `(key, lowercase spelling)` after screening**, and the counts are rows after that. Rejects are counted per row before de-duplication.
- **A variant with fewer marks than every option of an ambiguous key, but equal to none, is reported as `new_pattern`.** Cost if wrong: a rare extra review row.
- **The report file is written on every run, dry or applied.** Default path `bt-variant-import-report.json` in the current directory, never inside the package. The ADR left the name open.
- **`BTLineParser.raw_variants` duplicates about ten lines of `parse`** instead of refactoring it, because `parse` also needs the match end and distinct skip reasons. A consistency test (raw variants, normalized, equal `parse().variants`) guards drift.
- **The command keeps the ADR's working name `diacritic import-variants`.**

## Review Focus

- **Re-running `--apply` right after an apply** adds nothing (second run: 0 added, the same keys counted as same-marks) and leaves the file content identical.
- **A dry run never writes the index**, even when it would add keys.
- **A capitalized BT variant (`Tiolung`)** is stored lowercase, and every stored form normalizes to its key.
- **A key in `ambiguous_completed`** is never added to `unique`, never listed as a collision.
- **Unparseable input:** blank lines, a line with no `<B>` headword, a line with too few `@` fields, CRLF line endings and NFD (decomposed) BT text neither crash nor yield junk; a missing source or index file is a clean `ClickException`.
- **Two variants for one new key with different mark patterns** add neither (both reported); with the same pattern they add once.

---

### Task 1: Building blocks: `BTLineParser.raw_variants` and `DiacriticTransfer.mark_relation`

**Files:**
- Modify: `wyrdcraeft/services/dictionary/line_parser.py` (new public method after `parse`)
- Modify: `wyrdcraeft/services/markup.py` (`DiacriticTransfer.mark_relation`)
- Test: `tests/dictionary/test_line_parser.py`, `tests/test_markup.py`

**Interfaces:**
- Produces: `BTLineParser.raw_variants(self, line: str) -> tuple[str, tuple[str, ...]] | None`: the canonical headword as BT prints it and the un-normalized variants (bold-tag extras first, then pre-POS variants, source order, parser de-duplication and parser filters kept), or `None` for a line `parse` would skip. `DiacriticTransfer.mark_relation(existing: str, candidate: str, elements: StandardElements | None = None) -> Literal["same", "fewer", "more", "conflict"]`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/dictionary/test_line_parser.py` (keep the file's existing imports; add `BTLineParser` and `pytest` if missing):

```python
RAW_VARIANT_LINES = [
    "tilung@<B>tilung,</B> teolung, tiolung; <I>f.</I> striving.@tilung",
    "bar@<B>bār,</B> v. Cf. Ps. Rdr; <I>m.</I> a boar.@bar",
    "maegth@<B>mægþ, mægeþ;</B> <I>f.</I> maid.@maegth",
    "aa@<B>ā,</B> aa; <I>adv.</I> ever.@a",
]


@pytest.mark.parametrize(
    ("line", "headword", "variants"),
    [
        (RAW_VARIANT_LINES[0], "tilung", ("teolung", "tiolung")),
        (RAW_VARIANT_LINES[1], "bār", ("v", "Cf", "Ps", "Rdr")),
        (RAW_VARIANT_LINES[2], "mægþ", ("mægeþ",)),
        (RAW_VARIANT_LINES[3], "ā", ("aa",)),
    ],
)
def test_raw_variants_returns_unnormalized_spellings(line, headword, variants):
    assert BTLineParser().raw_variants(line) == (headword, variants)


@pytest.mark.parametrize(
    "line",
    ["", "no at signs", "a@b", "x@no bold headword here@x", "x@<B>12</B> text@x"],
)
def test_raw_variants_returns_none_for_lines_parse_skips(line):
    parser = BTLineParser()

    assert parser.raw_variants(line) is None
    assert parser.parse(1, line).raw_line is None


@pytest.mark.parametrize("line", RAW_VARIANT_LINES)
def test_raw_variants_agree_with_parse(line):
    parser = BTLineParser()
    headword, variants = parser.raw_variants(line)  # type: ignore[misc]

    assert parser.parse(1, line).variants == parser._normalize_variants(variants)
```

Append to `tests/test_markup.py`:

```python
@pytest.mark.parametrize(
    ("existing", "candidate", "expected"),
    [
        ("weg", "weg", "same"),
        ("wēg", "wēg", "same"),
        ("ǣ-ge", "ǣge", "same"),  # hyphens do not count
        ("wēg", "weg", "fewer"),
        ("weg", "wēg", "more"),
        ("wĕg", "wēg", "conflict"),  # breve against macron
        ("weg", "wēge", "conflict"),  # different letters
        ("leāst", "lēast", "same"),  # diphthong style does not count
    ],
)
def test_mark_relation(existing: str, candidate: str, expected: str):
    assert DiacriticTransfer.mark_relation(existing, candidate) == expected


def test_mark_relation_standardizes_elements_first():
    elements = StandardElements(["for-"])

    assert DiacriticTransfer.mark_relation("fōr-beran", "for-beran", elements) == "same"
    assert DiacriticTransfer.mark_relation("fōr-beran", "for-beran") == "fewer"
```

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/bin/python -m pytest tests/dictionary/test_line_parser.py tests/test_markup.py -q`
Expected: FAIL: `AttributeError: 'BTLineParser' object has no attribute 'raw_variants'` and `type object 'DiacriticTransfer' has no attribute 'mark_relation'`. The "returns None for lines parse skips" tests also fail on the missing method. If a `parse` assertion in that test fails because one of the five skip lines does not actually skip, replace that line with one that `parse` really skips and ledger it.

- [ ] **Step 3: Implement `raw_variants`**

In `line_parser.py`, inside `BTLineParser`, after `parse`:

```python
    def raw_variants(self, line: str) -> tuple[str, tuple[str, ...]] | None:
        """
        Extract the headword and its variants exactly as Bosworth-Toller prints them.

        Unlike :meth:`parse` this does not run the spelling normalizer, so BT's
        acute-to-macron and diphthong rewriting never touches the spellings.

        Args:
            line: Raw line from ``oe_bt.txt``.

        Returns:
            The canonical headword and its variants (bold-tag extras first, then
            pre-POS variants), or ``None`` when :meth:`parse` would skip the line.

        """
        split_line = self.splitter.split(line)
        if split_line is None:
            return None
        headword_match = BOLD_HEADWORD_RE.search(split_line.body)
        if headword_match is None:
            return None
        headword_forms = _split_headword_forms(headword_match.group(1))
        if headword_forms is None:
            return None
        headword_raw, bold_variants = headword_forms
        pos_fragment = self._extract_pos_fragment(split_line, headword_match.end())
        prefix_variants = self._extract_variants(
            headword_raw=headword_raw, pos_fragment=pos_fragment
        )
        return headword_raw, bold_variants + prefix_variants
```

- [ ] **Step 4: Implement `mark_relation`**

In `DiacriticTransfer`, after `same_marks`:

```python
    @classmethod
    def mark_relation(
        cls,
        existing: str,
        candidate: str,
        elements: StandardElements | None = None,
    ) -> Literal["same", "fewer", "more", "conflict"]:
        """
        Compare the marks of a candidate form with an existing form of one key.

        Hyphens, case, ``ð``/``þ`` and diphthong style do not count, and standard
        elements are applied first when ``elements`` is given.

        Args:
            existing: The form already in the index.
            candidate: The form being considered.
            elements: Standard element list, or ``None``.

        Returns:
            ``same``; ``fewer`` when every mark of the candidate is in the
            existing form; ``more`` when every mark of the existing form is in the
            candidate; else ``conflict`` (also when the letters differ).

        """
        if elements is not None:
            existing = elements.standardize(existing)
            candidate = elements.standardize(candidate)
        old = cls.mark_pattern(existing)
        new = cls.mark_pattern(candidate)
        if old == new:
            return "same"
        if [base for base, _ in old] != [base for base, _ in new]:
            return "conflict"
        old_marks = [marks for _, marks in old]
        new_marks = [marks for _, marks in new]
        if all(n <= o for n, o in zip(new_marks, old_marks, strict=True)):
            return "fewer"
        if all(o <= n for o, n in zip(old_marks, new_marks, strict=True)):
            return "more"
        return "conflict"
```

- [ ] **Step 5: Run to verify they pass; gate; commit**

Run: `.venv/bin/python -m pytest tests/dictionary/test_line_parser.py tests/test_markup.py -q` (all PASS), `ruff check` and `.venv/bin/mypy` on the touched files, `make napoleon-gate` (94), `graphify update .`, then:

```bash
git add wyrdcraeft/services/dictionary/line_parser.py wyrdcraeft/services/markup.py tests/dictionary/test_line_parser.py tests/test_markup.py
git commit -m "feat: raw BT variants from the line parser; mark_relation on DiacriticTransfer"
```

---

### Task 2: `BTVariantFilter` and the stoplist (ADR 0017 decision 4)

**Files:**
- Create: `wyrdcraeft/services/variant_filter.py`
- Create: `wyrdcraeft/etc/diacritic/bt_variant_stoplist.txt` (already packaged by `etc/diacritic/*.txt`)
- Test: `tests/test_variant_filter.py` (new)

**Interfaces:**
- Produces: `BTVariantFilter(stoplist: Iterable[str])`; `BTVariantFilter.load(path: Path = DEFAULT_VARIANT_STOPLIST_PATH) -> BTVariantFilter`; `reject_reason(self, spelling: str, headword_count: int) -> str | None` returning one of `"all_caps"`, `"fragment"`, `"stoplist"`, `"frequent"` or `None`; `within_gate(key: str, headword_key: str) -> bool` (static); `DEFAULT_VARIANT_STOPLIST_PATH`.

- [ ] **Step 1: Write the failing tests**

`tests/test_variant_filter.py`:

```python
from __future__ import annotations

import unicodedata
from typing import TYPE_CHECKING

import pytest

from wyrdcraeft.services.variant_filter import (
    DEFAULT_VARIANT_STOPLIST_PATH,
    BTVariantFilter,
)

if TYPE_CHECKING:
    from pathlib import Path

FILTER = BTVariantFilter(["v", "cf", "ps", "rdr", "ii"])


@pytest.mark.parametrize(
    ("spelling", "headword_count", "expected"),
    [
        ("II", 1, "all_caps"),
        ("UNCERTAIN", 1, "all_caps"),
        ("APPLE-SHREDS", 1, "all_caps"),
        ("on-g", 1, "fragment"),
        ("ge-ǣ", 1, "fragment"),
        (unicodedata.normalize("NFD", "ge-ǣ"), 1, "fragment"),
        ("Cf", 1, "stoplist"),
        ("Ps", 1, "stoplist"),
        ("v", 1, "stoplist"),
        ("zzz", 3, "frequent"),
        ("zzz", 2, None),
        ("tiolung", 1, None),
        ("aa", 1, None),  # a real short word (variant of ā)
        ("Æ", 1, None),  # one capital letter is not all-caps text
        ("ā-ǣlan", 1, None),  # a one-letter prefix is not a fragment
        ("Lindesīge", 1, None),
    ],
)
def test_reject_reason(spelling: str, headword_count: int, expected: str | None):
    assert FILTER.reject_reason(spelling, headword_count) == expected


@pytest.mark.parametrize(
    ("key", "headword_key", "expected"),
    [
        ("aa", "a", True),
        ("tiolung", "tilung", True),
        ("senu", "seonu", True),
        ("lindessige", "lindesse", True),
        ("with", "landbygen", False),
        ("classes", "stregdan", False),
        ("bacest", "bacan", False),  # a real inflected form: reported, not imported
        ("seotu", "seoþþan", False),
    ],
)
def test_within_gate(key: str, headword_key: str, expected: bool):
    assert BTVariantFilter.within_gate(key, headword_key) is expected


def test_load_ignores_comments_blanks_and_bom(tmp_path: Path):
    path = tmp_path / "stoplist.txt"
    path.write_text("﻿# sigla\n\nCf  # see also\nvii\n", encoding="utf-8")

    loaded = BTVariantFilter.load(path)

    assert loaded.reject_reason("cf", 1) == "stoplist"
    assert loaded.reject_reason("VII", 1) == "all_caps"
    assert loaded.reject_reason("vii", 1) == "stoplist"


def test_missing_stoplist_logs_a_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
):
    with caplog.at_level("WARNING"):
        loaded = BTVariantFilter.load(tmp_path / "missing.txt")

    assert any("missing.txt" in record.message for record in caplog.records)
    assert loaded.reject_reason("v", 1) is None


def test_packaged_stoplist_has_the_sigla_and_numerals():
    loaded = BTVariantFilter.load(DEFAULT_VARIANT_STOPLIST_PATH)

    for token in ["v", "Cf", "ii", "Ps", "Rdr", "Wrt", "Voc", "Gl", "xiv"]:
        assert loaded.reject_reason(token, 1) in {"stoplist", "all_caps"}, token
    assert loaded.reject_reason("aa", 1) is None
    assert loaded.reject_reason("tiolung", 1) is None
```

(`"Cf  # see also"` checks inline comments; entries are lowercased on load, and lookup lowercases the spelling.)

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_variant_filter.py -q`
Expected: collection ERROR `ModuleNotFoundError: wyrdcraeft.services.variant_filter`.

- [ ] **Step 3: Write the data file and the module**

`wyrdcraeft/etc/diacritic/bt_variant_stoplist.txt`:

```text
# Citation sigla and Roman numerals that Bosworth-Toller entries contain but
# that are not Old English words (ADR 0017). One entry per line, matched
# ignoring case. A # starts a comment, also after an entry. The importer also
# rejects any key listed as a variant under 3 or more headwords; this list
# catches the rest, and everything on a source too small for that rule.
i
ii
iii
iv
v
vi
vii
viii
ix
x
xi
xii
xiii
xiv
cf
ps
rdr
gl
wrt
voc
kmbl
lchdm
hpt
mk
mt
sat
bd
bt
hml
homl
angl
exon
lch
```

`wyrdcraeft/services/variant_filter.py` (write `LOGGER` the way `markup.py` does, with its `#:` comment):

```python
"""Junk filter and similarity gate for Bosworth-Toller variant spellings."""

from __future__ import annotations

import logging
import re
import unicodedata
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Iterable

#: Module logger.
LOGGER = logging.getLogger(__name__)
#: Packaged, hand-edited list of citation sigla and numerals to reject.
DEFAULT_VARIANT_STOPLIST_PATH: Final[Path] = (
    Path(__file__).resolve().parents[1] / "etc" / "diacritic" / "bt_variant_stoplist.txt"
)
#: A key listed as a variant under this many headwords is a siglum, not a word.
FREQUENT_HEADWORD_COUNT: Final[int] = 3
#: A hyphenated token ending in one letter is a truncated fragment.
FRAGMENT_RE: Final[re.Pattern[str]] = re.compile(r"-\w$")
#: Edit distance always allowed between a variant and its headword.
MIN_GATE_DISTANCE: Final[int] = 2
#: The gate also allows one edit per this many letters of the headword key.
GATE_LENGTH_DIVISOR: Final[int] = 3
#: Fewest letters for a token to count as ALL-CAPS text.
MIN_ALL_CAPS_LETTERS: Final[int] = 2


class BTVariantFilter:
    """
    Decide which parser "variants" are real spellings of their headword.

    Args:
        stoplist: Tokens to reject, matched ignoring case.

    """

    def __init__(self, stoplist: Iterable[str]):
        """
        Store the stoplist.

        Args:
            stoplist: Tokens to reject, matched ignoring case.

        """
        #: Lowercase tokens that are never imported.
        self.stoplist = frozenset(token.strip().lower() for token in stoplist)

    @classmethod
    def load(cls, path: Path = DEFAULT_VARIANT_STOPLIST_PATH) -> BTVariantFilter:
        """
        Read a stoplist file.

        A ``#`` starts a comment anywhere on a line. A missing file logs a
        warning and gives an empty stoplist.

        Args:
            path: Stoplist file, one token per line.

        Returns:
            The loaded filter.

        """
        if not path.exists():
            LOGGER.warning("Variant stoplist missing: %s", path)
            return cls([])
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        entries = (line.split("#", maxsplit=1)[0] for line in lines)
        return cls(entry for entry in entries if entry.strip())

    def reject_reason(self, spelling: str, headword_count: int) -> str | None:
        """
        Say why a variant spelling is junk, if it is.

        Args:
            spelling: The variant exactly as Bosworth-Toller prints it.
            headword_count: How many different headwords list this key as a variant.

        Returns:
            ``all_caps``, ``fragment``, ``stoplist`` or ``frequent`` (checked in
            that order), or ``None`` when the spelling passes.

        """
        text = unicodedata.normalize("NFC", spelling)
        letters = sum(1 for char in text if char.isalpha())
        if letters >= MIN_ALL_CAPS_LETTERS and text.isupper():
            return "all_caps"
        if FRAGMENT_RE.search(text):
            return "fragment"
        if text.lower() in self.stoplist:
            return "stoplist"
        if headword_count >= FREQUENT_HEADWORD_COUNT:
            return "frequent"
        return None

    @staticmethod
    def within_gate(key: str, headword_key: str) -> bool:
        """
        Tell whether a variant is a spelling of its own headword.

        Args:
            key: Normalized key of the variant.
            headword_key: Normalized key of the headword it is listed under.

        Returns:
            ``True`` when the edit distance is at most
            ``max(2, len(headword_key) // 3)``.

        """
        limit = max(MIN_GATE_DISTANCE, len(headword_key) // GATE_LENGTH_DIVISOR)
        previous = list(range(len(headword_key) + 1))
        for i, char in enumerate(key, start=1):
            current = [i]
            for j, other in enumerate(headword_key, start=1):
                current.append(
                    min(
                        previous[j] + 1,
                        current[j - 1] + 1,
                        previous[j - 1] + (char != other),
                    )
                )
            previous = current
        return previous[-1] <= limit
```

- [ ] **Step 4: Run to verify they pass; gate; commit**

Run: `.venv/bin/python -m pytest tests/test_variant_filter.py -q` (all PASS; if one `within_gate` expectation is off by the edit-distance arithmetic, recompute it by hand, fix the test and ledger a ruling: the rule, not the table, is the spec), `ruff check`, `.venv/bin/mypy`, `make napoleon-gate`, `graphify update .`, then:

```bash
git add wyrdcraeft/services/variant_filter.py wyrdcraeft/etc/diacritic/bt_variant_stoplist.txt tests/test_variant_filter.py
git commit -m "feat: BT variant junk filter, similarity gate and stoplist"
```

---

### Task 3: `BTVariantImporter` and the report models (decisions 1, 2, 3, 6)

**Files:**
- Create: `wyrdcraeft/models/variant_import.py`
- Create: `wyrdcraeft/services/variant_importer.py`
- Modify: `wyrdcraeft/models/__init__.py` (export the new models, matching how it exports `MacronIndexPayload`)
- Test: `tests/test_variant_importer.py` (new)

**Interfaces:**
- Consumes: Task 1's `BTLineParser.raw_variants` and `DiacriticTransfer.mark_relation`; Task 2's `BTVariantFilter`; `StandardElements`; `MacronIndexPayload`.
- Produces: models `VariantRow(spelling, key, headword, line_no)`, `CollisionRow(variant: VariantRow, existing: list[str], reason: Literal["more_marks", "conflicting_marks", "new_pattern"])`, `ConflictingNewKey(key, variants: list[VariantRow])`, `VariantImportReport(additions: dict[str, str], collisions, conflicting_new, below_gate: list[VariantRow], counts: dict[str, int])`. `BTVariantImporter(parser: BTLineParser | None = None, variant_filter: BTVariantFilter | None = None, standard_elements: StandardElements | None = None)`; `build_report(self, source_path: Path, payload: MacronIndexPayload) -> VariantImportReport`; `apply(self, report: VariantImportReport, payload: MacronIndexPayload) -> int` (adds `report.additions` to `payload.unique`, returns how many). Count names: `candidates`, `rejected_all_caps`, `rejected_fragment`, `rejected_stoplist`, `rejected_frequent`, `skipped_completed`, `skipped_same_marks`, `skipped_fewer_marks`, `skipped_matches_option`, `added`; absent means 0.

- [ ] **Step 1: Write the failing tests**

`tests/test_variant_importer.py`:

```python
from __future__ import annotations

import unicodedata
from typing import TYPE_CHECKING

import pytest

from wyrdcraeft.models.diacritics import MacronIndexPayload
from wyrdcraeft.services.markup import normalize_old_english
from wyrdcraeft.services.variant_filter import BTVariantFilter
from wyrdcraeft.services.variant_importer import BTVariantImporter

if TYPE_CHECKING:
    from pathlib import Path

    from wyrdcraeft.models.variant_import import VariantImportReport


def _line(headword: str, *variants: str) -> str:
    return f"{headword}@<B>{headword},</B> {', '.join(variants)}; <I>m.</I> a word.@{headword}"


def _importer() -> BTVariantImporter:
    return BTVariantImporter(
        variant_filter=BTVariantFilter(["v", "cf", "ps", "rdr"])
    )


def _report(
    tmp_path: Path,
    lines: list[str],
    *,
    unique: dict[str, str] | None = None,
    ambiguous: dict[str, list[str]] | None = None,
    completed: set[str] | None = None,
) -> VariantImportReport:
    source = tmp_path / "oe_bt.txt"
    source.write_text("\n".join(lines) + "\n", encoding="utf-8")
    payload = MacronIndexPayload(
        unique=unique or {},
        ambiguous=ambiguous or {},
        ambiguous_completed=completed or set(),
    )
    return _importer().build_report(source, payload)


def test_adds_spelling_variants_of_the_headword(tmp_path: Path):
    report = _report(tmp_path, [_line("tilung", "teolung", "tiolung")])

    assert report.additions == {"teolung": "teolung", "tiolung": "tiolung"}
    assert report.counts["added"] == 2
    assert report.collisions == []
    assert report.below_gate == []


def test_stores_what_bt_prints_lowercased_never_the_headword_marks(tmp_path: Path):
    report = _report(tmp_path, [_line("bār", "Barr")])

    # No macron is copied from the headword; capitalization is dropped.
    assert report.additions == {"barr": "barr"}


def test_every_added_form_normalizes_to_its_key(tmp_path: Path):
    report = _report(
        tmp_path,
        [_line("hīred-mann", "heord-mann", "Hīrēd-mann"), _line("tilung", "Tiolung")],
    )

    assert report.additions
    for key, form in report.additions.items():
        assert normalize_old_english(form) == key
        assert form == form.lower()


def test_rejects_junk_and_counts_it(tmp_path: Path):
    lines = [
        "bar@<B>bār,</B> v. Cf. Ps. Rdr; <I>m.</I> a boar.@bar",
        "stregdan@<B>stregdan,</B> classes, UNCERTAIN, on-g; <I>v.</I> to strew.@stregdan",
        _line("aaa", "zzz"),
        _line("bbb", "zzz"),
        _line("ccc", "zzz"),
    ]

    report = _report(tmp_path, lines)

    assert report.additions == {}
    assert report.counts["rejected_stoplist"] == 4
    assert report.counts["rejected_all_caps"] == 1
    assert report.counts["rejected_fragment"] == 1
    assert report.counts["rejected_frequent"] == 3


def test_variants_that_are_not_spellings_of_their_headword_go_to_review(
    tmp_path: Path,
):
    stregdan = (
        "stregdan@<B>stregdan,</B> classes; <I>v.</I> to strew.@stregdan"
    )

    report = _report(tmp_path, [_line("tilung", "tiolung"), stregdan])

    assert "classes" not in report.additions
    assert [(r.spelling, r.headword, r.line_no) for r in report.below_gate] == [
        ("classes", "stregdan", 2)
    ]


def test_below_gate_skips_keys_already_in_the_index(tmp_path: Path):
    stregdan = (
        "stregdan@<B>stregdan,</B> classes; <I>v.</I> to strew.@stregdan"
    )

    report = _report(tmp_path, [stregdan], unique={"classes": "classes"})

    assert report.below_gate == []


@pytest.mark.parametrize(
    ("unique", "variant", "counter", "collision_reason"),
    [
        ({"weg": "wēg"}, "wēg", "skipped_same_marks", None),
        ({"weg": "wēg"}, "weg", "skipped_fewer_marks", None),
        ({"weg": "weg"}, "wēg", None, "more_marks"),
        ({"weg": "wĕg"}, "wēg", None, "conflicting_marks"),
    ],
)
def test_collisions_with_a_unique_entry(
    tmp_path: Path,
    unique: dict[str, str],
    variant: str,
    counter: str | None,
    collision_reason: str | None,
):
    report = _report(tmp_path, [_line("wege", variant)], unique=unique)

    assert report.additions == {}
    if counter is not None:
        assert report.counts[counter] == 1
        assert report.collisions == []
    else:
        assert [c.reason for c in report.collisions] == [collision_reason]
        assert report.collisions[0].existing == list(unique.values())
        assert report.collisions[0].variant.spelling == variant


@pytest.mark.parametrize(
    ("variant", "completed", "counter", "collision_reason"),
    [
        ("wēg", set(), "skipped_matches_option", None),
        ("wĕg", set(), None, "new_pattern"),
        ("wēg", {"weg"}, "skipped_completed", None),
        ("wĕg", {"weg"}, "skipped_completed", None),
    ],
)
def test_collisions_with_an_ambiguous_key(
    tmp_path: Path,
    variant: str,
    completed: set[str],
    counter: str | None,
    collision_reason: str | None,
):
    report = _report(
        tmp_path,
        [_line("wege", variant)],
        ambiguous={"weg": ["weg", "wēg"]},
        completed=completed,
    )

    assert report.additions == {}
    if counter is not None:
        assert report.counts[counter] == 1
        assert report.collisions == []
    else:
        assert [c.reason for c in report.collisions] == [collision_reason]
        assert report.collisions[0].existing == ["weg", "wēg"]


def test_two_variants_with_different_marks_for_one_new_key_add_neither(
    tmp_path: Path,
):
    report = _report(tmp_path, [_line("wege", "weg"), _line("wēge", "wēg")])

    assert report.additions == {}
    assert [c.key for c in report.conflicting_new] == ["weg"]
    assert sorted(v.spelling for v in report.conflicting_new[0].variants) == [
        "weg",
        "wēg",
    ]


def test_two_variants_with_the_same_marks_add_once(tmp_path: Path):
    report = _report(tmp_path, [_line("wege", "weg"), _line("wegen", "Weg")])

    assert report.additions == {"weg": "weg"}
    assert report.conflicting_new == []


def test_hyphen_and_case_differences_do_not_conflict(tmp_path: Path):
    report = _report(tmp_path, [_line("ǣwege", "ǣ-weg"), _line("ǣwegen", "Ǣweg")])

    # Same marks once hyphens and case are ignored: one entry, first spelling kept.
    assert report.conflicting_new == []
    assert report.additions == {"æweg": "ǣ-weg"}


def test_blank_unparseable_crlf_and_nfd_lines_do_not_crash(tmp_path: Path):
    source = tmp_path / "oe_bt.txt"
    nfd = unicodedata.normalize("NFD", _line("tilung", "tīolung"))
    source.write_text(
        "\r\n".join(["", "no at signs", "a@b", "x@<B>12</B> text@x", nfd]) + "\r\n",
        encoding="utf-8",
        newline="",
    )

    report = _importer().build_report(source, MacronIndexPayload())

    assert report.additions == {"tiolung": "tīolung"}


def test_apply_adds_only_new_keys_and_is_idempotent(tmp_path: Path):
    lines = [_line("tilung", "teolung", "tiolung")]
    source = tmp_path / "oe_bt.txt"
    source.write_text("\n".join(lines) + "\n", encoding="utf-8")
    payload = MacronIndexPayload(unique={"tilung": "tilung"})
    importer = _importer()

    first = importer.build_report(source, payload)
    added = importer.apply(first, payload)
    second = importer.build_report(source, payload)

    assert added == 2
    assert payload.unique == {
        "tilung": "tilung",
        "teolung": "teolung",
        "tiolung": "tiolung",
    }
    assert second.additions == {}
    assert second.counts["skipped_same_marks"] == 2
    assert importer.apply(second, payload) == 0
```

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_variant_importer.py -q`
Expected: collection ERROR `ModuleNotFoundError: wyrdcraeft.services.variant_importer` (and the models module).

- [ ] **Step 3: Models**

`wyrdcraeft/models/variant_import.py` (follow `models/diacritics.py`: `ConfigDict(extra="forbid")`, `#:` comments):

```python
"""Models for the Bosworth-Toller variant import report."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class VariantRow(BaseModel):
    """
    One variant spelling found in a Bosworth-Toller entry.
    """

    model_config = ConfigDict(extra="forbid")

    #: Variant spelling exactly as BT prints it.
    spelling: str = Field(..., min_length=1)
    #: Normalized index key of the spelling.
    key: str = Field(..., min_length=1)
    #: Canonical headword of the entry that lists the variant.
    headword: str = Field(..., min_length=1)
    #: 1-based line number in the Bosworth-Toller source.
    line_no: int = Field(..., ge=1)


class CollisionRow(BaseModel):
    """
    A variant whose key already exists with marks the importer will not change.
    """

    model_config = ConfigDict(extra="forbid")

    #: The variant that collides.
    variant: VariantRow
    #: Existing forms for the key: one for a unique key, the options if ambiguous.
    existing: list[str]
    #: ``more_marks`` and ``conflicting_marks`` for a unique key, ``new_pattern``
    #: for an undecided ambiguous key.
    reason: Literal["more_marks", "conflicting_marks", "new_pattern"]


class ConflictingNewKey(BaseModel):
    """
    A new key proposed by several variants with different mark patterns.
    """

    model_config = ConfigDict(extra="forbid")

    #: The normalized key.
    key: str = Field(..., min_length=1)
    #: Every variant proposing the key.
    variants: list[VariantRow]


class VariantImportReport(BaseModel):
    """
    Everything a variant import would do, and everything it leaves for review.
    """

    model_config = ConfigDict(extra="forbid")

    #: New key -> stored form (BT spelling, lowercased).
    additions: dict[str, str] = Field(default_factory=dict)
    #: Variants colliding with an existing key, left for the user.
    collisions: list[CollisionRow] = Field(default_factory=list)
    #: New keys whose variants disagree on marks; none is added.
    conflicting_new: list[ConflictingNewKey] = Field(default_factory=list)
    #: Variants that are not spellings of their headword, for keys not in the index.
    below_gate: list[VariantRow] = Field(default_factory=list)
    #: Row counts by outcome (see the importer for the names).
    counts: dict[str, int] = Field(default_factory=dict)
```

Export the four models from `wyrdcraeft/models/__init__.py` the way the other diacritic models are.

- [ ] **Step 4: Importer**

`wyrdcraeft/services/variant_importer.py`:

```python
"""Import Bosworth-Toller variant spellings into the macron index (ADR 0017)."""

from __future__ import annotations

import unicodedata
from collections import Counter, defaultdict
from typing import TYPE_CHECKING

from ..models.variant_import import (
    CollisionRow,
    ConflictingNewKey,
    VariantImportReport,
    VariantRow,
)
from .dictionary.line_parser import BTLineParser
from .markup import DiacriticTransfer, normalize_old_english
from .standard_elements import StandardElements
from .variant_filter import BTVariantFilter

if TYPE_CHECKING:
    from pathlib import Path

    from ..models.diacritics import MacronIndexPayload


class BTVariantImporter:
    """
    Decide which Bosworth-Toller variants become their own macron index entries.

    The importer never changes an existing key (ADR 0017 decision 3): it adds
    keys that are absent from ``unique`` and ``ambiguous`` and reports the rest.

    Args:
        parser: Line parser used for raw variants.
        variant_filter: Junk filter and similarity gate.
        standard_elements: Standard element list applied before comparing marks.

    """

    def __init__(
        self,
        parser: BTLineParser | None = None,
        variant_filter: BTVariantFilter | None = None,
        standard_elements: StandardElements | None = None,
    ):
        """
        Initialize the importer's collaborators.

        Args:
            parser: Line parser used for raw variants.
            variant_filter: Junk filter and similarity gate; packaged stoplist
                when omitted.
            standard_elements: Standard element list; packaged list when omitted.

        """
        #: Parser for raw (un-normalized) headwords and variants.
        self.parser = parser or BTLineParser()
        #: Junk filter and similarity gate.
        self.variant_filter = variant_filter or BTVariantFilter.load()
        #: Standard elements applied before comparing marks.
        self.standard_elements = standard_elements or StandardElements.load()

    def build_report(
        self, source_path: Path, payload: MacronIndexPayload
    ) -> VariantImportReport:
        """
        Work out what importing the variants of a source file would do.

        Args:
            source_path: Bosworth-Toller ``oe_bt.txt``.
            payload: The macron index; not modified.

        Returns:
            The additions, the collisions and conflicts left for review, the
            below-gate variants, and counts.

        """
        rows = self._read_rows(source_path)
        counts: Counter[str] = Counter(candidates=len(rows))
        report = VariantImportReport()
        kept = self._screen(rows, payload, report, counts)
        new_by_key = self._classify_existing(kept, payload, report, counts)
        self._classify_new(new_by_key, report, counts)
        report.counts = dict(counts)
        return report

    def apply(self, report: VariantImportReport, payload: MacronIndexPayload) -> int:
        """
        Add the report's new keys to the index payload.

        Side Effects:
            Adds entries to ``payload.unique``; existing keys are never replaced.

        Args:
            report: Report from :meth:`build_report` for the same payload.
            payload: The macron index to extend.

        Returns:
            How many keys were added.

        """
        added = 0
        for key, form in report.additions.items():
            if key not in payload.unique and key not in payload.ambiguous:
                payload.unique[key] = form
                added += 1
        return added

    def _read_rows(self, source_path: Path) -> list[VariantRow]:
        """
        Read every variant of every parseable line.

        Args:
            source_path: Bosworth-Toller ``oe_bt.txt``.

        Returns:
            One row per variant, in source order.

        """
        rows: list[VariantRow] = []
        with source_path.open(encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                parsed = self.parser.raw_variants(line.rstrip("\r\n"))
                if parsed is None:
                    continue
                headword, variants = parsed
                for spelling in variants:
                    key = normalize_old_english(spelling)
                    if key:
                        rows.append(
                            VariantRow(
                                spelling=unicodedata.normalize("NFC", spelling),
                                key=key,
                                headword=headword,
                                line_no=line_no,
                            )
                        )
        return rows

    def _screen(
        self,
        rows: list[VariantRow],
        payload: MacronIndexPayload,
        report: VariantImportReport,
        counts: Counter[str],
    ) -> list[VariantRow]:
        """
        Drop junk, set aside variants below the similarity gate, de-duplicate.

        Side Effects:
            Appends to ``report.below_gate`` and updates ``counts``.

        Args:
            rows: All variants.
            payload: The macron index (to skip below-gate variants of known keys).
            report: Report receiving the below-gate rows.
            counts: Outcome counters.

        Returns:
            The variants that passed, unique by key and lowercase spelling.

        """
        headwords: dict[str, set[str]] = defaultdict(set)
        for row in rows:
            headwords[row.key].add(row.headword.lower())
        kept: list[VariantRow] = []
        seen: set[tuple[str, str]] = set()
        for row in rows:
            reason = self.variant_filter.reject_reason(
                row.spelling, len(headwords[row.key])
            )
            if reason is not None:
                counts[f"rejected_{reason}"] += 1
                continue
            headword_key = normalize_old_english(row.headword) or ""
            if not self.variant_filter.within_gate(row.key, headword_key):
                if row.key not in payload.unique and row.key not in payload.ambiguous:
                    report.below_gate.append(row)
                continue
            identity = (row.key, row.spelling.lower())
            if identity not in seen:
                seen.add(identity)
                kept.append(row)
        return kept

    def _classify_existing(
        self,
        kept: list[VariantRow],
        payload: MacronIndexPayload,
        report: VariantImportReport,
        counts: Counter[str],
    ) -> dict[str, list[VariantRow]]:
        """
        Compare variants of known keys with the index; collect the new keys.

        Side Effects:
            Appends to ``report.collisions`` and updates ``counts``.

        Args:
            kept: Screened variants.
            payload: The macron index.
            report: Report receiving collisions.
            counts: Outcome counters.

        Returns:
            Variants of keys that are in neither ``unique`` nor ``ambiguous``,
            grouped by key.

        """
        new_by_key: dict[str, list[VariantRow]] = defaultdict(list)
        for row in kept:
            if row.key in payload.ambiguous_completed:
                counts["skipped_completed"] += 1
            elif row.key in payload.ambiguous:
                self._compare(row, payload.ambiguous[row.key], report, counts)
            elif row.key in payload.unique:
                self._compare(row, [payload.unique[row.key]], report, counts)
            else:
                new_by_key[row.key].append(row)
        return new_by_key

    def _compare(
        self,
        row: VariantRow,
        existing: list[str],
        report: VariantImportReport,
        counts: Counter[str],
    ) -> None:
        """
        Skip a variant that adds nothing, or list it for review.

        Side Effects:
            Updates ``counts`` or appends to ``report.collisions``.

        Args:
            row: The colliding variant.
            existing: Forms already in the index for its key.
            report: Report receiving collisions.
            counts: Outcome counters.

        """
        variant = row.spelling.lower()
        relations = [
            DiacriticTransfer.mark_relation(form, variant, self.standard_elements)
            for form in existing
        ]
        if "same" in relations:
            counts["skipped_same_marks" if len(existing) == 1 else "skipped_matches_option"] += 1
        elif len(existing) == 1 and relations[0] == "fewer":
            counts["skipped_fewer_marks"] += 1
        else:
            if len(existing) > 1:
                reason = "new_pattern"
            elif relations[0] == "more":
                reason = "more_marks"
            else:
                reason = "conflicting_marks"
            report.collisions.append(
                CollisionRow(variant=row, existing=list(existing), reason=reason)
            )

    def _classify_new(
        self,
        new_by_key: dict[str, list[VariantRow]],
        report: VariantImportReport,
        counts: Counter[str],
    ) -> None:
        """
        Add each new key whose variants agree on marks; list the rest.

        Side Effects:
            Fills ``report.additions`` and ``report.conflicting_new``; updates
            ``counts["added"]``.

        Args:
            new_by_key: Variants of absent keys, grouped by key.
            report: Report receiving additions and conflicts.
            counts: Outcome counters.

        """
        for key, rows in new_by_key.items():
            patterns = {
                DiacriticTransfer.mark_pattern(
                    self.standard_elements.standardize(row.spelling.lower())
                )
                for row in rows
            }
            if len(patterns) == 1:
                report.additions[key] = rows[0].spelling.lower()
                counts["added"] += 1
            else:
                report.conflicting_new.append(ConflictingNewKey(key=key, variants=rows))
```

Fix the over-long `counts[...]` line in `_compare` to fit 88 columns (assign the counter name to a local first). `reason` needs a `Literal` annotation for mypy: annotate `reason: Literal["more_marks", "conflicting_marks", "new_pattern"]` before the branches (import `Literal`).

- [ ] **Step 5: Run to verify they pass; gate; commit**

Run: `.venv/bin/python -m pytest tests/test_variant_importer.py -q` (all PASS), then `ruff check`, `.venv/bin/mypy`, `make napoleon-gate`, `graphify update .`:

```bash
git add wyrdcraeft/models/variant_import.py wyrdcraeft/models/__init__.py wyrdcraeft/services/variant_importer.py tests/test_variant_importer.py
git commit -m "feat: BT variant importer service and report models"
```

---

### Task 4: The `diacritic import-variants` command, docs, and a dry run on the real source (decisions 1 and 3)

**Files:**
- Modify: `wyrdcraeft/cli/diacritic.py` (new command)
- Create: `doc/source/overview/command_diacritic_import_variants.rst`; modify `doc/source/overview/using_cli.rst` (add it to the toctree after `command_diacritic_add`)
- Modify: `docs/context/diacritic.md`, `CONTEXT.md` (terms "variant import", "variant review report"), `docs/adr/0017-diacritic-cli-imports-bt-variants.md` (Implementation notes; status stays `proposed`)
- Test: `tests/test_cli_diacritic_import_variants.py` (new)

**Interfaces:**
- Consumes: Task 3's `BTVariantImporter`, `VariantImportReport`; existing `_load_macron_index_payload`, `_write_macron_index_payload`, `print_info`; `default_bt_source_path()` from `services/dictionary/resources.py`.
- Produces: `wyrdcraeft diacritic import-variants [--source-path PATH] [--index-path PATH] [--apply] [--report-output PATH]`.

- [ ] **Step 1: Write the failing tests**

`tests/test_cli_diacritic_import_variants.py`:

```python
from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

import wyrdcraeft.cli.diacritic as diacritic_module
from wyrdcraeft.cli.cli import cli

if TYPE_CHECKING:
    from pathlib import Path

BT_LINES = [
    "tilung@<B>tilung,</B> teolung, tiolung; <I>f.</I> striving.@tilung",
    "wege@<B>wege,</B> wēg; <I>m.</I> a way.@wege",
]


@pytest.fixture
def files(temp_dir: Path) -> dict[str, Path]:
    source = temp_dir / "oe_bt.txt"
    source.write_text("\n".join(BT_LINES) + "\n", encoding="utf-8")
    index = temp_dir / "index.json"
    index.write_text(
        json.dumps(
            {
                "meta": {"source_path": "kept"},
                "unique": {"weg": "weg"},
                "ambiguous": {},
                "ambiguous_completed": [],
                "ambiguous_metadata": {},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return {"source": source, "index": index, "report": temp_dir / "report.json"}


def _run(runner, files, monkeypatch, *extra: str):
    # print_info writes to a stderr console CliRunner does not capture.
    messages: list[str] = []
    monkeypatch.setattr(diacritic_module, "print_info", messages.append)
    result = runner.invoke(
        cli,
        [
            "diacritic",
            "import-variants",
            "--source-path",
            str(files["source"]),
            "--index-path",
            str(files["index"]),
            "--report-output",
            str(files["report"]),
            *extra,
        ],
    )
    return result, messages


def test_dry_run_writes_the_report_but_not_the_index(runner, files, monkeypatch):
    before = files["index"].read_text(encoding="utf-8")

    result, messages = _run(runner, files, monkeypatch)

    assert result.exit_code == 0, result.output
    assert files["index"].read_text(encoding="utf-8") == before
    report = json.loads(files["report"].read_text(encoding="utf-8"))
    assert report["additions"] == {"teolung": "teolung", "tiolung": "tiolung"}
    assert [c["reason"] for c in report["collisions"]] == ["more_marks"]
    assert any(m.startswith("Would add 2") for m in messages)


def test_apply_adds_new_keys_and_keeps_everything_else(runner, files, monkeypatch):
    result, messages = _run(runner, files, monkeypatch, "--apply")

    assert result.exit_code == 0, result.output
    written = json.loads(files["index"].read_text(encoding="utf-8"))
    assert written["unique"] == {
        "weg": "weg",
        "teolung": "teolung",
        "tiolung": "tiolung",
    }
    assert written["meta"]["source_path"] == "kept"
    assert written["meta"]["unique_count"] == 3
    assert any(m.startswith("Added 2") for m in messages)


def test_apply_twice_adds_nothing_the_second_time(runner, files, monkeypatch):
    _run(runner, files, monkeypatch, "--apply")
    first = files["index"].read_text(encoding="utf-8")

    result, messages = _run(runner, files, monkeypatch, "--apply")

    assert result.exit_code == 0, result.output
    assert files["index"].read_text(encoding="utf-8") == first
    assert any(m.startswith("Added 0") for m in messages)


def test_missing_source_is_a_clean_error(runner, files, monkeypatch):
    files["source"].unlink()

    result, _ = _run(runner, files, monkeypatch)

    assert result.exit_code != 0
    assert "Traceback" not in result.output


def test_missing_index_is_a_clean_error(runner, files, monkeypatch):
    files["index"].unlink()

    result, _ = _run(runner, files, monkeypatch)

    assert result.exit_code == 1
    assert "Macron index file not found" in result.output
```

(`runner` and `temp_dir` are the repo's shared fixtures, used by `tests/test_cli_diacritic.py`. `--source-path` uses `click.Path(exists=True)` so a missing source exits 2 with a usage error; the test asserts only non-zero and no traceback.)

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_cli_diacritic_import_variants.py -q`
Expected: FAIL: `No such command 'import-variants'` (exit code 2), so the report/index assertions fail.

- [ ] **Step 3: Implement the command**

In `wyrdcraeft/cli/diacritic.py` add imports `from ..services.dictionary.resources import default_bt_source_path` and `from ..services.variant_importer import BTVariantImporter`, then after `diacritic_delete`:

```python
@diacritic_group.command(
    name="import-variants",
    help=(
        "Add Bosworth-Toller variant spellings to the macron index as their own "
        "entries. Dry run unless --apply is given."
    ),
)
@click.option(
    "--source-path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Bosworth-Toller oe_bt.txt. Default: the packaged source.",
)
@click.option(
    "--index-path",
    type=click.Path(path_type=Path),
    default=DEFAULT_MACRON_INDEX_PATH,
    show_default=True,
    help="Macron index JSON path.",
)
@click.option(
    "--apply",
    "apply_changes",
    is_flag=True,
    help="Write the new entries to the index (default: dry run).",
)
@click.option(
    "--report-output",
    type=click.Path(path_type=Path),
    default=Path("bt-variant-import-report.json"),
    show_default=True,
    help="Review report JSON: collisions, conflicting keys, below-gate variants.",
)
def diacritic_import_variants(
    source_path: Path | None,
    index_path: Path,
    apply_changes: bool,
    report_output: Path,
) -> None:
    """
    Import Bosworth-Toller variants into the unique list of the macron index.

    A variant becomes its own entry, spelled as BT prints it (lowercased). An
    existing key is never changed; collisions, conflicting new keys and
    variants that are not spellings of their headword go to the report.

    Side Effects:
        Writes the report; with ``--apply`` also writes the index.

    Args:
        source_path: Bosworth-Toller source; packaged source when omitted.
        index_path: Path to macron index JSON file.
        apply_changes: If True, write the new entries to the index.
        report_output: Where to write the review report.

    """
    payload = _load_macron_index_payload(index_path)
    importer = BTVariantImporter()
    report = importer.build_report(source_path or default_bt_source_path(), payload)

    report_output.parent.mkdir(parents=True, exist_ok=True)
    report_output.write_text(
        json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if apply_changes:
        added = importer.apply(report, payload)
        if added:
            _write_macron_index_payload(index_path, payload)
        verb, count = "Added", added
    else:
        verb, count = "Would add", len(report.additions)
    print_info(
        f"{verb} {count} new keys. For review in {report_output}: "
        f"{len(report.collisions)} collisions, "
        f"{len(report.conflicting_new)} conflicting new keys, "
        f"{len(report.below_gate)} variants below the similarity gate."
    )
```

Keep the method ≤ 60 lines and ruff clean (the command has four parameters; no `noqa` needed).

- [ ] **Step 4: Run to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_cli_diacritic_import_variants.py tests/test_cli_diacritic.py -q`
Expected: PASS.

- [ ] **Step 5: Dry run on the real source (no `--apply`)**

Run from the scratchpad so no report lands in the repo:

```bash
.venv/bin/wyrdcraeft diacritic import-variants --report-output "$SCRATCH/bt-variant-import-report.json"
```

Expected, within about 5% (measured while planning on the current index): about **2,439 would be added**, **80 collisions** (75 `more_marks`, 4 `conflicting_marks`, 1 `new_pattern`), **10 conflicting new keys**, about **1,622** below-gate keys (a few more rows), and the packaged index file unchanged (`git diff --stat wyrdcraeft/etc/diacritic/oe_bt_macron_index.json` empty). If a figure is far off, stop and investigate before documenting; ledger the finding. Skim the report: `additions` should look like real spellings (`tiolung`, `teolung`), `below_gate` should be mostly inflected forms and English words, `collisions` should read like the ADR's examples (`bide`/`bīde`).

- [ ] **Step 6: Docs and ADR notes**

- `command_diacritic_import_variants.rst`: purpose, syntax, options, what is added (BT spelling, lowercased, no marks copied), what is never touched, the junk filter and similarity gate in plain language, the collision policy, the report sections and how to settle a case with `diacritic add --force`, "dry run first, then `--apply`, then review the diff". Add it to the toctree in `using_cli.rst`.
- `docs/context/diacritic.md`: a bullet on the importer and its report. `CONTEXT.md`: terms "variant import" and "variant review report".
- ADR 0017 Implementation notes: the four classes and where they live, the final rules, the measured dry-run numbers from Step 5, the rulings above that are not already in the ADR (stoplist file, no affix rule, `below_gate` only for absent keys, report default path), and that the packaged index was not changed. Intro: "Implemented; the packaged index has not been imported yet." Status stays `proposed`.

- [ ] **Step 7: Gate and commit**

Full suite `.venv/bin/python -m pytest -q` (all green), `ruff check` and `.venv/bin/mypy` on all touched files, `make napoleon-gate` (94), `graphify update .`, then:

```bash
git add wyrdcraeft/cli/diacritic.py tests/test_cli_diacritic_import_variants.py doc/source/overview/command_diacritic_import_variants.rst doc/source/overview/using_cli.rst docs/context/diacritic.md CONTEXT.md docs/adr/0017-diacritic-cli-imports-bt-variants.md
git commit -m "feat: diacritic import-variants command with review report"
```

After the final review, tell the user how to run the real import: `wyrdcraeft diacritic import-variants --apply`, then review `git diff` of the index and the report.
