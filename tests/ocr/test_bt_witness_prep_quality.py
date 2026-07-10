from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter

from wyrdcraeft.services.ocr.bt_witness_prep.models import BTTileQuality
from wyrdcraeft.services.ocr.bt_witness_prep.quality import (
    BTTileMetricValues,
    BTTileQualityConfig,
    BTTileQualityScorer,
    BTTileScoreContext,
    _apply_guardrail,
    column_contamination_score,
    composite_readability_score,
    focus_score,
    line_separability_score,
    margin_clipping_score,
    small_component_preservation_score,
    stroke_contrast_score,
)


def _gray_array(width: int, height: int, background: int = 255) -> np.ndarray:
    return np.full((height, width), background, dtype=np.uint8)


def _score_context(
    *,
    column: int = 1,
    width: int = 240,
    height: int = 160,
    page_width: int = 480,
) -> BTTileScoreContext:
    return BTTileScoreContext(
        column=column,
        crop_box=(0, 0, width, height),
        page_width_px=page_width,
        page_height_px=height,
        column_gutter_px=10,
    )


def _draw_horizontal_bars(
    canvas: np.ndarray,
    *,
    y_positions: tuple[int, ...],
    bar_height: int = 8,
    ink: int = 0,
) -> np.ndarray:
    for y in y_positions:
        top = max(0, y)
        bottom = min(canvas.shape[0], y + bar_height)
        canvas[top:bottom, 20 : canvas.shape[1] - 20] = ink
    return canvas


def _draw_small_dots(
    canvas: np.ndarray,
    *,
    positions: tuple[tuple[int, int], ...],
    radius: int = 1,
    ink: int = 0,
) -> np.ndarray:
    for row, col in positions:
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                y = row + dy
                x = col + dx
                if 0 <= y < canvas.shape[0] and 0 <= x < canvas.shape[1]:
                    canvas[y, x] = ink
    return canvas


def _image_from_array(array: np.ndarray) -> Image.Image:
    return Image.fromarray(array, mode="L")


def _scorer() -> BTTileQualityScorer:
    return BTTileQualityScorer()


def test_stroke_contrast_score_prefers_high_contrast_text_bars() -> None:
    high = _image_from_array(
        _draw_horizontal_bars(_gray_array(240, 160), y_positions=(40, 80, 120)),
    )
    low = _image_from_array(
        _draw_horizontal_bars(
            _gray_array(240, 160, background=220),
            y_positions=(40, 80, 120),
            ink=190,
        ),
    )

    assert stroke_contrast_score(high) > stroke_contrast_score(low)
    assert stroke_contrast_score(high) >= 0.7


def test_focus_score_prefers_sharp_bars_over_blurred_copy() -> None:
    sharp = _image_from_array(
        _draw_horizontal_bars(_gray_array(240, 160), y_positions=(30, 70, 110)),
    )
    blurred = sharp.filter(ImageFilter.GaussianBlur(radius=2.5))

    assert focus_score(sharp) > focus_score(blurred)
    assert focus_score(sharp) >= 0.4


def test_small_component_preservation_score_tracks_dot_loss() -> None:
    dotted = _image_from_array(
        _draw_small_dots(
            _draw_horizontal_bars(_gray_array(240, 160), y_positions=(50, 100)),
            positions=((45, 60), (45, 120), (95, 180), (95, 210)),
        ),
    )
    erased = dotted.filter(ImageFilter.MedianFilter(size=7))

    assert small_component_preservation_score(dotted) > (
        small_component_preservation_score(erased)
    )
    assert small_component_preservation_score(dotted) >= 0.6


def test_line_separability_score_prefers_spaced_lines() -> None:
    spaced = _image_from_array(
        _draw_horizontal_bars(
            _gray_array(240, 180),
            y_positions=(20, 60, 100, 140),
            bar_height=6,
        ),
    )
    solid = _image_from_array(
        _draw_horizontal_bars(
            _gray_array(240, 180),
            y_positions=(20,),
            bar_height=120,
        ),
    )

    assert line_separability_score(spaced) > line_separability_score(solid)
    assert line_separability_score(spaced) >= 0.5


def test_column_contamination_score_penalizes_gutter_ink() -> None:
    clean = _image_from_array(
        _draw_horizontal_bars(_gray_array(200, 160), y_positions=(40, 90)),
    )
    contaminated = clean.copy()
    contaminated_array = np.array(contaminated, dtype=np.uint8)
    contaminated_array[30:130, 185:200] = 0
    contaminated = _image_from_array(contaminated_array)

    clean_score = column_contamination_score(
        clean,
        context=_score_context(width=200, page_width=400),
    )
    dirty_score = column_contamination_score(
        contaminated,
        context=_score_context(width=200, page_width=400),
    )

    assert clean_score > dirty_score
    assert clean_score >= 0.8


def test_margin_clipping_score_penalizes_edge_touching_ink() -> None:
    padded = _image_from_array(
        _draw_horizontal_bars(_gray_array(220, 160), y_positions=(40, 100)),
    )
    clipped = _image_from_array(
        _draw_horizontal_bars(_gray_array(220, 160), y_positions=(0, 150)),
    )

    assert margin_clipping_score(padded) > margin_clipping_score(clipped)
    assert margin_clipping_score(padded) >= 0.7


def test_composite_readability_score_uses_documented_weights() -> None:
    metrics = {
        "stroke_contrast_score": 0.9,
        "focus_score": 0.8,
        "small_component_preservation_score": 0.7,
        "line_separability_score": 0.6,
        "column_contamination_score": 0.5,
        "margin_clipping_score": 0.4,
    }
    expected = (
        0.30 * 0.9
        + 0.20 * 0.8
        + 0.20 * 0.7
        + 0.15 * 0.6
        + 0.10 * 0.5
        + 0.05 * 0.4
    )

    assert composite_readability_score(BTTileMetricValues(**metrics)) == expected


def test_scorer_populates_bt_tile_quality_fields() -> None:
    image = _image_from_array(
        _draw_small_dots(
            _draw_horizontal_bars(_gray_array(240, 160), y_positions=(40, 90)),
            positions=((35, 70), (35, 140), (85, 200)),
        ),
    )

    quality = _scorer().score_image(
        image,
        context=_score_context(),
    )

    assert quality.status == "ready"
    assert quality.stroke_contrast_score is not None
    assert quality.focus_score is not None
    assert quality.small_component_preservation_score is not None
    assert quality.line_separability_score is not None
    assert quality.column_contamination_score is not None
    assert quality.margin_clipping_score is not None
    assert quality.composite_score is not None
    assert 0.0 <= quality.composite_score <= 1.0


def test_bt_tile_quality_to_dict_includes_metric_fields() -> None:
    quality = BTTileQuality(
        status="ready",
        stroke_contrast_score=0.8,
        focus_score=0.7,
        small_component_preservation_score=0.6,
        line_separability_score=0.5,
        column_contamination_score=0.9,
        margin_clipping_score=0.85,
        composite_score=0.72,
        small_component_guardrail_failed=False,
    )

    payload = quality.to_dict()

    assert payload["stroke_contrast_score"] == 0.8
    assert payload["composite_score"] == 0.72
    assert payload["small_component_guardrail_failed"] is False


def test_guardrail_flags_catastrophic_small_component_loss_despite_focus_gain() -> (
    None
):
    baseline = _image_from_array(
        _draw_small_dots(
            _draw_horizontal_bars(_gray_array(240, 160), y_positions=(50, 100)),
            positions=((45, 60), (45, 120), (95, 180), (95, 210)),
        ),
    )
    degraded = baseline.filter(ImageFilter.GaussianBlur(radius=1.2))
    degraded = degraded.filter(ImageFilter.MedianFilter(size=9))

    baseline_quality = _scorer().score_image(
        baseline,
        context=_score_context(),
    )
    degraded_quality = _scorer().score_image(
        degraded,
        context=_score_context(),
    )

    degraded_small = degraded_quality.small_component_preservation_score
    baseline_small = baseline_quality.small_component_preservation_score
    assert degraded_small is not None
    assert baseline_small is not None
    assert degraded_small < baseline_small
    assert degraded_quality.small_component_guardrail_failed is True
    assert degraded_quality.composite_score is not None
    assert baseline_quality.composite_score is not None
    assert degraded_quality.composite_score <= baseline_quality.composite_score
    assert any("small component" in note.lower() for note in degraded_quality.notes)


def test_guardrail_caps_composite_when_preservation_collapses_under_high_other_scores() -> (
    None
):
    """Prove composite cap fires when other metrics would otherwise mask loss."""
    config = BTTileQualityConfig()
    raw = BTTileQuality(
        status="ready",
        stroke_contrast_score=0.95,
        focus_score=0.95,
        small_component_preservation_score=0.10,
        line_separability_score=0.95,
        column_contamination_score=0.95,
        margin_clipping_score=0.95,
        composite_score=0.82,
    )

    guarded = _apply_guardrail(raw, config=config)

    assert guarded.small_component_guardrail_failed is True
    assert guarded.composite_score == config.guardrail_composite_cap
    assert guarded.composite_score < raw.composite_score
    assert any("small component" in note.lower() for note in guarded.notes)


def test_scorer_results_are_deterministic_for_repeated_input() -> None:
    image = _image_from_array(
        _draw_small_dots(
            _draw_horizontal_bars(_gray_array(240, 160), y_positions=(40, 90)),
            positions=((35, 70), (35, 140), (85, 200)),
        ),
    )

    first = _scorer().score_image(
        image,
        context=_score_context(),
    )
    second = _scorer().score_image(
        image,
        context=_score_context(),
    )

    assert first == second
