"""Anchor seed builders and writers for Bosworth-Toller witness preparation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from wyrdcraeft.services.ocr.bt_witness_prep.models import BTAnchorSeed, BTTile

if TYPE_CHECKING:
    from collections.abc import Sequence

#: Region type assigned to one column half-tile OCR region.
COLUMN_HALF_TILE_REGION_TYPE = "column_half_tile"
#: Relative path for anchor seeds under the witness-prep output dir.
ANCHOR_SEEDS_REL = Path("anchors/anchor_seeds.jsonl")


def _write_jsonl(path: Path, records: Sequence[dict[str, Any]]) -> None:
    """
    Write one JSON object per line to a UTF-8 JSONL file.

    Args:
        path: Destination JSONL path.
        records: Serializable row mappings in write order.

    Side Effects:
        Creates parent directories and writes UTF-8 JSONL.

    """
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, ensure_ascii=False) for record in records]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


class BTAnchorSeedBuilder:
    """
    Derive anchor seeds from prepared tile regions.

    Each tile becomes one ``column_half_tile`` region seed with the page as
    parent region.

    """

    def build_from_tiles(self, tiles: Sequence[BTTile]) -> tuple[BTAnchorSeed, ...]:
        """
        Build one anchor seed per prepared tile region.

        Args:
            tiles: Prepared tile records to convert into anchor seeds.

        Returns:
            Anchor seeds sorted by ``region_id``.

        """
        seeds = tuple(self._seed_for_tile(tile) for tile in tiles)
        return tuple(sorted(seeds, key=lambda seed: seed.region_id))

    def _seed_for_tile(self, tile: BTTile) -> BTAnchorSeed:
        """
        Build one anchor seed for a single tile region.

        Args:
            tile: Prepared tile record.

        Returns:
            Anchor seed with page-parent hierarchy and placeholder line fields.

        """
        return BTAnchorSeed(
            source_path=tile.source_path,
            page_id=tile.page_id,
            tile_id=tile.tile_id,
            region_id=tile.tile_id,
            region_type=COLUMN_HALF_TILE_REGION_TYPE,
            parent_region_id=tile.page_id,
            crop_box=tile.crop_box,
        )


class BTAnchorSeedWriter:
    """
    Write anchor seed records for one witness preparation run.

    Args:
        output_dir: Workspace directory for prepared artifacts.

    """

    def __init__(self, output_dir: Path) -> None:
        """
        Initialize one anchor seed writer for a witness-prep output directory.

        Args:
            output_dir: Workspace directory for prepared artifacts.

        """
        #: Workspace directory for prepared artifacts.
        self.output_dir = output_dir

    def write(self, seeds: Sequence[BTAnchorSeed]) -> Path:
        """
        Serialize anchor seeds to ``anchors/anchor_seeds.jsonl``.

        Args:
            seeds: Anchor seed records to serialize.

        Returns:
            Path to the written anchor seed manifest.

        Side Effects:
            Creates ``anchors/`` and writes UTF-8 JSONL rows sorted by
            ``region_id``.

        """
        path = self.output_dir / ANCHOR_SEEDS_REL
        sorted_seeds = sorted(seeds, key=lambda seed: seed.region_id)
        _write_jsonl(path, [seed.to_dict() for seed in sorted_seeds])
        return path
