"""Source page enumeration for Bosworth-Toller witness preparation."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PIL import Image

from wyrdcraeft.services.ocr.bt_witness_prep.models import BTSourcePage

#: Callable that opens one scan image for dimension reads.
ImageOpener = Callable[[Path], Image.Image]
#: Filename suffix accepted for Bosworth-Toller scan pages.
_JP2_SUFFIX = ".jp2"


class BTSourcePageEnumerator:
    """
    Scan one source directory and enumerate JP2 scan pages.

    Args:
        recipe_id: Preprocessing recipe identifier stamped onto each page.
        open_image: Optional image opener for tests; defaults to Pillow.

    """

    def __init__(
        self,
        recipe_id: str,
        *,
        open_image: ImageOpener | None = None,
    ) -> None:
        """
        Initialize one enumerator for a preprocessing recipe.

        Args:
            recipe_id: Preprocessing recipe identifier stamped onto each page.

        Keyword Args:
            open_image: Optional image opener for tests; defaults to Pillow.

        """
        #: Preprocessing recipe identifier stamped onto each page.
        self._recipe_id = recipe_id
        #: Image opener used to read page dimensions.
        self._open_image = open_image or _open_image

    def enumerate(self, source_dir: Path) -> list[BTSourcePage]:
        """
        Enumerate JP2 source pages in stable filename order.

        Args:
            source_dir: Directory containing Bosworth-Toller scan images.

        Raises:
            FileNotFoundError: When ``source_dir`` does not exist.
            NotADirectoryError: When ``source_dir`` is not a directory.
            ValueError: When ``source_dir`` contains no ``.jp2`` page files.

        Returns:
            Source page provenance records sorted by filename.

        """
        resolved_dir = source_dir.resolve()
        if not resolved_dir.exists():
            message = f"BT witness prep source directory does not exist: {resolved_dir}"
            raise FileNotFoundError(message)
        if not resolved_dir.is_dir():
            message = f"BT witness prep source path is not a directory: {resolved_dir}"
            raise NotADirectoryError(message)

        page_paths = sorted(
            (
                path
                for path in resolved_dir.iterdir()
                if path.is_file() and path.suffix.lower() == _JP2_SUFFIX
            ),
            key=lambda path: path.name,
        )
        if not page_paths:
            message = (
                "BT witness prep source directory contains no .jp2 page files: "
                f"{resolved_dir}"
            )
            raise ValueError(message)

        return [self._page_record(path) for path in page_paths]

    def _page_record(self, source_path: Path) -> BTSourcePage:
        """
        Build one source page record from a scan path.

        Args:
            source_path: JP2 scan image path.

        Returns:
            Source page provenance record with image dimensions.

        """
        with self._open_image(source_path) as image:
            width_px, height_px = image.size
        return BTSourcePage(
            source_path=source_path.resolve(),
            page_id=BTSourcePage.page_id_for(source_path),
            recipe_id=self._recipe_id,
            width_px=width_px,
            height_px=height_px,
        )


def enumerate_source_pages(source_dir: Path, recipe_id: str) -> list[BTSourcePage]:
    """
    Enumerate JP2 source pages in one scan directory.

    Args:
        source_dir: Directory containing Bosworth-Toller scan images.
        recipe_id: Preprocessing recipe identifier stamped onto each page.

    Returns:
        Source page provenance records sorted by filename.

    """
    return BTSourcePageEnumerator(recipe_id).enumerate(source_dir)


def _open_image(source_path: Path) -> Image.Image:
    """
    Open one source scan image with Pillow.

    Args:
        source_path: Scan image path.

    Returns:
        Open Pillow image handle.

    """
    return Image.open(source_path)
