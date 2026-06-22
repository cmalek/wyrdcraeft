"""Phase 04 target resolver for Bosworth-Toller editorial cross-references."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

from ..markup import normalize_old_english

if TYPE_CHECKING:
    from ...models.dictionary import BTPos
    from .line_parser import ParsedBTLine

#: Strips all HTML tags for plain-text extraction.
_TAG_RE: Final[re.Pattern[str]] = re.compile(r"<[^>]+>")

#: Collapses whitespace.
_WS_RE: Final[re.Pattern[str]] = re.compile(r"\s+")

#: Extracts ``for X in Dict`` substitute target from raw line body.
_FOR_X_IN_DICT_RE: Final[re.Pattern[str]] = re.compile(
    r"for\s+(.+?)\s+in\s+Dict",
    re.IGNORECASE,
)

#: Trailing punctuation patterns stripped from extracted target names.
_TRAILING_PUNCT_RE: Final[re.Pattern[str]] = re.compile(r"[;,.:]+$")


class BTTargetResolver:
    """
    Resolve editorial target references in Bosworth-Toller supplement lines.

    Parses ``for X in Dict`` phrases from editorial line bodies and normalises
    the extracted target name using
    :func:`~wyrdcraeft.services.markup.normalize_old_english` to obtain a
    stable lookup key.  When no explicit target is present the resolver falls
    back to the headword of the editorial line itself.

    """

    def resolve_target_norm_key(self, parsed_line: ParsedBTLine) -> str | None:
        """
        Return the normalised lookup key for the editorial target of *parsed_line*.

        When the line carries an ``editorial_target`` value the target text is
        normalised.  When no explicit target is present the line's own headword is
        used.

        Args:
            parsed_line: Parsed BT line whose editorial target should be resolved.

        Returns:
            Normalised target key, or ``None`` when the line has no valid headword.

        """
        if parsed_line.skip_reason is not None:
            return None

        target_text = parsed_line.editorial_target
        if target_text:
            norm = normalize_old_english(target_text)
            if norm:
                return norm

        raw = parsed_line.raw_line
        if raw is None:
            return None
        return normalize_old_english(raw.headword_raw)

    def resolve_for_x_in_dict(self, body: str) -> str | None:
        """
        Extract and normalise a ``for X in Dict`` target from *body*.

        Strips HTML tags before matching so markup variations do not affect the
        result.

        Args:
            body: Raw HTML body content from one BT source line.

        Returns:
            Normalised target key when the pattern is found, otherwise ``None``.

        """
        plain = _TAG_RE.sub(" ", body)
        plain = _WS_RE.sub(" ", plain).strip()
        match = _FOR_X_IN_DICT_RE.search(plain)
        if match is None:
            return None
        target = match.group(1).strip()
        target = _TRAILING_PUNCT_RE.sub("", target).strip()
        if not target:
            return None
        return normalize_old_english(target)

    def slug_to_norm_key(self, slug_field: str) -> str | None:
        """
        Convert a slug field (third ``@``-separated field) to a normalised lookup key.

        The slug field uses hyphen-separated ASCII forms of headwords.  This method
        normalises the first comma-separated value in the slug for use as a lookup
        key of last resort.

        Args:
            slug_field: Third ``@`` field from the BT source line.

        Returns:
            Normalised first slug token, or ``None`` when the field is empty.

        """
        if not slug_field:
            return None
        first_slug = slug_field.split(",", maxsplit=1)[0].strip()
        if not first_slug:
            return None
        return normalize_old_english(first_slug)

    def merge_key_for_line(
        self,
        parsed_line: ParsedBTLine,
    ) -> tuple[str, BTPos] | None:
        """
        Return the ``(norm_key, pos)`` merge key for a parsed line.

        Uses the line's own headword (not any editorial target), since merge groups
        are formed by the headword of the line, not the target it might modify.

        Args:
            parsed_line: Parsed BT line to derive the key from.

        Returns:
            ``(norm_key, pos)`` tuple, or ``None`` when the line is skipped or has
            no valid headword.

        """
        if parsed_line.skip_reason is not None:
            return None
        raw = parsed_line.raw_line
        if raw is None:
            return None
        norm = normalize_old_english(raw.headword_raw)
        if not norm:
            return None
        return (norm, parsed_line.pos)
