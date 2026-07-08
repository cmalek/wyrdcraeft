"""Phase 03 sense segmenter for Bosworth-Toller line bodies."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from wyrdcraeft.models.dictionary import BTSense

from ..dictionary.attestation_stripper import BTAttestationStripper
from .sense_metadata import SenseMetadataClassifier
from .sense_tree import CanonicalSenseFragment, RawSenseFragment, SenseTreeNormalizer

#: Matches bold sense-label tags in the BT supplement format.
#:
#: Handles all observed variants:
#: - ``<B>I.</B>`` -- Roman numeral (I, II, III, IV, V, ...)
#: - ``<B>II a.</B>`` -- Roman + lowercase letter sub-sense
#: - ``<B>A.</B>``, ``<B>B.</B>`` -- single capital letter
#: - ``<B>B. I.</B>``, ``<B>B. IV.</B>`` -- capital letter + Roman
#: - ``<B>I</B>.`` -- period placed outside the bold tag (rare variant)
_BOLD_SENSE_RE: Final[re.Pattern[str]] = re.compile(
    r"<B>\s*"
    r"("
    r"[IVX]+(?:\s+[a-z])?\.?"  # Roman numeral + optional sub-letter: I, II, II a
    r"|[A-Z](?:\.\s*[IVX]+(?:\s+[a-z])?)?\.?"  # Letter/Letter+Roman: A, B, B. I
    r")"
    r"\s*</B>(?P<ext>\.?)"  # closing </B>, capture trailing period
)

#: Matches plain (unbolded) sense labels in the older BT main-dictionary format.
#:
#: The plain label must be preceded by whitespace (or start-of-string) and
#: immediately followed by an italic open tag, which distinguishes it from
#: Roman-numeral references in source citations.
_PLAIN_SENSE_RE: Final[re.Pattern[str]] = re.compile(
    r"(?:(?<=\s)|^)"
    r"([IVX]+(?:\s+[a-z])?)\."
    r"(?=\s+<[Ii]>)"
)

#: Strips any HTML tags for post-processing.
_TAG_RE: Final[re.Pattern[str]] = re.compile(r"<[^>]+>")

#: Collapses whitespace.
_WS_RE: Final[re.Pattern[str]] = re.compile(r"\s+")

#: Minimum gloss character length to treat a segment as a real sense.
_MIN_GLOSS_LEN: Final[int] = 2


@dataclass(frozen=True)
class BTSegmentResult:
    """
    Segmented senses plus diagnostics emitted during one body parse.

    Attributes:
        senses: Ordered sense records extracted from the body.
        warnings: Machine-readable segmentation warning codes in source order.

    """

    #: Ordered sense records extracted from the body.
    senses: tuple[BTSense, ...]
    #: Segmentation warning codes such as ``modifier_only_fragment``.
    warnings: tuple[str, ...] = ()


def _normalise_label(raw: str, ext: str = "") -> str:
    """
    Strip markup from a raw sense-label capture and normalise spacing.

    Args:
        raw: Raw label text from a regex capture group.
        ext: Optional trailing period character captured outside ``</B>``.

    Returns:
        Normalised sense label without surrounding whitespace or punctuation.

    """
    label = _WS_RE.sub(" ", raw.strip())
    # Add period back if it was outside </B>
    if ext == "." and not label.endswith("."):
        label = label + "."
    # Strip trailing period from final label text
    return label.rstrip(".")


def _source_label_raw(label: str) -> str:
    """
    Format a normalized label for ``source_label_raw`` storage.

    Args:
        label: Normalized sense label without trailing period.

    Returns:
        Source label text with a trailing period when non-empty.

    """
    if not label:
        return ""
    return label if label.endswith(".") else f"{label}."


def _split_body(body: str) -> list[tuple[str, int]]:
    """
    Find all sense-boundary positions in *body*, returning ``(label, pos)`` pairs.

    Bold-wrapped labels are preferred.  If none are found, plain Roman-numeral
    labels followed by an italic span are used as a fallback.

    Args:
        body: Raw ``@``-field body content from ``oe_bt.txt``.

    Returns:
        Ordered list of ``(label, start_position)`` tuples for each sense boundary.

    """
    splits: list[tuple[str, int]] = []

    for m in _BOLD_SENSE_RE.finditer(body):
        raw = m.group(1)
        ext = m.group("ext") or ""
        label = _normalise_label(raw, ext)
        splits.append((label, m.start()))

    if not splits:
        for m in _PLAIN_SENSE_RE.finditer(body):
            label = m.group(1).strip()
            splits.append((label, m.start()))

    return splits


def _split_raw_fragments(body: str) -> list[RawSenseFragment]:
    """
    Split a body field into ordered raw sense fragments.

    Args:
        body: Raw HTML body field from one ``oe_bt.txt`` line.

    Returns:
        Ordered raw fragments preserving source labels and fragment text.

    """
    splits = _split_body(body)
    if not splits:
        return []

    fragments: list[RawSenseFragment] = []
    for i, (label, start) in enumerate(splits):
        end = splits[i + 1][1] if i + 1 < len(splits) else len(body)
        fragments.append(
            RawSenseFragment(
                source_label_raw=_source_label_raw(label),
                source_fragment_raw=body[start:end].strip(),
            )
        )
    return fragments


class BTSenseSegmenter:
    """
    Split a Bosworth-Toller line body into ordered English-gloss senses.

    Identifies sense boundaries via ``<B>I.</B>``-style labels (or plain
    ``I.`` labels in the older BT format), normalizes hierarchical sense paths,
    then delegates each sense-block body to
    :class:`~wyrdcraeft.services.dictionary.attestation_stripper.BTAttestationStripper`
    to remove OE/Latin attestation tails.

    Args:
        stripper: Optional attestation-stripping collaborator.
        normalizer: Optional sense-tree normalizer collaborator.
        metadata_classifier: Optional sense-prefix metadata classifier.

    """

    def __init__(
        self,
        stripper: BTAttestationStripper | None = None,
        normalizer: SenseTreeNormalizer | None = None,
        metadata_classifier: SenseMetadataClassifier | None = None,
    ) -> None:
        """
        Initialise with optional attestation-stripper and normalizer collaborators.

        Args:
            stripper: Optional pre-built attestation stripper.
            normalizer: Optional sense-tree normalizer.
            metadata_classifier: Optional sense-prefix metadata classifier.

        """
        #: Attestation stripper collaborator.
        self.stripper: BTAttestationStripper = stripper or BTAttestationStripper()
        #: Sense-tree normalizer collaborator.
        self.normalizer: SenseTreeNormalizer = normalizer or SenseTreeNormalizer()
        #: Sense-prefix metadata classifier collaborator.
        self.metadata_classifier: SenseMetadataClassifier = (
            metadata_classifier or SenseMetadataClassifier()
        )

    def segment(self, body: str) -> list[BTSense]:
        """
        Return an ordered list of :class:`~wyrdcraeft.models.dictionary.BTSense`
        for *body*.

        When no sense-boundary markers are found the entire body is treated as
        a single unlabelled sense.  The sense order matches the source document.

        Args:
            body: Raw HTML body field from one ``oe_bt.txt`` line.

        Returns:
            Ordered list of ``BTSense`` records with English-only glosses.

        """
        return list(self.segment_with_warnings(body).senses)

    def segment_with_warnings(self, body: str) -> BTSegmentResult:
        """
        Segment one body and return senses plus segmentation diagnostics.

        Args:
            body: Raw HTML body field from one ``oe_bt.txt`` line.

        Returns:
            Segmented senses and any warning codes emitted during parsing.

        """
        raw_fragments = _split_raw_fragments(body)

        if not raw_fragments:
            return self._segment_unlabeled_body(body)

        canonical_fragments = self.normalizer.normalize(raw_fragments)

        senses: list[BTSense] = []
        warnings: list[str] = []
        for fragment in canonical_fragments:
            if fragment.warnings:
                warnings.append("orphan_source_label_depth_fallback")
            sense, sense_warnings = self._build_sense(fragment)
            warnings.extend(sense_warnings)
            if sense is not None:
                senses.append(sense)

        return BTSegmentResult(senses=tuple(senses), warnings=tuple(warnings))

    def _segment_unlabeled_body(self, body: str) -> BTSegmentResult:
        """
        Segment a body with no explicit sense labels into zero or one senses.

        Args:
            body: Raw HTML body field from one ``oe_bt.txt`` line.

        Returns:
            Segmentation result containing zero or one sense plus warnings.

        """
        sense, warnings = self._build_sense_from_body(
            body.strip(),
            sense_path="1",
            parent_path=None,
            source_label_raw="",
            source_fragment_raw=body.strip(),
        )
        if sense is None:
            return BTSegmentResult(senses=(), warnings=tuple(warnings))
        return BTSegmentResult(senses=(sense,), warnings=tuple(warnings))

    def _build_sense(
        self,
        fragment: CanonicalSenseFragment,
    ) -> tuple[BTSense | None, tuple[str, ...]]:
        """
        Build one :class:`~wyrdcraeft.models.dictionary.BTSense` from a fragment.

        Args:
            fragment: Canonical sense fragment from the tree normalizer.

        Returns:
            Parsed sense record and any warning codes, or ``None`` when no gloss.

        """
        segment_body = fragment.source_fragment_raw
        segment_body = _BOLD_SENSE_RE.sub("", segment_body, count=1)
        segment_body = _PLAIN_SENSE_RE.sub("", segment_body, count=1)
        return self._build_sense_from_body(
            segment_body.strip(),
            sense_path=fragment.sense_path,
            parent_path=fragment.parent_path,
            source_label_raw=fragment.source_label_raw.rstrip("."),
            source_fragment_raw=fragment.source_fragment_raw,
        )

    def _build_sense_from_body(
        self,
        segment_body: str,
        *,
        sense_path: str,
        parent_path: str | None,
        source_label_raw: str,
        source_fragment_raw: str,
    ) -> tuple[BTSense | None, tuple[str, ...]]:
        """
        Classify prefix metadata and extract one sense gloss from *segment_body*.

        Args:
            segment_body: Raw HTML sense body with sense labels already removed.

        Keyword Args:
            sense_path: Canonical hierarchical sense path.
            parent_path: Parent sense path when nested.
            source_label_raw: Raw source sense label.
            source_fragment_raw: Raw source fragment for provenance.

        Returns:
            Parsed sense record and warning codes, or ``None`` when debris remains.

        """
        metadata = self.metadata_classifier.classify(segment_body)
        warnings: list[str] = []
        if "prefix_only_no_gloss" in metadata.warnings:
            warnings.append("modifier_only_fragment")
            return None, tuple(warnings)
        gloss = self.stripper.strip(metadata.remainder)
        if len(gloss) < _MIN_GLOSS_LEN:
            return None, tuple(warnings)
        return (
            BTSense(
                gloss_en=gloss,
                sense_path=sense_path,
                parent_path=parent_path,
                source_label_raw=source_label_raw,
                source_fragment_raw=source_fragment_raw,
                prefix_fragment_raw=metadata.prefix_fragment_raw,
                modifiers=metadata.modifiers,
                grammatical_context=metadata.grammatical_context,
                usage_note=metadata.usage_note,
            ),
            tuple(warnings),
        )

    def segment_parsed_line(
        self,
        body: str,
    ) -> BTSegmentResult:
        """
        Segment one body for ``ParsedBTLine`` construction.

        Args:
            body: Raw HTML body field from one ``oe_bt.txt`` line.

        Returns:
            Segmented senses and segmentation warning codes.

        """
        return self.segment_with_warnings(body)
