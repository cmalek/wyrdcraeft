"""JSONL manifest writers for Bosworth-Toller witness preparation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wyrdcraeft.services.ocr.bt_witness_prep.models import (
        BTPreprocessedPage,
        BTTile,
    )

#: Relative path for the page manifest under the witness-prep output dir.
PAGES_MANIFEST_REL = Path("manifests/pages.jsonl")
#: Relative path for the tile manifest under the witness-prep output dir.
TILES_MANIFEST_REL = Path("manifests/tiles.jsonl")


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


class BTWitnessManifestWriter:
    """
    Write page and tile manifests for one witness preparation run.

    Args:
        output_dir: Workspace directory for prepared artifacts.

    """

    def __init__(self, output_dir: Path) -> None:
        """
        Initialize one manifest writer for a witness-prep output directory.

        Args:
            output_dir: Workspace directory for prepared artifacts.

        """
        #: Workspace directory for prepared artifacts.
        self.output_dir = output_dir

    def write_pages(self, pages: Sequence[BTPreprocessedPage]) -> Path:
        """
        Serialize preprocessed page provenance to ``manifests/pages.jsonl``.

        Args:
            pages: Preprocessed page records to serialize.

        Returns:
            Path to the written page manifest.

        Side Effects:
            Creates ``manifests/`` and writes UTF-8 JSONL rows sorted by
            ``page_id``.

        """
        path = self.output_dir / PAGES_MANIFEST_REL
        sorted_pages = sorted(pages, key=lambda page: page.page_id)
        _write_jsonl(path, [page.to_dict() for page in sorted_pages])
        return path

    def write_tiles(self, tiles: Sequence[BTTile]) -> Path:
        """
        Serialize tile provenance to ``manifests/tiles.jsonl``.

        Args:
            tiles: Prepared tile records to serialize.

        Returns:
            Path to the written tile manifest.

        Side Effects:
            Creates ``manifests/`` and writes UTF-8 JSONL rows sorted by
            ``tile_id``.

        """
        path = self.output_dir / TILES_MANIFEST_REL
        sorted_tiles = sorted(tiles, key=lambda tile: tile.tile_id)
        _write_jsonl(path, [tile.to_dict() for tile in sorted_tiles])
        return path
