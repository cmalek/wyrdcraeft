from __future__ import annotations

import importlib
import os
from pathlib import Path
from typing import Any

import click

from wyrdcraeft.services.ocr import (
    OldEnglishOCRConfig,
    run_old_english_ocr_pipeline,
)


@click.group(
    name="ocr",
    help="OCR workflow commands for Old English source PDFs.",
)
def ocr_group() -> None:
    """
    OCR command group for Old English source processing.
    """


def _run_proxy_server() -> None:
    """
    Import and run the proxy server entrypoint lazily.

    Side Effects:
        Imports proxy server module and starts a long-running HTTP service.

    """
    proxy_server = importlib.import_module("wyrdcraeft.services.ocr_proxy.server")
    proxy_server.main()


def _resolve_cli_value(value: Any | None, fallback: Any) -> Any:
    """
    Resolve one CLI option against a settings fallback.

    Args:
        value: Value explicitly provided via CLI option.
        fallback: Value loaded from settings.

    Returns:
        ``value`` when provided, otherwise ``fallback``.

    """
    if value is None:
        return fallback
    return value


@ocr_group.command(
    name="old-english",
    help="Run olmocr + normalization pipeline for Old English PDFs.",
)
@click.option(
    "--input-pdf",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to input PDF.",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory. Default is data/ocr/<input-stem> under repo root.",
)
@click.option(
    "--pages",
    default=None,
    help="Page-range option is not supported in olmocr mode (kept for compatibility).",
)
@click.option(
    "--lang",
    default=None,
    help="Legacy option (ignored in olmocr mode).",
)
@click.option(
    "--tesseract-psm",
    type=int,
    default=None,
    help="Legacy option (ignored in olmocr mode).",
)
@click.option(
    "--oversample-dpi",
    type=int,
    default=None,
    help="Legacy option (ignored in olmocr mode).",
)
@click.option(
    "--skip-ocr/--no-skip-ocr",
    default=None,
    help="Skip olmocr execution and reuse existing workspace markdown output.",
)
@click.option(
    "--rules-file",
    type=click.Path(path_type=Path),
    default=Path("data/ocr/rules/old_english_safe.tsv"),
    show_default=True,
    help="Regex correction rules file (TSV).",
)
@click.option(
    "--wordlist-file",
    type=click.Path(path_type=Path),
    default=Path("data/ocr/wordlists/old_english_seed.txt"),
    show_default=True,
    help="Seed wordlist for unknown-token report.",
)
@click.option(
    "--upstream-base-url",
    default=None,
    help="Upstream OpenAI-compatible base URL used by the managed proxy.",
)
@click.option(
    "--olmocr-model",
    default=None,
    help="Optional olmocr model passed to olmocr.pipeline --model.",
)
@click.option(
    "--olmocr-workers",
    type=int,
    default=None,
    help="Worker count forwarded to olmocr.pipeline --workers.",
)
@click.option(
    "--olmocr-max-concurrent-requests",
    type=int,
    default=None,
    help="Request concurrency forwarded to olmocr.pipeline.",
)
@click.option(
    "--olmocr-target-longest-image-dim",
    type=int,
    default=None,
    help="Image dimension forwarded to olmocr.pipeline.",
)
@click.option(
    "--olmocr-max-page-retries",
    type=int,
    default=None,
    help="Page retry budget forwarded to olmocr.pipeline.",
)
@click.option(
    "--proxy-max-tokens-cap",
    type=int,
    default=None,
    help="Managed proxy max token clamp cap.",
)
@click.option(
    "--proxy-override-length-to-stop/--no-proxy-override-length-to-stop",
    default=None,
    help="Managed proxy finish_reason override toggle.",
)
@click.option(
    "--proxy-min-body-chars-after-yaml",
    type=int,
    default=None,
    help="Managed proxy YAML heuristic body char threshold.",
)
@click.option(
    "--proxy-min-body-lines-after-yaml",
    type=int,
    default=None,
    help="Managed proxy YAML heuristic body line threshold.",
)
@click.option(
    "--proxy-clamp-both-token-fields/--no-proxy-clamp-both-token-fields",
    default=None,
    help="Managed proxy token-field synchronization toggle.",
)
@click.option(
    "--proxy-temperature-override",
    type=float,
    default=None,
    help="Managed proxy temperature override (optional).",
)
@click.option(
    "--proxy-top-p-override",
    type=float,
    default=None,
    help="Managed proxy top_p override (optional).",
)
@click.option(
    "--proxy-upstream-timeout-seconds",
    type=float,
    default=None,
    help="Managed proxy upstream timeout in seconds.",
)
@click.option(
    "--proxy-upstream-max-retries",
    type=int,
    default=None,
    help="Managed proxy retry budget for transient upstream failures.",
)
@click.option(
    "--proxy-upstream-retry-backoff-seconds",
    type=float,
    default=None,
    help="Managed proxy base retry backoff in seconds for transient upstream failures.",
)
@click.option(
    "--proxy-startup-timeout-seconds",
    type=float,
    default=None,
    help="Managed proxy startup timeout in seconds.",
)
@click.pass_context
def old_english_ocr(  # noqa: PLR0913
    ctx: click.Context,
    input_pdf: Path,
    output_dir: Path | None,
    pages: str | None,
    lang: str | None,
    tesseract_psm: int | None,
    oversample_dpi: int | None,
    skip_ocr: bool | None,
    rules_file: Path,
    wordlist_file: Path,
    upstream_base_url: str | None,
    olmocr_model: str | None,
    olmocr_workers: int | None,
    olmocr_max_concurrent_requests: int | None,
    olmocr_target_longest_image_dim: int | None,
    olmocr_max_page_retries: int | None,
    proxy_max_tokens_cap: int | None,
    proxy_override_length_to_stop: bool | None,
    proxy_min_body_chars_after_yaml: int | None,
    proxy_min_body_lines_after_yaml: int | None,
    proxy_clamp_both_token_fields: bool | None,
    proxy_temperature_override: float | None,
    proxy_top_p_override: float | None,
    proxy_upstream_timeout_seconds: float | None,
    proxy_upstream_max_retries: int | None,
    proxy_upstream_retry_backoff_seconds: float | None,
    proxy_startup_timeout_seconds: float | None,
) -> None:
    """
    Run the Old English OCR pipeline through the main ``wyrdcraeft`` CLI.

    Side Effects:
        Creates OCR, text, and report artifacts under the selected output directory.

    Args:
        ctx: Click context containing loaded application settings.
        input_pdf: Path to source PDF.
        output_dir: Optional destination directory for emitted artifacts.
        pages: Legacy page-range option; not supported in olmocr mode.
        lang: Legacy OCR option (ignored in olmocr mode).
        tesseract_psm: Legacy OCR option (ignored in olmocr mode).
        oversample_dpi: Legacy OCR option (ignored in olmocr mode).
        skip_ocr: Whether to skip olmocr and reuse existing workspace output.
        rules_file: TSV regex-correction rules path.
        wordlist_file: Seed lexicon file path for unknown-token report.
        upstream_base_url: Upstream OpenAI-compatible base URL for proxy forwarding.
        olmocr_model: Optional olmocr model passed through to pipeline.
        olmocr_workers: Worker count passed through to olmocr.pipeline.
        olmocr_max_concurrent_requests: Max request concurrency for olmocr.
        olmocr_target_longest_image_dim: Raster dimension for olmocr rendering.
        olmocr_max_page_retries: Retry budget for olmocr page failures.
        proxy_max_tokens_cap: Managed proxy token clamp cap.
        proxy_override_length_to_stop: Managed proxy finish reason override toggle.
        proxy_min_body_chars_after_yaml: Managed proxy YAML char threshold.
        proxy_min_body_lines_after_yaml: Managed proxy YAML line threshold.
        proxy_clamp_both_token_fields: Managed proxy token-field sync toggle.
        proxy_temperature_override: Managed proxy temperature override.
        proxy_top_p_override: Managed proxy top_p override.
        proxy_upstream_timeout_seconds: Managed proxy upstream timeout.
        proxy_upstream_max_retries: Managed proxy retry budget for transient failures.
        proxy_upstream_retry_backoff_seconds: Managed proxy retry backoff in seconds.
        proxy_startup_timeout_seconds: Managed proxy startup timeout.

    Raises:
        click.ClickException: If configuration or external tool execution fails.

    """
    settings = ctx.obj["settings"]
    resolved_lang = _resolve_cli_value(lang, settings.ocr_legacy_lang)
    resolved_tesseract_psm = _resolve_cli_value(
        tesseract_psm, settings.ocr_legacy_tesseract_psm
    )
    resolved_oversample_dpi = _resolve_cli_value(
        oversample_dpi, settings.ocr_legacy_oversample_dpi
    )
    resolved_skip_ocr = _resolve_cli_value(skip_ocr, settings.ocr_skip_ocr)
    resolved_upstream_base_url = _resolve_cli_value(
        upstream_base_url, settings.ocr_upstream_base_url
    )
    resolved_olmocr_model = _resolve_cli_value(olmocr_model, settings.ocr_olmocr_model)
    resolved_olmocr_workers = _resolve_cli_value(
        olmocr_workers, settings.ocr_olmocr_workers
    )
    resolved_olmocr_max_concurrent_requests = _resolve_cli_value(
        olmocr_max_concurrent_requests,
        settings.ocr_olmocr_max_concurrent_requests,
    )
    resolved_olmocr_target_longest_image_dim = _resolve_cli_value(
        olmocr_target_longest_image_dim,
        settings.ocr_olmocr_target_longest_image_dim,
    )
    resolved_olmocr_max_page_retries = _resolve_cli_value(
        olmocr_max_page_retries,
        settings.ocr_olmocr_max_page_retries,
    )
    resolved_proxy_max_tokens_cap = _resolve_cli_value(
        proxy_max_tokens_cap,
        settings.ocr_proxy_max_tokens_cap,
    )
    resolved_proxy_override_length_to_stop = _resolve_cli_value(
        proxy_override_length_to_stop,
        settings.ocr_proxy_override_length_to_stop,
    )
    resolved_proxy_min_body_chars_after_yaml = _resolve_cli_value(
        proxy_min_body_chars_after_yaml,
        settings.ocr_proxy_min_body_chars_after_yaml,
    )
    resolved_proxy_min_body_lines_after_yaml = _resolve_cli_value(
        proxy_min_body_lines_after_yaml,
        settings.ocr_proxy_min_body_lines_after_yaml,
    )
    resolved_proxy_clamp_both_token_fields = _resolve_cli_value(
        proxy_clamp_both_token_fields,
        settings.ocr_proxy_clamp_both_token_fields,
    )
    resolved_proxy_temperature_override = _resolve_cli_value(
        proxy_temperature_override,
        settings.ocr_proxy_temperature_override,
    )
    resolved_proxy_top_p_override = _resolve_cli_value(
        proxy_top_p_override,
        settings.ocr_proxy_top_p_override,
    )
    resolved_proxy_upstream_timeout_seconds = _resolve_cli_value(
        proxy_upstream_timeout_seconds,
        settings.ocr_proxy_upstream_timeout_seconds,
    )
    resolved_proxy_upstream_max_retries = _resolve_cli_value(
        proxy_upstream_max_retries,
        settings.ocr_proxy_upstream_max_retries,
    )
    resolved_proxy_upstream_retry_backoff_seconds = _resolve_cli_value(
        proxy_upstream_retry_backoff_seconds,
        settings.ocr_proxy_upstream_retry_backoff_seconds,
    )
    resolved_proxy_startup_timeout_seconds = _resolve_cli_value(
        proxy_startup_timeout_seconds,
        settings.ocr_proxy_startup_timeout_seconds,
    )

    config = OldEnglishOCRConfig(
        input_pdf=input_pdf,
        output_dir=output_dir,
        pages=pages,
        lang=resolved_lang,
        tesseract_psm=resolved_tesseract_psm,
        oversample_dpi=resolved_oversample_dpi,
        skip_ocr=resolved_skip_ocr,
        rules_file=rules_file,
        wordlist_file=wordlist_file,
        upstream_base_url=resolved_upstream_base_url,
        olmocr_model=resolved_olmocr_model,
        olmocr_workers=resolved_olmocr_workers,
        olmocr_max_concurrent_requests=resolved_olmocr_max_concurrent_requests,
        olmocr_target_longest_image_dim=resolved_olmocr_target_longest_image_dim,
        olmocr_max_page_retries=resolved_olmocr_max_page_retries,
        proxy_max_tokens_cap=resolved_proxy_max_tokens_cap,
        proxy_override_length_to_stop=resolved_proxy_override_length_to_stop,
        proxy_min_body_chars_after_yaml=resolved_proxy_min_body_chars_after_yaml,
        proxy_min_body_lines_after_yaml=resolved_proxy_min_body_lines_after_yaml,
        proxy_clamp_both_token_fields=resolved_proxy_clamp_both_token_fields,
        proxy_temperature_override=resolved_proxy_temperature_override,
        proxy_top_p_override=resolved_proxy_top_p_override,
        proxy_upstream_timeout_seconds=resolved_proxy_upstream_timeout_seconds,
        proxy_upstream_max_retries=resolved_proxy_upstream_max_retries,
        proxy_upstream_retry_backoff_seconds=(
            resolved_proxy_upstream_retry_backoff_seconds
        ),
        proxy_startup_timeout_seconds=resolved_proxy_startup_timeout_seconds,
    )
    try:
        output = run_old_english_ocr_pipeline(config)
    except RuntimeError as e:
        raise click.ClickException(str(e)) from e

    click.echo("OCR pipeline complete.")
    click.echo(f"Input PDF: {output.input_pdf}")
    click.echo(f"Output directory: {output.output_dir}")
    click.echo(f"Raw text: {output.raw_text_path}")
    click.echo(f"Normalized text: {output.normalized_text_path}")
    click.echo(f"Unknown token report: {output.unknown_tokens_path}")


@ocr_group.command(
    name="proxy",
    help="Run the local OpenAI-compatible proxy for olmocr requests.",
)
@click.option(
    "--upstream-base-url",
    default=None,
    help="Upstream OpenAI-compatible base URL (typically llama.cpp/LM Studio /v1).",
)
@click.option(
    "--host",
    default=None,
    help="Proxy bind host.",
)
@click.option(
    "--port",
    type=int,
    default=None,
    help="Proxy bind port.",
)
@click.option(
    "--max-tokens-cap",
    type=int,
    default=None,
    help="Clamp cap applied to max_tokens/max_completion_tokens.",
)
@click.option(
    "--override-length-to-stop/--no-override-length-to-stop",
    default=None,
    help="Enable conservative finish_reason length->stop overrides.",
)
@click.option(
    "--min-body-chars-after-yaml",
    type=int,
    default=None,
    help="Minimum post-YAML body characters for length->stop override.",
)
@click.option(
    "--min-body-lines-after-yaml",
    type=int,
    default=None,
    help="Minimum post-YAML non-empty lines for length->stop override.",
)
@click.option(
    "--clamp-both-token-fields/--no-clamp-both-token-fields",
    default=None,
    help="Synchronize max_tokens and max_completion_tokens before forwarding.",
)
@click.option(
    "--temperature-override",
    type=float,
    default=None,
    help="Optional proxy temperature override value.",
)
@click.option(
    "--top-p-override",
    type=float,
    default=None,
    help="Optional proxy top_p override value.",
)
@click.option(
    "--upstream-timeout-seconds",
    type=float,
    default=None,
    help="Proxy upstream timeout in seconds.",
)
@click.option(
    "--upstream-max-retries",
    type=int,
    default=None,
    help="Retry budget for transient upstream proxy failures.",
)
@click.option(
    "--upstream-retry-backoff-seconds",
    type=float,
    default=None,
    help="Base retry backoff in seconds for transient upstream proxy failures.",
)
@click.pass_context
def run_ocr_proxy(  # noqa: PLR0913
    ctx: click.Context,
    upstream_base_url: str | None,
    host: str | None,
    port: int | None,
    max_tokens_cap: int | None,
    override_length_to_stop: bool | None,
    min_body_chars_after_yaml: int | None,
    min_body_lines_after_yaml: int | None,
    clamp_both_token_fields: bool | None,
    temperature_override: float | None,
    top_p_override: float | None,
    upstream_timeout_seconds: float | None,
    upstream_max_retries: int | None,
    upstream_retry_backoff_seconds: float | None,
) -> None:
    """
    Run the local OpenAI-compatible proxy under the ``wyrdcraeft`` CLI.

    Side Effects:
        Sets process-local proxy configuration environment variables and starts
        a long-running HTTP server process.

    Args:
        ctx: Click context containing loaded application settings.
        upstream_base_url: Upstream OpenAI-compatible base URL.
        host: Proxy bind host.
        port: Proxy bind port.
        max_tokens_cap: Clamp cap for completion token fields.
        override_length_to_stop: Enables conservative finish-reason rewrites.
        min_body_chars_after_yaml: Character threshold for rewrite heuristic.
        min_body_lines_after_yaml: Line threshold for rewrite heuristic.
        clamp_both_token_fields: Whether both token fields are synchronized.
        temperature_override: Optional forced proxy temperature.
        top_p_override: Optional forced proxy top_p.
        upstream_timeout_seconds: Proxy upstream timeout.
        upstream_max_retries: Retry budget for transient upstream request failures.
        upstream_retry_backoff_seconds:
            Base backoff in seconds between transient upstream retries.

    """
    settings = ctx.obj["settings"]
    resolved_upstream_base_url = _resolve_cli_value(
        upstream_base_url, settings.ocr_upstream_base_url
    )
    resolved_host = _resolve_cli_value(host, settings.ocr_proxy_host)
    resolved_port = _resolve_cli_value(port, settings.ocr_proxy_port)
    resolved_max_tokens_cap = _resolve_cli_value(
        max_tokens_cap, settings.ocr_proxy_max_tokens_cap
    )
    resolved_override_length_to_stop = _resolve_cli_value(
        override_length_to_stop,
        settings.ocr_proxy_override_length_to_stop,
    )
    resolved_min_body_chars_after_yaml = _resolve_cli_value(
        min_body_chars_after_yaml,
        settings.ocr_proxy_min_body_chars_after_yaml,
    )
    resolved_min_body_lines_after_yaml = _resolve_cli_value(
        min_body_lines_after_yaml,
        settings.ocr_proxy_min_body_lines_after_yaml,
    )
    resolved_clamp_both_token_fields = _resolve_cli_value(
        clamp_both_token_fields,
        settings.ocr_proxy_clamp_both_token_fields,
    )
    resolved_temperature_override = _resolve_cli_value(
        temperature_override,
        settings.ocr_proxy_temperature_override,
    )
    resolved_top_p_override = _resolve_cli_value(
        top_p_override,
        settings.ocr_proxy_top_p_override,
    )
    resolved_upstream_timeout_seconds = _resolve_cli_value(
        upstream_timeout_seconds,
        settings.ocr_proxy_upstream_timeout_seconds,
    )
    resolved_upstream_max_retries = _resolve_cli_value(
        upstream_max_retries,
        settings.ocr_proxy_upstream_max_retries,
    )
    resolved_upstream_retry_backoff_seconds = _resolve_cli_value(
        upstream_retry_backoff_seconds,
        settings.ocr_proxy_upstream_retry_backoff_seconds,
    )

    updates = {
        "UPSTREAM_BASE_URL": resolved_upstream_base_url,
        "PROXY_HOST": resolved_host,
        "PROXY_PORT": str(resolved_port),
        "PROXY_MAX_TOKENS_CAP": str(resolved_max_tokens_cap),
        "OVERRIDE_LENGTH_TO_STOP": (
            "true" if resolved_override_length_to_stop else "false"
        ),
        "MIN_BODY_CHARS_AFTER_YAML": str(resolved_min_body_chars_after_yaml),
        "MIN_BODY_LINES_AFTER_YAML": str(resolved_min_body_lines_after_yaml),
        "CLAMP_BOTH_TOKEN_FIELDS": (
            "true" if resolved_clamp_both_token_fields else "false"
        ),
        "PROXY_UPSTREAM_TIMEOUT_SECONDS": str(resolved_upstream_timeout_seconds),
        "PROXY_UPSTREAM_MAX_RETRIES": str(resolved_upstream_max_retries),
        "PROXY_UPSTREAM_RETRY_BACKOFF_SECONDS": str(
            resolved_upstream_retry_backoff_seconds
        ),
    }
    if resolved_temperature_override is not None:
        updates["PROXY_TEMPERATURE_OVERRIDE"] = str(resolved_temperature_override)
    if resolved_top_p_override is not None:
        updates["PROXY_TOP_P_OVERRIDE"] = str(resolved_top_p_override)
    original_values = {key: os.environ.get(key) for key in updates}
    os.environ.update(updates)
    try:
        _run_proxy_server()
    finally:
        for key, value in original_values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
