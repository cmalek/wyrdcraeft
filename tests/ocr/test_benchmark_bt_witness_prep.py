from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO_ROOT / "scripts" / "ocr"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import benchmark_bt_witness_prep as benchmark

from wyrdcraeft.services.ocr.bt_witness_prep.validation import (
    BTValidationManifest,
    BTValidationPage,
)


def _write_png(path: Path, color: tuple[int, int, int] = (20, 20, 20)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (8, 8), color).save(path, format="PNG")


def test_discover_candidate_tile_images_uses_reading_order(tmp_path: Path) -> None:
    page_id = "bt-0007"
    tiles_dir = tmp_path / "tiles"
    # Write out of order so discovery must impose reading order.
    for geometry in (
        "col-2-part-2",
        "col-1-part-2",
        "col-2-part-1",
        "col-1-part-1",
    ):
        _write_png(tiles_dir / f"{page_id}-{geometry}.png")

    discovered = benchmark.discover_candidate_tile_images(tmp_path, page_id)

    assert [path.name for path in discovered] == [
        f"{page_id}-col-1-part-1.png",
        f"{page_id}-col-1-part-2.png",
        f"{page_id}-col-2-part-1.png",
        f"{page_id}-col-2-part-2.png",
    ]


def test_discover_candidate_tile_images_falls_back_to_whole_page(
    tmp_path: Path,
) -> None:
    page_id = "bt-0002"
    _write_png(tmp_path / "tiles" / f"{page_id}-whole-page.png")

    discovered = benchmark.discover_candidate_tile_images(tmp_path, page_id)

    assert [path.name for path in discovered] == [f"{page_id}-whole-page.png"]


def test_materialize_baseline_pages_uses_manifest_source_filename(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "sources"
    output_dir = tmp_path / "baseline_pages"
    real_source = source_dir / "BT 0007.jp2"
    decoy = source_dir / "bt-0007.png"
    _write_png(real_source, (10, 20, 30))
    _write_png(decoy, (200, 200, 200))

    manifest = BTValidationManifest(
        pages=(
            BTValidationPage(
                page_id="bt-0007",
                source_filename="BT 0007.jp2",
                classification="standard_dense",
                comparison_witness_available=False,
            ),
        ),
    )

    paths = benchmark.materialize_baseline_pages(manifest, source_dir, output_dir)

    assert paths["bt-0007"] == output_dir.resolve() / "bt-0007.png"
    with Image.open(paths["bt-0007"]) as image:
        assert image.getpixel((0, 0)) == (10, 20, 30)


def test_collect_guardrail_flags_reads_manifests_tiles_jsonl_and_ors(
    tmp_path: Path,
) -> None:
    manifests = tmp_path / "manifests"
    manifests.mkdir(parents=True)
    rows = [
        {
            "page_id": "bt-0007",
            "tile_id": "bt-0007:col-1-part-1",
            "quality": {"small_component_guardrail_failed": False},
        },
        {
            "page_id": "bt-0007",
            "tile_id": "bt-0007:col-1-part-2",
            "quality": {"small_component_guardrail_failed": True},
        },
        {
            "page_id": "bt-0010",
            "tile_id": "bt-0010:col-1-part-1",
            "quality": {"small_component_guardrail_failed": False},
        },
    ]
    (manifests / "tiles.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )
    # Wrong path must be ignored.
    (tmp_path / "tiles.jsonl").write_text(
        json.dumps(
            {
                "page_id": "bt-0010",
                "quality": {"small_component_guardrail_failed": True},
            },
        )
        + "\n",
        encoding="utf-8",
    )

    flags = benchmark.collect_guardrail_flags(tmp_path)

    assert flags == {"bt-0007": True, "bt-0010": False}


def test_run_benchmark_live_arms_use_distinct_image_inputs(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source_dir = tmp_path / "sources"
    prep_dir = tmp_path / "prep"
    ocr_output_dir = tmp_path / "ocr"
    manifest_path = tmp_path / "validation_manifest.json"
    page_id = "bt-0007"
    source_name = "BT 0007.jp2"
    _write_png(source_dir / source_name, (11, 11, 11))
    tiles_dir = prep_dir / "tiles"
    for geometry in benchmark.CANDIDATE_TILE_READING_ORDER:
        _write_png(tiles_dir / f"{page_id}-{geometry}.png", (40, 40, 40))
    (prep_dir / "manifests").mkdir(parents=True)
    (prep_dir / "manifests" / "tiles.jsonl").write_text("", encoding="utf-8")
    manifest_path.write_text(
        json.dumps(
            {
                "pages": [
                    {
                        "page_id": page_id,
                        "source_filename": source_name,
                        "classification": "standard_dense",
                        "comparison_witness_available": False,
                        "comparison_witness_path": None,
                    },
                ],
            },
        ),
        encoding="utf-8",
    )

    seen_images: list[Path] = []

    def fake_ocr(image_path: Path, _output_dir: Path) -> str:
        seen_images.append(image_path.resolve())
        return f"text-from-{image_path.name}"

    monkeypatch.setattr(benchmark, "prepare_pages", lambda _input: None)

    args = benchmark.parse_args(
        [
            "--manifest",
            str(manifest_path),
            "--output",
            str(tmp_path / "summary.json"),
            "--source-dir",
            str(source_dir),
            "--prepare-output-dir",
            str(prep_dir),
            "--ocr-output-dir",
            str(ocr_output_dir),
        ],
    )
    summary = benchmark.run_benchmark(args, ocr_runner=fake_ocr)

    baseline_images = [
        path for path in seen_images if "baseline_pages" in path.parts
    ]
    candidate_images = [
        path for path in seen_images if path.parent.name == "tiles"
    ]
    assert len(baseline_images) == 1
    assert len(candidate_images) == 4
    assert baseline_images[0].name == f"{page_id}.png"
    assert [path.name for path in candidate_images] == [
        f"{page_id}-col-1-part-1.png",
        f"{page_id}-col-1-part-2.png",
        f"{page_id}-col-2-part-1.png",
        f"{page_id}-col-2-part-2.png",
    ]
    assert summary["baseline_arm"]["kind"] == "raw_whole_page"
    assert summary["candidate_arm"]["kind"] == "prepared_tiles_concatenated"
    assert summary["page_arm_metadata"][0]["candidate_tile_count"] == 4
