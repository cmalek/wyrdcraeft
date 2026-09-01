"""Bosworth-Toller dictionary index models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class BTPos(StrEnum):
    """
    Normalized part-of-speech label for Bosworth-Toller entries.

    Used as half of the homograph merge key ``(norm_key, pos)``.
    """

    #: Masculine/feminine/neuter noun entries.
    NOUN = "noun"
    #: Strong/weak verb entries.
    VERB = "verb"
    #: Adjective entries.
    ADJ = "adj"
    #: Adverb entries.
    ADV = "adv"
    #: Preposition entries.
    PREP = "prep"
    #: Conjunction entries.
    CONJ = "conj"
    #: Interjection entries.
    INTERJ = "interj"
    #: Pronoun entries.
    PRON = "pron"
    #: Numeral entries.
    NUMERAL = "numeral"
    #: Indeclinable entries.
    INDECL = "indecl"
    #: POS could not be determined from the prefix fragment.
    UNKNOWN = "unknown"


class BTGender(StrEnum):
    """
    Noun gender marker extracted from BT headword prefixes.
    """

    #: Masculine gender.
    M = "m"
    #: Feminine gender.
    F = "f"
    #: Neuter gender.
    N = "n"


class BTLineKind(StrEnum):
    """
    Classification of one raw ``oe_bt.txt`` line before editorial merge.
    """

    #: Primary headword definition line.
    MAIN = "main"
    #: Editorial ``Add:`` supplement line.
    ADD = "add"
    #: Editorial ``Substitute:`` replacement line.
    SUBSTITUTE = "substitute"
    #: Editorial ``Dele`` removal line.
    DELE = "dele"
    #: Editorial delete-and-replace line.
    DELE_AND_ADD = "dele_and_add"
    #: ``v.`` / ``vide`` cross-reference line.
    CROSS_REF = "cross_ref"
    #: Line kind could not be classified.
    UNKNOWN = "unknown"


class BTEditorialOp(StrEnum):
    """
    Editorial operation applied when consolidating BT lines into one entry.
    """

    #: Append supplemental material to an entry.
    ADD = "add"
    #: Replace existing entry material.
    SUBSTITUTE = "substitute"
    #: Remove existing entry material.
    DELE = "dele"
    #: Remove then replace entry material in one editorial action.
    DELE_AND_ADD = "dele_and_add"


def format_sense_display_label(sense_path: str) -> str:
    """
    Convert canonical ``sense_path`` to Arabic display text.

    Top-level paths stay as Arabic numerals. Nested numeric segments become
    lowercase letters (``2.1`` → ``2a``, ``4.3`` → ``4c``).

    Args:
        sense_path: Canonical hierarchical path such as ``2.1``.

    Returns:
        Human-facing sense label without a trailing period.

    """
    if not sense_path:
        return ""
    parts = sense_path.split(".")
    if not parts:
        return ""
    display = parts[0]
    max_letter_index = ord("z") - ord("a") + 1
    for segment in parts[1:]:
        if segment.isdigit():
            index = int(segment)
            if 1 <= index <= max_letter_index:
                display += chr(ord("a") + index - 1)
            else:
                display += segment
        else:
            display += segment
    return display


def sense_path_sort_key(sense_path: str) -> tuple[int, ...]:
    """
    Build a sort key that orders senses by hierarchical path.

    ``4`` sorts before ``4.1`` (displayed as ``4a``), which sorts before ``5``.

    Args:
        sense_path: Canonical hierarchical path such as ``4.1``.

    Returns:
        Tuple of integer path segments for stable sorting.

    """
    if not sense_path:
        return (0,)
    key: list[int] = []
    for segment in sense_path.split("."):
        if segment.isdigit():
            key.append(int(segment))
        else:
            key.append(0)
    return tuple(key)


@dataclass(frozen=True)
class BTSense:
    """
    One English gloss sense for a consolidated dictionary entry.

    Attributes:
        gloss_en: English definition text with attestations stripped.
        sense_path: Hierarchical sense path within the source entry block.
        parent_path: Parent sense path when nested; ``None`` for top-level senses.
        source_label_raw: Raw Roman-numeral or letter label from the source.
        source_fragment_raw: Raw HTML/text fragment for this sense body.
        prefix_fragment_raw: POS/gender prefix fragment preceding the sense body.
        modifiers: Editorial modifier tokens attached to the sense.
        grammatical_context: Grammatical context tags for the sense gloss.
        usage_note: Free-text usage note when present in the source.

    """

    #: English gloss only; no OE/Latin citation tails.
    gloss_en: str
    #: Hierarchical sense path within one source entry block.
    sense_path: str
    #: Parent sense path when nested; ``None`` for top-level senses.
    parent_path: str | None
    #: Raw Roman-numeral or letter label from the source.
    source_label_raw: str
    #: Raw HTML/text fragment for this sense body.
    source_fragment_raw: str
    #: POS/gender prefix fragment preceding the sense body.
    prefix_fragment_raw: str
    #: Editorial modifier tokens attached to the sense.
    modifiers: tuple[str, ...]
    #: Grammatical context tags for the sense gloss.
    grammatical_context: tuple[str, ...]
    #: Free-text usage note when present in the source.
    usage_note: str

    @property
    def sense_label(self) -> str:
        """
        Backward-compatible sense label derived from ``source_label_raw``.

        Returns:
            Normalized sense label without a trailing period.

        """
        return self.source_label_raw.rstrip(".")

    @property
    def display_label(self) -> str:
        """
        User-facing sense label derived from ``sense_path``.

        Roman source labels are not shown. Unlabeled single senses return an
        empty string so browse output stays label-free.

        Returns:
            Arabic display label such as ``2a``; empty when unlabeled.

        """
        if not self.source_label_raw.strip():
            return ""
        return format_sense_display_label(self.sense_path)


def legacy_bt_sense(
    sense_label: str,
    gloss_en: str,
    *,
    sense_path: str | None = None,
    source_fragment_raw: str | None = None,
) -> BTSense:
    """
    Build a minimal ``BTSense`` from legacy label and gloss fields.

    Args:
        sense_label: Roman-numeral or letter label (for example ``I.``).
        gloss_en: English definition text with attestations stripped.

    Keyword Args:
        sense_path: Optional explicit sense path; defaults to ``sense_label`` or
            ``"1"`` when the label is empty.
        source_fragment_raw: Optional raw source fragment; defaults to
            ``gloss_en``.

    Returns:
        Rich ``BTSense`` populated with empty optional fields.

    """
    path = sense_path if sense_path is not None else (sense_label or "1")
    fragment = gloss_en if source_fragment_raw is None else source_fragment_raw
    return BTSense(
        gloss_en=gloss_en,
        sense_path=path,
        parent_path=None,
        source_label_raw=sense_label,
        source_fragment_raw=fragment,
        prefix_fragment_raw="",
        modifiers=(),
        grammatical_context=(),
        usage_note="",
    )


@dataclass(frozen=True)
class RawBTLine:
    """
    Parsed representation of one ``oe_bt.txt`` line before sense segmentation.

    Attributes:
        line_no: One-based source line number in ``oe_bt.txt``.
        kind: Line classification (main, add, substitute, etc.).
        headword_raw: First ``<B>…</B>`` headword text.
        pos_fragment: HTML immediately after the closing ``</B>`` tag.
        raw_text: Full unparsed line body between ``@`` separators.

    """

    #: One-based line number in the source file.
    line_no: int
    #: Editorial/main-line classification.
    kind: BTLineKind
    #: Bold headword spelling as printed in BT.
    headword_raw: str
    #: Prefix after ``</B>`` containing POS and gender markers.
    pos_fragment: str
    #: Full raw line text for downstream parsers.
    raw_text: str


@dataclass
class BTConsolidatedEntry:
    """
    Canonical dictionary record after editorial merge for one ``(norm_key, pos)``.

    Attributes:
        norm_key: ``normalize_old_english(headword_raw)`` lookup key.
        headword_raw: Display headword from the first contributing main line.
        headword_macronized: Acute-to-macron display spelling.
        normalized_title: Macron/dot-preserving normalized headword for joins.
        pos: Normalized part of speech.
        genders: Noun genders when applicable; empty otherwise.
        variants: Alternate spellings from the headword prefix.
        senses: Ordered English gloss senses.
        etymology: Bracket etymology blocks as plain text.
        see_also: Cross-reference targets from ``v.`` / ``vide`` lines.
        source_line_nos: Contributing ``oe_bt.txt`` line numbers.
        entry_order: Stable source-block ordering within the dictionary build.

    """

    #: Normalized Old English lookup key.
    norm_key: str
    #: First bold headword from contributing main line(s).
    headword_raw: str
    #: Macronized display form of ``headword_raw``.
    headword_macronized: str
    #: Macron/dot-preserving normalized headword for morphology joins.
    normalized_title: str
    #: Normalized part of speech.
    pos: BTPos
    #: Noun genders; empty when not applicable.
    genders: list[BTGender] = field(default_factory=list)
    #: Comma-separated variant spellings before POS markers.
    variants: list[str] = field(default_factory=list)
    #: Ordered sense glosses.
    senses: list[BTSense] = field(default_factory=list)
    #: Bracket etymology text with language tags preserved.
    etymology: str = ""
    #: Cross-reference headwords (not standalone entries).
    see_also: list[str] = field(default_factory=list)
    #: Source line numbers that contributed to this entry.
    source_line_nos: list[int] = field(default_factory=list)
    #: Stable source-block ordering within the dictionary build.
    entry_order: int = 0


@dataclass(frozen=True)
class BTParseWarning:
    """
    One parse warning emitted during dictionary indexing.

    Attributes:
        line_no: One-based source line number in ``oe_bt.txt``.
        body: Raw HTML body field from the source line.
        headword: Display headword for the warning record.
        pos_hint: Normalized POS label or ``unknown``.
        failure_reason: Diagnostic code describing the parse failure.
        detail: Optional human-readable diagnostic context.

    """

    #: One-based source line number.
    line_no: int
    #: Raw HTML body from the source line.
    body: str
    #: Display headword for the warning record.
    headword: str
    #: Normalized POS hint for the warning record.
    pos_hint: str
    #: Machine-readable warning reason.
    failure_reason: str
    #: Optional human-readable diagnostic context.
    detail: str = ""

    def to_json(self) -> dict[str, object]:
        """
        Serialize the warning to a JSON-friendly mapping.

        Returns:
            Mapping suitable for one ``parse_warnings.jsonl`` record.

        """
        return {
            "line_no": self.line_no,
            "body": self.body,
            "headword": self.headword,
            "pos_hint": self.pos_hint,
            "failure_reason": self.failure_reason,
            **({"detail": self.detail} if self.detail else {}),
        }

    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> BTParseWarning:
        """
        Parse one warning record from JSONL.

        Args:
            payload: Decoded JSON object from ``parse_warnings.jsonl``.

        Returns:
            Parsed warning record.

        """
        return cls(
            line_no=int(payload["line_no"]),
            body=str(payload["body"]),
            headword=str(payload["headword"]),
            pos_hint=str(payload["pos_hint"]),
            failure_reason=str(payload["failure_reason"]),
            detail=str(payload.get("detail", "")),
        )
