from __future__ import annotations

from pathlib import Path

from PIL import Image

from wyrdcraeft.services.ocr.bt_witness_prep.models import BTSourcePage
from wyrdcraeft.services.ocr.bt_witness_prep.preprocess import (
    BTPagePreprocessor,
    BTPreprocessRecipe,
    _clamp_crop_box,
    preprocess_source_page,
)
from wyrdcraeft.services.ocr.bt_witness_prep.source import enumerate_source_pages

FIXTURE_DIR = (
    Path(__file__).resolve().parents[1] / "fixtures" / "ocr" / "bt_witness_prep"
)
RECIPE_ID = "bt-two-column-v1"
RECIPE = BTPreprocessRecipe.conservative_default(RECIPE_ID)

EXPECTED_CROP_BOUNDS: dict[str, tuple[int, int, int, int]] = {
    "bt-0002": (0, 0, 120, 160),
    "bt-0007": (14, 14, 227, 307),
    "bt-0010": (22, 22, 459, 619),
}
PROTECTED_MARKER_MAX_LUMINANCE = 32


def _source_page(page_id: str):
    pages = {page.page_id: page for page in enumerate_source_pages(FIXTURE_DIR, RECIPE_ID)}
    return pages[page_id]


def test_preprocess_crop_box_is_deterministic_for_fixture_page(tmp_path: Path) -> None:
    source_page = _source_page("bt-0007")
    preprocessor = BTPagePreprocessor(RECIPE)

    first = preprocessor.preprocess(source_page, tmp_path / "first")
    second = preprocessor.preprocess(source_page, tmp_path / "second")

    assert first.crop_box == second.crop_box == EXPECTED_CROP_BOUNDS["bt-0007"]


def test_preprocess_preserves_output_dimensions_and_contracts(tmp_path: Path) -> None:
    source_page = _source_page("bt-0007")
    result = preprocess_source_page(source_page, tmp_path, RECIPE)

    left, top, right, bottom = result.crop_box
    assert result.source_path == source_page.source_path
    assert result.page_id == source_page.page_id
    assert result.status == "ready"
    assert result.width_px == right - left
    assert result.height_px == bottom - top
    assert result.image_path.exists()
    assert result.image_path.parent == tmp_path.resolve()


def test_preprocess_records_recipe_id_on_result(tmp_path: Path) -> None:
    source_page = _source_page("bt-0010")

    result = preprocess_source_page(source_page, tmp_path, RECIPE)

    assert result.recipe_id == RECIPE_ID


def test_preprocess_writes_grayscale_background_normalized_output(tmp_path: Path) -> None:
    source_page = _source_page("bt-0007")
    source_mtime = source_page.source_path.stat().st_mtime

    result = preprocess_source_page(source_page, tmp_path, RECIPE)

    with Image.open(result.image_path) as prepared:
        assert prepared.mode == "L"
        assert prepared.size == (result.width_px, result.height_px)
        assert prepared.getextrema()[0] != prepared.getextrema()[1]
    assert source_page.source_path.stat().st_mtime == source_mtime


def test_regression_fixture_pages_preserve_expected_crop_bounds(tmp_path: Path) -> None:
    preprocessor = BTPagePreprocessor(RECIPE)

    for page_id, expected_crop in EXPECTED_CROP_BOUNDS.items():
        result = preprocessor.preprocess(_source_page(page_id), tmp_path / page_id)
        assert result.crop_box == expected_crop


def test_regression_fixture_pages_do_not_clip_protected_corner_markers(
    tmp_path: Path,
) -> None:
    for page_id in ("bt-0007", "bt-0010"):
        result = preprocess_source_page(_source_page(page_id), tmp_path / page_id, RECIPE)

        with Image.open(result.image_path) as prepared:
            width, height = prepared.size
            corner_samples = (
                prepared.getpixel((2, 2)),
                prepared.getpixel((width - 3, 2)),
                prepared.getpixel((2, height - 3)),
                prepared.getpixel((width - 3, height - 3)),
            )

        assert all(sample <= PROTECTED_MARKER_MAX_LUMINANCE for sample in corner_samples)


def test_preprocess_function_matches_preprocessor_entrypoint(tmp_path: Path) -> None:
    source_page = _source_page("bt-0002")

    expected = BTPagePreprocessor(RECIPE).preprocess(source_page, tmp_path / "class")
    actual = preprocess_source_page(source_page, tmp_path / "function", RECIPE)

    assert actual.crop_box == expected.crop_box
    assert actual.recipe_id == expected.recipe_id
    assert actual.width_px == expected.width_px
    assert actual.height_px == expected.height_px


def test_preprocess_clamps_pathological_over_crop_to_max_margin(
    tmp_path: Path,
) -> None:
    width_px = 200
    height_px = 200
    max_margin_fraction = 0.12
    max_left = int(width_px * max_margin_fraction)
    source_path = tmp_path / "synthetic-overcrop.png"
    image = Image.new("RGB", (width_px, height_px), (245, 245, 245))
    pixels = image.load()
    assert pixels is not None
    # Sparse left-edge ink: aggressive detector with high min_content misses it.
    for y in range(0, height_px, 20):
        pixels[1, y] = (10, 10, 10)
    # Dense content starts past the clamp boundary so raw detection over-crops.
    for x in range(50, width_px - 10):
        for y in range(20, height_px - 20):
            pixels[x, y] = (15, 15, 15)
    # Marker inside the band clamp must preserve (lost if left were ~50).
    for x in range(30, 36):
        for y in range(30, 36):
            pixels[x, y] = (0, 0, 0)
    image.save(source_path, format="PNG")

    source_page = BTSourcePage(
        source_path=source_path,
        page_id="synthetic-overcrop",
        recipe_id="clamp-regression",
        width_px=width_px,
        height_px=height_px,
    )
    recipe = BTPreprocessRecipe(
        recipe_id="clamp-regression",
        margin_luminance_delta=20,
        min_content_pixels_per_line=40,
        max_margin_fraction=max_margin_fraction,
        deskew_mode="noop",
        normalize_background=False,
        export_grayscale=True,
        sharpen=False,
    )

    result = preprocess_source_page(source_page, tmp_path / "out", recipe)
    left, _top, right, bottom = result.crop_box

    assert left == max_left
    assert left / width_px <= max_margin_fraction
    assert (width_px - right) / width_px <= max_margin_fraction
    assert (height_px - bottom) / height_px <= max_margin_fraction or bottom == height_px
    with Image.open(result.image_path) as prepared:
        # Marker was at source x=30..35; after left crop it sits near x=6..11.
        marker_samples = (
            prepared.getpixel((6, 10)),
            prepared.getpixel((8, 12)),
        )
    assert all(sample <= PROTECTED_MARKER_MAX_LUMINANCE for sample in marker_samples)


def test_clamp_crop_box_falls_back_to_full_frame_when_geometry_collapses() -> None:
    recipe = BTPreprocessRecipe(
        recipe_id="clamp-collapse",
        max_margin_fraction=0.6,
    )

    assert _clamp_crop_box((70, 10, 30, 90), 100, 100, recipe) == (0, 0, 100, 100)
