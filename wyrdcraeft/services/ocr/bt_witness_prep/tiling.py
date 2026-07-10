"""Fixed four-tile page splitting for Bosworth-Toller witness preparation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from PIL import Image

from wyrdcraeft.services.ocr.bt_witness_prep.models import (
    BTPreprocessedPage,
    BTTile,
    BTTileQuality,
)

if TYPE_CHECKING:
    from pathlib import Path

#: Pixel crop box as ``(left, top, right, bottom)`` in preprocessed-page coords.
CropBox = tuple[int, int, int, int]
#: One-based upper part index within a column split.
_UPPER_PART = 1
#: One-based lower part index within a column split.
_LOWER_PART = 2


@dataclass(frozen=True)
class BTTilingConfig:
    """
    Deterministic tiling contract for standard Bosworth-Toller dictionary pages.

    Args:
        overlap_px: Vertical overlap between upper and lower parts in one column.
        column_gutter_px: Horizontal inset from the page midline that keeps
            column tiles from crossing into the neighboring column.
        min_page_width_px: Minimum preprocessed page width required for a
            two-column split.
        min_page_height_px: Minimum preprocessed page height required for an
            upper/lower split.
        min_aspect_ratio: Minimum width-to-height ratio accepted for tiling.
        max_aspect_ratio: Maximum width-to-height ratio accepted for tiling.

    """

    #: Vertical overlap between upper and lower parts in one column.
    overlap_px: int = 30
    #: Horizontal inset from the page midline for column isolation.
    column_gutter_px: int = 10
    #: Minimum preprocessed page width required for a two-column split.
    min_page_width_px: int = 180
    #: Minimum preprocessed page height required for an upper/lower split.
    min_page_height_px: int = 120
    #: Minimum width-to-height ratio accepted for tiling.
    min_aspect_ratio: float = 0.45
    #: Maximum width-to-height ratio accepted for tiling.
    max_aspect_ratio: float = 1.2

    @staticmethod
    def standard_two_column() -> BTTilingConfig:
        """
        Build the default tiling contract for two-column dictionary pages.

        Returns:
            Default tiling configuration for Bosworth-Toller scans.

        """
        return BTTilingConfig()


class BTPageTiler:
    """
    Split one preprocessed Bosworth-Toller page into four OCR tiles.

    Tile crop boxes are expressed in coordinates relative to the preprocessed
    page image, not the original source scan.

    Args:
        config: Frozen tiling configuration applied to every page.

    """

    def __init__(self, config: BTTilingConfig) -> None:
        """
        Initialize one tiler for a tiling configuration.

        Args:
            config: Frozen tiling configuration applied to every page.

        """
        #: Frozen tiling configuration applied to every page.
        self._config = config

    def tile(
        self,
        page: BTPreprocessedPage,
        output_dir: Path,
    ) -> tuple[BTPreprocessedPage, tuple[BTTile, ...]]:
        """
        Split one preprocessed page into tiles and write tile image files.

        Side Effects:
            Creates ``output_dir`` when missing and writes tile PNG artifacts.

        Args:
            page: Preprocessed full-page provenance record to split.
            output_dir: Directory that receives prepared tile images.

        Returns:
            Updated page status plus prepared tile provenance records.

        """
        resolved_output_dir = output_dir.resolve()
        resolved_output_dir.mkdir(parents=True, exist_ok=True)

        fallback_status = _fallback_status_for(page, self._config)
        if fallback_status is not None:
            return self._emit_fallback(page, resolved_output_dir, fallback_status)

        column_boxes = _column_boxes(page.width_px, self._config)
        part_boxes = _part_boxes(page.height_px, self._config.overlap_px)
        tiles = self._emit_standard_tiles(
            page,
            resolved_output_dir,
            column_boxes,
            part_boxes,
        )
        return replace(page, status="ready"), tiles

    def _emit_standard_tiles(
        self,
        page: BTPreprocessedPage,
        output_dir: Path,
        column_boxes: tuple[CropBox, CropBox],
        part_boxes: tuple[CropBox, CropBox],
    ) -> tuple[BTTile, ...]:
        """
        Build and write the four standard tiles for one ready page.

        Side Effects:
            Writes four tile PNG artifacts under ``output_dir``.

        Args:
            page: Preprocessed full-page provenance record to split.
            output_dir: Directory that receives prepared tile images.
            column_boxes: Left and right column bounds in page coordinates.
            part_boxes: Upper and lower part bounds in page coordinates.

        Returns:
            Prepared tile provenance records in stable geometry order.

        """
        overlap_px = self._config.overlap_px
        with Image.open(page.image_path) as page_image:
            tiles: list[BTTile] = []
            for column, column_box in enumerate(column_boxes, start=1):
                for part, part_box in enumerate(part_boxes, start=1):
                    crop_box = _combine_boxes(column_box, part_box)
                    tile_id = BTTile.tile_id_for(page.page_id, column, part)
                    filename = f"{page.page_id}-col-{column}-part-{part}.png"
                    image_path = output_dir / filename
                    tile_image = page_image.crop(crop_box)
                    tile_image.save(image_path, format="PNG")
                    width_px, height_px = tile_image.size
                    tiles.append(
                        BTTile(
                            source_path=page.source_path,
                            page_id=page.page_id,
                            recipe_id=page.recipe_id,
                            tile_id=tile_id,
                            image_path=image_path,
                            column=column,
                            part=part,
                            crop_box=crop_box,
                            width_px=width_px,
                            height_px=height_px,
                            quality=BTTileQuality(status="ready"),
                            overlap_px=0,
                            overlaps_tile_ids=(),
                        ),
                    )

        return _attach_overlap_links(tuple(tiles), overlap_px)

    def _emit_fallback(
        self,
        page: BTPreprocessedPage,
        output_dir: Path,
        page_status: str,
    ) -> tuple[BTPreprocessedPage, tuple[BTTile, ...]]:
        """
        Emit one whole-page fallback tile for a non-standard page.

        Side Effects:
            Writes one fallback tile PNG artifact under ``output_dir``.

        Args:
            page: Preprocessed page that cannot be split safely.
            output_dir: Directory that receives the fallback tile image.
            page_status: Explicit page-level fallback status to record.

        Returns:
            Updated page status plus one fallback tile provenance record.

        """
        crop_box = (0, 0, page.width_px, page.height_px)
        tile_id = f"{page.page_id}:whole-page"
        image_path = output_dir / f"{page.page_id}-whole-page.png"
        with Image.open(page.image_path) as page_image:
            page_image.save(image_path, format="PNG")

        tile = BTTile(
            source_path=page.source_path,
            page_id=page.page_id,
            recipe_id=page.recipe_id,
            tile_id=tile_id,
            image_path=image_path,
            column=0,
            part=0,
            crop_box=crop_box,
            width_px=page.width_px,
            height_px=page.height_px,
            quality=BTTileQuality(status="fallback", notes=(page_status,)),
            overlap_px=0,
            overlaps_tile_ids=(),
        )
        return replace(page, status=page_status), (tile,)


def tile_preprocessed_page(
    page: BTPreprocessedPage,
    output_dir: Path,
    config: BTTilingConfig,
) -> tuple[BTPreprocessedPage, tuple[BTTile, ...]]:
    """
    Split one preprocessed page with a tiling configuration.

    Side Effects:
        Creates ``output_dir`` when missing and writes tile PNG artifacts.

    Args:
        page: Preprocessed full-page provenance record to split.
        output_dir: Directory that receives prepared tile images.
        config: Frozen tiling configuration applied to the page.

    Returns:
        Updated page status plus prepared tile provenance records.

    """
    return BTPageTiler(config).tile(page, output_dir)


def _fallback_status_for(
    page: BTPreprocessedPage,
    config: BTTilingConfig,
) -> str | None:
    """
    Decide whether one page must use explicit fallback tiling.

    Args:
        page: Preprocessed page candidate for four-tile splitting.
        config: Tiling configuration containing layout guardrails.

    Returns:
        Explicit fallback status, or ``None`` when standard tiling applies.

    """
    if page.status != "ready":
        return page.status

    if page.width_px < config.min_page_width_px:
        return "fallback_whole_page_only"

    if page.height_px < config.min_page_height_px:
        return "fallback_whole_page_only"

    aspect_ratio = page.width_px / page.height_px
    if aspect_ratio < config.min_aspect_ratio or aspect_ratio > config.max_aspect_ratio:
        return "unsupported_layout"

    gutter_half = config.column_gutter_px // 2
    midline = page.width_px // 2
    if (midline - gutter_half) < 1 or (page.width_px - (midline + gutter_half)) < 1:
        return "unsupported_layout"

    return None


def _column_boxes(width_px: int, config: BTTilingConfig) -> tuple[CropBox, CropBox]:
    """
    Compute left and right column bounds with a midline gutter.

    Args:
        width_px: Preprocessed page width in pixels.
        config: Tiling configuration containing the column gutter.

    Returns:
        Column bounds as ``(left, top, right, bottom)`` page-coordinate boxes.

    """
    gutter_half = config.column_gutter_px // 2
    midline = width_px // 2
    left_column = (0, 0, midline - gutter_half, 0)
    right_column = (midline + gutter_half, 0, width_px, 0)
    return left_column, right_column


def _part_boxes(height_px: int, overlap_px: int) -> tuple[CropBox, CropBox]:
    """
    Compute upper and lower part bounds with vertical overlap.

    Args:
        height_px: Preprocessed page height in pixels.
        overlap_px: Vertical overlap shared by adjacent parts.

    Returns:
        Part bounds as ``(left, top, right, bottom)`` page-coordinate boxes.

    """
    half = height_px // 2
    overlap_half = overlap_px // 2
    upper = (0, 0, 0, half + overlap_half)
    lower = (0, half - overlap_half, 0, height_px)
    return upper, lower


def _combine_boxes(column_box: CropBox, part_box: CropBox) -> CropBox:
    """
    Combine one column box and one part box into a tile crop box.

    Args:
        column_box: Column bounds with horizontal edges populated.
        part_box: Part bounds with vertical edges populated.

    Returns:
        Tile crop box relative to the preprocessed page image.

    """
    col_left, _, col_right, _ = column_box
    _, part_top, _, part_bottom = part_box
    return (col_left, part_top, col_right, part_bottom)


def _attach_overlap_links(
    tiles: tuple[BTTile, ...],
    overlap_px: int,
) -> tuple[BTTile, ...]:
    """
    Populate overlap metadata for vertically adjacent tiles.

    Args:
        tiles: Standard tiles in stable geometry order.
        overlap_px: Vertical overlap shared by adjacent parts.

    Returns:
        Tiles with ``overlaps_tile_ids`` populated for vertical neighbors.

    """
    by_geometry = {(tile.column, tile.part): tile for tile in tiles}
    linked: list[BTTile] = []
    for tile in tiles:
        if tile.part == _UPPER_PART:
            neighbor = by_geometry[(tile.column, _LOWER_PART)]
            linked.append(
                replace(
                    tile,
                    overlap_px=overlap_px,
                    overlaps_tile_ids=(neighbor.tile_id,),
                ),
            )
            continue
        if tile.part == _LOWER_PART:
            neighbor = by_geometry[(tile.column, _UPPER_PART)]
            linked.append(
                replace(
                    tile,
                    overlap_px=overlap_px,
                    overlaps_tile_ids=(neighbor.tile_id,),
                ),
            )
            continue
        linked.append(tile)
    return tuple(linked)
