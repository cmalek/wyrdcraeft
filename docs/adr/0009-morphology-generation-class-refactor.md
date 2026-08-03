# ADR 0009: Collapse morphology generation callback-soup into PoS generator classes

## Status

Proposed

## Context

`wyrdcraeft/services/morphology/generation/` is a direct Perl-to-Python port of
`create_dict31.pl` (tichy_oe_generator). During the port, incremental
refactors accumulated redirection layers that the original Perl never had:

- `dispatch.py` — five free functions (`generate_vbforms`,
  `generate_adjforms`, etc.), each just constructing a
  `MorphologyGenerationFacade` and calling one method. No branching, no
  logic, no reason to exist as a separate module.
- `facade.py` — `MorphologyGenerationFacade` is a thin pass-through: each
  public method unpacks `session.word_pool` / `session.run_state` and
  forwards to a module-level function. It adds a class shape without adding
  behavior.
- Per-PoS generator modules (`adj_forms.py`, `adv_forms.py`, `noun_forms.py`,
  `num_forms.py`) are grab-bags of independent `_gen_*` functions selected by
  regex matching on `paradigm` strings inside one large `generate_*forms`
  function. Nothing declares invocation order or shared state; it's
  reconstructed by reading control flow top to bottom.
- Verb generation (`common.py`, `strong_inflections.py`,
  `strong_principal_flow.py`, `strong_derivation_flow.py`,
  `weak_inflections.py`, `weak_principal_flow.py`, `weak_derivation_flow.py`,
  `paradigm_flow.py`, `verb_engine.py`) is the worst offender, and the largest
  part of the package: behavior is threaded through `functools.partial`-bound
  callbacks 4-5 layers deep
  (`generate_strong_verb_parts_with_emitters` → `generate_strong_verb_parts` →
  `emit_strong_principal_part_sequence` → `emit_strong_derived_from_inf_sequence`
  → `emit_strong_derived_from_inf_non_umlaut`, each layer rebinding
  `partial()` callbacks). This was almost certainly introduced while trying
  to keep functions "pure" and independently testable during the port, but it
  makes the actual verb-paradigm generation order nearly impossible to read
  without a debugger. Four specifics matter for the decision below:
  - `common.py` (60KB, the single largest file in the package) contains a
    class named `VerbFormGenerator` (lines 124-1918, ~1,800 lines). Any plan
    to introduce a differently-scoped `VerbFormGenerator` must instead be a
    plan to gut and rebuild *this* class, not to add a new one of the same
    name — this ADR previously described the target as if it didn't exist
    yet, which was wrong.
  - **Second correction (found during implementation, not during ADR review
    or the first correction pass below): `VerbFormGenerator` holds almost no
    logic, and the 7 "callback-driven" modules named above are not glue
    around its logic — they hold essentially all of it.** An AST pass over
    every one of the class's 52 methods (stripped of docstrings) found 49 are
    pure single-statement forwards (`return self._x(...)` or `self._x(...)`,
    nothing else); only `__init__`, `generate`, and `_process_word` contain
    more than one statement, and even those are trivial (a handful of
    attribute assignments, a single loop). The 1,800 lines are overwhelmingly
    docstrings wrapped around delegation, not paradigm logic to "gut." The
    real logic — **~5,000 lines across 87 free functions** — lives in the 7
    modules this ADR calls "now-empty support modules": `strong_inflections.py`
    (8 fns/439 lines), `strong_principal_flow.py` (6/390),
    `strong_derivation_flow.py` (12/670), `weak_inflections.py` (17/949),
    `weak_principal_flow.py` (16/828), `weak_derivation_flow.py` (15/1,119),
    `paradigm_flow.py` (13/567) — coordinated through 68 `Callable`-typed
    parameters accepting `self`-bound methods as injected callbacks. Two of
    these 87 functions (`paradigm_flow.build_verb_formhash_base`,
    `paradigm_flow.derive_paradigm_seed_vowels`) have no corresponding
    `VerbFormGenerator` method at all — they're called from inside another
    free function, not from the class. This means the verb-generation
    collapse (Decision item 4) is not a same-file rename-and-split; it is a
    migration of ~5,000 lines of real logic across 87 functions into two new
    classes, converting `Callable`-injection into ordinary method dispatch,
    under byte-exact parity — a materially larger and differently-shaped task
    than "split `VerbFormGenerator` along its `_strong_*`/`_weak_*` naming
    seam," and should be planned/executed as staged sub-steps (e.g.
    `paradigm_flow.py`'s traversal logic into `VerbFormGenerator` first, then
    the strong trio, then the weak trio), each gated by the parity harness
    independently, rather than as one large change.
  - The actual call chain from `facade.generate_verbs()` to that class is
    five hops deep, and is the single clearest example of the redirection
    problem this whole ADR exists to fix:
    `dispatch.generate_vbforms()` → `facade.generate_verbs()` →
    `common.generate_vbforms()` (a second wrapper function, also in
    `common.py`, whose entire body is a local import of `verb_engine` plus
    two lines constructing/calling it) →
    `verb_engine.VerbFormOrchestrator.generate()` (whose entire body
    constructs `common.VerbFormGenerator` and calls `.generate()`) →
    `common.VerbFormGenerator.generate()`, where any real work finally
    starts. Three of those five hops (`common.generate_vbforms`,
    `VerbFormOrchestrator`, and `dispatch.generate_vbforms`) do nothing but
    forward the call.
  - `form_rows.py` holds shared low-level row-emission primitives
    (`print_one_form`, `output_manual_forms`, `generate_and_print_form`,
    `emit_form_for_context`, `generate_and_print_form_with_sound_changes`,
    etc.) that `adj_forms.py`, `noun_forms.py`, and `adv_forms.py` also call
    directly — this is legitimate shared infrastructure across parts of
    speech, not verb-specific callback soup, and needs different treatment
    than the verb-only files above. `form_assembly.py` (small pure `formParts`
    string helpers: `perl_interpolate`, `assemble_form_parts`,
    `materialize_form`) is consumed only by `form_rows.py` and belongs in the
    same "stays as-is" bucket, not the verb-callback collapse below.
  - **Correction to this ADR's original text (found during implementation
    planning, not caught during the initial review):** `sound_changes.py`
    and `sound_dispatch_flow.py` were originally listed above as verb
    generation's "worst offender" files to gut into a new
    `SoundChangeApplier` collaborator. That was wrong. `form_rows.py` (just
    described as shared, out-of-scope infrastructure) directly imports and
    calls `sound_dispatch_flow.generate_and_print_form_with_sound_changes`
    and `sound_dispatch_flow.emit_sound_changed_form_for_context` — deleting
    `sound_dispatch_flow.py` would break `form_rows.py`, and therefore every
    part-of-speech generator, not just verbs. Worse, `common.py`'s own
    `VerbFormGenerator._generate_and_print_form_with_sound_changes` method is
    itself confirmed to be a one-line forward to that same
    `form_rows.generate_and_print_form_with_sound_changes` function (imported
    at the top of `common.py` as `_generate_and_print_form_with_sound_changes_row`).
    `sound_changes.py`/`sound_dispatch_flow.py` are shared infrastructure
    exactly like `form_rows.py`/`form_assembly.py`, not verb-specific — they
    are removed from the "verb generation" file list above and added to the
    out-of-scope list below. There is no `SoundChangeApplier` class; verb
    generation continues to call `form_rows.py`'s existing shared functions
    directly, the same way `adj_forms.py`/`noun_forms.py`/`adv_forms.py`
    already do.
- `generators/num_forms.py` is a deprecated compatibility shim re-exporting
  `generation.num_forms.generate_numforms` — dead indirection.
- `query.py`, `probability.py`, `form_fk_resolver.py`, `sinks.py`,
  `sound_changes.py`, and `sound_dispatch_flow.py` are unrelated concerns
  (SQL query service, small numeric helpers, morph-class FK resolution,
  output sinks — SQLite/TSV/composite — and shared sound-change row
  derivation) that happen to live in the same package; they are fine as-is
  and out of scope here. Note `form_rows.py` (kept, see below) imports
  `TsvParitySink` from `sinks.py` and `generate_and_print_form_with_sound_changes`/
  `emit_sound_changed_form_for_context` from `sound_dispatch_flow.py`
  directly — the dependency runs from kept code into out-of-scope code, not
  the reverse, so this doesn't pull `sinks.py`/`sound_dispatch_flow.py` into
  scope, but it means neither can be touched independently of verifying
  `form_rows.py` still works.

This violates `AGENTS.md`'s Architecture section directly: it calls for
"cohesive, human-comprehensible classes over loose function collections,"
methods ≤ 60 lines, single responsibility per class, and per-run mutable
state isolated in a dedicated orchestrator — none of which the current
callback-threaded shape provides.

**Constraint:** output parity with the Perl generator must be preserved
exactly (row order, `formParts`/`probability` values, etc.). This is a
structural refactor, not a behavior change.

## Decision

1. **Delete `dispatch.py`.** `facade.py`'s `MorphologyGenerationFacade`
   becomes the sole public entrypoint into generation. `dispatch` currently
   has nine importers, not just the parity harness:
   - Production code: `wyrdcraeft/services/morphology/reference_snapshots.py`,
     `wyrdcraeft/services/morphology/build_runner.py`
   - Tests: `tests/morphology/parity_harness.py`,
     `tests/morphology/test_form_generation_reference.py`,
     `tests/morphology/test_generation_package_imports.py`,
     `tests/morphology/test_query_service.py`,
     `tests/morphology/test_full_flow_reference.py`
   - Scripts: `scripts/morphology/generate_refactor_baseline.py`,
     `scripts/morphology/profile_adj_stage.py`

   Every one of these must be updated to construct a
   `MorphologyGenerationFacade(session, output)` instead of importing the
   free functions, but not all of them can just call `.generate_all_forms()`
   — three distinct shapes exist:
   - **Call the aggregate method directly:** `parity_harness.py`,
     `test_query_service.py`, `test_form_generation_reference.py`, and
     `test_full_flow_reference.py` import all six functions and call them in
     `generate_all_forms()`'s exact order with no per-stage logic in
     between — a straight swap. `reference_snapshots.py` does the same at
     *three* separate call sites within the file (not one), so the swap
     applies three times there.
   - **Need individual bound methods, not one call:** `build_runner.py`
     does **not** call these functions directly — it passes each one as a
     bound callable into a per-stage runner config
     (`generator=output_manual_forms`, `generator=generate_vbforms`, etc.,
     presumably for per-stage progress tracking), in the same six-stage
     order. This must become `generator=facade.output_manual_forms`,
     `generator=facade.generate_verbs`, etc. — six individually-referenced
     bound methods, not one `generate_all_forms()` call.
     `scripts/morphology/profile_adj_stage.py` (only
     `output_manual_forms`/`generate_vbforms`/`generate_adjforms`, to profile
     just the adjective stage) and
     `scripts/morphology/generate_refactor_baseline.py` (five of six,
     omitting `output_manual_forms`) need the same individual-method
     treatment for a different reason — they only exercise a subset of
     stages.
   - **Rewrite outright:** `test_generation_package_imports.py` only smoke
     tests that `generate_vbforms` is importable/callable from `dispatch` —
     it needs rewriting to assert against the facade (e.g.
     `MorphologyGenerationFacade.generate_verbs` is callable) since there is
     no longer a `dispatch` module to smoke-test.

   The two production callers (`reference_snapshots.py`, `build_runner.py`)
   are the higher-risk half of this list — they're both correctness-real,
   not test/profiling code, and `build_runner.py` in particular needs the
   less-mechanical bound-method migration. All nine must land in the same
   change as `dispatch.py`'s deletion (a partial migration leaves half the
   callers broken); the parity harness in particular must stay green and
   importable throughout, since it is the golden-path check for every step
   that follows.

2. **Keep `facade.py`, thin by design.** It stays a thin facade per
   `AGENTS.md` ("keep the public service a thin facade with a small
   entry-point API") — but each method now delegates to one PoS generator
   class instance instead of a module-level function.

3. **One generator class per part of speech**, replacing each `_gen_*`
   grab-bag module:
   - `AdjectiveFormGenerator` (replaces `adj_forms.py` free functions)
   - `AdverbFormGenerator` (replaces `adv_forms.py`)
   - `NounFormGenerator` (replaces `noun_forms.py`)
   - `NumeralFormGenerator` (replaces `num_forms.py`)

   Each class takes `WordPool`, `GenerationRunState`, `FormOutput`, and
   optional progress coordinator via constructor injection (matching
   existing signatures), exposes one public `generate()` method, and moves
   today's `_gen_<paradigm>` functions to private methods with an explicit
   paradigm-dispatch table (dict of paradigm-pattern → bound method) instead
   of a chain of `elif re.search(...)`. This makes invocation order and
   paradigm coverage readable as data, not control flow.

4. **Full collapse of strong/weak verb generation, rebuilding the existing
   `common.VerbFormGenerator` rather than adding a class of the same name.**
   Delete `verb_engine.py` and `common.py`'s `generate_vbforms()` wrapper
   function entirely — both are pure redirection (see Context), and
   `facade.generate_verbs()` should construct and call `VerbFormGenerator`
   directly, collapsing the five-hop chain down to one, consistent with
   removing every other thin wrapper in this ADR.

   Per the second correction in Context, this is not "gut the
   callback-threading inside `VerbFormGenerator`" — `VerbFormGenerator`
   itself holds almost none of it. The actual work is migrating the ~5,000
   lines of real logic (87 functions) out of `strong_inflections.py`,
   `strong_principal_flow.py`, `strong_derivation_flow.py`,
   `weak_inflections.py`, `weak_principal_flow.py`, `weak_derivation_flow.py`,
   and `paradigm_flow.py`, replacing the current
   `Callable`-injection/free-function shape with:
   - `VerbFormGenerator` (kept as the top-level name callers already know,
     via `facade.generate_verbs()`; its current ~1,800-line body is rewritten,
     not renamed away) — the "dedicated execution/orchestrator class"
     `AGENTS.md` asks for. Owns per-paradigm/per-word iteration (today's
     `paradigm_flow.py` traversal collapses into plain iteration here, not a
     separately dispatched callback chain) and constructs one
     `StrongVerbGenerator` or `WeakVerbGenerator` per word/paradigm to drive.
   - `StrongVerbGenerator` — holds the active `Word`, `VerbParadigm`,
     `GenerationRunState`, `FormOutput`, and per-variant/per-part context as
     instance state (replacing `_StrongPrincipalPartContext` and the
     `partial()`-bound emitter chain across `strong_inflections.py`,
     `strong_principal_flow.py`, and `strong_derivation_flow.py`). Methods
     correspond directly to Perl block names (`_emit_principal_part`,
     `_emit_infinitive_derived`, `_emit_painsg1_derived`,
     `_emit_painpl_derived`, `_emit_umlaut_forms`) called in explicit,
     readable sequence from one `generate_word(word, paradigm)` entry method.
   - `WeakVerbGenerator` — same treatment for `_WeakPrincipalPartContext` /
     `_WeakInfDerivationContext` / `_WeakPainsg1DerivationContext` /
     `_WeakPsinsg2DerivationContext` across `weak_inflections.py`,
     `weak_principal_flow.py`, and `weak_derivation_flow.py`, collapsing the
     current context-then-emitter-then-context-again indirection into direct
     method calls on `self`.
   - No `SoundChangeApplier` class. `sound_changes.py`/`sound_dispatch_flow.py`
     are shared cross-PoS infrastructure (see the correction above), not part
     of this collapse. Several of `VerbFormGenerator`'s current methods
     (`_generate_and_print_form_with_sound_changes`,
     `_add_participle_to_adjectives`, and likely others sharing the same
     `X as _X_row`/`X as _X_session` import-aliasing pattern at the top of
     `common.py`) are themselves confirmed thin one-line forwards to
     `form_rows.py`/`participles.py` functions — those wrapper methods are
     deleted outright, not relocated into either new class, and
     `StrongVerbGenerator`/`WeakVerbGenerator` call the shared functions
     directly instead (an eighth instance of the exact redirection pattern
     this ADR exists to remove, found only once someone actually read the
     method bodies rather than trusting the names).
   - `StrongVerbGenerator`/`WeakVerbGenerator` remain the stateless-per-call
     collaborators `VerbFormGenerator` drives (they hold per-word context,
     not cross-word run state, so they don't violate the
     stateless-collaborator guidance in spirit — cross-word state stays in
     `GenerationRunState`, unchanged).
   - Row emission continues to go through `form_rows.py`'s shared primitives
     (`print_one_form`, `generate_and_print_form`, etc.), the
     `form_assembly.py` helpers it calls, and `sound_changes.py`/
     `sound_dispatch_flow.py`'s sound-change derivation — all are cross-PoS
     infrastructure (also used by `adj_forms.py`, `noun_forms.py`,
     `adv_forms.py`) and are not part of this collapse; only their
     verb-specific callers (the former thin-wrapper methods, now deleted)
     change shape.

   `models/morphology.py` currently exports six `_*Context` dataclasses
   (`_StrongPrincipalPartContext`, `_StrongInfDerivationContext`,
   `_WeakPrincipalPartContext`, `_WeakInfDerivationContext`,
   `_WeakPainsg1DerivationContext`, `_WeakPsinsg2DerivationContext`) that
   exist to carry state between the free functions above. Once that state
   lives on `StrongVerbGenerator`/`WeakVerbGenerator` instances instead,
   these dataclasses are largely redundant, but `models/morphology.py` is a
   separate file from every one named in this task's scope and removing them
   is a separate blast-radius decision — implementers should confirm at
   execution time whether removal is in scope or deferred, rather than
   assuming either way.

   Given the corrected size of this migration (~5,000 lines / 87 functions,
   not a same-file rename), it should be planned and executed as staged
   sub-steps with independent parity-harness gates per stage (e.g.
   `paradigm_flow.py`'s traversal logic into `VerbFormGenerator` first, then
   the strong-side modules into `StrongVerbGenerator`, then the weak-side
   modules into `WeakVerbGenerator`), not as one single change landing all
   87 functions behind one gate — a single gate on a change this size
   gives a parity failure nothing useful to bisect against.

5. **Delete `generators/num_forms.py`.** Confirmed zero callers in the repo
   (production, tests, or scripts) — it is pure dead weight, safe to delete
   outright with no migration step needed. This leaves `generators/`
   containing only an empty `__init__.py`; delete the whole directory rather
   than leave a package with nothing in it.

6. **`query.py`, `probability.py`, `form_fk_resolver.py`, `sinks.py`,
   `sound_changes.py`, and `sound_dispatch_flow.py` are untouched** — out of
   scope, no architectural complaint against any of them.

7. **Output parity is enforced by `tests/morphology/test_parity_harness.py`**
   (`test_parity_harness_matches_subset_snapshot`, comparing a full
   generation run over `tests/morphology/data/full_flow_subset.jsonl.gz`
   against `parity_harness.assert_snapshot_parity`). This is the golden-path
   check: run it before touching a module and after each incremental step: a
   diff here means a parity regression, full stop. No behavior change is
   intended; this ADR only changes structure/naming/call shape.

## Consequences

**Positive:**
- Verb generation order becomes traceable by reading one class's methods
  top-to-bottom instead of following `functools.partial` chains across nine
  files (`common.py`, `strong_inflections.py`, `strong_principal_flow.py`,
  `strong_derivation_flow.py`, `weak_inflections.py`,
  `weak_principal_flow.py`, `weak_derivation_flow.py`, `paradigm_flow.py`,
  and `verb_engine.py`) plus a five-hop call chain collapsed to one, plus
  deleting several confirmed thin-wrapper methods inside `VerbFormGenerator`
  itself that forwarded into `form_rows.py`/`participles.py`.
- Paradigm dispatch in adjective/adverb/noun/numeral generation becomes a
  declared table instead of an implicit `elif` chain, making "which
  paradigms exist" answerable by reading one attribute instead of the whole
  function body.
- Three fewer indirection files (`dispatch.py`, `verb_engine.py`, and
  `generators/num_forms.py` all deleted).
- Matches `AGENTS.md` Architecture section directly (cohesive classes,
  ≤60-line methods, single responsibility, thin facade, dedicated
  orchestrator for per-run state).

**Negative / risks:**
- Large mechanical diff across the entire `generation/` package; must be
  done incrementally per PoS/verb-class with differential tests run after
  each step to catch parity regressions early rather than at the end.
- The verb-generation collapse (item 4) is substantially larger than a
  same-file class split: ~5,000 lines across 87 functions must move out of
  7 modules into two new classes, converting `Callable`-injection into
  method dispatch. This should be staged into independently-gated sub-steps
  (see item 4) rather than landed as one change — a single parity gate on a
  change this size cannot localize a regression if one appears.
- The many `Protocol`/`Callable` type aliases used for callback signatures
  (e.g. `StrongFormEmitter`, `WeakPsinsg2SoundWithPostEmitter`) go away;
  anything outside this package that imports them directly (unlikely, but
  not yet verified) will need updating.
- Some current "pure function" unit tests that test individual `_emit_*`
  helpers in isolation will need to become method-level tests on the new
  classes; test count/shape changes, though coverage intent stays the same.
- Once step 1 lands, `tests/morphology/parity_harness.py` (and the other
  eight `dispatch` importers) call into generation only through the facade.
  Steps 2-6 then only require touching the harness if they change the
  facade's public method shapes — none are planned to. If a later step does
  need to change a facade method signature, the harness update must land in
  the same change, since it is the mechanism every other step is verified
  against.

## Alternatives Considered

- **Partial collapse (wrap callbacks in thin classes, keep internals
  callback-based):** rejected — this was explicitly considered and rejected
  in favor of full collapse, since the callback threading itself (not just
  its packaging) is the readability problem.
- **Leave verb flow alone, only refactor simpler PoS generators:** rejected
  for the same reason — verb generation is where the redirection actually
  hurts, and deferring it risks the ADR being reopened immediately after
  merge with no new information gained.
