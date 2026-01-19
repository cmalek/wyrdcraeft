from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final, Literal

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
#: Test for lines that consist only of a numbering marker (e.g. "[12]") and
#: nothing else.
NUMBER_ONLY_LINE_RE = re.compile(r"^\s*[\[(]?\d+[\])\.]?\s*")
#: The minimum number of lines in a verse block to be considered verse.
NUM_VERSE_LINES: Final[int] = 2
#: The minimum average length of a line in a verse block to
#: be considered verse.
MIN_AVG_VERSE_LINE_LENGTH: Final[int] = 60


def _is_verse_line(line: str, *, max_len: int = 80) -> bool:
    """
    Heuristic: short, line-broken, non-empty lines
    typical of OE verse editions.
    """
    stripped = line.rstrip()
    if not stripped:
        return False

    # Ignore pure numbering lines like "[12]".
    if NUMBER_ONLY_LINE_RE.fullmatch(stripped):
        return False

    # Verse lines tend to be short and not sentence-like
    if len(stripped) > max_len:
        return False

    # Prose often ends with period + space; verse often does not
    # And verse will have multiple spaces between words once.
    return not (stripped.endswith(".") and "  " not in stripped)


def split_prose_and_verse_runs(
    text: str, category: str | None, page: int | None = None
) -> list[RawBlock]:
    """
    Split text into ordered prose / verse chunks.

    - Preserves original text exactly
    - Preserves ordering
    - No normalization
    - Sets the category and page of the blocks.
    - If the text is verse, it will be set to the kind "verse".
    - If the text is prose, it will be set to the kind "prose".

    Args:
        text: The text to split.
        category: The category of the text.
        page: The page number of the text.

    Returns:
        A list of blocks.

    """
    lines = text.splitlines(keepends=True)

    blocks: list[RawBlock] = []

    buffer: list[str] = []
    current_kind: Literal["prose", "verse"] = "prose"

    def flush():
        nonlocal buffer, current_kind
        if buffer:
            blocks.append(
                RawBlock(
                    text="".join(buffer),
                    category=category,
                    kind=current_kind,
                    page=page,
                )
            )
            buffer = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Look ahead to detect verse runs
        if _is_verse_line(line):
            run_lines = [line]
            j = i + 1

            while j < len(lines) and _is_verse_line(lines[j]):
                run_lines.append(lines[j])
                j += 1

            # Require at least :data:`NUM_VERSE_LINES` consecutive verse-like
            # lines and an average line length of less than
            # :data:`MIN_AVG_VERSE_LINE_LENGTH` characters to be considered
            # verse.
            if len(run_lines) >= NUM_VERSE_LINES:
                avg = sum(len(ln) for ln in run_lines) / len(run_lines)
                if avg <= MIN_AVG_VERSE_LINE_LENGTH:
                    flush()
                    blocks.append(
                        RawBlock(
                            text="".join(run_lines),
                            category=category,
                            kind="verse",
                            page=page,
                        )
                    )
                    print(f"Adding verse block: {' '.join(run_lines)}")
                i = j
                continue

        buffer.append(line)
        current_kind = "prose"
        i += 1

    flush()
    return blocks

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

        blocks.extend(split_prose_and_verse_runs(text, category=category, page=page))

    return blocks
