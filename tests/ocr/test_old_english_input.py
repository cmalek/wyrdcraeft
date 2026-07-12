from __future__ import annotations

from unittest.mock import patch

import pytest
from PIL import Image

from wyrdcraeft.services.ocr.old_english_pipeline import (
    BOSWORTH_TOLLER_WITNESS_INPUT_HINT,
    OldEnglishOCRConfig,
    _normalize_ocr_input_to_pdf,
    run_old_english_ocr_pipeline,
)


def _write_support_files(temp_dir) -> tuple:
    rules_file = temp_dir / "rules.tsv"
    rules_file.write_text("", encoding="utf-8")
    wordlist_file = temp_dir / "wordlist.txt"
    wordlist_file.write_text("known\n", encoding="utf-8")
    return rules_file, wordlist_file


def test_old_english_rejects_jp2_file(temp_dir) -> None:
    jp2_path = temp_dir / "scan.jp2"
    jp2_path.write_bytes(b"fake-jp2")
    rules_file, wordlist_file = _write_support_files(temp_dir)

    with pytest.raises(RuntimeError, match="bosworth-toller") as exc_info:
        run_old_english_ocr_pipeline(
            OldEnglishOCRConfig(
                input_path=jp2_path,
                rules_file=rules_file,
                wordlist_file=wordlist_file,
            )
        )

    assert str(exc_info.value) == BOSWORTH_TOLLER_WITNESS_INPUT_HINT


def test_old_english_rejects_image_directory_with_images(temp_dir) -> None:
    image_dir = temp_dir / "images"
    image_dir.mkdir()
    Image.new("RGB", (4, 4), "white").save(image_dir / "page.png")
    rules_file, wordlist_file = _write_support_files(temp_dir)

    with pytest.raises(RuntimeError, match="bosworth-toller") as exc_info:
        run_old_english_ocr_pipeline(
            OldEnglishOCRConfig(
                input_path=image_dir,
                rules_file=rules_file,
                wordlist_file=wordlist_file,
            )
        )

    assert str(exc_info.value) == BOSWORTH_TOLLER_WITNESS_INPUT_HINT


@patch("wyrdcraeft.services.ocr.old_english_pipeline.run_olmocr_pipeline_with_managed_proxy")
def test_old_english_accepts_pdf(mock_run, temp_dir) -> None:
    input_pdf = temp_dir / "source.pdf"
    input_pdf.write_bytes(b"%PDF-1.4\n%stub\n")
    output_dir = temp_dir / "out"
    rules_file, wordlist_file = _write_support_files(temp_dir)

    def _mock_olmocr(_args, *, launch_config) -> int:  # noqa: ARG001
        workspace = output_dir / "olmocr_workspace" / "markdown"
        workspace.mkdir(parents=True, exist_ok=True)
        (workspace / "source_pg1.md").write_text("known", encoding="utf-8")
        return 0

    mock_run.side_effect = _mock_olmocr

    output = run_old_english_ocr_pipeline(
        OldEnglishOCRConfig(
            input_path=input_pdf,
            output_dir=output_dir,
            rules_file=rules_file,
            wordlist_file=wordlist_file,
        )
    )

    assert output.ocr_pdf == input_pdf.resolve()
    assert mock_run.call_count == 1


def test_normalize_ocr_input_to_pdf_accepts_pdf(temp_dir) -> None:
    input_pdf = temp_dir / "source.pdf"
    input_pdf.write_bytes(b"%PDF-1.4\n%stub\n")
    workspace = temp_dir / "workspace"
    workspace.mkdir()

    resolved_pdf = _normalize_ocr_input_to_pdf(
        input_path=input_pdf.resolve(),
        workspace=workspace,
    )

    assert resolved_pdf == input_pdf.resolve()


@patch("wyrdcraeft.services.ocr.old_english_pipeline.run_olmocr_pipeline_with_managed_proxy")
def test_old_english_accepts_single_png(mock_run, temp_dir) -> None:
    input_image = temp_dir / "source.png"
    Image.new("RGB", (4, 4), "white").save(input_image)
    output_dir = temp_dir / "out"
    rules_file, wordlist_file = _write_support_files(temp_dir)

    def _mock_olmocr(_args, *, launch_config) -> int:  # noqa: ARG001
        workspace = output_dir / "olmocr_workspace" / "markdown"
        workspace.mkdir(parents=True, exist_ok=True)
        (workspace / "source_pg1.md").write_text("known", encoding="utf-8")
        return 0

    mock_run.side_effect = _mock_olmocr

    output = run_old_english_ocr_pipeline(
        OldEnglishOCRConfig(
            input_path=input_image,
            output_dir=output_dir,
            rules_file=rules_file,
            wordlist_file=wordlist_file,
        )
    )

    assert output.input_path == input_image.resolve()
    assert output.ocr_pdf == (output_dir / "olmocr_workspace" / "input.pdf").resolve()
    assert output.ocr_pdf.exists()
    assert mock_run.call_count == 1
