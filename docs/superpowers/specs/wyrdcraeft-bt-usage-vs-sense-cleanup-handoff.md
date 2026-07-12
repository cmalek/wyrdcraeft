# BT Usage-vs-Sense Cleanup Handoff

Date: 2026-06-28
Repo: `/Users/cmalek/src/workspace/wyrdcraeft`
Focus: Clean up Bosworth-Toller pseudo-senses produced by `wyrdcraeft dictionary index-bt` / `dictionary lookup`.

## Current understanding

Problem is real and reproduced from live `data/oe_bt.txt` examples like `wesan`, `þonne`/`þanne`, `þā`, and `willan`.

Root cause is in `wyrdcraeft/services/dictionary/sense_segmenter.py`, not lookup/rendering:

- `BTIndexPipeline._parse_and_segment(...)` always trusts `BTSenseSegmenter`
- `BTSenseSegmenter` currently:
  - splits on sense labels
  - strips attestations
  - keeps any remaining gloss text
- it does **not** distinguish true lexical senses from structural usage headings

Confirmed by direct probe of current segmenter output:

- `wesan` keeps bad pseudo-senses like:
  - `III: with a predicative adjective or participle`
  - `III a: with a predicative genitive`
  - `III b: with prepositional phrases, () prep, and noun`
  - `III c: with a clause`
- `willan` keeps bad pseudo-senses like:
  - `VII: of habitual action`
  - `IX a: without infinitive`
- corpus scan also found other likely bad families:
  - `thanne`: `the comparison is between ...`
  - `cwethan`: `introducing a question`
  - `thaet` / `thaette`: `introducing substantive clauses ...`

User preference already locked:

- `drop only`, not gloss rewriting
- example: keep `as an independent verb ... to be, exist`; do **not** trim that text away
- user wants to review hand-picked candidates before heuristic finalized
- first review batch size: 20 balanced examples

## Key files

- `wyrdcraeft/services/dictionary/sense_segmenter.py`
- `wyrdcraeft/services/dictionary/attestation_stripper.py`
- `wyrdcraeft/services/dictionary/pipeline.py`
- `tests/dictionary/test_sense_segmenter.py`
- `data/oe_bt.txt`

## Proposed implementation

1. Mine candidate pseudo-senses from `data/oe_bt.txt` using current segmenter output.
2. Hand-pick 20 review items:
   - 10 `drop`
   - 10 `keep`
3. Save review artifact under test fixtures.
4. After user approval, add one private post-strip filter inside `BTSenseSegmenter`.
5. Keep heuristic narrow:
   - drop structural/grammatical headings with no standalone definition core
   - keep senses where structural wording still carries real lexical meaning
   - no broad gloss normalization
6. Add regression tests for:
   - user examples
   - approved `keep` counterexamples, especially from `with`, `of`, `in`

## Suggested review artifact shape

For each candidate:

- lemma
- source line number
- sense label
- current gloss text
- verdict: `drop` or `keep`
- one-line rationale

## Useful corpus findings already gathered

Current segmenter-output buckets from whole-corpus scan:

- `with ...`: 469 hits
- `without ...`: 152 hits
- `of ...`: 889 hits
- `in ...`: 703 hits
- `where ...`: 14 hits
- `when ...`: 4 hits
- `denoting ...`: 17 hits
- `used ...`: 110 hits
- `introducing ...`: 6 hits
- `the comparison is ...`: 2 hits

Takeaway: cannot use blunt prefix blacklist. Need paired `drop` and `keep` cases.

## Validation required after edits

- targeted `pytest` for dictionary sense segmentation
- `ruff check` on touched Python files
- `.venv/bin/mypy` on touched Python files
- `make napoleon-gate`

## Suggested skills

- `caveman` for terse operator chatter
- `ponytail:ponytail` to keep heuristic minimal
- `handoff` only if making a fresh temp-dir resume note later
- `superpowers:test-driven-development` before changing filter logic
- `superpowers:verification-before-completion` before claiming done
