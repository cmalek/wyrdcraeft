# Architecture review — 2026-08-01

Placeholder ADR. An `/improve-codebase-architecture` pass was run against the
current tree (commit `120c22b3`) to surface deepening candidates: seams that
are shallow (interface ~= implementation) versus ones that concentrate real
behavior.

Candidates surfaced from god-node/import-cycle analysis (graphify + codegraph):

- `GeneratorSession` (`wyrdcraeft/services/morphology/session.py`) — public
  mutable list/dict fields (`words`, `manual_forms`, `verb_paradigms`, ...)
  reached into directly by 56+ callers across the morphology package.
- `wyrdcraeft/services/morphology/generation/facade.py` +
  `generation/__init__.py` — thin one-line delegate methods that create
  import cycles (8 cycles reported, all rooted here) without hiding real
  complexity.
- `cli()` root command (`wyrdcraeft/cli/cli.py`) — mixes settings load,
  logging config, and DB-readiness gating in one entry point; 97 callers.

## Decision

Candidate #2 (the `generation/__init__.py` / `facade.py` import cycles) was
picked and implemented (plan:
`docs/superpowers/plans/2026-08-01-generation-package-import-cycle.md`,
merged commit `8ac0187`). Root cause turned out simpler than the original
guess above: `facade.py` already imported its sibling `*_forms.py` /
`*_flow.py` modules directly — the actual cycle root was
`generation/__init__.py` eagerly re-exporting `MorphologyGenerationFacade`
via `from .facade import MorphologyGenerationFacade`, which nothing in the
repo consumed (every real caller already used `.facade` or `.dispatch`
directly). The fix was to delete that dead re-export, reducing
`generation/__init__.py` to its module docstring. Verified: all 8 reported
cycles gone (`graphify-out/GRAPH_REPORT.md` Import Cycles section reads
"None detected"), 358/358 tests passing, zero behavior change for any
caller.

**Caveat on "None detected":** graphify's cycle detection is file-level and
does not see cycles built from deferred (in-function-body) imports. There
is a separate, known, and deliberately out-of-scope cycle between
`wyrdcraeft/services/morphology/generation/common.py` and
`wyrdcraeft/services/morphology/generation/verb_engine.py` —
`verb_engine.py` does `from .common import VerbFormGenerator` at module
level, and `common.py`'s `generate_vbforms` does `from .verb_engine import
VerbFormOrchestrator` deferred inside the function body specifically to
break that cycle. That deferred-import pattern is legitimate and necessary
(the two modules genuinely depend on each other), but it means a clean
graphify report should not be read as "this package has no import cycles at
all" — only "no cycles graphify's static file-level scan can see." If this
cycle is ever worth resolving (e.g. by extracting a shared interface both
modules can depend on instead of depending on each other), it needs its own
ADR/plan; it was left untouched here since removing the workaround without
addressing the underlying two-way dependency would just move it back to a
load-time ImportError.

Candidate #3 (`cli()` mixed-concern entrypoint) is **closed, not worth
doing**. A `graphify query`/`graphify path` trace of the DB-readiness call
chain (`cli()` → `_run_database_readiness_gate()` →
`ensure_database_ready()` → `DatabaseStartupRuntime.ensure_ready()` →
`._handle_pending_backup()` / `._get_current_revision()` /
`._get_head_revision()` / `._create_backup()` /
`._run_migration_attempt()` / `._reset_to_fresh_canonical_db()`, raising
`LegacyDatabaseResetRequired` on the legacy-reset path) showed the original
worry was overstated: the migration/backup/legacy-reset decision tree is
already a genuinely deep module — one small entry point
(`ensure_database_ready()`) hiding real orchestration behind it — properly
living in `wyrdcraeft/db/runtime.py`, not leaked into the CLI layer. What's
left in `cli()` is only that it inlines the startup *sequence* (settings
load → logging config → console-state reset → call the gate) as loose
statements in the Click command body rather than one named
`CliBootstrap`-style collaborator. That's cosmetic sequencing, not a
business-logic leak, and not worth a task on its own. Revisit only if
`cli()` grows further or that sequencing becomes a real testability
problem in practice.

Candidate #1 (`GeneratorSession` god-object) was picked and implemented
(plan: `docs/superpowers/plans/2026-08-02-generatorsession-word-pool-run-state-split.md`,
merged commit `33d143d`, 10 commits across a 9-task subagent-driven-development
run). Investigation found `GeneratorSession` conflated two different kinds of
state: word-pool data (`words`/`manual_forms`/`verb_paradigms`/`prefixes`/
`adjectives`/`nouns`/`verbs`) and cross-stage scalar run state
(`output_counter`/`perl_probability`/`enable_num_probability_carry`/
`enable_r_stem_nouns` — genuinely shared mutable state by design, matching
the "per-run orchestration + mutable run state" pattern `AGENTS.md` already
blesses, not itself the coupling problem). The fix split it into `WordPool`
and `GenerationRunState`, with `GeneratorSession` composing both via full
get/set forwarding properties (added first, non-breaking, so every
subsequent task could migrate one caller layer at a time). Each of the
three paradigm assigners, the shared sink/row-emission layer used by all 5
generation paths, and each of the 5 PoS generators (adverb → numeral → noun
→ adjective → verb, in increasing risk order) were migrated in turn to take
`word_pool: WordPool` / `run_state: GenerationRunState` directly instead of
the whole `GeneratorSession`.

Verified: `GeneratorSession`'s graph edge count dropped from 176 to 110
(-37.5%); mypy went from passing-with-caveats to 0 errors across the whole
140-file `wyrdcraeft` package; the existing golden-snapshot parity tests
(`test_full_flow_reference.py` et al. — this codebase is a near-direct
Perl-to-Python translation where output parity is byte-for-byte
non-negotiable) passed with zero diff after every one of the 9 tasks and
the final whole-branch review's fix wave; 1094 passed / 3 skipped on the
full repo suite after merge. `Word`'s edge count ticked up slightly
(164→168) rather than dropping — assessed as graphify heuristic
re-anchoring noise (the same `list[Word]` type relationship just anchored
at `WordPool` instead of `GeneratorSession` in more places), not a real
regression, since no new production coupling to `Word` was introduced and
every gate stayed green. The more accurate framing: raw coupling was
*redistributed*, not purely reduced — `GenerationRunState` itself entered
the God Nodes list with 81 edges — but a narrow, cohesive 4-field value
object appearing widely as a parameter type is qualitatively different
from one 11-attribute god object appearing everywhere; judge this on
cohesion, which genuinely improved.

The final whole-branch review (run after all 9 tasks, per
subagent-driven-development) found no Critical issues and one fix wave
covering: a stale napoleon-gate baseline (2 line numbers drifted by this
branch's changes), missing `Side Effects:` docstring sections on the two
functions that write the cross-stage `enable_num_probability_carry`/
`perl_probability` flags, `prefix_regex` logic duplicated three times
(deduped into `WordPool.prefix_regex`, with `GeneratorSession.prefix_regex`
now forwarding to it), a stale `ParadigmAssigner` protocol in `contracts.py`
(zero implementers, updated anyway for consistency), and one more dead
legacy wrapper function in `common.py` (deleted, joining four siblings
already removed in Task 8). One residual minor finding was parked rather
than triggering a second fix wave: `_gen_weak`'s new `Side Effects:` section
copies its sibling `_emit_weak_degree_forms`'s wording verbatim, which
itself never documented its own `run_state.perl_probability` write — a
tiny documentation-completeness gap in both functions, zero parity/behavior
risk, worth a standalone follow-up docstring tweak someday.

## Status

All three candidates resolved: the import-cycle candidate (#2) and the
`GeneratorSession` god-object candidate (#1) are decided and shipped; the
`cli()` candidate (#3) is closed as not worth doing.
