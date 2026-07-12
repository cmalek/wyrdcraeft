# Lexicon Browser BT V2 Adaptation Skeleton

Date: 2026-06-28
Repo: `/Users/cmalek/src/workspace/wyrdcraeft`
Focus: Adapt lexicon browse v1 to consume BT v2 dictionary data with minimal UI
delta after the BT parser/schema migration lands.

## Purpose

This is intentionally a dependency-first skeleton, not a full implementation
plan yet.

Reason:

- lexicon browse v1 is being finished separately against the current flat BT
  contract
- BT v2 will change the dictionary-side contract materially
- we want the browser adaptation captured now, but we do not want to guess the
  exact adapter details before BT v2 lands

## Dependencies

This plan should not be implemented until all of these are true:

1. browse v1 orchestration has finished
2. BT visibility review is complete
3. BT v2 parser/schema/query/CLI migration has landed

Required upstream specs:

- [2026-06-28-bt-visibility-review.md](/Users/cmalek/src/workspace/wyrdcraeft/docs/superpowers/specs/2026-06-28-bt-visibility-review.md)
- [2026-06-28-bt-v2-parser-schema-migration.md](/Users/cmalek/src/workspace/wyrdcraeft/docs/superpowers/specs/2026-06-28-bt-v2-parser-schema-migration.md)

## Locked Decisions

- Minimal UI delta only
- Keep current browse shell shape:
  - left results pane
  - right details pane
  - no TUI redesign
- Hard cutover to BT v2
- No dual support for flat BT v1 and tree BT v2 contracts
- Hidden structural/unresolved nodes remain out of translator-facing browse view

## Expected BT V2 Inputs

The browse layer should assume BT v2 can provide:

- lowercased display lemma/headword
- lowercased variants
- entry-level `lead_gloss`
- visible tree projection for translator-facing output
- full scholarly tree stored behind that projection
- hidden unresolved/structural nodes excluded from default-visible output

This plan deliberately avoids locking exact BT v2 table names.

## Browse Changes This Plan Owns

When BT v2 is ready, this plan should adapt:

- lexicon build projection
- lexicon query details payload
- details-pane rendering
- tests that currently assume flat `senses_json` + first-gloss summary

Likely touched files:

- `wyrdcraeft/services/lexicon/build.py`
- `wyrdcraeft/services/lexicon/query.py`
- `wyrdcraeft/services/lexicon/tui.py`
- `wyrdcraeft/services/lexicon/schema.py`
- `tests/lexicon/test_build.py`
- `tests/lexicon/test_query_service.py`
- `tests/lexicon/test_tui.py`

## Likely Data-Contract Changes

Current browse code assumes:

- one flat summary sense
- one flat ordered full-sense list

After BT v2, browse should instead consume:

- overview text derived from `lead_gloss`
- visible dictionary detail payload derived from BT tree projection

The exact internal lexicon storage choice remains open until BT v2 lands:

- either keep a projected browse-friendly summary/outline payload in
  `lexicon_*`
- or keep a thinner lexicon projection and let query/TUI shape the outline

That decision should be filled in after BT v2 is concrete.

## Details-Pane Outcome

Minimal expected user-facing change:

- same details pane
- same overall browse interaction
- dictionary section becomes:
  - `Overview`
  - outlined senses/families
  - no raw hidden structural nodes

What should stay stable:

- results list behavior
- single-hit auto-focus behavior
- orphan morphology section behavior
- morphology grouping behavior

## Open Questions Deferred Until BT V2 Lands

1. Should lexicon projection store pre-rendered visible outline JSON, or rebuild
   outline from BT query payload on demand?
2. Should summary/overview live in `lexicon_entries` as a simple string cache,
   or be derived lazily from BT-side `lead_gloss`?
3. What is the cheapest stable serialization shape for outlined senses inside
   `lexicon_*` if denormalized projection remains desirable?
4. Do any result-row disambiguation tweaks become necessary once lemmas are
   lowercased uniformly?

## Skeleton Implementation Order

Fill this section in after BT v2 lands.

Expected eventual order:

1. inspect final BT v2 query/storage contract
2. choose lexicon projection boundary
3. update builder projection
4. update query payloads
5. update details-pane rendering with minimal UI delta
6. refresh tests and docs

## Acceptance Criteria

This plan will be ready to flesh out when BT v2 is done and the team can answer:

- exact BT v2 payload shape for overview and visible tree
- whether lexicon stores projected outline or computes it at query time
- which current browse tests fail because of flat-sense assumptions

This plan will be done later when:

- lexicon browse consumes BT v2 without dual-support code
- details pane shows overview + outline cleanly
- no hidden structural/unresolved nodes leak into default translator view
- UI layout remains recognizably browse v1
