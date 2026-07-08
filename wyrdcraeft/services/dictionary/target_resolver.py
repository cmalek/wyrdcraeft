"""Phase 04 target resolver for Bosworth-Toller editorial cross-references."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

from ...models.dictionary import BTPos
from ..markup import normalize_old_english
from .sense_tree import RawSenseFragment, SenseTreeNormalizer

if TYPE_CHECKING:
    from ...models.dictionary import BTSense
    from .line_parser import ParsedBTLine
    from .source_blocks import BTSourceBlock

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

#: Roman-numeral sense label with optional lowercase suffix.
_ROMAN_LABEL_RE: Final[re.Pattern[str]] = re.compile(
    r"^[IVX]+(?:[\s.][a-z]|[a-z])?$",
    re.IGNORECASE,
)


class BTTargetResolver:
    """
    Resolve editorial target references in Bosworth-Toller supplement lines.

    Parses ``for X in Dict`` phrases from editorial line bodies and normalises
    the extracted target name using
    :func:`~wyrdcraeft.services.markup.normalize_old_english` to obtain a
    stable lookup key.  Editorial lines without explicit targets fall back to
    the nearest preceding compatible dictionary source block.  Roman sense labels
    map to canonical ``sense_path`` values such as ``1`` or ``4.1``.

    Args:
        normalizer: Optional sense-tree normalizer collaborator.

    """

    def __init__(self, normalizer: SenseTreeNormalizer | None = None) -> None:
        """
        Initialise the resolver with an optional sense-tree normalizer.

        Args:
            normalizer: Optional sense-tree normalizer collaborator.

        """
        #: Sense-tree normalizer collaborator.
        self.normalizer: SenseTreeNormalizer = normalizer or SenseTreeNormalizer()

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
        Return the legacy ``(norm_key, pos)`` merge key for a parsed line.

        Uses the line's own headword (not any editorial target).  New dictionary
        builds group by source block instead of this key, but cross-reference
        handling still uses it as a fallback lookup.

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

    def resolve_block_for_line(  # noqa: PLR0911
        self,
        line: ParsedBTLine,
        blocks: list[BTSourceBlock],
    ) -> BTSourceBlock | None:
        """
        Resolve the dictionary source block for one editorial line.

        Resolution order:
        1. Explicit ``for X in Dict`` target when it maps to exactly one block.
        2. Nearest preceding block sharing the line's ``norm_key`` and, when
           known, the same ``pos``.
        3. ``None`` when no compatible block exists.

        Args:
            line: Parsed editorial line to attach.
            blocks: Source blocks built so far in document order.

        Returns:
            Target block, or ``None`` when attachment is impossible.

        """
        if line.raw_line is None or not blocks:
            return None

        explicit_target = self.resolve_target_norm_key(line)
        if line.editorial_target and explicit_target:
            matches = [block for block in blocks if block.norm_key == explicit_target]
            if len(matches) == 1:
                return matches[0]
            if len(matches) > 1:
                return None

        norm_key = normalize_old_english(line.raw_line.headword_raw)
        if not norm_key:
            return None

        candidates = [block for block in blocks if block.norm_key == norm_key]
        if not candidates:
            return None

        if line.pos != BTPos.UNKNOWN:
            pos_matches = [block for block in candidates if block.pos == line.pos]
            if len(pos_matches) == 1:
                return self._nearest_preceding_block(line, pos_matches)
            if len(pos_matches) > 1:
                return self._nearest_preceding_block(line, pos_matches)

        return self._nearest_preceding_block(line, candidates)

    def resolve_sense_path(
        self,
        label: str,
        senses: list[BTSense],
    ) -> str | None:
        """
        Map one Roman sense label to a canonical ``sense_path``.

        When the label matches an existing sense in *senses*, that sense's path
        is returned.  Otherwise the label is normalised in isolation via
        :class:`~wyrdcraeft.services.dictionary.sense_tree.SenseTreeNormalizer`.

        Args:
            label: Roman-numeral or letter label such as ``I`` or ``IVa``.
            senses: Current senses for the target entry block.

        Returns:
            Canonical sense path such as ``1`` or ``4.1``, or ``None``.

        """
        cleaned = label.strip().rstrip(".")
        if not cleaned:
            return None

        for sense in senses:
            if sense.source_label_raw.rstrip(".").lower() == cleaned.lower():
                return sense.sense_path

        normalized = self.normalizer.normalize(
            [
                RawSenseFragment(
                    source_label_raw=cleaned,
                    source_fragment_raw="",
                )
            ]
        )
        if not normalized:
            return None
        return normalized[0].sense_path

    def resolve_sense_paths_for_refs(
        self,
        refs: list[str],
        senses: list[BTSense],
    ) -> tuple[list[str], str]:
        """
        Resolve deletion/substitution references to canonical sense paths.

        Args:
            refs: Raw reference strings from one editorial line.
            senses: Current senses for the target entry block.

        Returns:
            Tuple of resolved paths and a diagnostic note.  The note is
            ``target_ambiguous`` when multiple senses match one reference,
            ``target_missing`` when no reference resolves, or empty on success.

        """
        resolved: list[str] = []
        missing = False
        ambiguous = False

        for ref in refs:
            ref_clean = ref.strip().rstrip(".")
            if not ref_clean:
                continue
            if not _ROMAN_LABEL_RE.match(ref_clean):
                missing = True
                continue

            label_matches = [
                sense.sense_path
                for sense in senses
                if sense.source_label_raw.rstrip(".").lower() == ref_clean.lower()
            ]
            if len(label_matches) == 1:
                resolved.append(label_matches[0])
                continue
            if len(label_matches) > 1:
                ambiguous = True
                continue

            path = self.resolve_sense_path(ref_clean, senses)
            if path is None:
                missing = True
                continue
            resolved.append(path)

        if ambiguous:
            return resolved, "target_ambiguous"
        if missing and not resolved:
            return resolved, "target_missing"
        if missing:
            return resolved, "target_missing"
        return resolved, ""

    @staticmethod
    def _nearest_preceding_block(
        line: ParsedBTLine,
        candidates: list[BTSourceBlock],
    ) -> BTSourceBlock | None:
        """
        Return the nearest preceding candidate block for *line*.

        Args:
            line: Parsed editorial line requesting attachment.
            candidates: Compatible blocks sharing lookup identity.

        Returns:
            Last candidate whose max line number precedes *line*, or ``None``.

        """
        if line.raw_line is None:
            return None
        line_no = line.raw_line.line_no
        preceding = [
            block for block in candidates if block.max_line_no < line_no
        ]
        if not preceding:
            return None
        return preceding[-1]
