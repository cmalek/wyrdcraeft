# Diphthong-Aware Diacritic Transfer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `DiacriticTransfer` treat a diphthong as one unit so a source already marked in BT's diphthong style is no longer double-marked, and expose a `mark_pattern` helper that later plans reuse.

**Architecture:** `DiacriticTransfer` (in `wyrdcraeft/services/markup.py`) is rewritten around a small frozen dataclass `_Letter`. Both the source and the index (reference) form are parsed into letters. The *reference* decides which letter pairs are diphthongs (`ea`, `eo`, `ie`, `io`, adjacent with no hyphen between them, only macrons on them); in a diphthong all marks are merged onto the first vowel. A mark is added to a source letter only when the source's merged marks for that letter are empty.

**Tech Stack:** Python 3.13, pytest, ruff, mypy. No new dependencies.

**Spec:** `docs/adr/0020-diacritic-transfer-treats-a-diphthong-as-one-unit.md` (status `proposed`; also read `docs/adr/0015-mark-diacritics-is-additive-transfer.md`). ADR 0020 decision 2 was amended while this plan was reviewed against the index data: only macrons form a diphthong, so a breve in a loanword (`ēliŏtrŏpus`) is left alone.

## Global Constraints

- Additive only: no source character is removed, replaced or re-cased; no hyphen is added (ADR 0015).
- Diphthongs are exactly `ea`, `eo`, `ie`, `io`, only when the two vowels are adjacent in the reference with no hyphen or dash between them, and only when the reference carries no mark other than a macron on either vowel. A breve in a loanword such as `ēliŏtrŏpus` marks a hiatus, not a diphthong, and stays on its own letter.
- In a diphthong the macron always goes on the **first** vowel, whichever vowel the reference or the source marked.
- Marks already on a source letter (or on either vowel of a source diphthong, of any kind) are never changed, even if they differ from the reference.
- Lookup stays `normalize_old_english`; `BTSpellingNormalizer` is not used in matching or transfer.
- Project rules (`AGENTS.md`): Napoleon docstrings on every non-test function/method (only applicable sections), `#:` comments on class attributes and module globals, function bodies ≤ 60 lines, no workarounds.
- Quality gate after Python edits: `.venv/bin/ruff check` and `.venv/bin/ruff format` on touched files, `.venv/bin/mypy` on touched files, `make napoleon-gate`. **Known baseline:** `make napoleon-gate` already fails on the clean tree (94 reported against 95 baseline keys) and `.venv/bin/mypy wyrdcraeft/cli/cli.py` has one error at line 107. Neither is yours; do not add new violations (the gate must still report 94 total).
- Run tests with `.venv/bin/python -m pytest`, never bare `pytest`.
- Existing index data is unaffected: of 41,630 index forms only two (`īē-scēada`, `fēōnd-sēocnes`, both with a macron on both vowels) are changed by merging, so this change alters output only for sources that already mark a diphthong.

## Review Focus

- Uppercase and mixed-case source (`LEAST`, `Least`): the macron must land on the first vowel in the source's case (`LĒAST`).
- Source in decomposed (NFD) form that already marks the diphthong: nothing may be added.
- Reference with a hyphen between the vowels (`be-ōdrian`): not a diphthong, the macron stays on `ō`.
- Source carrying a breve (or any other mark) on a diphthong vowel: kept, nothing added to the pair.
- Loanword hiatus with a breve in the reference (`ēliŏtrŏpus`): the breve is not moved onto the `i`.
- Reference with a macron on both vowels (`fēōnd`): merged onto the first vowel (`fēond`).
- Vowel pairs that are not diphthongs (`ia`, `ae`) keep per-letter behavior.
- Three vowels in a row (`beoa`): pairs do not overlap; the first pair wins.

---

### Task 1: `mark_pattern` and the parsing helpers

**Files:**
- Modify: `wyrdcraeft/services/markup.py` (imports at the top; module globals after `DOT_ABOVE`; class `DiacriticTransfer`)
- Test: `tests/test_markup.py`

**Interfaces:**
- Consumes: `CLUSTER_RE`, `DASH_CHARS` (existing module globals in `markup.py`).
- Produces:
  - `DIPHTHONGS: Final[frozenset[tuple[str, str]]]` and `MACRON: Final[str]`
  - `_Letter` frozen dataclass with fields `cluster: str`, `base: str`, `marks: frozenset[str]`, `joined: bool`
  - `DiacriticTransfer._parse(text: str) -> list[_Letter]`
  - `DiacriticTransfer._diphthong_starts(letters: list[_Letter]) -> list[int]`
  - `DiacriticTransfer._merge_diphthongs(letters: list[_Letter], starts: list[int]) -> list[frozenset[str]]`
  - `DiacriticTransfer.mark_pattern(form: str) -> tuple[tuple[str, frozenset[str]], ...]`
- `DiacriticTransfer.transfer` is left unchanged in this task and still works.

- [ ] **Step 1: Write the failing tests**

In `tests/test_markup.py`, add `DiacriticTransfer` to the existing import list (keep it alphabetical, after `DiacriticRestorer`):

```python
from wyrdcraeft.services.markup import (
    DEFAULT_MACRON_INDEX_PATH,
    CPalatalizer,
    DiacriticRestorer,
    DiacriticTransfer,
    GPalatalizer,
    MacronApplicator,
    normalize_morphology_title,
    normalize_old_english,
)
```

Two existing tests import `DiacriticTransfer` inside the function body; delete those two lines now that it is imported at module level: `    from wyrdcraeft.services.markup import DiacriticTransfer` (in `test_diacritic_transfer_preserves_source_letters_hyphens_and_case` and `test_diacritic_transfer_unalignable_returns_none`).

Append at the end of the file:

```python
def test_mark_pattern_shape_for_a_diphthong():
    macron = "\u0304"
    assert DiacriticTransfer.mark_pattern("lēast") == (
        ("l", frozenset()),
        ("e", frozenset({macron})),
        ("a", frozenset()),
        ("s", frozenset()),
        ("t", frozenset()),
    )


def test_mark_pattern_moves_a_second_vowel_macron_to_the_first():
    assert DiacriticTransfer.mark_pattern("leāst") == DiacriticTransfer.mark_pattern(
        "lēast"
    )


def test_mark_pattern_ignores_case_hyphens_and_eth_thorn():
    pattern = DiacriticTransfer.mark_pattern
    assert pattern("Hlāford") == pattern("hlā-ford")
    assert pattern("ðā") == pattern("þā")
    assert pattern("a\u2014ælan") == pattern("aælan")


def test_mark_pattern_does_not_join_vowels_separated_by_a_hyphen():
    pattern = DiacriticTransfer.mark_pattern
    assert pattern("be-ōdrian") != pattern("bēodrian")
    assert pattern("beōdrian") == pattern("bēodrian")


def test_mark_pattern_leaves_a_breve_on_its_own_letter():
    breve = "\u0306"
    pattern = DiacriticTransfer.mark_pattern("ēliŏtrŏpus")
    assert pattern[3] == ("o", frozenset({breve}))
    assert pattern[2] == ("i", frozenset())
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_markup.py -k mark_pattern -v`
Expected: FAIL with `AttributeError: type object 'DiacriticTransfer' has no attribute 'mark_pattern'`.

- [ ] **Step 3: Add the import and the globals**

In `wyrdcraeft/services/markup.py`, add to the imports, directly after `import unicodedata`:

```python
from dataclasses import dataclass
```

Directly after the `DOT_ABOVE` global add:

```python
#: Adjacent vowel pairs (first, second) that count as one diphthong.
DIPHTHONGS: Final[frozenset[tuple[str, str]]] = frozenset(
    {("e", "a"), ("e", "o"), ("i", "e"), ("i", "o")}
)
#: Combining macron, the only mark that is shared between a diphthong's vowels.
MACRON: Final[str] = "\u0304"
```

- [ ] **Step 4: Add `_Letter` and the new helpers to `DiacriticTransfer`**

Directly above `class DiacriticTransfer:` add:

```python
@dataclass(frozen=True)
class _Letter:
    """
    One letter of a token together with its combining marks.
    """

    #: Letter plus combining marks, exactly as written.
    cluster: str
    #: Case-folded base letter, with ``ð`` as ``þ``.
    base: str
    #: Combining marks on the letter, as decomposed characters.
    marks: frozenset[str]
    #: Whether no hyphen or dash separates this letter from the previous one.
    joined: bool
```

Inside `DiacriticTransfer`, add these four methods **before** `transfer` (leave `_letters`, `_base` and `transfer` as they are for now):

```python
    @staticmethod
    def _parse(text: str) -> list[_Letter]:
        """
        Split text into letters, dropping hyphens and dashes.

        Args:
            text: Token text.

        Returns:
            The letters in order, each noting whether it is joined to the
            previous letter without a hyphen or dash between them.

        """
        letters: list[_Letter] = []
        joined = False
        for cluster in CLUSTER_RE.findall(text):
            if cluster in DASH_CHARS:
                joined = False
                continue
            decomposed = unicodedata.normalize("NFD", cluster)
            letters.append(
                _Letter(
                    cluster=cluster,
                    base=decomposed[0].lower().replace("ð", "þ"),
                    marks=frozenset(decomposed[1:]),
                    joined=joined,
                )
            )
            joined = True
        return letters

    @staticmethod
    def _diphthong_starts(letters: list[_Letter]) -> list[int]:
        """
        Find the diphthongs of a form.

        A diphthong is an adjacent pair from :data:`DIPHTHONGS` with no hyphen
        between the vowels and no mark other than a macron on either (a breve in
        a loanword such as ``ēliŏtrŏpus`` marks a hiatus, not a diphthong).
        Pairs do not overlap; the first one wins.

        Args:
            letters: Letters of the form that defines the word, the index form.

        Returns:
            The index of the first vowel of each diphthong, in order.

        """
        starts: list[int] = []
        i = 0
        while i + 1 < len(letters):
            first, second = letters[i], letters[i + 1]
            if (
                second.joined
                and (first.base, second.base) in DIPHTHONGS
                and (first.marks | second.marks) <= {MACRON}
            ):
                starts.append(i)
                i += 2
            else:
                i += 1
        return starts

    @staticmethod
    def _merge_diphthongs(
        letters: list[_Letter], starts: list[int]
    ) -> list[frozenset[str]]:
        """
        Return each letter's marks with diphthong marks moved to the first vowel.

        Args:
            letters: Letters of one form.
            starts: First-vowel indexes of the diphthongs, from the index form.

        Returns:
            One mark set per letter; the second vowel of a diphthong has none.

        """
        marks = [letter.marks for letter in letters]
        for i in starts:
            marks[i] = marks[i] | marks[i + 1]
            marks[i + 1] = frozenset()
        return marks

    @classmethod
    def mark_pattern(cls, form: str) -> tuple[tuple[str, frozenset[str]], ...]:
        """
        Describe a form as its letters and marks, independent of spelling noise.

        Case, hyphens, dashes and ``ð``/``þ`` do not matter, and a diphthong's
        macron is always on its first vowel, so ``leāst`` and ``lēast`` have the
        same pattern.

        Args:
            form: A source word or an index display form.

        Returns:
            One ``(base letter, marks)`` pair per letter.

        """
        letters = cls._parse(form)
        marks = cls._merge_diphthongs(letters, cls._diphthong_starts(letters))
        return tuple(
            (letter.base, mark_set)
            for letter, mark_set in zip(letters, marks, strict=True)
        )
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_markup.py -v`
Expected: all tests PASS (the five new `mark_pattern` tests and every existing test).

- [ ] **Step 6: Lint, type-check, commit**

```bash
.venv/bin/ruff format wyrdcraeft/services/markup.py tests/test_markup.py
.venv/bin/ruff check wyrdcraeft/services/markup.py tests/test_markup.py
.venv/bin/mypy wyrdcraeft/services/markup.py
```
Expected: ruff clean; mypy reports nothing for `markup.py` (the only repo-wide error is `cli/cli.py:107`).

```bash
git add wyrdcraeft/services/markup.py tests/test_markup.py
git commit -m "feat: add DiacriticTransfer.mark_pattern with diphthong-merged macrons

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Make `transfer` treat a diphthong as one unit

**Files:**
- Modify: `wyrdcraeft/services/markup.py` (`DiacriticTransfer.transfer` and class docstring; delete `_letters` and `_base`)
- Test: `tests/test_markup.py`

**Interfaces:**
- Consumes: `_Letter`, `DiacriticTransfer._parse`, `_diphthong_starts`, `_merge_diphthongs`, `DIPHTHONGS`, `MACRON` from Task 1.
- Produces: `DiacriticTransfer.transfer(source: str, marked: str) -> str | None` with the same signature, now diphthong-aware.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_markup.py`:

```python
@pytest.mark.parametrize(
    ("source", "reference", "expected"),
    [
        # source already marks the second vowel: nothing is added (the bug)
        ("leāst", "lēast", "leāst"),
        ("lēast", "lēast", "lēast"),
        # unmarked source gets the macron on the FIRST vowel, from either style
        ("least", "lēast", "lēast"),
        ("least", "leāst", "lēast"),
        # source case wins
        ("LEAST", "lēast", "LĒAST"),
        ("Least", "leāst", "Lēast"),
        # ie and io are diphthongs too
        ("driefan", "driēfan", "drīefan"),
        ("driēfan", "drīefan", "driēfan"),
        ("hio", "hīo", "hīo"),
        # a hyphen in the REFERENCE keeps the vowels apart
        ("beodrian", "be-ōdrian", "beōdrian"),
        ("beodrian", "beōdrian", "bēodrian"),
        # a hyphen in the SOURCE does not matter
        ("e-a", "ēa", "ē-a"),
        # a different mark on the source is kept, nothing is added to the pair
        ("leăst", "lēast", "leăst"),
        # macrons on both reference vowels merge onto the first
        ("feond", "fēōnd", "fēond"),
        ("lēast", "lēāst", "lēast"),
        # a breve in the reference marks a hiatus: each mark stays on its letter
        ("eliotropus", "ēliŏtrŏpus", "ēliŏtrŏpus"),
        # not a diphthong: per-letter behavior
        ("hia", "hiā", "hiā"),
        ("hae", "hāe", "hāe"),
        # pairs do not overlap: the first pair wins
        ("beoa", "beōa", "bēoa"),
    ],
)
def test_transfer_treats_a_diphthong_as_one_unit(source, reference, expected):
    assert DiacriticTransfer.transfer(source, reference) == expected


def test_transfer_diphthong_in_decomposed_source_is_not_double_marked():
    import unicodedata

    source = unicodedata.normalize("NFD", "leāst")
    assert DiacriticTransfer.transfer(source, "lēast") == source


def test_transfer_adds_marks_to_a_decomposed_source_letter_as_composed():
    import unicodedata

    result = DiacriticTransfer.transfer(unicodedata.normalize("NFD", "least"), "lēast")
    assert result == unicodedata.normalize("NFC", "lēast")


def test_restorer_does_not_double_mark_a_bt_style_diphthong(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(index_path, unique={"least": "leāst"}, ambiguous={})
    restorer = DiacriticRestorer(macron_index_path=index_path)

    result = restorer.restore_text("least leāst lēast LEAST\n")

    assert result.marked_text == "lēast leāst lēast LĒAST\n"
    assert result.unaligned == []
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_markup.py -k "diphthong or double_mark" -v`
Expected: FAIL. At minimum `leāst`/`lēast` returns `lēāst` instead of `leāst`, and the restorer test fails the same way.

- [ ] **Step 3: Replace `transfer`, the class docstring, and remove the old helpers**

In `wyrdcraeft/services/markup.py`, delete the old `_letters` and `_base` static methods from `DiacriticTransfer`, replace the whole `transfer` method with the code below, and replace the class docstring with the one shown.

```python
    @classmethod
    def transfer(cls, source: str, marked: str) -> str | None:
        """
        Add the index form's marks to the matching letters of ``source``.

        Args:
            source: Verbatim source token.
            marked: Macron-index display form for the same word.

        Returns:
            The source token with missing marks added, or ``None`` when the
            letters of the two forms cannot be aligned.

        """
        source_letters = cls._parse(source)
        index_letters = cls._parse(marked)
        if len(source_letters) != len(index_letters) or any(
            s.base != i.base for s, i in zip(source_letters, index_letters, strict=True)
        ):
            return None
        starts = cls._diphthong_starts(index_letters)
        source_marks = cls._merge_diphthongs(source_letters, starts)
        index_marks = cls._merge_diphthongs(index_letters, starts)
        additions = {
            n: index_marks[n]
            for n in range(len(source_letters))
            if index_marks[n] and not source_marks[n]
        }
        out: list[str] = []
        letter_index = 0
        for cluster in CLUSTER_RE.findall(source):
            if cluster in DASH_CHARS:
                out.append(cluster)
                continue
            if letter_index in additions:
                marks = "".join(sorted(additions[letter_index]))
                out.append(unicodedata.normalize("NFC", cluster + marks))
            else:
                out.append(cluster)
            letter_index += 1
        return "".join(out)
```

Class docstring:

```python
    """
    Copy combining marks from a macron-index form onto a source token.

    The index form never replaces the source token: its letters are aligned
    one-to-one with the source letters (case, ``ð``≡``þ`` and hyphens/dashes
    ignored) and only marks missing from the source are added. A diphthong
    (``ea``, ``eo``, ``ie``, ``io``, with no hyphen between the vowels in the
    index form and only macrons on them) is one unit whose macron always sits on
    the first vowel, whichever vowel the index form or the source marked.
    """
```

- [ ] **Step 4: Confirm nothing else used the removed helpers**

Run: `grep -rn "DiacriticTransfer\._letters\|DiacriticTransfer\._base\|cls\._letters\|cls\._base" wyrdcraeft tests`
Expected: no output.

- [ ] **Step 5: Run the whole mark-diacritics test set**

Run: `.venv/bin/python -m pytest tests/test_markup.py tests/test_cli_mark_diacritics.py tests/test_macron_index_builder.py -v`
Expected: all PASS, including the older transfer tests (`test_diacritic_transfer_preserves_source_letters_hyphens_and_case`, `test_diacritic_transfer_unalignable_returns_none`, the NFD and dash tests).

- [ ] **Step 6: Lint, type-check, commit**

```bash
.venv/bin/ruff format wyrdcraeft/services/markup.py tests/test_markup.py
.venv/bin/ruff check wyrdcraeft/services/markup.py tests/test_markup.py
.venv/bin/mypy wyrdcraeft/services/markup.py
git add wyrdcraeft/services/markup.py tests/test_markup.py
git commit -m "fix: stop double-marking diphthongs in DiacriticTransfer

A source already marking a diphthong in BT's style (leāst) was given a second
mark against a normal-style index form (lēast -> lēāst). The transfer now
treats ea/eo/ie/io as one unit with the macron on the first vowel.

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Docs, ADR amendment, glossary, full gates

**Files:**
- Modify: `docs/adr/0020-diacritic-transfer-treats-a-diphthong-as-one-unit.md` (`## Consequences`)
- Modify: `docs/adr/0015-mark-diacritics-is-additive-transfer.md` (section `## Refined by`)
- Modify: `doc/source/overview/command_convert_mark_diacritics.rst`
- Modify: `CONTEXT.md` (glossary, after the `sc exception` bullet)
- Modify: `doc/source/changelog.rst` (**do not commit this file**, see Step 6)

**Interfaces:**
- Consumes: the finished behavior from Task 2.
- Produces: documentation only.

- [ ] **Step 1: Update ADR 0020's consequences**

(ADR 0020 decision 2 already says macrons only; it was amended during plan review. Check that it does before continuing.)

In `docs/adr/0020-diacritic-transfer-treats-a-diphthong-as-one-unit.md`, `## Consequences`, replace the first bullet (`Fixes the double-marking above, which exists in the code today.`) with:

```markdown
- Fixes the double-marking above (implemented in `DiacriticTransfer`, with
  `DiacriticTransfer.mark_pattern` as the shared helper ADR 0019 reuses). Of
  41,630 index forms only two (`īē-scēada`, `fēōnd-sēocnes`, a macron on both
  vowels) change under the merge, so existing output is otherwise unaffected.
```

Do **not** change the ADR's `status:` line; accepting it is the user's call.

- [ ] **Step 2: Update ADR 0015's `## Refined by` section**

Replace its body with:

```markdown
[ADR 0020](0020-diacritic-transfer-treats-a-diphthong-as-one-unit.md)
(proposed) makes the transfer treat a diphthong as one unit and fixes source
capitalization; it is implemented in `DiacriticTransfer`, so a source already
marked in BT's diphthong style is no longer double-marked.
```

- [ ] **Step 3: Document the behavior in the command page**

In `doc/source/overview/command_convert_mark_diacritics.rst`, the "Runtime processing flow" item that begins "if key in ``unique``: align the index form with the source token" ends with the words "emit an unaligned row". Append this to that item (same indentation as the item's continuation lines):

```rst
     A diphthong (``ea``, ``eo``, ``ie``, ``io``, not separated by a hyphen in
     the index form) is treated as one unit whose macron goes on the first
     vowel; a source that already marks either vowel gets nothing added to it.
```

- [ ] **Step 4: Add the glossary term**

In `CONTEXT.md`, after the `sc exception` bullet, add:

```markdown
- mark pattern: a form reduced to its letters and combining marks, ignoring case,
  hyphens/dashes and eth/thorn, with a diphthong's macron on its first vowel;
  `DiacriticTransfer.mark_pattern` computes it
```

- [ ] **Step 5: Changelog (leave uncommitted)**

In `doc/source/changelog.rst`, under `Unreleased` → `Bugfixes`, add:

```rst
- ``wyrdcraeft source mark-diacritics`` no longer double-marks a diphthong that the source already marks in Bosworth-Toller's style (``leāst`` stayed ``leāst`` instead of becoming ``lēāst``).
```

This file also holds the user's own uncommitted release notes, so do **not** `git add` it. Say in the hand-off that this line is left uncommitted.

- [ ] **Step 6: Full gates**

Run:
```bash
.venv/bin/python -m pytest tests -q -p no:cacheprovider
.venv/bin/ruff check wyrdcraeft/services/markup.py tests/test_markup.py
make napoleon-gate
graphify update .
```
Expected: all tests PASS (about 1,100); ruff clean; `make napoleon-gate` still fails with exactly the baseline count (94 total against 95 baseline keys), i.e. no new violations; graphify updates.

- [ ] **Step 7: Commit**

```bash
git add docs/adr/0015-mark-diacritics-is-additive-transfer.md docs/adr/0020-diacritic-transfer-treats-a-diphthong-as-one-unit.md doc/source/overview/command_convert_mark_diacritics.rst CONTEXT.md
git commit -m "docs: describe diphthong-aware transfer and the mark pattern term

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

## Self-Review

- **Spec coverage (ADR 0020):** decision 1 (lookup unchanged, no `BTSpellingNormalizer`) is honored by not touching it (Global Constraints); decision 2 (diphthong as one unit, macron on the first vowel) is Task 2 (macron-only, as amended in the ADR); decision 3 (reference hyphens honored) is the `be-ōdrian` cases and `joined`; decision 4 (shared mark pattern for ADR 0019) is Task 1's `mark_pattern`; decisions 5 and 6 (source never rewritten, source capitalization wins) are the `LEAST`/`Least` and untouched-cluster cases.
- **Placeholder scan:** none; every step has its full code or command.
- **Type consistency:** `_Letter`, `_parse`, `_diphthong_starts`, `_merge_diphthongs`, `mark_pattern`, `DIPHTHONGS`, `MACRON` have the same names and signatures in every task that uses them; the code blocks were generated from one validated module.
- **Review Focus:** each of the eight lines maps to a test (case, NFD, hyphen in reference, breve on source, `ēliŏtrŏpus`, `fēōnd`, `hia`/`hae`, `beoa`).
