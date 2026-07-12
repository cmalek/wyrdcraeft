"""End-to-end orchestration for Bosworth-Toller OCR witness preparation."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from wyrdcraeft.services.ocr.bt_witness_prep.anchors import (
    BTAnchorSeedBuilder,
    BTAnchorSeedWriter,
)
from wyrdcraeft.services.ocr.bt_witness_prep.manifest import BTWitnessManifestWriter
from wyrdcraeft.services.ocr.bt_witness_prep.models import (
    BTPreprocessedPage,
    BTSourcePage,
    BTTile,
    BTWitnessPrepInput,
    BTWitnessPrepRun,
)
from wyrdcraeft.services.ocr.bt_witness_prep.preprocess import (
    BTPagePreprocessor,
    BTPreprocessRecipe,
)
from wyrdcraeft.services.ocr.bt_witness_prep.quality import (
    BTTileQualityScorer,
    BTTileScoreContext,
)
from wyrdcraeft.services.ocr.bt_witness_prep.source import BTSourcePageEnumerator
from wyrdcraeft.services.ocr.bt_witness_prep.tiling import (
    BTPageTiler,
    BTTilingConfig,
)

#: Relative directory for preprocessed full-page images.
PAGES_OUTPUT_DIR = Path("pages")
#: Relative directory for prepared tile images.
TILES_OUTPUT_DIR = Path("tiles")
#: Tile readiness status that receives quality scoring.
_READY_TILE_STATUS = "ready"


class BTWitnessPrepPipeline:
    """
    Orchestrate enumerate → preprocess → tile → score → manifest for BT scans.

    Args:
        recipe: Preprocessing recipe applied to every source page.
        tiling_config: Tiling contract for standard two-column dictionary pages.
        quality_scorer: Scorer that populates readability metrics on ready tiles.

    """

    def __init__(
        self,
        *,
        recipe: BTPreprocessRecipe | None = None,
        tiling_config: BTTilingConfig | None = None,
        quality_scorer: BTTileQualityScorer | None = None,
    ) -> None:
        """
        Initialize one pipeline with default or injected collaborators.

        Keyword Args:
            recipe: Preprocessing recipe applied to every source page.
            tiling_config: Tiling contract for standard two-column pages.
            quality_scorer: Scorer for ready tile readability metrics.

        """
        resolved_recipe = recipe or BTPreprocessRecipe.conservative_default(
            "bt-two-column-v1",
        )
        resolved_tiling = tiling_config or BTTilingConfig.standard_two_column()
        #: Preprocessing recipe applied to every source page.
        self._recipe = resolved_recipe
        #: Tiling contract for standard two-column dictionary pages.
        self._tiling_config = resolved_tiling
        #: Scorer that populates readability metrics on ready tiles.
        self._quality_scorer = quality_scorer or BTTileQualityScorer()
        #: Enumerates JP2 source pages from one scan directory.
        self._enumerator = BTSourcePageEnumerator(resolved_recipe.recipe_id)
        #: Prepares conservative full-page grayscale images.
        self._preprocessor = BTPagePreprocessor(resolved_recipe)
        #: Splits prepared pages into OCR tiles or explicit fallback regions.
        self._tiler = BTPageTiler(resolved_tiling)
        #: Derives anchor seeds from prepared tile regions.
        self._anchor_builder = BTAnchorSeedBuilder()

    def prepare(self, prep_input: BTWitnessPrepInput) -> BTWitnessPrepRun:
        """
        Run witness preparation for every JP2 page in the input source directory.

        Side Effects:
            Writes page and tile images plus JSONL manifests under
            ``prep_input.output_dir``.

        Args:
            prep_input: Source directory, output workspace, and recipe identity.

        Returns:
            Typed run manifest with source, page, tile, and anchor provenance.

        """
        output_dir = prep_input.output_dir.resolve()
        pages_dir = output_dir / PAGES_OUTPUT_DIR
        tiles_dir = output_dir / TILES_OUTPUT_DIR

        # Align recipe identity with the run input when callers construct the
        # pipeline without an explicit recipe (direct class usage).
        if prep_input.recipe_id != self._recipe.recipe_id:
            recipe = BTPreprocessRecipe.conservative_default(prep_input.recipe_id)
            enumerator = BTSourcePageEnumerator(prep_input.recipe_id)
            preprocessor = BTPagePreprocessor(recipe)
        else:
            enumerator = self._enumerator
            preprocessor = self._preprocessor

        source_pages = _filter_source_pages(
            enumerator.enumerate(prep_input.source_dir),
            page_ids=prep_input.page_ids,
            limit=prep_input.limit,
        )
        tiling_config = self._tiling_config
        if prep_input.overlap_px is not None:
            tiling_config = replace(tiling_config, overlap_px=prep_input.overlap_px)
        tiler = (
            self._tiler
            if tiling_config.overlap_px == self._tiling_config.overlap_px
            else BTPageTiler(tiling_config)
        )
        preprocessed_pages: list[BTPreprocessedPage] = []
        all_tiles: list[BTTile] = []

        for source_page in source_pages:
            preprocessed = preprocessor.preprocess(source_page, pages_dir)
            tiled_page, tiles = tiler.tile(preprocessed, tiles_dir)
            scored_tiles = self._score_tiles(
                tiled_page,
                tiles,
                column_gutter_px=tiling_config.column_gutter_px,
            )
            preprocessed_pages.append(tiled_page)
            all_tiles.extend(scored_tiles)

        manifest_writer = BTWitnessManifestWriter(output_dir)
        manifest_writer.write_pages(preprocessed_pages)
        manifest_writer.write_tiles(all_tiles)

        anchor_seeds = self._anchor_builder.build_from_tiles(all_tiles)
        BTAnchorSeedWriter(output_dir).write(anchor_seeds)

        return BTWitnessPrepRun(
            prep_input=prep_input,
            source_pages=tuple(source_pages),
            preprocessed_pages=tuple(preprocessed_pages),
            tiles=tuple(all_tiles),
            anchor_seeds=anchor_seeds,
        )

    def _score_tiles(
        self,
        page: BTPreprocessedPage,
        tiles: tuple[BTTile, ...],
        *,
        column_gutter_px: int,
    ) -> tuple[BTTile, ...]:
        """
        Score ready tiles while preserving explicit fallback quality metadata.

        Args:
            page: Preprocessed page that owns the tile crop geometry.
            tiles: Prepared tile records emitted by the tiler.

        Keyword Args:
            column_gutter_px: Horizontal gutter width used for contamination scoring.

        Returns:
            Tiles with populated quality metrics for ready regions only.

        """
        scored: list[BTTile] = []
        for tile in tiles:
            if tile.quality.status != _READY_TILE_STATUS:
                scored.append(tile)
                continue
            quality = self._quality_scorer.score_image(
                tile.image_path,
                context=BTTileScoreContext(
                    column=tile.column,
                    crop_box=tile.crop_box,
                    page_width_px=page.width_px,
                    page_height_px=page.height_px,
                    column_gutter_px=column_gutter_px,
                ),
                status=_READY_TILE_STATUS,
            )
            scored.append(replace(tile, quality=quality))
        return tuple(scored)


def prepare_pages(input_config: BTWitnessPrepInput) -> BTWitnessPrepRun:
    """
    Prepare Bosworth-Toller witness pages from one input configuration.

    Side Effects:
        Writes page and tile images plus JSONL manifests under
        ``input_config.output_dir``.

    Args:
        input_config: Source directory, output workspace, and recipe identity.

    Returns:
        Typed run manifest with source, page, tile, and anchor provenance.

    """
    recipe = BTPreprocessRecipe.conservative_default(input_config.recipe_id)
    tiling_config = BTTilingConfig.standard_two_column()
    if input_config.overlap_px is not None:
        tiling_config = replace(tiling_config, overlap_px=input_config.overlap_px)
    return BTWitnessPrepPipeline(recipe=recipe, tiling_config=tiling_config).prepare(
        input_config,
    )


def _filter_source_pages(
    source_pages: list[BTSourcePage],
    *,
    page_ids: tuple[str, ...] | None,
    limit: int | None,
) -> list[BTSourcePage]:
    """
    Filter enumerated source pages in memory for one witness-prep run.

    Args:
        source_pages: Enumerated JP2 source pages in stable filename order.

    Keyword Args:
        page_ids: Optional ``page_id`` slugs to keep.
        limit: Optional maximum page count applied after ``page_ids`` filtering.

    Raises:
        ValueError: When filtering removes every source page.

    Returns:
        Filtered source pages in stable order.

    """
    filtered = source_pages
    if page_ids is not None:
        allowed = {page_id.strip().lower() for page_id in page_ids if page_id.strip()}
        filtered = [page for page in filtered if page.page_id in allowed]
    if limit is not None:
        filtered = filtered[:limit]
    if not filtered:
        if page_ids is not None:
            requested = ", ".join(page_id.strip().lower() for page_id in page_ids)
            message = f"No JP2 pages matched requested page_ids: {requested}"
            raise ValueError(message)
        message = "No JP2 pages remain after page filtering"
        raise ValueError(message)
    return filtered
