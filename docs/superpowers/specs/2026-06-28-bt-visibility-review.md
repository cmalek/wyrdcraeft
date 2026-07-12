# BT Structural Visibility Review

Date: 2026-06-28
Repo: `/Users/cmalek/src/workspace/wyrdcraeft`
Focus: Review Bosworth-Toller sense/heading candidates to decide what should be
visible by default in translator-facing dictionary and lexicon views.

## Purpose

Before changing the BT parser and storage model, we need a reviewed sample that
separates:

- structural-only headings that should be hidden by default
- genuine lexical content that must remain visible

This spec exists to lock the review artifact and review rules. It does **not**
implement the parser/schema migration itself.

## Why This Is Separate

The earlier narrow plan treated the problem as only a post-strip filter in
`sense_segmenter.py`. Current examples show a broader problem space:

- flat pseudo-senses
- lead-gloss leakage
- true hierarchical families
- malformed unresolved tails

The review set is still useful, but now its job is narrower: define default
visibility policy for structural nodes in the future BT v2 tree.

## Dependencies

- Current BT dictionary data and parser behavior
- Human review of the artifact

This spec should be executed before the BT v2 migration spec, but it does not
depend on the separate lexicon browse v1 orchestration completing first.

## Locked Decisions

- Review batch size: 20 items
- Balance: 10 `hide_by_default`, 10 `keep_visible`
- Preserve scholarly structure in storage later; this review only decides
  translator-facing default visibility
- No broad gloss rewriting
- No dropping unresolved material from storage
- Review artifact should prefer real source examples over synthetic fixtures

## Candidate Types To Include

The sample should cover more than one family of problem:

1. structural grammar/usage headings
   - `with ...`
   - `without ...`
   - `of ...`
   - `in ...`
   - `when ...`
   - `introducing ...`
2. hierarchical family headings
   - `A.`, `B.`, `C.`, `D.`
   - top-level Roman headings that function as family buckets rather than glosses
3. counterexamples where structural-looking wording is still real lexical content
4. at least one example from each of:
   - `wesan`
   - `þonne` / `þanne`
   - `willan`
   - one conjunction/complementizer example such as `cwethan` or `þæt`

## Review Artifact Shape

Each row should contain:

- `lemma`
- `source_line_no`
- `sense_label`
- `node_text`
- `current_reason`
  - short note on why current parser keeps this text
- `proposed_default`
  - `hide_by_default`
  - `keep_visible`
- `rationale`
  - one sentence

Optional but useful:

- `family`
  - e.g. `with`, `comparison`, `question-introducer`
- `pos`

## Review Heuristic Guidance

Use these rules while assembling the sample:

- Hide by default when text is only structural framing and does not stand alone
  as a useful dictionary gloss.
- Keep visible when text still carries lexical meaning a translator would want
  even if the wording is framed structurally.
- When unsure, include the example in the artifact instead of silently deciding.

Examples of likely `hide_by_default`:

- `with a predicative adjective or participle`
- `introducing a question`
- `the comparison is between different objects`

Examples of likely `keep_visible`:

- `as an independent verb ... to be, exist`
- cases where the structural preface still contains the actual semantic value

## Deliverables

1. One review artifact under test fixtures
2. Short note summarizing:
   - reviewed totals
   - ambiguous items
   - any family where rule confidence stays low

## Acceptance Criteria

- Artifact contains 20 reviewed items with the required 10/10 split
- Includes at least three distinct problem families
- Includes at least three `keep_visible` counterexamples that would break a
  blunt prefix blacklist
- Human can inspect artifact without loading `data/oe_bt.txt`

## Non-Goals

- No parser changes
- No schema changes
- No CLI rendering changes
- No lexicon browse changes

## Downstream Use

The BT v2 migration spec will consume this artifact to define which tree nodes
are visible by default in:

- `wyrdcraeft dictionary lookup`
- future lexicon detail views after BT v2 adaptation
