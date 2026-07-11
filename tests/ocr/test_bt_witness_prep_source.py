from __future__ import annotations

from pathlib import Path

import pytest

from wyrdcraeft.services.ocr.bt_witness_prep.models import BTSourcePage
from wyrdcraeft.services.ocr.bt_witness_prep.source import (
    BTSourcePageEnumerator,
    enumerate_source_pages,
)

FIXTURE_DIR = (
    Path(__file__).resolve().parents[1] / "fixtures" / "ocr" / "bt_witness_prep"
)
RECIPE_ID = "bt-two-column-v1"


def test_enumerate_source_pages_finds_jp2_in_stable_sorted_order() -> None:
    pages = enumerate_source_pages(FIXTURE_DIR, RECIPE_ID)

    assert [page.source_path.name for page in pages] == [
        "BT 0002.jp2",
        "BT 0007.jp2",
        "BT 0010.jp2",
        "anglosaxondictio00bosw_0142.jp2",
        "anglosaxondictio00bosw_0397.jp2",
    ]


def test_enumerate_source_pages_ignores_unsupported_files() -> None:
    pages = enumerate_source_pages(FIXTURE_DIR, RECIPE_ID)

    names = {page.source_path.name for page in pages}
    assert names == {
        "BT 0002.jp2",
        "BT 0007.jp2",
        "BT 0010.jp2",
        "anglosaxondictio00bosw_0142.jp2",
        "anglosaxondictio00bosw_0397.jp2",
    }


def test_enumerate_source_pages_derives_page_ids_from_filenames() -> None:
    pages = enumerate_source_pages(FIXTURE_DIR, RECIPE_ID)

    assert [page.page_id for page in pages] == [
        "bt-0002",
        "bt-0007",
        "bt-0010",
        "anglosaxondictio00bosw-0142",
        "anglosaxondictio00bosw-0397",
    ]
    assert all(page.page_id == BTSourcePage.page_id_for(page.source_path) for page in pages)


def test_page_id_for_normalizes_underscores_to_hyphens() -> None:
    assert (
        BTSourcePage.page_id_for(Path("anglosaxondictio00bosw_0142.jp2"))
        == "anglosaxondictio00bosw-0142"
    )


def test_enumerate_source_pages_stamps_recipe_id_and_dimensions(
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "BT 0042.jp2"
    from PIL import Image

    Image.new("RGB", (101, 202), color="white").save(image_path, "PNG")

    pages = enumerate_source_pages(tmp_path, RECIPE_ID)

    assert len(pages) == 1
    page = pages[0]
    assert page.recipe_id == RECIPE_ID
    assert page.width_px == 101
    assert page.height_px == 202
    assert page.source_path == image_path.resolve()


def test_enumerate_source_pages_accepts_case_insensitive_jp2_extension(
    tmp_path: Path,
) -> None:
    from PIL import Image

    Image.new("RGB", (10, 20), color="white").save(tmp_path / "BT 0099.JP2", "PNG")

    pages = enumerate_source_pages(tmp_path, RECIPE_ID)

    assert len(pages) == 1
    assert pages[0].page_id == "bt-0099"


def test_enumerate_source_pages_raises_for_missing_directory(tmp_path: Path) -> None:
    missing = tmp_path / "missing-scans"

    with pytest.raises(FileNotFoundError, match="does not exist"):
        enumerate_source_pages(missing, RECIPE_ID)


def test_enumerate_source_pages_raises_for_empty_directory(tmp_path: Path) -> None:
    empty = tmp_path / "empty-scans"
    empty.mkdir()
    (empty / "notes.txt").write_text("no pages here", encoding="utf-8")

    with pytest.raises(ValueError, match=r"no \.jp2"):
        enumerate_source_pages(empty, RECIPE_ID)


def test_bt_source_page_enumerator_matches_function_entrypoint() -> None:
    expected = enumerate_source_pages(FIXTURE_DIR, RECIPE_ID)
    actual = BTSourcePageEnumerator(RECIPE_ID).enumerate(FIXTURE_DIR)

    assert actual == expected
