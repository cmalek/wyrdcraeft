"""Phase 03 attestation stripper for Bosworth-Toller sense blocks."""

from __future__ import annotations

import re
from typing import Final

#: Matches the canonical attestation separator ``:--`` (space before ``--`` optional).
_ATTEST_SEP_RE: Final[re.Pattern[str]] = re.compile(r":\s*--")

#: Italic span extractor — non-greedy, single-line.
_ITALIC_SPAN_RE: Final[re.Pattern[str]] = re.compile(r"<[Ii]>(.*?)</[Ii]>")

#: Strips any remaining HTML tags.
_TAG_RE: Final[re.Pattern[str]] = re.compile(r"<[^>]+>")

#: Bracket etymology blocks ``[...]`` (may contain inline italic tags).
_BRACKET_BLOCK_RE: Final[re.Pattern[str]] = re.compile(r"\[[^\[\]]*\]")

#: Collapses runs of whitespace.
_WS_RE: Final[re.Pattern[str]] = re.compile(r"\s+")

#: Source-abbreviation patterns (Ps., Chr., Gen., Bt., Gr. D., Ors., Hml., ...).
_SOURCE_ABBR_RE: Final[re.Pattern[str]] = re.compile(
    r"\b(?:Ps|Chr|Gen|Bt|Gr|Ors|Hml|Exon|Bd|Mt|Mk|Lk|Jn|Cd|El|An|Beo|Sal"
    r"|Nar|Angl|Wrt|Scint|Bl|Germ|Hy|Rtl|Shrn|Lch|Ælfc|Deut"
    r"|Kmbl|Th|Spl|Grn|Lind|War|Bos|Srt|Rdr|Hpt|Sch|Txts)\b",
    re.IGNORECASE,
)

#: OE-specific Unicode codepoints: macron vowels, ash, thorn, eth, wynn.
_OE_CHARS_RE: Final[re.Pattern[str]] = re.compile(
    r"[āēīōūǣæÆÐðÞþĀĒĪŌŪǢ]"
)

#: Grammatical abbreviation patterns that identify non-gloss italic spans.
_GRAM_ABBREV_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?:"
    r"m\.?|f\.?|n\.?|m\s*:|f\s*:|n\s*:"  # gender markers
    r"|adj\.?|adv\.?|prep\.?|conj\.?|interj\.?|pron\.?|indecl\.?"  # POS abbrevs
    r"|p\.?|pp\.?|pl\.?|sg\.?|ptcpl\.?"  # inflection abbrevs
    r"|v\.?\s*(?:trans|intrans|a|n|refl|def)?\.?"  # verb class abbrevs
    r"|dat\.?|acc\.?|gen\.?|nom\.?|voc\.?"  # case abbrevs
    r"|impert\.?|impt\.?|subj\.?|indic\.?|pres\.?|inf\.?"  # mood/tense
    r"|reflex\.?|comp\.?|superl\.?"  # other gram abbrevs
    r")$",
    re.IGNORECASE,
)

#: Editorial directives that identify supplement-marker italic spans.
#: These spans carry no English gloss content.
_EDITORIAL_MARKER_SET: Final[frozenset[str]] = frozenset(
    {"add", "dele", "omit", "substitute", "substitute the following"}
)

#: Leading editorial directive prefix stripped from combined directive-gloss spans.
#: E.g. ``Substitute: A property`` -> ``A property``.
_EDITORIAL_DIRECTIVE_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?:Substitute(?:\s+the\s+following)?:|Add(?:\s+and\s+see)?:?|Dele\.?|Omit\.?)\s*",
    re.IGNORECASE,
)

#: Leading grammatical marker prefix stripped from combined gender-gloss italic spans.
#: E.g. ``f. An oak`` -> ``An oak``.
_LEADING_GRAM_PREFIX_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?:m\.|f\.|n\.|adj\.|adv\.|prep\.|conj\.|interj\.|pron\.|indecl\."
    r"|v\.\s*(?:trans|intrans|a|n|refl)?\.?|p\.|pp\.|pl\.|sg\.)\s+",
    re.IGNORECASE,
)

#: Maximum length considered "short abbreviation-only" for citation-span detection.
_MAX_ABBREV_LEN: Final[int] = 6

#: Minimum plain-text length for substantive sense-body warning heuristics.
_MIN_SUBSTANTIVE_BODY_LEN: Final[int] = 20
#: Minimum gloss length before low-confidence attestation warnings fire.
_MIN_GLOSS_LEN: Final[int] = 3
#: Minimum source body length for short-gloss low-confidence warnings.
_MIN_BODY_LEN_FOR_SHORT_GLOSS: Final[int] = 80
#: Maximum gloss length paired with long source bodies for low-confidence warnings.
_MAX_SHORT_GLOSS_LEN: Final[int] = 10


def _substantive_html_content(sense_body: str) -> bool:
    """
    Return ``True`` when *sense_body* still contains meaningful text after cleanup.

    Args:
        sense_body: Raw HTML sense block.

    Returns:
        ``True`` when enough non-tag content remains to expect a gloss.

    """
    plain = _TAG_RE.sub(" ", _BRACKET_BLOCK_RE.sub("", sense_body))
    plain = _WS_RE.sub(" ", plain).strip(" ,;.:-()")
    return len(plain) >= _MIN_SUBSTANTIVE_BODY_LEN


def _is_grammatical_abbrev(text: str) -> bool:
    """
    Return ``True`` when *text* is a grammatical abbreviation, not an English gloss.

    Args:
        text: Stripped italic span content.

    Returns:
        ``True`` when the span looks like a grammar marker rather than a definition.

    """
    return _GRAM_ABBREV_RE.match(text.strip().rstrip(";,.:")) is not None


def _is_editorial_marker(text: str) -> bool:
    """
    Return ``True`` when *text* is a BT supplement editorial directive.

    Editorial directives such as ``Add:``, ``Substitute``, ``Dele``, and ``Omit``
    appear as italic spans and carry no English gloss content.

    Args:
        text: Stripped italic span content.

    Returns:
        ``True`` when the span is a supplement editorial directive.

    """
    return text.strip().rstrip(";,.:").lower() in _EDITORIAL_MARKER_SET


def _contains_oe_chars(text: str) -> bool:
    """
    Return ``True`` when *text* contains Old English-specific Unicode characters.

    Args:
        text: Plain-text content to inspect.

    Returns:
        ``True`` when OE-specific codepoints are present.

    """
    return _OE_CHARS_RE.search(text) is not None


def _is_citation_span(text: str) -> bool:
    """
    Return ``True`` when an italic span looks like an OE citation, not an English gloss.

    The heuristic fires when the span is a grammatical abbreviation, a supplement
    editorial marker, or contains OE-specific Unicode characters together with a
    recognised source abbreviation.

    Args:
        text: Stripped italic span content.

    Returns:
        ``True`` when the span matches the OE/Latin citation heuristic.

    """
    stripped = text.strip()
    if not stripped:
        return True
    if _is_grammatical_abbrev(stripped):
        return True
    if _is_editorial_marker(stripped):
        return True
    if _contains_oe_chars(stripped) and _SOURCE_ABBR_RE.search(stripped):
        return True
    # Very short abbreviation with a period (e.g. "v. l.", "n. s.")
    return (
        len(stripped) <= _MAX_ABBREV_LEN
        and "." in stripped
        and re.fullmatch(r"[a-z\s\.]+", stripped, re.IGNORECASE) is not None
    )


def _strip_leading_gram_prefix(text: str) -> str:
    """
    Remove a leading grammatical marker from a combined gender-gloss italic span.

    Some BT spans combine a POS/gender abbreviation with the English definition:
    ``f. An oak`` -> ``An oak``.

    Args:
        text: Italic span content stripped of outer whitespace.

    Returns:
        Text with any leading grammatical abbreviation removed.

    """
    return _LEADING_GRAM_PREFIX_RE.sub("", text, count=1)


def _strip_editorial_directive(text: str) -> str:
    """
    Remove a leading editorial directive from an italic span that contains a gloss.

    Some BT spans begin with an editorial verb followed by the replacement gloss:
    ``Substitute: A property`` -> ``A property``.

    Args:
        text: Italic span content stripped of outer whitespace.

    Returns:
        Text with any leading editorial directive prefix removed.

    """
    return _EDITORIAL_DIRECTIVE_RE.sub("", text, count=1)


class BTAttestationStripper:
    """
    Remove Old English attestation tails from a Bosworth-Toller sense block.

    Implements the Phase 03 attestation-stripping rules:

    1. Etymology bracket blocks ``[...]`` are removed before processing.
    2. Everything after the first ``:--`` separator is discarded.
    3. Italic spans matching the OE/Latin citation heuristic or editorial markers
       are removed.
    4. Editorial directive prefixes (``Substitute:``, ``Add:``) are stripped from
       combined directive-gloss italic spans.
    5. Leading grammatical markers (``f.``, ``m.``, ``adj.``, ...) are stripped
       from combined gender-gloss italic spans.
    6. All remaining HTML tags are stripped.
    7. Whitespace is normalised.

    If italic spans were present but all filtered out, the method returns an empty
    string rather than falling back to potentially noisy plain text.  The plain-text
    fallback is reserved for entries with no italic spans at all (some older BT
    main-dictionary sub-senses).

    The result is an English-only gloss string suitable for storage in
    :attr:`~wyrdcraeft.models.dictionary.BTSense.gloss_en`.

    """

    def strip(self, sense_body: str) -> str:
        """
        Return an English-only gloss from one sense-block body string.

        Args:
            sense_body: Raw HTML body for one sense (after sense-label split).

        Returns:
            English gloss text with attestations removed and tags stripped.

        """
        body = _BRACKET_BLOCK_RE.sub("", sense_body)
        pre_attest = self._cut_at_separator(body)
        return self._extract_gloss(pre_attest)

    def is_low_confidence(self, sense_body: str, gloss: str) -> bool:
        """
        Return ``True`` when attestation stripping likely left noisy or
        incomplete glosses.

        Heuristics include residual attestation separators, very short glosses relative
        to the source body, and empty glosses when the body still contains substantive
        HTML content after bracket removal.

        Args:
            sense_body: Raw HTML sense block passed to :meth:`strip`.
            gloss: Gloss returned by :meth:`strip`.

        Returns:
            ``True`` when the strip result should be flagged for optional LLM repair.

        """
        if not gloss.strip():
            return _substantive_html_content(sense_body)
        if len(gloss.strip()) < _MIN_GLOSS_LEN:
            return True
        if _ATTEST_SEP_RE.search(gloss):
            return True
        plain_body = _TAG_RE.sub(" ", _BRACKET_BLOCK_RE.sub("", sense_body))
        plain_body = _WS_RE.sub(" ", plain_body).strip()
        return (
            len(plain_body) >= _MIN_BODY_LEN_FOR_SHORT_GLOSS
            and len(gloss.strip()) < _MAX_SHORT_GLOSS_LEN
        )

    def _cut_at_separator(self, text: str) -> str:
        r"""
        Truncate *text* at the first attestation separator.

        The primary separator is ``:--``; a secondary pattern ``</I>\s*--``
        handles entries where the definition italic span ends with a colon and the
        ``--`` follows immediately after the closing tag
        (e.g. ``<I>An oak:</I> -- Aac-tun``).

        Args:
            text: Raw sense body HTML with bracket blocks already removed.

        Returns:
            Text up to (but not including) the attestation separator.

        """
        primary = _ATTEST_SEP_RE.search(text)
        secondary = re.search(r"</[Ii]>\s*--", text)

        candidates = [m.start() for m in (primary, secondary) if m is not None]
        if not candidates:
            return text
        cut = min(candidates)
        if primary is not None and primary.start() == cut:
            return text[: cut + 1]
        if secondary is None:
            return text  # pragma: no cover
        return text[: secondary.start() + len("</I>")]

    def _extract_gloss(self, pre_attest: str) -> str:
        """
        Extract English gloss text from the pre-attestation portion of a sense body.

        Italic spans matching the citation or grammatical-abbreviation heuristic, or
        supplement editorial markers, are discarded.  Leading editorial directives
        (``Substitute:``) and grammatical prefixes (``f.``, ``m.``) are stripped from
        kept spans.

        When italic spans were present but all filtered out, an empty string is returned
        immediately to avoid noisy plain-text fallback output.  The plain-text fallback
        is used only when the sense body contains no italic spans at all.

        Args:
            pre_attest: Sense body with the attestation tail and bracket blocks removed.

        Returns:
            Cleaned English gloss string.

        """
        italic_spans = _ITALIC_SPAN_RE.findall(pre_attest)
        had_italic_spans = len(italic_spans) > 0
        candidates: list[str] = []
        for span in italic_spans:
            plain = _TAG_RE.sub("", span).strip()
            if not plain:
                continue
            if _is_citation_span(plain):
                continue
            plain = _strip_editorial_directive(plain)
            plain = _strip_leading_gram_prefix(plain)
            plain = plain.rstrip(";,.:").strip()
            if plain:
                candidates.append(plain)

        if candidates:
            return _WS_RE.sub(" ", "; ".join(candidates)).strip()

        if had_italic_spans:
            # All italic spans were editorial/grammatical markers; no gloss present.
            return ""

        # No italic spans at all -- attempt plain-text extraction (older BT format).
        plain_text = _TAG_RE.sub(" ", pre_attest)
        return self._clean_plain_fallback(plain_text)

    def _clean_plain_fallback(self, plain_text: str) -> str:
        """
        Clean plain-text fallback by removing source abbreviations and OE tokens.

        Used when the sense body contains no italic spans at all.  Returns an empty
        string when fewer than two words survive the cleaning pass, to prevent bare
        headword tokens from appearing as glosses.

        Args:
            plain_text: Tag-stripped sense body text.

        Returns:
            Best-effort English gloss extracted from plain text, or empty string.

        """
        text = _SOURCE_ABBR_RE.sub("", plain_text)
        text = re.sub(r"\S*[āēīōūǣæÆÐðÞþĀĒĪŌŪǢ]\S*", "", text)
        text = re.sub(
            r"\b\w+(?:are|ure|ere|ire|um|us|ae|is|em)\b",
            "",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(r"\b\d+(?:[,\s]*\d+)*\b", "", text)
        # Require at least two words so bare headword tokens are not glosses.
        text = _WS_RE.sub(" ", text).strip(" ,;.:-()")
        if " " not in text:
            return ""
        return text
