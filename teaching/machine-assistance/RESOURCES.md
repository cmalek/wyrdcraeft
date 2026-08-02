# Machine Assistance For Old English Work Resources

## Knowledge

- [AllenAI `olmocr` repository](https://github.com/allenai/olmocr)
  Primary operational reference for the OCR engine used in this repo. Use for: real CLI behavior, workspace artifacts, server mode, and deployment patterns.

- [Poznanski et al., "olmOCR: Unlocking Trillions of Tokens in PDFs with Vision Language Models"](https://arxiv.org/abs/2502.18443)
  Primary paper for the model and pipeline philosophy behind `olmocr`. Use for: why it is strong on reading order, tables, equations, and hard PDF layouts.

- [Wyrdcraeft OCR context](/Users/cmalek/src/workspace/wyrdcraeft/docs/context/ocr.md)
  The local truth for how this repo divides literary OCR, BT witness preparation, proxy behavior, and sharp edges. Use for: understanding what commands and artifacts already exist here.

- [Wyrdcraeft runbook: Old English OCR Pipeline](/Users/cmalek/src/workspace/wyrdcraeft/doc/source/runbook/old_english_ocr_pipeline.rst)
  Concrete local workflow for `wyrdcraeft ocr old-english`, including quality metrics and benchmarking. Use for: the current literary-PDF path and its acceptance gates.

- [Wyrdcraeft runbook: BT Dictionary Structuring Workflow](/Users/cmalek/src/workspace/wyrdcraeft/doc/source/runbook/bt_dictionary_structuring_workflow.rst)
  Concrete local workflow for witness-first structured data. Use for: how to preserve raw evidence, overlays, and normalized output separately.

- [Tesseract documentation](https://tesseract-ocr.github.io/tessdoc/FAQ.html)
  Official reference for low-level OCR output formats such as plain text, hOCR, TSV, PDF, ALTO, and PAGE-related tooling. Use for: layout-bearing fallback artifacts and debugging when `olmocr` output needs extra evidence.

- [Kanerva et al., "OCR Error Post-Correction with LLMs in Historical Documents: No Free Lunches"](https://arxiv.org/abs/2502.01205)
  Useful corrective against overconfidence in fully automatic post-correction. Use for: understanding where LLM cleanup helps and where it can over-correct or hallucinate.

- [HIPE-OCRepair 2026 competition report](https://arxiv.org/abs/2607.08143)
  Recent evaluation of LLM-assisted OCR post-correction on historical documents. Use for: what "minimal human involvement" can realistically mean in practice and why evaluation still matters.

## Wisdom (Communities)

- [OCR-D](https://ocr-d.de/en/)
  High-signal digital-humanities OCR ecosystem. Use for: historical OCR workflow patterns, layout standards, and tool comparisons.

- [r/MachineLearning](https://www.reddit.com/r/MachineLearning/)
  Broad ML community with mixed quality. Use for: tracking relevant papers and tooling announcements, not for relying on every workflow claim.

## Gaps

- I do not yet have one stable open-access reference focused specifically on OCR and post-correction for philological dictionaries with heavy diacritics and mixed tables.
- I should add stronger resources on provenance-preserving table extraction and structured export formats for scholarly text.
