# Ambiguity Collapses on Marks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `source mark-diacritics` stops treating an ambiguous key as ambiguous when every option has the same letters and marks (differing only in hyphens, case, eth/thorn or BT diphthong style): it applies the marks and writes no ambiguity row. `diacritic-disambiguate` stops queueing such keys.

**Architecture:** One pure predicate on `DiacriticTransfer` (`same_marks(forms)`, built on the existing `mark_pattern`) decides whether options agree. `MacronIndex` gains `ambiguous_completed` so the applicator can protect curated keys. `MacronApplicator.apply` resolves a collapsing, non-curated ambiguous key through the same transfer path as a unique key. The `diacritic-disambiguate` queue filters with the same predicate. The index file is never rewritten.

**Tech Stack:** Python dataclasses, pydantic payload, click `CliRunner`, pytest.

**Spec:** [ADR 0019](../../adr/0019-ambiguity-is-judged-on-marks-and-resolved-by-policy.md), decisions 2, 5 and 7 (the part of 7 that needs no standard-element list), plus the Consequence "`MacronIndex` must carry `ambiguous_completed`". Depends on [ADR 0020](../../adr/0020-diacritic-transfer-treats-a-diphthong-as-one-unit.md) (`mark_pattern`, already implemented).

## Scope: what this plan does not do

ADR 0019 is too big for one plan. This is the first slice, the one that needs no new data and no judgement call. Left for later plans, each a separate change:

- **Decision 3, standard element forms** (`a-`, `for-`, `fore-`, `ge-`, `bonde`, `hīrēd-`, `bēacen-`, `ōþ-`): a data file, hyphen evidence from BT forms, and standardizing unique forms too (823 `ā-` forms lose a mark). It extends the collapse in this plan and the queue skip in Task 2.
- **Decision 4, `--ambiguity-policy auto|leave|union`** and decision 6 (guessed tokens stay in the report with the form written and the policy). Needs the standard-element list for its prefix guard, and the report model gains fields.
- **Decision 8, the labeled-decisions acceptance fixture**, which exists to measure `auto`.

Until those land, an ambiguous key that does not collapse behaves exactly as today.

## Global Constraints

- Compare options with `DiacriticTransfer.mark_pattern` only. No new rule: letters and diphthong-canonical marks, ignoring hyphens, case and `ð`/`þ` (ADR 0019 decision 2).
- This is a runtime rule. Do not rewrite the `ambiguous` list in any index file and do not touch `wyrdcraeft/etc/diacritic/oe_bt_macron_index.json` (ADR 0016: the index is curated data).
- A key in `ambiguous_completed` never collapses (decision 5). The user decided it is genuinely ambiguous.
- Additive only (ADR 0015): nothing is removed or replaced in the source.
- Methods ≤ 60 lines; Napoleon docstrings with `Keyword Args:` for kw-only arguments; `#:` comments on dataclass attributes. `make napoleon-gate` must stay at the 94-violation baseline; `mypy` keeps its one pre-existing error at `wyrdcraeft/cli/cli.py:107`.
- Do not stage `doc/source/changelog.rst`, `uv.lock`, `wyrdcraeft/etc/dictionary/oe_bt.json` or `graphify-out/`.
- Do not run `ruff format` on the whole `wyrdcraeft/cli` directory (it reformats `cli.py`); name files.
- Test command: `.venv/bin/python -m pytest`.

## Rulings to confirm (made while planning)

- **A completed key never collapses**, even when its options agree on marks. Two completed keys do collapse by marks today. The user marked them completed on purpose, so the safe reading of decision 5 is "hands off". Cost if wrong: two tokens stay in the ambiguity report.
- **The first option is the one transferred.** All options share letters and marks, so any one gives the same result; the first is deterministic.
- **`diacritic-disambiguate KEY` still opens a collapsing key.** Only the no-argument queue skips them. An explicit key is an explicit request.
- **The queue prints how many keys it skipped**, so a shorter queue is not a silent change.
- **No change to the report models.** A collapsed token produces no ambiguity row, which is the intended behavior in decision 2.

## Review Focus

- A source token in decomposed (NFD) input on a collapsing key must still be marked, with its own letters untouched. Task 1.
- A source that already carries the marks, or a case-only difference (`Cuslyppe`), must come out additive and case-preserved. Task 1.
- A key whose options differ in marks (`ac`/`āc`) stays ambiguous and unchanged. Task 1.
- A completed key whose options agree on marks stays ambiguous. Task 1.
- A key whose only options are one entry (a one-element `ambiguous` list, which the validator allows) must not crash or collapse oddly. Task 1.
- `diacritic-disambiguate` with no argument must not list a collapsing key but must still list a non-collapsing one; with an explicit key it must still open it. Task 2.

---

### Task 1: `same_marks`, `ambiguous_completed` on `MacronIndex`, and the collapse in `apply`

**Files:**
- Modify: `wyrdcraeft/services/markup.py` (`DiacriticTransfer.same_marks` after `mark_pattern`; `MacronApplicator.load_index`; `MacronApplicator.apply`, split)
- Modify: `wyrdcraeft/models/macron_index.py`
- Test: `tests/test_markup.py`

**Interfaces:**
- Consumes: `DiacriticTransfer.mark_pattern(form: str) -> tuple[tuple[str, frozenset[str]], ...]`, `DiacriticTransfer.transfer(source: str, marked: str) -> str | None`.
- Produces:
  - `DiacriticTransfer.same_marks(forms: Iterable[str]) -> bool`: `True` when `forms` is non-empty and every form has the same mark pattern. Task 2 imports it.
  - `MacronIndex.ambiguous_completed: frozenset[str]`, default `frozenset()`.
  - `MacronApplicator._ambiguity_row(word, normalized, line_number, word_number) -> MacronAmbiguity` (the existing row-building block, extracted unchanged).
  - `MacronApplicator._collapsed_form(normalized: str) -> str | None`: the form to transfer when the key is ambiguous, not completed and its options agree on marks, else `None`.
  - `apply` keeps its 4-tuple return.

- [ ] **Step 1: Write the failing tests**

In `tests/test_markup.py`, extend `_write_index` with a keyword argument and write it out (existing callers are unaffected):

```python
def _write_index(
    path: Path,
    *,
    unique: dict[str, str],
    ambiguous: dict[str, list[str]],
    ambiguous_metadata: dict[str, dict[str, dict[str, str]]] | None = None,
    ambiguous_completed: list[str] | None = None,
) -> None:
    payload = {
        "unique": unique,
        "ambiguous": ambiguous,
        "ambiguous_completed": ambiguous_completed or [],
        "ambiguous_metadata": ambiguous_metadata or {},
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
```

Append these tests:

```python
@pytest.mark.parametrize(
    ("forms", "expected"),
    [
        (["ǣwisc-nys", "ǣwiscnys"], True),
        (["leāst", "lēast"], True),
        (["þēod-ne", "ðēodne"], True),
        (["cū-slyppe", "Cūslyppe"], True),
        (["ac", "āc"], False),
        (["wegas", "wēgas"], False),
        (["ǣwiscnys"], True),
        ([], False),
    ],
)
def test_same_marks(forms, expected):
    assert DiacriticTransfer.same_marks(forms) is expected


def test_macron_index_carries_completed_keys(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(
        index_path,
        unique={},
        ambiguous={"ac": ["ac", "āc"]},
        ambiguous_completed=["ac"],
    )

    assert MacronApplicator(index_path).index.ambiguous_completed == frozenset({"ac"})


@pytest.mark.parametrize(
    ("options", "word", "expected"),
    [
        (["ǣwisc-nys", "ǣwiscnys"], "æwiscnys", "ǣwiscnys"),
        (["cū-slyppe", "cūslyppe"], "Cuslyppe", "Cūslyppe"),
        (["þēod-ne", "ðēodne"], "ðeodne", "ðēodne"),
        (["leāst", "lēast"], "least", "lēast"),
        (["cū-slyppe", "cūslyppe"], "cūslyppe", "cūslyppe"),
    ],
)
def test_apply_collapses_options_that_agree_on_marks(
    tmp_path: Path, options, word, expected
):
    index_path = tmp_path / "index.json"
    key = normalize_old_english(options[0])
    _write_index(index_path, unique={}, ambiguous={key: options})

    marked, ambiguity, is_unknown, unaligned = MacronApplicator(index_path).apply(
        word, line_number=1, word_number=1
    )

    assert marked == expected
    assert ambiguity is None
    assert is_unknown is False
    assert unaligned is None


def test_apply_collapse_keeps_decomposed_source_letters(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(
        index_path, unique={}, ambiguous={"cuslyppe": ["cū-slyppe", "cūslyppe"]}
    )
    # The source already has a dot on the c, written as c + combining dot.
    source = unicodedata.normalize("NFD", "ċuslyppe")

    marked, ambiguity, _, _ = MacronApplicator(index_path).apply(
        source, line_number=1, word_number=1
    )

    assert ambiguity is None
    assert unicodedata.normalize("NFC", marked) == "ċūslyppe"


def test_apply_keeps_ambiguity_when_options_differ_in_marks(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(index_path, unique={}, ambiguous={"ac": ["ac", "āc"]})

    marked, ambiguity, _, _ = MacronApplicator(index_path).apply(
        "ac", line_number=1, word_number=1
    )

    assert marked == "ac"
    assert ambiguity is not None


def test_apply_never_collapses_a_completed_key(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(
        index_path,
        unique={},
        ambiguous={"cuslyppe": ["cū-slyppe", "cūslyppe"]},
        ambiguous_completed=["cuslyppe"],
    )

    marked, ambiguity, _, _ = MacronApplicator(index_path).apply(
        "cuslyppe", line_number=1, word_number=1
    )

    assert marked == "cuslyppe"
    assert ambiguity is not None


def test_apply_single_option_ambiguous_key_marks_it(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(index_path, unique={}, ambiguous={"cild": ["cīld"]})

    marked, ambiguity, _, _ = MacronApplicator(index_path).apply(
        "cild", line_number=1, word_number=1
    )

    assert marked == "cīld"
    assert ambiguity is None


def test_restorer_marks_collapsed_token_and_reports_nothing(tmp_path: Path):
    index_path = tmp_path / "index.json"
    _write_index(
        index_path,
        unique={},
        ambiguous={"cuslyppe": ["cū-slyppe", "cūslyppe"], "ac": ["ac", "āc"]},
    )

    result = DiacriticRestorer(macron_index_path=index_path).restore_text(
        "Cuslyppe ac\n"
    )

    assert result.marked_text == "Cūslyppe ac\n"
    assert [a.word for a in result.ambiguities] == ["ac"]
    assert result.unknowns == []
    assert result.unaligned == []
```

Add `import unicodedata` to the test file's imports (after `import json`).

Ruling inside the tests: `test_apply_single_option_ambiguous_key_marks_it` pins the one-element case. A one-element list collapses trivially (one pattern), so it is marked. `same_marks([])` is `False` so an empty list never collapses.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_markup.py -k "same_marks or completed or collapses or collapse_keeps or differ_in_marks or single_option or restorer_marks_collapsed" -v`
Expected: `test_same_marks` cases FAIL (`same_marks` not defined). The `completed_keys` test FAILS (no attribute). The `collapses`, `decomposed`, `single_option` and `restorer_marks_collapsed` tests FAIL (token returned unchanged with an ambiguity row). `differ_in_marks` and `never_collapses_a_completed_key` PASS already (they pin behavior that must not change; a pass now is correct).

- [ ] **Step 3: Write the implementation**

`wyrdcraeft/models/macron_index.py`, add after `ambiguous_metadata`:

```python
    #: Ambiguous keys the user decided are genuinely ambiguous; never auto-resolved.
    ambiguous_completed: frozenset[str] = frozenset()
```

`wyrdcraeft/services/markup.py`:

1. In `load_index`, pass `ambiguous_completed=frozenset(payload.ambiguous_completed)` to `MacronIndex(...)`. The builder's `MacronIndex(...)` near line 596 needs no change (the field has a default).

2. After `DiacriticTransfer.mark_pattern`, add (import `Iterable` under `TYPE_CHECKING` if the module already uses that block, else from `collections.abc`; follow the module's existing import style):

```python
    @classmethod
    def same_marks(cls, forms: Iterable[str]) -> bool:
        """
        Tell whether every form has the same letters and marks.

        Hyphens, case, ``ð``/``þ`` and diphthong marking style do not count
        (see :meth:`mark_pattern`).

        Args:
            forms: Index display forms for one key.

        Returns:
            ``True`` when ``forms`` is non-empty and all share one mark pattern.

        """
        patterns = {cls.mark_pattern(form) for form in forms}
        return len(patterns) == 1
```

3. In `MacronApplicator`, split `apply`. Move the row-building block (from `raw_options = self.index.ambiguous[normalized]` through the `ambiguity = MacronAmbiguity(...)` construction and its `LOGGER.debug`) into:

```python
    def _ambiguity_row(
        self, word: str, normalized: str, line_number: int, word_number: int
    ) -> MacronAmbiguity:
        """
        Build the ambiguity report row for a token whose key is ambiguous.

        Args:
            word: Verbatim lexical token.
            normalized: Normalized key, present in ``index.ambiguous``.
            line_number: 1-based line number.
            word_number: 1-based lexical token number within line.

        Returns:
            Row listing every option with its part of speech and meanings.

        """
```

Copy the moved body exactly as it is now, ending `return ambiguity`. Then add:

```python
    def _collapsed_form(self, normalized: str) -> str | None:
        """
        Pick the form to apply when an ambiguous key is not really ambiguous.

        A key collapses when every option has the same letters and marks
        (ADR 0019). A key the user marked completed never collapses.

        Args:
            normalized: Normalized key, present in ``index.ambiguous``.

        Returns:
            The first option when the options agree on marks, else ``None``.

        """
        options = self.index.ambiguous[normalized]
        if normalized in self.index.ambiguous_completed:
            return None
        if not DiacriticTransfer.same_marks(options):
            return None
        return options[0]
```

In `apply`, replace the old ambiguous block and the `marked = self.index.unique.get(normalized)` line with:

```python
        marked = self.index.unique.get(normalized)
        if normalized in self.index.ambiguous:
            marked = self._collapsed_form(normalized)
            if marked is None:
                ambiguity = self._ambiguity_row(
                    word, normalized, line_number, word_number
                )
                return word, ambiguity, False, None
        if marked is None:
            ...  # the existing no-match branch, unchanged
```

Keep the rest of `apply` (the no-match branch, the `transfer` call, the unaligned branch, the success branch) unchanged. Extend the `apply` docstring: "An ambiguous key whose options all share one mark pattern is applied like a unique key and writes no ambiguity row." If `apply` is still over 60 lines, move the unaligned/success tail into `_transfer_logged(word, marked, line_number, word_number)` the same way; do not leave it over.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_markup.py tests/test_cli_mark_diacritics.py -v`
Expected: all pass. If a `test_cli_mark_diacritics.py` test fails because it used a key whose options differ only in hyphens or case and expected an ambiguity row, check that the key really collapses; if so, change that test's options to ones that differ in marks (`["ac", "āc"]`) and ledger it as a ruling. Otherwise stop and investigate.

- [ ] **Step 5: Real-index check, quality gate and commit**

Run:

```bash
.venv/bin/python - <<'E'
from wyrdcraeft.services.markup import MacronApplicator
idx = MacronApplicator().index
keys = [k for k, v in idx.ambiguous.items() if k not in idx.ambiguous_completed]
from wyrdcraeft.services.markup import DiacriticTransfer as T
print(sum(T.same_marks(idx.ambiguous[k]) for k in keys), "of", len(keys))
E
.venv/bin/ruff format wyrdcraeft/services/markup.py wyrdcraeft/models/macron_index.py tests/test_markup.py
.venv/bin/ruff check wyrdcraeft/services/markup.py wyrdcraeft/models/macron_index.py tests/test_markup.py
.venv/bin/mypy wyrdcraeft/services/markup.py wyrdcraeft/models/macron_index.py
```

Expected: the script prints `143 of 889` (145 collapse by marks, 2 of them completed; ADR 0019 says 142 for "letters-only differences", which counts a slightly different set, so the figure is a sanity check, not a contract: ledger a different number rather than failing). Ruff clean; mypy only the pre-existing `cli.py:107` error.

```bash
git add wyrdcraeft/services/markup.py wyrdcraeft/models/macron_index.py tests/test_markup.py
git commit -m "feat: mark-diacritics applies marks when every ambiguous option agrees on them"
```

(End the message with the Co-Authored-By line from the session's attribution rule.)

---

### Task 2: `diacritic-disambiguate` skips collapsing keys; docs and ADR note

**Files:**
- Modify: `wyrdcraeft/cli/diacritic_disambiguate.py` (import near line 25; the no-argument branch near line 472)
- Modify: `doc/source/overview/command_convert_mark_diacritics.rst`, `doc/source/overview/command_diacritic_disambiguate.rst`, `docs/context/diacritic.md`, `CONTEXT.md`
- Modify: `docs/adr/0019-ambiguity-is-judged-on-marks-and-resolved-by-policy.md` (note only; status stays `proposed`)
- Test: `tests/test_cli_diacritic_disambiguate.py`

**Interfaces:**
- Consumes: `DiacriticTransfer.same_marks(forms: Iterable[str]) -> bool` from Task 1.
- Produces: nothing later tasks use. The skip is the one place the queue and the applicator must agree, so both call `same_marks`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_cli_diacritic_disambiguate.py` (reuse `_write_index`, `runner`, `temp_dir`, the autouse BT mock):

```python
def _collapsing_index(path, *, completed=()):
    _write_index(
        path,
        {
            "meta": {"unique_count": 0, "ambiguous_count": 2},
            "unique": {},
            "ambiguous": {
                "ac": ["ac", "āc"],
                "cuslyppe": ["cū-slyppe", "cūslyppe"],
            },
            "ambiguous_completed": list(completed),
            "ambiguous_metadata": {},
        },
    )


def _run_queue(runner, index_path, monkeypatch, *args):
    # ``print_info`` writes to a stderr console bound at import time, which
    # CliRunner does not capture, so record the messages directly.
    messages: list[str] = []
    monkeypatch.setattr(diacritic_disambiguate_module, "print_info", messages.append)
    result = runner.invoke(
        cli,
        ["diacritic", "disambiguate", *args, "--index-path", str(index_path)],
        input="q\n",
    )
    return result, messages


def test_diacritic_disambiguate_queue_skips_keys_that_collapse(
    runner, temp_dir, monkeypatch
):
    index_path = temp_dir / "index.json"
    _collapsing_index(index_path)

    result, messages = _run_queue(runner, index_path, monkeypatch)

    assert result.exit_code == 0, result.output
    assert "cū-slyppe" not in result.output
    assert any(m.startswith("Skipped 1 entries") for m in messages)


def test_diacritic_disambiguate_queue_does_not_count_a_completed_key_as_skipped(
    runner, temp_dir, monkeypatch
):
    index_path = temp_dir / "index.json"
    _collapsing_index(index_path, completed=["cuslyppe"])

    result, messages = _run_queue(runner, index_path, monkeypatch)

    assert result.exit_code == 0, result.output
    assert not any(m.startswith("Skipped") for m in messages)


def test_diacritic_disambiguate_explicit_collapsing_key_still_opens(
    runner, temp_dir, monkeypatch
):
    index_path = temp_dir / "index.json"
    _collapsing_index(index_path)

    result, _ = _run_queue(runner, index_path, monkeypatch, "cuslyppe")

    assert result.exit_code == 0, result.output
    assert "cū-slyppe" in result.output
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_cli_diacritic_disambiguate.py -k "queue_skips or completed_key_as_skipped or explicit_collapsing" -v`
Expected: `queue_skips` FAILS (the queue shows `cuslyppe`, no "Skipped" message). `not_count_a_completed_key` and `explicit_collapsing` PASS already (they pin behavior that must not change).

- [ ] **Step 3: Write the implementation**

Change the import to `from ..services.markup import DEFAULT_MACRON_INDEX_PATH, DiacriticTransfer`.

In the `else:` branch that builds `target_keys` (near line 472), replace the list with:

```python
        pending = sorted(
            key for key in payload.ambiguous if key not in payload.ambiguous_completed
        )
        target_keys = [
            key
            for key in pending
            if not DiacriticTransfer.same_marks(payload.ambiguous[key])
        ]
        if len(pending) > len(target_keys):
            print_info(
                f"Skipped {len(pending) - len(target_keys)} entries whose options "
                "differ only in hyphens, case, eth/thorn or diphthong marking."
            )
```

Leave the `if not target_keys:` message and everything after it unchanged. `diacritic_disambiguate` already carries `# noqa: PLR0912, PLR0915`; do not add logic beyond this block.

- [ ] **Step 4: Run the tests, then the whole file**

Run: `.venv/bin/python -m pytest tests/test_cli_diacritic_disambiguate.py tests/test_cli_diacritic.py -v`
Expected: all pass. Existing tests that put keys with agreeing options in the queue (check any using `["…-…", "…"]` pairs) need the options changed to differ in marks; ledger it as a ruling if any does.

- [ ] **Step 5: Docs, ADR note, quality gate, full suite, commit**

- `doc/source/overview/command_convert_mark_diacritics.rst`: in the lookup steps (near line 87, "if key in `ambiguous`: keep source token…") say that an ambiguous key whose options all have the same letters and marks, ignoring hyphens, case, eth/thorn and diphthong style, is applied like a unique key and writes no ambiguity row, and that a key marked completed is never treated this way. Adjust the ambiguity-report sentence (near line 54) to say "multiple valid macron candidates that differ in their marks".
- `doc/source/overview/command_diacritic_disambiguate.rst`: one sentence that the no-argument queue skips such keys and prints how many, and that an explicit KEY still opens one.
- `docs/context/diacritic.md`: add one bullet under the invariants list (near line 57) with both facts.
- `CONTEXT.md`: add a glossary term "collapsing ambiguity: an ambiguous key whose options all share one mark pattern; applied like a unique key" in the diacritic block (near line 115). Glossary only, no implementation detail.
- `docs/adr/0019-…md`: change "Nothing here is implemented yet." to "Decisions 2 and 5, and the queue skip of decision 7, are implemented; decisions 3, 4, 6 and 8 are not." and append an "Implementation notes" section: a completed key never collapses (two completed keys would otherwise), the first option is transferred, an explicit `disambiguate KEY` still opens a collapsing key, the queue prints the skip count, and the measured count on the packaged index (use the real number from Task 1 Step 5). Status stays `proposed`.

Run:

```bash
.venv/bin/ruff format wyrdcraeft/cli/diacritic_disambiguate.py tests/test_cli_diacritic_disambiguate.py
.venv/bin/ruff check wyrdcraeft/cli/diacritic_disambiguate.py tests/test_cli_diacritic_disambiguate.py
.venv/bin/mypy wyrdcraeft/cli/diacritic_disambiguate.py
make napoleon-gate
.venv/bin/python -m pytest -q
```

Expected: ruff clean on the touched files (the 43 older errors elsewhere in `wyrdcraeft/cli` and `tests` are pre-existing; `ruff format` on this file may join a few unrelated lines, so check the diff and revert noise); mypy only the pre-existing `cli.py:107` error; napoleon gate at the 94 baseline; full suite green (1,167 before plus the new tests; report the real number).

```bash
git add wyrdcraeft/cli/diacritic_disambiguate.py tests/test_cli_diacritic_disambiguate.py
git add -u doc/source docs/context CONTEXT.md docs/adr -- ':!doc/source/changelog.rst'
git commit -m "feat: disambiguate skips keys whose options agree on marks"
```

(End the message with the Co-Authored-By line from the session's attribution rule.)
