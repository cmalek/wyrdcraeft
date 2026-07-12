from __future__ import annotations

import json
from pathlib import Path

import pytest

from wyrdcraeft.services.ocr.bt_witness_prep import (
    BTWitnessPrepInput,
    BTWitnessPrepRun,
    prepare_pages,
)
from wyrdcraeft.services.ocr.bt_witness_prep.anchors import ANCHOR_SEEDS_REL
from wyrdcraeft.services.ocr.bt_witness_prep.manifest import (
    PAGES_MANIFEST_REL,
    TILES_MANIFEST_REL,
)

FIXTURE_DIR = (
    Path(__file__).resolve().parents[1] / "fixtures" / "ocr" / "bt_witness_prep"
)
RECIPE_ID = "bt-two-column-v1"


def test_prepare_pages_runs_end_to_end_pipeline(tmp_path: Path) -> None:
    prep_input = BTWitnessPrepInput(
        source_dir=FIXTURE_DIR,
        output_dir=tmp_path / "witness-prep",
        recipe_id=RECIPE_ID,
    )

    run = prepare_pages(prep_input)

    assert isinstance(run, BTWitnessPrepRun)
    assert run.prep_input == prep_input
    assert [page.page_id for page in run.source_pages] == [
        "bt-0002",
        "bt-0007",
        "bt-0010",
        "anglosaxondictio00bosw-0142",
        "anglosaxondictio00bosw-0397",
    ]
    assert len(run.preprocessed_pages) == 5
    assert len(run.tiles) == 11
    assert len(run.anchor_seeds) == 11

    pages_by_id = {page.page_id: page for page in run.preprocessed_pages}
    assert pages_by_id["bt-0002"].status == "fallback_whole_page_only"
    assert pages_by_id["bt-0007"].status == "ready"
    assert pages_by_id["bt-0010"].status == "ready"
    assert pages_by_id["anglosaxondictio00bosw-0142"].status == "fallback_whole_page_only"
    assert pages_by_id["anglosaxondictio00bosw-0397"].status == "fallback_whole_page_only"

    tiles_by_page: dict[str, list] = {}
    for tile in run.tiles:
        tiles_by_page.setdefault(tile.page_id, []).append(tile)

    assert len(tiles_by_page["bt-0002"]) == 1
    assert tiles_by_page["bt-0002"][0].quality.status == "fallback"
    assert tiles_by_page["bt-0002"][0].quality.composite_score is None
    assert len(tiles_by_page["anglosaxondictio00bosw-0142"]) == 1
    assert len(tiles_by_page["anglosaxondictio00bosw-0397"]) == 1

    assert len(tiles_by_page["bt-0007"]) == 4
    assert len(tiles_by_page["bt-0010"]) == 4
    for page_id in ("bt-0007", "bt-0010"):
        for tile in tiles_by_page[page_id]:
            assert tile.quality.status == "ready"
            assert tile.quality.composite_score is not None
            assert tile.image_path.exists()

    output_dir = prep_input.output_dir
    assert (output_dir / "pages" / "bt-0007.png").exists()
    assert (output_dir / "tiles" / "bt-0007-col-1-part-1.png").exists()
    assert (output_dir / PAGES_MANIFEST_REL).exists()
    assert (output_dir / TILES_MANIFEST_REL).exists()
    assert (output_dir / ANCHOR_SEEDS_REL).exists()

    page_rows = [
        json.loads(line)
        for line in (output_dir / PAGES_MANIFEST_REL)
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    tile_rows = [
        json.loads(line)
        for line in (output_dir / TILES_MANIFEST_REL)
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert len(page_rows) == 5
    assert len(tile_rows) == 11
    pages_by_manifest_id = {row["page_id"]: row for row in page_rows}
    assert pages_by_manifest_id["bt-0002"]["status"] == "fallback_whole_page_only"
    assert pages_by_manifest_id["anglosaxondictio00bosw-0142"]["status"] == (
        "fallback_whole_page_only"
    )
    assert any(row["quality"]["status"] == "fallback" for row in tile_rows)
    assert any(row["quality"]["status"] == "ready" for row in tile_rows)


def test_prepare_pages_honors_overlap_px_override(tmp_path: Path) -> None:
    prep_input = BTWitnessPrepInput(
        source_dir=FIXTURE_DIR,
        output_dir=tmp_path / "overlap-prep",
        recipe_id=RECIPE_ID,
        page_ids=("bt-0007",),
        overlap_px=40,
    )

    run = prepare_pages(prep_input)

    overlap_values = {
        tile.overlap_px for tile in run.tiles if tile.overlap_px > 0
    }
    assert overlap_values == {40}


def test_prepare_pages_filters_page_ids_in_memory(tmp_path: Path) -> None:
    prep_input = BTWitnessPrepInput(
        source_dir=FIXTURE_DIR,
        output_dir=tmp_path / "filtered-prep",
        recipe_id=RECIPE_ID,
        page_ids=("bt-0007", "bt-0010"),
    )

    run = prepare_pages(prep_input)

    assert [page.page_id for page in run.source_pages] == ["bt-0007", "bt-0010"]
    assert len(run.preprocessed_pages) == 2


def test_prepare_pages_zero_page_filter_raises(tmp_path: Path) -> None:
    prep_input = BTWitnessPrepInput(
        source_dir=FIXTURE_DIR,
        output_dir=tmp_path / "empty-prep",
        recipe_id=RECIPE_ID,
        page_ids=("bt-missing",),
    )

    with pytest.raises(ValueError, match="bt-missing"):
        prepare_pages(prep_input)
