"""Display rules for one dictionary browse results row (ADR 0026, ADR 0028)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Protocol

from textual.content import Content

from wyrdcraeft.services.markup import normalize_old_english

if TYPE_CHECKING:
    from wyrdcraeft.services.dictionary.browse_query import BrowseSearchHit

#: Theme style for dim parts of a results row (hyphens, ``→ headword``).
DIM_STYLE = "$text-muted"

#: Part-of-speech label shown when the entry has none.
UNKNOWN_POS = "unknown"

#: Characters not allowed in a ``pos-<code>`` CSS class name.
_CLASS_UNSAFE = re.compile(r"[^a-z0-9_-]+")


class HasPos(Protocol):
    """Anything carrying a dictionary part of speech (a hit or entry details)."""

    @property
    def pos(self) -> str:
        """Part of speech stored on the dictionary entry."""
        ...


def pos_label(hit: HasPos) -> str:
    """
    Return the part-of-speech text shown in a results row or banner tag.

    Args:
        hit: Search hit or entry details carrying a part of speech.

    Returns:
        The hit's part of speech, or ``unknown`` when it has none.

    """
    return hit.pos.strip() or UNKNOWN_POS


def pos_tag_class(hit: HasPos) -> str:
    """
    Return the ``pos-<code>`` CSS class that tints a part-of-speech tag.

    Args:
        hit: Search hit or entry details carrying a part of speech.

    Returns:
        CSS class name such as ``pos-noun``.

    """
    code = _CLASS_UNSAFE.sub("-", pos_label(hit).lower()).strip("-")
    return f"pos-{code or UNKNOWN_POS}"


def _headword_parts(headword: str) -> list[tuple[str, str] | str]:
    """
    Split a headword so each hyphen inside it can be drawn dim.

    Args:
        headword: Dictionary headword such as ``for-sceamian``.

    Returns:
        Plain and ``(text, style)`` parts for :meth:`Content.assemble`.

    """
    parts: list[tuple[str, str] | str] = []
    for index, piece in enumerate(headword.split("-")):
        if index:
            parts.append(("-", DIM_STYLE))
        if piece:
            parts.append(piece)
    return parts


def matched_variant(hit: BrowseSearchHit) -> bool:
    """
    Report whether the hit matched a variant spelling rather than the headword.

    Args:
        hit: Dictionary-backed search hit.

    Returns:
        ``True`` when the matched text differs from the headword.

    """
    headword_norm = normalize_old_english(hit.headword) or ""
    matched_norm = normalize_old_english(hit.matched_text) or ""
    return hit.rank_tier > 1 and bool(matched_norm) and matched_norm != headword_norm


def headword_content(hit: BrowseSearchHit) -> Content:
    """
    Build the headword cell of a results row.

    A hyphen inside the headword is dim. When the hit matched a variant, the
    cell shows the matched text first, then ``→ headword`` dim.

    Args:
        hit: Dictionary-backed search hit.

    Returns:
        Styled headword cell content.

    """
    if not matched_variant(hit):
        return Content.assemble(*_headword_parts(hit.headword))
    return Content.assemble(hit.matched_text, " ", (f"→ {hit.headword}", DIM_STYLE))


def definition_text(hit: BrowseSearchHit) -> str:
    """
    Return the dim definition line shown in a results row.

    Args:
        hit: Dictionary-backed search hit.

    Returns:
        The cached definition line, or an empty string when it is empty or
        not computed yet.

    """
    return hit.definition_line or ""
