# `GPalatalizer` Reads `g/frontal.txt` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `GPalatalizer` read its "`g` stays velar before a front vowel" exceptions from the hand-edited file `wyrdcraeft/etc/diacritic/g/frontal.txt` instead of a hardcoded Python list, without losing any protection the Python list gives today.

**Architecture:** A small module function `_load_folded_word_list` (same idea as `CPalatalizer._load_word_list`, but it folds with `_fold` so macrons are kept) loads the file once in a new `GPalatalizer.__init__`. The 43 words that exist only in the Python list are first appended to the file (a union), so behavior is preserved, then the Python list is removed. The ending exceptions (`ENDING_G_EXCEPTIONS`) stay in code.

**Tech Stack:** Python 3.13, pytest, ruff, mypy. No new dependencies.

**Spec:** `docs/adr/0015-mark-diacritics-is-additive-transfer.md`, section "Proposed follow-up (not implemented): `GPalatalizer` reads `g/frontal.txt`". The user has asked for this change; confirm the union migration (Task 2) with them before executing, because it edits their hand-maintained file.

## Global Constraints

- The file is one word per line, hand-edited by the user; blank lines and `#` comment lines are ignored.
- Entries are compared **folded**: NFC, lowercase, `ð` as `þ`, macrons kept (`gēar` and `gear` are different entries). A trailing hyphen is dropped (`gǣst-` means `gǣst`) because the palatalizer compares one dash-free segment at a time.
- An entry exempts only that exact word (`gǣst` does not exempt `gǣstas`), as the Python list did.
- A missing file logs a warning and gives an empty exception set, like `CPalatalizer` does.
- The file may start with a UTF-8 byte-order mark (some editors add one); it is ignored. Inline comments are **not** supported: a `#` after a word becomes part of that line's entry, so comments go on their own lines.
- No existing exception may stop working: every one of the 44 words in today's `FRONTAL_G_EXCEPTIONS` must still exempt after the change.
- Project rules (`AGENTS.md`): Napoleon docstrings on every non-test function/method (only applicable sections), `#:` comments on class attributes, instance attributes and module globals, function bodies ≤ 60 lines, no workarounds.
- Quality gate after Python edits: `.venv/bin/ruff check` and `.venv/bin/ruff format` on touched files, `.venv/bin/mypy` on touched files, `make napoleon-gate`. **Known baseline:** `make napoleon-gate` already fails on the clean tree (94 reported against 95 baseline keys) and `.venv/bin/mypy wyrdcraeft/cli/cli.py` has one error at line 107; neither is yours. The gate must still report 94 total.
- Run tests with `.venv/bin/python -m pytest`, never bare `pytest`.
- The package data globs in `pyproject.toml` already include `etc/diacritic/*/*.txt`; no packaging change is needed.

## Review Focus

- The file is empty, or only comments: no crash, no exceptions.
- File entries with capitals (`Gildas`) and surrounding spaces must still match the lowercase word.
- Hyphenated tokens: `gǣst-hūs` must be exempted through its `gǣst` segment.
- An entry that is a prefix of a longer word must not exempt the longer word (`gǣst` vs `gǣstas`).
- Words that are exempt today only because of the Python list (`gēar`, `gēat`, `gǣt`, `gēn`) stay exempt through the default file.
- A line holding only `-` must not become an empty-string entry, and `gǣlsa -` (space before the hyphen) must still mean `gǣlsa`.
- A file saved with a UTF-8 byte-order mark: its first word must still match.

---

### Task 1: The folded word-list loader

**Files:**
- Modify: `wyrdcraeft/services/markup.py` (module globals near `DEFAULT_C_FORCE_NON_PALATALIZE_PATH`, line ~39; helper functions after `_fold`, line ~140)
- Test: `tests/test_markup.py`

**Interfaces:**
- Consumes: `_fold(text: str) -> str`, `LOGGER`, `DEFAULT_DIACRITIC_DIR` (existing in `markup.py`).
- Produces:
  - `DEFAULT_G_FRONTAL_PATH: Final[Path]` (= `DEFAULT_DIACRITIC_DIR / "g" / "frontal.txt"`)
  - `_load_folded_word_list(path: Path) -> frozenset[str]`

- [ ] **Step 1: Write the failing tests**

In `tests/test_markup.py`, extend the existing import with the two new names (keep the list alphabetical; constants first):

```python
from wyrdcraeft.services.markup import (
    DEFAULT_G_FRONTAL_PATH,
    DEFAULT_MACRON_INDEX_PATH,
    CPalatalizer,
    DiacriticRestorer,
    GPalatalizer,
    MacronApplicator,
    _load_folded_word_list,
    normalize_morphology_title,
    normalize_old_english,
)
```

(If the diphthong plan (`2026-10-08-diphthong-aware-diacritic-transfer.md`) has already been executed, `DiacriticTransfer` is in that import list too: keep it, in alphabetical place, and add only the two new names.) Append at the end of the file:

```python
def test_load_folded_word_list_skips_comments_blanks_and_folds(tmp_path: Path):
    words = tmp_path / "frontal.txt"
    words.write_text(
        "# a comment\n\n  Gildas  \ngǣst-\ngǣlsa -\ngēoguð\n-\n#-\n",
        encoding="utf-8",
    )

    assert _load_folded_word_list(words) == frozenset(
        {"gildas", "gǣst", "gǣlsa", "gēoguþ"}
    )


def test_load_folded_word_list_ignores_a_byte_order_mark(tmp_path: Path):
    words = tmp_path / "bom.txt"
    words.write_bytes(b"\xef\xbb\xbfGildas\ngigant\n")

    assert _load_folded_word_list(words) == frozenset({"gildas", "gigant"})


def test_load_folded_word_list_missing_file_is_empty_and_warns(tmp_path: Path):
    from unittest.mock import patch

    missing = tmp_path / "nope.txt"
    # patch the module logger: caplog depends on logging config other tests change
    with patch("wyrdcraeft.services.markup.LOGGER") as logger:
        result = _load_folded_word_list(missing)

    assert result == frozenset()
    logger.warning.assert_called_once()
    assert missing in logger.warning.call_args.args


def test_load_folded_word_list_empty_file_is_empty(tmp_path: Path):
    words = tmp_path / "empty.txt"
    words.write_text("", encoding="utf-8")

    assert _load_folded_word_list(words) == frozenset()


def test_default_g_frontal_path_points_to_the_packaged_file():
    assert DEFAULT_G_FRONTAL_PATH.name == "frontal.txt"
    assert DEFAULT_G_FRONTAL_PATH.parent.name == "g"
    assert DEFAULT_G_FRONTAL_PATH.exists()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_markup.py -k "folded_word_list or default_g_frontal" -v`
Expected: FAIL at import time with `ImportError: cannot import name '_load_folded_word_list'`.

- [ ] **Step 3: Add the path constant**

In `wyrdcraeft/services/markup.py`, directly after `DEFAULT_C_FORCE_NON_PALATALIZE_PATH` add:

```python
#: Default list of words whose initial ``g`` stays velar before a front vowel.
DEFAULT_G_FRONTAL_PATH: Final[Path] = DEFAULT_DIACRITIC_DIR / "g" / "frontal.txt"
```

- [ ] **Step 4: Add the loader**

Directly after the `_fold` function add:

```python
def _load_folded_word_list(path: Path) -> frozenset[str]:
    """
    Load a one-word-per-line exception list, folded for comparison.

    Blank lines and ``#`` comment lines are skipped, a leading byte-order mark
    is ignored, and a trailing hyphen is dropped (``gǣst-`` means ``gǣst``)
    because palatalizers compare one dash-free segment at a time. A missing file
    logs a warning and gives an empty set.

    Args:
        path: Word list file.

    Returns:
        The folded words (see :func:`_fold`).

    """
    if not path.exists():
        LOGGER.warning("Exception list missing: %s", path)
        return frozenset()
    words: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        word = _fold(line.rstrip("-").strip())
        if word:
            words.add(word)
    return frozenset(words)
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_markup.py -v`
Expected: all PASS.

- [ ] **Step 6: Lint, type-check, commit**

```bash
.venv/bin/ruff format wyrdcraeft/services/markup.py tests/test_markup.py
.venv/bin/ruff check wyrdcraeft/services/markup.py tests/test_markup.py
.venv/bin/mypy wyrdcraeft/services/markup.py
git add wyrdcraeft/services/markup.py tests/test_markup.py
git commit -m "feat: add a folded word-list loader and the g/frontal.txt path

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Migrate the Python-only exceptions into `frontal.txt`

**Files:**
- Modify: `wyrdcraeft/etc/diacritic/g/frontal.txt` (append 43 lines plus a comment header)
- Test: `tests/test_markup.py`

**Interfaces:**
- Consumes: `_load_folded_word_list`, `DEFAULT_G_FRONTAL_PATH` from Task 1; `GPalatalizer.FRONTAL_G_EXCEPTIONS` and `_fold` (still present until Task 3).
- Produces: a `frontal.txt` that contains every word of today's hardcoded list.

> Confirm with the user before this task: it edits their hand-maintained file. They can prune afterwards. About six of the 43 are redundant because a `g` before a back vowel is never dotted anyway (`gaf`, `gafol`, `gafolgyld`, `galan`, `gangan`, `gār`, `gāt`); they are migrated anyway so the move is a faithful union.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_markup.py`:

```python
#: Every word in ``GPalatalizer.FRONTAL_G_EXCEPTIONS`` before it moved to a file.
OLD_FRONTAL_G_EXCEPTIONS = [
    "gǣl", "gǣf", "gǣfon", "gǣlscipe", "gǣng", "gǣnge", "gǣr", "gǣrlicgǣst",
    "gǣstas", "gǣsthus", "gǣstlic", "gǣstlīce", "gǣt", "gǣten", "gaf", "gafol",
    "gafolrǣden", "gafolgyld", "galan", "gangan", "gār", "gāt", "gēar", "gēara",
    "gēoguð", "geōguþ", "gēn", "gēna", "gēola", "gēol", "gēomor", "gēong",
    "gēongra", "gēs", "gēsne", "gēsnian", "gēsting", "gēstlīc", "gēsthus",
    "gēat", "gēatlic", "gēard", "gēatas", "gēatland",
]  # fmt: skip


def test_default_frontal_file_keeps_every_old_hardcoded_exception():
    from wyrdcraeft.services.markup import _fold

    in_file = _load_folded_word_list(DEFAULT_G_FRONTAL_PATH)

    missing = [w for w in OLD_FRONTAL_G_EXCEPTIONS if _fold(w) not in in_file]
    assert missing == []
    assert len(OLD_FRONTAL_G_EXCEPTIONS) == 44


def test_default_frontal_file_keeps_the_users_own_entries():
    in_file = _load_folded_word_list(DEFAULT_G_FRONTAL_PATH)

    assert {"gigant", "genesis", "gylden", "girwan", "gildas", "gǣst"} <= in_file
```

- [ ] **Step 2: Run the tests to verify the first one fails**

Run: `.venv/bin/python -m pytest tests/test_markup.py -k "default_frontal_file" -v`
Expected: `keeps_every_old_hardcoded_exception` FAILS with 43 words in `missing`; `keeps_the_users_own_entries` PASSES.

- [ ] **Step 3: Append the 43 words to the file**

Run this once (it appends a comment header and the words, and makes sure the file ends with a newline first):

```bash
python3 - <<'EOF'
from pathlib import Path

path = Path("wyrdcraeft/etc/diacritic/g/frontal.txt")
text = path.read_text(encoding="utf-8")
header = "# Migrated from GPalatalizer.FRONTAL_G_EXCEPTIONS (ADR 0015 follow-up).\n"
if header in text:
    raise SystemExit("already migrated; nothing to do")
if not text.endswith("\n"):
    text += "\n"
migrated = """gǣl gǣf gǣfon gǣlscipe gǣng gǣnge gǣr gǣrlicgǣst gǣstas gǣsthus gǣstlic
gǣstlīce gǣt gǣten gaf gafol gafolrǣden gafolgyld galan gangan gār gāt gēar
gēara gēoguð geōguþ gēn gēna gēola gēol gēomor gēong gēongra gēsne gēsnian
gēsting gēstlīc gēsthus gēat gēatlic gēard gēatas gēatland""".split()
assert len(migrated) == 43
text += header + "\n".join(migrated) + "\n"
path.write_text(text, encoding="utf-8")
EOF
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_markup.py -v`
Expected: all PASS (including the two new tests and every existing `GPalatalizer` test, which still uses the Python list at this point).

- [ ] **Step 5: Commit**

```bash
git add wyrdcraeft/etc/diacritic/g/frontal.txt tests/test_markup.py
git commit -m "data: migrate the hardcoded g exceptions into g/frontal.txt

The 43 words that were only in GPalatalizer.FRONTAL_G_EXCEPTIONS are appended
so switching the code to read the file loses no protection.

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 3: `GPalatalizer` reads the file; remove the hardcoded list

**Files:**
- Modify: `wyrdcraeft/services/markup.py` (class `GPalatalizer`)
- Test: `tests/test_markup.py`

**Interfaces:**
- Consumes: `DEFAULT_G_FRONTAL_PATH`, `_load_folded_word_list`, `_fold` from Tasks 1-2.
- Produces:
  - `GPalatalizer.__init__(self, frontal_path: Path = DEFAULT_G_FRONTAL_PATH)`
  - instance attributes `frontal_exceptions: frozenset[str]` and `ending_exceptions: frozenset[str]`
  - `GPalatalizer.FRONTAL_G_EXCEPTIONS` is **removed**.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_markup.py`:

```python
def test_g_palatalizer_reads_its_exceptions_from_the_given_file(tmp_path: Path):
    words = tmp_path / "frontal.txt"
    words.write_text("# comment\nGildas\ngǣst-\n", encoding="utf-8")
    palatalizer = GPalatalizer(frontal_path=words)

    assert palatalizer.palatalize("Gildas") == "Gildas"
    assert palatalizer.palatalize("gǣst") == "gǣst"
    # an entry exempts only that exact word, not longer words
    assert palatalizer.palatalize("gǣstas") == "ġǣstas"
    # a hyphenated token is exempted through its dash-free segment
    assert palatalizer.palatalize("gǣst-hūs") == "gǣst-hūs"
    # words not in this file lose the protection the old list gave
    assert palatalizer.palatalize("gēar") == "ġēar"


def test_g_palatalizer_with_an_empty_file_has_no_frontal_exceptions(tmp_path: Path):
    words = tmp_path / "empty.txt"
    words.write_text("", encoding="utf-8")

    assert GPalatalizer(frontal_path=words).palatalize("gēar") == "ġēar"


def test_g_palatalizer_default_file_applies_the_users_own_entries():
    palatalizer = GPalatalizer()

    assert palatalizer.palatalize("gigant") == "gigant"
    assert palatalizer.palatalize("Gildas") == "Gildas"
    assert palatalizer.palatalize("gylden") == "gylden"


def test_g_palatalizer_default_file_keeps_the_old_protection():
    palatalizer = GPalatalizer()

    for word in ("gēar", "gēat", "gǣt", "gēn", "gǣl", "gēs"):
        assert palatalizer.palatalize(word) == word


def test_g_palatalizer_ending_exceptions_still_apply():
    palatalizer = GPalatalizer()

    assert palatalizer.palatalize("plǣg") == "plǣg"
    assert palatalizer.palatalize("sweg") == "sweg"


def test_g_palatalizer_no_longer_has_a_hardcoded_frontal_list():
    assert not hasattr(GPalatalizer, "FRONTAL_G_EXCEPTIONS")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_markup.py -k "g_palatalizer" -v`
Expected: FAIL (`TypeError: GPalatalizer() takes no arguments` and the `hasattr` test).

- [ ] **Step 3: Remove the hardcoded list**

Delete from `class GPalatalizer` the attribute `FRONTAL_G_EXCEPTIONS` including its `#:` comment. Anchors: it starts at the line `    #: Words that seem like they should have a palatalized ``g``, but do not.` and ends at the closing `    ]` of the list, directly before `    #: Ending palatalized-g exceptions.`. Use this to do it exactly:

```bash
python3 - <<'EOF'
from pathlib import Path

path = Path("wyrdcraeft/services/markup.py")
text = path.read_text(encoding="utf-8")
start = text.index("    #: Words that seem like they should have a palatalized ``g``, but do not.")
end = text.index("    #: Ending palatalized-g exceptions.")
path.write_text(text[:start] + text[end:], encoding="utf-8")
EOF
```

Check: `grep -n "FRONTAL_G_EXCEPTIONS" wyrdcraeft/services/markup.py` must now only show the two places fixed in the next steps.

- [ ] **Step 4: Add `__init__` and replace the two properties**

In `class GPalatalizer`, add `__init__` right after the class attributes (after `BACK_VOWELS`):

```python
    def __init__(self, frontal_path: Path = DEFAULT_G_FRONTAL_PATH) -> None:
        """
        Load the frontal exception list.

        Args:
            frontal_path: File of words whose initial ``g`` stays velar before
                a front vowel, one per line (``#`` comments allowed).

        """
        #: Folded words whose initial ``g`` stays velar before a front vowel.
        self.frontal_exceptions: frozenset[str] = _load_folded_word_list(
            frontal_path
        )
        #: Folded words whose final ``g`` stays velar after a front vowel.
        self.ending_exceptions: frozenset[str] = frozenset(
            _fold(word) for word in self.ENDING_G_EXCEPTIONS
        )
```

Delete the two `@property` methods `_frontal_exceptions` and `_ending_exceptions` entirely (they sit at the end of the class, right before `def _possible_pre_iumlaut_sources`, which must stay). In `_is_palatal`, replace `self._frontal_exceptions` with `self.frontal_exceptions` and `self._ending_exceptions` with `self.ending_exceptions`.

The project's napoleon gate requires a class with constructor arguments to document them in the class docstring, so replace the class docstring of `GPalatalizer` with:

```python
    """
    Palatalize ``g`` in a single lexical token.

    Args:
        frontal_path: File of words whose initial ``g`` stays velar before a
            front vowel, one per line (``#`` comments allowed).

    """
```

- [ ] **Step 5: Run the tests**

Run: `.venv/bin/python -m pytest tests/test_markup.py tests/test_cli_mark_diacritics.py -v`
Expected: all PASS, including the existing tests `test_g_palatalizer_handles_compounds_and_exceptions` (`gēar` stays `gēar`), `test_g_palatalizer_ges_exception`, `test_g_palatalizer_velar_before_back_vowel_and_folded_exceptions` (`gēoguð` and `gēoguþ` stay unchanged through the folded file entries).

- [ ] **Step 6: Lint, type-check, napoleon gate**

```bash
.venv/bin/ruff format wyrdcraeft/services/markup.py tests/test_markup.py
.venv/bin/ruff check wyrdcraeft/services/markup.py tests/test_markup.py
.venv/bin/mypy wyrdcraeft/services/markup.py
make napoleon-gate
```
Expected: ruff and mypy clean for these files; `make napoleon-gate` still reports exactly the baseline (94 total against 95 baseline keys), no new violations. (Removing the two properties removes two docstrings, so the count may only go down.)

- [ ] **Step 7: Docs and commit**

In `docs/adr/0015-mark-diacritics-is-additive-transfer.md`, first fix the now-stale bullet "Exception lists are folded, not normalized": replace the words `` `FRONTAL_G_EXCEPTIONS` and\n  `ENDING_G_EXCEPTIONS` compare with NFC, lowercase and ð≡þ.`` with ``The frontal exceptions (read from\n  `g/frontal.txt`) and `ENDING_G_EXCEPTIONS` compare with NFC, lowercase and ð≡þ.``. Then rename the section `## Proposed follow-up (not implemented): `GPalatalizer` reads `g/frontal.txt`` to `## Follow-up (implemented): `GPalatalizer` reads `g/frontal.txt``, and remove the bullet in `## Not changed / known gaps` that says `g/frontal.txt` is not read by any code. In `doc/source/changelog.rst` under `Unreleased` → `Bugfixes` add (and do **not** `git add` this file, it holds the user's own uncommitted release notes; say so in the hand-off):

```rst
- ``wyrdcraeft source mark-diacritics`` now reads the ``g`` exceptions from ``wyrdcraeft/etc/diacritic/g/frontal.txt`` instead of a hardcoded list, so edits to that file take effect.
```

In `docs/context/diacritic.md`, under `Inputs:`, add the bullet:

```markdown
- hand-edited palatalization exception lists under `wyrdcraeft/etc/diacritic/`
  (`c_palatalization_*.txt` and `g/frontal.txt`)
```

Then:

```bash
.venv/bin/python -m pytest tests -q -p no:cacheprovider
graphify update .
git add wyrdcraeft/services/markup.py tests/test_markup.py docs/adr/0015-mark-diacritics-is-additive-transfer.md docs/context/diacritic.md
git commit -m "refactor: GPalatalizer reads its frontal exceptions from g/frontal.txt

The hardcoded list is removed; the 43 words that only it held were migrated
into the file first, so no existing exception is lost.

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```
Expected: the full suite PASSES.

---

## Self-Review

- **Spec coverage (ADR 0015 follow-up):** load from the file (Tasks 1 and 3), remove the hardcoded list (Task 3 Step 3), migrate the 43 missing words first (Task 2), comments/blank lines/fold/trailing hyphen (Task 1), `ENDING_G_EXCEPTIONS` out of scope and kept (Task 3 `ending_exceptions`, tested), the user's 21 extra entries now apply (Task 3 test), docs (Task 3 Step 7, including the stale ADR bullet).
- **Placeholder scan:** none; every step has its full code, command or data.
- **Type consistency:** `_load_folded_word_list`, `DEFAULT_G_FRONTAL_PATH`, `frontal_exceptions`, `ending_exceptions` are named identically in all three tasks.
- **Review Focus:** empty file (Task 1 and Task 3 tests), capitals and spaces (`  Gildas  ` in Task 1; `Gildas` in Task 3), hyphenated token (`gǣst-hūs`), prefix entry not exempting longer word (`gǣstas`), old protections (`gēar`, `gēat`, `gǣt`, `gēn`), lone `-` line (Task 1 test file contains `-` and `#-`).
