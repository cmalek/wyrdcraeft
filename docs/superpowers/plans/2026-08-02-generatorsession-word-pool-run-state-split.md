# GeneratorSession → WordPool + GenerationRunState Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate `GeneratorSession`'s god-object coupling (176 graph edges,
the most-connected symbol in the repo) by splitting it into two focused
collaborators — `WordPool` (categorized word lists + supporting dictionaries)
and `GenerationRunState` (cross-stage scalar run state) — and migrating every
direct `session.<attr>` touch site onto the narrower collaborator it actually
needs, while preserving byte-for-byte output parity with the existing Perl
translation.

**Architecture:** This is candidate #1 from the 2026-08-01 architecture review
(`docs/adr/0008-architecture-review-2026-08-01.md`). Investigation (this
session, via a full-repo inventory of every `session.<attr>` touch site —
saved at `.superpowers/sdd/generatorsession-inventory.md`) found
`GeneratorSession` conflates two different kinds of state:

1. **Word-pool data** — `words`, `manual_forms`, `verb_paradigms`, `prefixes`,
   `adjectives`, `nouns`, `verbs`. This is what assigners and generators
   mostly *read* and occasionally *recategorize*.
2. **Cross-stage scalar run state** — `output_counter`, `perl_probability`,
   `enable_num_probability_carry`, `enable_r_stem_nouns`. This is genuinely
   shared mutable state *by design*: `adj_forms.py` sets
   `enable_num_probability_carry` for `num_forms.py` to read later in the same
   run; every sink increments `output_counter` and every stage reports it to
   progress. This matches the "per-run orchestration + mutable run state"
   pattern `AGENTS.md` already blesses (`ExtractionOrchestrator`/`RunStats`) —
   it should not be flattened into per-call arguments.

The fix: `GeneratorSession` becomes a thin composition of `WordPool` +
`GenerationRunState`, keeping its existing 11 attributes as forwarding
properties (get **and** set) so the migration can land incrementally without
breaking every caller in one commit. Each subsequent task then migrates one
bounded layer of the codebase off `session: GeneratorSession` parameters and
onto `word_pool: WordPool` / `run_state: GenerationRunState` parameters,
verified against the existing golden-snapshot parity tests after every task.

**Critical context from the codebase owner:** this code is a near-direct
Python translation of a Perl generator
(https://github.com/madeleineth/tichy_oe_generator) and intentionally retains
much of the original Perl's shape because output parity was paramount. The
owner is willing to refactor toward clean architecture but **output parity
must be preserved exactly** — this is not negotiable and is the reason every
task below ends with the same non-negotiable verification step.

**Tech Stack:** Python 3, pytest, ruff, mypy, graphify (static import/coupling
analysis, already installed at `graphify-out/`).

**Task dependency order (bottom-up, each depends on the previous):**
Task 1 (seam) → Task 2 (assigners, independent of generators) → Task 3
(shared sink/row-emission leaf layer — every one of the 5 generation paths
calls into this) → Tasks 4-7 (one PoS generator each, in increasing size/risk
order: adverbs → numerals → nouns → adjectives) → Task 8 (verb path, the
deepest-threaded) → Task 9 (final orchestration cleanup + remaining tests).

## Global Constraints

- **Parity gate (non-negotiable, every task):** after each task's code
  changes, run:
  ```bash
  .venv/bin/pytest tests/morphology/test_full_flow_reference.py tests/morphology/test_paradigm_reference.py tests/morphology/test_preprocess_reference.py -v
  ```
  Every test must PASS with **zero** diff. These tests SHA256-hash
  canonicalized generation output against golden snapshots
  (`tests/morphology/data/full_flow_subset.jsonl.gz`,
  `full_flow_full_smoke.jsonl.gz`). A single differing byte in emitted output
  is a hard stop — do not proceed to the next task, and do not "fix" a
  snapshot mismatch by regenerating the snapshot; find and fix the behavior
  regression instead.
- **Full suite, every task:** `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q` must pass with the same pass count as before the task (no new failures, no newly-skipped tests).
- **Any remaining old-signature caller shows up as `TypeError`/`AttributeError` at test time** — Python does not silently accept a mismatched call. If the whole-suite run in a task's last step raises either, grep the traceback's file for the migrated function/attribute name and fix that call site before proceeding; do not special-case or skip the failing test.
- Post-implementation quality gate (Python files only, from `AGENTS.md`): `ruff check` on touched files, `.venv/bin/mypy` on touched files, `make napoleon-gate` — fix all reported problems before finishing each task.
- No monkey-patching, runtime patching, or indirection to dodge parity or doc-gate friction — fix the root cause in the correct source file.
- Keep every existing napoleon-style `#:` attribute docstring and `Args:`/`Keyword Args:`/`Side Effects:` docstring section intact on any function whose signature changes — update the parameter name/description in the docstring to match the new signature, do not delete the section.
- After all 9 tasks: run `graphify update .` and confirm `GeneratorSession`'s edge count in `graphify-out/GRAPH_REPORT.md`'s God Nodes section has dropped materially from 176 (an exact target isn't meaningful here — some legitimate edges remain, e.g. `build_runner.py` owning the session — but the ~15 direct-attribute-reach-in call sites enumerated in the inventory should no longer show as edges from files outside `session.py`/`build_runner.py`).

---

## File Structure

Files modified across this plan (grouped by task, see each task for exact
line targets):

- **Task 1:** `wyrdcraeft/services/morphology/session.py` (rewritten), `wyrdcraeft/services/morphology/build_runner.py` (`_apply_limit` only)
- **Task 2:** `wyrdcraeft/services/morphology/assigners/{noun,verb,adj}.py`, `wyrdcraeft/services/morphology/build_runner.py` (call sites), `wyrdcraeft/services/morphology/reference_snapshots.py` (call sites), `tests/morphology/conftest.py`, `tests/morphology/test_assigner_branches.py`
- **Task 3:** `wyrdcraeft/services/morphology/contracts.py`, `wyrdcraeft/services/morphology/generation/sinks.py`, `wyrdcraeft/services/morphology/generation/form_rows.py`, `tests/lexicon/source_db.py`, `tests/morphology/test_query_service.py`
- **Task 4:** `wyrdcraeft/services/morphology/generation/adv_forms.py`, `wyrdcraeft/services/morphology/generation/facade.py` (`generate_adverbs` only)
- **Task 5:** `wyrdcraeft/services/morphology/generation/num_forms.py`, `facade.py` (`generate_numerals` only)
- **Task 6:** `wyrdcraeft/services/morphology/generation/noun_forms.py`, `facade.py` (`generate_nouns` only)
- **Task 7:** `wyrdcraeft/services/morphology/generation/adj_forms.py`, `facade.py` (`generate_adjectives` only)
- **Task 8:** `wyrdcraeft/services/morphology/generation/common.py` (`VerbFormGenerator` only), `wyrdcraeft/services/morphology/generation/verb_engine.py`, `wyrdcraeft/services/morphology/generation/participles.py`, `facade.py` (`generate_verbs` only), `tests/morphology/test_generation_branches.py`
- **Task 9:** `wyrdcraeft/services/morphology/progress.py` (`compute_stage_totals_for_session`), `wyrdcraeft/services/morphology/build_runner.py` (`_current_stage_total`)

**Not touched by this plan** (confirmed via inventory to be pure pass-through, or the legitimate top-level orchestrator that's allowed to own a whole session per `AGENTS.md`):
- `wyrdcraeft/services/morphology/generation/dispatch.py` — zero direct `session.*` touches, pure forwarding to `facade.py`. Its public signatures (`generate_vbforms(session, output_file, ...)` etc.) stay as `session: GeneratorSession` — this is `facade.py`'s call contract, not a reach-in site.
- `wyrdcraeft/services/morphology/reference_snapshots.py`'s `preprocess_snapshot_rows`, `paradigm_snapshot_rows`, `form_rows_for_stage`, `full_flow_rows`, `full_flow_metadata` — these read `session.words` directly but call no function whose signature this plan changes to something incompatible with a `GeneratorSession`; they keep working unchanged via Task 1's forwarding properties.
- `wyrdcraeft/services/morphology/build_runner.py`'s `run_morphology_generation` — it constructs and owns `session = GeneratorSession()` for the whole run; this is the legitimate orchestrator object, matching `AGENTS.md`'s blessed "per-run orchestration + mutable run state" pattern. Only its two call sites that need updating (assigner calls in Task 2, `_apply_limit` in Task 1) change.
- `scripts/morphology/profile_adj_stage.py` — only reads `session.output_counter` before/after a stage for profiling; keeps working unchanged via forwarding properties.
- `tests/morphology/test_paradigm_reference.py`, `tests/morphology/test_preprocess_reference.py` — read `session.words` only, no migrated-function calls; unaffected.

---

### Task 1: Introduce `WordPool` + `GenerationRunState`, compose `GeneratorSession` from them

**Files:**
- Modify: `wyrdcraeft/services/morphology/session.py` (full rewrite, 122 → ~230 lines)
- Modify: `wyrdcraeft/services/morphology/build_runner.py:216-225` (`_apply_limit`)

**Interfaces:**
- Produces: `WordPool` (new class) with attributes `words: list[Word]`, `manual_forms: list[ManualForm]`, `verb_paradigms: dict[str, VerbParadigm]`, `prefixes: list[str]`, `adjectives: list[Word]`, `nouns: list[Word]`, `verbs: list[Word]`, and methods `categorize() -> None` and `append_participle(word: Word) -> None`.
- Produces: `GenerationRunState` (new class) with attributes `output_counter: int`, `perl_probability: int`, `enable_num_probability_carry: bool`, `enable_r_stem_nouns: bool`.
- Produces: `GeneratorSession.word_pool: WordPool` and `GeneratorSession.run_state: GenerationRunState` — every later task's new function signatures take one or both of these types.
- Consumes: nothing from earlier tasks (this is the first task).

- [ ] **Step 1: Write the failing test**

Create `tests/morphology/test_session_composition.py`:

```python
"""Regression tests for the GeneratorSession -> WordPool/GenerationRunState split.

GeneratorSession's 11 public attributes must keep working exactly as before
(read and write) via forwarding properties onto the new word_pool/run_state
collaborators, so every existing caller keeps working unchanged during the
incremental migration in the rest of this plan.
"""

from wyrdcraeft.services.morphology.session import (
    GenerationRunState,
    GeneratorSession,
    WordPool,
)


def test_session_composes_word_pool_and_run_state():
    session = GeneratorSession()
    assert isinstance(session.word_pool, WordPool)
    assert isinstance(session.run_state, GenerationRunState)


def test_word_pool_attrs_forward_through_session():
    session = GeneratorSession()
    session.words = ["w1", "w2"]
    assert session.word_pool.words == ["w1", "w2"]
    session.word_pool.words.append("w3")
    assert session.words == ["w1", "w2", "w3"]


def test_run_state_attrs_forward_through_session():
    session = GeneratorSession()
    session.output_counter = 5
    assert session.run_state.output_counter == 5
    session.run_state.output_counter += 1
    assert session.output_counter == 6

    session.enable_r_stem_nouns = True
    assert session.run_state.enable_r_stem_nouns is True


def test_word_pool_categorize_matches_load_all_categorization():
    from wyrdcraeft.models.morphology import Word

    pool = WordPool()
    pool.words = [
        Word(id=1, title="a", stem="a", verb=1, pspart=0, papart=0, adjective=0, numeral=0, noun=0, prefix="0", syllables=1, wright="", para_id="", paradigm="", adj_paradigm=[], noun_paradigm=""),
        Word(id=2, title="b", stem="b", verb=0, pspart=0, papart=0, adjective=1, numeral=0, noun=0, prefix="0", syllables=1, wright="", para_id="", paradigm="", adj_paradigm=[], noun_paradigm=""),
        Word(id=3, title="c", stem="c", verb=0, pspart=0, papart=0, adjective=0, numeral=0, noun=1, prefix="0", syllables=1, wright="", para_id="", paradigm="", adj_paradigm=[], noun_paradigm=""),
    ]
    pool.categorize()
    assert [w.title for w in pool.verbs] == ["a"]
    assert [w.title for w in pool.adjectives] == ["b"]
    assert [w.title for w in pool.nouns] == ["c"]


def test_word_pool_append_participle():
    from wyrdcraeft.models.morphology import Word

    pool = WordPool()
    pool.adjectives = []
    participle = Word(id=9, title="p", stem="p", verb=0, pspart=1, papart=0, adjective=0, numeral=0, noun=0, prefix="0", syllables=1, wright="", para_id="", paradigm="", adj_paradigm=[], noun_paradigm="")
    pool.append_participle(participle)
    assert pool.adjectives == [participle]
```

> Note for the implementer: check `wyrdcraeft/models/morphology.py`'s `Word` model's actual required constructor fields before running this test — the field list above was assembled from context in this session and may not be complete or may use different field names/defaults (e.g. some fields might have defaults and not need to be passed explicitly). Read the `Word` class definition first, adjust the two `Word(...)` construction calls in `test_word_pool_categorize_matches_load_all_categorization` and `test_word_pool_append_participle` to match its real required fields, and only then proceed to Step 2. This is the one place in this plan where you must verify a detail against current code before transcribing — everything else is exact.

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/morphology/test_session_composition.py -v`

Expected: FAIL with `ImportError: cannot import name 'WordPool'` (or similar) — none of `WordPool`, `GenerationRunState` exist yet.

- [ ] **Step 3: Rewrite `session.py`**

Replace the full contents of `wyrdcraeft/services/morphology/session.py` with:

```python
import re
from typing import TYPE_CHECKING

from .loaders import load_dictionary, load_forms, load_paradigms, load_prefixes
from .text_utils import OENormalizer

if TYPE_CHECKING:
    from wyrdcraeft.models.morphology import ManualForm, VerbParadigm, Word


class WordPool:
    """
    Categorized word lists and supporting dictionaries for one morphology
    generation run.
    """

    def __init__(self) -> None:
        #: The words: the words to be processed.
        self.words: list["Word"] = []
        #: The manual forms
        self.manual_forms: list["ManualForm"] = []
        #: The verb paradigms
        self.verb_paradigms: dict[str, "VerbParadigm"] = {}
        #: The prefixes
        self.prefixes: list[str] = []
        #: The adjectives: for discovered participles
        self.adjectives: list["Word"] = []
        #: The nouns
        self.nouns: list["Word"] = []
        #: The verbs
        self.verbs: list["Word"] = []

    def categorize(self) -> None:
        """
        Recompute the verb/adjective/noun pools from the current word list.

        Side Effects:
            Overwrites :attr:`verbs`, :attr:`adjectives`, and :attr:`nouns` in place.

        """
        self.verbs = [
            w for w in self.words if w.verb == 1 and (w.pspart + w.papart == 0)
        ]
        self.adjectives = [
            w
            for w in self.words
            if w.adjective == 1 and (w.pspart + w.papart + w.numeral == 0)
        ]
        self.nouns = [w for w in self.words if w.noun == 1]

    def append_participle(self, word: "Word") -> None:
        """
        Add a verb-discovered participle to the adjective pool.

        Args:
            word: Participle word discovered during verb generation.

        Side Effects:
            Appends ``word`` to :attr:`adjectives`.

        """
        self.adjectives.append(word)


class GenerationRunState:
    """
    Cross-stage scalar state shared across one morphology generation run.
    """

    def __init__(self) -> None:
        #: The output counter: the number of words output.
        self.output_counter: int = 0
        #: Perl-style shared probability scalar used across generator phases.
        self.perl_probability: int = 0
        #: Whether numeral generation should carry probability across prints.
        #: Enabled by adjective generation in full-flow parity mode.
        self.enable_num_probability_carry: bool = False
        #: Opt-in non-parity extension gate for r-stem noun support.
        #: Default is False to preserve Perl-compatible behavior.
        self.enable_r_stem_nouns: bool = False


class GeneratorSession:
    """
    The primary entry point for the morphology generation service.  This is used
    to store the session data for the generator as the generator is run.

    Composes a :class:`WordPool` and a :class:`GenerationRunState`. Every
    attribute below is a forwarding property onto one or the other, kept for
    backward compatibility with existing callers while callers are migrated,
    file by file, onto the narrower ``word_pool``/``run_state`` collaborators
    directly.
    """

    def __init__(self) -> None:
        #: Categorized word pools and supporting dictionaries for this run.
        self.word_pool = WordPool()
        #: Cross-stage scalar run state for this run.
        self.run_state = GenerationRunState()

    @property
    def words(self) -> list["Word"]:
        """The words: the words to be processed."""
        return self.word_pool.words

    @words.setter
    def words(self, value: list["Word"]) -> None:
        self.word_pool.words = value

    @property
    def manual_forms(self) -> list["ManualForm"]:
        """The manual forms."""
        return self.word_pool.manual_forms

    @manual_forms.setter
    def manual_forms(self, value: list["ManualForm"]) -> None:
        self.word_pool.manual_forms = value

    @property
    def verb_paradigms(self) -> dict[str, "VerbParadigm"]:
        """The verb paradigms."""
        return self.word_pool.verb_paradigms

    @verb_paradigms.setter
    def verb_paradigms(self, value: dict[str, "VerbParadigm"]) -> None:
        self.word_pool.verb_paradigms = value

    @property
    def prefixes(self) -> list[str]:
        """The prefixes."""
        return self.word_pool.prefixes

    @prefixes.setter
    def prefixes(self, value: list[str]) -> None:
        self.word_pool.prefixes = value

    @property
    def adjectives(self) -> list["Word"]:
        """The adjectives: for discovered participles."""
        return self.word_pool.adjectives

    @adjectives.setter
    def adjectives(self, value: list["Word"]) -> None:
        self.word_pool.adjectives = value

    @property
    def nouns(self) -> list["Word"]:
        """The nouns."""
        return self.word_pool.nouns

    @nouns.setter
    def nouns(self, value: list["Word"]) -> None:
        self.word_pool.nouns = value

    @property
    def verbs(self) -> list["Word"]:
        """The verbs."""
        return self.word_pool.verbs

    @verbs.setter
    def verbs(self, value: list["Word"]) -> None:
        self.word_pool.verbs = value

    @property
    def output_counter(self) -> int:
        """The output counter: the number of words output."""
        return self.run_state.output_counter

    @output_counter.setter
    def output_counter(self, value: int) -> None:
        self.run_state.output_counter = value

    @property
    def perl_probability(self) -> int:
        """Perl-style shared probability scalar used across generator phases."""
        return self.run_state.perl_probability

    @perl_probability.setter
    def perl_probability(self, value: int) -> None:
        self.run_state.perl_probability = value

    @property
    def enable_num_probability_carry(self) -> bool:
        """Whether numeral generation should carry probability across prints."""
        return self.run_state.enable_num_probability_carry

    @enable_num_probability_carry.setter
    def enable_num_probability_carry(self, value: bool) -> None:
        self.run_state.enable_num_probability_carry = value

    @property
    def enable_r_stem_nouns(self) -> bool:
        """Opt-in non-parity extension gate for r-stem noun support."""
        return self.run_state.enable_r_stem_nouns

    @enable_r_stem_nouns.setter
    def enable_r_stem_nouns(self, value: bool) -> None:
        self.run_state.enable_r_stem_nouns = value

    @property
    def prefix_regex(self) -> str:
        """
        Get the prefix regex, used to match the prefixes of the words.

        Prefixes are loaded from the prefixes file

        Returns:
            The prefix regex.

        """
        if not self.prefixes:
            return "0"
        # Perl: foreach (@prefix_input) { $prefix_regex = "$prefix_regex|$_"; }
        return "|".join(self.prefixes)

    def load_all(
        self, dict_path: str, forms_path: str, para_path: str, prefix_path: str
    ) -> None:
        """
        Load all the data from the supporting files into the session.

        - Loads the dictionary
        - Loads the manual forms
        - Loads the paradigms
        - Loads the prefixes
        - Categorizes the words initially into verbs (:attr:`verbs`), adjectives
          (:attr:`adjectives`), and nouns (:attr:`nouns`)

        Args:
            dict_path: The path to the dictionary file.
            forms_path: The path to the forms file.
            para_path: The path to the paradigms file.
            prefix_path: The path to the prefixes file.

        """
        self.words = load_dictionary(dict_path)
        self.manual_forms = load_forms(forms_path)
        self.verb_paradigms = load_paradigms(para_path)
        self.prefixes = load_prefixes(prefix_path)
        self.word_pool.categorize()

    def remove_prefixes(self) -> None:
        """
        Remove the prefixes from the words.
        """
        for word in self.words:
            word.prefix = "0"
            stem = word.stem
            match = re.match(r"^(.*)[\- ](.*)$", stem)
            if match:
                word.prefix = match.group(1)
                word.stem = match.group(2)
            else:
                word.stem = stem

    def remove_hyphens(self) -> None:
        """
        Remove the hyphens from the words.
        """
        for word in self.words:
            word.prefix = word.prefix.replace("-", "")
            word.stem = word.stem.replace("-", "")

    def count_syllables(self) -> None:
        """
        Count the syllables in the words.
        """
        for word in self.words:
            word.syllables = OENormalizer.syllable_count(word.stem)
```

Note the old `load_all` had 3 lines of inline categorization (`self.verbs =
[...]`, `self.adjectives = [...]`, `self.nouns = [...]`) — the new version
above replaces those 3 lines with a single `self.word_pool.categorize()`
call. Confirm the categorization predicates in `WordPool.categorize()` above
match exactly (they were copied verbatim from the current `load_all` body —
`w.verb == 1 and (w.pspart + w.papart == 0)` for verbs,
`w.adjective == 1 and (w.pspart + w.papart + w.numeral == 0)` for adjectives,
`w.noun == 1` for nouns).

- [ ] **Step 4: Deduplicate `_apply_limit` in `build_runner.py`**

In `wyrdcraeft/services/morphology/build_runner.py`, find `_apply_limit`
(currently around line 200-225). It currently duplicates the same three
categorization list comprehensions inline after truncating `session.words`:

```python
session.words = session.words[:limit]
session.verbs = [
    w for w in session.words if w.verb == 1 and (w.pspart + w.papart == 0)
]
session.adjectives = [
    w
    for w in session.words
    if w.adjective == 1 and (w.pspart + w.papart + w.numeral == 0)
]
session.nouns = [w for w in session.words if w.noun == 1]
```

Replace those last three assignments (the `session.verbs = ...` /
`session.adjectives = ...` / `session.nouns = ...` block) with a single call:

```python
session.words = session.words[:limit]
session.word_pool.categorize()
```

- [ ] **Step 5: Run the new tests to verify they pass**

Run: `.venv/bin/pytest tests/morphology/test_session_composition.py -v`

Expected: all 5 tests PASS.

- [ ] **Step 6: Run the parity gate (see Global Constraints)**

Run: `.venv/bin/pytest tests/morphology/test_full_flow_reference.py tests/morphology/test_paradigm_reference.py tests/morphology/test_preprocess_reference.py -v`

Expected: all PASS, zero diff. This task changes only `session.py`'s
internal storage shape and `_apply_limit`'s categorization call — every
external attribute read/write behaves identically via the forwarding
properties, so output must be byte-for-byte identical.

- [ ] **Step 7: Run the full test suite**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`

Expected: same pass count as the pre-task baseline (355 passed, per this
session's earlier baseline run), plus the 5 new tests from Step 1 = 360
passed. No failures.

- [ ] **Step 8: Quality gate**

```bash
ruff check wyrdcraeft/services/morphology/session.py wyrdcraeft/services/morphology/build_runner.py tests/morphology/test_session_composition.py
.venv/bin/mypy wyrdcraeft/services/morphology/session.py wyrdcraeft/services/morphology/build_runner.py
make napoleon-gate
```

- [ ] **Step 9: Commit**

```bash
git add wyrdcraeft/services/morphology/session.py wyrdcraeft/services/morphology/build_runner.py tests/morphology/test_session_composition.py
git commit -m "refactor: split GeneratorSession into WordPool + GenerationRunState"
```

---

### Task 2: Migrate the assigners (`noun.py`, `verb.py`, `adj.py`) onto `WordPool`

**Files:**
- Modify: `wyrdcraeft/services/morphology/assigners/noun.py:552-586` (`set_noun_paradigm`)
- Modify: `wyrdcraeft/services/morphology/assigners/verb.py:297,332,341-361,372-374` (`_assign_verb_heuristics`, `_assign_verb_fallback`, `set_verb_paradigm`)
- Modify: `wyrdcraeft/services/morphology/assigners/adj.py:43-49` (`set_adj_paradigm`)
- Modify: `wyrdcraeft/services/morphology/build_runner.py:439,442,445`
- Modify: `wyrdcraeft/services/morphology/reference_snapshots.py:197-199`
- Modify: `tests/morphology/conftest.py:38-40`
- Modify: `tests/morphology/test_assigner_branches.py` (13 call sites)
- Test: reuse existing `tests/morphology/test_assigner_branches.py` (already covers these functions; this task's job is only to update its 13 call sites to the new signature — see Step 1)

**Interfaces:**
- Consumes: `WordPool` from Task 1 (`wyrdcraeft/services/morphology/session.py`).
- Produces: `set_noun_paradigm(word_pool: WordPool) -> None`, `set_verb_paradigm(word_pool: WordPool) -> None`, `set_adj_paradigm(word_pool: WordPool) -> None` — Task 9's `reference_snapshots.py` cleanup and any future caller use these new signatures.

- [ ] **Step 1: Update `assigners/noun.py`**

Change the entrypoint signature at line 552 from:
```python
def set_noun_paradigm(session: GeneratorSession) -> None:
```
to:
```python
def set_noun_paradigm(word_pool: WordPool) -> None:
```

Update the `TYPE_CHECKING` import block near the top of the file (currently
`from wyrdcraeft.models.morphology import Word` guarded by
`if TYPE_CHECKING:` alongside `from ..session import GeneratorSession`) to
import `WordPool` instead of `GeneratorSession`:
```python
if TYPE_CHECKING:
    from wyrdcraeft.models.morphology import Word

    from ..session import WordPool
```

Inside `set_noun_paradigm`'s body, rename every `session.` reference to
`word_pool.` — the exact lines (per the inventory) are:
- L566 `nouns = session.nouns` → `nouns = word_pool.nouns`
- L567 `prefix_re = session.prefix_regex` → this reads the `prefix_regex`
  *property*, which lives on `GeneratorSession`, not `WordPool`. Since
  `WordPool` doesn't have a `prefix_regex` property, inline the property's
  logic instead: `prefix_re = "|".join(word_pool.prefixes) if word_pool.prefixes else "0"`
- L575 `session.enable_r_stem_nouns,` → this is `GenerationRunState`, not
  `WordPool` — since `set_noun_paradigm` only receives `word_pool` now and
  this assigner's r-stem gate is a run-state flag, **do not** thread
  `GenerationRunState` into the assigners in this task (that would widen
  this task's scope into run-state, which Tasks 4-8 own). Instead: this
  specific call passes `session.enable_r_stem_nouns` into
  `_run_initial_assignment_pass` — check that function's signature; if it's
  a plain `bool` parameter (not `session`), the caller (this task's `Task
  2`) needs a `enable_r_stem_nouns: bool` parameter threaded onto
  `set_noun_paradigm` itself: change the signature to
  `def set_noun_paradigm(word_pool: WordPool, *, enable_r_stem_nouns: bool) -> None:`
  and update this line to `enable_r_stem_nouns,` (pass the parameter
  through unchanged, just renamed away from a `session.` reach-in).
- L580 `session.words,` → `word_pool.words,`
- L586 `_run_final_fallback_pass(nouns, session.words)` → `_run_final_fallback_pass(nouns, word_pool.words)`

Update the 3 docstring-only prose mentions of `` session.words `` at L399,
L425, L451 (in `Args:`/`Note:` blocks of unrelated helper functions) to read
`` word_pool.words `` instead, for consistency — these are prose, not code,
so any wording that keeps the same meaning is fine.

- [ ] **Step 2: Update `assigners/verb.py`**

Change the `TYPE_CHECKING` import the same way as Step 1 (swap
`GeneratorSession` for `WordPool`).

Change `_assign_verb_fallback`'s signature at line 341 from:
```python
def _assign_verb_fallback(words: list[Word], session: GeneratorSession) -> None:
```
to:
```python
def _assign_verb_fallback(words: list[Word], word_pool: WordPool) -> None:
```
and its two touch sites:
- L354 `vp = session.verb_paradigms.get("13")` → `vp = word_pool.verb_paradigms.get("13")`
- L356 `vp = session.verb_paradigms.get("76")` → `vp = word_pool.verb_paradigms.get("76")`

`_assign_verb_heuristics` (called at L396 inside `set_verb_paradigm`) also
touches `session.verb_paradigms` at L297 and L332 — find its signature
(search for `def _assign_verb_heuristics` near line 228) and rename its
`session: GeneratorSession` parameter to `word_pool: WordPool` the same way,
updating both `session.verb_paradigms.get(assigned_id)` reads to
`word_pool.verb_paradigms.get(assigned_id)`.

Change `set_verb_paradigm`'s signature at line 361 from:
```python
def set_verb_paradigm(session: GeneratorSession) -> None:
```
to:
```python
def set_verb_paradigm(word_pool: WordPool) -> None:
```
and its 3 touch sites:
- L372 `vparadigms = list(session.verb_paradigms.values())` → `vparadigms = list(word_pool.verb_paradigms.values())`
- L373 `verbs = session.verbs` → `verbs = word_pool.verbs`
- L374 `prefix_re = session.prefix_regex` → `prefix_re = "|".join(word_pool.prefixes) if word_pool.prefixes else "0"` (same `prefix_regex` inlining as Task 2 Step 1)

Update the two internal calls this function makes (`_assign_verb_heuristics(verbs, session, ...)` at L396 and `_assign_verb_fallback(verbs, session)` at L408 — confirm exact call syntax by reading the surrounding lines) to pass `word_pool` instead of `session`.

- [ ] **Step 3: Update `assigners/adj.py`**

Change the `TYPE_CHECKING` import the same way.

Change `set_adj_paradigm`'s signature at line 43 from:
```python
def set_adj_paradigm(session: GeneratorSession) -> None:  # noqa: PLR0912
```
to:
```python
def set_adj_paradigm(word_pool: WordPool) -> None:  # noqa: PLR0912
```
and its 2 touch sites:
- L48 `adjectives = session.words` → `adjectives = word_pool.words`
- L49 `session.adjectives = list(adjectives)` → `word_pool.adjectives = list(adjectives)`

- [ ] **Step 4: Update all 4 call sites**

`wyrdcraeft/services/morphology/build_runner.py:439,442,445` — change:
```python
set_verb_paradigm(session)
...
set_adj_paradigm(session)
...
set_noun_paradigm(session)
```
to:
```python
set_verb_paradigm(session.word_pool)
...
set_adj_paradigm(session.word_pool)
...
set_noun_paradigm(session.word_pool)
```
(If Step 2's `set_noun_paradigm` ended up needing the extra
`enable_r_stem_nouns` keyword argument per Step 1's note, update this call
to `set_noun_paradigm(session.word_pool, enable_r_stem_nouns=session.enable_r_stem_nouns)`.)

`wyrdcraeft/services/morphology/reference_snapshots.py:197-199` — same
transformation:
```python
set_verb_paradigm(session.word_pool)
set_adj_paradigm(session.word_pool)
set_noun_paradigm(session.word_pool)
```
(with the same `enable_r_stem_nouns` keyword if needed)

`tests/morphology/conftest.py:38-40` — same transformation.

`tests/morphology/test_assigner_branches.py` — grep the file for
`set_verb_paradigm(session)`, `set_adj_paradigm(session)`,
`set_noun_paradigm(session)` (13 occurrences total per the inventory) and
change every one to pass `session.word_pool` instead of `session`.

- [ ] **Step 5: Run the parity gate**

Run: `.venv/bin/pytest tests/morphology/test_full_flow_reference.py tests/morphology/test_paradigm_reference.py tests/morphology/test_preprocess_reference.py -v`

Expected: all PASS, zero diff.

- [ ] **Step 6: Run the full test suite**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`

Expected: same pass count as Task 1's end state, no failures. Any remaining
old-signature call this step didn't already find will raise `TypeError:
set_noun_paradigm() takes 1 positional argument but ...` (or similar) — fix
by applying the same `session` → `session.word_pool` transformation at the
reported file:line.

- [ ] **Step 7: Quality gate**

```bash
ruff check wyrdcraeft/services/morphology/assigners/noun.py wyrdcraeft/services/morphology/assigners/verb.py wyrdcraeft/services/morphology/assigners/adj.py wyrdcraeft/services/morphology/build_runner.py wyrdcraeft/services/morphology/reference_snapshots.py tests/morphology/conftest.py tests/morphology/test_assigner_branches.py
.venv/bin/mypy wyrdcraeft/services/morphology/assigners/noun.py wyrdcraeft/services/morphology/assigners/verb.py wyrdcraeft/services/morphology/assigners/adj.py
make napoleon-gate
```

- [ ] **Step 8: Commit**

```bash
git add wyrdcraeft/services/morphology/assigners/ wyrdcraeft/services/morphology/build_runner.py wyrdcraeft/services/morphology/reference_snapshots.py tests/morphology/conftest.py tests/morphology/test_assigner_branches.py
git commit -m "refactor: migrate paradigm assigners from GeneratorSession to WordPool"
```

---

### Task 3: Migrate the shared sink + row-emission leaf layer onto `GenerationRunState`/`WordPool`

This is the highest-leverage task: every one of the 5 generation paths
(verb, adjective, adverb, numeral, noun) calls `print_one_form`, which
forwards into this layer. Confirmed via direct reads this session: all
functions in this layer either touch only `output_counter` (→
`GenerationRunState`) or forward an opaque `session` parameter purely to
keep passing it along (no other attribute access) — those become
`run_state: GenerationRunState` too, since that's all they ultimately
deliver to the sink.

**Files:**
- Modify: `wyrdcraeft/services/morphology/contracts.py:11-35` (`ParityFormOutput` protocol)
- Modify: `wyrdcraeft/services/morphology/generation/sinks.py` (3 classes: `TsvParitySink`, `SqliteIndexSink`, `CompositeSink`)
- Modify: `wyrdcraeft/services/morphology/generation/form_rows.py` (all functions: `print_one_form`, `output_manual_forms`, `generate_and_print_form`, `generate_and_print_manual`, `emit_form_for_context`, `emit_imsg_for_context`, `generate_and_print_form_with_sound_changes` + its nested `_emit_source_form`, `emit_sound_changed_form_for_context` + its nested `_emit_with_sound_changes`)
- Modify: `wyrdcraeft/services/morphology/generation/facade.py:55-68` (`output_manual_forms` method only)
- Modify: `tests/lexicon/source_db.py` (imports `print_one_form`)
- Modify: `tests/morphology/test_query_service.py` (imports `print_one_form`, 3 call sites)

**IMPORTANT — arity change, not just a rename:** unlike every other function touched in this
task, `output_manual_forms`'s parameter *count* changes (1 `session` param becomes 2:
`word_pool` + `run_state`). Every other renamed function in this task keeps taking exactly
one collaborator positionally, so an unmigrated caller still passing a whole
`GeneratorSession` object keeps working by duck-typing through Task 1's forwarding
properties (harmless until its own task lands). `output_manual_forms` is different: its
one caller, `facade.py`'s `output_manual_forms(self)` method (line 55-68), currently calls
`_output_manual_forms(self._session, self._output_file, progress=self._progress)` — a
2-positional-arg call. Once the signature requires 3 positional args before `progress`,
this call raises `TypeError: _output_manual_forms() missing 1 required positional
argument: 'output_file'` immediately, breaking the parity gate's manual-forms stage. This
task MUST also update that one `facade.py` method call (no other file in Tasks 4-8 owns
it) — see the added step below.

**Interfaces:**
- Consumes: `GenerationRunState`, `WordPool` from Task 1.
- Produces: `print_one_form(run_state: GenerationRunState, form_data: dict[str, str], output_file: FormOutput) -> None`, `output_manual_forms(word_pool: WordPool, run_state: GenerationRunState, output_file: FormOutput, *, progress=None) -> None`, and the 6 other `form_rows.py` functions each taking `run_state: GenerationRunState` where they took `session: GeneratorSession` before. Tasks 4-8 (every PoS generator) call into these new signatures.

- [ ] **Step 1: Update `contracts.py`**

Change:
```python
class ParityFormOutput(Protocol):
    """Parity-aware output protocol accepting legacy form payloads."""

    def emit_form_data(
        self, session: GeneratorSession, form_data: dict[str, str]
    ) -> Any:
        """
        Emit one legacy form payload using parity row semantics.

        Note:
            Linguistic behavior follows ``data/OldEnglishGrammar.pdf`` and
            ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this turns one
            lexeme-plus-inflection payload into surface-form rows for the word's
            Part of Speech.

        Args:
            session: Active generator session tracking output state.
            form_data: Legacy mutable row payload.

        """
```
to:
```python
class ParityFormOutput(Protocol):
    """Parity-aware output protocol accepting legacy form payloads."""

    def emit_form_data(
        self, run_state: GenerationRunState, form_data: dict[str, str]
    ) -> Any:
        """
        Emit one legacy form payload using parity row semantics.

        Note:
            Linguistic behavior follows ``data/OldEnglishGrammar.pdf`` and
            ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this turns one
            lexeme-plus-inflection payload into surface-form rows for the word's
            Part of Speech.

        Args:
            run_state: Active generation run state tracking the output counter.
            form_data: Legacy mutable row payload.

        """
```
and update the `if TYPE_CHECKING:` import from `from .session import
GeneratorSession` to `from .session import GenerationRunState`.

- [ ] **Step 2: Update `sinks.py`'s 3 classes**

`TsvParitySink.emit_form_data` — change:
```python
    def emit_form_data(
        self, session: GeneratorSession, form_data: dict[str, str]
    ) -> list[FormRow]:
        """
        Emit parity rows from legacy ``form_data`` and update session counter.

        Args:
            session: Active generation session tracking output counter.
            form_data: Legacy mutable row payload.

        Returns:
            Emitted rows in output order.

        """
        rows = _build_form_rows_from_form_data(
            counter=session.output_counter,
            form_data=form_data,
        )
        self.emit_rows(rows)
        session.output_counter += len(rows)
        return rows
```
to:
```python
    def emit_form_data(
        self, run_state: GenerationRunState, form_data: dict[str, str]
    ) -> list[FormRow]:
        """
        Emit parity rows from legacy ``form_data`` and update the run's output counter.

        Args:
            run_state: Active generation run state tracking the output counter.
            form_data: Legacy mutable row payload.

        Returns:
            Emitted rows in output order.

        """
        rows = _build_form_rows_from_form_data(
            counter=run_state.output_counter,
            form_data=form_data,
        )
        self.emit_rows(rows)
        run_state.output_counter += len(rows)
        return rows
```

`SqliteIndexSink.emit_form_data` — apply the identical transformation (same
parameter rename, same body change, only the docstring's second line differs
slightly: "Build parity rows from legacy ``form_data`` and persist them to
SQLite." stays as-is, only the `Args:` line and body change per the pattern
above).

`CompositeSink.emit_form_data` — change:
```python
    def emit_form_data(
        self, session: GeneratorSession, form_data: dict[str, str]
    ) -> list[FormRow]:
        """
        Emit parity rows and fan them out to all attached row sinks.

        Args:
            session: Active generation session tracking output counter.
            form_data: Legacy mutable row payload.

        Returns:
            Emitted rows in output order.

        """
        rows = self._primary_sink.emit_form_data(session, form_data)
        for sink in self._row_sinks:
            sink.emit_rows(rows)
        return rows
```
to:
```python
    def emit_form_data(
        self, run_state: GenerationRunState, form_data: dict[str, str]
    ) -> list[FormRow]:
        """
        Emit parity rows and fan them out to all attached row sinks.

        Args:
            run_state: Active generation run state tracking the output counter.
            form_data: Legacy mutable row payload.

        Returns:
            Emitted rows in output order.

        """
        rows = self._primary_sink.emit_form_data(run_state, form_data)
        for sink in self._row_sinks:
            sink.emit_rows(rows)
        return rows
```

Update `sinks.py`'s `if TYPE_CHECKING:` import of `GeneratorSession` to
`GenerationRunState` (check the top of the file for the exact import
location — it wasn't in this plan's inventory excerpt, grep the file for
`GeneratorSession` to find and replace the import).

- [ ] **Step 3: Update `form_rows.py`**

Update the `if TYPE_CHECKING:` import from `from
wyrdcraeft.services.morphology.session import GeneratorSession` to `from
wyrdcraeft.services.morphology.session import GenerationRunState, WordPool`.

`print_one_form` (L24-26) — change:
```python
def print_one_form(
    session: GeneratorSession, form_data: dict[str, str], output_file: FormOutput
) -> None:
```
to:
```python
def print_one_form(
    run_state: GenerationRunState, form_data: dict[str, str], output_file: FormOutput
) -> None:
```
Update the `Args:` docstring line from `session: Active generation session.`
to `run_state: Active generation run state tracking the output counter.`
Update the body (L53-57):
```python
    emit_form_data = getattr(output_file, "emit_form_data", None)
    if callable(emit_form_data):
        emit_form_data(session, form_data)
        return
    TsvParitySink(cast("FormWriter", output_file)).emit_form_data(session, form_data)
```
to:
```python
    emit_form_data = getattr(output_file, "emit_form_data", None)
    if callable(emit_form_data):
        emit_form_data(run_state, form_data)
        return
    TsvParitySink(cast("FormWriter", output_file)).emit_form_data(run_state, form_data)
```

`output_manual_forms` (L60-65) — this one needs BOTH collaborators (it
reads `session.manual_forms` for the word list AND `session.output_counter`
for progress). Change:
```python
def output_manual_forms(
    session: GeneratorSession,
    output_file: FormOutput,
    *,
    progress: MorphologyGenerateProgressCoordinator | None = None,
) -> None:
```
to:
```python
def output_manual_forms(
    word_pool: WordPool,
    run_state: GenerationRunState,
    output_file: FormOutput,
    *,
    progress: MorphologyGenerateProgressCoordinator | None = None,
) -> None:
```
Update its body: L77 `for mf in session.manual_forms:` →
`for mf in word_pool.manual_forms:`; L83 `forms_written=session.output_counter,`
→ `forms_written=run_state.output_counter,`; and its call to `print_one_form`
further down in the function (find it — it's after the `form_data = {...}`
dict construction shown in this session's read excerpt, likely around
L95-110) needs to pass `run_state` instead of `session`.

For the remaining 6 functions — `generate_and_print_form` (L106),
`generate_and_print_manual` (L169), `emit_form_for_context` (L202),
`emit_imsg_for_context` (L265), `generate_and_print_form_with_sound_changes`
(L315, plus its nested `_emit_source_form`), and
`emit_sound_changed_form_for_context` (L406, plus its nested
`_emit_with_sound_changes`) — confirmed this session: none of them touch any
`session.<attr>` directly; they only take `session: GeneratorSession` to
forward it into `print_one_form`, `generate_and_print_form`, or
`generate_and_print_manual`. For each of these 6 functions (7 counting the
nested closures separately if you prefer, but they share their enclosing
function's parameter):

1. Rename the `session: GeneratorSession` parameter to `run_state:
   GenerationRunState` in the signature.
2. Update the `Args:` docstring line the same way as `print_one_form` above.
3. Find every place inside the function body where `session` is passed as
   an argument (to `print_one_form`, `generate_and_print_form`,
   `generate_and_print_manual`, or via `partial(generate_and_print_manual,
   session, output_file)` in `generate_and_print_form_with_sound_changes` —
   confirmed this session at the line reading
   `emit_manual=partial(generate_and_print_manual, session, output_file),`)
   and rename that argument to `run_state`. Do not change anything else in
   the function body — no other logic touches session state in these 6
   functions.

After this step, grep the whole file for the literal string `GeneratorSession`
— it should return zero hits (only `WordPool`/`GenerationRunState` should
remain as type references).

- [ ] **Step 4: Update test callers of `print_one_form`**

`tests/lexicon/source_db.py` imports `print_one_form` from
`wyrdcraeft.services.morphology.generation.common` (re-exported there) — find
its 1 call site and change the first argument from a `GeneratorSession`
instance (or `session`) to `session.run_state` (or the equivalent local
variable holding a `GenerationRunState`).

`tests/morphology/test_query_service.py` imports `print_one_form` the same
way — find its 3 call sites and apply the same transformation.

- [ ] **Step 5: Update `facade.py`'s `output_manual_forms` method (required — see arity-change note above)**

`output_manual_forms`'s parameter count just changed (1 → 2), unlike every
other function in this task. Its one caller is `facade.py`'s
`output_manual_forms(self)` method (around line 55-68). Change:
```python
    def output_manual_forms(self) -> None:
        """
        ...
        """
        _output_manual_forms(self._session, self._output_file, progress=self._progress)
```
to:
```python
    def output_manual_forms(self) -> None:
        """
        ...
        """
        _output_manual_forms(
            self._session.word_pool,
            self._session.run_state,
            self._output_file,
            progress=self._progress,
        )
```
(keep the existing docstring unchanged — only the body's function call
changes). Without this step, the parity gate's manual-forms stage raises
`TypeError` immediately — this is not optional cleanup, it's required for
this task's own parity gate (Step 6 below) to pass.

- [ ] **Step 6: Run the parity gate**

Run: `.venv/bin/pytest tests/morphology/test_full_flow_reference.py tests/morphology/test_paradigm_reference.py tests/morphology/test_preprocess_reference.py -v`

Expected: all PASS, zero diff — including the manual-forms stage, now that
Step 5 has updated its one caller. Note: this task alone will likely cause
several *other* generator files (adv_forms.py, num_forms.py, noun_forms.py,
adj_forms.py, common.py's VerbFormGenerator) to fail at runtime if their own
call to `print_one_form` still passes a whole `session` — but per the
arity-change note above, `print_one_form`'s arity did NOT change (still one
collaborator positionally), so this actually keeps working via duck typing
through Task 1's forwarding properties (a `GeneratorSession` instance still
has a working `.output_counter`). **Confirm the full-flow test passes as a
whole** — if it does, duck typing is correctly papering over the
not-yet-migrated generator files, and Tasks 4-8 can proceed in any order
without a hard dependency-ordering requirement beyond "Task 3 must land
first."

- [ ] **Step 7: Run the full test suite**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`

Expected: same pass count as Task 2's end state (360 passed), no new
failures — Step 5's facade.py fix plus duck typing for the rest means this
task should be a clean, fully-green task, not a partial/expected-failure one.
If any test fails, that's a real bug in this task's changes (most likely a
missed `session` → `run_state`/`word_pool` rename somewhere in `form_rows.py`
that Step 3 didn't catch) — find and fix it before proceeding, do not treat
any failure at this point as "expected."

- [ ] **Step 8: Quality gate**

```bash
ruff check wyrdcraeft/services/morphology/contracts.py wyrdcraeft/services/morphology/generation/sinks.py wyrdcraeft/services/morphology/generation/form_rows.py wyrdcraeft/services/morphology/generation/facade.py tests/lexicon/source_db.py tests/morphology/test_query_service.py
.venv/bin/mypy wyrdcraeft/services/morphology/contracts.py wyrdcraeft/services/morphology/generation/sinks.py wyrdcraeft/services/morphology/generation/form_rows.py wyrdcraeft/services/morphology/generation/facade.py
make napoleon-gate
```

- [ ] **Step 9: Commit**

```bash
git add wyrdcraeft/services/morphology/contracts.py wyrdcraeft/services/morphology/generation/sinks.py wyrdcraeft/services/morphology/generation/form_rows.py wyrdcraeft/services/morphology/generation/facade.py tests/lexicon/source_db.py tests/morphology/test_query_service.py
git commit -m "refactor: migrate sink + row-emission layer from GeneratorSession to GenerationRunState"
```

---

### Task 4: Migrate `generation/adv_forms.py` (smallest generator — proves the pattern end to end)

**Files:**
- Modify: `wyrdcraeft/services/morphology/generation/adv_forms.py:17-41` (`generate_advforms`)
- Modify: `wyrdcraeft/services/morphology/generation/facade.py:100-113` (`generate_adverbs`)

**Interfaces:**
- Consumes: `WordPool`, `GenerationRunState` (Task 1), migrated `print_one_form` (Task 3).
- Produces: `generate_advforms(word_pool: WordPool, run_state: GenerationRunState, output_file: FormOutput, *, progress=None) -> None` — no downstream task consumes this directly (each generator is independent), but the pattern established here (facade unpacks `session.word_pool`/`session.run_state` when calling the migrated function) is reused identically in Tasks 5-7.

- [ ] **Step 1: Update `adv_forms.py`**

Change the signature (L17-22):
```python
def generate_advforms(
    session: GeneratorSession,
    output_file: FormOutput,
    *,
    progress: MorphologyGenerateProgressCoordinator | None = None,
) -> None:
```
to:
```python
def generate_advforms(
    word_pool: WordPool,
    run_state: GenerationRunState,
    output_file: FormOutput,
    *,
    progress: MorphologyGenerateProgressCoordinator | None = None,
) -> None:
```
Update the `if TYPE_CHECKING:` import from `GeneratorSession` to
`GenerationRunState, WordPool`.

Update its 2 touch sites:
- L34 `for word in session.words:` → `for word in word_pool.words:`
- L41 `forms_written=session.output_counter,` → `forms_written=run_state.output_counter,`

Update its call to `print_one_form` (per Task 3, this now takes `run_state`
as its first argument) — find the 3 call sites (per the earlier grep: L63,
L74, L90) and change `print_one_form(session, ...)` to
`print_one_form(run_state, ...)` at each.

- [ ] **Step 2: Update `facade.py`'s `generate_adverbs`**

Change:
```python
    def generate_adverbs(self) -> None:
        """
        ...
        """
        _generate_advforms(self._session, self._output_file, progress=self._progress)
```
to:
```python
    def generate_adverbs(self) -> None:
        """
        ...
        """
        _generate_advforms(
            self._session.word_pool,
            self._session.run_state,
            self._output_file,
            progress=self._progress,
        )
```
(keep the existing docstring unchanged — only the body's function call changes)

- [ ] **Step 3: Run the parity gate**

Run: `.venv/bin/pytest tests/morphology/test_full_flow_reference.py tests/morphology/test_paradigm_reference.py tests/morphology/test_preprocess_reference.py -v`

Expected: all PASS, zero diff.

- [ ] **Step 4: Run the full test suite**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`

Expected: no new failures versus Task 3's recorded baseline. If a test
directly imports and calls `generate_advforms(session, ...)` with the old
signature (check `tests/morphology/test_generation_branches.py` and
`tests/morphology/test_full_flow_reference.py`/`parity_harness.py` — the
latter two call `generate_advforms(session, output)` per this plan's earlier
research and need updating to `generate_advforms(session.word_pool,
session.run_state, output)`), fix each reported call site.

- [ ] **Step 5: Quality gate**

```bash
ruff check wyrdcraeft/services/morphology/generation/adv_forms.py wyrdcraeft/services/morphology/generation/facade.py
.venv/bin/mypy wyrdcraeft/services/morphology/generation/adv_forms.py wyrdcraeft/services/morphology/generation/facade.py
make napoleon-gate
```

- [ ] **Step 6: Commit**

```bash
git add wyrdcraeft/services/morphology/generation/adv_forms.py wyrdcraeft/services/morphology/generation/facade.py tests/
git commit -m "refactor: migrate adverb generation from GeneratorSession to WordPool/GenerationRunState"
```

---

### Task 5: Migrate `generation/num_forms.py`

**Files:**
- Modify: `wyrdcraeft/services/morphology/generation/num_forms.py:32-90` (`_num_print`), `:91-205` (`generate_numforms`)
- Modify: `wyrdcraeft/services/morphology/generation/facade.py:115-128` (`generate_numerals`)

**Interfaces:**
- Consumes: `WordPool`, `GenerationRunState` (Task 1), migrated `print_one_form` (Task 3).
- Produces: `generate_numforms(word_pool: WordPool, run_state: GenerationRunState, output_file: FormOutput, *, progress=None) -> None`.

- [ ] **Step 1: Update `_num_print`**

Read the full signature at line 32 first (this plan's research only
confirmed it takes `session` as a parameter and is `# noqa: PLR0913`
meaning 6+ params — read the file to get its exact other parameter names
before editing). Rename its `session: GeneratorSession` parameter to
`run_state: GenerationRunState`. Update its 2 touch sites:
- L55 `if session.enable_num_probability_carry:` → `if run_state.enable_num_probability_carry:`
- L69 `elif not session.enable_num_probability_carry:` → `elif not run_state.enable_num_probability_carry:`

Update its call to `print_one_form` (L71) from `print_one_form(session,
fh, output_file)` to `print_one_form(run_state, fh, output_file)`.

- [ ] **Step 2: Update `generate_numforms`**

Change the signature (L199-205):
```python
def generate_numforms(  # noqa: PLR0912, PLR0915
    session: GeneratorSession,
    output_file: FormOutput,
    *,
    progress: MorphologyGenerateProgressCoordinator | None = None,
) -> None:
```
to:
```python
def generate_numforms(  # noqa: PLR0912, PLR0915
    word_pool: WordPool,
    run_state: GenerationRunState,
    output_file: FormOutput,
    *,
    progress: MorphologyGenerateProgressCoordinator | None = None,
) -> None:
```
Update the `if TYPE_CHECKING:` import.

Update its touch sites:
- L115 `for word in session.words:` → `for word in word_pool.words:`
- L123 `forms_written=session.output_counter,` → `forms_written=run_state.output_counter,`
- L255 `if session.enable_num_probability_carry:` → `if run_state.enable_num_probability_carry:`
- The line reading `getattr(session, "perl_probability", 0)` near L258 →
  `getattr(run_state, "perl_probability", 0)`

Update every one of the ~30 calls to `_num_print(session, output_file,
formhash_base, fp, "...")` throughout the function (e.g. L147, L151, L156,
and all others found by grepping this file for `_num_print(session,`) to
pass `run_state` instead of `session`.

- [ ] **Step 3: Update `facade.py`'s `generate_numerals`**

Same transformation as Task 4 Step 2, targeting the `generate_numerals`
method and `_generate_numforms`.

- [ ] **Step 4: Run the parity gate**

Same command as Task 4 Step 3. Expected: all PASS, zero diff.

- [ ] **Step 5: Run the full test suite**

Same as Task 4 Step 4 — this file's caller in `parity_harness.py` and
`test_full_flow_reference.py`'s `generate_numforms(session, output)` calls
need the same `session` → `session.word_pool, session.run_state` update
found in Task 4.

- [ ] **Step 6: Quality gate**

```bash
ruff check wyrdcraeft/services/morphology/generation/num_forms.py wyrdcraeft/services/morphology/generation/facade.py
.venv/bin/mypy wyrdcraeft/services/morphology/generation/num_forms.py wyrdcraeft/services/morphology/generation/facade.py
make napoleon-gate
```

- [ ] **Step 7: Commit**

```bash
git add wyrdcraeft/services/morphology/generation/num_forms.py wyrdcraeft/services/morphology/generation/facade.py tests/
git commit -m "refactor: migrate numeral generation from GeneratorSession to WordPool/GenerationRunState"
```

---

### Task 6: Migrate `generation/noun_forms.py`

**Files:**
- Modify: `wyrdcraeft/services/morphology/generation/noun_forms.py` (the noun-generation entrypoint spanning roughly L1320-1424, plus `_gen_r_stem_faeder`/`_gen_r_stem_brothor`/`_gen_r_stem_modor`/`_gen_r_stem_dohtor`/`_gen_r_stem_sweostor` at L1370-1378 if they independently touch `session`)
- Modify: `wyrdcraeft/services/morphology/generation/facade.py:130-143` (`generate_nouns`)

**Interfaces:**
- Consumes: `WordPool`, `GenerationRunState` (Task 1), migrated `print_one_form` (Task 3).
- Produces: `generate_nounforms(word_pool: WordPool, run_state: GenerationRunState, output_file: FormOutput, *, progress=None) -> None`.

- [ ] **Step 1: Read the entrypoint's full signature**

This plan's research confirmed the tail of the signature (ending L1324:
`session: GeneratorSession, output_file: FormOutput, *, progress:
MorphologyGenerateProgressCoordinator | None = None) -> None:`) but not its
name or earlier parameters — read
`wyrdcraeft/services/morphology/generation/noun_forms.py` starting a few
lines before L1320 to find the `def` line and confirm the function name and
any parameters before `session`.

- [ ] **Step 2: Migrate the signature and touch sites**

Rename the `session: GeneratorSession` parameter to `word_pool: WordPool,
run_state: GenerationRunState` (two params, inserted in that order in place
of the one `session` param). Update the `if TYPE_CHECKING:` import.

Update the 3 confirmed touch sites:
- L1339 `for word in session.words:` → `for word in word_pool.words:`
- L1347 `forms_written=session.output_counter,` → `forms_written=run_state.output_counter,`
- L1368 `if session.enable_r_stem_nouns and paradigm in R_STEM_PARADIGMS:` → `if run_state.enable_r_stem_nouns and paradigm in R_STEM_PARADIGMS:`

Find the calls to `_gen_r_stem_faeder`/`_gen_r_stem_brothor`/`_gen_r_stem_modor`/`_gen_r_stem_dohtor`/`_gen_r_stem_sweostor`
(L1370-1378 per this plan's research) — each currently receives `session` as
their first argument. Read each of these 5 functions' own signatures; if any
of them touch `session.<attr>` directly (this plan's inventory could not
confirm beyond "no additional grep hits were found," meaning they likely
only forward `session` further into `print_one_form` or similar), apply the
same rename pattern (parameter rename + update the `print_one_form` call
inside each to pass `run_state`). If a given `_gen_r_stem_*` function needs
`word_pool` too (check whether it reads any word list), add that parameter
as well — confirm by reading each function body before editing.

Find every remaining call to `print_one_form(session, ...)` in this file
(the entrypoint itself may call it in addition to the `_gen_r_stem_*`
helpers — grep the file for `print_one_form(session` to find all
occurrences) and rename the first argument to `run_state`.

- [ ] **Step 3: Update `facade.py`'s `generate_nouns`**

Same transformation pattern as Task 4 Step 2, targeting `generate_nouns`
and `_generate_nounforms`.

- [ ] **Step 4: Run the parity gate**

Same as Task 4 Step 3.

- [ ] **Step 5: Run the full test suite**

Same as Task 4 Step 4 — update `parity_harness.py`/`test_full_flow_reference.py`'s
`generate_nounforms(session, output)` calls the same way.

- [ ] **Step 6: Quality gate**

```bash
ruff check wyrdcraeft/services/morphology/generation/noun_forms.py wyrdcraeft/services/morphology/generation/facade.py
.venv/bin/mypy wyrdcraeft/services/morphology/generation/noun_forms.py wyrdcraeft/services/morphology/generation/facade.py
make napoleon-gate
```

- [ ] **Step 7: Commit**

```bash
git add wyrdcraeft/services/morphology/generation/noun_forms.py wyrdcraeft/services/morphology/generation/facade.py tests/
git commit -m "refactor: migrate noun generation from GeneratorSession to WordPool/GenerationRunState"
```

---

### Task 7: Migrate `generation/adj_forms.py` (largest, most delicate — 2 scalar writes)

**Files:**
- Modify: `wyrdcraeft/services/morphology/generation/adj_forms.py:1365-1481` (`generate_adjforms`), plus `_gen_comparative`, `_gen_superlative`, `_emit_weak_degree_forms`, and the separate weak-degree helper touching L995
- Modify: `wyrdcraeft/services/morphology/generation/facade.py:85-98` (`generate_adjectives`)

**Interfaces:**
- Consumes: `WordPool`, `GenerationRunState` (Task 1), migrated `print_one_form` (Task 3).
- Produces: `generate_adjforms(word_pool: WordPool, run_state: GenerationRunState, output_file: FormOutput, *, progress=None) -> None`. **Task 5 depends on this task's `enable_num_probability_carry` write landing correctly** — `num_forms.py` reads that flag (already migrated in Task 5 to read it off `run_state`); if Task 5 ran before this task in your session, re-run Task 5's parity gate after this task completes to confirm the cross-stage flag still threads correctly end to end.

- [ ] **Step 1: Migrate `generate_adjforms`'s signature**

Change (L1365-1157... i.e. L1365-1157 is wrong, use L1365 onward per this
plan's confirmed signature):
```python
def generate_adjforms(  # noqa: PLR0912
    session: GeneratorSession,
    output_file: FormOutput,
    *,
    progress: MorphologyGenerateProgressCoordinator | None = None,
) -> None:
```
to:
```python
def generate_adjforms(  # noqa: PLR0912
    word_pool: WordPool,
    run_state: GenerationRunState,
    output_file: FormOutput,
    *,
    progress: MorphologyGenerateProgressCoordinator | None = None,
) -> None:
```
Update the `if TYPE_CHECKING:` import.

Update the entrypoint-level touch sites:
- L1389 `for w in session.adjectives` → `for w in word_pool.adjectives`
- L1392 `use_perl_hash_order = len(session.adjectives) > len(session.words)` → `use_perl_hash_order = len(word_pool.adjectives) > len(word_pool.words)`
- L1399 `forms_written=session.output_counter,` → `forms_written=run_state.output_counter,`
- L1481 `session.enable_num_probability_carry = True` → `run_state.enable_num_probability_carry = True`

- [ ] **Step 2: Migrate `_gen_comparative`, `_gen_superlative`, `_emit_weak_degree_forms`**

Read each function's exact signature (the inventory confirmed line numbers
of their `session.*` touches but not their full parameter lists — read
lines surrounding L1199 for `_gen_comparative`, L1331 for `_gen_superlative`,
and the function containing L354 for `_emit_weak_degree_forms`). Each takes
`session: GeneratorSession` — rename to `word_pool: WordPool, run_state:
GenerationRunState` (both, since this file touches both types across these
helpers) unless a given function turns out to need only one (confirm from
its actual body).

Update:
- L354 `session.perl_probability = prob` → `run_state.perl_probability = prob` (inside `_emit_weak_degree_forms`)
- L1199 `len(session.adjectives) > len(session.words)` → `len(word_pool.adjectives) > len(word_pool.words)` (inside `_gen_comparative`)
- L1331 `len(session.adjectives) > len(session.words)` → `len(word_pool.adjectives) > len(word_pool.words)` (inside `_gen_superlative`)

Update every call among these 3 functions and `generate_adjforms` that
passes `session` to `_gen_comparative`, `_gen_superlative`, or
`_emit_weak_degree_forms` (this plan confirmed call sites at L363, L1210,
L1342, L1471 — read each and pass `word_pool, run_state` in place of
`session`, in that order, matching the new signatures from this step).

Update every remaining `print_one_form(session, ...)` call in this file
(grep for `print_one_form(session`) to pass `run_state`.

- [ ] **Step 3: Migrate the separate weak-degree helper touching L995**

This plan's inventory noted a participle/pronoun-adjacent weak-degree
emission loop at L995 (`session.perl_probability = int(prob)`) that shares
the module but wasn't confirmed to be directly under `generate_adjforms`'s
call chain. Locate its enclosing function (read the file around L995 to
find the `def`), apply the same `session` → `run_state` rename to its
signature and this touch site, and update its caller(s) the same way.

- [ ] **Step 4: Update `facade.py`'s `generate_adjectives`**

Same transformation pattern as Task 4 Step 2, targeting `generate_adjectives`
and `_generate_adjforms`.

- [ ] **Step 5: Run the parity gate**

Same as Task 4 Step 3 — this is the highest-risk generator file (2 distinct
scalar writes plus the cross-stage flag consumed by `num_forms.py`); if this
step fails, do not proceed — diff the actual vs. expected snapshot output to
find exactly which row diverges before making further changes.

- [ ] **Step 6: Run the full test suite**

Same as Task 4 Step 4 — update `parity_harness.py`/`test_full_flow_reference.py`'s
`generate_adjforms(session, output)` calls the same way.

- [ ] **Step 7: Re-verify Task 5's cross-stage flag** (see Interfaces above)

Run: `.venv/bin/pytest tests/morphology/test_full_flow_reference.py -v -k "full"`

Confirm the full-flow test (which runs verb → adjective → adverb → numeral
→ noun in sequence, per `parity_harness.py`'s `full_flow_rows`) still passes
— this is the test that actually exercises `adj_forms.py` setting
`enable_num_probability_carry` and `num_forms.py` reading it back within the
same run, now both going through `run_state` instead of `session`.

- [ ] **Step 8: Quality gate**

```bash
ruff check wyrdcraeft/services/morphology/generation/adj_forms.py wyrdcraeft/services/morphology/generation/facade.py
.venv/bin/mypy wyrdcraeft/services/morphology/generation/adj_forms.py wyrdcraeft/services/morphology/generation/facade.py
make napoleon-gate
```

- [ ] **Step 9: Commit**

```bash
git add wyrdcraeft/services/morphology/generation/adj_forms.py wyrdcraeft/services/morphology/generation/facade.py tests/
git commit -m "refactor: migrate adjective generation from GeneratorSession to WordPool/GenerationRunState"
```

---

### Task 8: Migrate the verb path (`common.py`'s `VerbFormGenerator`, `verb_engine.py`, `participles.py`)

**Files:**
- Modify: `wyrdcraeft/services/morphology/generation/common.py:135-~250` (`VerbFormGenerator.__init__`, `.generate()`) plus its forwarding call sites at L512, L565, L617, L659, L693-699, L1541, L1576
- Modify: `wyrdcraeft/services/morphology/generation/verb_engine.py` (full file, 65 lines — shown in full earlier this session)
- Modify: `wyrdcraeft/services/morphology/generation/participles.py:105-149` (`add_participle_to_adjectives`)
- Modify: `wyrdcraeft/services/morphology/generation/facade.py:70-83` (`generate_verbs`)
- Modify: `tests/morphology/test_generation_branches.py` (imports `VerbFormGenerator` directly, 6 `GeneratorSession()` constructions)

**Interfaces:**
- Consumes: `WordPool`, `GenerationRunState` (Task 1), migrated `print_one_form`/other `form_rows.py` functions (Task 3).
- Produces: `VerbFormOrchestrator(word_pool: WordPool, run_state: GenerationRunState, output_file: FormOutput, *, progress=None)`, `VerbFormGenerator(word_pool: WordPool, run_state: GenerationRunState, output_file: FormOutput, *, progress=None)`.

- [ ] **Step 1: Migrate `participles.py`'s `add_participle_to_adjectives`**

Change:
```python
def add_participle_to_adjectives(
    session: GeneratorSession,
    *,
    word: Word,
    prefix: str,
    form_parts: str,
    is_past: bool,
) -> None:
```
to:
```python
def add_participle_to_adjectives(
    word_pool: WordPool,
    *,
    word: Word,
    prefix: str,
    form_parts: str,
    is_past: bool,
) -> None:
```
Update the `if TYPE_CHECKING:` import from `GeneratorSession` to `WordPool`.
Update the docstring's `Args:` line and `Side Effects:` line to reference
`word_pool`/`WordPool.append_participle` instead of `session`/`session.adjectives`.

Change the body:
```python
    if perl_numify(prefix) != perl_numify(word.prefix):
        return

    session.adjectives.append(
        build_participle_adjective(
            word=word,
            prefix=prefix,
            form_parts=form_parts,
            is_past=is_past,
        )
    )
```
to:
```python
    if perl_numify(prefix) != perl_numify(word.prefix):
        return

    word_pool.append_participle(
        build_participle_adjective(
            word=word,
            prefix=prefix,
            form_parts=form_parts,
            is_past=is_past,
        )
    )
```
(this uses the `WordPool.append_participle` method introduced in Task 1
instead of the raw `.adjectives.append(...)` call — matching the approved
design)

- [ ] **Step 2: Migrate `VerbFormGenerator` in `common.py`**

Read `VerbFormGenerator.__init__` (around L230-237, confirmed this session)
and `.generate()` (around L185-210) in full before editing — this plan's
research confirmed the constructor stores `self.session = session` (L185)
and `.generate()` reads `self.session.words` (L193) and
`self.session.output_counter` (L200), but did not read every line of
`.generate()`'s body.

Change the constructor:
```python
    def __init__(
        self,
        session: GeneratorSession,
        output_file: FormOutput,
        *,
        progress: MorphologyGenerateProgressCoordinator | None = None,
    ) -> None:
```
to:
```python
    def __init__(
        self,
        word_pool: WordPool,
        run_state: GenerationRunState,
        output_file: FormOutput,
        *,
        progress: MorphologyGenerateProgressCoordinator | None = None,
    ) -> None:
```
and its body from `self.session = session` to `self.word_pool = word_pool`
plus `self.run_state = run_state` (two attributes replacing one). Update the
constructor's docstring `Args:` accordingly.

Update `.generate()`'s 2 confirmed touch sites: `for word in
self.session.words:` → `for word in self.word_pool.words:`; `forms_written=
self.session.output_counter,` → `forms_written=self.run_state.output_counter,`.

Update every one of the 7 forwarding call sites confirmed this session:
- L512 `self.session,` → replace with whatever the surrounding call
  actually needs — this forwards into `_generate_and_print_form` (Task 3's
  migrated `generate_and_print_form`, which now takes `run_state`), so
  change to `self.run_state,`
- L565 `self.session,` → into `_emit_form_for_context_row` (Task 3's
  `emit_form_for_context`, takes `run_state`) → `self.run_state,`
- L617 `self.session,` → into `_emit_sound_changed_form_for_context_row`
  (Task 3's `emit_sound_changed_form_for_context`, takes `run_state`) →
  `self.run_state,`
- L659 `self.session,` → into `_emit_imsg_for_context_row` (Task 3's
  `emit_imsg_for_context`, takes `run_state`) → `self.run_state,`
- L693-694 `_add_participle_to_adjectives_session(self.session, ...)` → this
  calls `participles.add_participle_to_adjectives`, migrated in Step 1 above
  to take `word_pool` → change to
  `_add_participle_to_adjectives_session(self.word_pool, ...)`
- L1541 `self.session,` → into `_generate_and_print_form_with_sound_changes_row`
  (Task 3's `generate_and_print_form_with_sound_changes`, takes `run_state`)
  → `self.run_state,`
- L1576 `self.session,` → into `_generate_and_print_manual` (Task 3's
  `generate_and_print_manual`, takes `run_state`) → `self.run_state,`

Before making each of these 7 changes, read the immediately surrounding
lines (a few lines before and after each) to confirm which of
`self.word_pool`/`self.run_state` the target function now actually expects,
per Task 3's and this task's own signature changes — do not assume the
mapping above is complete without checking, since some of these call sites
may pass additional context alongside `self.session,` that this plan's
research did not capture in full.

- [ ] **Step 3: Migrate `verb_engine.py`**

This file is a pure pass-through (confirmed this session, zero direct
`session.*` touches) — but its constructor and `.generate()` forward
`self._session` into `VerbFormGenerator`, whose signature just changed in
Step 2. Change:
```python
    def __init__(
        self,
        session: GeneratorSession,
        output_file: FormOutput,
        *,
        progress: MorphologyGenerateProgressCoordinator | None = None,
    ) -> None:
        """
        Bind one session, output sink, and optional progress coordinator.

        Args:
            session: Active generation session.
            output_file: Output sink receiving generated rows.

        Keyword Args:
            progress: Optional live progress coordinator.

        """
        #: Active generation session.
        self._session = session
        #: Output sink receiving generated rows.
        self._output_file = output_file
        #: Optional live progress coordinator.
        self._progress = progress

    def generate(self) -> None:
        """Generate all verb forms using the legacy parity engine."""
        generator = VerbFormGenerator(
            self._session,
            self._output_file,
            progress=self._progress,
        )
        generator.generate()
```
to:
```python
    def __init__(
        self,
        word_pool: WordPool,
        run_state: GenerationRunState,
        output_file: FormOutput,
        *,
        progress: MorphologyGenerateProgressCoordinator | None = None,
    ) -> None:
        """
        Bind one word pool, run state, output sink, and optional progress coordinator.

        Args:
            word_pool: Categorized word pool for this run.
            run_state: Cross-stage scalar run state for this run.
            output_file: Output sink receiving generated rows.

        Keyword Args:
            progress: Optional live progress coordinator.

        """
        #: Categorized word pool for this run.
        self._word_pool = word_pool
        #: Cross-stage scalar run state for this run.
        self._run_state = run_state
        #: Output sink receiving generated rows.
        self._output_file = output_file
        #: Optional live progress coordinator.
        self._progress = progress

    def generate(self) -> None:
        """Generate all verb forms using the legacy parity engine."""
        generator = VerbFormGenerator(
            self._word_pool,
            self._run_state,
            self._output_file,
            progress=self._progress,
        )
        generator.generate()
```
Update the class docstring's `Args:` block (near the top of the class) the
same way, and update the `if TYPE_CHECKING:` import.

- [ ] **Step 4: Update `facade.py`'s `generate_verbs`**

Change:
```python
    def generate_verbs(self) -> None:
        """
        ...
        """
        _generate_vbforms(self._session, self._output_file, progress=self._progress)
```
to:
```python
    def generate_verbs(self) -> None:
        """
        ...
        """
        _generate_vbforms(
            self._session.word_pool,
            self._session.run_state,
            self._output_file,
            progress=self._progress,
        )
```
Note `_generate_vbforms` is imported from `.common` as `generate_vbforms`
(the module-level thin wrapper at `common.py` L1924) — confirm whether that
wrapper itself needs updating too (read `common.py` around L1924; if it just
does `VerbFormOrchestrator(session, output_file, progress=progress).generate()`,
change it the same way to unpack `session.word_pool`/`session.run_state` and
call the newly-signatured `VerbFormOrchestrator`).

- [ ] **Step 5: Update `tests/morphology/test_generation_branches.py`**

This file imports `VerbFormGenerator` directly and constructs
`GeneratorSession()` 6 times across its 43 tests. Grep the file for
`VerbFormGenerator(` and update every call to pass `session.word_pool,
session.run_state` instead of `session`. Also grep for any direct
`session.adjectives`/`session.words` assertions following a
`VerbFormGenerator(...).generate()` call — these keep working unchanged via
Task 1's forwarding properties, no edit needed for assertions, only for the
constructor calls themselves.

- [ ] **Step 6: Run the parity gate**

Same as Task 4 Step 3.

- [ ] **Step 7: Run the full test suite**

Same as Task 4 Step 4 — update `parity_harness.py`/`test_full_flow_reference.py`'s
`generate_vbforms(session, output)` calls the same way (unpack
`session.word_pool, session.run_state`).

- [ ] **Step 8: Quality gate**

```bash
ruff check wyrdcraeft/services/morphology/generation/common.py wyrdcraeft/services/morphology/generation/verb_engine.py wyrdcraeft/services/morphology/generation/participles.py wyrdcraeft/services/morphology/generation/facade.py tests/morphology/test_generation_branches.py
.venv/bin/mypy wyrdcraeft/services/morphology/generation/common.py wyrdcraeft/services/morphology/generation/verb_engine.py wyrdcraeft/services/morphology/generation/participles.py
make napoleon-gate
```

- [ ] **Step 9: Commit**

```bash
git add wyrdcraeft/services/morphology/generation/common.py wyrdcraeft/services/morphology/generation/verb_engine.py wyrdcraeft/services/morphology/generation/participles.py wyrdcraeft/services/morphology/generation/facade.py tests/morphology/test_generation_branches.py tests/
git commit -m "refactor: migrate verb generation path from GeneratorSession to WordPool/GenerationRunState"
```

---

### Task 9: Final orchestration cleanup — `progress.py`, `build_runner.py`, remaining tests

**Files:**
- Modify: `wyrdcraeft/services/morphology/progress.py:213-279` (`MorphologyGenerateProgressCoordinator.compute_stage_totals_for_session`)
- Modify: `wyrdcraeft/services/morphology/build_runner.py:77-90` (`_current_stage_total`)
- Modify: `tests/morphology/parity_harness.py` and `tests/morphology/test_full_flow_reference.py` if not already fully updated by Tasks 4-8 (these call all 6 stage functions in sequence — confirm every call now unpacks `session.word_pool`/`session.run_state` correctly)

**Interfaces:**
- Consumes: `WordPool` from Task 1.
- Produces: `MorphologyGenerateProgressCoordinator.compute_stage_totals_for_session(word_pool: WordPool) -> dict[MorphologyStage, int]` — this is the last remaining direct-attribute-touch call site identified in the original inventory; after this task, `GeneratorSession` should have zero direct external readers of its word-pool/run-state attributes outside `build_runner.py` itself (which legitimately owns the session as its per-run orchestrator).

- [ ] **Step 1: Migrate `compute_stage_totals_for_session`**

Change the classmethod signature:
```python
    @classmethod
    def compute_stage_totals_for_session(
        cls,
        session: GeneratorSession,
    ) -> dict[MorphologyStage, int]:
```
to:
```python
    @classmethod
    def compute_stage_totals_for_session(
        cls,
        word_pool: WordPool,
    ) -> dict[MorphologyStage, int]:
```
Update the `if TYPE_CHECKING:` import from `GeneratorSession` to `WordPool`.
Update the method body — every `session.manual_forms`/`session.words`/
`session.adjectives` reference (5 confirmed touch sites: L261, L264, L270,
L275-277) becomes `word_pool.manual_forms`/`word_pool.words`/
`word_pool.adjectives` respectively. Update the docstring's `Args:` line.

- [ ] **Step 2: Update `build_runner.py`'s `_current_stage_total`**

Change:
```python
def _current_stage_total(session: GeneratorSession, stage: MorphologyStage) -> int:
```
to accept and forward `session.word_pool`:
```python
def _current_stage_total(session: GeneratorSession, stage: MorphologyStage) -> int:
```
(keep this function's own signature unchanged — it's an internal
`build_runner.py` helper that legitimately owns the whole `session`, per
this plan's scope decision that `build_runner.py`'s own orchestration code
doesn't need conversion) — only change its call to
`MorphologyGenerateProgressCoordinator.compute_stage_totals_for_session(session)`
to `compute_stage_totals_for_session(session.word_pool)`.

- [ ] **Step 3: Confirm remaining test callers**

Grep `tests/morphology/parity_harness.py` and
`tests/morphology/test_full_flow_reference.py` for every call to
`output_manual_forms`, `generate_vbforms`, `generate_adjforms`,
`generate_advforms`, `generate_numforms`, `generate_nounforms` — confirm
each now passes `session.word_pool, session.run_state` (or, for
`output_manual_forms`, the same two-argument form established in Task 3)
instead of a bare `session`. If Tasks 4-8 already updated these (likely, per
each task's own Step covering "the full test suite"), this step should find
nothing left to change — treat any remaining bare-`session` call as a bug
introduced by an earlier task and fix it here.

- [ ] **Step 4: Run the parity gate**

Same as Task 4 Step 3.

- [ ] **Step 5: Run the full test suite**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`

Expected: all pass, count matches the running total from Task 8 (no
regressions across the whole 9-task migration).

- [ ] **Step 6: Quality gate**

```bash
ruff check wyrdcraeft/services/morphology/progress.py wyrdcraeft/services/morphology/build_runner.py
.venv/bin/mypy wyrdcraeft/services/morphology/progress.py wyrdcraeft/services/morphology/build_runner.py
make napoleon-gate
```

- [ ] **Step 7: Run graphify and confirm the coupling reduction**

Run: `graphify update .`

Open `graphify-out/GRAPH_REPORT.md`'s God Nodes section — confirm
`GeneratorSession`'s edge count has dropped materially from its pre-plan
value of 176, and that `Word`'s edge count (previously 164, driven by the
same reach-in call sites) has also dropped.

- [ ] **Step 8: Commit**

```bash
git add wyrdcraeft/services/morphology/progress.py wyrdcraeft/services/morphology/build_runner.py tests/
git commit -m "refactor: migrate progress-coordinator stage totals from GeneratorSession to WordPool"
```

- [ ] **Step 9: Update ADR 0008**

Add a `## Decision` note to `docs/adr/0008-architecture-review-2026-08-01.md`
recording that candidate #1 (`GeneratorSession`) was implemented via this
plan, split into `WordPool` + `GenerationRunState`, with a link to this plan
file and a summary of the before/after edge counts from Step 7 — following
the same pattern used for candidates #2 and #3 in that ADR.
