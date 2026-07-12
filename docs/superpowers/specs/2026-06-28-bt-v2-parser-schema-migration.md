# BT V2 Parser And Schema Migration

Date: 2026-06-28
Repo: `/Users/cmalek/src/workspace/wyrdcraeft`
Focus: Replace the current flat Bosworth-Toller sense model with a tree-aware
dictionary data model that supports lead glosses, structural headings, hidden
unresolved fragments, and cleaner translator-facing output.

## Context

The current BT pipeline assumes a flat sense list:

- parser emits `BTSense(label, gloss_en)`
- SQLite stores flat `bt_senses`
- dictionary query and CLI render that flat list directly
- lexicon browse v1 separately projects the same flat contract

That model breaks on real corpus cases such as:

- `grǣdig`
  - lead gloss leaks into visible sense list
- `LIBBAN`
  - stray `To`
  - malformed unresolved OE fragment becomes visible output
- `þonne` / `þanne`
  - hierarchical families flatten into unusable soup
- `hālig`
  - supplement line survives as separate `POS: unknown` entry

## Scope

This spec covers BT v2 dictionary work only:

- parser/model/schema changes
- dictionary query contract
- dictionary CLI rendering
- editorial merge behavior needed to produce clean BT entries

This spec does **not** cover:

- lexicon browse adaptation work beyond naming the contract it will consume
- a dual-read compatibility layer
- redesign of the lexicon browse UI

## Dependencies

- Reviewed visibility artifact from
  [2026-06-28-bt-visibility-review.md](/Users/cmalek/src/workspace/wyrdcraeft/docs/superpowers/specs/2026-06-28-bt-visibility-review.md)
- Current BT source corpus and current dictionary indexer
- Browse v1 orchestration may finish independently before this work; this spec
  does not patch or reopen that orchestration plan

## Locked Decisions

- Hard cutover to BT v2; no dual support for flat BT v1 and tree BT v2
- Derived dictionary DB may change schema freely and be rebuilt from source
- Preserve full scholarly structure in storage
- Translator-facing default output hides structural-only nodes by default
- Keep a separate entry-level `lead_gloss`; do not fake it as a numbered sense
- Suspicious unresolved fragments attach to nearest preceding sense
- User-facing stored BT spellings are lowercased:
  - lemma/headword display
  - variants
  - `see_also`
- Raw provenance/source casing remains preserved separately
- Lowercasing must be Unicode-aware and covered by tests for:
  - `Æ/æ`
  - `Ð/ð`
  - `Þ/þ`
  - macronized vowels
  - dotted letters when present

## Problem Classes BT V2 Must Fix

1. **Lead-gloss leakage**
   - `grǣdig` -> `covetous`
   - `LIBBAN` -> `To`
2. **Structural-only pseudo-senses**
   - `with ...`
   - `introducing ...`
   - `the comparison is between ...`
3. **Flattened hierarchy**
   - `A/B/C/D` and nested `I/II/...` families collapse into one list
4. **Malformed unresolved tails**
   - OE or citation fragments incorrectly shown as glosses
5. **Unknown-POS supplement drift**
   - editorial lines should merge into one clear sibling POS when unambiguous
6. **Display spelling inconsistency**
   - e.g. `LIBBAN`

## Target Data Model

### Entry-level model

Each BT entry should expose at least:

- `norm_key`
- `headword_raw`
- `headword_display`
- `pos`
- `genders`
- `variants`
- `lead_gloss`
- `etymology`
- `see_also`
- ordered sense tree
- source line provenance

### Sense-tree model

Replace flat-only `BTSense` assumptions with tree nodes.

Minimum node attributes:

- stable node id
- entry id
- optional parent id
- order index
- `node_kind`
- optional `sense_label`
- `text_en`
- `visible_by_default`
- optional raw/unresolved note payload

Expected `node_kind` values:

- `family_heading`
- `sense_gloss`
- `structural_heading`
- `unclassified`

Interpretation:

- `family_heading`
  - may be visible by default if it meaningfully groups child senses
- `sense_gloss`
  - translator-facing lexical content
- `structural_heading`
  - stored, but usually hidden by default
- `unclassified`
  - unresolved fragment kept for scholar/debug use, hidden by default

## Storage Direction

Conceptual target:

- extend `bt_entries`
  - add `lead_gloss`
  - replace stored display spelling with lowercased display form
- replace flat `bt_senses` dependency with a tree table such as
  `bt_sense_nodes`

Expected node-table columns:

- `id`
- `entry_id`
- `parent_id`
- `order_index`
- `node_kind`
- `sense_label`
- `text_en`
- `visible_by_default`
- `raw_note`

Exact table names may vary, but BT v2 must stop requiring the old flat-only
consumer assumption that every row is just `(sense_label, gloss_en)`.

## Pipeline Changes

### 1. Parsing and segmentation

Update dictionary parsing so it can produce:

- entry-level `lead_gloss`
- ordered tree nodes
- unresolved node attachment points

The parser must stop treating every bold Roman/letter marker as a final visible
gloss row.

### 2. Attestation stripping

Attestation stripping still removes OE/Latin tails for real gloss extraction,
but unresolved or malformed leftovers should no longer be forced into a visible
flat gloss.

### 3. Editorial merge

Update merge logic so:

- unambiguous `unknown` supplement lines inherit sibling POS before final merge
- lead glosses and tree nodes merge without collapsing back to a flat list
- family headings preserve order and parent/child structure

### 4. Lowercased display spellings

Centralize user-facing BT lowercasing in one explicit helper.

Requirements:

- Unicode-aware
- tested against OE letters and marked vowels
- used consistently for stored display headword/variants/see-also values

## Query Contract

Dictionary query should return:

- entry metadata
- `lead_gloss`
- full ordered tree
- default-visible projection metadata

By default, translator-facing consumers should use:

- `lead_gloss` as `Overview:`
- visible tree projection
- hidden unresolved/structural nodes omitted

JSON or internal query payloads may still expose full tree data for scholar or
debug surfaces.

## CLI Output Contract

`wyrdcraeft dictionary lookup` should change from flat:

- `Senses:`
  - `I. ...`
  - `II. ...`

to:

- `Overview: ...` when `lead_gloss` exists
- `Senses:`
  - compact outline using visible family headings and visible child senses

Default CLI behavior:

- show visible nodes only
- do not show hidden unresolved fragments
- do not show structural-only nodes unless future options explicitly request it

## Implementation Slices

### Slice 1: consume visibility review

- turn reviewed artifact into node visibility policy
- avoid broad blacklist hacks

### Slice 2: models and schema

- add entry-level `lead_gloss`
- add tree-node storage
- add lowercased display-spelling path

### Slice 3: parser and merge

- emit tree nodes
- attach unresolved fragments to nearest preceding sense
- inherit POS for unambiguous editorial unknowns

### Slice 4: query and CLI

- expose full tree and default-visible projection
- render `Overview:` and compact outline

### Slice 5: rebuild and verify

- rebuild BT-derived DB
- verify corpus examples now behave as intended

## Acceptance Criteria

BT v2 is done when all of these are true:

1. `grǣdig` summary is separated from numbered senses
2. `LIBBAN` no longer shows stray `To`
3. `LIBBAN` malformed unresolved fragment is not shown as a visible sense
4. `þonne` / `þanne` can be rendered as outline rather than one flat soup list
5. `hālig` supplement content no longer survives as a stray `POS: unknown`
   entry when one unambiguous sibling POS exists
6. displayed lemmas/variants/see-also are lowercased consistently
7. raw/source provenance remains available
8. no dual-read compatibility layer is required to keep old flat schema alive

## Validation

- targeted `pytest` for dictionary parsing/segmentation
- targeted `pytest` for editorial merge
- targeted `pytest` for dictionary query/CLI
- lowercasing tests for OE Unicode edge cases
- `ruff check` on touched Python files
- `.venv/bin/mypy` on touched Python files
- `make napoleon-gate`

## Follow-on Work

After BT v2 lands, execute the separate lexicon adaptation skeleton:

- [2026-06-28-lexicon-browser-bt-v2-adaptation-skeleton.md](/Users/cmalek/src/workspace/wyrdcraeft/docs/superpowers/specs/2026-06-28-lexicon-browser-bt-v2-adaptation-skeleton.md)

That follow-on will update browse code to consume BT v2 instead of the current
flat BT projection assumptions.
