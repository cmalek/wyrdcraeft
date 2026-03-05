from __future__ import annotations

import os
from unittest.mock import patch

from wyrdcraeft.cli.cli import cli
from wyrdcraeft.services.ocr import OldEnglishOCROutput

#: Expected test value for OCRmyPDF page-segmentation mode.
EXPECTED_TEST_PSM = 6
#: Expected test value for OCRmyPDF oversample DPI.
EXPECTED_TEST_OVERSAMPLE_DPI = 450
#: Settings-fallback worker count for olmocr in CLI tests.
EXPECTED_SETTINGS_OLMOCR_WORKERS = 3
#: Settings-fallback max concurrent requests in CLI tests.
EXPECTED_SETTINGS_OLMOCR_MAX_CONCURRENT_REQUESTS = 4
#: Settings-fallback render dimension in CLI tests.
EXPECTED_SETTINGS_OLMOCR_TARGET_DIM = 1200
#: Settings-fallback page retries in CLI tests.
EXPECTED_SETTINGS_OLMOCR_PAGE_RETRIES = 7
#: Settings-fallback proxy token cap in CLI tests.
EXPECTED_SETTINGS_PROXY_MAX_TOKENS_CAP = 1700
#: Settings-fallback YAML char threshold in CLI tests.
EXPECTED_SETTINGS_PROXY_MIN_BODY_CHARS = 70
#: Settings-fallback YAML line threshold in CLI tests.
EXPECTED_SETTINGS_PROXY_MIN_BODY_LINES = 9
#: Settings-fallback upstream timeout in CLI tests.
EXPECTED_SETTINGS_PROXY_TIMEOUT_SECONDS = 88.5
#: Settings-fallback startup timeout in CLI tests.
EXPECTED_SETTINGS_PROXY_STARTUP_TIMEOUT_SECONDS = 22.5


def test_ocr_group_help(runner) -> None:
    result = runner.invoke(cli, ["ocr", "--help"])
    assert result.exit_code == 0
    assert "old-english" in result.output
    assert "proxy" in result.output


def test_ocr_old_english_help(runner) -> None:
    result = runner.invoke(cli, ["ocr", "old-english", "--help"])
    assert result.exit_code == 0
    assert "--input-pdf" in result.output
    assert "--skip-ocr" in result.output
    assert "--rules-file" in result.output
    assert "--upstream-base-url" in result.output


def test_ocr_proxy_help(runner) -> None:
    result = runner.invoke(cli, ["ocr", "proxy", "--help"])
    assert result.exit_code == 0
    assert "--upstream-base-url" in result.output
    assert "--max-tokens-cap" in result.output
    assert "--override-length-to-stop" in result.output


@patch("wyrdcraeft.cli.ocr.run_old_english_ocr_pipeline")
def test_ocr_old_english_option_flow(mock_run, runner, temp_dir) -> None:
    input_pdf = temp_dir / "source.pdf"
    input_pdf.write_bytes(b"%PDF-1.4\n%stub\n")

    rules_file = temp_dir / "rules.tsv"
    rules_file.write_text("", encoding="utf-8")
    wordlist_file = temp_dir / "wordlist.txt"
    wordlist_file.write_text("word\n", encoding="utf-8")

    output = OldEnglishOCROutput(
        input_pdf=input_pdf.resolve(),
        output_dir=(temp_dir / "out").resolve(),
        ocr_pdf=(temp_dir / "out" / "01_ocr.pdf").resolve(),
        raw_text_path=(temp_dir / "out" / "02_raw.txt").resolve(),
        normalized_text_path=(temp_dir / "out" / "03_normalized.txt").resolve(),
        unknown_tokens_path=(temp_dir / "out" / "04_unknown_tokens.tsv").resolve(),
    )
    mock_run.return_value = output

    result = runner.invoke(
        cli,
        [
            "ocr",
            "old-english",
            "--input-pdf",
            str(input_pdf),
            "--output-dir",
            str(temp_dir / "out"),
            "--pages",
            "1-5",
            "--lang",
            "eng+lat",
            "--tesseract-psm",
            str(EXPECTED_TEST_PSM),
            "--oversample-dpi",
            str(EXPECTED_TEST_OVERSAMPLE_DPI),
            "--skip-ocr",
            "--rules-file",
            str(rules_file),
            "--wordlist-file",
            str(wordlist_file),
            "--upstream-base-url",
            "http://127.0.0.1:8080/v1",
        ],
    )

    assert result.exit_code == 0
    assert "OCR pipeline complete." in result.output
    assert f"Output directory: {output.output_dir}" in result.output

    assert mock_run.call_count == 1
    config = mock_run.call_args.args[0]
    assert config.input_pdf == input_pdf
    assert config.output_dir == temp_dir / "out"
    assert config.pages == "1-5"
    assert config.lang == "eng+lat"
    assert config.tesseract_psm == EXPECTED_TEST_PSM
    assert config.oversample_dpi == EXPECTED_TEST_OVERSAMPLE_DPI
    assert config.skip_ocr is True
    assert config.rules_file == rules_file
    assert config.wordlist_file == wordlist_file
    assert config.upstream_base_url == "http://127.0.0.1:8080/v1"


@patch("wyrdcraeft.cli.ocr.run_old_english_ocr_pipeline")
def test_ocr_old_english_uses_settings_fallback(mock_run, runner, temp_dir) -> None:
    input_pdf = temp_dir / "source.pdf"
    input_pdf.write_bytes(b"%PDF-1.4\n%stub\n")

    rules_file = temp_dir / "rules.tsv"
    rules_file.write_text("", encoding="utf-8")
    wordlist_file = temp_dir / "wordlist.txt"
    wordlist_file.write_text("word\n", encoding="utf-8")

    mock_run.return_value = OldEnglishOCROutput(
        input_pdf=input_pdf.resolve(),
        output_dir=(temp_dir / "out").resolve(),
        ocr_pdf=input_pdf.resolve(),
        raw_text_path=(temp_dir / "out" / "02_raw.txt").resolve(),
        normalized_text_path=(temp_dir / "out" / "03_normalized.txt").resolve(),
        unknown_tokens_path=(temp_dir / "out" / "04_unknown_tokens.tsv").resolve(),
    )

    env = {
        "wyrdcraeft_OCR_OLMOCR_WORKERS": str(EXPECTED_SETTINGS_OLMOCR_WORKERS),
        "wyrdcraeft_OCR_OLMOCR_MAX_CONCURRENT_REQUESTS": str(
            EXPECTED_SETTINGS_OLMOCR_MAX_CONCURRENT_REQUESTS
        ),
        "wyrdcraeft_OCR_OLMOCR_TARGET_LONGEST_IMAGE_DIM": str(
            EXPECTED_SETTINGS_OLMOCR_TARGET_DIM
        ),
        "wyrdcraeft_OCR_OLMOCR_MAX_PAGE_RETRIES": str(
            EXPECTED_SETTINGS_OLMOCR_PAGE_RETRIES
        ),
        "wyrdcraeft_OCR_UPSTREAM_BASE_URL": "http://127.0.0.1:9999/v1",
        "wyrdcraeft_OCR_PROXY_MAX_TOKENS_CAP": str(
            EXPECTED_SETTINGS_PROXY_MAX_TOKENS_CAP
        ),
        "wyrdcraeft_OCR_PROXY_OVERRIDE_LENGTH_TO_STOP": "false",
        "wyrdcraeft_OCR_PROXY_MIN_BODY_CHARS_AFTER_YAML": str(
            EXPECTED_SETTINGS_PROXY_MIN_BODY_CHARS
        ),
        "wyrdcraeft_OCR_PROXY_MIN_BODY_LINES_AFTER_YAML": str(
            EXPECTED_SETTINGS_PROXY_MIN_BODY_LINES
        ),
        "wyrdcraeft_OCR_PROXY_CLAMP_BOTH_TOKEN_FIELDS": "true",
        "wyrdcraeft_OCR_PROXY_UPSTREAM_TIMEOUT_SECONDS": str(
            EXPECTED_SETTINGS_PROXY_TIMEOUT_SECONDS
        ),
        "wyrdcraeft_OCR_PROXY_STARTUP_TIMEOUT_SECONDS": str(
            EXPECTED_SETTINGS_PROXY_STARTUP_TIMEOUT_SECONDS
        ),
    }
    result = runner.invoke(
        cli,
        [
            "ocr",
            "old-english",
            "--input-pdf",
            str(input_pdf),
            "--rules-file",
            str(rules_file),
            "--wordlist-file",
            str(wordlist_file),
        ],
        env=env,
    )

    assert result.exit_code == 0
    config = mock_run.call_args.args[0]
    assert config.olmocr_workers == EXPECTED_SETTINGS_OLMOCR_WORKERS
    assert (
        config.olmocr_max_concurrent_requests
        == EXPECTED_SETTINGS_OLMOCR_MAX_CONCURRENT_REQUESTS
    )
    assert config.olmocr_target_longest_image_dim == EXPECTED_SETTINGS_OLMOCR_TARGET_DIM
    assert config.olmocr_max_page_retries == EXPECTED_SETTINGS_OLMOCR_PAGE_RETRIES
    assert config.upstream_base_url == "http://127.0.0.1:9999/v1"
    assert config.proxy_max_tokens_cap == EXPECTED_SETTINGS_PROXY_MAX_TOKENS_CAP
    assert config.proxy_override_length_to_stop is False
    assert (
        config.proxy_min_body_chars_after_yaml
        == EXPECTED_SETTINGS_PROXY_MIN_BODY_CHARS
    )
    assert (
        config.proxy_min_body_lines_after_yaml
        == EXPECTED_SETTINGS_PROXY_MIN_BODY_LINES
    )
    assert config.proxy_clamp_both_token_fields is True
    assert (
        config.proxy_upstream_timeout_seconds
        == EXPECTED_SETTINGS_PROXY_TIMEOUT_SECONDS
    )
    assert (
        config.proxy_startup_timeout_seconds
        == EXPECTED_SETTINGS_PROXY_STARTUP_TIMEOUT_SECONDS
    )


@patch("wyrdcraeft.cli.ocr.run_old_english_ocr_pipeline")
def test_ocr_old_english_reports_runtime_errors(mock_run, runner, temp_dir) -> None:
    input_pdf = temp_dir / "source.pdf"
    input_pdf.write_bytes(b"%PDF-1.4\n%stub\n")

    rules_file = temp_dir / "rules.tsv"
    rules_file.write_text("", encoding="utf-8")
    wordlist_file = temp_dir / "wordlist.txt"
    wordlist_file.write_text("word\n", encoding="utf-8")

    mock_run.side_effect = RuntimeError(
        "Required tool 'ocrmypdf' not found. Install it and rerun."
    )

    result = runner.invoke(
        cli,
        [
            "ocr",
            "old-english",
            "--input-pdf",
            str(input_pdf),
            "--rules-file",
            str(rules_file),
            "--wordlist-file",
            str(wordlist_file),
        ],
    )

    assert result.exit_code != 0
    assert "Required tool 'ocrmypdf' not found" in result.output


@patch("wyrdcraeft.cli.ocr._run_proxy_server")
def test_ocr_proxy_command_sets_env(mock_run, runner) -> None:
    original_upstream_base_url = os.environ.get("UPSTREAM_BASE_URL")

    def _assert_env() -> None:
        assert os.environ.get("UPSTREAM_BASE_URL") == "http://127.0.0.1:8080/v1"
        assert os.environ.get("PROXY_HOST") == "127.0.0.1"
        assert os.environ.get("PROXY_PORT") == "8011"
        assert os.environ.get("PROXY_MAX_TOKENS_CAP") == "1400"
        assert os.environ.get("OVERRIDE_LENGTH_TO_STOP") == "true"
        assert os.environ.get("MIN_BODY_CHARS_AFTER_YAML") == "60"
        assert os.environ.get("MIN_BODY_LINES_AFTER_YAML") == "6"

    mock_run.side_effect = _assert_env

    result = runner.invoke(
        cli,
        [
            "ocr",
            "proxy",
            "--upstream-base-url",
            "http://127.0.0.1:8080/v1",
            "--host",
            "127.0.0.1",
            "--port",
            "8011",
            "--max-tokens-cap",
            "1400",
            "--override-length-to-stop",
            "--min-body-chars-after-yaml",
            "60",
            "--min-body-lines-after-yaml",
            "6",
        ],
    )

    assert result.exit_code == 0
    assert mock_run.call_count == 1
    assert os.environ.get("UPSTREAM_BASE_URL") == original_upstream_base_url


@patch("wyrdcraeft.cli.ocr._run_proxy_server")
def test_ocr_proxy_uses_settings_fallback(mock_run, runner) -> None:
    def _assert_env() -> None:
        assert os.environ.get("UPSTREAM_BASE_URL") == "http://127.0.0.1:9000/v1"
        assert os.environ.get("PROXY_HOST") == "127.0.0.1"
        assert os.environ.get("PROXY_PORT") == "9001"
        assert os.environ.get("PROXY_MAX_TOKENS_CAP") == "1900"
        assert os.environ.get("OVERRIDE_LENGTH_TO_STOP") == "false"
        assert os.environ.get("MIN_BODY_CHARS_AFTER_YAML") == "55"
        assert os.environ.get("MIN_BODY_LINES_AFTER_YAML") == "8"
        assert os.environ.get("CLAMP_BOTH_TOKEN_FIELDS") == "true"
        assert os.environ.get("PROXY_TEMPERATURE_OVERRIDE") == "0.2"
        assert os.environ.get("PROXY_TOP_P_OVERRIDE") == "0.95"
        assert os.environ.get("PROXY_UPSTREAM_TIMEOUT_SECONDS") == "111.0"

    mock_run.side_effect = _assert_env

    result = runner.invoke(
        cli,
        ["ocr", "proxy"],
        env={
            "wyrdcraeft_OCR_UPSTREAM_BASE_URL": "http://127.0.0.1:9000/v1",
            "wyrdcraeft_OCR_PROXY_HOST": "127.0.0.1",
            "wyrdcraeft_OCR_PROXY_PORT": "9001",
            "wyrdcraeft_OCR_PROXY_MAX_TOKENS_CAP": "1900",
            "wyrdcraeft_OCR_PROXY_OVERRIDE_LENGTH_TO_STOP": "false",
            "wyrdcraeft_OCR_PROXY_MIN_BODY_CHARS_AFTER_YAML": "55",
            "wyrdcraeft_OCR_PROXY_MIN_BODY_LINES_AFTER_YAML": "8",
            "wyrdcraeft_OCR_PROXY_CLAMP_BOTH_TOKEN_FIELDS": "true",
            "wyrdcraeft_OCR_PROXY_TEMPERATURE_OVERRIDE": "0.2",
            "wyrdcraeft_OCR_PROXY_TOP_P_OVERRIDE": "0.95",
            "wyrdcraeft_OCR_PROXY_UPSTREAM_TIMEOUT_SECONDS": "111.0",
        },
    )

    assert result.exit_code == 0
    assert mock_run.call_count == 1
