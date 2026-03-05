from __future__ import annotations

from unittest.mock import patch

import pytest

from wyrdcraeft.services.ocr.old_english_pipeline import (
    OldEnglishOCRConfig,
    run_old_english_ocr_pipeline,
)


@patch("wyrdcraeft.services.ocr.old_english_pipeline.run_olmocr_pipeline_with_managed_proxy")
def test_pipeline_reads_olmocr_markdown_output(mock_run, temp_dir) -> None:
    input_pdf = temp_dir / "source.pdf"
    input_pdf.write_bytes(b"%PDF-1.4\n%stub\n")

    output_dir = temp_dir / "out"
    rules_file = temp_dir / "rules.tsv"
    rules_file.write_text("", encoding="utf-8")
    wordlist_file = temp_dir / "wordlist.txt"
    wordlist_file.write_text("known\n", encoding="utf-8")

    def _mock_olmocr(_args, *, launch_config) -> int:  # noqa: ARG001
        workspace = output_dir / "olmocr_workspace"
        markdown_dir = workspace / "markdown"
        markdown_dir.mkdir(parents=True, exist_ok=True)
        markdown_path = markdown_dir / "source_pg1.md"
        markdown_path.write_text("some OCR text with unknownword", encoding="utf-8")
        return 0

    mock_run.side_effect = _mock_olmocr

    output = run_old_english_ocr_pipeline(
        OldEnglishOCRConfig(
            input_pdf=input_pdf,
            output_dir=output_dir,
            rules_file=rules_file,
            wordlist_file=wordlist_file,
            upstream_base_url="http://127.0.0.1:8080/v1",
        )
    )

    assert mock_run.call_count == 1
    assert output.raw_text_path.exists()
    assert "some OCR text" in output.raw_text_path.read_text(encoding="utf-8")
    assert output.normalized_text_path.exists()
    unknown_report = output.unknown_tokens_path.read_text(encoding="utf-8")
    assert "unknownword" in unknown_report


@patch("wyrdcraeft.services.ocr.old_english_pipeline.run_olmocr_pipeline_with_managed_proxy")
def test_pipeline_skip_ocr_uses_existing_workspace(mock_run, temp_dir) -> None:
    input_pdf = temp_dir / "source.pdf"
    input_pdf.write_bytes(b"%PDF-1.4\n%stub\n")

    output_dir = temp_dir / "out"
    workspace = output_dir / "olmocr_workspace" / "markdown"
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "existing.md").write_text("precomputed OCR text", encoding="utf-8")

    rules_file = temp_dir / "rules.tsv"
    rules_file.write_text("", encoding="utf-8")
    wordlist_file = temp_dir / "wordlist.txt"
    wordlist_file.write_text("precomputed\nocr\ntext\n", encoding="utf-8")

    output = run_old_english_ocr_pipeline(
        OldEnglishOCRConfig(
            input_pdf=input_pdf,
            output_dir=output_dir,
            skip_ocr=True,
            rules_file=rules_file,
            wordlist_file=wordlist_file,
        )
    )

    assert mock_run.call_count == 0
    assert "precomputed OCR text" in output.raw_text_path.read_text(encoding="utf-8")


def test_pipeline_rejects_pages_option(temp_dir) -> None:
    input_pdf = temp_dir / "source.pdf"
    input_pdf.write_bytes(b"%PDF-1.4\n%stub\n")

    rules_file = temp_dir / "rules.tsv"
    rules_file.write_text("", encoding="utf-8")
    wordlist_file = temp_dir / "wordlist.txt"
    wordlist_file.write_text("known\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="--pages option is not supported"):
        run_old_english_ocr_pipeline(
            OldEnglishOCRConfig(
                input_pdf=input_pdf,
                pages="1-5",
                rules_file=rules_file,
                wordlist_file=wordlist_file,
            )
        )

