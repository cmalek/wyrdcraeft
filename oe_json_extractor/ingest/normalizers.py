from __future__ import annotations

import re
from typing import TYPE_CHECKING

from ..models.parsing import RawBlock

if TYPE_CHECKING:
    from collections.abc import Iterable

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

#: A regular expression to match footnote markers or page numbers.
FOOTNOTE_RE = re.compile(r"""^\s*\(?\d+\)?\s*$""")
#: A regular expression to match running headers.
HEADER_RE = re.compile(r"""^[A-Z\s]{5,}$""")


def normalize_elements_to_blocks(elements: Iterable[object]) -> list[RawBlock]:
    """
    Normalize elements to blocks.  This means converting the elements into a list of
    blocks of text.  This is the first step in the ingestion pipeline.

    Args:
        elements: The elements to normalize.

    Returns:
        A list of blocks.

    """
    blocks: list[RawBlock] = []

    for el in elements:
        text = getattr(el, "text", None)
        if not text:
            continue

        text = text.strip()
        if not text:
            continue

        # Drop footnote markers or page numbers
        if FOOTNOTE_RE.match(text):
            continue

        # Drop obvious running headers
        if HEADER_RE.match(text):
            continue

        meta = getattr(el, "metadata", None)
        page = getattr(meta, "page_number", None) if meta else None
        category = getattr(el, "category", "Unknown")

        blocks.append(
            RawBlock(
                text=text,
                category=str(category),
                page=page,
            )
        )

    return blocks
