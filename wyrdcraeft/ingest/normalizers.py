from __future__ import annotations

import re
from typing import Final, Literal

from ..models.parsing import RawBlock

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

#: Test for lines that consist only of a numbering marker (e.g. "[12]") and
#: nothing else.
NUMBER_ONLY_LINE_RE = re.compile(r"^\s*[\[(]?\d+[\])\.]?\s*")
#: The minimum number of lines in a verse block to be considered verse.
NUM_VERSE_LINES: Final[int] = 2
#: The minimum average length of a line in a verse block to
#: be considered verse.
MIN_AVG_VERSE_LINE_LENGTH: Final[int] = 60


def _is_heading_line(line: str) -> bool:
    """
    Test if a line looks like a heading.
    """
    t = line.strip()
    if not t:
        return False
    # Roman numeral chapter heading: "I. THE PASSING OF SCYLD." or just "I."
    if re.match(r"^[IVXLCDM]+\.?(\s+|$)", t):
        return True
    # All caps heading: "BEÓWULF."
    if len(t) >= 3 and t.upper() == t and not any(c.isdigit() for c in t):
        return True
    if re.match(r"^(Cap\.|CAP\.|Chapter\b|CHAPTER\b)", t):
        return True
    if re.match(r"^(?:A\.D\.|AD)\s*\d{3,4}\b", t):
        return True
    return bool(re.match(r"^Her\s+\d{3,4}\b", t))


def _is_verse_line(line: str, *, max_len: int = 80) -> bool:
    """
    Heuristic: short, line-broken, non-empty lines
    typical of OE verse editions.
    """
    stripped = line.strip()
    if not stripped:
        return False

    # Headings are not verse
    if _is_heading_line(line):
        return False

    # Ignore pure numbering lines like "[12]" or standalone "5", "10".
    if NUMBER_ONLY_LINE_RE.fullmatch(stripped) or re.fullmatch(r"^\d+$", stripped):
        return False

    # Verse lines tend to be short and not sentence-like
    if len(stripped) > max_len:
        return False

    # Prose often ends with period + space; verse often does not
    # And verse will have multiple spaces between words once.
    # Exception: very short lines (like "Amen.") or lines with leading
    # whitespace are often still verse.
    if line.startswith("    ") or len(stripped) < 20:
        return True

    return not (stripped.endswith(".") and "  " not in stripped)


def _is_number_line(line: str) -> bool:
    """
    Test if a line is just a numbering marker (e.g. "[12]" or "5").
    """
    stripped = line.strip()
    return bool(
        NUMBER_ONLY_LINE_RE.fullmatch(stripped) or re.fullmatch(r"^\d+$", stripped)
    )


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

        # Explicitly split on headings
        if _is_heading_line(line):
            flush()
            blocks.append(
                RawBlock(
                    text=line,
                    category=category,
                    kind="prose",
                    page=page,
                )
            )
            i += 1
            continue

        # Look ahead to detect verse runs (can start with verse OR a line number)
        if _is_verse_line(line) or _is_number_line(line):
            run_lines = [line]
            has_verse = _is_verse_line(line)
            j = i + 1

            while j < len(lines):
                if _is_heading_line(lines[j]):
                    break
                if _is_verse_line(lines[j]) or _is_number_line(lines[j]):
                    if _is_verse_line(lines[j]):
                        has_verse = True
                    run_lines.append(lines[j])
                    j += 1
                else:
                    break

            # Require at least :data:`NUM_VERSE_LINES` consecutive verse-like
            # lines (including markers), at least one actual verse line,
            # and an average line length of less than
            # :data:`MIN_AVG_VERSE_LINE_LENGTH` characters.
            if has_verse and len(run_lines) >= NUM_VERSE_LINES:
                # Filter out number lines for avg length calculation
                content_lines = [ln for ln in run_lines if not _is_number_line(ln)]
                if content_lines:
                    avg = sum(len(ln) for ln in content_lines) / len(content_lines)
                else:
                    avg = 0

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
                    i = j
                    continue

        buffer.append(line)
        current_kind = "prose"
        i += 1

    flush()
    return blocks
