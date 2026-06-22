"""POS and gender extraction from Bosworth-Toller headword prefixes."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from ...models.dictionary import BTGender, BTPos

#: Matches each ``<I>…</I>`` span in a headword prefix fragment.
_ITALIC_TAG_RE: Final[re.Pattern[str]] = re.compile(r"<I>([^<]*)</I>", re.IGNORECASE)
#: Strong verb/noun paradigm marker: ``ic -bace`` style.
_VERB_PARADIGM_RE: Final[re.Pattern[str]] = re.compile(
    r"\bic\s+-[\wæþðūǣȳáéíóúýǽ]+",
    re.IGNORECASE,
)
#: Weak noun genitive ending before POS/gender markers.
_GENITIVE_NOUN_RE: Final[re.Pattern[str]] = re.compile(
    r"(?:^|[,;\s])(?:es|as|an|a|e|um)\s*;",
    re.IGNORECASE,
)
#: Gender letters with BT period or colon marker (``m.``, ``f:``, etc.).
_GENDER_LETTER_RE: Final[re.Pattern[str]] = re.compile(r"\b([mfn])[\.:]", re.IGNORECASE)
#: BT verb inflection tags such as ``<I>p.</I>`` or ``<I>. p.</I>``.
_VERB_INFLECTION_P_RE: Final[re.Pattern[str]] = re.compile(
    r"<I>\s*\.?\s*p\.\s*</I>",
    re.IGNORECASE,
)
#: BT past-participle inflection tag ``<I>pp.</I>``.
_VERB_INFLECTION_PP_RE: Final[re.Pattern[str]] = re.compile(
    r"<I>\s*pp\.\s*</I>",
    re.IGNORECASE,
)
#: BT plural inflection tag ``<I>pl.</I>``.
_VERB_INFLECTION_PL_RE: Final[re.Pattern[str]] = re.compile(
    r"<I>\s*pl\.\s*</I>",
    re.IGNORECASE,
)
#: POS keyword patterns applied to lowercased italic content (first match wins).
_POS_FROM_ITALIC: Final[tuple[tuple[re.Pattern[str], BTPos], ...]] = (
    (re.compile(r"\bindecl\b"), BTPos.INDECL),
    (re.compile(r"\binterj\b"), BTPos.INTERJ),
    (re.compile(r"\bprep\b"), BTPos.PREP),
    (re.compile(r"\bconj\b"), BTPos.CONJ),
    (re.compile(r"\badv\b"), BTPos.ADV),
    (re.compile(r"\badj\b"), BTPos.ADJ),
    (re.compile(r"\bpron\b"), BTPos.PRON),
    (re.compile(r"\bnum\b"), BTPos.NUMERAL),
)


def _italic_spans(fragment: str) -> list[str]:
    """
    Collect inner text from ``<I>…</I>`` tags, including unclosed tail spans.

    BT prefix fragments are sometimes truncated before the closing ``</I>``;
    treat any trailing ``<I>…`` without a close tag as one span.

    Args:
        fragment: Headword prefix HTML fragment.

    Returns:
        Ordered italic inner-text spans.

    """
    spans = [match.group(1).strip() for match in _ITALIC_TAG_RE.finditer(fragment)]
    open_tail = re.search(r"<I>([^<]*)$", fragment, re.IGNORECASE)
    if open_tail is None:
        return spans
    tail = open_tail.group(1).strip()
    if not tail:
        return spans
    if spans and spans[-1] == tail:
        return spans
    spans.append(tail)
    return spans


@dataclass(frozen=True)
class PosGenderResult:
    """
    POS and gender values extracted from a BT headword prefix fragment.

    Attributes:
        pos: Normalized part of speech, or ``unknown`` when unparseable.
        genders: Noun gender markers in source order; empty when N/A.

    """

    #: Normalized part of speech.
    pos: BTPos
    #: Extracted noun genders; empty when not applicable.
    genders: tuple[BTGender, ...]


class BTPosGenderExtractor:
    """
    Deterministic POS/gender extractor for HTML after the first ``</B>`` tag.

    Reads the prefix fragment before ``:--`` or sense ``I.`` markers and
    returns normalized ``BTPos`` plus any ``BTGender`` values found in BT
    italic markup.
    """

    def extract(self, pos_fragment: str) -> PosGenderResult:
        """
        Extract POS and genders from a BT headword prefix HTML fragment.

        Args:
            pos_fragment: Text immediately after ``</B>`` (before gloss body).

        Returns:
            Normalized POS and gender list; ``pos`` is ``unknown`` when
            no reliable signal is found (never raises).

        """
        fragment = pos_fragment.strip()
        if not fragment:
            return PosGenderResult(pos=BTPos.UNKNOWN, genders=())

        if self._is_verb_paradigm(fragment):
            return PosGenderResult(pos=BTPos.VERB, genders=())

        italic_spans = _italic_spans(fragment)
        genders = self._collect_genders(italic_spans)
        pos = self._pos_from_italic(italic_spans)

        if pos is None and genders:
            pos = BTPos.NOUN
        if pos is None and _GENITIVE_NOUN_RE.search(fragment):
            pos = BTPos.NOUN
        if pos is None:
            pos = BTPos.UNKNOWN

        return PosGenderResult(pos=pos, genders=genders)

    def _is_verb_paradigm(self, fragment: str) -> bool:
        """
        Detect BT verb paradigm markup in a prefix fragment.

        Args:
            fragment: Headword prefix HTML fragment.

        Returns:
            ``True`` when the fragment carries verb inflection signals.

        """
        if _VERB_PARADIGM_RE.search(fragment):
            return True
        has_p = _VERB_INFLECTION_P_RE.search(fragment) is not None
        has_pp = _VERB_INFLECTION_PP_RE.search(fragment) is not None
        has_pl = _VERB_INFLECTION_PL_RE.search(fragment) is not None
        if has_p and has_pp:
            return True
        return has_pl and (has_p or has_pp)

    def _collect_genders(self, italic_spans: list[str]) -> tuple[BTGender, ...]:
        """
        Collect unique gender markers from italic spans in source order.

        Args:
            italic_spans: Inner text of each ``<I>…</I>`` tag.

        Returns:
            De-duplicated gender tuple preserving first-seen order.

        """
        seen: set[BTGender] = set()
        ordered: list[BTGender] = []
        for span in italic_spans:
            for match in _GENDER_LETTER_RE.finditer(span.lower()):
                gender = BTGender(match.group(1).lower())
                if gender not in seen:
                    seen.add(gender)
                    ordered.append(gender)
        return tuple(ordered)

    def _pos_from_italic(self, italic_spans: list[str]) -> BTPos | None:
        """
        Resolve POS from italic span text using BT keyword conventions.

        Args:
            italic_spans: Inner text of each ``<I>…</I>`` tag.

        Returns:
            Matched ``BTPos``, or ``None`` when no POS keyword is found.

        """
        for span in italic_spans:
            lowered = span.lower()
            for pattern, pos in _POS_FROM_ITALIC:
                if pattern.search(lowered):
                    return pos
        return None
