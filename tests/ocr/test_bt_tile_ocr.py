from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from wyrdcraeft.services.ocr.bt_tile_ocr import (
    TILE_READING_ORDER,
    concatenate_tile_texts,
    discover_tile_images,
    run_page_witness_ocr,
    run_tile_ocr,
    tile_id_from_image_path,
)
from wyrdcraeft.services.ocr.old_english_pipeline import OldEnglishOCRConfig


def _write_png(path: Path, color: tuple[int, int, int] = (20, 20, 20)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (8, 8), color).save(path, format="PNG")


def test_discover_tile_images_uses_reading_order(tmp_path: Path) -> None:
    page_id = "bt-0007"
    tiles_dir = tmp_path / "tiles"
    for geometry in (
        "col-2-part-2",
        "col-1-part-2",
        "col-2-part-1",
        "col-1-part-1",
    ):
        _write_png(tiles_dir / f"{page_id}-{geometry}.png")

    discovered = discover_tile_images(tmp_path, page_id)

    assert [path.name for path in discovered] == [
        f"{page_id}-col-1-part-1.png",
        f"{page_id}-col-2-part-1.png",
        f"{page_id}-col-1-part-2.png",
        f"{page_id}-col-2-part-2.png",
    ]


def test_discover_tile_images_falls_back_to_whole_page(tmp_path: Path) -> None:
    page_id = "bt-0002"
    _write_png(tmp_path / "tiles" / f"{page_id}-whole-page.png")

    discovered = discover_tile_images(tmp_path, page_id)

    assert [path.name for path in discovered] == [f"{page_id}-whole-page.png"]


def test_tile_id_from_image_path_maps_geometry_suffix() -> None:
    tile_path = Path("tiles/bt-0007-col-1-part-2.png")

    assert tile_id_from_image_path(tile_path) == "bt-0007:col-1-part-2"


def test_concatenate_tile_texts_joins_with_blank_lines() -> None:
    joined = concatenate_tile_texts([" alpha ", "", "beta"])

    assert joined == "alpha\n\nbeta\n"


def test_run_tile_ocr_uses_injected_runner(tmp_path: Path) -> None:
    image_path = tmp_path / "tile.png"
    output_dir = tmp_path / "ocr"
    _write_png(image_path)

    def fake_runner(path: Path, workspace: Path) -> str:
        assert path == image_path
        assert workspace == output_dir
        return "witness text"

    text = run_tile_ocr(image_path, output_dir, ocr_runner=fake_runner)

    assert text == "witness text"


def test_run_tile_ocr_skip_ocr_reads_cached_normalized_text(tmp_path: Path) -> None:
    image_path = tmp_path / "tile.png"
    output_dir = tmp_path / "ocr"
    _write_png(image_path)
    output_dir.mkdir(parents=True)
    (output_dir / "03_normalized.txt").write_text("cached text\n", encoding="utf-8")

    text = run_tile_ocr(image_path, output_dir, skip_ocr=True)

    assert text == "cached text\n"


def test_run_tile_ocr_skip_ocr_raises_when_cache_missing(tmp_path: Path) -> None:
    image_path = tmp_path / "tile.png"
    output_dir = tmp_path / "ocr"
    _write_png(image_path)

    with pytest.raises(RuntimeError, match="skip-ocr enabled"):
        run_tile_ocr(image_path, output_dir, skip_ocr=True)


@patch("wyrdcraeft.services.ocr.bt_tile_ocr.run_old_english_ocr_pipeline")
def test_run_tile_ocr_calls_old_english_pipeline(
    mock_pipeline,
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "tile.png"
    output_dir = tmp_path / "ocr"
    _write_png(image_path)
    normalized = output_dir / "03_normalized.txt"
    normalized.parent.mkdir(parents=True)
    normalized.write_text("live text\n", encoding="utf-8")
    mock_pipeline.return_value = MagicMock(normalized_text_path=normalized)
    base_config = OldEnglishOCRConfig(
        input_path=Path("placeholder"),
        olmocr_workers=3,
    )

    text = run_tile_ocr(
        image_path,
        output_dir,
        ocr_config=base_config,
    )

    assert text == "live text\n"
    passed_config = mock_pipeline.call_args.args[0]
    assert passed_config.input_path == image_path
    assert passed_config.output_dir == output_dir
    assert passed_config.olmocr_workers == 3


def test_run_page_witness_ocr_concatenates_tile_outputs(tmp_path: Path) -> None:
    page_id = "bt-0007"
    tile_paths = [
        tmp_path / "tiles" / f"{page_id}-{geometry}.png"
        for geometry in TILE_READING_ORDER[:2]
    ]
    for tile_path in tile_paths:
        _write_png(tile_path)

    def fake_runner(path: Path, _workspace: Path) -> str:
        return f"text-from-{path.stem}"

    joined = run_page_witness_ocr(
        tile_paths,
        lambda _tile_path, index: tmp_path / "witnesses" / f"tile-{index:02d}",
        ocr_runner=fake_runner,
    )

    assert joined == (
        "text-from-bt-0007-col-1-part-1\n\n"
        "text-from-bt-0007-col-2-part-1\n"
    )
