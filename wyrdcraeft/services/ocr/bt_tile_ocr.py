"""Tile-level OCR helpers for Bosworth-Toller witness preparation."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import replace
from pathlib import Path

from wyrdcraeft.services.ocr.bt_witness_prep.pipeline import TILES_OUTPUT_DIR
from wyrdcraeft.services.ocr.old_english_pipeline import (
    OldEnglishOCRConfig,
    run_old_english_ocr_pipeline,
)

#: Callable signature for injectable OCR runners in tests and offline runs.
OCRRunner = Callable[[Path, Path], str]
#: Candidate tile geometry suffixes in reading order for ready pages.
TILE_READING_ORDER = (
    "col-1-part-1",
    "col-2-part-1",
    "col-1-part-2",
    "col-2-part-2",
)
#: Backward-compatible alias retained for benchmark callers.
CANDIDATE_TILE_READING_ORDER = TILE_READING_ORDER
#: Relative directory for per-tile and page witness artifacts.
WITNESSES_OUTPUT_DIR = Path("witnesses")
#: Relative directory for per-tile OCR witness workspaces.
WITNESSES_TILES_DIR = Path("witnesses/tiles")
#: Relative directory for joined page-level markdown witnesses.
WITNESSES_PAGES_DIR = Path("witnesses/pages")
#: Whole-page fallback geometry slug used in tile filenames and ids.
WHOLE_PAGE_GEOMETRY = "whole-page"


def discover_tile_images(
    prep_output_dir: Path,
    page_id: str,
) -> list[Path]:
    """
    Discover prepared tile images for one page in reading order.

    Args:
        prep_output_dir: ``prepare_pages()`` workspace containing ``tiles/``.
        page_id: Validation page id whose tiles should be collected.

    Returns:
        Tile image paths in reading order, or one whole-page fallback tile.

    Raises:
        FileNotFoundError: When no prepared tile images exist for ``page_id``.

    """
    tiles_dir = prep_output_dir.resolve() / TILES_OUTPUT_DIR
    ordered: list[Path] = []
    for geometry in TILE_READING_ORDER:
        candidate = tiles_dir / f"{page_id}-{geometry}.png"
        if candidate.is_file():
            ordered.append(candidate)
    if ordered:
        return ordered

    fallback = tiles_dir / f"{page_id}-{WHOLE_PAGE_GEOMETRY}.png"
    if fallback.is_file():
        return [fallback]

    message = f"no prepared candidate tiles for {page_id} under {tiles_dir}"
    raise FileNotFoundError(message)


def tile_id_from_image_path(image_path: Path) -> str:
    """
    Derive manifest ``tile_id`` from one prepared tile image filename.

    Args:
        image_path: Prepared tile image path under ``tiles/``.

    Returns:
        Tile id using ``page_id:geometry`` slug form.

    Raises:
        ValueError: When the filename does not match a known tile geometry.

    """
    stem = image_path.stem
    geometries = (*TILE_READING_ORDER, WHOLE_PAGE_GEOMETRY)
    for geometry in geometries:
        suffix = f"-{geometry}"
        if stem.endswith(suffix):
            page_id = stem[: -len(suffix)]
            return f"{page_id}:{geometry}"
    message = f"unable to derive tile_id from prepared tile image {image_path}"
    raise ValueError(message)


def concatenate_tile_texts(tile_texts: Sequence[str]) -> str:
    """
    Join per-tile OCR texts into one page-level witness.

    Args:
        tile_texts: OCR texts for one page's tiles in reading order.

    Returns:
        Page-level witness text with blank-line separators between tiles.

    """
    parts = [text.strip() for text in tile_texts if text.strip()]
    if not parts:
        return ""
    return "\n\n".join(parts) + "\n"


def run_tile_ocr(
    image_path: Path,
    output_dir: Path,
    *,
    skip_ocr: bool = False,
    ocr_runner: OCRRunner | None = None,
    ocr_config: OldEnglishOCRConfig | None = None,
) -> str:
    """
    Run or load OCR text for one prepared page or tile image.

    Args:
        image_path: Prepared image path passed to olmocr.
        output_dir: Workspace directory for one OCR invocation.

    Keyword Args:
        skip_ocr: When ``True``, reuse existing normalized OCR output if present.
        ocr_runner: Injectable OCR runner for tests or custom integrations.
        ocr_config: Optional olmocr configuration for live OCR runs.

    Returns:
        Normalized OCR text for the image.

    Raises:
        RuntimeError: When live OCR is unavailable and no cached text exists.

    """
    if ocr_runner is not None:
        return ocr_runner(image_path, output_dir)

    normalized_path = output_dir / "03_normalized.txt"
    if skip_ocr:
        if normalized_path.is_file():
            return normalized_path.read_text(encoding="utf-8")
        message = (
            f"skip-ocr enabled but no cached OCR output exists for {image_path} "
            f"at {normalized_path}"
        )
        raise RuntimeError(message)

    if ocr_config is None:
        ocr_config = OldEnglishOCRConfig(
            input_path=image_path,
            output_dir=output_dir,
        )
    else:
        ocr_config = replace(
            ocr_config,
            input_path=image_path,
            output_dir=output_dir,
            skip_ocr=False,
        )
    result = run_old_english_ocr_pipeline(ocr_config)
    return result.normalized_text_path.read_text(encoding="utf-8")


def run_page_witness_ocr(
    tile_paths: Sequence[Path],
    tile_output_dir: Callable[[Path, int], Path],
    *,
    skip_ocr: bool = False,
    ocr_runner: OCRRunner | None = None,
    ocr_config: OldEnglishOCRConfig | None = None,
) -> str:
    """
    OCR prepared tiles and concatenate them page-wise.

    Args:
        tile_paths: Candidate tile images in reading order.
        tile_output_dir: Callable that resolves one tile OCR workspace path.

    Keyword Args:
        skip_ocr: When ``True``, reuse cached OCR outputs when present.
        ocr_runner: Injectable OCR runner for tests or custom integrations.
        ocr_config: Optional olmocr configuration for live OCR runs.

    Returns:
        Page-level witness OCR text.

    """
    tile_texts = [
        run_tile_ocr(
            tile_path,
            tile_output_dir(tile_path, index),
            skip_ocr=skip_ocr,
            ocr_runner=ocr_runner,
            ocr_config=ocr_config,
        )
        for index, tile_path in enumerate(tile_paths)
    ]
    return concatenate_tile_texts(tile_texts)
