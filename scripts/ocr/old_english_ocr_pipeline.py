from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import unicodedata
from collections import Counter
from pathlib import Path

#: Default OCR language bundle for Tesseract via OCRmyPDF.
DEFAULT_OCR_LANG = "eng+lat"
#: Default Tesseract page segmentation mode for grammar-style text blocks.
DEFAULT_TESSERACT_PSM = 4
#: Default resolution used for force-OCR processing.
DEFAULT_OVERSAMPLE_DPI = 400
#: Token regex including common Old English graphemes.
TOKEN_REGEX = re.compile(r"[A-Za-zÆæÐðÞþŌōĀāĒēĪīȲȳǢǣ]+")


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the OCR pipeline script."""
    parser = argparse.ArgumentParser(
        description=(
            "Run OCR + text extraction + deterministic normalization for Old "
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
            "Optional OCR page range for OCRmyPDF, e.g. '1-20' or "
            "'194-220'."
        ),
    )
    parser.add_argument(
        "--lang",
        default=DEFAULT_OCR_LANG,
        help=f"OCR language bundle (default: {DEFAULT_OCR_LANG}).",
    )
    parser.add_argument(
        "--tesseract-psm",
        type=int,
        default=DEFAULT_TESSERACT_PSM,
        help=f"Tesseract page segmentation mode (default: {DEFAULT_TESSERACT_PSM}).",
    )
    parser.add_argument(
        "--oversample-dpi",
        type=int,
        default=DEFAULT_OVERSAMPLE_DPI,
        help=f"OCR oversample DPI (default: {DEFAULT_OVERSAMPLE_DPI}).",
    )
    parser.add_argument(
        "--skip-ocr",
        action="store_true",
        help="Skip OCRmyPDF and extract text directly from input PDF.",
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
    return parser.parse_args()


def _run_command(command: list[str]) -> None:
    """
    Run a subprocess command and raise on non-zero exit.

    Args:
        command: Command and args to execute.

    Raises:
        RuntimeError: If the command exits with non-zero status.

    """
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode == 0:
        return
    stderr = result.stderr.strip()
    stdout = result.stdout.strip()
    message = stderr or stdout or "unknown subprocess error"
    raise RuntimeError(f"Command failed: {' '.join(command)}\n{message}")


def _require_tool(binary: str) -> None:
    """
    Validate that an external command is available on ``PATH``.

    Args:
        binary: Executable name to check.

    Raises:
        RuntimeError: If executable is not found.

    """
    if shutil.which(binary):
        return
    raise RuntimeError(
        f"Required tool '{binary}' not found. Install it and rerun."
    )


def _extract_text_with_ghostscript(pdf_path: Path, output_path: Path) -> None:
    """
    Extract machine-readable text from a PDF using Ghostscript txtwrite.

    Args:
        pdf_path: PDF source path.
        output_path: Destination plain-text file path.

    """
    command = [
        "gs",
        "-q",
        "-sDEVICE=txtwrite",
        "-o",
        str(output_path),
        str(pdf_path),
    ]
    _run_command(command)


def _run_ocrmypdf(
    *,
    input_pdf: Path,
    output_pdf: Path,
    lang: str,
    tesseract_psm: int,
    oversample_dpi: int,
    pages: str | None,
) -> None:
    """
    Run OCRmyPDF with settings tuned for historical grammar scans.

    Args:
        input_pdf: Source PDF path.
        output_pdf: OCR output PDF path.
        lang: OCR language bundle.
        tesseract_psm: Tesseract page segmentation mode.
        oversample_dpi: OCR oversample resolution.
        pages: Optional page-range string.

    """
    command = [
        "ocrmypdf",
        "--force-ocr",
        "--rotate-pages",
        "--deskew",
        "--clean",
        "--optimize",
        "0",
        "--oversample",
        str(oversample_dpi),
        "--tesseract-timeout",
        "180",
        "--tesseract-pagesegmode",
        str(tesseract_psm),
        "-l",
        lang,
    ]
    if pages:
        command.extend(["--pages", pages])
    command.extend([str(input_pdf), str(output_pdf)])
    _run_command(command)


def _load_regex_rules(path: Path) -> list[tuple[re.Pattern[str], str]]:
    """
    Load sequential regex substitution rules from a TSV file.

    Args:
        path: Rule file path with ``pattern<TAB>replacement`` rows.

    Returns:
        Ordered compiled regex/replacement pairs.

    Raises:
        RuntimeError: If the file contains malformed non-comment lines.

    """
    compiled: list[tuple[re.Pattern[str], str]] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            raise RuntimeError(
                f"Invalid rule line {line_number} in {path}: expected "
                "pattern<TAB>replacement."
            )
        pattern, replacement = parts[0], parts[1]
        compiled.append((re.compile(pattern), replacement))
    return compiled


def _apply_rules(text: str, rules: list[tuple[re.Pattern[str], str]]) -> str:
    """
    Apply regex correction rules in file order.

    Args:
        text: Raw extracted text.
        rules: Ordered compiled regex/replacement pairs.

    Returns:
        Corrected text after all substitutions.

    """
    corrected = text
    for pattern, replacement in rules:
        corrected = pattern.sub(replacement, corrected)
    return corrected


def _load_wordlist(path: Path) -> set[str]:
    """
    Load lowercase lexicon tokens from a newline-delimited file.

    Args:
        path: Wordlist path.

    Returns:
        Lowercased token set.

    """
    words = {
        line.strip().lower()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    return words


def _write_unknown_tokens_report(
    *,
    text: str,
    wordlist: set[str],
    report_path: Path,
) -> None:
    """
    Write a TSV frequency report of tokens missing from the seed wordlist.

    Args:
        text: Corrected OCR text.
        wordlist: Known lowercase token set.
        report_path: Destination TSV file path.

    """
    counter: Counter[str] = Counter()
    for token in TOKEN_REGEX.findall(text):
        normalized = token.lower()
        if len(normalized) <= 2:
            continue
        if normalized in wordlist:
            continue
        counter[normalized] += 1

    lines = ["token\tcount"]
    for token, count in counter.most_common():
        lines.append(f"{token}\t{count}")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _default_output_dir(input_pdf: Path) -> Path:
    """
    Build default output directory path for an input PDF.

    Args:
        input_pdf: Source PDF path.

    Returns:
        ``data/ocr/<pdf-stem>`` under repository root.

    """
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "data" / "ocr" / input_pdf.stem


def main() -> int:
    """
    Run the Old English OCR pipeline end to end.

    Returns:
        Process exit code (``0`` for success, ``1`` for failure).

    """
    args = _parse_args()
    input_pdf = args.input_pdf.resolve()
    if not input_pdf.exists():
        print(f"Input PDF not found: {input_pdf}", file=sys.stderr)
        return 1

    output_dir = (
        args.output_dir.resolve()
        if args.output_dir
        else _default_output_dir(input_pdf)
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    ocr_pdf = output_dir / "01_ocr.pdf"
    raw_text_path = output_dir / "02_raw.txt"
    normalized_text_path = output_dir / "03_normalized.txt"
    unknown_tokens_path = output_dir / "04_unknown_tokens.tsv"

    rules_file = args.rules_file.resolve()
    wordlist_file = args.wordlist_file.resolve()

    try:
        _require_tool("gs")
        if not args.skip_ocr:
            _require_tool("ocrmypdf")
            _run_ocrmypdf(
                input_pdf=input_pdf,
                output_pdf=ocr_pdf,
                lang=args.lang,
                tesseract_psm=args.tesseract_psm,
                oversample_dpi=args.oversample_dpi,
                pages=args.pages,
            )
            text_source_pdf = ocr_pdf
        else:
            text_source_pdf = input_pdf

        _extract_text_with_ghostscript(text_source_pdf, raw_text_path)
        raw_text = raw_text_path.read_text(encoding="utf-8")
        normalized_text = unicodedata.normalize("NFKC", raw_text)

        rules = _load_regex_rules(rules_file)
        normalized_text = _apply_rules(normalized_text, rules)
        normalized_text_path.write_text(normalized_text, encoding="utf-8")

        wordlist = _load_wordlist(wordlist_file)
        _write_unknown_tokens_report(
            text=normalized_text,
            wordlist=wordlist,
            report_path=unknown_tokens_path,
        )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print("OCR pipeline complete.")
    print(f"Input PDF: {input_pdf}")
    print(f"Output directory: {output_dir}")
    print(f"Raw text: {raw_text_path}")
    print(f"Normalized text: {normalized_text_path}")
    print(f"Unknown token report: {unknown_tokens_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

