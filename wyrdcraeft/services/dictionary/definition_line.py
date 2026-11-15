"""Read Bosworth-Toller glosses as one definition line."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

#: Prepositions that can turn a semicolon into an `` or `` join.
_COMPLEMENT_WORDS = frozenset(
    {
        "of",
        "to",
        "for",
        "in",
        "on",
        "at",
        "with",
        "from",
        "by",
        "into",
        "upon",
        "over",
        "under",
        "after",
        "before",
        "against",
        "through",
        "than",
        "as",
        "unto",
        "towards",
        "toward",
        "without",
        "within",
        "about",
        "between",
        "among",
        "across",
    }
)
#: First-word abbreviations that always keep a comma boundary.
_ABBREVIATION_WORDS = frozenset({"pp", "pl", "fut", "t", "p"})
#: Casefolded prefixes that mark a right-hand piece as a list item.
_LIST_PREFIXES = ("to ", "a ", "an ", "the ")
#: Leading infinitive markers stripped from verb sense parts.
_INFINITIVE_PREFIXES = ("to ", "To ")
#: Join used when a semicolon is a complement boundary.
_OR_JOIN = " or "
#: Join used when a semicolon is a list boundary.
_COMMA_JOIN = ", "


def definition_line(pos: str, glosses: Sequence[str]) -> str:
    """
    Format one dictionary entry as a single definition line.

    Args:
        pos: Part of speech; a verb strips leading infinitive markers.
        glosses: English gloss strings in caller-chosen sense order.

    Returns:
        Joined definition line, or an empty string when no senses remain.

    """
    senses = [_format_gloss(pos, gloss) for gloss in glosses]
    return "; ".join(sense for sense in senses if sense)


def _format_gloss(pos: str, gloss: str) -> str:
    """
    Join one gloss's semicolon pieces, then strip verbs and drop repeats.

    Args:
        pos: Part of speech for infinitive-marker stripping.
        gloss: Raw English gloss for one sense.

    Returns:
        Formatted sense string, or empty when the gloss has no pieces.

    """
    pieces = [piece.strip() for piece in gloss.split(";") if piece.strip()]
    if not pieces:
        return ""
    accumulated = pieces[0]
    for index, right in enumerate(pieces[1:], start=1):
        joiner = _OR_JOIN if _is_or_boundary(pieces[index - 1], right) else _COMMA_JOIN
        accumulated = f"{accumulated}{joiner}{right}"
    parts = [part.strip() for part in accumulated.split(",") if part.strip()]
    if pos.strip().casefold() == "verb":
        parts = [_strip_leading_to(part) for part in parts]
        parts = [part for part in parts if part]
    return _COMMA_JOIN.join(_dedupe_casefold(parts))


def _is_or_boundary(left: str, right: str) -> bool:
    """
    Return whether *right* should join *left* with `` or ``.

    Args:
        left: Semicolon piece immediately before this boundary.
        right: Next semicolon piece.

    Returns:
        ``True`` when the boundary is a complement join.

    """
    stripped = right.strip()
    folded = stripped.casefold()
    words = stripped.split()
    if (
        any(folded.startswith(prefix) for prefix in _LIST_PREFIXES)
        or not words
        or _word_key(words[0]) in _ABBREVIATION_WORDS
    ):
        return False
    try:
        head, complement_token, *_rest = words
    except ValueError:
        return False
    complement = _word_key(complement_token)
    if head.endswith(",") or complement not in _COMPLEMENT_WORDS:
        return False
    left_words = {_word_key(word) for word in left.split()}
    return complement not in left_words


def _word_key(word: str) -> str:
    """
    Return a casefolded word with trailing punctuation stripped.

    Args:
        word: One whitespace token.

    Returns:
        Normalized token used for abbreviation and complement checks.

    """
    return word.casefold().rstrip(".,;:")


def _strip_leading_to(part: str) -> str:
    """
    Strip a leading infinitive marker from one comma-separated part.

    Args:
        part: One comma-separated sense fragment.

    Returns:
        *part* without a leading ``to `` or ``To ``.

    """
    for prefix in _INFINITIVE_PREFIXES:
        if part.startswith(prefix):
            return part.removeprefix(prefix)
    return part


def _dedupe_casefold(parts: Sequence[str]) -> list[str]:
    """
    Keep the first spelling of each case-insensitive duplicate.

    Args:
        parts: Comma-separated fragments in join order.

    Returns:
        Deduplicated fragments preserving first-seen spelling.

    """
    seen: set[str] = set()
    kept: list[str] = []
    for part in parts:
        key = part.casefold()
        if key in seen:
            continue
        seen.add(key)
        kept.append(part)
    return kept
