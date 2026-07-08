"""Phase 02 parser for Bosworth-Toller raw source lines."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Final

from ...models.dictionary import BTGender, BTLineKind, BTPos, BTSense, RawBTLine
from ..markup import BOLD_HEADWORD_RE, TRAILING_HEADWORD_PUNCT_RE, _is_oe_wordlike
from .bt_spelling import BTSpellingNormalizer
from .line_splitter import BTLineSplitter, BTSplitLine
from .pos_gender import BTPosGenderExtractor

#: ``<I>Add:</I>``, ``<I>Add :</I>``, or ``<I>Add</I>`` marker.
_ADD_RE: Final[re.Pattern[str]] = re.compile(r"<I>\s*Add\s*:?\s*</I>", re.IGNORECASE)
#: ``Substitute`` marker (typically in italic tags).
_SUBSTITUTE_RE: Final[re.Pattern[str]] = re.compile(r"\bSubstitute\b", re.IGNORECASE)
#: ``Dele`` marker (typically in italic tags).
_DELE_RE: Final[re.Pattern[str]] = re.compile(r"<I>\s*Dele\b[^<]*</I>", re.IGNORECASE)
#: ``v.`` or ``vide`` cross-reference marker.
_CROSS_REF_RE: Final[re.Pattern[str]] = re.compile(
    r"(?:\sv\.\s|\svide\s)",
    re.IGNORECASE,
)
#: Prefix delimiter used to stop POS-fragment extraction.
_POS_STOP_RE: Final[re.Pattern[str]] = re.compile(
    r":--|<B>\s*[IVX]+(?:\s+[a-z])?\.\s*</B>"
)
#: Variant candidate regex from the non-italic prefix between headword and POS.
_VARIANT_RE: Final[re.Pattern[str]] = re.compile(r"[^\s,;()]+")
#: Inline tags remover for editorial and cross-ref extraction.
_TAG_RE: Final[re.Pattern[str]] = re.compile(r"<[^>]+>")
#: Extracts ``for X in Dict`` substitute target text.
_EDITORIAL_TARGET_RE: Final[re.Pattern[str]] = re.compile(
    r"for\s+(.+?)\s+in\s+Dict",
    re.IGNORECASE,
)
#: Bracket block extraction for trailing etymology capture.
_BRACKET_BLOCK_RE: Final[re.Pattern[str]] = re.compile(r"\[[^\[\]]+\]")
#: Detect trailing bracket blocks region in a line body.
_TRAILING_BRACKETS_RE: Final[re.Pattern[str]] = re.compile(r"(?:\s*\[[^\[\]]+\]\s*)+$")
#: Whitespace normalizer for skip reasons and extracted fragments.
_WS_RE: Final[re.Pattern[str]] = re.compile(r"\s+")
#: Splits compound bold headwords such as ``mægþ, mægeþ;``.
_HEADWORD_FORM_SPLIT_RE: Final[re.Pattern[str]] = re.compile(r"[,;]+")
#: Strips editorial sense anchors from bold headwords such as ``mǣgþ. I.``.
_EDITORIAL_HEADWORD_SENSE_SUFFIX_RE: Final[re.Pattern[str]] = re.compile(
    r"^(.+?)\.\s*([IVX]+(?:\s+[a-z])?|[A-Z])\.\s*$"
)


def _split_headword_forms(capture: str) -> tuple[str, tuple[str, ...]] | None:
    """
    Split one bold headword capture into canonical and variant spellings.

    Bosworth-Toller often lists multiple spellings inside the first ``<B>`` tag
    (for example ``mægþ, mægeþ;``). Editorial add lines may instead anchor a
    sense label in the bold tag (for example ``mǣgþ. I.``).

    Args:
        capture: Raw text from the first ``<B>…</B>`` match.

    Returns:
        Canonical headword plus any additional spellings from the bold tag, or
        ``None`` when no wordlike form is present.

    """
    stripped = capture.strip()
    sense_suffix = _EDITORIAL_HEADWORD_SENSE_SUFFIX_RE.match(stripped)
    if sense_suffix is not None:
        cleaned = TRAILING_HEADWORD_PUNCT_RE.sub("", sense_suffix.group(1).strip())
    else:
        cleaned = TRAILING_HEADWORD_PUNCT_RE.sub("", stripped)

    forms: list[str] = []
    seen: set[str] = set()
    for fragment in _HEADWORD_FORM_SPLIT_RE.split(cleaned):
        candidate = TRAILING_HEADWORD_PUNCT_RE.sub("", fragment.strip())
        if not candidate or not _is_oe_wordlike(candidate):
            continue
        lowered = candidate.casefold()
        if lowered in seen:
            continue
        seen.add(lowered)
        forms.append(candidate)
    if not forms:
        return None
    return forms[0], tuple(forms[1:])


@dataclass(frozen=True)
class ParsedBTLine:
    """
    Parsed line payload produced by :class:`BTLineParser`.

    Carries the ``RawBTLine`` record plus phase-02 metadata.  Phase 03
    populates :attr:`senses` via
    :class:`~wyrdcraeft.services.dictionary.sense_segmenter.BTSenseSegmenter`;
    the field defaults to an empty tuple so phase-02 callers need no changes.

    Attributes:
        raw_line: Base raw-line record consumed by later phases.
        lookup_keys: Lookup aliases from the first ``@`` field.
        slug_field: Third ``@`` field from source.
        headword_macronized: Display-normalized headword spelling.
        variants: Macronized variant spellings between ``</B>`` and POS markers.
        pos: Normalized part-of-speech from the prefix fragment.
        genders: Parsed noun genders (empty when not applicable).
        editorial_target: Parsed target from ``Substitute ... for X in Dict``.
        dele_refs: Parsed deletion references from ``Dele`` fragments.
        etymology_blocks: Trailing ``[...]`` blocks preserved as raw text.
        senses: Ordered English gloss senses; empty until phase 03 populates it.
        segment_warnings: Segmentation warning codes from phase 03.
        skip_reason: Non-empty when line was skipped.

    """

    #: Raw line model used by downstream parsers.
    raw_line: RawBTLine | None
    #: Parsed lookup aliases from field 1.
    lookup_keys: tuple[str, ...]
    #: Parsed slug field from field 3.
    slug_field: str
    #: Display-normalized headword spelling.
    headword_macronized: str
    #: Variant spellings near the headword prefix.
    variants: tuple[str, ...]
    #: Normalized part of speech.
    pos: BTPos
    #: Parsed genders in source order.
    genders: tuple[BTGender, ...]
    #: Parsed target entry for substitute lines.
    editorial_target: str | None
    #: Parsed delete targets.
    dele_refs: tuple[str, ...]
    #: Trailing raw bracket blocks.
    etymology_blocks: tuple[str, ...]
    #: Ordered sense glosses populated by phase 03 segmentation; empty by default.
    senses: tuple[BTSense, ...] = field(default_factory=tuple)
    #: Segmentation warning codes emitted by phase 03; empty by default.
    segment_warnings: tuple[str, ...] = field(default_factory=tuple)
    #: Skip reason string when parsing was rejected.
    skip_reason: str | None = None


class BTLineParser:
    """
    Parse Bosworth-Toller lines into deterministic phase-02 records.

    Args:
        splitter: Optional ``@`` field splitter implementation.
        pos_gender_extractor: Optional POS/gender extraction service.

    """

    def __init__(
        self,
        splitter: BTLineSplitter | None = None,
        pos_gender_extractor: BTPosGenderExtractor | None = None,
        spelling_normalizer: BTSpellingNormalizer | None = None,
    ) -> None:
        """
        Initialize parser collaborators for split and POS extraction.

        Args:
            splitter: Optional ``@``-field splitter service.
            pos_gender_extractor: Optional POS/gender extraction service.
            spelling_normalizer: Optional BT display spelling normalizer.

        """
        #: ``@``-field splitting collaborator.
        self.splitter = splitter or BTLineSplitter()
        #: Prefix POS/gender extraction collaborator.
        self.pos_gender_extractor = pos_gender_extractor or BTPosGenderExtractor()
        #: BT display spelling normalizer for headword and variants.
        self.spelling_normalizer = spelling_normalizer or BTSpellingNormalizer()

    def parse(self, source_line_no: int, line: str) -> ParsedBTLine:
        """
        Parse one source line into ``RawBTLine`` plus phase-02 metadata.

        Args:
            source_line_no: One-based source line number.
            line: Raw line from ``oe_bt.txt``.

        Returns:
            Parsed line payload. ``raw_line`` is ``None`` when the line is skipped.

        """
        split_line = self.splitter.split(line)
        if split_line is None:
            return self._skip("not 3 @ fields")

        headword_match = BOLD_HEADWORD_RE.search(split_line.body)
        if headword_match is None:
            return self._skip("no <B> headword")

        headword_forms = _split_headword_forms(headword_match.group(1))
        if headword_forms is None:
            return self._skip("headword not wordlike")
        headword_raw, bold_variants = headword_forms
        headword_macronized = self.spelling_normalizer.normalize(headword_raw)

        pos_fragment = self._extract_pos_fragment(split_line, headword_match.end())
        kind = self._classify_kind(split_line.body)
        pos_gender = self.pos_gender_extractor.extract(pos_fragment)

        raw_line = RawBTLine(
            line_no=source_line_no,
            kind=kind,
            headword_raw=headword_raw,
            pos_fragment=pos_fragment,
            raw_text=split_line.body,
        )
        prefix_variants = self._extract_variants(
            headword_raw=headword_raw,
            pos_fragment=pos_fragment,
        )
        return ParsedBTLine(
            raw_line=raw_line,
            lookup_keys=split_line.lookup_keys,
            slug_field=split_line.slug_field,
            headword_macronized=headword_macronized,
            variants=self._normalize_variants(bold_variants + prefix_variants),
            pos=pos_gender.pos,
            genders=pos_gender.genders,
            editorial_target=self._extract_editorial_target(split_line.body),
            dele_refs=self._extract_dele_refs(split_line.body),
            etymology_blocks=self._extract_etymology_blocks(split_line.body),
            skip_reason=None,
        )

    def _classify_kind(self, body: str) -> BTLineKind:
        """
        Classify one line into ``BTLineKind``.

        Args:
            body: Main ``@`` field body content.

        Returns:
            Deterministic line kind classification.

        """
        has_add = _ADD_RE.search(body) is not None
        has_substitute = _SUBSTITUTE_RE.search(body) is not None
        has_dele = _DELE_RE.search(body) is not None
        has_and_add = re.search(r"\band add\b", body, re.IGNORECASE) is not None

        if has_substitute:
            return BTLineKind.SUBSTITUTE
        if has_dele and (has_add or has_and_add):
            return BTLineKind.DELE_AND_ADD
        if has_dele:
            return BTLineKind.DELE
        if has_add:
            return BTLineKind.ADD
        if self._is_cross_ref(body):
            return BTLineKind.CROSS_REF
        return BTLineKind.MAIN

    def _is_cross_ref(self, body: str) -> bool:
        """
        Detect whether a line is primarily a cross-reference.

        Args:
            body: Main ``@`` field body content.

        Returns:
            ``True`` when line appears to be an abbreviated ``v.`` / ``vide`` link.

        """
        if _CROSS_REF_RE.search(body) is None:
            return False
        return ":--" not in body

    def _extract_pos_fragment(self, split_line: BTSplitLine, headword_end: int) -> str:
        """
        Extract the POS prefix fragment immediately after the first headword.

        Args:
            split_line: Pre-split line fields.
            headword_end: End index of first ``</B>`` match in ``body``.

        Returns:
            Prefix fragment used by POS/gender extraction.

        """
        after_head = split_line.body[headword_end:]
        stop_match = _POS_STOP_RE.search(after_head)
        if stop_match is None:
            return after_head.strip()
        return after_head[: stop_match.start()].strip()

    def _extract_variants(
        self,
        headword_raw: str,
        pos_fragment: str,
    ) -> tuple[str, ...]:
        """
        Extract alternate headword spellings from the pre-POS plain-text prefix.

        Args:
            headword_raw: Parsed first bold headword.
            pos_fragment: Prefix fragment after the first ``</B>``.

        Returns:
            Variant spellings in source order.

        """
        plain_prefix = pos_fragment.split("<I>", maxsplit=1)[0]
        variants: list[str] = []
        seen: set[str] = set()
        for match in _VARIANT_RE.finditer(plain_prefix):
            candidate = TRAILING_HEADWORD_PUNCT_RE.sub("", match.group(0).strip())
            if not candidate or not _is_oe_wordlike(candidate):
                continue
            if candidate.lower() == headword_raw.lower():
                continue
            if candidate.casefold() in {"es", "as", "an", "a", "e", "um"}:
                continue
            lowered = candidate.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            variants.append(candidate)
        return tuple(variants)

    def _normalize_variants(self, variants: tuple[str, ...]) -> tuple[str, ...]:
        """
        Apply display spelling normalization to variants with de-duplication.

        Args:
            variants: Raw extracted variant spellings in source order.

        Returns:
            Macronized variants preserving first-seen order.

        """
        normalized: list[str] = []
        seen: set[str] = set()
        for variant in variants:
            macronized = self.spelling_normalizer.normalize(variant)
            lowered = macronized.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            normalized.append(macronized)
        return tuple(normalized)

    def _extract_editorial_target(self, body: str) -> str | None:
        """
        Extract substitute target text from ``for X in Dict`` patterns.

        Args:
            body: Main ``@`` field body content.

        Returns:
            Target text when present, otherwise ``None``.

        """
        match = _EDITORIAL_TARGET_RE.search(body)
        stripped = _TAG_RE.sub(" ", body)
        match = _EDITORIAL_TARGET_RE.search(stripped)
        if match is None:
            return None
        return _WS_RE.sub(" ", match.group(1)).strip(" .,;:")

    def _extract_dele_refs(self, body: str) -> tuple[str, ...]:
        """
        Extract reference fragments listed after ``Dele`` markers.

        Args:
            body: Main ``@`` field body content.

        Returns:
            Deletion target fragments in source order.

        """
        marker = _DELE_RE.search(body)
        if marker is None:
            return ()
        tail = body[marker.end() :]
        tail = _TAG_RE.sub("", tail)
        for stopper in ("and add", "and see", " v. ", " vide ", ":--"):
            index = tail.lower().find(stopper)
            if index != -1:
                tail = tail[:index]
        refs = []
        for fragment in re.split(r"[;,]", tail):
            cleaned = _WS_RE.sub(" ", fragment).strip(" .:")
            if cleaned:
                refs.append(cleaned)
        return tuple(refs)

    def _extract_etymology_blocks(self, body: str) -> tuple[str, ...]:
        """
        Extract trailing bracket etymology blocks from the line body.

        Args:
            body: Main ``@`` field body content.

        Returns:
            Raw bracket blocks in source order.

        """
        trailing = _TRAILING_BRACKETS_RE.search(body)
        if trailing is None:
            return ()
        return tuple(_BRACKET_BLOCK_RE.findall(trailing.group(0)))

    def _skip(self, reason: str) -> ParsedBTLine:
        """
        Build a skipped parse result with the provided reason.

        Args:
            reason: Human-readable skip explanation.

        Returns:
            Skipped parsed-line payload.

        """
        return ParsedBTLine(
            raw_line=None,
            lookup_keys=(),
            slug_field="",
            headword_macronized="",
            variants=(),
            pos=BTPos.UNKNOWN,
            genders=(),
            editorial_target=None,
            dele_refs=(),
            etymology_blocks=(),
            skip_reason=reason,
        )
