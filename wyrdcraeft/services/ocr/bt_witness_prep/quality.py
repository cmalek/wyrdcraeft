"""Deterministic tile quality metrics for Bosworth-Toller witness preparation."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from wyrdcraeft.services.ocr.bt_witness_prep.models import BTTileQuality

#: Pixel crop box as ``(left, top, right, bottom)`` in preprocessed-page coords.
CropBox = tuple[int, int, int, int]
#: Ink threshold for grayscale tiles; darker pixels count as ink.
_INK_THRESHOLD = 200
#: Robust contrast spread mapped to a ``1.0`` score.
_STROKE_CONTRAST_SCALE = 200.0
#: Laplacian variance mapped to a ``1.0`` focus score.
_FOCUS_VARIANCE_SCALE = 500.0
#: Minimum connected-component area counted as punctuation-sized ink.
_SMALL_COMPONENT_MIN_AREA = 1
#: Maximum connected-component area counted as punctuation-sized ink.
_SMALL_COMPONENT_MAX_AREA = 16
#: Reference small-component count used to normalize preservation scores.
_SMALL_COMPONENT_REFERENCE_COUNT = 6.0
#: Small-component preservation threshold that triggers the guardrail.
_SMALL_COMPONENT_GUARDRAIL_THRESHOLD = 0.35
#: Maximum composite score allowed when the guardrail fails.
_GUARDRAIL_COMPOSITE_CAP = 0.55
#: Row-normalized ink threshold that marks text-line bands.
_LINE_INK_THRESHOLD = 0.30
#: Row-normalized ink threshold that marks active projection rows.
_LINE_ACTIVE_THRESHOLD = 0.01
#: One-based column index for the right-hand page column.
_RIGHT_COLUMN_INDEX = 2
#: Expected dimensionality for grayscale tile arrays.
_GRAYSCALE_ARRAY_DIMENSIONS = 2
#: Maximum distinct line-band count treated as a single block.
_SINGLE_LINE_RUN_COUNT = 1
#: Composite readability weights documented for witness-prep review.
_COMPOSITE_WEIGHTS = {
    "stroke_contrast_score": 0.30,
    "focus_score": 0.20,
    "small_component_preservation_score": 0.20,
    "line_separability_score": 0.15,
    "column_contamination_score": 0.10,
    "margin_clipping_score": 0.05,
}


@dataclass(frozen=True)
class BTTileScoreContext:
    """
    Page geometry context used when scoring one prepared tile.

    Args:
        column: One-based column index within the page layout.
        crop_box: Tile crop box relative to the preprocessed page image.
        page_width_px: Preprocessed page width in pixels.
        page_height_px: Preprocessed page height in pixels.
        column_gutter_px: Horizontal gutter width between page columns.

    """

    #: One-based column index within the page layout.
    column: int
    #: Tile crop box relative to the preprocessed page image.
    crop_box: CropBox
    #: Preprocessed page width in pixels.
    page_width_px: int
    #: Preprocessed page height in pixels.
    page_height_px: int
    #: Horizontal gutter width between page columns.
    column_gutter_px: int = 10


@dataclass(frozen=True)
class BTTileMetricValues:
    """
    Individual metric scores combined into the readability composite.

    Args:
        stroke_contrast_score: Stroke contrast readability score.
        focus_score: Focus or edge-sharpness score.
        small_component_preservation_score: Preservation score for punctuation-
            sized connected components.
        line_separability_score: Horizontal line separation score.
        column_contamination_score: Column isolation score.
        margin_clipping_score: Margin preservation score.

    """

    #: Stroke contrast readability score.
    stroke_contrast_score: float
    #: Focus or edge-sharpness score.
    focus_score: float
    #: Preservation score for punctuation-sized connected components.
    small_component_preservation_score: float
    #: Horizontal line separation score.
    line_separability_score: float
    #: Column isolation score.
    column_contamination_score: float
    #: Margin preservation score.
    margin_clipping_score: float


@dataclass(frozen=True)
class BTTileQualityConfig:
    """
    Thresholds and normalization constants for tile quality scoring.

    Args:
        ink_threshold: Grayscale value below which pixels count as ink.
        stroke_contrast_scale: Robust contrast spread mapped to ``1.0``.
        focus_variance_scale: Laplacian variance mapped to a ``1.0`` focus score.
        small_component_min_area: Minimum punctuation-sized component area.
        small_component_max_area: Maximum punctuation-sized component area.
        small_component_reference_count: Reference count for normalization.
        small_component_guardrail_threshold: Preservation threshold for the
            guardrail.
        guardrail_composite_cap: Maximum composite score after guardrail failure.

    """

    #: Grayscale value below which pixels count as ink.
    ink_threshold: int = _INK_THRESHOLD
    #: Robust contrast spread mapped to ``1.0``.
    stroke_contrast_scale: float = _STROKE_CONTRAST_SCALE
    #: Laplacian variance mapped to a ``1.0`` focus score.
    focus_variance_scale: float = _FOCUS_VARIANCE_SCALE
    #: Minimum punctuation-sized component area.
    small_component_min_area: int = _SMALL_COMPONENT_MIN_AREA
    #: Maximum punctuation-sized component area.
    small_component_max_area: int = _SMALL_COMPONENT_MAX_AREA
    #: Reference count for small-component normalization.
    small_component_reference_count: float = _SMALL_COMPONENT_REFERENCE_COUNT
    #: Preservation threshold that triggers the guardrail.
    small_component_guardrail_threshold: float = _SMALL_COMPONENT_GUARDRAIL_THRESHOLD
    #: Maximum composite score after guardrail failure.
    guardrail_composite_cap: float = _GUARDRAIL_COMPOSITE_CAP


class BTTileQualityScorer:
    """
    Compute deterministic readability metrics for one prepared OCR tile.

    Args:
        config: Frozen scoring thresholds and normalization constants.

    """

    def __init__(self, config: BTTileQualityConfig | None = None) -> None:
        """
        Initialize one scorer for a scoring configuration.

        Args:
            config: Frozen scoring thresholds and normalization constants.

        """
        #: Frozen scoring thresholds and normalization constants.
        self._config = config or BTTileQualityConfig()

    def score_image(
        self,
        image: Image.Image | Path | np.ndarray,
        *,
        context: BTTileScoreContext,
        status: str = "ready",
    ) -> BTTileQuality:
        """
        Score one tile image and return populated quality metadata.

        Args:
            image: Prepared tile image as Pillow, path, or grayscale array.

        Keyword Args:
            context: Page geometry context for contamination heuristics.
            status: Tile readiness status to record on the result.

        Returns:
            Tile quality metadata with metric fields and composite score.

        """
        gray = _to_gray_array(image)
        stroke = stroke_contrast_score(gray, config=self._config)
        focus = focus_score(gray, config=self._config)
        small_components = small_component_preservation_score(
            gray,
            config=self._config,
        )
        separability = line_separability_score(gray, config=self._config)
        contamination = column_contamination_score(
            gray,
            context=context,
            config=self._config,
        )
        clipping = margin_clipping_score(gray, config=self._config)
        composite = composite_readability_score(
            BTTileMetricValues(
                stroke_contrast_score=stroke,
                focus_score=focus,
                small_component_preservation_score=small_components,
                line_separability_score=separability,
                column_contamination_score=contamination,
                margin_clipping_score=clipping,
            ),
        )
        return _apply_guardrail(
            BTTileQuality(
                status=status,
                stroke_contrast_score=stroke,
                focus_score=focus,
                small_component_preservation_score=small_components,
                line_separability_score=separability,
                column_contamination_score=contamination,
                margin_clipping_score=clipping,
                composite_score=composite,
            ),
            config=self._config,
        )


def stroke_contrast_score(
    image: Image.Image | np.ndarray,
    *,
    config: BTTileQualityConfig | None = None,
) -> float:
    """
    Score stroke contrast using a robust grayscale spread.

    Args:
        image: Prepared tile image as Pillow or grayscale array.

    Keyword Args:
        config: Optional scoring thresholds and normalization constants.

    Returns:
        Contrast score on ``0.0``-``1.0`` where higher is better.

    """
    resolved = config or BTTileQualityConfig()
    gray = _to_gray_array(image)
    low, high = np.percentile(gray, [10, 90])
    spread = float(high - low)
    return _clamp01(spread / resolved.stroke_contrast_scale)


def focus_score(
    image: Image.Image | np.ndarray,
    *,
    config: BTTileQualityConfig | None = None,
) -> float:
    """
    Score focus using Laplacian variance on the grayscale tile.

    Args:
        image: Prepared tile image as Pillow or grayscale array.

    Keyword Args:
        config: Optional scoring thresholds and normalization constants.

    Returns:
        Focus score on ``0.0``-``1.0`` where higher is sharper.

    """
    resolved = config or BTTileQualityConfig()
    gray = _to_gray_array(image)
    variance = _laplacian_variance(gray)
    return _clamp01(variance / resolved.focus_variance_scale)


def small_component_preservation_score(
    image: Image.Image | np.ndarray,
    *,
    config: BTTileQualityConfig | None = None,
) -> float:
    """
    Score preservation of punctuation-sized connected ink components.

    Args:
        image: Prepared tile image as Pillow or grayscale array.

    Keyword Args:
        config: Optional scoring thresholds and normalization constants.

    Returns:
        Preservation score on ``0.0``-``1.0`` where higher is better.

    """
    resolved = config or BTTileQualityConfig()
    gray = _to_gray_array(image)
    areas = _component_areas(_ink_mask(gray, resolved.ink_threshold))
    small_count = sum(
        1
        for area in areas
        if (
            resolved.small_component_min_area
            <= area
            <= resolved.small_component_max_area
        )
    )
    return _clamp01(small_count / resolved.small_component_reference_count)


def line_separability_score(
    image: Image.Image | np.ndarray,
    *,
    config: BTTileQualityConfig | None = None,
) -> float:
    """
    Score horizontal line separation using row-wise ink projections.

    Args:
        image: Prepared tile image as Pillow or grayscale array.

    Keyword Args:
        config: Optional scoring thresholds and normalization constants.

    Returns:
        Separability score on ``0.0``-``1.0`` where higher is better.

    """
    _ = config
    gray = _to_gray_array(image)
    projection = _ink_mask(gray).sum(axis=1).astype(np.float64)
    if projection.max() == 0:
        return 0.0

    smoothed = np.convolve(projection, np.ones(3, dtype=np.float64) / 3.0, mode="same")
    normalized = smoothed / smoothed.max()
    line_rows = normalized > _LINE_INK_THRESHOLD

    runs = 0
    in_run = False
    for is_line in line_rows:
        if is_line and not in_run:
            runs += 1
            in_run = True
        elif not is_line:
            in_run = False

    gap_score = (
        0.0
        if runs <= _SINGLE_LINE_RUN_COUNT
        else float((~line_rows).mean())
    )
    active = normalized[normalized > _LINE_ACTIVE_THRESHOLD]
    rhythm = float(active.std() / max(active.mean(), 0.01)) if active.size else 0.0
    multi_line_bonus = min(1.0, (runs - 1) / 3.0)
    return _clamp01(gap_score * 1.5 + rhythm * 0.5 + multi_line_bonus * 0.35)


def column_contamination_score(
    image: Image.Image | np.ndarray,
    *,
    context: BTTileScoreContext,
    config: BTTileQualityConfig | None = None,
) -> float:
    """
    Score column isolation using gutter-adjacent ink heuristics.

    Args:
        image: Prepared tile image as Pillow or grayscale array.

    Keyword Args:
        context: Page geometry context for contamination heuristics.
        config: Optional scoring thresholds and normalization constants.

    Returns:
        Isolation score on ``0.0``-``1.0`` where higher means less contamination.

    """
    _ = (context.crop_box, context.page_width_px, context.page_height_px)
    resolved = config or BTTileQualityConfig()
    gray = _to_gray_array(image)
    mask = _ink_mask(gray, resolved.ink_threshold)
    _height, width = mask.shape
    band = max(4, context.column_gutter_px + 4)

    if context.column == 1:
        edge_mask = mask[:, max(0, width - band) :]
    elif context.column == _RIGHT_COLUMN_INDEX:
        edge_mask = mask[:, : min(band, width)]
    else:
        return 1.0

    if edge_mask.size == 0:
        return 1.0

    contamination = float(edge_mask.mean())
    return _clamp01(1.0 - contamination * 5.0)


def margin_clipping_score(
    image: Image.Image | np.ndarray,
    *,
    config: BTTileQualityConfig | None = None,
) -> float:
    """
    Score margin preservation by penalizing ink that touches tile borders.

    Args:
        image: Prepared tile image as Pillow or grayscale array.

    Keyword Args:
        config: Optional scoring thresholds and normalization constants.

    Returns:
        Margin score on ``0.0``-``1.0`` where higher means less clipping.

    """
    resolved = config or BTTileQualityConfig()
    gray = _to_gray_array(image)
    mask = _ink_mask(gray, resolved.ink_threshold)
    edge_band = 2
    edge_density = (
        float(mask[:edge_band, :].mean()),
        float(mask[-edge_band:, :].mean()),
        float(mask[:, :edge_band].mean()),
        float(mask[:, -edge_band:].mean()),
    )
    penalty = max(edge_density)
    return _clamp01(1.0 - penalty * 4.0)


def composite_readability_score(metrics: BTTileMetricValues) -> float:
    """
    Combine metric scores into the documented readability composite.

    Args:
        metrics: Individual metric scores for one tile.

    Returns:
        Weighted composite score on ``0.0``-``1.0``.

    """
    weighted = (
        _COMPOSITE_WEIGHTS["stroke_contrast_score"] * metrics.stroke_contrast_score
        + _COMPOSITE_WEIGHTS["focus_score"] * metrics.focus_score
        + _COMPOSITE_WEIGHTS["small_component_preservation_score"]
        * metrics.small_component_preservation_score
        + _COMPOSITE_WEIGHTS["line_separability_score"]
        * metrics.line_separability_score
        + _COMPOSITE_WEIGHTS["column_contamination_score"]
        * metrics.column_contamination_score
        + _COMPOSITE_WEIGHTS["margin_clipping_score"] * metrics.margin_clipping_score
    )
    return _clamp01(weighted)


def _apply_guardrail(
    quality: BTTileQuality,
    *,
    config: BTTileQualityConfig,
) -> BTTileQuality:
    """
    Cap composite readability when small-component preservation collapses.

    Args:
        quality: Candidate tile quality metadata with metric fields populated.

    Keyword Args:
        config: Scoring thresholds and normalization constants.

    Returns:
        Tile quality metadata with guardrail adjustments applied.

    """
    preservation = quality.small_component_preservation_score
    if preservation is None or quality.composite_score is None:
        return quality

    if preservation >= config.small_component_guardrail_threshold:
        return quality

    capped = min(quality.composite_score, config.guardrail_composite_cap)
    notes = (
        *quality.notes,
        "small component preservation below guardrail threshold",
    )
    return BTTileQuality(
        status=quality.status,
        notes=notes,
        stroke_contrast_score=quality.stroke_contrast_score,
        focus_score=quality.focus_score,
        small_component_preservation_score=preservation,
        line_separability_score=quality.line_separability_score,
        column_contamination_score=quality.column_contamination_score,
        margin_clipping_score=quality.margin_clipping_score,
        composite_score=capped,
        small_component_guardrail_failed=True,
    )


def _to_gray_array(image: Image.Image | Path | np.ndarray) -> np.ndarray:
    """
    Convert one tile image input into a grayscale numpy array.

    Args:
        image: Prepared tile image as Pillow, path, or grayscale array.

    Returns:
        Two-dimensional ``uint8`` grayscale array.

    """
    if isinstance(image, np.ndarray):
        if image.ndim != _GRAYSCALE_ARRAY_DIMENSIONS:
            msg = "grayscale arrays must be two-dimensional"
            raise ValueError(msg)
        return image.astype(np.uint8, copy=False)

    if isinstance(image, Image.Image):
        return np.asarray(image.convert("L"), dtype=np.uint8)

    if isinstance(image, Path):
        with Image.open(image) as opened:
            return np.asarray(opened.convert("L"), dtype=np.uint8)

    msg = f"unsupported image type: {type(image)!r}"
    raise TypeError(msg)


def _ink_mask(gray: np.ndarray, threshold: int = _INK_THRESHOLD) -> np.ndarray:
    """
    Build a boolean ink mask from one grayscale tile array.

    Args:
        gray: Two-dimensional grayscale tile array.
        threshold: Grayscale value below which pixels count as ink.

    Returns:
        Boolean mask where ``True`` marks ink pixels.

    """
    return gray < threshold


def _laplacian_variance(gray: np.ndarray) -> float:
    """
    Compute Laplacian variance for one grayscale tile array.

    Args:
        gray: Two-dimensional grayscale tile array.

    Returns:
        Variance of the discrete Laplacian response.

    """
    padded = np.pad(gray.astype(np.float64), 1, mode="edge")
    center = padded[1:-1, 1:-1]
    laplacian = (
        padded[:-2, 1:-1]
        + padded[2:, 1:-1]
        + padded[1:-1, :-2]
        + padded[1:-1, 2:]
        - 4.0 * center
    )
    return float(laplacian.var())


def _component_areas(mask: np.ndarray) -> list[int]:
    """
    Measure connected-component areas for one boolean ink mask.

    Args:
        mask: Boolean mask where ``True`` marks ink pixels.

    Returns:
        Connected-component areas in stable scan order.

    """
    height, width = mask.shape
    labels = np.zeros((height, width), dtype=np.int32)
    areas: list[int] = []
    current_label = 0
    neighbors = (
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
        (-1, -1),
        (-1, 1),
        (1, -1),
        (1, 1),
    )

    for row in range(height):
        for col in range(width):
            if not mask[row, col] or labels[row, col]:
                continue
            current_label += 1
            queue: deque[tuple[int, int]] = deque([(row, col)])
            labels[row, col] = current_label
            area = 0
            while queue:
                y, x = queue.popleft()
                area += 1
                for dy, dx in neighbors:
                    ny = y + dy
                    nx = x + dx
                    if (
                        0 <= ny < height
                        and 0 <= nx < width
                        and mask[ny, nx]
                        and labels[ny, nx] == 0
                    ):
                        labels[ny, nx] = current_label
                        queue.append((ny, nx))
            areas.append(area)
    return areas


def _clamp01(value: float) -> float:
    """
    Clamp one scalar into the documented ``0.0``-``1.0`` score range.

    Args:
        value: Raw metric or composite value.

    Returns:
        Value constrained to ``0.0``-``1.0``.

    """
    return float(min(1.0, max(0.0, value)))
