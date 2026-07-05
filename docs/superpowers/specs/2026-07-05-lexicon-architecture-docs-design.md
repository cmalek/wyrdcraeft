# Lexicon Architecture Docs Design

Date: 2026-07-05
Repo: `/Users/cmalek/src/workspace/wyrdcraeft`
Focus: Replace current user-facing architecture docs with a four-page
architecture set that explains dictionary, morphology, and lexicon as-built for
both scholars and engineers.

## Purpose

`wyrdcraeft` now has three linked lexicon-building flows with real source
provenance, real SQLite sinks, and real workflow boundaries:

- dictionary
- morphology
- lexicon

Current user-facing architecture pages do not explain those flows clearly for
either primary audience:

- scholarly translators and linguists
- computational linguists and software engineers

This design defines a replacement architecture section that:

- explains each flow in plain language first
- explains the actual code/data path second
- keeps provenance visible
- avoids claiming more than the code and local sources support

This is a documentation design only. It does not change product behavior.

## Why This Is Separate

The immediate task is not to redesign the lexicon product. The task is to
document the current product truth in a form that two different audiences can
both use.

That needs its own design because:

- audience split affects page structure
- provenance claims need discipline
- optional Wright text enrichment must not be presented as a critical path
- user-facing docs should replace the current architecture section cleanly

## Locked Decisions

- Published docs target is `doc/source/architecture/`
- The architecture set will have four pages:
  - `index.rst`
  - `dictionary.rst`
  - `morphology.rst`
  - `lexicon.rst`
- The architecture set will use one concept stack with two reading depths
  rather than separate scholar and engineer doc trees
- Each flow page will mirror the same core section pattern, followed by
  explicitly named flow-specific extra sections
- Claims about current product behavior must follow explicit evidence
  precedence:
  - current code paths first
  - current CLI surfaces second
  - checked-in prose/docs last
- Uncertain provenance must be marked explicitly as uncertain
- The landing page will include:
  - one shared system map
  - one provenance matrix
  - one sink matrix
- `wright_sections.section_text` must be documented as optional enrichment, not
  as part of the critical build path
- On the lexicon page, morphology classification and Wright excerpt lookup must
  be separate subsections
- The morphology page will include a brief related-work section, not a full
  literature review

## Primary Audience Model

Each page must serve two readers in sequence:

1. scholar or translator
2. engineer or computational linguist

The page should not fork into two independent documents. Instead, each page
should present:

- a plain-language explanation of what the flow does, what sources it depends
  on, and what comes out
- then a concrete explanation of commands, classes, collaborators, tables, and
  process flow

Reason:

- one shared vocabulary lowers drift
- both audiences can anchor on the same concepts
- engineers still get enough code detail to enter the implementation quickly

## File Layout

Target files:

- `doc/source/architecture/index.rst`
- `doc/source/architecture/dictionary.rst`
- `doc/source/architecture/morphology.rst`
- `doc/source/architecture/lexicon.rst`

Current `morphology_refactor_spec.rst` and
`morphology_refactor_baseline.rst` should leave the user-facing architecture
navigation. They may remain on disk if still useful, but they are not part of
the replacement architecture stack and do not belong in the user-facing
architecture toctree.

## Shared Page Template

Each flow page should mirror this core structure:

1. `What This Flow Does`
2. `For Scholars and Translators`
3. `Sources, Provenance, and Limits`
4. `Process Flow`
5. `For Engineers`
6. `Data Read and Data Written`
7. `Sharp Edges and Non-Goals`

After those seven shared sections, each page must add these exact
flow-specific sections:

- dictionary:
  - `Parsing and Editorial Merge`
- morphology:
  - `Optional Wright Section Ingest`
  - `Related Work and Alternatives`
- lexicon:
  - `Morphology Classification`
  - `Optional Wright Excerpt Lookup`

## Landing Page Design

`doc/source/architecture/index.rst` should do four jobs.

### 1. Orient the reader

Give a short explanation of how the three flows relate:

- dictionary turns Bosworth-Toller source into `bt_*` tables
- morphology turns Tichý-derived lemma data into `forms` plus morph-class data
- lexicon builds a derived browse read model from dictionary plus morphology

### 2. Show shared system flow

Include one system-level flow visualization that distinguishes:

- critical build paths
- optional enrichment paths

The diagram must not place `wright_sections.section_text` on the direct build
path for dictionary, morphology, or lexicon build.

Current docs configuration in `doc/source/conf.py` does not show Mermaid
support. Therefore the default should be a text-first schematic or equivalent
plain reStructuredText presentation. In detail:

- implementation should use a plain reStructuredText table, enumerated flow, or
  simple textual schematic by default
- if the existing docs build already supports Mermaid indirectly, Mermaid may be
  used instead
- enabling new Sphinx diagram tooling is out of scope for this docs rewrite

### 3. Show provenance matrix

One table covering:

- source artifact
- upstream provenance
- checked-in local file
- which flow uses it
- role in that flow
- certainty note when provenance is not fully established

Initial rows should cover at least:

- `data/oe_bt.txt`
- `data/oe_bosworthtoller.txt.bz2`
- Bosworth-Toller bibliographic source
- `wyrdcraeft/etc/morphology/manual_forms.txt`
- `wyrdcraeft/etc/morphology/dict_adj-vb-part-num-adv-noun.txt`
- `wyrdcraeft/etc/morphology/para_vb.txt`
- `wyrdcraeft/etc/morphology/prefixes.txt`
- `wyrdcraeft/etc/morphology/wright_paradigms.json`
- `wyrdcraeft/etc/morphology/wright-morphology-fixture.schema.json`
- `data/sources/wright.md`

### 4. Show sink matrix

One table covering:

- artifact or table family written
- producing command
- main code writer
- consuming command or UI
- role in downstream flow

Initial rows should cover at least:

- `bt_entries`, `bt_senses`, `bt_variants`
- `forms`
- morph catalog tables
- `lemma_morph_classes`
- `wright_sections.section_text`
- `lexicon_entries`, `lexicon_forms`, `lexicon_search_keys`,
  `lexicon_build_meta`

## Dictionary Page Design

The dictionary page should explain:

- Bosworth-Toller source text as input
- parsing, sense segmentation, and editorial merge as the core transformation
- dictionary build as a distinct workflow, even though it writes into the
  canonical DB
- `BTIndexPipeline` as the main orchestrator
- `BTLineParser`, `BTSenseSegmenter`, and `BTEditorialMerger` as the key
  collaborators
- `BTQueryService` as the main lookup-side reader

Scholar depth should emphasize:

- that this is a structured index over Bosworth-Toller source text
- that parser/merge choices shape how entries and senses become browsable
- that the LLM repair pass is optional and warning-scoped, not the primary
  parsing path

Engineer depth should emphasize:

- `wyrdcraeft dictionary build`
- `wyrdcraeft dictionary lookup`
- which `bt_*` tables are written
- required dependency on existing canonical DB/forms when using normal build

## Morphology Page Design

The morphology page should explain:

- bundled Tichý-derived source files as the main generator inputs
- paradigm assignment and staged form generation as the core transformation
- Wright morph catalog seeding and lemma-class assignment as part of build
- Wright section text ingest as a separate optional command

Engineer depth should anchor on:

- `wyrdcraeft morphology build`
- `GeneratorSession`
- paradigm assignment helpers
- generation dispatch functions
- `MorphologyCatalogLoader.ensure_seeded()`
- `LemmaMorphClassAssigner.assign_all()`
- `MorphologyQueryService`

The page must explicitly distinguish:

- critical build path:
  - load source files
  - normalize/process lemmas
  - assign paradigms
  - seed catalog
  - assign lemma classes
  - emit `forms`
- optional enrichment path:
  - `wyrdcraeft morphology ingest-wright-text`
  - update `wright_sections.section_text`

Related-work subsection should stay brief:

- note dependence on Tichý paper and upstream Perl/data work
- note that `wyrdcraeft` is one practical Old English morphology implementation
  rather than a survey of all OE morphology efforts
- optionally note future room for comparison with other OE morphology projects
  without claiming current integration

## Lexicon Page Design

The lexicon page should explain:

- lexicon as a derived read model over existing dictionary and morphology data
- `lexicon build` as a rebuild of `lexicon_*` rows, not a regeneration of
  dictionary or morphology source data
- browse/search as the user-facing combined surface

Engineer depth should anchor on:

- `wyrdcraeft lexicon build`
- `wyrdcraeft lexicon browse`
- `rebuild_lexicon()`
- `LexiconBuilder`
- `LexiconQueryService`

The page must keep these subsections separate:

### Morphology Classification

- explain that browse can show morph-class information through catalog-backed
  lookup
- explain that this depends on `lemma_morph_classes` and catalog tables

### Optional Wright Excerpt Lookup

- explain that stored Wright section text is only used when a user asks to read
  a cited Wright section from browse
- explain that this depends on prior `morphology ingest-wright-text`
- explain that missing section text does not block lexicon build or browse

## Evidence Rules

Every page must separate three kinds of claims.

### 1. As built in `wyrdcraeft`

Allowed evidence:

- current code paths
- current CLI help and entrypoints
- checked-in data files
- checked-in docs

These claims should use concrete references to:

- commands
- classes
- modules
- tables
- local data artifacts

When sources disagree about current behavior, use this precedence order:

1. code paths
2. current CLI surfaces
3. checked-in prose/docs

Checked-in prose may describe intent, prior behavior, or stale design state. It
must not override current code when documenting the product as built.

### 2. Upstream provenance

Allowed evidence:

- bibliographic citations supplied by the user and present in local docs/specs
- checked-in provenance notes
- local source files whose names or content support the claim

Where provenance is not fully proven by repository evidence, wording must stay
careful.

Example style:

- `data/oe_bt.txt` appears to derive from ...

Not:

- `data/oe_bt.txt` was definitely extracted from ...

### 3. Optional or non-critical behavior

Optional enrichments must be marked clearly as optional, especially:

- Wright section text ingest
- Wright excerpt display in browse
- dictionary LLM repair pass

## Diagram Rules

Mermaid diagrams are allowed where they reduce ambiguity, but they are not
required.

Use them for:

- whole-system flow on landing page
- per-flow process diagrams when the transformation is easier to see than read

If current docs tooling cannot render Mermaid without new configuration, use a
text-first fallback instead. The architecture rewrite should remain a docs
content task, not a docs-build-tooling task.

Do not use them when they blur optional and critical paths together.

Optional enrichment should be shown with visibly separate edges or lanes.

## Non-Goals

This design does not commit work for:

- changing dictionary parsing behavior
- changing morphology generation logic
- changing lexicon ranking/join logic
- adding new source data
- building a full scholarly literature review
- documenting every helper function in the implementation
- splitting docs into separate scholar and engineer trees

## Acceptance Criteria

This design is satisfied when all of these are true:

- `doc/source/architecture/` contains four user-facing pages for index,
  dictionary, morphology, and lexicon
- the landing page includes a system map, provenance matrix, and sink matrix
- each flow page follows the same mirrored two-depth structure
- scholar-facing sections explain sources, transformations, outputs, and limits
  in plain language
- engineer-facing sections identify the main commands, orchestrators,
  collaborators, and data boundaries without dropping into exhaustive helper
  documentation
- optional Wright excerpt lookup is documented as optional enrichment rather
  than critical build path
- all current-behavior claims are supported by repository evidence
- uncertain provenance is labeled as uncertain

## Next Implementation Step

After this design is reviewed, implementation should:

1. replace `doc/source/architecture/index.rst` navigation
2. add `dictionary.rst`, `morphology.rst`, and `lexicon.rst`
3. remove the current refactor-specific pages from user-facing architecture
   navigation only; they do not need relocation or rewrite in this task
4. build docs and correct only the references or rendering issues introduced by
   the new architecture pages or their direct navigation changes
