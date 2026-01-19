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
#: A regular expression to match running headers (relaxed, line-based).
# Match short ALL-CAPS running headers or titles (but not full OE lines)
HEADER_RE = re.compile(r"""^[A-Z][A-Z\s]{3,}$""")
#: Test for lines that consist only of a numbering marker (e.g. "[12]") and
#: nothing else.
NUMBER_ONLY_LINE_RE = re.compile(r"^\s*[\[(]?\d+[\])\.]?\s*")
#: The minimum number of lines in a verse block to be considered verse.
NUM_VERSE_LINES: Final[int] = 2
#: The minimum average length of a line in a verse block to
#: be considered verse.
MIN_AVG_VERSE_LINE_LENGTH: Final[int] = 60
#: Max number of words in a header line.
MAX_HEADER_WORDS: Final[int] = 6


def _is_verse_line(line: str, *, max_len: int = 80) -> bool:
    """
    Heuristic: short, line-broken, non-empty lines
    typical of OE verse editions.
    """
    stripped = line.strip()
    if not stripped:
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


def match_normalized_to_original(normalized_text: str, raw_text: str) -> str:
    """
    Find the original text in raw_text that matches normalized_text
    ignoring differences in whitespace.
    """
    if not raw_text or not normalized_text:
        return normalized_text

    # Escape special regex characters in the normalized text
    # then replace any whitespace run with a flexible whitespace regex
    # We include \s* at the very beginning and end to capture surrounding whitespace
    # of the block in the original source.
    flexible_pattern = r"\s*"
    for char in normalized_text:
        if char.isspace():
            if not flexible_pattern.endswith(r"\s*"):
                flexible_pattern += r"\s*"
        else:
            flexible_pattern += re.escape(char)
    flexible_pattern += r"\s*"

    try:
        match = re.search(flexible_pattern, raw_text, re.DOTALL)
        if match:
            return match.group(0)
    except re.error:
        pass

    return normalized_text


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

        # Look ahead to detect verse runs
        if _is_verse_line(line):
            run_lines = [line]
            j = i + 1

            while j < len(lines):
                if _is_verse_line(lines[j]) or _is_number_line(lines[j]):
                    run_lines.append(lines[j])
                    j += 1
                else:
                    break

            # Require at least :data:`NUM_VERSE_LINES` consecutive verse-like
            # lines and an average line length of less than
            # :data:`MIN_AVG_VERSE_LINE_LENGTH` characters to be considered
            # verse.
            if len(run_lines) >= NUM_VERSE_LINES:
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


def normalize_elements_to_blocks(
    elements: Iterable[object], raw_text: str = ""
) -> list[RawBlock]:
    """
    Normalize elements to blocks.

    Args:
        elements: The elements to normalize.
        raw_text: The original raw text of the source document.

    Returns:
        A list of blocks.

    """
    blocks: list[RawBlock] = []

    for el in elements:
        text = getattr(el, "text", None)

        if not text:
            continue

        # Re-align with raw text to preserve whitespaces (multiple spaces, tabs, etc.)
        # We do this BEFORE stripping so we can capture the original context.
        if raw_text:
            text = match_normalized_to_original(text, raw_text)

        text = text.strip()
        if not text:
            continue

        # Drop footnote markers or page numbers
        if FOOTNOTE_RE.match(text):
            continue

        # Instead of dropping blocks with headers, filter lines within the block
        lines = text.splitlines(keepends=True)
        filtered_lines: list[str] = []

        for ln in lines:
            stripped = ln.strip()
            if not stripped:
                filtered_lines.append(ln)
                continue
            # Drop pure headers, but only if they are short
            if (
                HEADER_RE.fullmatch(stripped)
                and len(stripped.split()) <= MAX_HEADER_WORDS
            ):
                continue
            filtered_lines.append(ln)

        text = "".join(filtered_lines).rstrip()
        if not text:
            continue

        meta = getattr(el, "metadata", None)
        page = getattr(meta, "page_number", None) if meta else None
        category = getattr(el, "category", None)

        blocks.extend(split_prose_and_verse_runs(text, category=category, page=page))

    return blocks
