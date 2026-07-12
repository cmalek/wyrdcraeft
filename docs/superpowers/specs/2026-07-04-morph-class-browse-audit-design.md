# Morph Class Browse And Audit Design

Date: 2026-07-04
Repo: `/Users/cmalek/src/workspace/wyrdcraeft`
Focus: Use existing Wright catalog work to surface modern linguistic class plus
Wright citations in `lexicon browse`, while keeping legacy source `wright`
fields as audit inputs rather than canonical truth.

## Purpose

This design clarifies what the product should treat as primary truth for
dictionary morphology classification.

Target outcome:

- each dictionary lemma+POS can show a modern linguistic class label
- the same detail pane can show linked Wright section citations
- users can inspect Wright text inline from `lexicon browse`
- legacy `wright` source columns remain valuable for validation, but do not
  block deterministic classification

This is a focused design on top of the existing Wright catalog phase work. It
does not replace:

- [doc/plans/morphology-wright-catalog/00-design-decisions.md](/Users/cmalek/src/workspace/wyrdcraeft/doc/plans/morphology-wright-catalog/00-design-decisions.md)
- [doc/plans/morphology-wright-catalog/phase-3-forms-link-and-query.md](/Users/cmalek/src/workspace/wyrdcraeft/doc/plans/morphology-wright-catalog/phase-3-forms-link-and-query.md)
- [doc/plans/morphology-wright-catalog/phase-4-wright-section-text-ingest.md](/Users/cmalek/src/workspace/wyrdcraeft/doc/plans/morphology-wright-catalog/phase-4-wright-section-text-ingest.md)

## Current Facts

- `lemma_morph_classes` already exists as `(normalized_title, pos) ->
  morph_class_id`
- `morph_classes` already stores full class metadata, including
  `canonical_name`, `modern_class`, and `traditional_class`
- `wright_sections` already exists and already anticipates stored `section_text`
- `MorphologyCatalogQueryService.lookup_lemma_class()` already returns class
  metadata plus Wright section numbers
- source data still has large Wright gaps:
  - `dict_adj-vb-part-num-adv-noun.txt`: `34,263` relevant lemmas,
    `30,260` missing Wright
  - `manual_forms.txt`: only `85` relevant lemma+POS pairs, `4` missing Wright
  - `para_vb.txt`: `119` rows contain invalid token `Camp`

Conclusion: source `wright` is too incomplete and noisy to be canonical truth.

## Locked Decisions

- Primary truth is `morph class`, not legacy source `wright`
- Wright sections remain required product data, but as class-linked citations
- Deterministic only:
  - one exact class -> assign
  - zero exact classes -> leave unclassified
  - many exact classes -> leave unclassified
- Classification is per POS bucket, not headword-wide
- First browse release is display-only
- First browse release attaches class/Wright to dictionary detail only
- First browse release shows `Unclassified` explicitly
- Wright section text opens inline or in an overlay pane
- Source lemma validation is a separate audit command, not part of normal build

## Canonical Model

The main product model should be:

```text
(normalized_title, pos) -> lemma_morph_classes -> morph_classes
                                         \
                                          -> provenance

morph_classes -> morph_class_wright_sections -> wright_sections
```

Interpretation:

- `lemma_morph_classes` is the canonical lemma classification layer
- `morph_classes` carries the modern scholarly label users care about
- Wright sections are supporting citations attached to the class
- legacy source `wright` values are inputs for validation and limited fallback,
  not primary product truth

## Browse V1

`lexicon browse` should enrich dictionary detail rows by join-time lookup, not
by first-release denormalization into lexicon projection tables.

Reason:

- first release is display-only
- existing catalog tables already hold needed data
- join-time lookup keeps schema churn small
- label/text behavior can evolve without reshaping lexicon read-model tables

Dictionary detail pane should show:

- full class label
  - examples:
    - `noun, masculine a-stem`
    - `verb, strong class IIa`
    - `adjective, strong a/o-stem`
- assignment provenance
  - `paradigm`
  - `features`
  - `wright_section`
- Wright citation list
  - clickable/selectable section numbers
- explicit `Unclassified` when no deterministic class exists

First release should not:

- decorate every morphology form row with class metadata
- add class or Wright filters
- add analysis UX

Those are later steps once classification quality is proven in use.

## Wright Text Pane

When a user selects a Wright section citation in browse, the UI should show the
stored section text inline or in an overlay pane.

Implementation direction:

- follow Phase 4 plan
- ingest `data/sources/wright.md` into `wright_sections.section_text`
- browse reads from SQLite, not from runtime markdown or PDF parsing

If a class links to many Wright sections:

- show all linked sections
- let user inspect any of them
- do not invent one fake "primary" section for first release

## Audit Command

Validation should live in a separate audit command with:

- human-readable summary by default
- optional JSON output for later analysis

First audit scope:

- source lemma files first
- generated/manual artifacts second

First audit checks:

1. malformed legacy Wright values
   - legal shape: blank, `0`, or semicolon-list of integers
   - example invalid token: `Camp`
2. contradiction between encoded Wright and deterministically assigned class
   sections
3. unclassified lemma+POS rows
4. lemma+POS rows where deterministic class exists even though encoded Wright is
   blank

First audit command should not:

- rewrite source files automatically
- block normal `morphology build`
- insert probabilistic suggestions into canonical tables

## Relationship To Existing Phase Work

This design sharpens the intended use of existing Wright catalog slices:

- Phase 2 remains the core classification layer
  - `lemma_morph_classes` is canonical truth for lemma+POS classification
- Phase 3 should surface that classification in browse/query
  - first release can prefer join-time browse lookup
  - later work may denormalize if performance or UX demands it
- Phase 4 should ingest Wright section text
  - this is required for inline/overlay browse inspection

## Non-Goals

This design does not commit first-release work for:

- browse filters by class or Wright
- browse analysis dashboards
- auto-cleanup of source `wright` fields
- probabilistic classification queues
- manual curation workflow
- forced single-section narrowing when only class-level section sets are known

## Recommended Incremental Order

1. enrich browse dictionary detail with class label, provenance, and Wright
   section numbers using existing assignment/catalog tables
2. ingest Wright section text into `wright_sections.section_text`
3. add browse inline/overlay section text pane
4. add separate audit command for legacy Wright quality and deterministic
   coverage reporting
5. later: add filters and analysis once browse display is trusted

## Acceptance Criteria

This design is satisfied when all of these are true:

- browse shows per-POS class metadata on dictionary detail rows
- unclassified rows are visible as `Unclassified`
- browse can show Wright section text inline or in overlay from stored DB text
- no first-release UX depends on filling missing source `wright` cells
- audit command can report malformed, contradictory, and unclassified source
  rows without mutating source files
