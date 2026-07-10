from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PIL import Image

from wyrdcraeft.services.ocr.bt_witness_prep.models import BTPreprocessedPage
from wyrdcraeft.services.ocr.bt_witness_prep.preprocess import (
    BTPreprocessRecipe,
    preprocess_source_page,
)
from wyrdcraeft.services.ocr.bt_witness_prep.source import enumerate_source_pages
from wyrdcraeft.services.ocr.bt_witness_prep.tiling import (
    BTPageTiler,
    BTTilingConfig,
    tile_preprocessed_page,
)

FIXTURE_DIR = (
    Path(__file__).resolve().parents[1] / "fixtures" / "ocr" / "bt_witness_prep"
)
RECIPE_ID = "bt-two-column-v1"
RECIPE = BTPreprocessRecipe.conservative_default(RECIPE_ID)
TILING_CONFIG = BTTilingConfig.standard_two_column()
EXPECTED_TILE_ORDER = (
    (1, 1),
    (1, 2),
    (2, 1),
    (2, 2),
)


def _source_page(page_id: str):
    pages = {page.page_id: page for page in enumerate_source_pages(FIXTURE_DIR, RECIPE_ID)}
    return pages[page_id]


def _preprocessed_page(page_id: str, tmp_path: Path) -> BTPreprocessedPage:
    return preprocess_source_page(_source_page(page_id), tmp_path / "pages", RECIPE)


def _tiler() -> BTPageTiler:
    return BTPageTiler(TILING_CONFIG)


def test_standard_page_splits_into_exactly_four_tiles(tmp_path: Path) -> None:
    page = _preprocessed_page("bt-0007", tmp_path)
    result_page, tiles = _tiler().tile(page, tmp_path / "tiles")

    assert result_page.status == "ready"
    assert len(tiles) == 4
    assert all(tile.image_path.exists() for tile in tiles)


def test_tile_order_is_stable_col_part_sequence(tmp_path: Path) -> None:
    page = _preprocessed_page("bt-0010", tmp_path)
    _, tiles = _tiler().tile(page, tmp_path / "tiles")

    assert [(tile.column, tile.part) for tile in tiles] == list(EXPECTED_TILE_ORDER)
    assert [tile.tile_id for tile in tiles] == [
        f"{page.page_id}:col-{column}-part-{part}"
        for column, part in EXPECTED_TILE_ORDER
    ]


def test_vertical_overlap_coordinates_are_correct(tmp_path: Path) -> None:
    page = _preprocessed_page("bt-0007", tmp_path)
    _, tiles = _tiler().tile(page, tmp_path / "tiles")

    by_geometry = {(tile.column, tile.part): tile for tile in tiles}
    overlap_px = TILING_CONFIG.overlap_px

    for column in (1, 2):
        upper = by_geometry[(column, 1)]
        lower = by_geometry[(column, 2)]
        upper_bottom = upper.crop_box[3]
        lower_top = lower.crop_box[1]
        assert upper_bottom > lower_top
        assert upper_bottom - lower_top == overlap_px
        assert upper.overlap_px == overlap_px
        assert lower.overlap_px == overlap_px
        assert upper.overlaps_tile_ids == (lower.tile_id,)
        assert lower.overlaps_tile_ids == (upper.tile_id,)


def test_column_crop_boxes_respect_midline_gutter_guardrails(tmp_path: Path) -> None:
    page = _preprocessed_page("bt-0010", tmp_path)
    _, tiles = _tiler().tile(page, tmp_path / "tiles")

    midline = page.width_px // 2
    gutter_half = TILING_CONFIG.column_gutter_px // 2
    col1_max_right = midline - gutter_half
    col2_min_left = midline + gutter_half

    for tile in tiles:
        left, _, right, _ = tile.crop_box
        if tile.column == 1:
            assert right <= col1_max_right
            assert left == 0
        else:
            assert left >= col2_min_left
            assert right == page.width_px


def test_tiling_is_deterministic_for_fixture_page(tmp_path: Path) -> None:
    page = _preprocessed_page("bt-0007", tmp_path)
    tiler = _tiler()

    first_page, first_tiles = tiler.tile(page, tmp_path / "first")
    second_page, second_tiles = tiler.tile(page, tmp_path / "second")

    assert first_page.status == second_page.status == "ready"
    assert [tile.crop_box for tile in first_tiles] == [
        tile.crop_box for tile in second_tiles
    ]


def test_too_narrow_page_emits_fallback_whole_page_only(tmp_path: Path) -> None:
    page = _preprocessed_page("bt-0002", tmp_path)
    result_page, tiles = _tiler().tile(page, tmp_path / "tiles")

    assert result_page.status == "fallback_whole_page_only"
    assert len(tiles) == 1
    assert tiles[0].crop_box == (0, 0, page.width_px, page.height_px)
    assert tiles[0].quality.status == "fallback"
    assert tiles[0].overlap_px == 0
    assert tiles[0].overlaps_tile_ids == ()


def test_explicit_non_ready_page_status_skips_forced_four_tile_split(
    tmp_path: Path,
) -> None:
    page = replace(
        _preprocessed_page("bt-0010", tmp_path),
        status="needs_manual_review",
    )
    result_page, tiles = _tiler().tile(page, tmp_path / "tiles")

    assert result_page.status == "needs_manual_review"
    assert len(tiles) == 1
    assert tiles[0].quality.status == "fallback"
    assert all(tile.column == 0 for tile in tiles)


def test_unsupported_aspect_ratio_emits_explicit_fallback_status(
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "wide-page.png"
    Image.new("L", (500, 200), color=255).save(image_path)
    page = BTPreprocessedPage(
        source_path=Path("scans/wide-page.png"),
        page_id="wide-page",
        recipe_id=RECIPE_ID,
        image_path=image_path,
        crop_box=(0, 0, 500, 200),
        width_px=500,
        height_px=200,
        status="ready",
    )

    result_page, tiles = _tiler().tile(page, tmp_path / "tiles")

    assert result_page.status == "unsupported_layout"
    assert len(tiles) == 1
    assert tiles[0].quality.status == "fallback"


def test_tile_function_matches_tiler_entrypoint(tmp_path: Path) -> None:
    page = _preprocessed_page("bt-0007", tmp_path)

    expected_page, expected_tiles = _tiler().tile(page, tmp_path / "class")
    actual_page, actual_tiles = tile_preprocessed_page(
        page,
        tmp_path / "function",
        TILING_CONFIG,
    )

    assert actual_page.status == expected_page.status
    assert [tile.crop_box for tile in actual_tiles] == [
        tile.crop_box for tile in expected_tiles
    ]


def test_tile_records_match_image_dimensions(tmp_path: Path) -> None:
    page = _preprocessed_page("bt-0007", tmp_path)
    _, tiles = _tiler().tile(page, tmp_path / "tiles")

    for tile in tiles:
        left, top, right, bottom = tile.crop_box
        assert tile.width_px == right - left
        assert tile.height_px == bottom - top
        with Image.open(tile.image_path) as image:
            assert image.size == (tile.width_px, tile.height_px)
