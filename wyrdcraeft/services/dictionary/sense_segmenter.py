"""Phase 03 sense segmenter for Bosworth-Toller line bodies."""

from __future__ import annotations

import re
from typing import Final

from ...models.dictionary import BTSense
from ..dictionary.attestation_stripper import BTAttestationStripper

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


class BTSenseSegmenter:
    """
    Split a Bosworth-Toller line body into ordered English-gloss senses.

    Identifies sense boundaries via ``<B>I.</B>``-style labels (or plain
    ``I.`` labels in the older BT format), then delegates each sense-block body to
    :class:`~wyrdcraeft.services.dictionary.attestation_stripper.BTAttestationStripper`
    to remove OE/Latin attestation tails.

    Args:
        stripper: Optional attestation-stripping collaborator.

    """

    def __init__(self, stripper: BTAttestationStripper | None = None) -> None:
        """
        Initialise with an optional attestation-stripper collaborator.

        Args:
            stripper: Optional pre-built attestation stripper.

        """
        #: Attestation stripper collaborator.
        self.stripper: BTAttestationStripper = stripper or BTAttestationStripper()

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
        splits = _split_body(body)

        if not splits:
            gloss = self.stripper.strip(body)
            if gloss:
                return [BTSense(sense_label="", gloss_en=gloss)]
            return []

        senses: list[BTSense] = []
        for i, (label, start) in enumerate(splits):
            end = splits[i + 1][1] if i + 1 < len(splits) else len(body)
            segment_body = body[start:end]
            # Strip the opening label tag so the stripper sees only the body text
            segment_body = _BOLD_SENSE_RE.sub("", segment_body, count=1)
            segment_body = _PLAIN_SENSE_RE.sub("", segment_body, count=1)
            gloss = self.stripper.strip(segment_body.strip())
            if len(gloss) >= _MIN_GLOSS_LEN:
                senses.append(BTSense(sense_label=label, gloss_en=gloss))

        return senses

    def segment_parsed_line(
        self,
        body: str,
    ) -> tuple[BTSense, ...]:
        """
        Convenience wrapper returning a tuple of senses for use in ``ParsedBTLine``.

        Args:
            body: Raw HTML body field from one ``oe_bt.txt`` line.

        Returns:
            Tuple of :class:`~wyrdcraeft.models.dictionary.BTSense` records.

        """
        return tuple(self.segment(body))
