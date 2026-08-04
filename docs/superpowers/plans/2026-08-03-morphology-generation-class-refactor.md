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
`_gen_*` functions selected by an `elif re.search(...)` chain.

Verb generation is different in kind, not degree: an attempted execution of
the original single-task plan (Tasks 6-9 below were then one task) found via
AST analysis that `common.VerbFormGenerator`'s ~1,800 lines are 49
single-call forwards holding almost no logic — the real logic (~5,000 lines
across 87 functions) lives in the 7 modules the original task assumed were
"now-empty." ADR 0009 has been corrected to match this finding (see its
Context "second correction" and Decision item 4). Tasks 6-9 replace the
original single verb-collapse task with 4 staged sub-tasks, each
independently gated by the parity harness: Task 6 folds `paradigm_flow.py`'s
traversal logic into `VerbFormGenerator`; Task 7 migrates the strong-side
modules into a new `StrongVerbGenerator`; Task 8 migrates the weak-side
modules (the largest sub-task) into a new `WeakVerbGenerator`; Task 9
deletes the remaining wrapper chain (`verb_engine.py`, `generate_vbforms()`),
resolves the confirmed thin-wrapper methods, and wires `facade.py`.
Genuinely shared row/sound-change emission stays exactly where it already
lives — `form_rows.py`, `sound_changes.py`, `sound_dispatch_flow.py`
(`form_rows.py` depends directly on `sound_dispatch_flow.py`, and several of
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
nouns → adjectives) → Task 6 (fold `paradigm_flow.py` into
`VerbFormGenerator`'s traversal) → Tasks 7-8 (strong- and weak-side verb
logic migration, each depends on Task 6, independent of each other) → Task 9
(delete the remaining wrapper chain, resolve thin wrappers, wire the facade
— depends on Tasks 6-8) → Task 10 (delete the now-empty `generators/`
directory).

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
- After Task 10: run `graphify update .` to keep the knowledge graph current.

---

## File Structure

- **Task 1:** `wyrdcraeft/services/morphology/generation/dispatch.py` (deleted), `wyrdcraeft/services/morphology/reference_snapshots.py`, `wyrdcraeft/services/morphology/build_runner.py`, `tests/morphology/parity_harness.py`, `tests/morphology/test_form_generation_reference.py`, `tests/morphology/test_generation_package_imports.py`, `tests/morphology/test_query_service.py`, `tests/morphology/test_full_flow_reference.py`, `scripts/morphology/generate_refactor_baseline.py`, `scripts/morphology/profile_adj_stage.py`
- **Task 2:** `wyrdcraeft/services/morphology/generation/adv_forms.py`, `wyrdcraeft/services/morphology/generation/facade.py` (`generate_adverbs` only)
- **Task 3:** `wyrdcraeft/services/morphology/generation/num_forms.py`, `facade.py` (`generate_numerals` only)
- **Task 4:** `wyrdcraeft/services/morphology/generation/noun_forms.py`, `facade.py` (`generate_nouns` only)
- **Task 5:** `wyrdcraeft/services/morphology/generation/adj_forms.py`, `facade.py` (`generate_adjectives` only)
- **Task 6:** `wyrdcraeft/services/morphology/generation/common.py` (modified — 9 orchestration methods gain real bodies), `wyrdcraeft/services/morphology/generation/paradigm_flow.py` (deleted), `tests/morphology/test_generation_branches.py`
- **Task 7:** `common.py` (modified — adds `StrongVerbGenerator`), `wyrdcraeft/services/morphology/generation/strong_inflections.py`, `strong_principal_flow.py`, `strong_derivation_flow.py` (deleted), `tests/morphology/test_generation_branches.py`
- **Task 8:** `common.py` (modified — adds `WeakVerbGenerator`), `wyrdcraeft/services/morphology/generation/weak_inflections.py`, `weak_principal_flow.py`, `weak_derivation_flow.py` (deleted), `tests/morphology/test_generation_branches.py`
- **Task 9:** `common.py` (modified — deletes `generate_vbforms()`, resolves confirmed thin-wrapper methods), `wyrdcraeft/services/morphology/generation/verb_engine.py` (deleted), `facade.py` (`generate_verbs` only), `tests/morphology/test_generation_branches.py` (`sound_changes.py`/`sound_dispatch_flow.py` are NOT deleted by any of Tasks 6-9 — shared infrastructure, see Task 9's correction note; `models/morphology.py`'s `_*Context` dataclasses only if Task 9 Step 2 confirms all six are dead)
- **Task 10:** `wyrdcraeft/services/morphology/generators/` (whole directory deleted)

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

### Task 6: Migrate `paradigm_flow.py`'s traversal logic into `VerbFormGenerator`

**Re-planned task — see ADR 0009's "second correction" in Context and
Decision item 4.** Task 6's original single-task shape assumed
`common.VerbFormGenerator` already held the strong/weak logic and just
needed splitting along its naming seam. An AST pass over all 52 methods
(confirmed during an attempted execution of the original task, no code was
written) found 49 are pure single-statement forwards — the class holds
almost no logic. The real logic (~5,000 lines / 87 functions) lives in the
7 modules the original task called "now-empty." This re-plan splits the
verb-generation collapse into 4 staged sub-tasks (this one plus Tasks 7-9),
each independently gated by the parity harness, so a regression can be
localized to the sub-task that introduced it rather than searched for
across an 87-function diff.

This task handles the smallest, most foundational slice:
`paradigm_flow.py`'s 13 functions (567 lines) — the per-word/per-paradigm
traversal logic that `VerbFormGenerator`'s 9 "orchestration" methods
(`_process_paradigm`, `_dispatch_variant_context`, `_process_variant`,
`_dispatch_part_context`, `_process_part`, `_derive_part_stem_segments`,
`_get_prefix`, `_get_post_vowel`, `_get_pre_vowel`) currently forward to,
plus 2 functions with no corresponding method at all
(`build_verb_formhash_base`, `derive_paradigm_seed_vowels`, called from
inside `paradigm_flow.py`'s own traversal function). Tasks 7-8 (strong/weak
logic) depend on this task landing first, since they call into
`VerbFormGenerator`'s traversal to reach per-word/per-paradigm context.

**Files:**
- Modify: `wyrdcraeft/services/morphology/generation/common.py` (the 9
  orchestration methods gain real bodies instead of forwarding)
- Delete: `wyrdcraeft/services/morphology/generation/paradigm_flow.py`

**Interfaces:**
- Consumes: `WordPool`, `GenerationRunState`, `FormOutput`,
  `MorphologyGenerateProgressCoordinator`, `Word`, `VerbParadigm`,
  `ParadigmVariant`, `ParadigmPart` (all already exist, unchanged).
- Produces: `VerbFormGenerator`'s public shape is unchanged by this task —
  `generate()` still exists with the same signature; Tasks 7-8 depend on its
  traversal methods (`_process_paradigm`/`_process_variant`/`_process_part`
  et al.) now containing real logic they can call into for per-word/
  per-paradigm state, instead of the previous callback-injection shape.

- [ ] **Step 1: Record baseline**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`, note pass count
(run it yourself — do not assume the number from a prior task's report).

- [ ] **Step 2: Read `paradigm_flow.py` and the 9 forwarding methods it targets, in full**

Read `wyrdcraeft/services/morphology/generation/paradigm_flow.py` (all 13
functions, 567 lines) and `common.py`'s `VerbFormGenerator.__init__`,
`generate`, `_process_word`, `_process_paradigm`,
`_dispatch_variant_context`, `_process_variant`, `_dispatch_part_context`,
`_process_part`, `_derive_part_stem_segments`, `_get_prefix`,
`_get_post_vowel`, `_get_pre_vowel` (lines 124-1918 of `common.py` — grep for
these method names to locate exact line numbers, since Task 6's original
line-offset table was built against the pre-Task-1-through-5 file and may
have shifted). For each of the 9 forwarding methods, confirm which
`paradigm_flow.py` function it currently forwards to and read that
function's full body — this is the logic that moves into the method.

- [ ] **Step 3: Fold each `paradigm_flow.py` function's body into its corresponding `VerbFormGenerator` method**

For each of the 9 methods, replace its current one-line forward with the
body of the `paradigm_flow.py` function it called, adapting `Callable`-typed
parameters that were previously injected (e.g. an `emit_form_for_context:
EmitFormForContext` parameter) into direct calls to the corresponding
`VerbFormGenerator` method on `self` (e.g. `self._emit_form_for_context(...)`
if that method still exists after Task 9's cleanup, or a direct call to the
`form_rows.py`/`participles.py` function it forwards to if Task 9 confirms
it's a pure thin wrapper — coordinate with the "thin wrapper" bucket
findings Task 9 will also need; if you reach a forwarding call this task
doesn't yet know the fate of, keep calling the current method by name and
let Task 9 resolve it, rather than guessing). Fold `build_verb_formhash_base`
and `derive_paradigm_seed_vowels` in as new private methods on
`VerbFormGenerator` (they have no existing forwarding-method counterpart to
replace) since they're called from within the traversal logic these 9
methods implement. Preserve every regex, conditional, and string literal
unchanged — this is a logic *relocation*, not a rewrite; only the calling
convention (`Callable` parameter → direct method call) changes.

- [ ] **Step 4: Delete `paradigm_flow.py`**

Grep `common.py` for any remaining `from .paradigm_flow import` first — if
Step 3's fold isn't complete, this will show a leftover import. Resolve it
before deleting:
```bash
grep -n "from .paradigm_flow import\|from \.paradigm_flow" wyrdcraeft/services/morphology/generation/common.py
rm wyrdcraeft/services/morphology/generation/paradigm_flow.py
```

- [ ] **Step 5: Update any test that imports `paradigm_flow` directly**

`tests/morphology/test_generation_branches.py` imports 2 named symbols from
`paradigm_flow` (confirmed during Task 6's original attempt). Read the
relevant test(s), and update each to call the new `VerbFormGenerator` method
directly instead of the deleted free function.

- [ ] **Step 6: Run the golden-path parity gate**

Run: `.venv/bin/pytest tests/morphology/test_parity_harness.py -v`

Expected: PASS, zero diff. If it fails, `git stash` this task's changes,
confirm the gate passes on the pre-task state (isolating that the
regression is genuinely from this task), then reapply the stash and bisect
by reverting one of the 9 folded methods at a time back to its pre-fold
forwarding call (restored from git history) to isolate which method's fold
introduced the mismatch.

- [ ] **Step 7: Run the full test suite**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`

Expected: identical pass count to Step 1.

- [ ] **Step 8: Quality gate**

```bash
ruff check wyrdcraeft/services/morphology/generation/common.py tests/morphology/test_generation_branches.py
.venv/bin/mypy wyrdcraeft/services/morphology/generation/common.py
make napoleon-gate
```
Carry over any `# noqa:` suppression the folded `paradigm_flow.py` functions
had, re-evaluating it against the new method's actual arg count/statement
count rather than copying it blindly (per the lesson from this plan's
Task 3, which dropped a suppression and introduced 25 unnoticed violations).

- [ ] **Step 9: Commit**

```bash
git add wyrdcraeft/services/morphology/generation/common.py tests/morphology/test_generation_branches.py
git rm wyrdcraeft/services/morphology/generation/paradigm_flow.py
git commit -m "refactor: fold paradigm_flow.py traversal logic into VerbFormGenerator"
```

---

### Task 7: Migrate strong verb generation into `StrongVerbGenerator`

Depends on Task 6 (needs `VerbFormGenerator`'s traversal methods holding
real logic to call into). Migrates the strong-side logic: `strong_inflections.py`
(8 fns/439 lines), `strong_principal_flow.py` (6/390),
`strong_derivation_flow.py` (12/670) — 26 functions, ~1,500 lines total —
plus `VerbFormGenerator`'s 12 confirmed strong-only forwarding methods
(`_emit_strong_vowel_form_context`, `_emit_strong_vowel_sound_context`,
`_emit_strong_inf_derivation_context`,
`_emit_strong_principal_form_for_vowel_context`,
`_emit_strong_principal_participle_context`,
`_emit_strong_principal_inf_derivation_context`,
`_generate_strong_verb_parts`, `_generate_strong_derived_from_inf`,
`_emit_strong_derived_inf_form_for_vowel_context`,
`_emit_strong_derived_inf_sound_for_vowel_context`,
`_emit_strong_derived_inf_participle_context`,
`_emit_strong_derived_inf_imsg_context` — line offsets from Task 6's
original attempt are stale after Tasks 6's edits; re-locate by name).

**Files:**
- Modify: `wyrdcraeft/services/morphology/generation/common.py` (add
  `StrongVerbGenerator` class; `VerbFormGenerator` gains a dispatch point
  that constructs one per strong-paradigm word and calls its entry method)
- Delete: `wyrdcraeft/services/morphology/generation/strong_inflections.py`, `strong_principal_flow.py`, `strong_derivation_flow.py`

**Interfaces:**
- Consumes: `VerbFormGenerator`'s traversal methods from Task 6 (per-word/
  per-paradigm state reachable from `self` inside the traversal).
- Produces: `StrongVerbGenerator(word, paradigm, run_state, output_file)` (or
  the equivalent constructor shape Step 2 confirms fits how `VerbFormGenerator`
  reaches per-word/per-paradigm state) with an entry method
  `VerbFormGenerator` calls once per strong-paradigm word/variant/part,
  consumed by Task 9's final wiring step.

- [ ] **Step 1: Record baseline**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`, note pass count
(run it yourself).

- [ ] **Step 2: Read all 26 strong-side functions and the 12 forwarding methods, in full**

Read `strong_inflections.py`, `strong_principal_flow.py`,
`strong_derivation_flow.py` completely, and grep `common.py` for the 12
strong-only method names listed above to read their current (post-Task-6)
bodies. Confirm: which of the 12 methods forward into which of the 26
functions; whether `_StrongPrincipalPartContext`/`_StrongInfDerivationContext`
(from `models/morphology.py`, out of this task's file list) are read/written
identically at every call site or carry hidden per-call-site variation; and
whether any of the 26 functions is itself a pure forward to
`form_rows.py`/`participles.py` (if so, it belongs in Task 9's "thin
wrapper" cleanup, not here — flag it in your report rather than migrating
it as strong-specific logic).

- [ ] **Step 3: Design and write `StrongVerbGenerator`**

Based on Step 2's read, write `StrongVerbGenerator` as a class in
`common.py`. Give it whichever constructor shape the confirmed call pattern
needs (likely the active `Word`, `VerbParadigm`, `GenerationRunState`,
`FormOutput`, since `_StrongPrincipalPartContext`/`_StrongInfDerivationContext`
carry exactly this shape today) — do not assume; confirm from Step 2's read.
Each of the 12 forwarding methods' logic moves onto `StrongVerbGenerator` as
a same-named method minus the redundant `strong` prefix (e.g.
`_emit_strong_vowel_form_context` → `_emit_vowel_form_context`), with its
body being the corresponding `strong_*.py` function's logic, adapted from
free-function-with-injected-callables to a bound method reading `self`'s
constructor-injected state. Preserve every regex, conditional, and string
literal unchanged.

- [ ] **Step 4: Wire `VerbFormGenerator` to construct and call `StrongVerbGenerator`**

Update `VerbFormGenerator`'s dispatch point (confirm the exact location via
Step 2 — likely `_process_part` or wherever it branches on `vp.type == "s"`)
to construct one `StrongVerbGenerator` per strong-paradigm word/variant/part
and call its entry method, replacing the current call into the (still
present until Task 9) forwarding methods.

- [ ] **Step 5: Delete the 3 now-folded strong modules**

Grep `common.py` for any remaining `from .strong_inflections import`,
`from .strong_principal_flow import`, `from .strong_derivation_flow import`
first:
```bash
grep -n "from \.strong_inflections\|from \.strong_principal_flow\|from \.strong_derivation_flow" wyrdcraeft/services/morphology/generation/common.py
rm wyrdcraeft/services/morphology/generation/strong_inflections.py
rm wyrdcraeft/services/morphology/generation/strong_principal_flow.py
rm wyrdcraeft/services/morphology/generation/strong_derivation_flow.py
```

- [ ] **Step 6: Update tests that import these 3 modules directly**

`tests/morphology/test_generation_branches.py` imports directly from
`strong_principal_flow` (1 symbol) and `strong_inflections` (7 symbols),
plus 2 `TYPE_CHECKING`-only imports from `strong_derivation_flow`/
`strong_principal_flow` (confirmed during Task 6's original attempt). Read
each affected test and update it to call the new `StrongVerbGenerator`
method directly.

- [ ] **Step 7: Run the golden-path parity gate**

Run: `.venv/bin/pytest tests/morphology/test_parity_harness.py -v`

Expected: PASS, zero diff. If it fails, `git stash`, confirm the gate passes
pre-task, then bisect by reverting one migrated method at a time.

- [ ] **Step 8: Run the full test suite**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`

Expected: identical pass count to Step 1.

- [ ] **Step 9: Quality gate**

```bash
ruff check wyrdcraeft/services/morphology/generation/common.py tests/morphology/test_generation_branches.py
.venv/bin/mypy wyrdcraeft/services/morphology/generation/common.py
make napoleon-gate
```

- [ ] **Step 10: Commit**

```bash
git add wyrdcraeft/services/morphology/generation/common.py tests/morphology/test_generation_branches.py
git rm wyrdcraeft/services/morphology/generation/strong_inflections.py wyrdcraeft/services/morphology/generation/strong_principal_flow.py wyrdcraeft/services/morphology/generation/strong_derivation_flow.py
git commit -m "refactor: migrate strong verb generation into StrongVerbGenerator"
```

---

### Task 8: Migrate weak verb generation into `WeakVerbGenerator`

Depends on Task 6 (same reason as Task 7); independent of Task 7 (strong
and weak paths don't share logic, only the traversal Task 6 provides).
Migrates the weak-side logic: `weak_inflections.py` (17 fns/949 lines),
`weak_principal_flow.py` (16/828), `weak_derivation_flow.py` (15/1,119) —
48 functions, ~2,900 lines total, the largest single sub-task in this
verb-collapse re-plan — plus `VerbFormGenerator`'s 21 confirmed weak-only
forwarding methods (`_emit_weak_principal_form_context`,
`_emit_weak_inf_form_context`, `_emit_weak_painsg1_form_for_vowel_context`,
`_emit_weak_painsg1_form_for_vowel_derivation_context`,
`_emit_weak_painsg1_manual_context`, `_emit_weak_painsg1_participle_context`,
`_emit_weak_psinsg2_form_with_post_context`,
`_emit_weak_psinsg2_sound_with_post_context`,
`_emit_weak_psinsg2_form_with_post_derivation_context`,
`_emit_weak_psinsg2_sound_with_post_derivation_context`,
`_emit_weak_principal_pspt_participle_context`,
`_emit_weak_principal_papt_participle_context`,
`_emit_weak_principal_inf_derivation_context`,
`_emit_weak_principal_psinsg2_derivation_context`,
`_emit_weak_principal_painsg1_derivation_context`,
`_generate_weak_verb_parts`, `_generate_weak_derived_from_inf`,
`_emit_weak_derived_inf_form_context`,
`_emit_weak_derived_inf_participle_context`,
`_generate_weak_derived_from_painsg1`, `_generate_weak_derived_from_psinsg2`
— line offsets are stale after Task 6/7's edits; re-locate by name).

**Files:**
- Modify: `wyrdcraeft/services/morphology/generation/common.py` (add
  `WeakVerbGenerator` class; `VerbFormGenerator` gains a dispatch point that
  constructs one per weak-paradigm word and calls its entry method)
- Delete: `wyrdcraeft/services/morphology/generation/weak_inflections.py`, `weak_principal_flow.py`, `weak_derivation_flow.py`

**Interfaces:**
- Consumes: `VerbFormGenerator`'s traversal methods from Task 6.
- Produces: `WeakVerbGenerator(word, paradigm, run_state, output_file)` (or
  the equivalent constructor shape Step 2 confirms) with an entry method
  `VerbFormGenerator` calls once per weak-paradigm word/variant/part,
  consumed by Task 9's final wiring step.

- [ ] **Step 1: Record baseline**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`, note pass count
(run it yourself).

- [ ] **Step 2: Read all 48 weak-side functions and the 21 forwarding methods, in full**

Same approach as Task 7 Step 2, scoped to the weak-side files/methods. This
is the largest single read in the plan (2,900 lines across 48 functions) —
budget time accordingly and do not skim. Confirm the same three things Task
7 Step 2 confirmed (which method forwards to which function; whether the
`_Weak*Context` dataclasses vary per call site; whether any of the 48
functions is itself a pure forward that belongs in Task 9's cleanup instead
of here).

- [ ] **Step 3: Design and write `WeakVerbGenerator`**

Same approach as Task 7 Step 3, scoped to the weak side. Each of the 21
forwarding methods' logic moves onto `WeakVerbGenerator` as a same-named
method minus the redundant `weak` prefix, body preserved unchanged apart
from the free-function-to-bound-method adaptation.

- [ ] **Step 4: Wire `VerbFormGenerator` to construct and call `WeakVerbGenerator`**

Same approach as Task 7 Step 4, for the weak-paradigm branch of the
dispatch point Task 7 already touched (confirm both branches of the same
`if`/`else` are updated together, not just the strong one).

- [ ] **Step 5: Delete the 3 now-folded weak modules**

```bash
grep -n "from \.weak_inflections\|from \.weak_principal_flow\|from \.weak_derivation_flow" wyrdcraeft/services/morphology/generation/common.py
rm wyrdcraeft/services/morphology/generation/weak_inflections.py
rm wyrdcraeft/services/morphology/generation/weak_principal_flow.py
rm wyrdcraeft/services/morphology/generation/weak_derivation_flow.py
```

- [ ] **Step 6: Update tests that import these 3 modules directly**

`tests/morphology/test_generation_branches.py` imports directly from
`weak_inflections` (11 symbols) and `weak_derivation_flow` (7 symbols), plus
1 symbol from `weak_principal_flow` (confirmed during Task 6's original
attempt) — the largest test-update surface of any sub-task here. Read each
affected test and update it to call the new `WeakVerbGenerator` method
directly. Three of the imports across this file are `Callable` type-alias
names themselves (e.g. `WeakFormContextEmitter`,
`WeakPsinsg2SoundWithPostEmitter`) whose tests exist to verify the
callback-injection protocol this whole verb-collapse dissolves — these
tests need rethinking, not a mechanical call-site swap; read what each one
actually asserts before deciding whether it still has a purpose against the
new method-dispatch shape or should be deleted as testing a protocol that
no longer exists.

- [ ] **Step 7: Run the golden-path parity gate**

Run: `.venv/bin/pytest tests/morphology/test_parity_harness.py -v`

Expected: PASS, zero diff. If it fails, `git stash`, confirm the gate passes
pre-task, then bisect by reverting one migrated method at a time. Given this
is the largest sub-task, prefer bisecting by principal-part group
(painsg1/psinsg2/pspt/papt) before individual methods, to narrow the search
faster.

- [ ] **Step 8: Run the full test suite**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`

Expected: identical pass count to Step 1.

- [ ] **Step 9: Quality gate**

```bash
ruff check wyrdcraeft/services/morphology/generation/common.py tests/morphology/test_generation_branches.py
.venv/bin/mypy wyrdcraeft/services/morphology/generation/common.py
make napoleon-gate
```

- [ ] **Step 10: Commit**

```bash
git add wyrdcraeft/services/morphology/generation/common.py tests/morphology/test_generation_branches.py
git rm wyrdcraeft/services/morphology/generation/weak_inflections.py wyrdcraeft/services/morphology/generation/weak_principal_flow.py wyrdcraeft/services/morphology/generation/weak_derivation_flow.py
git commit -m "refactor: migrate weak verb generation into WeakVerbGenerator"
```

---

### Task 9: Delete the wrapper chain (`verb_engine.py`, `generate_vbforms()`), clean up thin wrappers, wire the facade

Depends on Tasks 6-8 landing first (this task assumes `StrongVerbGenerator`/
`WeakVerbGenerator` already exist and `VerbFormGenerator`'s traversal is
real). Finishes the collapse: deletes the two remaining pure-redirection
hops (`verb_engine.VerbFormOrchestrator` and `common.py`'s
`generate_vbforms()` wrapper), resolves the 7 "thin wrapper" bucket methods
flagged-but-deferred in Tasks 6-8 (`_generate_and_print_form`,
`_emit_form_for_context`, `_emit_sound_changed_form_for_context`,
`_emit_imsg_for_context`, `_add_participle_to_adjectives`,
`_generate_and_print_form_with_sound_changes`,
`_generate_and_print_manual` — 2 of 7 confirmed pure one-line forwards to
`form_rows.py`/`participles.py` during Task 6's original attempt; the other
5 need confirming here if Tasks 6-8 didn't already resolve them), and wires
`facade.py`.

**Correction carried from ADR 0009 — `sound_changes.py`/`sound_dispatch_flow.py`
are NOT deleted, and there is no `SoundChangeApplier` class.** `form_rows.py`
(out-of-scope shared infrastructure) imports and calls
`sound_dispatch_flow.generate_and_print_form_with_sound_changes` and
`sound_dispatch_flow.emit_sound_changed_form_for_context` directly — both
files are shared infrastructure like `form_rows.py`/`form_assembly.py`, used
by every PoS generator, not verb-specific. This task leaves both untouched.

**Files:**
- Modify: `wyrdcraeft/services/morphology/generation/common.py` (delete
  `generate_vbforms()`; resolve remaining thin-wrapper methods)
- Delete: `wyrdcraeft/services/morphology/generation/verb_engine.py`
- Modify: `wyrdcraeft/services/morphology/generation/facade.py` (`generate_verbs` only)
- Modify: `tests/morphology/test_generation_branches.py` (remaining call sites, if any)
- Modify: `models/morphology.py` — **only if** Step 2 confirms the six
  `_*Context` dataclasses (`_StrongPrincipalPartContext`,
  `_StrongInfDerivationContext`, `_WeakPrincipalPartContext`,
  `_WeakInfDerivationContext`, `_WeakPainsg1DerivationContext`,
  `_WeakPsinsg2DerivationContext`) are now genuinely unused after Tasks 7-8;
  if any is still constructed/read anywhere, leave `models/morphology.py`
  untouched and note the ones still in use in your report

**Interfaces:**
- Consumes: `StrongVerbGenerator`/`WeakVerbGenerator` from Tasks 7-8,
  `VerbFormGenerator`'s traversal from Task 6.
- Produces: `VerbFormGenerator(word_pool, run_state, output_file, *,
  progress=None).generate() -> None` (same public shape `facade.py` already
  calls — unchanged by this task).

- [ ] **Step 1: Record baseline**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`, note pass count
(run it yourself).

- [ ] **Step 2: Confirm the 7 thin-wrapper methods and the `_*Context` dataclasses' fate**

Read the current bodies of `_generate_and_print_form`,
`_emit_form_for_context`, `_emit_sound_changed_form_for_context`,
`_emit_imsg_for_context`, `_add_participle_to_adjectives`,
`_generate_and_print_form_with_sound_changes`, `_generate_and_print_manual`
on `VerbFormGenerator` (2 of 7 already confirmed as pure one-line forwards
to `form_rows.py`/`participles.py` — confirm the other 5 the same way,
reading the body rather than assuming from the name). For each confirmed
pure forward, plan to delete the method and have callers (in
`StrongVerbGenerator`/`WeakVerbGenerator`, from Tasks 7-8) call the
`form_rows.py`/`participles.py` function directly instead — keeping a
same-named wrapper method here is exactly the redirection this whole ADR
exists to remove. If any of the 7 has real logic beyond forwarding (none
confirmed so far, but verify), keep it as a method and note which class(es)
need it injected. Separately, grep the repo for constructions of the six
`_*Context` dataclasses in `models/morphology.py` — if Tasks 7-8's migration
made all of them dead, note this in your report as a candidate for a
follow-up cleanup task (do not remove them in this task unless doing so is
a trivial, zero-risk deletion you're confident about; `models/morphology.py`
is not otherwise in this plan's scope).

- [ ] **Step 3: Delete the confirmed-thin-wrapper methods, repoint their callers**

For each of the 7 methods Step 2 confirmed as a pure forward, delete it from
`VerbFormGenerator` and update every caller (now in `StrongVerbGenerator`/
`WeakVerbGenerator` after Tasks 7-8, or still on `VerbFormGenerator` itself)
to call the underlying `form_rows.py`/`participles.py` function directly,
using the same already-imported aliases (`X as _X_row`/`X as _X_session`)
`common.py` already has at the top of the file.

- [ ] **Step 4: Delete `common.py`'s `generate_vbforms()` wrapper function and `verb_engine.py`**

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
Delete this function entirely (pure redirection into
`verb_engine.VerbFormOrchestrator`, itself pure redirection into
`VerbFormGenerator` — both hops add nothing):
```bash
rm wyrdcraeft/services/morphology/generation/verb_engine.py
```

- [ ] **Step 5: Update `facade.py`'s `generate_verbs`**

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

- [ ] **Step 6: Update any remaining `test_generation_branches.py` call sites**

Tasks 6-8 should have handled most of this file's updates already; read it
once more here to confirm no call site still references a method Step 3
just deleted, and fix any that remain.

- [ ] **Step 7: Run the golden-path parity gate**

Run: `.venv/bin/pytest tests/morphology/test_parity_harness.py -v`

Expected: PASS, zero diff. This is the final gate for the whole verb
collapse — if it fails, bisect by temporarily restoring one of the 7
deleted thin-wrapper methods (from git history) and routing its callers
back through it, to confirm whether Step 3's repointing (not Tasks 6-8's
earlier migrations, already independently gated) introduced the mismatch.

- [ ] **Step 8: Run the full test suite**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`

Expected: identical pass count to Step 1.

- [ ] **Step 9: Quality gate**

```bash
ruff check wyrdcraeft/services/morphology/generation/common.py wyrdcraeft/services/morphology/generation/facade.py tests/morphology/test_generation_branches.py
.venv/bin/mypy wyrdcraeft/services/morphology/generation/common.py wyrdcraeft/services/morphology/generation/facade.py
make napoleon-gate
```

- [ ] **Step 10: Commit**

```bash
git add wyrdcraeft/services/morphology/generation/common.py wyrdcraeft/services/morphology/generation/facade.py tests/morphology/test_generation_branches.py
git rm wyrdcraeft/services/morphology/generation/verb_engine.py
git commit -m "refactor: delete verb-generation wrapper chain (verb_engine.py, generate_vbforms), resolve thin-wrapper methods, wire facade"
```

---

### Task 10: Delete the now-empty `generators/` directory

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

---

## Addendum: Tasks 11-14 (added after final whole-branch review)

The final whole-branch review of Tasks 1-10 found no Critical issues and zero
dangling references, but flagged two ADR-vs-reality gaps: (1) the verb
collapse (Tasks 6-9) eliminated the 5-hop redirection chain and 7-file spread
but left the `functools.partial`/`Callable`-injection callback threading
intact *inside* `StrongVerbGenerator`/`WeakVerbGenerator` (relocated into
class scope, not collapsed into direct `self.` method calls, per ADR 0009
Decision item 4's original goal); (2) the paradigm-dispatch table ADR 0009
Decision item 3 describes was never built — `noun_forms.py`/`adj_forms.py`
still dispatch via `elif re.search(...)` chains. The human decided to close
both gaps rather than merge with the ADR overclaiming the outcome. Tasks
11-14 close them, in dependency order: Task 11 (paradigm-dispatch tables,
independent of verb work) → Task 12 (strong-side callback collapse) → Task
13 (weak-side callback collapse, independent of Task 12) → Task 14 (final
cleanup: remove now-dead `_*Context` dataclasses/`Callable` aliases/
`Protocol` classes, verify ADR 0009 now accurately describes the delivered
state).

Same golden-path gate and Global Constraints as Tasks 1-10 apply to all four.

---

### Task 11: Build paradigm-dispatch tables for `NounFormGenerator` and `AdjectiveFormGenerator`

`AdverbFormGenerator`/`NumeralFormGenerator` have no paradigm dispatch (single
function body each) — nothing to do there. `NounFormGenerator._generate_word`
and `AdjectiveFormGenerator._generate_word` currently select among
`_gen_<paradigm>`/`_gen_strong_*` methods via `elif re.search(pattern,
paradigm)` chains. Replace each with a paradigm-pattern → bound-method
dispatch table, per ADR 0009 Decision item 3, **without changing which
paradigm maps to which method or the regex patterns themselves** — this is a
dispatch-mechanism change, not a paradigm-matching change, and must not
affect output.

**Files:**
- Modify: `wyrdcraeft/services/morphology/generation/noun_forms.py`
- Modify: `wyrdcraeft/services/morphology/generation/adj_forms.py`

**Interfaces:**
- Consumes: nothing new — same constructor/`generate()` shape both classes
  already have.
- Produces: no change to either class's public shape; `_generate_word`'s
  internal dispatch mechanism changes from `elif` chain to table lookup.

- [ ] **Step 1: Record baseline**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`, note pass count
(run it yourself).

- [ ] **Step 2: Read both classes' current dispatch chains in full**

Read `NounFormGenerator._generate_word`'s `elif re.search(...)` chain (15
branches per the final review) and `AdjectiveFormGenerator._generate_word`'s
strong-paradigm chain (6 branches) in full. For each branch, note the exact
regex pattern and the method it dispatches to, in order — order matters if
any patterns could overlap (confirm via the read whether any do; if patterns
are mutually exclusive, table order doesn't matter, but if the current
`elif` chain relies on trying patterns in a specific order to break ties,
preserve that ordering in the table, e.g. via an ordered list of
`(pattern, method)` pairs tried in sequence rather than an unordered dict).

- [ ] **Step 3: Build the dispatch table for each class**

Add a class attribute (e.g. `_PARADIGM_DISPATCH: ClassVar[list[tuple[str,
str]]]` mapping regex pattern to method name, resolved via `getattr(self,
method_name)` at dispatch time — or a `dict[str, Callable[..., None]]` built
in `__init__` binding `self`'s methods directly, whichever reads more clearly
given what Step 2 found) declaring every `(pattern, method)` pair in the
exact order the current `elif` chain checks them. Replace the `elif
re.search(...)` chain in `_generate_word` with a loop over this table,
calling the first method whose pattern matches, preserving the exact
matching semantics (first-match-wins, same regex flags) the current chain
has.

- [ ] **Step 4: Run the golden-path parity gate**

Run: `.venv/bin/pytest tests/morphology/test_parity_harness.py -v`

Expected: PASS, zero diff. If it fails, the dispatch table's pattern order
or match semantics diverged from the original chain — compare side-by-side
against the original `elif` order restored from git history.

- [ ] **Step 5: Run the full test suite**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`

Expected: identical pass count to Step 1.

- [ ] **Step 6: Quality gate**

```bash
ruff check wyrdcraeft/services/morphology/generation/noun_forms.py wyrdcraeft/services/morphology/generation/adj_forms.py
.venv/bin/mypy wyrdcraeft/services/morphology/generation/noun_forms.py wyrdcraeft/services/morphology/generation/adj_forms.py
make napoleon-gate
```

- [ ] **Step 7: Commit**

```bash
git add wyrdcraeft/services/morphology/generation/noun_forms.py wyrdcraeft/services/morphology/generation/adj_forms.py
git commit -m "refactor: replace elif paradigm-dispatch chains with declared dispatch tables in NounFormGenerator/AdjectiveFormGenerator"
```

---

### Task 12: Collapse `StrongVerbGenerator`'s callback threading into direct method calls

Per the final review: `StrongVerbGenerator` still has ~19 inline `Callable`-
typed parameters and `partial(...)` construction sites (common.py L627-1188
at time of review — re-locate by name/content, not line number, since Tasks
11 and the cheap-fixes wave shift line numbers) forwarding bound methods as
callback arguments between its own methods, a relocated-but-not-collapsed
form of the pattern ADR 0009 Decision item 4 says gets eliminated. This task
converts each such callback-parameter method into a method that calls the
target method directly on `self`, removing the `partial`/`Callable`
indirection entirely.

**This carries real behavior risk** despite being "just" a calling-
convention change: some of these callbacks are conditionally bound to
different target methods depending on runtime state (that's the actual
reason callback injection was used at each site — confirm via Step 2's read
which sites are genuinely conditional-dispatch vs. which always bind the
same method and can become a direct call trivially). Sites with genuine
runtime-conditional dispatch need an equivalent `if`/`elif` inside the method
body calling the appropriate `self._x(...)` directly, not a naive
find-and-replace.

**Files:**
- Modify: `wyrdcraeft/services/morphology/generation/common.py`
  (`StrongVerbGenerator` only)
- Modify: `wyrdcraeft/models/morphology.py` — **only if** Step 2 confirms a
  given `_Strong*Context` dataclass becomes fully unused once its
  callback-carrying fields are no longer needed (don't touch this file
  speculatively; confirm per-dataclass via grep before removing any)

**Interfaces:**
- Consumes: `StrongVerbGenerator`'s existing constructor shape (unchanged).
- Produces: no change to `StrongVerbGenerator`'s public shape; internal
  methods lose their `Callable`-typed parameters, gain direct calls to
  `self`'s other methods (or an inline conditional calling one of several,
  where Step 2 confirms genuine runtime dispatch).

- [ ] **Step 1: Record baseline**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`, note pass count
(run it yourself).

- [ ] **Step 2: Read every `partial(...)` construction and `Callable`-typed
  parameter in `StrongVerbGenerator`, in full**

For each of the ~19 sites, identify: what method constructs the `partial`,
what target method(s) it can bind to (one, always the same — or more than
one, genuinely conditional on runtime state), and every method that receives
the resulting callback as a parameter and calls it. Categorize each site as
**always-same-target** (trivial direct-call conversion) or
**genuinely-conditional** (needs an inline `if`/`elif` calling the right
`self._x(...)` directly, preserving the exact condition the current dispatch
logic uses to choose between targets).

- [ ] **Step 3: Convert always-same-target sites**

For each site Step 2 confirmed always binds the same target method, delete
the `partial`/`Callable`-parameter plumbing and have the calling method call
`self._x(...)` directly instead.

- [ ] **Step 4: Convert genuinely-conditional sites**

For each site Step 2 confirmed has genuine runtime-conditional dispatch,
replace the callback parameter with an inline `if`/`elif` (matching the
exact condition currently used to select between `partial`-bound targets)
calling the appropriate `self._x(...)` directly. Do not lose any branch — if
the current code has N possible targets, the replacement must have all N
branches.

- [ ] **Step 5: Remove now-unused `Callable` type aliases and `partial` import if fully unused**

Grep `common.py` for remaining uses of each `Callable` type alias that was
only used by the sites just converted, and remove any now-unused ones.
Remove `from functools import partial` only if grep confirms zero remaining
`partial(` calls anywhere in the file (both `StrongVerbGenerator` and
`WeakVerbGenerator` — do not remove it here if Task 13 hasn't run yet and
`WeakVerbGenerator` still uses it; check before removing).

- [ ] **Step 6: Run the golden-path parity gate**

Run: `.venv/bin/pytest tests/morphology/test_parity_harness.py -v`

Expected: PASS, zero diff. This is a genuine behavior-risk task (unlike the
earlier pure-relocation tasks) — if it fails, bisect by reverting one
converted site at a time back to callback-parameter form, prioritizing the
genuinely-conditional sites from Step 4 as the most likely source of a
missed branch.

- [ ] **Step 7: Run the full test suite**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`

Expected: identical pass count to Step 1.

- [ ] **Step 8: Quality gate**

```bash
ruff check wyrdcraeft/services/morphology/generation/common.py
.venv/bin/mypy wyrdcraeft/services/morphology/generation/common.py
make napoleon-gate
```

- [ ] **Step 9: Commit**

```bash
git add wyrdcraeft/services/morphology/generation/common.py
git commit -m "refactor: collapse StrongVerbGenerator's partial/Callable callback threading into direct method calls"
```

---

### Task 13: Collapse `WeakVerbGenerator`'s callback threading into direct method calls

Same approach as Task 12, applied to `WeakVerbGenerator` — the larger side:
per the final review, ~17 more `Callable` type aliases and the bulk of the 36
`partial(...)` sites (common.py L3081-4964 at time of review — re-locate by
name/content) live here, plus the 3 callback `Protocol` classes
(`WeakParticipleAdder`, `WeakFormContextEmitter`,
`WeakPsinsg2SoundWithPostEmitter`) ADR 0009's Consequences section names as
things that "go away." Independent of Task 12 (no shared state between the
strong and weak sides), but do this task after Task 12 lands so Step 5's
"is `partial` still used anywhere" check has one, not two, moving targets.

**Files:**
- Modify: `wyrdcraeft/services/morphology/generation/common.py`
  (`WeakVerbGenerator` only)
- Modify: `wyrdcraeft/models/morphology.py` — **only if** Step 2 confirms a
  given `_Weak*Context` dataclass becomes fully unused (confirm per-dataclass
  via grep, don't remove speculatively)

**Interfaces:**
- Consumes: `WeakVerbGenerator`'s existing constructor shape (unchanged).
- Produces: no change to `WeakVerbGenerator`'s public shape; internal methods
  lose `Callable`-typed parameters, gain direct/conditional `self.` calls.

- [ ] **Step 1: Record baseline**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`, note pass count
(run it yourself).

- [ ] **Step 2: Read every `partial(...)` construction, `Callable`-typed
  parameter, and the 3 `Protocol` classes' usage in `WeakVerbGenerator`, in
  full**

Same categorization as Task 12 Step 2 (always-same-target vs.
genuinely-conditional), plus: for each of the 3 `Protocol` classes
(`WeakParticipleAdder`, `WeakFormContextEmitter`,
`WeakPsinsg2SoundWithPostEmitter`), confirm every call site that currently
type-annotates a parameter with one of these Protocols, and whether that
parameter disappears entirely once the corresponding callback site is
converted to a direct call (it should, if the Protocol exists only to type
the callback parameter this task removes).

This is the largest read among Tasks 11-14, mirroring Task 8's scale —
budget time accordingly and do not skim.

- [ ] **Step 3: Convert always-same-target sites**

Same as Task 12 Step 3, scoped to `WeakVerbGenerator`.

- [ ] **Step 4: Convert genuinely-conditional sites**

Same as Task 12 Step 4, scoped to `WeakVerbGenerator`. Prefer bisecting by
principal-part group (painsg1/psinsg2/pspt/papt) if the parity gate fails,
per this plan's established pattern for the largest verb sub-tasks.

- [ ] **Step 5: Remove now-unused `Callable` type aliases, `Protocol` classes, and `partial` import**

Delete each `Callable` alias and each of the 3 `Protocol` classes once Step 2
confirms no remaining reference. Remove `from functools import partial` if
grep confirms zero remaining `partial(` calls in the whole file (both
verb classes, now that Task 12 has already converted the strong side).

- [ ] **Step 6: Run the golden-path parity gate**

Run: `.venv/bin/pytest tests/morphology/test_parity_harness.py -v`

Expected: PASS, zero diff. Same stash-and-bisect protocol as Task 12 Step 6
if it fails.

- [ ] **Step 7: Run the full test suite**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`

Expected: identical pass count to Step 1.

- [ ] **Step 8: Quality gate**

```bash
ruff check wyrdcraeft/services/morphology/generation/common.py
.venv/bin/mypy wyrdcraeft/services/morphology/generation/common.py
make napoleon-gate
```

- [ ] **Step 9: Commit**

```bash
git add wyrdcraeft/services/morphology/generation/common.py
git commit -m "refactor: collapse WeakVerbGenerator's partial/Callable callback threading into direct method calls, delete callback Protocols"
```

---

### Task 14: Final cleanup — dead `_*Context` dataclasses, `tests/morphology/test_generation_branches.py` update, ADR verification

Closes out Tasks 11-13: removes any of the 8 `_*Context` dataclasses in
`models/morphology.py` that Tasks 12-13 left fully unused, updates
`test_generation_branches.py` for any call site that mocked/monkeypatched a
now-removed `Callable`-parameter signature, and confirms ADR 0009 now
accurately describes the delivered state (no further ADR correction should
be needed if Tasks 11-13 landed as designed — this step is verification, not
another rewrite).

**Files:**
- Modify: `wyrdcraeft/models/morphology.py` (remove confirmed-dead
  `_*Context` dataclasses only)
- Modify: `tests/morphology/test_generation_branches.py` (any remaining call
  sites referencing removed callback parameters/Protocols)
- Modify: `docs/adr/0009-morphology-generation-class-refactor.md` (only if
  verification finds a remaining mismatch)

**Interfaces:**
- Consumes: the state Tasks 11-13 leave behind.
- Produces: nothing new — pure cleanup and verification.

- [ ] **Step 1: Record baseline**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`, note pass count.

- [ ] **Step 2: Grep for each of the 8 `_*Context` dataclasses' usage**

For each of `_StrongPrincipalPartContext`, `_StrongInfDerivationContext`,
`_WeakPrincipalPartContext`, `_WeakInfDerivationContext`,
`_WeakPainsg1DerivationContext`, `_WeakPsinsg2DerivationContext` (and any
others Tasks 12-13's reports name), grep the whole repo for construction/
import sites. Delete only the ones with zero remaining references; leave any
still-constructed dataclass alone and note why in your report.

- [ ] **Step 3: Update `test_generation_branches.py` for any remaining stale call site**

Read the file for any test still monkeypatching/mocking a `Callable`
parameter or `Protocol` type Tasks 12-13 removed; update to call the
now-direct method instead, same pattern as Tasks 12-13's own test updates.

- [ ] **Step 4: Run the golden-path parity gate**

Run: `.venv/bin/pytest tests/morphology/test_parity_harness.py -v`

Expected: PASS, zero diff.

- [ ] **Step 5: Run the full test suite**

Run: `.venv/bin/pytest tests/morphology/ tests/lexicon/ -q`

Expected: identical pass count to Step 1.

- [ ] **Step 6: Verify ADR 0009 accuracy**

Re-read `docs/adr/0009-morphology-generation-class-refactor.md` Decision
items 3-4 and Consequences against the code Tasks 11-13 produced. If
everything now matches (dispatch tables exist, callback threading is gone,
named Protocols are deleted), no edit is needed — say so in your report. If
anything still doesn't match (e.g. a `_*Context` dataclass Step 2 correctly
kept because it's still used, contradicting a Consequences claim that all
context-passing goes away), edit the ADR to describe the actual final state
accurately.

- [ ] **Step 7: Quality gate**

```bash
ruff check wyrdcraeft/models/morphology.py wyrdcraeft/services/morphology/generation/common.py tests/morphology/test_generation_branches.py
.venv/bin/mypy wyrdcraeft/models/morphology.py wyrdcraeft/services/morphology/generation/common.py
make napoleon-gate
```

- [ ] **Step 8: Commit**

```bash
git add wyrdcraeft/models/morphology.py tests/morphology/test_generation_branches.py docs/adr/0009-morphology-generation-class-refactor.md
git commit -m "chore: remove dead verb-context dataclasses, verify ADR 0009 matches delivered state"
```
