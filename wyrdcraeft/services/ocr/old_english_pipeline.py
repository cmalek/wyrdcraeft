from __future__ import annotations

import re
import shutil
import subprocess
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from wyrdcraeft.services.ocr_proxy.config import DEFAULT_UPSTREAM_BASE_URL
from wyrdcraeft.services.ocr_proxy.runtime import (
    PROXY_STARTUP_TIMEOUT_SECONDS,
    ProxyLaunchConfig,
    run_olmocr_pipeline_with_managed_proxy,
)

#: Default OCR language bundle for Tesseract via OCRmyPDF.
DEFAULT_OCR_LANG = "eng+lat"
#: Default Tesseract page segmentation mode for grammar-style text blocks.
DEFAULT_TESSERACT_PSM = 4
#: Default resolution used for force-OCR processing.
DEFAULT_OVERSAMPLE_DPI = 400
#: Token regex including common Old English graphemes.
TOKEN_REGEX = re.compile(r"[A-Za-zÆæÐðÞþŌōĀāĒēĪīȲȳǢǣ]+")
#: Minimum number of TSV fields required for one regex correction rule.
MIN_RULE_FIELDS = 2
#: Tokens this length or shorter are omitted from unknown-token reports.
MIN_UNKNOWN_TOKEN_LENGTH = 2
#: Minimum meaningful characters required from pypdf extraction.
MIN_PYPDF_TEXT_LENGTH = 10
#: Default workspace subdirectory name for local olmocr outputs.
DEFAULT_OLMOCR_WORKSPACE_DIRNAME = "olmocr_workspace"
#: Default number of local olmocr workers for one PDF invocation.
DEFAULT_OLMOCR_WORKERS = 1
#: Default max concurrent requests for local olmocr invocation.
DEFAULT_OLMOCR_MAX_CONCURRENT_REQUESTS = 1
#: Default image rendering dimension for olmocr page rasterization.
DEFAULT_OLMOCR_TARGET_LONGEST_IMAGE_DIM = 1024
#: Default retry count for page-level olmocr failures.
DEFAULT_OLMOCR_MAX_PAGE_RETRIES = 5


@dataclass(frozen=True)
class OldEnglishOCRConfig:
    """
    Configuration contract for one Old English OCR pipeline run.

    Args:
        input_pdf: Input PDF file path.
        output_dir: Destination directory for generated artifacts.
        pages: Optional page-range expression (not supported in olmocr mode).
        lang: Legacy OCR language option retained for CLI compatibility.
        tesseract_psm: Legacy OCR option retained for CLI compatibility.
        oversample_dpi: Legacy OCR option retained for CLI compatibility.
        skip_ocr: If ``True``, skips olmocr run and reuses existing markdown output.
        rules_file: TSV regex correction rules file path.
        wordlist_file: Seed wordlist file path for unknown-token reporting.
        olmocr_model: Optional olmocr model argument passed through to pipeline.
        olmocr_workers: Number of local workers for olmocr pipeline.
        olmocr_max_concurrent_requests: Max concurrent request budget for olmocr.
        olmocr_target_longest_image_dim: Raster target dimension for olmocr rendering.
        olmocr_max_page_retries: Page retry budget for olmocr pipeline.
        upstream_base_url: Upstream OpenAI-compatible server URL for proxy forwarding.
        proxy_host: Managed proxy bind host.
        proxy_max_tokens_cap: Managed proxy max token cap.
        proxy_override_length_to_stop: Managed proxy finish-reason override toggle.
        proxy_min_body_chars_after_yaml: Managed proxy YAML heuristic char threshold.
        proxy_min_body_lines_after_yaml: Managed proxy YAML heuristic line threshold.
        proxy_clamp_both_token_fields: Managed proxy token-field sync toggle.
        proxy_temperature_override: Managed proxy temperature override.
        proxy_top_p_override: Managed proxy top_p override.
        proxy_upstream_timeout_seconds: Managed proxy upstream timeout.
        proxy_startup_timeout_seconds: Managed proxy startup readiness timeout.

    """

    #: Input PDF file path.
    input_pdf: Path
    #: Destination directory for generated artifacts.
    output_dir: Path | None = None
    #: Optional page-range expression (not supported in olmocr mode).
    pages: str | None = None
    #: Legacy OCR language option retained for CLI compatibility.
    lang: str = DEFAULT_OCR_LANG
    #: Legacy OCR option retained for CLI compatibility.
    tesseract_psm: int = DEFAULT_TESSERACT_PSM
    #: Legacy OCR option retained for CLI compatibility.
    oversample_dpi: int = DEFAULT_OVERSAMPLE_DPI
    #: If ``True``, skip olmocr run and reuse existing markdown output.
    skip_ocr: bool = False
    #: TSV regex correction rules file path.
    rules_file: Path = Path("data/ocr/rules/old_english_safe.tsv")
    #: Seed wordlist file path for unknown-token reporting.
    wordlist_file: Path = Path("data/ocr/wordlists/old_english_seed.txt")
    #: Optional olmocr model argument passed through to pipeline.
    olmocr_model: str | None = None
    #: Number of local workers for olmocr pipeline.
    olmocr_workers: int = DEFAULT_OLMOCR_WORKERS
    #: Max concurrent request budget for olmocr.
    olmocr_max_concurrent_requests: int = DEFAULT_OLMOCR_MAX_CONCURRENT_REQUESTS
    #: Raster target dimension for olmocr rendering.
    olmocr_target_longest_image_dim: int = DEFAULT_OLMOCR_TARGET_LONGEST_IMAGE_DIM
    #: Page retry budget for olmocr pipeline.
    olmocr_max_page_retries: int = DEFAULT_OLMOCR_MAX_PAGE_RETRIES
    #: Upstream OpenAI-compatible server URL for proxy forwarding.
    upstream_base_url: str = DEFAULT_UPSTREAM_BASE_URL
    #: Managed proxy bind host.
    proxy_host: str = "127.0.0.1"
    #: Managed proxy max token cap.
    proxy_max_tokens_cap: int = 1500
    #: Managed proxy finish-reason override toggle.
    proxy_override_length_to_stop: bool = True
    #: Managed proxy YAML heuristic char threshold.
    proxy_min_body_chars_after_yaml: int = 50
    #: Managed proxy YAML heuristic line threshold.
    proxy_min_body_lines_after_yaml: int = 5
    #: Managed proxy token-field sync toggle.
    proxy_clamp_both_token_fields: bool = False
    #: Managed proxy temperature override.
    proxy_temperature_override: float | None = None
    #: Managed proxy top_p override.
    proxy_top_p_override: float | None = None
    #: Managed proxy upstream timeout.
    proxy_upstream_timeout_seconds: float = 120.0
    #: Managed proxy startup readiness timeout.
    proxy_startup_timeout_seconds: float = PROXY_STARTUP_TIMEOUT_SECONDS


@dataclass(frozen=True)
class OldEnglishOCROutput:
    """
    Output artifact paths generated by one OCR pipeline run.

    Args:
        input_pdf: Resolved input PDF path.
        output_dir: Resolved output directory.
        ocr_pdf: OCR source PDF path used for this pipeline run.
        raw_text_path: Plain-text extraction path generated from olmocr markdown.
        normalized_text_path: Final normalized text output path.
        unknown_tokens_path: TSV report path for unknown tokens.

    """

    #: Resolved input PDF path.
    input_pdf: Path
    #: Resolved output directory.
    output_dir: Path
    #: OCR source PDF path used for this pipeline run.
    ocr_pdf: Path
    #: Plain-text extraction path generated from olmocr markdown.
    raw_text_path: Path
    #: Final normalized text output path.
    normalized_text_path: Path
    #: TSV report path for unknown tokens.
    unknown_tokens_path: Path


def build_default_output_dir(input_pdf: Path) -> Path:
    """
    Build default output directory path for an input PDF.

    Args:
        input_pdf: Source PDF path.

    Returns:
        ``data/ocr/<pdf-stem>`` under repository root.

    """
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / "data" / "ocr" / input_pdf.stem


def run_old_english_ocr_pipeline(config: OldEnglishOCRConfig) -> OldEnglishOCROutput:
    """
    Run the Old English OCR pipeline end to end.

    Side Effects:
        Creates output files and directories and invokes external binaries.

    Args:
        config: Pipeline configuration object.

    Raises:
        RuntimeError: If inputs are missing or required tools fail.

    Returns:
        Output artifact paths for the completed run.

    """
    input_pdf = config.input_pdf.resolve()
    _require_existing_file(input_pdf, label="Input PDF")

    output_dir = _resolve_output_dir(input_pdf=input_pdf, configured=config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_text_path = output_dir / "02_raw.txt"
    normalized_text_path = output_dir / "03_normalized.txt"
    unknown_tokens_path = output_dir / "04_unknown_tokens.tsv"

    rules_file = config.rules_file.resolve()
    wordlist_file = config.wordlist_file.resolve()
    _require_existing_file(rules_file, label="Rules file")
    _require_existing_file(wordlist_file, label="Wordlist file")

    if config.pages:
        message = (
            "The --pages option is not supported in olmocr mode. "
            "Provide a pre-sliced input PDF instead."
        )
        raise RuntimeError(message)

    olmocr_workspace = output_dir / DEFAULT_OLMOCR_WORKSPACE_DIRNAME
    olmocr_workspace.mkdir(parents=True, exist_ok=True)

    if not config.skip_ocr:
        _run_olmocr(
            input_pdf=input_pdf,
            workspace=olmocr_workspace,
            config=config,
        )
    raw_text = _collect_olmocr_markdown_text(olmocr_workspace)
    raw_text_path.write_text(raw_text, encoding="utf-8")
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

    return OldEnglishOCROutput(
        input_pdf=input_pdf,
        output_dir=output_dir,
        ocr_pdf=input_pdf,
        raw_text_path=raw_text_path,
        normalized_text_path=normalized_text_path,
        unknown_tokens_path=unknown_tokens_path,
    )


def _run_olmocr(
    *,
    input_pdf: Path,
    workspace: Path,
    config: OldEnglishOCRConfig,
) -> None:
    """
    Run one local olmocr pipeline invocation through the managed proxy.

    Side Effects:
        Creates workspace artifacts and markdown output under ``workspace``.

    Args:
        input_pdf: Source PDF path.
        workspace: Local olmocr workspace directory.
        config: OCR pipeline configuration.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    Raises:
        RuntimeError: If olmocr exits non-zero.

    """
    olmocr_args: list[str] = [
        str(workspace),
        "--pdfs",
        str(input_pdf),
        "--markdown",
        "--workers",
        str(config.olmocr_workers),
        "--max_concurrent_requests",
        str(config.olmocr_max_concurrent_requests),
        "--target_longest_image_dim",
        str(config.olmocr_target_longest_image_dim),
        "--max_page_retries",
        str(config.olmocr_max_page_retries),
    ]
    if config.olmocr_model:
        olmocr_args.extend(["--model", config.olmocr_model])

    launch_config = ProxyLaunchConfig(
        upstream_base_url=config.upstream_base_url,
        host=config.proxy_host,
        max_tokens_cap=config.proxy_max_tokens_cap,
        override_length_to_stop=config.proxy_override_length_to_stop,
        min_body_chars_after_yaml=config.proxy_min_body_chars_after_yaml,
        min_body_lines_after_yaml=config.proxy_min_body_lines_after_yaml,
        clamp_both_token_fields=config.proxy_clamp_both_token_fields,
        temperature_override=config.proxy_temperature_override,
        top_p_override=config.proxy_top_p_override,
        upstream_timeout_seconds=config.proxy_upstream_timeout_seconds,
        startup_timeout_seconds=config.proxy_startup_timeout_seconds,
    )
    return_code = run_olmocr_pipeline_with_managed_proxy(
        olmocr_args,
        launch_config=launch_config,
    )
    if return_code == 0:
        return
    message = f"olmocr pipeline failed with exit code {return_code}."
    raise RuntimeError(message)


def _collect_olmocr_markdown_text(workspace: Path) -> str:
    """
    Collect OCR text from olmocr markdown output files.

    Args:
        workspace: Local olmocr workspace directory.

    Raises:
        RuntimeError: If no markdown files were emitted.

    Returns:
        Concatenated markdown text payload.

    """
    markdown_root = workspace / "markdown"
    markdown_files = sorted(markdown_root.rglob("*.md"))
    if not markdown_files:
        message = f"olmocr completed but emitted no markdown files in {markdown_root}."
        raise RuntimeError(message)

    chunks: list[str] = []
    for markdown_path in markdown_files:
        text = markdown_path.read_text(encoding="utf-8").strip()
        if text:
            chunks.append(text)

    if not chunks:
        message = (
            "olmocr completed but markdown files were empty. "
            f"Workspace: {workspace}."
        )
        raise RuntimeError(message)
    return "\n\n".join(chunks).strip() + "\n"


def _resolve_output_dir(*, input_pdf: Path, configured: Path | None) -> Path:
    """
    Resolve output directory from explicit config or default convention.

    Args:
        input_pdf: Resolved input PDF path.
        configured: Optional configured output directory path.

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    Returns:
        Resolved output directory path.

    """
    if configured is not None:
        return configured.resolve()
    return build_default_output_dir(input_pdf)


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
    command_text = " ".join(command)
    error_message = f"Command failed: {command_text}\n{message}"
    raise RuntimeError(error_message)


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
    message = f"Required tool '{binary}' not found. Install it and rerun."
    raise RuntimeError(message)


def _require_existing_file(path: Path, *, label: str) -> None:
    """
    Ensure one required file path exists.

    Args:
        path: File path to validate.

    Keyword Args:
        label: Human-readable label used in error messages.

    Raises:
        RuntimeError: If ``path`` does not exist.

    """
    if path.exists():
        return
    message = f"{label} not found: {path}"
    raise RuntimeError(message)


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


def _extract_text_with_pypdf(pdf_path: Path, output_path: Path) -> None:
    """
    Extract text from a PDF using ``pypdf`` logical text decoding.

    Side Effects:
        Writes extracted text to ``output_path``.

    Args:
        pdf_path: PDF source path.
        output_path: Destination plain-text file path.

    Raises:
        RuntimeError: If the PDF cannot be parsed by ``pypdf``.

    """
    try:
        reader = PdfReader(str(pdf_path))
    except (PdfReadError, OSError, ValueError) as exc:
        message = f"pypdf failed to read {pdf_path}: {exc}"
        raise RuntimeError(message) from exc

    page_texts: list[str] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        page_texts.append(page_text.strip("\n"))

    extracted_text = "\n".join(page_texts).strip()
    output_path.write_text(extracted_text, encoding="utf-8")


def _extract_text_with_fallback(pdf_path: Path, output_path: Path) -> None:
    """
    Extract text with ``pypdf`` first, then fallback to Ghostscript ``txtwrite``.

    Side Effects:
        Writes extracted text to ``output_path``.

    Args:
        pdf_path: PDF source path.
        output_path: Destination plain-text file path.

    Raises:
        RuntimeError: If both extraction paths fail.

    """
    pypdf_error: RuntimeError | None = None
    try:
        _extract_text_with_pypdf(pdf_path, output_path)
        extracted = output_path.read_text(encoding="utf-8")
        if len(extracted.strip()) >= MIN_PYPDF_TEXT_LENGTH:
            return
    except RuntimeError as exc:
        pypdf_error = exc

    _require_tool("gs")
    _extract_text_with_ghostscript(pdf_path, output_path)

    if output_path.read_text(encoding="utf-8").strip():
        return
    if pypdf_error is None:
        message = f"Text extraction failed for {pdf_path}: no text produced."
    else:
        message = f"Text extraction failed for {pdf_path}. {pypdf_error}"
    raise RuntimeError(message)


def _run_ocrmypdf(  # noqa: PLR0913
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

    Keyword Args:
        Uses keyword-only parameters for all inputs.

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

    Raises:
        RuntimeError: If the file contains malformed non-comment lines.

    Returns:
        Ordered compiled regex/replacement pairs.

    """
    compiled: list[tuple[re.Pattern[str], str]] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for line_number, raw_line in enumerate(lines, 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < MIN_RULE_FIELDS:
            message = (
                f"Invalid rule line {line_number} in {path}: expected "
                "pattern<TAB>replacement."
            )
            raise RuntimeError(message)
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
    return {
        line.strip().lower()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


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

    Keyword Args:
        Uses keyword-only parameters for all inputs.

    """
    counter: Counter[str] = Counter()
    for token in TOKEN_REGEX.findall(text):
        normalized = token.lower()
        if len(normalized) <= MIN_UNKNOWN_TOKEN_LENGTH:
            continue
        if normalized in wordlist:
            continue
        counter[normalized] += 1

    lines = ["token\tcount"]
    for token, count in counter.most_common():
        lines.append(f"{token}\t{count}")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
