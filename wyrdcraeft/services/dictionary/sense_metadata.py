"""Sense-level prefix metadata classification for Bosworth-Toller sense bodies."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from wyrdcraeft.models.dictionary import BTGender, BTSense

#: Leading headword bold tag in an unlabeled body field.
_HEADWORD_RE: Final[re.Pattern[str]] = re.compile(r"<B>[^<]*</B>")

#: Italic span extractor — non-greedy, single-line.
_ITALIC_SPAN_RE: Final[re.Pattern[str]] = re.compile(r"<[Ii]>(.*?)</[Ii]>")

#: Strips any remaining HTML tags.
_TAG_RE: Final[re.Pattern[str]] = re.compile(r"<[^>]+>")

#: Collapses whitespace.
_WS_RE: Final[re.Pattern[str]] = re.compile(r"\s+")

#: Inflection endings dropped unless proven otherwise.
_INFLECTION_ENDING_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?:e|es|an)$",
    re.IGNORECASE,
)

#: Gender abbreviation at start of a token segment.
_GENDER_TOKEN_RE: Final[re.Pattern[str]] = re.compile(
    r"^([mfn])\.:?\s*(.*)$",
    re.IGNORECASE,
)

#: Case abbreviation tokens.
_CASE_TOKEN_RE: Final[re.Pattern[str]] = re.compile(
    r"^(nom\.?|acc\.?|gen\.?|g\.?|dat\.?|voc\.?|instr\.?|inst\.?)$",
    re.IGNORECASE,
)

#: Modifier abbreviation tokens normalized to controlled vocabulary.
_MODIFIER_TOKEN_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?:intrans\.?|trans\.?|wk\.?|weak|part\.?|indecl\.?|indeclinable|interrog\.?)$",
    re.IGNORECASE,
)

#: POS debris stripped from prefix zones but not stored as modifiers.
_POS_DEBRIS_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?:v\.?\s*(?:trans|intrans|a|n|refl|def)?\.?|p\.?|pp\.?|pl\.?|sg\.?|adj\.?|adv\.?|"
    r"prep\.?|conj\.?|interj\.?|pron\.?|num\.?)$",
    re.IGNORECASE,
)

#: Trailing modifier after a comma at the end of a gloss clause.
_TRAILING_MODIFIER_RE: Final[re.Pattern[str]] = re.compile(
    r"^(.*?),\s*(intrans\.?|trans\.?|wk\.?|weak|part\.?|indecl\.?|indeclinable)\.?\s*;?\s*$",
    re.IGNORECASE,
)

#: Maps normalized modifier tokens to controlled vocabulary.
_MODIFIER_NORMALIZE: Final[dict[str, str]] = {
    "intrans": "intransitive",
    "intrans.": "intransitive",
    "trans": "transitive",
    "trans.": "transitive",
    "wk": "weak",
    "wk.": "weak",
    "weak": "weak",
    "part": "participle",
    "part.": "participle",
    "indecl": "indeclinable",
    "indecl.": "indeclinable",
    "indeclinable": "indeclinable",
    "interrog": "interrogative",
    "interrog.": "interrogative",
}

#: Maps case abbreviations to normalized labels.
_CASE_NORMALIZE: Final[dict[str, str]] = {
    "nom": "nominative",
    "nom.": "nominative",
    "acc": "accusative",
    "acc.": "accusative",
    "gen": "genitive",
    "gen.": "genitive",
    "g": "genitive",
    "g.": "genitive",
    "dat": "dative",
    "dat.": "dative",
    "voc": "vocative",
    "voc.": "vocative",
    "instr": "instrumental",
    "instr.": "instrumental",
    "inst": "instrumental",
    "inst.": "instrumental",
}

#: Minimum plain-text length for substantive gloss detection after prefix peel.
_MIN_SUBSTANTIVE_GLOSS_LEN: Final[int] = 2

#: Maps grammatical-context gender labels to entry-level genders.
_GRAM_GENDER_TO_BT: Final[dict[str, BTGender]] = {
    "masculine": BTGender.M,
    "feminine": BTGender.F,
    "neuter": BTGender.N,
}


def _normalize_modifier(token: str) -> str | None:
    """
    Normalize one modifier abbreviation token.

    Args:
        token: Raw modifier token text.

    Returns:
        Controlled-vocabulary modifier label, or ``None`` when unrecognized.

    """
    key = token.strip().rstrip(".,:;").lower()
    if key in _MODIFIER_NORMALIZE:
        return _MODIFIER_NORMALIZE[key]
    if _MODIFIER_TOKEN_RE.match(token.strip()):
        return _MODIFIER_NORMALIZE.get(key, key)
    return None


def _normalize_case(token: str) -> str | None:
    """
    Normalize one case abbreviation token.

    Args:
        token: Raw case token text.

    Returns:
        Normalized case label, or ``None`` when unrecognized.

    """
    key = token.strip().rstrip(".,:;").lower()
    return _CASE_NORMALIZE.get(key)


def _normalize_gender(letter: str) -> str:
    """
    Map a gender letter to a grammatical-context label.

    Args:
        letter: Single gender letter ``m``, ``f``, or ``n``.

    Returns:
        Normalized gender label.

    """
    mapping = {"m": "masculine", "f": "feminine", "n": "neuter"}
    return mapping[letter.lower()]


@dataclass(frozen=True)
class SenseMetadata:
    """
    Prefix metadata extracted from one sense-body fragment.

    Attributes:
        modifiers: Controlled-vocabulary sense modifiers.
        grammatical_context: Normalized gender/case context tags.
        usage_note: Free-text usage note when present.
        prefix_fragment_raw: Raw prefix substring removed from the body.
        remainder: Sense body with prefix material removed for gloss extraction.
        warnings: Classification warnings (for example bare modifier-only bodies).

    """

    #: Controlled-vocabulary sense modifiers.
    modifiers: tuple[str, ...]
    #: Normalized gender/case context tags.
    grammatical_context: tuple[str, ...]
    #: Free-text usage note when present.
    usage_note: str
    #: Raw prefix substring removed from the body.
    prefix_fragment_raw: str
    #: Sense body with prefix material removed.
    remainder: str
    #: Classification warnings.
    warnings: tuple[str, ...] = ()


class SenseMetadataClassifier:
    """
    Classify sense-level prefix debris into structured metadata.

    Extracts modifiers, grammatical context, and usage notes from the local
    prefix zone of one sense fragment. Prefix tokens are never borrowed from
    neighboring fragments.
    """

    def classify(self, text: str) -> SenseMetadata:  # noqa: PLR0915
        """
        Classify prefix metadata for one sense-body fragment.

        Args:
            text: Raw HTML sense body after sense-label removal.

        Returns:
            Structured prefix metadata plus a cleaned body remainder.

        """
        modifiers: list[str] = []
        grammatical: list[str] = []
        warnings: list[str] = []
        prefix_raw_parts: list[str] = []
        remainder = _HEADWORD_RE.sub("", text, count=1).lstrip()
        remainder = self._strip_leading_variants(remainder)
        remainder, marker_prefix = self._strip_leading_inflection_markers(remainder)
        if marker_prefix:
            prefix_raw_parts.append(marker_prefix)

        usage_note, usage_prefix = self._extract_usage_note_at_start(remainder)
        if usage_prefix:
            prefix_raw_parts.append(usage_prefix)
            remainder = remainder[len(usage_prefix) :].lstrip()

        while True:
            remainder = self._strip_leading_paradigm_fragments(remainder)
            remainder = remainder.lstrip(" ,;")
            span_match = _ITALIC_SPAN_RE.search(remainder)
            if span_match is None or span_match.start() > 0:
                break
            inner = span_match.group(1)
            parsed = self._parse_italic_prefix(inner)
            if parsed is None:
                break
            mods, grams, _prefix_text, gloss_tail, consumed_all = parsed
            modifiers.extend(mods)
            grammatical.extend(grams)
            prefix_raw_parts.append(span_match.group(0))
            if consumed_all:
                remainder = remainder[span_match.end() :].lstrip()
                continue
            replacement = f"<I>{gloss_tail}</I>" if gloss_tail else ""
            start = span_match.start()
            end = span_match.end()
            remainder = remainder[:start] + replacement + remainder[end:]
            break

        if not usage_note:
            usage_note, usage_prefix = self._extract_usage_note(remainder)
            if usage_prefix:
                prefix_raw_parts.append(usage_prefix)
                remainder = remainder.replace(usage_prefix, "", 1).lstrip()
        remainder = self._strip_phrase_example_tail(remainder, usage_note)

        remainder = self._strip_leading_paradigm_fragments(remainder)

        trailing = self._parse_trailing_modifier(remainder)
        if trailing is not None:
            mod, cleaned = trailing
            modifiers.append(mod)
            prefix_raw_parts.append(f", {mod}")
            remainder = cleaned

        if not _has_substantive_gloss(remainder) and (modifiers or grammatical):
            warnings.append("prefix_only_no_gloss")

        return SenseMetadata(
            modifiers=tuple(dict.fromkeys(modifiers)),
            grammatical_context=tuple(dict.fromkeys(grammatical)),
            usage_note=usage_note,
            prefix_fragment_raw="".join(prefix_raw_parts).strip(),
            remainder=remainder.strip(),
            warnings=tuple(warnings),
        )

    def _parse_italic_prefix(  # noqa: PLR0911, PLR0912, PLR0915
        self,
        inner: str,
    ) -> tuple[list[str], list[str], str, str, bool] | None:
        """
        Parse one italic span for leading prefix tokens.

        Args:
            inner: Inner text of one ``<I>…</I>`` span.

        Returns:
            Tuple of modifiers, grammatical tags, consumed prefix text, gloss
            tail, and whether the entire span was prefix-only; ``None`` when
            the span does not begin with classifiable prefix debris.

        """
        plain = _TAG_RE.sub("", inner).strip()
        if not plain:
            return None

        segments = [segment.strip() for segment in plain.split(";") if segment.strip()]
        if not segments:
            return None

        modifiers: list[str] = []
        grammatical: list[str] = []
        consumed_segments: list[str] = []
        idx = 0

        while idx < len(segments):
            segment = segments[idx]
            if _INFLECTION_ENDING_RE.match(segment):
                consumed_segments.append(segment)
                idx += 1
                continue

            gender_match = _GENDER_TOKEN_RE.match(segment)
            if gender_match and gender_match.group(2):
                grammatical.append(_normalize_gender(gender_match.group(1)))
                consumed_segments.append(gender_match.group(1) + ".")
                gloss_tail = gender_match.group(2).strip().lstrip(", ")
                if gloss_tail:
                    prefix_text = "; ".join(consumed_segments)
                    return modifiers, grammatical, prefix_text, gloss_tail, False
                idx += 1
                continue

            if gender_match and not gender_match.group(2).strip():
                grammatical.append(_normalize_gender(gender_match.group(1)))
                consumed_segments.append(segment)
                idx += 1
                continue

            case_parts = re.split(r"\s+", segment.replace(",", " "))
            if case_parts and all(_normalize_case(part) for part in case_parts if part):
                for part in case_parts:
                    if part:
                        normalized = _normalize_case(part)
                        if normalized:
                            grammatical.append(normalized)
                consumed_segments.append(segment)
                idx += 1
                continue

            if _POS_DEBRIS_RE.match(segment):
                consumed_segments.append(segment)
                idx += 1
                continue

            modifier = _normalize_modifier(segment)
            if modifier:
                modifiers.append(modifier)
                consumed_segments.append(segment)
                idx += 1
                if idx < len(segments):
                    gloss_tail = "; ".join(segments[idx:]).strip()
                    gloss_tail = self._peel_leading_prefix_from_text(
                        gloss_tail,
                        grammatical,
                    )
                    prefix_text = "; ".join(consumed_segments)
                    return modifiers, grammatical, prefix_text, gloss_tail, False
                continue

            if idx == 0 and _looks_like_gloss_start(segment):
                return None

            break

        if not consumed_segments:
            tokenized = self._parse_token_prefix(plain)
            if tokenized is None:
                return None
            return tokenized

        prefix_text = "; ".join(consumed_segments)
        return modifiers, grammatical, prefix_text, "", True

    def _parse_token_prefix(  # noqa: PLR0911
        self,
        plain: str,
    ) -> tuple[list[str], list[str], str, str, bool] | None:
        """
        Parse space-delimited prefix tokens from one italic span.

        Args:
            plain: Tag-stripped italic span content.

        Returns:
            Parsed prefix tuple, or ``None`` when no prefix tokens are found.

        """
        tokens = plain.split()
        if not tokens:
            return None

        modifiers: list[str] = []
        grammatical: list[str] = []
        consumed: list[str] = []
        idx = 0

        while idx < len(tokens):
            token = tokens[idx].rstrip(";,")
            next_join = " ".join(tokens[idx:])

            gender_match = _GENDER_TOKEN_RE.match(next_join)
            if gender_match and gender_match.group(2).strip():
                grammatical.append(_normalize_gender(gender_match.group(1)))
                consumed.append(tokens[idx])
                gloss_tail = gender_match.group(2).strip().lstrip(", ")
                return modifiers, grammatical, " ".join(consumed), gloss_tail, False

            if _INFLECTION_ENDING_RE.match(token):
                consumed.append(tokens[idx])
                idx += 1
                continue

            normalized_case = _normalize_case(token)
            if normalized_case:
                grammatical.append(normalized_case)
                consumed.append(tokens[idx])
                idx += 1
                continue

            if _POS_DEBRIS_RE.match(token):
                consumed.append(tokens[idx])
                idx += 1
                continue

            modifier = _normalize_modifier(token)
            if modifier:
                modifiers.append(modifier)
                consumed.append(tokens[idx])
                idx += 1
                if idx < len(tokens):
                    gloss_tail = " ".join(tokens[idx:]).strip().rstrip(";,")
                    return modifiers, grammatical, " ".join(consumed), gloss_tail, False
                continue

            if not consumed:
                return None
            gloss_tail = " ".join(tokens[idx:]).strip().rstrip(";,")
            if gloss_tail:
                return modifiers, grammatical, " ".join(consumed), gloss_tail, False
            break

        if not consumed:
            return None
        return modifiers, grammatical, " ".join(consumed), "", True

    def _strip_leading_variants(self, text: str) -> str:
        """
        Remove leading hyphenated variant spellings before sense prefix spans.

        Args:
            text: HTML sense body with the headword already removed.

        Returns:
            Body with leading variant lists stripped.

        """
        cleaned = text.lstrip()
        variant_re = re.compile(
            r"^(?:(?:-[\wæþðūǣȳ\-]+,\s*)+-[\wæþðūǣȳ\-]+;\s*"
            r"|(?:-[\wæþðūǣȳ\-]+,\s*)+)",
            re.IGNORECASE,
        )
        while True:
            match = variant_re.match(cleaned)
            if match is None:
                break
            cleaned = cleaned[match.end() :].lstrip()
        return cleaned

    def _strip_leading_inflection_markers(self, text: str) -> tuple[str, str]:
        """
        Remove leading paradigm inflection markers such as ``an;`` or ``es;``.

        Args:
            text: HTML sense body after headword and variants were removed.

        Returns:
            Tuple of cleaned body and stripped marker prefix text.

        """
        cleaned = text.lstrip()
        stripped_parts: list[str] = []
        marker_re = re.compile(r"^(?:e|es|an|as|um|a);\s*", re.IGNORECASE)
        while True:
            match = marker_re.match(cleaned)
            if match is None:
                break
            stripped_parts.append(match.group(0))
            cleaned = cleaned[match.end() :].lstrip()
        return cleaned, "".join(stripped_parts)

    def _strip_leading_paradigm_fragments(self, text: str) -> str:
        """
        Remove leading weak-noun paradigm fragments such as ``-færes;``.

        Args:
            text: HTML sense body after prefix italic spans were stripped.

        Returns:
            Body with leading paradigm fragments removed.

        """
        cleaned = text.lstrip()
        patterns = (
            re.compile(r"^-\w[\wæþðūǣȳ\-]*;\s*", re.IGNORECASE),
            re.compile(r"^(?:-[\wæþðūǣȳ\-]+,\s*)+-[\wæþðūǣȳ\-]+;\s*", re.IGNORECASE),
            re.compile(r"^-[\wæþðūǣȳ\-]+,\s*", re.IGNORECASE),
        )
        while True:
            matched = False
            for pattern in patterns:
                match = pattern.match(cleaned)
                if match is None:
                    continue
                cleaned = cleaned[match.end() :].lstrip()
                matched = True
                break
            if not matched:
                break
        return cleaned

    def _strip_phrase_example_tail(self, text: str, usage_note: str) -> str:
        """
        Remove phrase-example tails that follow an ``in the phrase`` usage note.

        Args:
            text: HTML sense body after the usage note was removed.
            usage_note: Normalized usage note attached to the sense.

        Returns:
            Body with phrase-example material removed when applicable.

        """
        if usage_note != "in the phrase":
            return text
        return re.sub(
            r"<I>[^<]+</I>\s*=.*?(?=:\s*--|$)",
            "",
            text,
            count=1,
            flags=re.IGNORECASE,
        ).strip()

    def _extract_usage_note_at_start(self, text: str) -> tuple[str, str]:
        """
        Extract a usage-note phrase only when it leads the sense body.

        Args:
            text: HTML sense body fragment.

        Returns:
            Tuple of normalized usage note and raw matched prefix substring.

        """
        patterns: tuple[tuple[str, str], ...] = (
            (
                r"^(?:\(\d+\)\s*)?with\s+dat\.\s+of\s+person(?:\s+[^:<;]+)?\s*[,:\s]*",
                "with dative of person",
            ),
            (r"^(?:only\s+)?in\s+the\s+phrase\s*[,:\s]*", "in the phrase"),
            (
                r"^as\s+(?:an\s+)?ecclesiastical\s+term\s*[,:\s]*",
                "as ecclesiastical term",
            ),
        )
        for pattern, note in patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match is not None:
                return note, match.group(0)
        return "", ""

    def _extract_usage_note(self, text: str) -> tuple[str, str]:
        """
        Extract a usage-note phrase from plain text in *text*.

        Args:
            text: HTML sense body fragment.

        Returns:
            Tuple of normalized usage note and raw matched prefix substring.

        """
        patterns: tuple[tuple[str, str], ...] = (
            (
                r"(?:\(\d+\)\s*)?with\s+dat\.\s+of\s+person(?:\s+[^:<;]+)?\s*[,:\s]*",
                "with dative of person",
            ),
            (r"(?:only\s+)?in\s+the\s+phrase\s*[,:\s]*", "in the phrase"),
            (
                r"as\s+(?:an\s+)?ecclesiastical\s+term\s*[,:\s]*",
                "as ecclesiastical term",
            ),
        )
        for pattern, note in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match is not None:
                return note, match.group(0)
        return "", ""

    def _peel_leading_prefix_from_text(
        self,
        text: str,
        grammatical: list[str],
    ) -> str:
        """
        Remove leading gender or case tokens from a gloss-tail substring.

        Args:
            text: Remaining italic inner text after prefix segments.
            grammatical: Grammatical-context list to append into.

        Returns:
            Gloss tail with any leading prefix tokens removed.

        """
        remaining = text.strip()
        while remaining:
            gender_match = _GENDER_TOKEN_RE.match(remaining)
            if gender_match and gender_match.group(2).strip():
                grammatical.append(_normalize_gender(gender_match.group(1)))
                return gender_match.group(2).strip().lstrip(", ")
            case_token = remaining.split(maxsplit=1)[0].rstrip(".,;")
            normalized_case = _normalize_case(case_token)
            if normalized_case:
                grammatical.append(normalized_case)
                remaining = remaining[len(case_token) :].lstrip(" ,;")
                continue
            break
        return remaining

    def _parse_trailing_modifier(self, text: str) -> tuple[str, str] | None:
        """
        Detect a trailing modifier after the gloss clause in one italic span.

        Args:
            text: HTML sense body possibly containing one trailing modifier.

        Returns:
            Normalized modifier and cleaned body, or ``None``.

        """
        for span_match in _ITALIC_SPAN_RE.finditer(text):
            inner = _TAG_RE.sub("", span_match.group(1)).strip()
            trailing = _TRAILING_MODIFIER_RE.match(inner)
            if trailing is None:
                continue
            modifier = _normalize_modifier(trailing.group(2))
            if modifier is None:
                continue
            cleaned_inner = trailing.group(1).strip()
            cleaned = (
                text[: span_match.start()]
                + f"<I>{cleaned_inner}</I>"
                + text[span_match.end() :]
            )
            return modifier, cleaned
        return None


def _looks_like_gloss_start(segment: str) -> bool:
    """
    Return ``True`` when *segment* begins substantive English gloss text.

    Args:
        segment: One semicolon-delimited span segment.

    Returns:
        ``True`` when the segment looks like an English definition start.

    """
    if not segment:
        return False
    if segment[0].isupper():
        return True
    lowered = segment.lower()
    return lowered.startswith(("to ", "a ", "an ", "the "))


def _has_substantive_gloss(text: str) -> bool:
    """
    Return ``True`` when *text* still contains extractable gloss content.

    Args:
        text: HTML sense body after prefix removal.

    Returns:
        ``True`` when attestation stripping could yield a gloss.

    """
    plain = _TAG_RE.sub(" ", text)
    plain = _WS_RE.sub(" ", plain).strip(" ,;:()-")
    if len(plain) < _MIN_SUBSTANTIVE_GLOSS_LEN:
        return False
    if _looks_like_gloss_start(plain):
        return True
    return bool(re.search(r"[A-Za-z]{3,}", plain))


def promote_entry_gender_from_senses(
    entry_genders: tuple[BTGender, ...],
    senses: tuple[BTSense, ...],
) -> tuple[BTGender, ...]:
    """
    Promote a single sense-level gender context to entry-level genders.

    When the entry has no entry-level genders, exactly one sense, and that
    sense carries exactly one gender grammatical-context tag, copy it to the
    entry-level gender list.

    Args:
        entry_genders: Genders already parsed from the headword prefix.
        senses: Ordered senses for one consolidated entry.

    Returns:
        Entry-level genders, promoted from the sole sense when applicable.

    """
    if entry_genders:
        return entry_genders
    if len(senses) != 1:
        return entry_genders
    gender_tags = [
        tag
        for tag in senses[0].grammatical_context
        if tag in _GRAM_GENDER_TO_BT
    ]
    if len(gender_tags) != 1:
        return entry_genders
    promoted = _GRAM_GENDER_TO_BT[gender_tags[0]]
    return (promoted,)
