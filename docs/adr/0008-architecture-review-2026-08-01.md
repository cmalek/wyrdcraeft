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

No candidate has been chosen or decided on yet. This record exists only to
mark that the review happened; supersede or expand this ADR once the user
picks a candidate and a concrete change is agreed via `/grilling`.

## Status

Superseded when a specific deepening decision is recorded.
