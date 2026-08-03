# Morphology Generation Class Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement ADR 0009 (`docs/adr/0009-morphology-generation-class-refactor.md`):
collapse the redirection layers and callback-threaded verb generation in
`wyrdcraeft/services/morphology/generation/` into cohesive, human-readable
classes, while preserving byte-for-byte output parity with the existing
Perl-derived generator at every step.

**Architecture:** `dispatch.py` and `common.py`'s `generate_vbforms()` /
`verb_engine.py`'s `VerbFormOrchestrator` are pure redirection and get
deleted, leaving `facade.py`'s `MorphologyGenerationFacade` as the one public
entrypoint. Each part-of-speech generator module (`adv_forms.py`,
`num_forms.py`, `noun_forms.py`, `adj_forms.py`) becomes one class with a
`generate()` method and a paradigm-dispatch table instead of a grab-bag of
`_gen_*` functions selected by an `elif re.search(...)` chain. The existing
~1,800-line `common.VerbFormGenerator` class (which already groups its
~49 methods by a `_strong_*`/`_weak_*` naming convention, confirmed via
structural read this session) gets split along that existing seam into
`VerbFormGenerator` (paradigm/word/variant/part traversal only),
`StrongVerbGenerator`, and `WeakVerbGenerator`. Genuinely shared row/sound-
change emission stays exactly where it already lives — `form_rows.py`,
`sound_changes.py`, `sound_dispatch_flow.py` (confirmed this session:
`form_rows.py` depends directly on `sound_dispatch_flow.py`, and several of
`VerbFormGenerator`'s current methods are themselves thin one-line wrappers
forwarding into `form_rows.py`/`participles.py` — those wrapper methods are
deleted, not relocated, and their callers call the shared functions
directly).

This is a **structural refactor with zero intended behavior change** — no
step in this plan writes a new failing unit test for new behavior (there is
no new behavior). Every task instead re-runs the existing golden-path parity
test after its structural change and requires **zero diff**.

**Tech Stack:** Python 3, pytest, ruff, mypy, graphify (already installed at
`graphify-out/`), the project's `.venv`.

**Task dependency order:** Task 1 (delete `dispatch.py`, land the facade-only
seam every other task builds on) → Tasks 2-5 (one PoS generator class each,
independent of each other and of Task 1 only in the sense that they don't
depend on each other; ordered smallest-to-largest: adverbs → numerals →
nouns → adjectives) → Task 6 (verb generation collapse, the largest and
riskiest task, done after the simpler PoS tasks establish the pattern) →
Task 7 (delete the now-empty `generators/` directory).

## Global Constraints

- **Golden-path parity gate (non-negotiable, every task):** after each
  task's code changes, run:
  ```bash
  .venv/bin/pytest tests/morphology/test_parity_harness.py -v
  ```
  `test_parity_harness_matches_subset_snapshot` must PASS with **zero**
  diff — it SHA256-hashes canonicalized generation output against
  `tests/morphology/data/full_flow_subset.jsonl.gz`. A single differing byte
  in emitted output is a hard stop: do not proceed to the next task, and do
  not "fix" a mismatch by regenerating the snapshot — find and fix the
  behavior regression instead. Per ADR 0009 this is the designated
  golden-path check for this refactor.
- **Full suite, every task:** `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`
  must pass with the same pass count as immediately before the task (record
  the exact count from your own run before starting each task's Step 1 — do
  not assume a number from a prior session). No new failures, no newly
  skipped tests.
- **Any remaining old-signature caller shows up as `TypeError`/`AttributeError`
  at test time** — Python does not silently accept a mismatched call. If the
  full-suite run in a task's step raises either, grep the traceback's
  file for the migrated name and fix that call site before proceeding; do
  not special-case or skip the failing test.
- Post-implementation quality gate (Python files only, from `AGENTS.md`):
  `ruff check` on touched files, `.venv/bin/mypy` on touched files,
  `make napoleon-gate` — fix all reported problems before finishing each
  task.
- No monkey-patching, runtime patching, startup hooks, or other indirection
  to dodge parity or doc-gate friction — fix the root cause in the correct
  source file (`AGENTS.md` Implementation Priority).
- Keep every existing napoleon-style `#:` attribute docstring and
  `Args:`/`Keyword Args:`/`Side Effects:` docstring section intact on any
  function/method whose signature changes — update parameter names to match,
  do not delete the section.
- `query.py`, `probability.py`, `form_fk_resolver.py`, `sinks.py`,
  `form_rows.py`, and `form_assembly.py` are **out of scope for this plan** —
  no task below touches them except to call their existing public functions
  the same way current code does.
- After Task 7: run `graphify update .` to keep the knowledge graph current.

---

## File Structure

- **Task 1:** `wyrdcraeft/services/morphology/generation/dispatch.py` (deleted), `wyrdcraeft/services/morphology/reference_snapshots.py`, `wyrdcraeft/services/morphology/build_runner.py`, `tests/morphology/parity_harness.py`, `tests/morphology/test_form_generation_reference.py`, `tests/morphology/test_generation_package_imports.py`, `tests/morphology/test_query_service.py`, `tests/morphology/test_full_flow_reference.py`, `scripts/morphology/generate_refactor_baseline.py`, `scripts/morphology/profile_adj_stage.py`
- **Task 2:** `wyrdcraeft/services/morphology/generation/adv_forms.py`, `wyrdcraeft/services/morphology/generation/facade.py` (`generate_adverbs` only)
- **Task 3:** `wyrdcraeft/services/morphology/generation/num_forms.py`, `facade.py` (`generate_numerals` only)
- **Task 4:** `wyrdcraeft/services/morphology/generation/noun_forms.py`, `facade.py` (`generate_nouns` only)
- **Task 5:** `wyrdcraeft/services/morphology/generation/adj_forms.py`, `facade.py` (`generate_adjectives` only)
- **Task 6:** `wyrdcraeft/services/morphology/generation/common.py` (rewritten), `wyrdcraeft/services/morphology/generation/verb_engine.py` (deleted), `wyrdcraeft/services/morphology/generation/strong_inflections.py`, `strong_principal_flow.py`, `strong_derivation_flow.py`, `weak_inflections.py`, `weak_principal_flow.py`, `weak_derivation_flow.py`, `paradigm_flow.py` (all deleted, logic folded into `common.py`'s new classes — `sound_changes.py`/`sound_dispatch_flow.py` are NOT deleted, see Task 6's correction note), `facade.py` (`generate_verbs` only), `tests/morphology/test_generation_branches.py`
- **Task 7:** `wyrdcraeft/services/morphology/generators/` (whole directory deleted)

---

### Task 1: Delete `dispatch.py`, migrate all 9 importers to the facade

**Files:**
- Delete: `wyrdcraeft/services/morphology/generation/dispatch.py`
- Modify: `wyrdcraeft/services/morphology/reference_snapshots.py` (3 call sites)
- Modify: `wyrdcraeft/services/morphology/build_runner.py` (per-stage `generator=` callables)
- Modify: `tests/morphology/parity_harness.py`, `tests/morphology/test_form_generation_reference.py`, `tests/morphology/test_query_service.py`, `tests/morphology/test_full_flow_reference.py` (aggregate-call swap)
- Modify: `tests/morphology/test_generation_package_imports.py` (rewrite the smoke test)
- Modify: `scripts/morphology/generate_refactor_baseline.py`, `scripts/morphology/profile_adj_stage.py` (individual-method swap)

**Interfaces:**
- Consumes: `MorphologyGenerationFacade` (already exists in `facade.py`, unchanged by this task) with methods `output_manual_forms()`, `generate_verbs()`, `generate_adjectives()`, `generate_adverbs()`, `generate_numerals()`, `generate_nouns()`, `generate_all_forms()`.
- Produces: nothing new — this task only removes `dispatch.py`'s free-function surface. Every later task's facade methods (`generate_adverbs`, `generate_numerals`, `generate_nouns`, `generate_adjectives`, `generate_verbs`) keep their current names/signatures; Tasks 2-6 only change what those methods delegate to internally.

- [ ] **Step 1: Record your baseline**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q` and note the exact
"N passed" count. You will compare against this after Step 6.

- [ ] **Step 2: Migrate the four call sites that call all six functions in `generate_all_forms()` order**

`tests/morphology/parity_harness.py` — change:
```python
from wyrdcraeft.services.morphology.generation.dispatch import (
    generate_adjforms,
    generate_advforms,
    generate_nounforms,
    generate_numforms,
    generate_vbforms,
    output_manual_forms,
)
```
and the body of `full_flow_rows`:
```python
def full_flow_rows(session: GeneratorSession) -> list[dict[str, str]]:
    output = io.StringIO()
    output_manual_forms(session, output)
    generate_vbforms(session, output)
    generate_adjforms(session, output)
    generate_advforms(session, output)
    generate_numforms(session, output)
    generate_nounforms(session, output)
    return canonicalize_form_rows(parse_form_output(output.getvalue()))
```
to:
```python
from wyrdcraeft.services.morphology.generation.facade import (
    MorphologyGenerationFacade,
)
```
```python
def full_flow_rows(session: GeneratorSession) -> list[dict[str, str]]:
    output = io.StringIO()
    MorphologyGenerationFacade(session, output).generate_all_forms()
    return canonicalize_form_rows(parse_form_output(output.getvalue()))
```
(`generate_all_forms()`'s body already calls `output_manual_forms()`,
`generate_verbs()`, `generate_adjectives()`, `generate_adverbs()`,
`generate_numerals()`, `generate_nouns()` in exactly this order.)

`tests/morphology/test_query_service.py`, `tests/morphology/test_form_generation_reference.py`,
`tests/morphology/test_full_flow_reference.py` — each imports the same six
functions from `dispatch` and calls them in the same order at its own call
site(s). Apply the identical transformation: replace the `dispatch` import
with `from wyrdcraeft.services.morphology.generation.facade import
MorphologyGenerationFacade`, and replace each `output_manual_forms(session,
output); generate_vbforms(session, output); generate_adjforms(session,
output); generate_advforms(session, output); generate_numforms(session,
output); generate_nounforms(session, output)` sequence with
`MorphologyGenerationFacade(session, output).generate_all_forms()`.

`wyrdcraeft/services/morphology/reference_snapshots.py` has **three**
separate call sites with this exact six-function sequence (not one) — apply
the same transformation at each of the three locations.

- [ ] **Step 3: Migrate `build_runner.py` — both `_run_build_stages`'s six call sites AND `_run_generation_stage`'s internal call**

`build_runner.py` does not call the six functions directly. `_run_build_stages`
(around line 130) passes each one as a `generator=` keyword into
`_run_generation_stage`, six times:
```python
from wyrdcraeft.services.morphology.generation.dispatch import (
    generate_adjforms,
    generate_advforms,
    generate_nounforms,
    generate_numforms,
    generate_vbforms,
    output_manual_forms,
)
...
def _run_build_stages(
    *,
    session: GeneratorSession,
    output_sink: ParityFormOutput,
    progress: MorphologyGenerateProgressCoordinator,
    profiler: MorphologyBuildProfiler,
) -> None:
    _run_generation_stage(
        session=session,
        output_sink=output_sink,
        progress=progress,
        stage=MorphologyStage.MANUAL,
        generator=output_manual_forms,
        profiler=profiler,
    )
    _run_generation_stage(
        ...
        stage=MorphologyStage.VERBS,
        generator=generate_vbforms,
        ...
    )
    # ...same pattern for ADJECTIVES/generate_adjforms, ADVERBS/generate_advforms,
    # NUMERALS/generate_numforms, NOUNS/generate_nounforms
```
And `_run_generation_stage` itself (around line 97) calls `generator` with
**three arguments**, not zero:
```python
def _run_generation_stage(  # noqa: PLR0913
    *,
    session: GeneratorSession,
    output_sink: ParityFormOutput,
    progress: MorphologyGenerateProgressCoordinator,
    stage: MorphologyStage,
    generator: Callable[..., None],
    profiler: MorphologyBuildProfiler,
) -> None:
    profiler.begin_stage(stage, forms_written=session.output_counter)
    try:
        progress.start_stage(stage, total=_current_stage_total(session, stage))
        generator(session, output_sink, progress=progress)
        progress.finish_stage(stage)
    finally:
        profiler.end_stage(stage, forms_written=session.output_counter)
```
So a bare `generator=facade.generate_verbs` swap (a zero-arg bound method)
would break here — `_run_generation_stage` would call it as
`facade.generate_verbs(session, output_sink, progress=progress)`, raising
`TypeError: generate_verbs() takes 1 positional argument but 3 were given`.
Both places must change together:

1. In `_run_build_stages`, construct one facade right after the docstring,
   before the six `_run_generation_stage(...)` calls (this function already
   receives `session`, `output_sink`, `progress` as its own params, so this
   works correctly for both of `_run_build_stages`'s two call sites further
   down the file, which pass different `output_sink` values — one wrapping
   a `CompositeSink(TsvParitySink(...), sqlite_sink)`, one just
   `sqlite_sink`):
   ```python
   facade = MorphologyGenerationFacade(session, output_sink, progress=progress)
   ```
   Remove the `dispatch` import and add
   `from .generation.facade import MorphologyGenerationFacade` (match
   whatever relative import path the existing `dispatch` import used).
2. Change each of the six `generator=` values to the corresponding bound
   facade method — note the adverb/numeral method names are
   `generate_adverbs`/`generate_numerals`, not `generate_advforms`/
   `generate_numforms`:
   ```python
           generator=facade.output_manual_forms,
   ...
           generator=facade.generate_verbs,
   ...
           generator=facade.generate_adjectives,
   ...
           generator=facade.generate_adverbs,
   ...
           generator=facade.generate_numerals,
   ...
           generator=facade.generate_nouns,
   ```
3. In `_run_generation_stage`, change the call from
   `generator(session, output_sink, progress=progress)` to `generator()` —
   the facade already closed over `session`/`output_sink`/`progress` at
   construction in step 1, so no arguments are needed or accepted anymore.
   Update the `generator` parameter's type annotation from
   `Callable[..., None]` to `Callable[[], None]` to reflect this, and update
   the `Keyword Args:` docstring line for `generator` (currently "Callable
   that performs the stage work.") if it describes taking arguments —
   confirm by reading the current docstring text before editing.

- [ ] **Step 4: Migrate the two scripts that only exercise a subset of stages**

`scripts/morphology/profile_adj_stage.py` imports only
`output_manual_forms`, `generate_vbforms`, `generate_adjforms` (it profiles
just the adjective stage). Replace the `dispatch` import with a
`MorphologyGenerationFacade` construction the same way as Step 3, and change
its three call sites to `facade.output_manual_forms()`,
`facade.generate_verbs()`, `facade.generate_adjectives()` respectively
(same no-argument bound-method shape).

`scripts/morphology/generate_refactor_baseline.py` imports five of six
(`generate_adjforms`, `generate_advforms`, `generate_nounforms`,
`generate_numforms`, `generate_vbforms` — omitting `output_manual_forms`).
Apply the same transformation, calling `facade.generate_verbs()`,
`facade.generate_adjectives()`, `facade.generate_adverbs()`,
`facade.generate_numerals()`, `facade.generate_nouns()` in whatever order
the script currently calls the five free functions (preserve the existing
order — read the file to confirm it before editing).

- [ ] **Step 5: Rewrite the dispatch smoke test**

`tests/morphology/test_generation_package_imports.py` currently does:
```python
    from wyrdcraeft.services.morphology.generation.dispatch import (
        generate_vbforms,
    )

    assert callable(generate_vbforms)
```
There is no longer a `dispatch` module to smoke-test. Replace this with an
equivalent assertion against the facade:
```python
    from wyrdcraeft.services.morphology.generation.facade import (
        MorphologyGenerationFacade,
    )

    assert callable(MorphologyGenerationFacade.generate_verbs)
```
Keep the surrounding test function name and any other assertions in that
test unchanged — only replace this one import + assertion pair.

- [ ] **Step 6: Delete `dispatch.py`**

```bash
rm wyrdcraeft/services/morphology/generation/dispatch.py
```

- [ ] **Step 7: Run the golden-path parity gate**

Run: `.venv/bin/pytest tests/morphology/test_parity_harness.py -v`

Expected: `test_parity_harness_matches_subset_snapshot` PASSES with zero
diff. This task only changes *how* the six generation entrypoints are
reached (through the facade instead of `dispatch`'s free functions) — the
underlying generation code is untouched, so output must be byte-for-byte
identical.

- [ ] **Step 8: Run the full test suite**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`

Expected: identical pass count to Step 1's recorded baseline. If any test
raises `ImportError: cannot import name '...' from
'wyrdcraeft.services.morphology.generation.dispatch'` (module no longer
exists) or `ModuleNotFoundError`, that's a caller Steps 2-5 missed — grep the
whole repo for `generation.dispatch` or `generation import dispatch` to find
it and apply the same transformation pattern as the matching bucket above.

- [ ] **Step 9: Quality gate**

```bash
ruff check wyrdcraeft/services/morphology/reference_snapshots.py wyrdcraeft/services/morphology/build_runner.py tests/morphology/parity_harness.py tests/morphology/test_form_generation_reference.py tests/morphology/test_generation_package_imports.py tests/morphology/test_query_service.py tests/morphology/test_full_flow_reference.py scripts/morphology/generate_refactor_baseline.py scripts/morphology/profile_adj_stage.py
.venv/bin/mypy wyrdcraeft/services/morphology/reference_snapshots.py wyrdcraeft/services/morphology/build_runner.py
make napoleon-gate
```

- [ ] **Step 10: Commit**

```bash
git add wyrdcraeft/services/morphology/generation/dispatch.py wyrdcraeft/services/morphology/reference_snapshots.py wyrdcraeft/services/morphology/build_runner.py tests/morphology/parity_harness.py tests/morphology/test_form_generation_reference.py tests/morphology/test_generation_package_imports.py tests/morphology/test_query_service.py tests/morphology/test_full_flow_reference.py scripts/morphology/generate_refactor_baseline.py scripts/morphology/profile_adj_stage.py
git commit -m "refactor: delete generation/dispatch.py, route all callers through MorphologyGenerationFacade"
```

---

### Task 2: `AdverbFormGenerator` (smallest generator — proves the class pattern end to end)

**Files:**
- Modify: `wyrdcraeft/services/morphology/generation/adv_forms.py` (rewrite `generate_advforms` into a class)
- Modify: `wyrdcraeft/services/morphology/generation/facade.py` (`generate_adverbs` only)

**Interfaces:**
- Consumes: `WordPool`, `GenerationRunState`, `FormOutput`, `MorphologyGenerateProgressCoordinator` (all already exist, unchanged).
- Produces: `AdverbFormGenerator(word_pool, run_state, output_file, *, progress=None).generate() -> None` — the pattern (constructor injection of the same 4 params every other PoS generator already takes as free-function params, one public `generate()` method) is reused identically in Tasks 3-5.

- [ ] **Step 1: Record baseline**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`, note the pass
count.

- [ ] **Step 2: Rewrite `adv_forms.py`**

`generate_advforms` currently has this shape (single function, no `_gen_*`
helpers — the simplest of the four PoS modules):
```python
def generate_advforms(
    word_pool: WordPool,
    run_state: GenerationRunState,
    output_file: FormOutput,
    *,
    progress: MorphologyGenerateProgressCoordinator | None = None,
) -> None:
    for word in word_pool.words:
        if word.adverb == 1:
            ...  # full body: manual form emission + Co/Su degree loops
```
Replace it with:
```python
class AdverbFormGenerator:
    """
    Generates adverb surface forms (base, comparative, superlative) for one
    morphology generation run.

    Args:
        word_pool: Word pool supplying the lemmas to generate forms for.
        run_state: Mutable per-run generation state.
        output_file: Output stream receiving generated rows.

    Keyword Args:
        progress: Optional live progress coordinator.

    """

    def __init__(
        self,
        word_pool: WordPool,
        run_state: GenerationRunState,
        output_file: FormOutput,
        *,
        progress: MorphologyGenerateProgressCoordinator | None = None,
    ) -> None:
        #: Word pool supplying the lemmas to generate forms for.
        self._word_pool = word_pool
        #: Mutable per-run generation state.
        self._run_state = run_state
        #: Output stream receiving generated rows.
        self._output_file = output_file
        #: Optional live progress coordinator.
        self._progress = progress

    def generate(self) -> None:
        """
        Generate adverb forms and comparative/superlative derivatives.

        Side Effects:
            Writes generated rows to the morphology output stream.

        """
        for word in self._word_pool.words:
            if word.adverb == 1:
                self._generate_word(word)

    def _generate_word(self, word: Word) -> None:
        # Paste the exact body of the current `if word.adverb == 1:` block
        # here unchanged, replacing every `word_pool`/`run_state`/
        # `output_file`/`progress` reference with `self._word_pool`/
        # `self._run_state`/`self._output_file`/`self._progress`. Do not
        # change any regex, string literal, or conditional — this is a pure
        # mechanical extraction, not a rewrite of logic.
        ...
```
(The comment inside `_generate_word` is an instruction to the implementer,
not code to leave in the file — replace it with the real extracted body.)

Keep the module-level `import re` and any other imports the extracted body
needs. Add `if TYPE_CHECKING: from wyrdcraeft.models.morphology import Word`
if not already present (needed for the `_generate_word(self, word: Word)`
type hint).

- [ ] **Step 3: Update `facade.py`'s `generate_adverbs`**

Change:
```python
    def generate_adverbs(self) -> None:
        """..."""
        _generate_advforms(
            self._session.word_pool,
            self._session.run_state,
            self._output_file,
            progress=self._progress,
        )
```
to:
```python
    def generate_adverbs(self) -> None:
        """..."""
        AdverbFormGenerator(
            self._session.word_pool,
            self._session.run_state,
            self._output_file,
            progress=self._progress,
        ).generate()
```
(keep the existing docstring unchanged — only the body changes) and update
the import at the top of `facade.py` from
`from .adv_forms import generate_advforms as _generate_advforms` to
`from .adv_forms import AdverbFormGenerator`.

- [ ] **Step 4: Run the golden-path parity gate**

Run: `.venv/bin/pytest tests/morphology/test_parity_harness.py -v`

Expected: PASS, zero diff.

- [ ] **Step 5: Run the full test suite**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`

Expected: identical pass count to Step 1. Any `ImportError: cannot import
name 'generate_advforms'` means a test still imports the old free function
directly (check `tests/morphology/test_generation_branches.py`) — update it
to construct `AdverbFormGenerator(...).generate()` instead.

- [ ] **Step 6: Quality gate**

```bash
ruff check wyrdcraeft/services/morphology/generation/adv_forms.py wyrdcraeft/services/morphology/generation/facade.py
.venv/bin/mypy wyrdcraeft/services/morphology/generation/adv_forms.py wyrdcraeft/services/morphology/generation/facade.py
make napoleon-gate
```

- [ ] **Step 7: Commit**

```bash
git add wyrdcraeft/services/morphology/generation/adv_forms.py wyrdcraeft/services/morphology/generation/facade.py
git commit -m "refactor: collapse generate_advforms into AdverbFormGenerator"
```

---

### Task 3: `NumeralFormGenerator`

**Files:**
- Modify: `wyrdcraeft/services/morphology/generation/num_forms.py`
- Modify: `wyrdcraeft/services/morphology/generation/facade.py` (`generate_numerals` only)

**Interfaces:**
- Consumes: same constructor shape as `AdverbFormGenerator` (Task 2).
- Produces: `NumeralFormGenerator(word_pool, run_state, output_file, *, progress=None).generate() -> None`.

- [ ] **Step 1: Record baseline**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`, note pass count.

- [ ] **Step 2: Rewrite `num_forms.py`**

`num_forms.py` has three small private helpers
(`_form_from_parts`, `_num_print`, `_stem_no_ea`) plus one large
`generate_numforms` function with no `_gen_*` paradigm dispatch (it iterates
`word_pool.words` and, inline, emits noun-shaped forms when `word.noun == 1`
then adjective-shaped forms for every numeral). Convert this to:

```python
class NumeralFormGenerator:
    """
    Generates numeral surface forms — both noun-shaped cardinals (when
    ``word.noun == 1``) and adjective-shaped cardinals/ordinals (for every
    numeral) — for one morphology generation run.

    Args:
        word_pool: Word pool supplying the lemmas to generate forms for.
        run_state: Mutable per-run generation state.
        output_file: Form output sink.

    Keyword Args:
        progress: Optional live progress coordinator.

    """

    def __init__(
        self,
        word_pool: WordPool,
        run_state: GenerationRunState,
        output_file: FormOutput,
        *,
        progress: MorphologyGenerateProgressCoordinator | None = None,
    ) -> None:
        #: Word pool supplying the lemmas to generate forms for.
        self._word_pool = word_pool
        #: Mutable per-run generation state.
        self._run_state = run_state
        #: Form output sink.
        self._output_file = output_file
        #: Optional live progress coordinator.
        self._progress = progress

    def generate(self) -> None:
        """
        Generate numeral forms for every word where ``numeral == 1``.

        Side Effects:
            Writes generated rows to the morphology output stream.

        """
        for word in self._word_pool.words:
            if word.numeral != 1:
                continue
            self._generate_word(word)

    def _generate_word(self, word: Word) -> None:
        # Paste the current generate_numforms loop body (everything after
        # the `if word.numeral != 1: continue` guard) here unchanged,
        # replacing `word_pool`/`run_state`/`output_file`/`progress` with
        # `self._word_pool`/`self._run_state`/`self._output_file`/
        # `self._progress`, and replacing internal calls to the module-level
        # `_num_print(run_state, ...)` with `_num_print(self._run_state,
        # ...)` (keep `_num_print`, `_form_from_parts`, `_stem_no_ea` as
        # module-level private functions — they have no `self` state and
        # don't need to become methods).
        ...
```

- [ ] **Step 3: Update `facade.py`'s `generate_numerals`**

Same transformation pattern as Task 2 Step 3: replace the
`_generate_numforms(...)` call with `NumeralFormGenerator(...).generate()`,
update the import from `from .num_forms import generate_numforms as
_generate_numforms` to `from .num_forms import NumeralFormGenerator`.

- [ ] **Step 4: Run the golden-path parity gate**

Run: `.venv/bin/pytest tests/morphology/test_parity_harness.py -v`

Expected: PASS, zero diff.

- [ ] **Step 5: Run the full test suite**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`

Expected: identical pass count to Step 1. Fix any old-signature caller the
same way as Task 2 Step 5.

- [ ] **Step 6: Quality gate**

```bash
ruff check wyrdcraeft/services/morphology/generation/num_forms.py wyrdcraeft/services/morphology/generation/facade.py
.venv/bin/mypy wyrdcraeft/services/morphology/generation/num_forms.py wyrdcraeft/services/morphology/generation/facade.py
make napoleon-gate
```

- [ ] **Step 7: Commit**

```bash
git add wyrdcraeft/services/morphology/generation/num_forms.py wyrdcraeft/services/morphology/generation/facade.py
git commit -m "refactor: collapse generate_numforms into NumeralFormGenerator"
```

---

### Task 4: `NounFormGenerator`

**Files:**
- Modify: `wyrdcraeft/services/morphology/generation/noun_forms.py`
- Modify: `wyrdcraeft/services/morphology/generation/facade.py` (`generate_nouns` only)

**Interfaces:**
- Consumes: same constructor shape as Tasks 2-3.
- Produces: `NounFormGenerator(word_pool, run_state, output_file, *, progress=None).generate() -> None`.

- [ ] **Step 1: Record baseline**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`, note pass count.

- [ ] **Step 2: Rewrite `noun_forms.py`**

`noun_forms.py` currently has ~30 private `_gen_<paradigm>` functions (one
per noun paradigm: `_gen_word`, `_gen_hof`, `_gen_daeg`, `_gen_faet`,
`_gen_ar`, `_gen_strengu`, `_gen_hand_feld`, `_gen_sunu_duru`, `_gen_bearu`,
`_gen_bealu`, `_gen_guma`, `_gen_frea`, `_gen_tunge`, `_gen_eage`,
`_gen_wigend`, `_gen_r_stem_faeder`, `_gen_r_stem_brothor`,
`_gen_r_stem_modor`, `_gen_r_stem_dohtor`, `_gen_r_stem_sweostor`,
`_gen_stan_cynn`), a handful of `_build_stem_*` pure-string helpers, and one
`generate_nounforms` function that selects among the `_gen_*` functions via
an `elif re.search(paradigm_pattern, paradigm)` chain (the exact chain: see
the current `generate_nounforms` body for the full pattern → function
mapping — copy this mapping verbatim, do not re-derive it from paradigm
names).

Convert to:
```python
class NounFormGenerator:
    """
    Generates noun surface forms across every noun paradigm (a-stem,
    ja-stem, root nouns, ō-stem, u-stem, consonant-stem, wa-stem, weak
    n-stem, nd-stem, and opt-in r-stem) for one morphology generation run.

    Args:
        word_pool: Word pool supplying the lemmas to generate forms for.
        run_state: Mutable per-run generation state.
        output_file: The output file handle.

    Keyword Args:
        progress: Optional live progress coordinator.

    """

    def __init__(
        self,
        word_pool: WordPool,
        run_state: GenerationRunState,
        output_file: FormOutput,
        *,
        progress: MorphologyGenerateProgressCoordinator | None = None,
    ) -> None:
        #: Word pool supplying the lemmas to generate forms for.
        self._word_pool = word_pool
        #: Mutable per-run generation state.
        self._run_state = run_state
        #: The output file handle.
        self._output_file = output_file
        #: Optional live progress coordinator.
        self._progress = progress

    def generate(self) -> None:
        """
        Generate noun forms.

        Side Effects:
            Writes generated rows to the morphology output stream.

        """
        for word in self._word_pool.words:
            if not word.noun_paradigm:
                continue
            self._generate_word(word)

    def _generate_word(self, word: Word) -> None:
        # Paste the body of the current generate_nounforms function here,
        # starting from `if progress is not None:` through the end of the
        # `for _i2, paradigm in enumerate(word.noun_paradigm):` loop,
        # replacing `run_state`/`output_file`/`progress` with
        # `self._run_state`/`self._output_file`/`self._progress`, and
        # replacing every `_gen_<paradigm>(run_state, output_file, word,
        # formhash_base)` call with `self._gen_<paradigm>(word,
        # formhash_base)` (drop the now-redundant run_state/output_file args
        # since the private methods read them from self).
        ...

    def _gen_word(self, word: Word, formhash_base: dict[str, str]) -> None:
        # Paste the current module-level `_gen_word` function body here,
        # dropping the `run_state`/`output_file` parameters and replacing
        # every reference to them with `self._run_state`/`self._output_file`.
        # Repeat this exact pattern (drop run_state/output_file params,
        # replace their internal references with self._run_state/
        # self._output_file, keep every other parameter and all logic
        # unchanged) for each of: _gen_hof, _gen_daeg, _gen_faet, _gen_ar,
        # _gen_strengu, _gen_hand_feld, _gen_sunu_duru, _gen_bearu,
        # _gen_bealu, _gen_guma, _gen_frea, _gen_tunge, _gen_eage,
        # _gen_wigend, _gen_stan_cynn, _gen_r_stem_faeder,
        # _gen_r_stem_brothor, _gen_r_stem_modor, _gen_r_stem_dohtor,
        # _gen_r_stem_sweostor, and _emit_r_stem_forms (the shared r-stem
        # helper the five _gen_r_stem_* methods call).
        ...
```
Keep `_is_ge_collective`, `_form_from_parts`, `_noun_print`, and every
`_build_stem_*` helper (`_build_stem_geminate`, `_build_stem_syncope`,
`_build_stem_pl_no_ac`, `_build_stem_pl_ge_da`, `_build_stem_word_syncope`,
`_build_stem_hof_ge_da`, `_build_stem_daeg_pl`, `_build_stem_ar_sg_no_ac`,
`_build_stem_ar_sg_ge_da`, `_build_stem_ar_pl`) as module-level private
functions — none of them touch `run_state`/`output_file`, so they don't need
to become methods. `_noun_print` itself still takes `run_state` and
`output_file` explicitly as parameters; every `_gen_*` method calls it as
`_noun_print(self._run_state, self._output_file, ...)`.

The `R_STEM_PARADIGMS`, `R_STEM_FAEDER_FORMS`, `R_STEM_BROTHOR_FORMS`,
`R_STEM_DOHTOR_FORMS`, `R_STEM_MODOR_FORMS`, `R_STEM_SWEOSTOR_FORMS`
module-level constants stay exactly where they are, unchanged.

- [ ] **Step 3: Update `facade.py`'s `generate_nouns`**

Same transformation pattern as Task 2 Step 3.

- [ ] **Step 4: Run the golden-path parity gate**

Run: `.venv/bin/pytest tests/morphology/test_parity_harness.py -v`

Expected: PASS, zero diff. This is the highest-risk step in this task — 20
paradigm-specific generator functions moved into methods in one pass. If it
fails, bisect by temporarily reverting one `_gen_*` method back to a
module-level function call at a time to isolate which paradigm's migration
introduced the regression, rather than re-reading the whole diff at once.

- [ ] **Step 5: Run the full test suite**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`

Expected: identical pass count to Step 1.

- [ ] **Step 6: Quality gate**

```bash
ruff check wyrdcraeft/services/morphology/generation/noun_forms.py wyrdcraeft/services/morphology/generation/facade.py
.venv/bin/mypy wyrdcraeft/services/morphology/generation/noun_forms.py wyrdcraeft/services/morphology/generation/facade.py
make napoleon-gate
```

- [ ] **Step 7: Commit**

```bash
git add wyrdcraeft/services/morphology/generation/noun_forms.py wyrdcraeft/services/morphology/generation/facade.py
git commit -m "refactor: collapse generate_nounforms into NounFormGenerator"
```

---

### Task 5: `AdjectiveFormGenerator`

**Files:**
- Modify: `wyrdcraeft/services/morphology/generation/adj_forms.py`
- Modify: `wyrdcraeft/services/morphology/generation/facade.py` (`generate_adjectives` only)

**Interfaces:**
- Consumes: same constructor shape as Tasks 2-4.
- Produces: `AdjectiveFormGenerator(word_pool, run_state, output_file, *, progress=None).generate() -> None`.

- [ ] **Step 1: Record baseline**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`, note pass count.

- [ ] **Step 2: Rewrite `adj_forms.py`**

This is the largest PoS module (~1,500 lines). Its public entrypoint
`generate_adjforms` dispatches to one of 7 strong-paradigm functions
(`_gen_strong_manig`, `_gen_strong_halig`, `_gen_strong_wilde`,
`_gen_strong_glaed_til`, `_gen_strong_blind`, `_gen_strong_heah_thweorh`,
`_gen_strong_gearu`) via an `elif`/`re.search` chain on `paradigm`, then
unconditionally calls `_gen_weak`, and (when `word.numeral == 0 and
word.pronoun == 0`) `_gen_comparative` and `_gen_superlative`.

Convert to:
```python
class AdjectiveFormGenerator:
    """
    Generates adjective surface forms — strong/weak positive-degree
    paradigms plus comparative and superlative derivatives — for one
    morphology generation run.

    Args:
        word_pool: Word pool supplying the lemmas to generate forms for.
        run_state: Mutable per-run generation state.
        output_file: The output file handle.

    Keyword Args:
        progress: Optional live progress coordinator.

    """

    def __init__(
        self,
        word_pool: WordPool,
        run_state: GenerationRunState,
        output_file: FormOutput,
        *,
        progress: MorphologyGenerateProgressCoordinator | None = None,
    ) -> None:
        #: Word pool supplying the lemmas to generate forms for.
        self._word_pool = word_pool
        #: Mutable per-run generation state.
        self._run_state = run_state
        #: The output file handle.
        self._output_file = output_file
        #: Optional live progress coordinator.
        self._progress = progress

    def generate(self) -> None:
        """
        Generate adjective forms.

        Side Effects:
            Writes generated rows to the morphology output stream. Sets
            ``run_state.enable_num_probability_carry`` so a later
            ``NumeralFormGenerator`` stage carries the shared probability
            forward.

        """
        # Paste the current generate_adjforms function's `words = [...]`
        # filter and `use_perl_hash_order = ...` computation here unchanged
        # (they read only self._word_pool, no rename needed beyond adding
        # `self.`), then loop over `words` calling `self._generate_word(word,
        # use_perl_hash_order)` for each. Keep the final
        # `self._run_state.enable_num_probability_carry = True` line at the
        # end, exactly as today.
        ...

    def _generate_word(self, word: Word, use_perl_hash_order: bool) -> None:
        # Paste the loop body of the current generate_adjforms function
        # (progress.advance(...) call, paradigm resolution, formhash
        # construction, the manig/halig/wilde/glaed-til/blind/heah-thweorh/
        # gearu elif dispatch chain, the _gen_weak call, and the
        # comparative/superlative block) here, replacing
        # `run_state`/`output_file`/`progress` with `self._run_state`/
        # `self._output_file`/`self._progress`, and replacing each
        # `_gen_strong_*(run_state, output_file, word, formhash)` call with
        # `self._gen_strong_*(word, formhash)`, `_gen_weak(run_state,
        # output_file, word, paradigm)` with `self._gen_weak(word,
        # paradigm)`, and `_gen_comparative(word_pool, run_state,
        # output_file, word, ...)` / `_gen_superlative(...)` with
        # `self._gen_comparative(word, ...)` / `self._gen_superlative(word,
        # ...)` (drop word_pool/run_state/output_file params, read them from
        # self instead).
        ...

    # Repeat the drop-run_state/output_file-params-read-from-self pattern for
    # each of: _gen_strong_glaed_til, _gen_strong_blind,
    # _gen_strong_heah_thweorh, _gen_strong_manig, _gen_strong_halig,
    # _gen_strong_wilde, _gen_strong_gearu, _gen_weak, _gen_comparative,
    # _gen_superlative — each becomes a method with the same name (minus the
    # leading underscore's now-implicit self-binding) taking the same
    # parameters minus run_state/output_file (and minus word_pool for
    # _gen_comparative/_gen_superlative, which currently take it only to
    # read word_pool.adjectives/word_pool.words for the
    # use_perl_hash_order computation — read that from self._word_pool
    # instead).
```
Keep every pure-string/pure-data helper as a module-level private function,
unchanged (no `self` needed — none of them touch `run_state`/`output_file`/
`word_pool`): `_dedupe_preserve_first`, `_perl_hash_order`, `_form_from_parts`,
`_finalize_degree_titles`, `_expand_regular_degree_stems`,
`_build_adjective_formhash`, `_emit_weak_degree_forms` (this one *does* take
`run_state`/`output_file` — keep it module-level but have each calling
method pass `self._run_state, self._output_file` explicitly, the same way
`_noun_print` stays module-level in Task 4), `_emit_superlative_strong_forms`
(same — keep module-level, pass `self._run_state`/`self._output_file`
explicitly), `_adj_print` (same), `_build_weak_title_array`,
`_build_comparative_title_array`, `_shared_regular_degree_stems`,
`_build_superlative_title_array`. Keep every module-level constant
(`_FORM_PARTS_DELETE`, `_RE_U_SUFFIX`, `_RE_H_SUFFIX`, `_RE_VOWEL_EAO`,
`_RE_VOWEL_REPLACE`, `_RE_VOWEL_END`, `_RE_HALIG_SYNCOPE`,
`_WEAK_DEGREE_CASE_ENDINGS`, `_SP_STRONG_PROB_PLUS_1`,
`_SP_STRONG_PROB_PLUS_2`, `_SP_STRONG_CASE_ENDINGS`) exactly where they are.

- [ ] **Step 3: Update `facade.py`'s `generate_adjectives`**

Same transformation pattern as Task 2 Step 3.

- [ ] **Step 4: Run the golden-path parity gate**

Run: `.venv/bin/pytest tests/morphology/test_parity_harness.py -v`

Expected: PASS, zero diff. This is the largest single-file migration in this
plan — if it fails, bisect one `_gen_strong_*`/`_gen_weak`/
`_gen_comparative`/`_gen_superlative` method at a time (temporarily route it
back through the original module-level function signature) to isolate the
regression, same approach as Task 4 Step 4.

- [ ] **Step 5: Run the full test suite**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`

Expected: identical pass count to Step 1.

- [ ] **Step 6: Quality gate**

```bash
ruff check wyrdcraeft/services/morphology/generation/adj_forms.py wyrdcraeft/services/morphology/generation/facade.py
.venv/bin/mypy wyrdcraeft/services/morphology/generation/adj_forms.py wyrdcraeft/services/morphology/generation/facade.py
make napoleon-gate
```

- [ ] **Step 7: Commit**

```bash
git add wyrdcraeft/services/morphology/generation/adj_forms.py wyrdcraeft/services/morphology/generation/facade.py
git commit -m "refactor: collapse generate_adjforms into AdjectiveFormGenerator"
```

---

### Task 6: Collapse verb generation — rebuild `common.VerbFormGenerator`, delete the wrapper chain

This is the largest and riskiest task in this plan. Per ADR 0009, do **not**
skip the read-first step below — this task's exact boundaries depend on
what that read confirms.

**Files:**
- Modify: `wyrdcraeft/services/morphology/generation/common.py` (rewritten in place)
- Delete: `wyrdcraeft/services/morphology/generation/verb_engine.py`
- Delete: `wyrdcraeft/services/morphology/generation/strong_inflections.py`, `strong_principal_flow.py`, `strong_derivation_flow.py`, `weak_inflections.py`, `weak_principal_flow.py`, `weak_derivation_flow.py`, `paradigm_flow.py`
- Modify: `wyrdcraeft/services/morphology/generation/facade.py` (`generate_verbs` only)
- Modify: `tests/morphology/test_generation_branches.py`

**Correction from this plan's review pass — `sound_changes.py`/`sound_dispatch_flow.py`
are NOT deleted, and there is no `SoundChangeApplier` class.** Verified this
session: `form_rows.py` (declared out-of-scope shared infrastructure — see
Global Constraints) imports and calls
`sound_dispatch_flow.generate_and_print_form_with_sound_changes` and
`sound_dispatch_flow.emit_sound_changed_form_for_context` directly, at two
call sites. Deleting `sound_dispatch_flow.py` (as ADR 0009 originally
proposed) would break `form_rows.py`, which every PoS generator (adjective,
adverb, noun, numeral, verb) depends on — not a verb-only change. Also
confirmed: `common.py`'s own `VerbFormGenerator._generate_and_print_form_with_sound_changes`
method (line 1499) is itself a thin one-line wrapper forwarding to
`form_rows.generate_and_print_form_with_sound_changes` (imported at the top
of `common.py` as `_generate_and_print_form_with_sound_changes_row`) — so
`sound_changes.py`/`sound_dispatch_flow.py` were never verb-specific
"worst offender" files to begin with; they're shared infrastructure exactly
like `form_rows.py`/`form_assembly.py`, and this task leaves both files
untouched. (ADR 0009 itself should be corrected to match — out of scope for
this plan update, but flagged for a follow-up edit.)

**Interfaces:**
- Consumes: `WordPool`, `GenerationRunState`, `FormOutput`,
  `MorphologyGenerateProgressCoordinator`, `Word`, `VerbParadigm`,
  `ParadigmVariant`, `ParadigmPart` (all already exist, unchanged).
- Produces: `VerbFormGenerator(word_pool, run_state, output_file, *,
  progress=None).generate() -> None` (same public shape `facade.py` already
  calls — this task changes what's *inside* the class, not its public
  entrypoint name or constructor signature).

- [ ] **Step 1: Record baseline**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`, note pass count.

- [ ] **Step 2: Required read-first step (do not skip)**

Read `wyrdcraeft/services/morphology/generation/common.py` lines 124-1918 in
full (the entire current `VerbFormGenerator` class body) — not just method
signatures. This session confirmed the class's **method boundaries** via a
structural grep (49 methods total, listed below with their current line
offsets *within the class*, i.e. add 123 to each for the absolute line
number in `common.py`), but did **not** read every method's full body.
Before writing any code in this task, confirm for each method in the
"shared / needs a decision" bucket below whether it is used identically by
both strong and weak paths (→ stays as a shared helper) or has
strong-only/weak-only logic hidden inside a branch (→ splits into two
methods, one per class). Do not proceed to Step 3 until this is confirmed by
reading, not assumed from names.

Confirmed method inventory (line offsets relative to line 124):
- **Orchestration (stays on `VerbFormGenerator`):** `__init__` (33),
  `generate` (62), `_process_word` (75), `_process_paradigm` (86),
  `_dispatch_variant_context` (101), `_process_variant` (135),
  `_dispatch_part_context` (167), `_process_part` (201),
  `_derive_part_stem_segments` (240), `_get_prefix` (263),
  `_get_post_vowel` (286), `_get_pre_vowel` (316).
- **Strong-only (moves to `StrongVerbGenerator`):**
  `_emit_strong_vowel_form_context` (572),
  `_emit_strong_vowel_sound_context` (618),
  `_emit_strong_inf_derivation_context` (661),
  `_emit_strong_principal_form_for_vowel_context` (1093),
  `_emit_strong_principal_participle_context` (1127),
  `_emit_strong_principal_inf_derivation_context` (1147),
  `_generate_strong_verb_parts` (1175),
  `_generate_strong_derived_from_inf` (1216),
  `_emit_strong_derived_inf_form_for_vowel_context` (1271),
  `_emit_strong_derived_inf_sound_for_vowel_context` (1305),
  `_emit_strong_derived_inf_participle_context` (1336),
  `_emit_strong_derived_inf_imsg_context` (1356).
- **Weak-only (moves to `WeakVerbGenerator`):**
  `_emit_weak_principal_form_context` (704),
  `_emit_weak_inf_form_context` (753),
  `_emit_weak_painsg1_form_for_vowel_context` (802),
  `_emit_weak_painsg1_form_for_vowel_derivation_context` (851),
  `_emit_weak_painsg1_manual_context` (888),
  `_emit_weak_painsg1_participle_context` (919),
  `_emit_weak_psinsg2_form_with_post_context` (939),
  `_emit_weak_psinsg2_sound_with_post_context` (982),
  `_emit_weak_psinsg2_form_with_post_derivation_context` (1028),
  `_emit_weak_psinsg2_sound_with_post_derivation_context` (1059),
  `_emit_weak_principal_pspt_participle_context` (1456),
  `_emit_weak_principal_papt_participle_context` (1476),
  `_emit_weak_principal_inf_derivation_context` (1496),
  `_emit_weak_principal_psinsg2_derivation_context` (1515),
  `_emit_weak_principal_painsg1_derivation_context` (1534),
  `_generate_weak_verb_parts` (1554),
  `_generate_weak_derived_from_inf` (1605),
  `_emit_weak_derived_inf_form_context` (1657),
  `_emit_weak_derived_inf_participle_context` (1691),
  `_generate_weak_derived_from_painsg1` (1711),
  `_generate_weak_derived_from_psinsg2` (1759).
- **Thin wrappers around already-shared functions — very likely delete,
  don't relocate (confirm via this step's read):** `_generate_and_print_form`
  (337), `_emit_form_for_context` (397), `_emit_sound_changed_form_for_context`
  (450), `_emit_imsg_for_context` (503), `_add_participle_to_adjectives`
  (541), `_generate_and_print_form_with_sound_changes` (1376),
  `_generate_and_print_manual` (1427). Confirmed this session for two of the
  seven: `_generate_and_print_form_with_sound_changes` is a one-line
  forward to `form_rows.generate_and_print_form_with_sound_changes`
  (imported at the top of `common.py` as
  `_generate_and_print_form_with_sound_changes_row`), and
  `_add_participle_to_adjectives` forwards to
  `participles.add_participle_to_adjectives` (imported as
  `_add_participle_to_adjectives_session`). The other five follow the exact
  same `X as _X_row`/`X as _X_session` import-aliasing pattern at the top of
  `common.py` and are very likely thin forwards too — read each one's body
  to confirm. **If a method's entire body is a single call to its
  already-imported module-level counterpart with no other logic, delete the
  method and have `StrongVerbGenerator`/`WeakVerbGenerator` call the
  `form_rows.py`/`participles.py` function directly** (the same way
  `adj_forms.py`/`noun_forms.py`/`adv_forms.py` already call `form_rows.py`
  directly) — keeping a same-named wrapper method here would just be an
  eighth instance of the redirection pattern this whole ADR exists to
  remove. Only if a method's read reveals real logic beyond forwarding
  (unlikely per the confirmed two, but verify) should it be kept as a method
  shared via constructor injection instead of deleted outright.

- [ ] **Step 3: Design `StrongVerbGenerator` and `WeakVerbGenerator`**

Based on Step 2's confirmed read, write `StrongVerbGenerator` and
`WeakVerbGenerator` as two classes in `common.py`, each constructed with the
active `Word`, `VerbParadigm`, `GenerationRunState`, `FormOutput`, and (only
for the subset of the seven "thin wrapper" methods from Step 2 that turn out
to have real logic, not a confirmed pure forward) the owning
`VerbFormGenerator` instance as a small injected collaborator. For every
method Step 2 confirmed is a pure one-line forward to an already-imported
`form_rows.py`/`participles.py` function, do not carry it over at all —
`StrongVerbGenerator`/`WeakVerbGenerator` call that module-level function
directly wherever the old code called the wrapper method. Each new class's
remaining (strong-only/weak-only) methods keep their current names minus the
leading underscore's now-doubled meaning (e.g. `_emit_strong_vowel_form_context`
on `VerbFormGenerator` becomes `_emit_vowel_form_context` on
`StrongVerbGenerator` — drop the redundant `strong`/`weak` prefix since the
class name now carries that distinction). Move each such method's current
body over unchanged except for the prefix-drop rename, the `self.`
reference updates to match the new class's constructor-injected attributes,
and replacing any call to a now-deleted thin-wrapper method with a direct
call to the `form_rows.py`/`participles.py` function it forwarded to.

- [ ] **Step 4: Rewrite `VerbFormGenerator`'s orchestration methods**

Keep `__init__`, `generate`, `_process_word`, `_process_paradigm`,
`_dispatch_variant_context`, `_process_variant`, `_dispatch_part_context`,
`_process_part`, `_derive_part_stem_segments`, `_get_prefix`,
`_get_post_vowel`, `_get_pre_vowel` on `VerbFormGenerator`, updating
`_process_part` (and any other method that currently branches on
`vp.type == "s"` to call strong-path vs. weak-path logic — confirm the exact
branch location via Step 2's read) to construct one `StrongVerbGenerator` or
`WeakVerbGenerator` instance per word/paradigm and call its entrypoint
method instead of calling the (now-deleted) module-level
`_generate_strong_verb_parts_with_emitters`/
`_generate_weak_verb_parts_with_emitters` functions from
`strong_principal_flow.py`/`weak_principal_flow.py`.

- [ ] **Step 5: Delete `common.py`'s `generate_vbforms()` wrapper function and `verb_engine.py`**

`common.py`'s `generate_vbforms()` function (around line 1918, after the
rewritten `VerbFormGenerator` class) currently does:
```python
def generate_vbforms(
    word_pool: WordPool,
    run_state: GenerationRunState,
    output_file: FormOutput,
    *,
    progress: MorphologyGenerateProgressCoordinator | None = None,
) -> None:
    from .verb_engine import VerbFormOrchestrator

    orchestrator = VerbFormOrchestrator(
        word_pool, run_state, output_file, progress=progress
    )
    orchestrator.generate()
```
Delete this function entirely (it's pure redirection into
`verb_engine.VerbFormOrchestrator`, itself pure redirection into
`VerbFormGenerator` — both hops add nothing). Delete
`wyrdcraeft/services/morphology/generation/verb_engine.py`:
```bash
rm wyrdcraeft/services/morphology/generation/verb_engine.py
```

- [ ] **Step 6: Delete the now-empty support modules**

```bash
rm wyrdcraeft/services/morphology/generation/strong_inflections.py
rm wyrdcraeft/services/morphology/generation/strong_principal_flow.py
rm wyrdcraeft/services/morphology/generation/strong_derivation_flow.py
rm wyrdcraeft/services/morphology/generation/weak_inflections.py
rm wyrdcraeft/services/morphology/generation/weak_principal_flow.py
rm wyrdcraeft/services/morphology/generation/weak_derivation_flow.py
rm wyrdcraeft/services/morphology/generation/paradigm_flow.py
```
Do **not** delete `sound_changes.py` or `sound_dispatch_flow.py` — see the
correction note in this task's Files section; `form_rows.py` depends on
`sound_dispatch_flow.py` directly and both files are shared infrastructure,
not verb-only. Before running the `rm` commands above, grep `common.py` for
any remaining `from .strong_inflections import`, `from .weak_principal_flow
import`, etc. — if Step 3/4's rewrite of `common.py` still imports from any
of these 7 modules, that means their logic wasn't fully folded into
`StrongVerbGenerator`/`WeakVerbGenerator`/`VerbFormGenerator` yet; resolve
those imports (move the remaining logic in, per Step 3's pattern) before
deleting the files they'd otherwise still depend on.

- [ ] **Step 7: Update `facade.py`'s `generate_verbs`**

Change:
```python
    def generate_verbs(self) -> None:
        """..."""
        _generate_vbforms(
            self._session.word_pool,
            self._session.run_state,
            self._output_file,
            progress=self._progress,
        )
```
to:
```python
    def generate_verbs(self) -> None:
        """..."""
        VerbFormGenerator(
            self._session.word_pool,
            self._session.run_state,
            self._output_file,
            progress=self._progress,
        ).generate()
```
(keep the existing docstring unchanged) and update the import from
`from .common import generate_vbforms as _generate_vbforms` to
`from .common import VerbFormGenerator`.

- [ ] **Step 8: Update `tests/morphology/test_generation_branches.py`**

This file's scope is broader than just `common.VerbFormGenerator` — verified
this session, it directly imports from **all seven** modules this task
deletes (`strong_inflections`, `strong_principal_flow`,
`strong_derivation_flow`, `weak_inflections`, `weak_principal_flow`,
`weak_derivation_flow`, `paradigm_flow`), plus `common.py` itself (confirmed
edge `<-- test_generation_branches.py [imports]
tests/morphology/test_generation_branches.py:L63`, calling specific methods
directly by name — e.g.
`_generate_weak_verb_parts_uses_item_shape_for_id_window` and
`_generate_weak_painsg1_uses_preterite_vowel_and_sound_changes`, which call
`VerbFormGenerator` methods that move to `WeakVerbGenerator` in this task).
It does **not** import from `sound_dispatch_flow` (not deleted by this task
regardless) and its `sound_changes` import stays valid unchanged (that
module isn't deleted either, per this task's correction above). Read this
test file in full — expect substantially more call sites needing updates
than just the two `common.py`-facing tests named above, since it likely has
direct unit tests against free functions in each of the seven deleted
modules, not only against `VerbFormGenerator` methods. For each: if the
call was against a function that moved into `StrongVerbGenerator`/
`WeakVerbGenerator` as a method (per Step 2/3's split), construct the
correct new class and call the renamed (prefix-dropped) method; if it was
against a function this task deleted outright as a confirmed thin wrapper
(per Step 2's "thin wrappers" bucket), update the test to call the
`form_rows.py`/`participles.py` function directly instead, or delete the
test if it was only testing the wrapper's forwarding behavior and an
equivalent test already exists for the underlying shared function.

- [ ] **Step 9: Run the golden-path parity gate**

Run: `.venv/bin/pytest tests/morphology/test_parity_harness.py -v`

Expected: PASS, zero diff. This is the highest-risk gate in the whole plan —
if it fails, do not attempt to fix forward blindly. Instead, temporarily
`git stash` this task's changes, confirm the gate passes on the pre-task
state (isolating that the regression is genuinely from this task), then
reapply the stash and bisect by reverting one of `StrongVerbGenerator`/
`WeakVerbGenerator`'s methods at a time back to calling the original
(pre-deletion, restored from git history) module-level function, to isolate
which specific method's migration introduced the mismatch.

- [ ] **Step 10: Run the full test suite**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`

Expected: identical pass count to Step 1.

- [ ] **Step 11: Quality gate**

```bash
ruff check wyrdcraeft/services/morphology/generation/common.py wyrdcraeft/services/morphology/generation/facade.py tests/morphology/test_generation_branches.py
.venv/bin/mypy wyrdcraeft/services/morphology/generation/common.py wyrdcraeft/services/morphology/generation/facade.py
make napoleon-gate
```

- [ ] **Step 12: Commit**

```bash
git add wyrdcraeft/services/morphology/generation/common.py wyrdcraeft/services/morphology/generation/facade.py tests/morphology/test_generation_branches.py
git rm wyrdcraeft/services/morphology/generation/verb_engine.py wyrdcraeft/services/morphology/generation/strong_inflections.py wyrdcraeft/services/morphology/generation/strong_principal_flow.py wyrdcraeft/services/morphology/generation/strong_derivation_flow.py wyrdcraeft/services/morphology/generation/weak_inflections.py wyrdcraeft/services/morphology/generation/weak_principal_flow.py wyrdcraeft/services/morphology/generation/weak_derivation_flow.py wyrdcraeft/services/morphology/generation/paradigm_flow.py
git commit -m "refactor: split common.VerbFormGenerator into VerbFormGenerator/StrongVerbGenerator/WeakVerbGenerator, delete redirection wrapper chain"
```

---

### Task 7: Delete the now-empty `generators/` directory

**Files:**
- Delete: `wyrdcraeft/services/morphology/generators/` (whole directory — `num_forms.py` and `__init__.py`)

**Interfaces:**
- Consumes: nothing (confirmed zero callers of `generators/num_forms.py`
  anywhere in the repo — production, tests, or scripts).
- Produces: nothing — pure deletion.

- [ ] **Step 1: Confirm zero callers (re-verify before deleting)**

```bash
grep -rn "generation\.generators\.num_forms\|generators\.num_forms\|from \.\.generators import\|from \.generators\.num_forms" wyrdcraeft/ tests/ scripts/
```
Expected: no output. If this now finds a hit (e.g. a caller added since ADR
0009 was written), stop and update that caller to import
`wyrdcraeft.services.morphology.generation.num_forms.NumeralFormGenerator`
(from Task 3) directly before proceeding.

- [ ] **Step 2: Delete the directory**

```bash
rm -rf wyrdcraeft/services/morphology/generators/
```

- [ ] **Step 3: Run the golden-path parity gate**

Run: `.venv/bin/pytest tests/morphology/test_parity_harness.py -v`

Expected: PASS, zero diff (this task touches no code any generation path
runs through).

- [ ] **Step 4: Run the full test suite**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`

Expected: identical pass count to before this task (no test imports this
directory per Step 1's confirmation).

- [ ] **Step 5: Update the knowledge graph**

```bash
graphify update .
```

- [ ] **Step 6: Commit**

```bash
git add -A wyrdcraeft/services/morphology/generators/
git commit -m "chore: delete dead generators/ compatibility shim directory"
```
