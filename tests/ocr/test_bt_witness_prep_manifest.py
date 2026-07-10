from __future__ import annotations

import json
from pathlib import Path

import pytest

from wyrdcraeft.services.ocr.bt_witness_prep import (
    BTAnchorSeed,
    BTPreprocessedPage,
    BTSourcePage,
    BTTile,
    BTTileQuality,
    BTWitnessPrepInput,
    BTWitnessPrepRun,
)
from wyrdcraeft.services.ocr.bt_witness_prep.anchors import (
    BTAnchorSeedBuilder,
    BTAnchorSeedWriter,
)
from wyrdcraeft.services.ocr.bt_witness_prep.manifest import BTWitnessManifestWriter


def test_source_page_id_is_stable_from_filename_stem() -> None:
    assert BTSourcePage.page_id_for(Path("/scan-set/BT 0007.tif")) == "bt-0007"
    assert BTSourcePage.page_id_for(Path("/other/BT 0007.png")) == "bt-0007"


def test_tile_id_is_stable_from_page_and_split_geometry() -> None:
    assert BTTile.tile_id_for("bt-0007", column=1, part=1) == "bt-0007:col-1-part-1"
    assert BTTile.tile_id_for("bt-0007", column=2, part=2) == "bt-0007:col-2-part-2"


def test_page_and_tile_records_require_provenance_fields() -> None:
    source_page = BTSourcePage(
        source_path=Path("scans/BT 0007.tif"),
        page_id="bt-0007",
        recipe_id="bt-two-column-v1",
        width_px=2400,
        height_px=3200,
    )
    preprocessed_page = BTPreprocessedPage(
        source_path=source_page.source_path,
        page_id=source_page.page_id,
        recipe_id=source_page.recipe_id,
        image_path=Path("prep/bt-0007.png"),
        crop_box=(0, 0, 2400, 3200),
        width_px=2400,
        height_px=3200,
    )
    tile = BTTile(
        source_path=source_page.source_path,
        page_id=source_page.page_id,
        recipe_id=source_page.recipe_id,
        tile_id="bt-0007:col-1-part-1",
        image_path=Path("tiles/bt-0007-col-1-part-1.png"),
        column=1,
        part=1,
        crop_box=(0, 0, 1200, 1600),
        width_px=1200,
        height_px=1600,
        quality=BTTileQuality(status="ready"),
    )

    assert source_page.source_path == Path("scans/BT 0007.tif")
    assert source_page.page_id == preprocessed_page.page_id == tile.page_id
    assert source_page.recipe_id == preprocessed_page.recipe_id == tile.recipe_id
    assert preprocessed_page.crop_box == (0, 0, 2400, 3200)
    assert tile.crop_box == (0, 0, 1200, 1600)

    with pytest.raises(TypeError):
        BTSourcePage(page_id="bt-0007", recipe_id="bt-two-column-v1")  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        BTTile(page_id="bt-0007", tile_id="bt-0007:col-1-part-1")  # type: ignore[call-arg]


def test_witness_prep_run_is_json_serializable_dto() -> None:
    prep_input = BTWitnessPrepInput(
        source_dir=Path("scans"),
        output_dir=Path("work/bt"),
        recipe_id="bt-two-column-v1",
    )
    page = BTSourcePage(
        source_path=Path("scans/BT 0007.tif"),
        page_id="bt-0007",
        recipe_id=prep_input.recipe_id,
        width_px=2400,
        height_px=3200,
    )
    tile = BTTile(
        source_path=page.source_path,
        page_id=page.page_id,
        recipe_id=page.recipe_id,
        tile_id=BTTile.tile_id_for(page.page_id, column=1, part=1),
        image_path=Path("tiles/bt-0007-col-1-part-1.png"),
        column=1,
        part=1,
        crop_box=(0, 0, 1200, 1600),
        width_px=1200,
        height_px=1600,
        quality=BTTileQuality(status="ready", notes=("standard split",)),
    )
    anchor = BTAnchorSeed(
        source_path=page.source_path,
        page_id=page.page_id,
        tile_id=tile.tile_id,
        region_id=tile.tile_id,
        region_type="column_half_tile",
        parent_region_id=page.page_id,
        label="headword",
        text="wesan",
        crop_box=(10, 20, 110, 60),
    )
    run = BTWitnessPrepRun(
        prep_input=prep_input,
        source_pages=(page,),
        preprocessed_pages=(),
        tiles=(tile,),
        anchor_seeds=(anchor,),
    )

    encoded = json.dumps(run.to_dict(), sort_keys=True)
    decoded = json.loads(encoded)

    assert decoded["prep_input"]["source_dir"] == "scans"
    assert decoded["source_pages"][0]["source_path"] == "scans/BT 0007.tif"
    assert decoded["tiles"][0]["crop_box"] == [0, 0, 1200, 1600]
    assert decoded["tiles"][0]["quality"]["notes"] == ["standard split"]


def _sample_preprocessed_page(
    page_id: str,
    *,
    recipe_id: str = "bt-two-column-v1",
) -> BTPreprocessedPage:
    return BTPreprocessedPage(
        source_path=Path(f"scans/BT {page_id.removeprefix('bt-')}.tif"),
        page_id=page_id,
        recipe_id=recipe_id,
        image_path=Path(f"prep/{page_id}.png"),
        crop_box=(0, 0, 2400, 3200),
        width_px=2400,
        height_px=3200,
    )


def _sample_tile(  # noqa: PLR0913
    page_id: str,
    *,
    column: int,
    part: int,
    recipe_id: str = "bt-two-column-v1",
    overlap_px: int = 0,
    overlaps_tile_ids: tuple[str, ...] = (),
) -> BTTile:
    tile_id = BTTile.tile_id_for(page_id, column=column, part=part)
    return BTTile(
        source_path=Path(f"scans/BT {page_id.removeprefix('bt-')}.tif"),
        page_id=page_id,
        recipe_id=recipe_id,
        tile_id=tile_id,
        image_path=Path(f"tiles/{tile_id}.png"),
        column=column,
        part=part,
        crop_box=(0, 0, 1200, 1600),
        width_px=1200,
        height_px=1600,
        overlap_px=overlap_px,
        overlaps_tile_ids=overlaps_tile_ids,
        quality=BTTileQuality(
            status="ready",
            stroke_contrast_score=0.82,
            focus_score=0.77,
            composite_score=0.79,
            small_component_guardrail_failed=False,
        ),
    )


def test_pages_jsonl_contains_source_and_recipe_provenance(tmp_path: Path) -> None:
    page = _sample_preprocessed_page("bt-0007")
    writer = BTWitnessManifestWriter(tmp_path)

    pages_path = writer.write_pages((page,))

    rows = [json.loads(line) for line in pages_path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    row = rows[0]
    assert row["page_id"] == "bt-0007"
    assert row["source_path"] == "scans/BT 0007.tif"
    assert row["recipe_id"] == "bt-two-column-v1"
    assert row["image_path"] == "prep/bt-0007.png"
    assert row["crop_box"] == [0, 0, 2400, 3200]


def test_tiles_jsonl_contains_crop_overlap_and_quality_metadata(
    tmp_path: Path,
) -> None:
    page_id = "bt-0007"
    upper = _sample_tile(page_id, column=1, part=1)
    lower = _sample_tile(
        page_id,
        column=1,
        part=2,
        overlap_px=30,
        overlaps_tile_ids=(upper.tile_id,),
    )
    writer = BTWitnessManifestWriter(tmp_path)

    tiles_path = writer.write_tiles((lower, upper))

    rows = [json.loads(line) for line in tiles_path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 2
    row = rows[1]
    assert row["tile_id"] == lower.tile_id
    assert row["crop_box"] == [0, 0, 1200, 1600]
    assert row["overlap_px"] == 30
    assert row["overlaps_tile_ids"] == [upper.tile_id]
    assert row["quality"]["composite_score"] == 0.79
    assert row["quality"]["small_component_guardrail_failed"] is False


def test_anchor_seeds_jsonl_contains_page_region_hierarchy(tmp_path: Path) -> None:
    tile = _sample_tile("bt-0007", column=1, part=1)
    builder = BTAnchorSeedBuilder()
    writer = BTAnchorSeedWriter(tmp_path)

    seeds = builder.build_from_tiles((tile,))
    anchors_path = writer.write(seeds)

    rows = [json.loads(line) for line in anchors_path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    row = rows[0]
    assert row["page_id"] == "bt-0007"
    assert row["region_id"] == tile.tile_id
    assert row["region_type"] == "column_half_tile"
    assert row["parent_region_id"] == "bt-0007"
    assert row["crop_box"] == [0, 0, 1200, 1600]
    assert row["line_number"] is None
    assert row["line_text"] == ""


def test_manifest_serialization_order_is_deterministic(tmp_path: Path) -> None:
    pages = (
        _sample_preprocessed_page("bt-0010"),
        _sample_preprocessed_page("bt-0007"),
    )
    tiles = (
        _sample_tile("bt-0010", column=2, part=2),
        _sample_tile("bt-0007", column=1, part=1),
        _sample_tile("bt-0010", column=1, part=1),
    )
    manifest_writer = BTWitnessManifestWriter(tmp_path)
    anchor_writer = BTAnchorSeedWriter(tmp_path)
    seeds = BTAnchorSeedBuilder().build_from_tiles(tiles)

    pages_path = manifest_writer.write_pages(pages)
    tiles_path = manifest_writer.write_tiles(tiles)
    anchors_path = anchor_writer.write(seeds)

    page_ids = [
        json.loads(line)["page_id"]
        for line in pages_path.read_text(encoding="utf-8").splitlines()
    ]
    tile_ids = [
        json.loads(line)["tile_id"]
        for line in tiles_path.read_text(encoding="utf-8").splitlines()
    ]
    region_ids = [
        json.loads(line)["region_id"]
        for line in anchors_path.read_text(encoding="utf-8").splitlines()
    ]

    assert page_ids == ["bt-0007", "bt-0010"]
    assert tile_ids == [
        "bt-0007:col-1-part-1",
        "bt-0010:col-1-part-1",
        "bt-0010:col-2-part-2",
    ]
    assert region_ids == tile_ids
