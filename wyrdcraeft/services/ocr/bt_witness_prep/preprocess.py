"""Conservative preprocessing for Bosworth-Toller witness preparation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

from wyrdcraeft.services.ocr.bt_witness_prep.models import (
    BTPreprocessedPage,
    BTSourcePage,
)

#: Callable that opens one scan image for preprocessing.
ImageOpener = Callable[[Path], Image.Image]
#: Pixel crop box as ``(left, top, right, bottom)``.
CropBox = tuple[int, int, int, int]


@dataclass(frozen=True)
class BTPreprocessRecipe:
    """
    Conservative preprocessing recipe for one Bosworth-Toller scan page.

    Args:
        recipe_id: Stable recipe identifier recorded on prepared pages.
        margin_luminance_delta: Minimum luminance drop from edge background
            that marks page content during margin crop.
        min_content_pixels_per_line: Minimum dark pixels required to treat one
            row or column as content-bearing.
        max_margin_fraction: Maximum fraction of width or height removable
            from any one edge before crop is clamped.
        deskew_mode: Deskew contract name; ``noop`` leaves geometry unchanged.
        normalize_background: Whether to apply mild background normalization.
        export_grayscale: Whether to export the prepared page as grayscale.
        sharpen: Whether to apply a mild unsharp mask after normalization.

    """

    #: Stable recipe identifier recorded on prepared pages.
    recipe_id: str
    #: Minimum luminance drop from edge background that marks page content.
    margin_luminance_delta: int = 20
    #: Minimum dark pixels required to treat one row or column as content.
    min_content_pixels_per_line: int = 4
    #: Maximum fraction of width or height removable from any one edge.
    max_margin_fraction: float = 0.12
    #: Deskew contract name; ``noop`` leaves geometry unchanged.
    deskew_mode: str = "noop"
    #: Whether to apply mild background normalization.
    normalize_background: bool = True
    #: Whether to export the prepared page as grayscale.
    export_grayscale: bool = True
    #: Whether to apply a mild unsharp mask after normalization.
    sharpen: bool = True

    @staticmethod
    def conservative_default(recipe_id: str) -> BTPreprocessRecipe:
        """
        Build the default conservative preprocessing recipe.

        Args:
            recipe_id: Stable recipe identifier recorded on prepared pages.

        Returns:
            Default conservative recipe for Bosworth-Toller scans.

        """
        return BTPreprocessRecipe(recipe_id=recipe_id)


class BTPagePreprocessor:
    """
    Apply one conservative preprocessing recipe to Bosworth-Toller scan pages.

    Args:
        recipe: Frozen preprocessing recipe applied to every page.
        open_image: Optional image opener for tests; defaults to Pillow.

    """

    def __init__(
        self,
        recipe: BTPreprocessRecipe,
        *,
        open_image: ImageOpener | None = None,
    ) -> None:
        """
        Initialize one preprocessor for a preprocessing recipe.

        Args:
            recipe: Frozen preprocessing recipe applied to every page.

        Keyword Args:
            open_image: Optional image opener for tests; defaults to Pillow.

        """
        #: Frozen preprocessing recipe applied to every page.
        self._recipe = recipe
        #: Image opener used to read source scans.
        self._open_image = open_image or _open_image

    def preprocess(
        self,
        source_page: BTSourcePage,
        output_dir: Path,
    ) -> BTPreprocessedPage:
        """
        Prepare one source page and write a derived grayscale image.

        Side Effects:
            Creates ``output_dir`` when missing and writes one PNG artifact.

        Args:
            source_page: Source page provenance record to preprocess.
            output_dir: Directory that receives the prepared page image.

        Returns:
            Provenance record for the prepared full-page image.

        """
        resolved_output_dir = output_dir.resolve()
        resolved_output_dir.mkdir(parents=True, exist_ok=True)

        with self._open_image(source_page.source_path) as image:
            rgb_image = image.convert("RGB")
            deskewed = _apply_deskew(rgb_image, self._recipe)
            crop_box = _detect_crop_box(deskewed, self._recipe)
            cropped = deskewed.crop(crop_box)
            prepared = _enhance_for_ocr(cropped, self._recipe)

            image_path = resolved_output_dir / f"{source_page.page_id}.png"
            prepared.save(image_path, format="PNG")

        width_px, height_px = prepared.size
        return BTPreprocessedPage(
            source_path=source_page.source_path,
            page_id=source_page.page_id,
            recipe_id=self._recipe.recipe_id,
            image_path=image_path,
            crop_box=crop_box,
            width_px=width_px,
            height_px=height_px,
        )


def preprocess_source_page(
    source_page: BTSourcePage,
    output_dir: Path,
    recipe: BTPreprocessRecipe,
) -> BTPreprocessedPage:
    """
    Prepare one source page with a conservative preprocessing recipe.

    Side Effects:
        Creates ``output_dir`` when missing and writes one PNG artifact.

    Args:
        source_page: Source page provenance record to preprocess.
        output_dir: Directory that receives the prepared page image.
        recipe: Frozen preprocessing recipe applied to the page.

    Returns:
        Provenance record for the prepared full-page image.

    """
    return BTPagePreprocessor(recipe).preprocess(source_page, output_dir)


def _apply_deskew(image: Image.Image, recipe: BTPreprocessRecipe) -> Image.Image:
    """
    Apply the configured deskew contract to one RGB page image.

    Note:
        The first slice only supports ``noop`` deskew, which preserves the
        source geometry exactly for conservative OCR preparation.

    Args:
        image: Source page image in RGB mode.
        recipe: Preprocessing recipe containing the deskew contract.

    Returns:
        RGB image after the configured deskew step.

    """
    if recipe.deskew_mode != "noop":
        message = (
            "BT witness prep preprocessing only supports deskew_mode='noop' "
            f"in this slice: {recipe.deskew_mode!r}"
        )
        raise ValueError(message)
    return image


def _detect_crop_box(image: Image.Image, recipe: BTPreprocessRecipe) -> CropBox:
    """
    Detect a conservative margin crop box for one RGB page image.

    Args:
        image: Source page image in RGB mode.
        recipe: Preprocessing recipe controlling crop thresholds.

    Returns:
        Pixel crop box clamped to the configured maximum margin fraction.

    """
    width_px, height_px = image.size
    gray = image.convert("L")
    corner_points = (
        (0, 0),
        (width_px - 1, 0),
        (0, height_px - 1),
        (width_px - 1, height_px - 1),
    )
    background = sum(_gray_luminance(gray, point) for point in corner_points) // 4
    threshold = background - recipe.margin_luminance_delta

    def row_has_content(y: int) -> bool:
        dark_pixels = sum(
            1
            for x in range(width_px)
            if _gray_luminance(gray, (x, y)) < threshold
        )
        return dark_pixels >= recipe.min_content_pixels_per_line

    def col_has_content(x: int) -> bool:
        dark_pixels = sum(
            1
            for y in range(height_px)
            if _gray_luminance(gray, (x, y)) < threshold
        )
        return dark_pixels >= recipe.min_content_pixels_per_line

    top = 0
    while top < height_px and not row_has_content(top):
        top += 1
    bottom = height_px
    while bottom > top and not row_has_content(bottom - 1):
        bottom -= 1
    left = 0
    while left < width_px and not col_has_content(left):
        left += 1
    right = width_px
    while right > left and not col_has_content(right - 1):
        right -= 1

    if top >= bottom or left >= right:
        return (0, 0, width_px, height_px)

    return _clamp_crop_box((left, top, right, bottom), width_px, height_px, recipe)


def _clamp_crop_box(
    crop_box: CropBox,
    width_px: int,
    height_px: int,
    recipe: BTPreprocessRecipe,
) -> CropBox:
    """
    Clamp one crop box to the configured maximum margin fraction.

    Args:
        crop_box: Candidate crop box as ``(left, top, right, bottom)``.
        width_px: Source image width in pixels.
        height_px: Source image height in pixels.
        recipe: Preprocessing recipe containing the margin limit.

    Returns:
        Crop box that does not remove more than the allowed margin fraction.

    """
    left, top, right, bottom = crop_box
    max_left = int(width_px * recipe.max_margin_fraction)
    max_top = int(height_px * recipe.max_margin_fraction)
    max_right_trim = int(width_px * recipe.max_margin_fraction)
    max_bottom_trim = int(height_px * recipe.max_margin_fraction)

    left = max(left, 0)
    top = max(top, 0)
    right = min(right, width_px)
    bottom = min(bottom, height_px)

    left = min(left, max_left)
    top = min(top, max_top)
    right = max(right, width_px - max_right_trim)
    bottom = max(bottom, height_px - max_bottom_trim)

    if left >= right or top >= bottom:
        return (0, 0, width_px, height_px)
    return (left, top, right, bottom)


def _enhance_for_ocr(image: Image.Image, recipe: BTPreprocessRecipe) -> Image.Image:
    """
    Apply conservative OCR-oriented enhancements to one cropped page image.

    Args:
        image: Cropped page image in RGB mode.
        recipe: Preprocessing recipe controlling enhancement steps.

    Returns:
        Prepared page image ready for PNG export.

    """
    prepared = image
    if recipe.normalize_background:
        prepared = ImageOps.autocontrast(prepared.convert("L"), cutoff=0)
    elif recipe.export_grayscale:
        prepared = prepared.convert("L")

    if recipe.export_grayscale and prepared.mode != "L":
        prepared = prepared.convert("L")

    if recipe.sharpen:
        prepared = prepared.filter(
            ImageFilter.UnsharpMask(radius=1, percent=50, threshold=3),
        )

    return prepared


def _gray_luminance(gray: Image.Image, point: tuple[int, int]) -> int:
    """
    Read one grayscale luminance value from a Pillow image.

    Args:
        gray: Grayscale page image.
        point: Pixel coordinate as ``(x, y)``.

    Returns:
        Integer luminance for the requested pixel.

    """
    value = gray.getpixel(point)
    if value is None:
        return 255
    if isinstance(value, tuple):
        return int(value[0])
    return int(value)


def _open_image(source_path: Path) -> Image.Image:
    """
    Open one source scan image with Pillow.

    Args:
        source_path: Scan image path.

    Returns:
        Open Pillow image handle.

    """
    return Image.open(source_path)
