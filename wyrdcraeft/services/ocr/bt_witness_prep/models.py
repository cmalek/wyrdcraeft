"""Typed contracts for Bosworth-Toller OCR witness preparation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


def format_page_id(source_path_or_stem: Path | str) -> str:
    """
    Build a stable page id from a source path or filename stem.

    Args:
        source_path_or_stem: Source scan path or bare filename stem.

    Returns:
        Lowercase slug derived from the filename stem, with spaces and
        underscores normalized to hyphens.

    """
    if isinstance(source_path_or_stem, Path):
        stem = source_path_or_stem.stem
    else:
        path = Path(source_path_or_stem)
        stem = path.stem if path.suffix else source_path_or_stem
    return stem.lower().replace(" ", "-").replace("_", "-")


def format_tile_id(page_id: str, column: int, part: int) -> str:
    """
    Build a stable tile id from page identity and split geometry.

    Args:
        page_id: Stable page identifier.
        column: One-based column index within the page layout.
        part: One-based part index within the column split.

    Returns:
        Deterministic tile id using ``col-N-part-M`` geometry.

    """
    return f"{page_id}:col-{column}-part-{part}"


@dataclass(frozen=True)
class BTWitnessPrepInput:
    """
    Input contract for one Bosworth-Toller witness preparation run.

    Args:
        source_dir: Directory containing source scan images.
        output_dir: Workspace directory for prepared artifacts.
        recipe_id: Preprocessing recipe identifier applied to every page.

    """

    #: Directory containing source scan images.
    source_dir: Path
    #: Workspace directory for prepared artifacts.
    output_dir: Path
    #: Preprocessing recipe identifier applied to every page.
    recipe_id: str

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the input contract to a JSON-friendly mapping.

        Returns:
            Dictionary suitable for ``json.dumps``.

        """
        return {
            "source_dir": str(self.source_dir),
            "output_dir": str(self.output_dir),
            "recipe_id": self.recipe_id,
        }


@dataclass(frozen=True)
class BTSourcePage:
    """
    Provenance record for one source scan page before preprocessing.

    Args:
        source_path: Original scan image path.
        page_id: Stable page identifier derived from source identity.
        recipe_id: Preprocessing recipe identifier for this page.
        width_px: Source image width in pixels.
        height_px: Source image height in pixels.

    """

    #: Original scan image path.
    source_path: Path
    #: Stable page identifier derived from source identity.
    page_id: str
    #: Preprocessing recipe identifier for this page.
    recipe_id: str
    #: Source image width in pixels.
    width_px: int
    #: Source image height in pixels.
    height_px: int

    @staticmethod
    def page_id_for(source_path: Path) -> str:
        """
        Derive the stable page id for one source scan path.

        Args:
            source_path: Original scan image path.

        Returns:
            Stable page identifier for the source file.

        """
        return format_page_id(source_path)

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the source page record to a JSON-friendly mapping.

        Returns:
            Dictionary suitable for ``json.dumps``.

        """
        return {
            "source_path": str(self.source_path),
            "page_id": self.page_id,
            "recipe_id": self.recipe_id,
            "width_px": self.width_px,
            "height_px": self.height_px,
        }


@dataclass(frozen=True)
class BTPreprocessedPage:
    """
    Provenance record for one preprocessed full-page image.

    Args:
        source_path: Original scan image path.
        page_id: Stable page identifier for the source page.
        recipe_id: Preprocessing recipe identifier applied to this page.
        image_path: Prepared full-page image path.
        crop_box: Pixel crop box as ``(left, top, right, bottom)``.
        width_px: Prepared image width in pixels.
        height_px: Prepared image height in pixels.
        status: Optional preprocessing status for non-standard pages.

    """

    #: Original scan image path.
    source_path: Path
    #: Stable page identifier for the source page.
    page_id: str
    #: Preprocessing recipe identifier applied to this page.
    recipe_id: str
    #: Prepared full-page image path.
    image_path: Path
    #: Pixel crop box as ``(left, top, right, bottom)``.
    crop_box: tuple[int, int, int, int]
    #: Prepared image width in pixels.
    width_px: int
    #: Prepared image height in pixels.
    height_px: int
    #: Optional preprocessing status for non-standard pages.
    status: str = "ready"

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the preprocessed page record to a JSON-friendly mapping.

        Returns:
            Dictionary suitable for ``json.dumps``.

        """
        return {
            "source_path": str(self.source_path),
            "page_id": self.page_id,
            "recipe_id": self.recipe_id,
            "image_path": str(self.image_path),
            "crop_box": list(self.crop_box),
            "width_px": self.width_px,
            "height_px": self.height_px,
            "status": self.status,
        }


@dataclass(frozen=True)
class BTTileQuality:
    """
    Quality metadata for one prepared tile.

    Numeric scores are documented on the 0.0-1.0 scale where higher is better.
    Contamination and clipping scores also use higher-is-better semantics, meaning
    less contamination or clipping.

    Args:
        status: Tile readiness status such as ``ready`` or ``fallback``.
        notes: Optional human-readable quality notes.
        stroke_contrast_score: Stroke contrast readability score.
        focus_score: Focus or edge-sharpness score.
        small_component_preservation_score: Preservation score for punctuation-
            sized connected components.
        line_separability_score: Horizontal line separation score.
        column_contamination_score: Column isolation score with higher values
            meaning less neighboring-column contamination.
        margin_clipping_score: Margin preservation score with higher values
            meaning less edge clipping.
        composite_score: Weighted tile readability composite score.
        small_component_guardrail_failed: Whether catastrophic small-component
            loss triggered the readability guardrail.

    """

    #: Tile readiness status such as ``ready`` or ``fallback``.
    status: str
    #: Optional human-readable quality notes.
    notes: tuple[str, ...] = ()
    #: Stroke contrast readability score on ``0.0``-``1.0``.
    stroke_contrast_score: float | None = None
    #: Focus or edge-sharpness score on ``0.0``-``1.0``.
    focus_score: float | None = None
    #: Preservation score for punctuation-sized connected components.
    small_component_preservation_score: float | None = None
    #: Horizontal line separation score on ``0.0``-``1.0``.
    line_separability_score: float | None = None
    #: Column isolation score where higher means less contamination.
    column_contamination_score: float | None = None
    #: Margin preservation score where higher means less clipping.
    margin_clipping_score: float | None = None
    #: Weighted tile readability composite score on ``0.0``-``1.0``.
    composite_score: float | None = None
    #: Whether catastrophic small-component loss triggered the guardrail.
    small_component_guardrail_failed: bool = False

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize tile quality metadata to a JSON-friendly mapping.

        Returns:
            Dictionary suitable for ``json.dumps``.

        """
        return {
            "status": self.status,
            "notes": list(self.notes),
            "stroke_contrast_score": self.stroke_contrast_score,
            "focus_score": self.focus_score,
            "small_component_preservation_score": (
                self.small_component_preservation_score
            ),
            "line_separability_score": self.line_separability_score,
            "column_contamination_score": self.column_contamination_score,
            "margin_clipping_score": self.margin_clipping_score,
            "composite_score": self.composite_score,
            "small_component_guardrail_failed": (
                self.small_component_guardrail_failed
            ),
        }


@dataclass(frozen=True)
class BTTile:
    """
    Provenance record for one prepared OCR tile.

    Args:
        source_path: Original scan image path.
        page_id: Stable page identifier for the source page.
        recipe_id: Preprocessing recipe identifier applied to this tile.
        tile_id: Stable tile identifier derived from page and split geometry.
        image_path: Prepared tile image path.
        column: One-based column index within the page layout.
        part: One-based part index within the column split.
        crop_box: Pixel crop box as ``(left, top, right, bottom)`` relative to
            the preprocessed page image.
        width_px: Tile image width in pixels.
        height_px: Tile image height in pixels.
        quality: Tile quality metadata.
        overlap_px: Vertical overlap extent shared with adjacent parts in the
            same column.
        overlaps_tile_ids: Stable tile ids of vertically overlapping neighbors.

    """

    #: Original scan image path.
    source_path: Path
    #: Stable page identifier for the source page.
    page_id: str
    #: Preprocessing recipe identifier applied to this tile.
    recipe_id: str
    #: Stable tile identifier derived from page and split geometry.
    tile_id: str
    #: Prepared tile image path.
    image_path: Path
    #: One-based column index within the page layout.
    column: int
    #: One-based part index within the column split.
    part: int
    #: Pixel crop box relative to the preprocessed page image.
    crop_box: tuple[int, int, int, int]
    #: Tile image width in pixels.
    width_px: int
    #: Tile image height in pixels.
    height_px: int
    #: Tile quality metadata.
    quality: BTTileQuality
    #: Vertical overlap extent shared with adjacent parts in the same column.
    overlap_px: int = 0
    #: Stable tile ids of vertically overlapping neighbors.
    overlaps_tile_ids: tuple[str, ...] = ()

    @staticmethod
    def tile_id_for(page_id: str, column: int, part: int) -> str:
        """
        Derive the stable tile id for one page split geometry.

        Args:
            page_id: Stable page identifier.
            column: One-based column index within the page layout.
            part: One-based part index within the column split.

        Returns:
            Stable tile identifier for the split geometry.

        """
        return format_tile_id(page_id, column, part)

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the tile record to a JSON-friendly mapping.

        Returns:
            Dictionary suitable for ``json.dumps``.

        """
        return {
            "source_path": str(self.source_path),
            "page_id": self.page_id,
            "recipe_id": self.recipe_id,
            "tile_id": self.tile_id,
            "image_path": str(self.image_path),
            "column": self.column,
            "part": self.part,
            "crop_box": list(self.crop_box),
            "width_px": self.width_px,
            "height_px": self.height_px,
            "quality": self.quality.to_dict(),
            "overlap_px": self.overlap_px,
            "overlaps_tile_ids": list(self.overlaps_tile_ids),
        }


@dataclass(frozen=True)
class BTAnchorSeed:
    """
    Anchor seed for one page or tile region in witness preparation.

    Args:
        source_path: Original scan image path.
        page_id: Stable page identifier for the source page.
        tile_id: Stable tile identifier containing the anchor region.
        region_id: Stable region identifier, usually matching ``tile_id``.
        region_type: Region classification such as ``column_half_tile``.
        crop_box: Pixel crop box as ``(left, top, right, bottom)``.
        parent_region_id: Parent region identifier, usually the page id.
        label: Optional anchor label such as ``headword`` or ``sense``.
        text: Optional anchor text content.
        line_number: Optional one-based line index placeholder.
        line_text: Optional line text placeholder.

    """

    #: Original scan image path.
    source_path: Path
    #: Stable page identifier for the source page.
    page_id: str
    #: Stable tile identifier containing the anchor region.
    tile_id: str
    #: Stable region identifier, usually matching ``tile_id``.
    region_id: str
    #: Region classification such as ``column_half_tile``.
    region_type: str
    #: Pixel crop box as ``(left, top, right, bottom)``.
    crop_box: tuple[int, int, int, int]
    #: Parent region identifier, usually the page id.
    parent_region_id: str | None = None
    #: Optional anchor label such as ``headword`` or ``sense``.
    label: str = ""
    #: Optional anchor text content.
    text: str = ""
    #: Optional one-based line index placeholder.
    line_number: int | None = None
    #: Optional line text placeholder.
    line_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the anchor seed to a JSON-friendly mapping.

        Returns:
            Dictionary suitable for ``json.dumps``.

        """
        return {
            "source_path": str(self.source_path),
            "page_id": self.page_id,
            "tile_id": self.tile_id,
            "region_id": self.region_id,
            "region_type": self.region_type,
            "parent_region_id": self.parent_region_id,
            "crop_box": list(self.crop_box),
            "label": self.label,
            "text": self.text,
            "line_number": self.line_number,
            "line_text": self.line_text,
        }


@dataclass(frozen=True)
class BTWitnessPrepRun:
    """
    Manifest contract for one Bosworth-Toller witness preparation run.

    Args:
        prep_input: Run input contract.
        source_pages: Source page provenance records.
        preprocessed_pages: Preprocessed full-page provenance records.
        tiles: Prepared tile provenance records.
        anchor_seeds: Anchor seeds extracted from prepared tiles.

    """

    #: Run input contract.
    prep_input: BTWitnessPrepInput
    #: Source page provenance records.
    source_pages: tuple[BTSourcePage, ...]
    #: Preprocessed full-page provenance records.
    preprocessed_pages: tuple[BTPreprocessedPage, ...]
    #: Prepared tile provenance records.
    tiles: tuple[BTTile, ...]
    #: Anchor seeds extracted from prepared tiles.
    anchor_seeds: tuple[BTAnchorSeed, ...]

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the run manifest to a JSON-friendly mapping.

        Returns:
            Dictionary suitable for ``json.dumps``.

        """
        return {
            "prep_input": self.prep_input.to_dict(),
            "source_pages": [page.to_dict() for page in self.source_pages],
            "preprocessed_pages": [
                page.to_dict() for page in self.preprocessed_pages
            ],
            "tiles": [tile.to_dict() for tile in self.tiles],
            "anchor_seeds": [anchor.to_dict() for anchor in self.anchor_seeds],
        }
