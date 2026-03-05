from __future__ import annotations

import argparse
import sys
from pathlib import Path

from wyrdcraeft.services.ocr import (
    DEFAULT_OCR_LANG,
    DEFAULT_OVERSAMPLE_DPI,
    DEFAULT_TESSERACT_PSM,
    OldEnglishOCRConfig,
    run_old_english_ocr_pipeline,
)
from wyrdcraeft.services.ocr_proxy.config import DEFAULT_UPSTREAM_BASE_URL


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the OCR pipeline script."""
    parser = argparse.ArgumentParser(
        description=(
            "Run olmocr + text extraction + deterministic normalization for Old "
            "English PDFs."
        )
    )
    parser.add_argument(
        "--input-pdf",
        required=True,
        type=Path,
        help="Path to input PDF.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=(
            "Directory for outputs. Default is data/ocr/<input-stem> under "
            "repo root."
        ),
    )
    parser.add_argument(
        "--pages",
        default=None,
        help=(
            "Legacy option not supported in olmocr mode (kept for compatibility)."
        ),
    )
    parser.add_argument(
        "--lang",
        default=DEFAULT_OCR_LANG,
        help=f"Legacy option ignored in olmocr mode (default: {DEFAULT_OCR_LANG}).",
    )
    parser.add_argument(
        "--tesseract-psm",
        type=int,
        default=DEFAULT_TESSERACT_PSM,
        help=(
            "Legacy option ignored in olmocr mode "
            f"(default: {DEFAULT_TESSERACT_PSM})."
        ),
    )
    parser.add_argument(
        "--oversample-dpi",
        type=int,
        default=DEFAULT_OVERSAMPLE_DPI,
        help=(
            "Legacy option ignored in olmocr mode "
            f"(default: {DEFAULT_OVERSAMPLE_DPI})."
        ),
    )
    parser.add_argument(
        "--skip-ocr",
        action="store_true",
        help="Skip olmocr execution and reuse existing workspace markdown output.",
    )
    parser.add_argument(
        "--rules-file",
        type=Path,
        default=Path("data/ocr/rules/old_english_safe.tsv"),
        help="Regex correction rules file (TSV).",
    )
    parser.add_argument(
        "--wordlist-file",
        type=Path,
        default=Path("data/ocr/wordlists/old_english_seed.txt"),
        help="Seed wordlist for unknown-token report.",
    )
    parser.add_argument(
        "--upstream-base-url",
        default=DEFAULT_UPSTREAM_BASE_URL,
        help=(
            "Upstream OpenAI-compatible base URL used by the managed proxy "
            f"(default: {DEFAULT_UPSTREAM_BASE_URL})."
        ),
    )
    return parser.parse_args()


def main() -> int:
    """
    Run the Old English OCR pipeline end to end.

    Returns:
        Process exit code (``0`` for success, ``1`` for failure).

    """
    args = _parse_args()
    config = OldEnglishOCRConfig(
        input_pdf=args.input_pdf,
        output_dir=args.output_dir,
        pages=args.pages,
        lang=args.lang,
        tesseract_psm=args.tesseract_psm,
        oversample_dpi=args.oversample_dpi,
        skip_ocr=args.skip_ocr,
        rules_file=args.rules_file,
        wordlist_file=args.wordlist_file,
        upstream_base_url=args.upstream_base_url,
    )

    try:
        output = run_old_english_ocr_pipeline(config)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print("OCR pipeline complete.")
    print(f"Input PDF: {output.input_pdf}")
    print(f"Output directory: {output.output_dir}")
    print(f"Raw text: {output.raw_text_path}")
    print(f"Normalized text: {output.normalized_text_path}")
    print(f"Unknown token report: {output.unknown_tokens_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
