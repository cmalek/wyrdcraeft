.. _overview__bt_ocr_witness_preparation_method:

BT OCR Witness Preparation — Method
===================================

This page documents the architecture, artifacts, rationale, validation
methodology, and reproducibility contract for
``wyrdcraeft.services.ocr.bt_witness_prep``.

For the short overview and scope boundaries, see
:doc:`bt_ocr_witness_preparation`.

Architecture
------------

The package is organized as small, stateless collaborators orchestrated by
``BTWitnessPrepPipeline``. The module-level entrypoint ``prepare_pages`` builds
the default pipeline and returns ``BTWitnessPrepRun``.

.. mermaid::

   flowchart TB
       subgraph input [Input]
           SRC["source_dir/*.jp2"]
           CFG["BTWitnessPrepInput"]
       end

       subgraph pipeline [BTWitnessPrepPipeline]
           E["BTSourcePageEnumerator"]
           P["BTPagePreprocessor"]
           T["BTPageTiler"]
           Q["BTTileQualityScorer"]
           M["BTWitnessManifestWriter"]
           A["BTAnchorSeedBuilder / Writer"]
       end

       subgraph output [Output workspace]
           PG["pages/*.png"]
           TL["tiles/*.png"]
           MJ["manifests/{pages,tiles}.jsonl"]
           AN["anchors/anchor_seeds.jsonl"]
       end

       SRC --> E
       CFG --> E
       E --> P --> T --> Q
       P --> PG
       T --> TL
       Q --> M
       Q --> A
       M --> MJ
       A --> AN

Collaborator responsibilities:

- **``BTSourcePageEnumerator``** — stable filename order; records width/height
  and ``page_id`` derived from the JP2 stem
- **``BTPagePreprocessor``** — conservative margin crop, mild background
  normalization, grayscale export, optional unsharp mask; deskew is ``noop`` in
  this slice
- **``BTPageTiler``** — four-tile split for standard pages; explicit fallback
  for non-standard geometry
- **``BTTileQualityScorer``** — deterministic readability metrics on ``ready``
  tiles only
- **``BTWitnessManifestWriter``** — JSONL provenance for pages and tiles
- **``BTAnchorSeedBuilder``** — one ``column_half_tile`` seed per tile for
  downstream page/region/line anchoring

End-to-end process
------------------

.. mermaid::

   sequenceDiagram
       participant Caller
       participant Prep as prepare_pages
       participant Pipe as BTWitnessPrepPipeline
       participant Disk as output_dir

       Caller->>Prep: BTWitnessPrepInput
       Prep->>Pipe: prepare(input)
       loop each JP2 page
           Pipe->>Pipe: enumerate → preprocess
           alt standard two-column layout
               Pipe->>Pipe: 4 tiles + overlap links
               Pipe->>Pipe: quality score ready tiles
           else non-standard layout
               Pipe->>Pipe: whole-page fallback tile
           end
       end
       Pipe->>Disk: pages/, tiles/, manifests/, anchors/
       Pipe-->>Caller: BTWitnessPrepRun

Artifact Model
--------------

Every emitted record is provenance-first. Identifiers are stable across reruns
when source filenames and recipe ids are unchanged.

Page identifiers
~~~~~~~~~~~~~~~~

``page_id`` is the lowercase JP2 filename stem with spaces replaced by hyphens.
Example: ``BT 0002.jp2`` → ``bt-0002``.

Tile identifiers
~~~~~~~~~~~~~~~~

Standard tiles use ``{page_id}:col-{column}-part-{part}`` where column and part
are one-based. Example: ``bt-0002:col-1-part-2`` is the left column lower half.

Fallback tiles use ``{page_id}:whole-page``.

Manifest rows
~~~~~~~~~~~~~

``manifests/pages.jsonl`` — one ``BTPreprocessedPage`` per source page:

- original ``source_path``
- prepared ``image_path`` under ``pages/``
- ``crop_box``, dimensions, ``recipe_id``, ``status``

``manifests/tiles.jsonl`` — one ``BTTile`` per OCR region:

- ``tile_id``, ``column``, ``part``, ``crop_box``, ``image_path``
- ``overlap_px`` and ``overlaps_tile_ids`` for vertically adjacent halves
- nested ``quality`` object with metric scores and guardrail flags

``anchors/anchor_seeds.jsonl`` — one ``BTAnchorSeed`` per tile:

- ``region_type`` = ``column_half_tile``
- ``parent_region_id`` = page id
- ``crop_box`` copied from the tile
- placeholder ``line_number`` / ``line_text`` fields reserved for later
  line-level anchoring inside case bundles

Why Whole-Page OCR Is Insufficient
----------------------------------

Raw whole-page OCR on Bosworth-Toller scans fails in predictable ways that block
witness-first dictionary work:

- **Two-column bleed.** Dictionary pages place dense columns close to the
  midline. Whole-page models read across the gutter, merging headwords,
  attestations, and cross-column noise into one transcript.
- **Vertical compression.** A full page packs many small lines into one image.
  Vision OCR downscales detail; macrons, thorn/eth, and abbreviation marks
  collapse or swap.
- **Uneven signal across the page.** Headers, shadows, and binding curvature
  dominate some regions while others stay sharp. One global page treatment
  cannot optimize all regions.
- **No alignment scaffold.** Whole-page text alone does not give page/region
  coordinates that case bundles need to compare witnesses for one entry.

Witness preparation therefore produces **smaller, column-aware tiles** with
documented crop geometry and quality scores, so OCR runs on regions sized for
dictionary microstructure rather than on an undifferentiated page raster.

Why Witness-First Artifacts Matter
----------------------------------

This slice follows ADR 0004 and ADR 0005: parsing starts from a **lossless
source-grounded** layer with **multiple witnesses**, not from a single OCR pass
into final dictionary rows.

Prepared artifacts support that model because they:

- keep **scan provenance** attached to every page and tile row
- separate **image preparation** from **text interpretation**
- emit **anchor seeds** aligned to the page-region-line scaffold described in
  ``CONTEXT.md``
- travel as **shareable structured data** (JSONL + PNG) independent of SQLite or
  the wyrdcraeft runtime

OCR output produced from prepared tiles is still a **source witness**. It must
be compared against GLP corrected text, existing ``oe_bt.txt`` lines, and other
witnesses inside a case bundle before any normalized structure is treated as
derived fact.

Preprocessing Rationale
-----------------------

Default recipe id: ``bt-two-column-v1`` via
``BTPreprocessRecipe.conservative_default``.

Design choices:

- **Conservative margin crop** removes scanner bed background using edge
  luminance thresholds with a maximum removable fraction per edge. The goal is
  to drop blank margins without eating dictionary text near the binding.
- **Deskew noop** preserves source geometry exactly in this slice. Aggressive
  deskew risks shearing small diacritics before OCR sees them.
- **Mild background normalization and grayscale export** stabilize stroke
  contrast for both quality scoring and downstream olmocr input.
- **Optional unsharp mask** improves edge clarity for focus scoring without
  inventing ink.

Preprocessing writes one full-page PNG per source JP2 under ``pages/``. Tiling
always reads from the preprocessed page image, not the raw JP2, so crop boxes
in manifests refer to a consistent coordinate space.

Tiling Rationale
----------------

Standard Bosworth-Toller dictionary pages use a **fixed four-tile contract**:

.. code-block:: text

    +-------------------+-------------------+
    | col-1-part-1      | col-2-part-1    |
    | (upper left)      | (upper right)     |
    +-------------------+-------------------+
    | col-1-part-2      | col-2-part-2    |
    | (lower left)      | (lower right)     |
    +-------------------+-------------------+

Parameters in ``BTTilingConfig.standard_two_column()``:

- **Midline gutter** — ``column_gutter_px`` inset so column tiles do not cross
  into the neighboring column
- **Vertical overlap** — ``overlap_px`` shared between upper and lower halves so
  lines sitting on the horizontal midline appear intact in at least one tile
- **Layout guardrails** — minimum width/height and aspect-ratio bounds before
  four-tile splitting is allowed

Fallback behavior (never silent):

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Status
     - Meaning
   * - ``fallback_whole_page_only``
     - Page is too small for column or upper/lower splits
   * - ``unsupported_layout``
     - Aspect ratio or gutter geometry fails the two-column contract
   * - inherited non-``ready`` page status
     - Preprocessing marked the page non-standard; tiler preserves that status

Fallback pages emit one ``whole-page`` tile with ``quality.status = fallback``
and the explicit status recorded in ``quality.notes``.

Tile Quality Metrics
--------------------

``BTTileQualityScorer`` computes deterministic scores on ``0.0``–``1.0`` where
higher is better. Only tiles with ``quality.status = ready`` are scored during
``prepare_pages``.

.. list-table::
   :header-rows: 1
   :widths: 28 12 60

   * - Metric
     - Weight
     - What it detects
   * - ``stroke_contrast_score``
     - 0.30
     - Robust grayscale spread; collapsed contrast often precedes diacritic loss
   * - ``focus_score``
     - 0.20
     - Laplacian variance; blur smears punctuation-sized strokes
   * - ``small_component_preservation_score``
     - 0.20
     - Count of punctuation-sized connected ink components (area 1–16 px)
   * - ``line_separability_score``
     - 0.15
     - Horizontal projection rhythm; fused lines confuse OCR line breaks
   * - ``column_contamination_score``
     - 0.10
     - Ink density in the gutter-adjacent band of each column tile
   * - ``margin_clipping_score``
     - 0.05
     - Ink touching tile borders after crop

Composite score
~~~~~~~~~~~~~~~

``composite_score`` is the weighted sum of the metrics above.

Small-component guardrail
~~~~~~~~~~~~~~~~~~~~~~~~~

When ``small_component_preservation_score`` falls below **0.35**, the scorer:

- sets ``small_component_guardrail_failed = true``
- caps ``composite_score`` at **0.55**
- appends a note: ``small component preservation below guardrail threshold``

This guardrail exists because aggressive crop or normalization can erase
macrons, abbreviation points, and thorn/eth marks that remain visible to a human
reviewer. Stage B validation treats any guardrail failure as an automatic recipe
rejection even when aggregate CER looks improved.

Why Tile Quality Metrics Exist
------------------------------

Quality metrics serve three research needs:

1. **Explainability** — when OCR disagrees with a curated witness, manifests
   show whether the tile was clipped, contaminated, or lost small components
2. **Recipe comparison** — Stage B reads guardrail flags from ``tiles.jsonl`` when
   ranking preprocessing recipes
3. **Witness review** — case-bundle reviewers can prioritize re-scan or manual
   correction for low-composite tiles instead of trusting bad OCR blindly

Validation Methodology (Stage B)
--------------------------------

Stage B lives outside the core ``prepare_pages`` loop. It benchmarks OCR text
produced from prepared tiles against **raw whole-page OCR baselines** on a fixed
sample.

Fixed validation sample
~~~~~~~~~~~~~~~~~~~~~~~

Manifest:
``tests/fixtures/ocr/bt_witness_prep/validation_manifest.json``

Five pages covering:

- ``standard_dense`` — typical two-column dictionary density
- ``italics_abbreviations`` — mixed typography and abbreviation marks
- ``background_shadow`` — difficult background (witness text optional)

Curated comparison transcripts live under
``tests/fixtures/ocr/bt_witness_prep/transcriptions/``.

Benchmark driver
~~~~~~~~~~~~~~~~

``scripts/ocr/benchmark_bt_witness_prep.py``:

1. optionally runs ``prepare_pages`` on a JP2 source directory
2. OCRs baseline images (whole preprocessed pages) and candidate images
   (prepared tiles, concatenated or per-tile per script configuration)
3. loads comparison witnesses via ``validation.py``
4. computes per-page and aggregate metrics
5. emits a JSON summary with pass/fail

Scoring helpers in ``validation.py``:

- ``diacritic_sensitive_cer`` — character error rate on NFKC-normalized text
  with diacritics preserved
- ``historical_char_exact_match_rate`` — exact token match rate for tokens
  containing historical graphemes (thorn, eth, macrons, etc.)
- ``relative_cer_improvement`` — relative reduction from baseline to candidate
- ``recipe_passes_stage_b`` — encodes the pass rule

Pass rule
~~~~~~~~~

A candidate recipe passes when **both** are true:

- ``relative_cer_improvement >= 0.10`` (at least **10% relative** improvement in
  mean diacritic-sensitive CER versus the raw whole-page baseline across
  witnessed pages)
- ``small_component_guardrail_failed`` is **false** for every page in the run

Human-readable form (also stored as ``pass_rule`` on benchmark output):

   pass when relative diacritic-sensitive CER improvement is at least 10%
   versus the raw whole-page baseline and no catastrophic small-component
   guardrail failures are recorded

Reproducibility
---------------

Another researcher can reproduce witness preparation and Stage B validation
without private tooling.

Prerequisites
~~~~~~~~~~~~~

- Python environment from ``uv sync --dev``
- JP2 source pages in one flat directory (Internet Archive Bosworth-Toller scan
  naming is typical)
- For live Stage B OCR: olmocr stack documented in
  :doc:`/runbook/old_english_ocr_pipeline`

Step 1 — Prepare witnesses
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pathlib import Path

    from wyrdcraeft.services.ocr.bt_witness_prep import (
        BTWitnessPrepInput,
        prepare_pages,
    )

    output_dir = Path("data/ocr/bt_witness_prep/run-001")
    run = prepare_pages(
        BTWitnessPrepInput(
            source_dir=Path("path/to/jp2-pages"),
            output_dir=output_dir,
            recipe_id="bt-two-column-v1",
        )
    )

    print(f"pages: {len(run.preprocessed_pages)}")
    print(f"tiles: {len(run.tiles)}")
    print(f"anchors: {len(run.anchor_seeds)}")

Inspect ``output_dir``:

- confirm ``manifests/pages.jsonl`` and ``manifests/tiles.jsonl`` row counts
- spot-check ``quality.composite_score`` and guardrail flags on difficult pages
- verify fallback pages report explicit statuses instead of four-tile geometry

Step 2 — Run OCR on prepared tiles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the olmocr pipeline (:doc:`/runbook/old_english_ocr_pipeline`) on tile
images under ``tiles/``, retaining markdown witnesses separately from any
normalized views. Treat markdown output as **markdown witness** material per
``CONTEXT.md``.

Step 3 — Stage B benchmark
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: shell

    .venv/bin/python scripts/ocr/benchmark_bt_witness_prep.py \
      --output /tmp/stage-b-summary.json \
      --recipe-id bt-two-column-v1 \
      --source-dir path/to/jp2-pages \
      --prepare-output-dir data/ocr/bt_witness_prep/run-001

Use ``--skip-ocr`` with ``--baseline-dir`` and ``--candidate-dir`` when
replaying stored OCR text for deterministic CI or offline review.

Step 4 — Compare against curated witnesses
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For witnessed validation pages, compare candidate OCR to transcription files
referenced in ``validation_manifest.json``. Report:

- diacritic-sensitive CER (lower is better)
- historical-character exact-match rate (higher is better)
- guardrail failures (must be zero to pass)

Expected outputs summary
~~~~~~~~~~~~~~~~~~~~~~~~

After Steps 1–3, expect:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Artifact
     - Expectation
   * - ``pages/*.png``
     - One conservative grayscale page image per JP2
   * - ``tiles/*.png``
     - Four tiles per standard page, or one whole-page fallback tile
   * - ``manifests/pages.jsonl``
     - Page-level provenance and layout status
   * - ``manifests/tiles.jsonl``
     - Tile geometry, overlap links, quality metrics
   * - ``anchors/anchor_seeds.jsonl``
     - Region seeds for case-bundle anchoring (geometry only in this slice)
   * - Stage B JSON summary
     - Aggregate CER, improvement ratio, pass/fail, per-page breakdown

Limits and Non-Goals
--------------------

This slice deliberately stops where downstream dictionary structuring begins.

Not in scope
~~~~~~~~~~~~

- parsing ``data/oe_bt.txt`` into dictionary rows
- automatic headword or sense extraction from OCR text
- populating ``data/bt_cases/*/entry.raw.yaml`` fragments
- line-level OCR or line-number assignment inside anchor seeds
- HOCR, ABBYY, or ``djvu.txt`` ingestion
- CLI command registration (library-first in this slice)
- claiming OCR transcripts as canonical dictionary truth

Downstream work
~~~~~~~~~~~~~~~

Prepared witnesses feed:

- witness YAML stubs and anchors in case bundles
- :doc:`/runbook/bt_dictionary_structuring_workflow` review steps
- future fragment extraction that preserves **typed source fragments** and
  **unclassified remainder** per ADR 0004

Claims this slice **does** make
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- JP2 scans can be transformed into reproducible, provenance-rich tile artifacts
- four-tile splitting with overlap is the default contract for standard
  two-column pages
- non-standard pages surface explicit fallback statuses
- tile quality metrics and Stage B guardrails catch preprocessing that destroys
  punctuation-sized historical characters
- a passing Stage B recipe improves diacritic-sensitive OCR relative to raw
  whole-page baseline on the fixed validation sample

Related Documentation
---------------------

- :doc:`bt_ocr_witness_preparation` — overview, scope, and workflow summary
- :doc:`/runbook/bt_dictionary_structuring_workflow` — case-bundle operator path
- :doc:`/runbook/old_english_ocr_pipeline` — olmocr execution details
- ``docs/adr/0004-bt-ocr-parsing-starts-with-lossless-source-grounded-ast.md``
- ``docs/adr/0005-bt-source-acquisition-uses-multi-witness-download-set.md``
- ``CONTEXT.md`` — glossary: source witness, page-region-line anchor, case
  bundle, markdown witness, adjudication overlay
