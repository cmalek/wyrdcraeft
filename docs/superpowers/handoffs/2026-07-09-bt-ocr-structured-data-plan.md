# BT OCR Structured Data Handoff

**Date:** 2026-07-09  
**Status:** design locked enough to prototype  
**Primary goal:** convert messy Bosworth-Toller OCR into shareable machine-readable structured data with minimal human review burden  
**Review goal:** review by exception, not months of line-by-line cleanup

---

## One-line direction

Do **not** try to parse `data/oe_bt.txt` straight into final dictionary rows. Build a **lossless, source-grounded, multi-witness intermediate layer** first, then normalize from that, and only ask a human to review the worst 5-10% of cases.

---

## Locked decisions

1. First product is a **lossless source-grounded AST**, not a direct final entry model.
2. **All source text must be accounted for** by ordered typed spans/fragments. No silent dropping.
3. Keep **all parts of the definition**, including **attestations**.
4. Start from a **span-tagging / grouping / tree-building pipeline**, not a one-shot tree parser.
5. Support **multiple witnesses** from the start, not only `oe_bt.txt`.
6. Correction workflow should be **fragment-level adjudication**, not whole-entry rewrite.
7. Preserve both:
   - entry-level source witnesses
   - fragment-level provenance
8. Review should be **witness-first** so the human can see raw source beside parse output.
9. Base transcription should be **diplomatic**, not normalized.
10. `olmOCR` Markdown is acceptable as a **witness format**, but not as canonical truth by itself.
11. Witness alignment should begin from **page/region/line anchors**, not headword anchors.
12. Corrections/history should be **append-only with lineage**, not mutable latest-state edits.
13. First implementation target is a **thin end-to-end slice**, not a broad rebuild.
14. First nasty prototype case is **`wesan`**.
15. First persistence layer is **file-first case bundles**, not SQLite.
16. Human overlays should be **YAML**.
17. Final output should remain **shareable with other engineers and researchers**.
18. To minimize user effort, use **confidence-adaptive fragments** and **review by exception**.
19. Risk ranking should combine:
   - witness disagreement
   - parser uncertainty
   - structural risk class

---

## What changed in the recommendation

The old implicit plan was too parser-first and too optimistic about clean input.

The current plan is:

1. Ingest raw source witnesses.
2. Convert each witness into typed spans with explicit uncertainty.
3. Align spans across witnesses by page/region/line anchors.
4. Build a lossless entry bundle from those spans.
5. Derive normalized structured output from the bundle.
6. Only send high-risk fragments to human review.

That keeps the machine honest and cuts down the amount of human cleanup.

---

## Best source inputs found so far

### Better digital text than local `oe_bt.txt`

- Germanic Lexicon Project Bosworth-Toller about page:
  [https://www.germanic-lexicon-project.org/texts/oe_bosworthtoller_about.html](https://www.germanic-lexicon-project.org/texts/oe_bosworthtoller_about.html)
  Notes:
  - says the old GLP page is superseded by the Charles University version
  - says there is a "better corrected version of the dictionary text"
  - offers full text download, page images, and abbreviation XML

- Main Bosworth-Toller site:
  [https://bosworthtoller.com/](https://bosworthtoller.com/)
  Notes:
  - data are free to use
  - site says custom database dumps may be available for researchers

### Clear scan / downloadable OCR witnesses

- Internet Archive main volume:
  [https://archive.org/details/anglosaxondictio00bosw](https://archive.org/details/anglosaxondictio00bosw)
  Notes:
  - downloadable `PDF`, `FULL TEXT`, `HOCR`, `ABBYY GZ`, JP2 page images
  - metadata shows `Ppi 500`
  - caveats mention inner-margin loss and skew

- Internet Archive supplement:
  [https://archive.org/details/anglosaxondictio00tolluoft](https://archive.org/details/anglosaxondictio00tolluoft)
  Notes:
  - downloadable `PDF`, `FULL TEXT`, `HOCR`, `ABBYY GZ`, JP2 page images
  - metadata shows `Ppi 300`
  - raw images likely better than degraded PDF for OCR

### Concrete source-acquisition table

| Priority | Exact URL | What to download | What it is for |
|---|---|---|---|
| 1 | [https://www.germanic-lexicon-project.org/txt/oe_bosworthtoller.txt](https://www.germanic-lexicon-project.org/txt/oe_bosworthtoller.txt) | `oe_bosworthtoller.txt` | Best first-pass corrected text witness to compare with local `oe_bt.txt`. |
| 1 | [https://www.germanic-lexicon-project.org/xml/oe_bosworthtoller/oebt_abbreviations.xml](https://www.germanic-lexicon-project.org/xml/oe_bosworthtoller/oebt_abbreviations.xml) | `oebt_abbreviations.xml` | Abbreviation expansion table for reference parsing, prefix cleanup, and fragment typing. |
| 1 | [https://archive.org/download/anglosaxondictio00bosw/anglosaxondictio00bosw_orig_jp2.tar](https://archive.org/download/anglosaxondictio00bosw/anglosaxondictio00bosw_orig_jp2.tar) | Main-volume original JP2 page images | Primary scan witness for running our own OCR on the 1898 main volume. Prefer over PDF. |
| 1 | [https://archive.org/download/anglosaxondictio00tolluoft/anglosaxondictio00tolluoft_raw_jp2.zip](https://archive.org/download/anglosaxondictio00tolluoft/anglosaxondictio00tolluoft_raw_jp2.zip) | Supplement raw JP2 page images | Primary scan witness for running our own OCR on the 1921 supplement. Prefer over PDF. |
| 2 | [https://archive.org/download/anglosaxondictio00bosw/anglosaxondictio00bosw_hocr.html](https://archive.org/download/anglosaxondictio00bosw/anglosaxondictio00bosw_hocr.html) | Main-volume HOCR | Layout-aware OCR witness for page/block/line anchors. |
| 2 | [https://archive.org/download/anglosaxondictio00tolluoft/anglosaxondictio00tolluoft_hocr.html](https://archive.org/download/anglosaxondictio00tolluoft/anglosaxondictio00tolluoft_hocr.html) | Supplement HOCR | Layout-aware OCR witness for supplement page/block/line anchors. |
| 2 | [https://archive.org/download/anglosaxondictio00bosw/anglosaxondictio00bosw_abbyy.gz](https://archive.org/download/anglosaxondictio00bosw/anglosaxondictio00bosw_abbyy.gz) | Main-volume ABBYY OCR | Extra machine witness for cross-checking `olmOCR`, HOCR, and IA full text. |
| 2 | [https://archive.org/download/anglosaxondictio00tolluoft/anglosaxondictio00tolluoft_abbyy.gz](https://archive.org/download/anglosaxondictio00tolluoft/anglosaxondictio00tolluoft_abbyy.gz) | Supplement ABBYY OCR | Extra machine witness for supplement cross-checking. |
| 4 | [https://archive.org/stream/anglosaxondictio00bosw/anglosaxondictio00bosw_djvu.txt](https://archive.org/stream/anglosaxondictio00bosw/anglosaxondictio00bosw_djvu.txt) | Main-volume IA full text | Fallback-only junky OCR/text witness for rough grep, coarse recall, and disagreement hints. Do not trust for spelling, structure, or citations. |
| 4 | [https://archive.org/stream/anglosaxondictio00tolluoft/anglosaxondictio00tolluoft_djvu.txt](https://archive.org/stream/anglosaxondictio00tolluoft/anglosaxondictio00tolluoft_djvu.txt) | Supplement IA full text | Fallback-only junky OCR/text witness for supplement rough recall and disagreement hints. |
| 3 | [https://archive.org/download/anglosaxondictio00bosw/anglosaxondictio00bosw.pdf](https://archive.org/download/anglosaxondictio00bosw/anglosaxondictio00bosw.pdf) | Main-volume PDF | Human browsing/reference only. Not first choice for OCR. |
| 3 | [https://archive.org/download/anglosaxondictio00tolluoft/anglosaxondictio00tolluoft.pdf](https://archive.org/download/anglosaxondictio00tolluoft/anglosaxondictio00tolluoft.pdf) | Supplement PDF | Human browsing/reference only. Not first choice for OCR. |
| 3 | [https://www.germanic-lexicon-project.org/html/oe_bosworthtoller/b0001.html](https://www.germanic-lexicon-project.org/html/oe_bosworthtoller/b0001.html) | Page-level corrected HTML example | Example corrected page witness for exact-page case bundles and spot checks. |
| 3 | [https://www.germanic-lexicon-project.org/png/oe_bosworthtoller/b0001.png](https://www.germanic-lexicon-project.org/png/oe_bosworthtoller/b0001.png) | Page-level PNG example | Example visual page witness for fragment adjudication and anchor debugging. |
| 4 | [https://www.germanic-lexicon-project.org/texts/oe_bosworthtoller_about.html](https://www.germanic-lexicon-project.org/texts/oe_bosworthtoller_about.html) | No file; landing page | Metadata page that links GLP downloads and notes the Charles University version has a better corrected text. |
| 4 | [https://bosworthtoller.com/](https://bosworthtoller.com/) | No direct public dump found | Current online structured witness and likely contact path for custom researcher dumps. |
| 4 | [https://bosworthtoller.com/search/advanced](https://bosworthtoller.com/search/advanced) | No file; search UI | Spot-check structure, examples, grammar fields, and scan linkage during adjudication. |

### First downloads to prioritize

1. `oe_bosworthtoller.txt`
2. `oebt_abbreviations.xml`
3. `anglosaxondictio00bosw_orig_jp2.tar`
4. `anglosaxondictio00tolluoft_raw_jp2.zip`
5. both IA `hocr.html` witnesses
6. both IA `abbyy.gz` witnesses

### Witness trust order

1. GLP corrected text
2. IA raw page images (`JP2`) plus our own OCR
3. IA `hocr.html` and `abbyy.gz`
4. IA `djvu.txt` only as fallback-only rough recall

---

## OCR recommendation

### Short version

Yes, `olmOCR` Markdown works for us, **as one witness**.

### Better practical stack

Use at least **two witness generators** for hard pages:

1. Existing source text witness:
   - local `data/oe_bt.txt`
   - GLP / CUNI corrected text if obtained
2. Scan-derived OCR witness:
   - `olmOCR`
3. Comparison OCR witness:
   - `Qwen2.5-VL`
   - or `PaddleOCR-VL`

### Why not trust one OCR model

BT is messy in ways OCR alone will not solve:

- erratic typography
- abbreviations
- gender / grammar prefixes that look like content
- addenda interleaved with main entries
- etymology formatting drift
- sense labels that are structurally meaningful but visually weak

So the win is not "find perfect OCR." The win is "keep multiple imperfect witnesses and adjudicate only the hard parts."

### Long-term best quality path

If this becomes more than a toy prototype, the highest-upside path is likely:

- good page images from IA / GLP
- a small BT ground-truth set
- fine-tuned **Kraken / eScriptorium** historical OCR

That is more work up front, but likely beats generic OCR on this kind of book.

### OCR/model references already checked

- `olmOCR` collection:
  [https://huggingface.co/collections/allenai/olmocr](https://huggingface.co/collections/allenai/olmocr)
- `olmOCR` paper:
  [https://arxiv.org/abs/2502.18443](https://arxiv.org/abs/2502.18443)
- `olmOCR 2` paper:
  [https://arxiv.org/abs/2510.19817](https://arxiv.org/abs/2510.19817)
- `Qwen2.5-VL`:
  [https://arxiv.org/abs/2502.13923](https://arxiv.org/abs/2502.13923)
- `PaddleOCR 3.0`:
  [https://arxiv.org/abs/2507.05595](https://arxiv.org/abs/2507.05595)
- `PaddleOCR-VL`:
  [https://arxiv.org/abs/2606.03264](https://arxiv.org/abs/2606.03264)
- `MonkeyOCR`:
  [https://arxiv.org/abs/2506.05218](https://arxiv.org/abs/2506.05218)
- `GutenOCR`:
  [https://arxiv.org/abs/2601.14490](https://arxiv.org/abs/2601.14490)

---

## Human-effort-minimizing strategy

The right tradeoff is **not** "human reviews nothing" and **not** "human reviews every entry."

The right tradeoff is:

1. Machine parses everything.
2. Machine emits a risk score per entry and per fragment.
3. Human only reviews the worst cases.
4. Human decisions become YAML overlays and gold examples.
5. The system gets cheaper over time because those overlays feed better heuristics and better prompts.

### Suggested target

- Human reviews top **5-10%** highest-risk entries.
- Remaining **90-95%** ship automatically with provenance.

That is the only plausible path if this is a fun side project rather than a full-time editorial job.

---

## AI assistance recommendation

Yes, use AI to reduce the human workload.

### Best split by tool

- **Local model**
  - cheap bulk triage
  - witness disagreement checks
  - risk scoring
  - coarse fragment labeling

- **Codex / Cursor**
  - build tooling
  - generate and refine parsers
  - draft YAML overlays for hard entries

- **ChatGPT / Codex / strong remote model**
  - hard-case reasoning
  - compare witnesses
  - explain probable structure
  - draft adjudications for the nastiest entries

### What AI should not do

Do not let a model silently rewrite the source into clean modernized structure with no provenance. That is exactly how we lose trust in the output.

---

## First real artifact to build

Build a **single case bundle** for `wesan`.

Why `wesan`:

- already known to be ugly
- has placeholder-like senses
- exposes whether we can keep attestations without faking clean semantics
- good stress test for provenance

---

## Proposed `wesan` case-bundle schema

Suggested root:

`data/bt_cases/wesan/`

Suggested files:

```text
data/bt_cases/wesan/
  manifest.yaml
  entry.raw.yaml
  entry.normalized.yaml
  adjudication.overlay.yaml
  review.md
  witnesses/
    oe_bt_txt.txt
    glp_corrected.txt
    olmocr_main.md
    ia_fulltext.txt
  anchors/
    main_volume_page_XXXX.yaml
  spans/
    oe_bt_txt.spans.yaml
    glp_corrected.spans.yaml
    olmocr_main.spans.yaml
    ia_fulltext.spans.yaml
  alignments/
    witness_alignment.yaml
  exports/
    entry.json
    entry.yaml
```

### File roles

- `manifest.yaml`
  - entry id
  - headword
  - volumes/pages
  - witness inventory
  - pipeline status
  - risk score

- `entry.raw.yaml`
  - lossless source-grounded AST
  - ordered typed fragments
  - per-fragment provenance
  - unresolved / uncertain fragments

- `entry.normalized.yaml`
  - normalized entry derived from `entry.raw.yaml`
  - senses, grammar, variants, etymology, attestations
  - nothing here should exist without a source fragment trail

- `adjudication.overlay.yaml`
  - append-only human or AI-reviewed corrections
  - explicit patch-like decisions, not replacement text blobs

- `review.md`
  - short witness-first reviewer surface
  - "what looks wrong and why"

### Minimal fragment type set

Start small:

- `headword`
- `pos`
- `gender`
- `variant`
- `sense_label`
- `definition_text`
- `attestation`
- `usage_marker`
- `etymology`
- `cross_reference`
- `editorial_addendum`
- `unclassified`

If we need more types later, add them later. Do not over-model v1.

---

## Very small raw-entry shape

The first raw shape can stay dumb as long as it is lossless:

```yaml
entry_id: bt-wesan-main
headword: wesan
source_witnesses:
  - witness_id: oe-bt-local
    kind: corrected_text
  - witness_id: ia-main-olmocr
    kind: markdown_ocr
fragments:
  - fragment_id: f001
    type: headword
    text: "wesan"
    provenance:
      witness_id: oe-bt-local
      anchor: { page: 123, line_start: 1, line_end: 1 }
  - fragment_id: f002
    type: sense_label
    text: "4."
    provenance:
      witness_id: oe-bt-local
      anchor: { page: 123, line_start: 20, line_end: 20 }
  - fragment_id: f003
    type: definition_text
    text: "with a predictive adjective or participle"
    provenance:
      witness_id: oe-bt-local
      anchor: { page: 123, line_start: 20, line_end: 20 }
  - fragment_id: f004
    type: attestation
    text: "..."
    provenance:
      witness_id: ia-main-olmocr
      anchor: { page: 123, region: "body-2", line_start: 22, line_end: 23 }
```

That is enough to start. Do not invent the whole ontology first.

---

## Normalized output rule

The normalized entry is allowed to be cleaner, but it must satisfy both:

1. every normalized field points back to source fragments
2. leftover raw text still exists somewhere explicit as `unclassified` or `unresolved`

No disappearing text.

---

## Suggested pipeline, minimal version

### Phase 0: Source acquisition

- pull the best available text witness
- pull scan/page-image witness
- generate one OCR Markdown witness
- store all witnesses verbatim

### Phase 1: Witness span tagging

- split witness text into ordered spans
- label obvious fragment types
- mark uncertainty instead of forcing structure

### Phase 2: Witness alignment

- align by page/region/line anchors first
- align headwords and repeated labels second

### Phase 3: Raw entry assembly

- build a lossless entry bundle
- preserve all unattached debris explicitly

### Phase 4: Normalization

- derive structured entry
- compute risk score
- emit review surface

### Phase 5: Review by exception

- only high-risk entries get adjudication overlays

---

## Immediate next build steps

1. Create the `wesan` case-bundle directory and empty YAML shells.
2. Populate it with:
   - local `oe_bt.txt` witness
   - one scan-derived witness
   - one OCR Markdown witness
3. Hand-tag a tiny fragment set for `wesan`.
4. Define the first `entry.raw.yaml` shape from that real case.
5. Only after that, write generic loader/export code.

This keeps us from building a fake architecture before touching the ugly data.

---

## Important implication for current parser code

Current `wyrdcraeft/services/dictionary/sense_segmenter.py` strips attestations with `BTAttestationStripper`.

That conflicts directly with this project goal.

So for this workflow, attestations must move from "noise to strip" to "typed fragments to preserve."

---

## Resume point

When work resumes, the next best move is:

1. write the concrete `wesan` bundle files
2. ingest available witnesses into that bundle
3. hand-tag one ugly slice
4. let that real slice dictate the first parser structures

If time is tight, skip UI. Plain files plus a tiny terminal or HTML review helper are enough.
