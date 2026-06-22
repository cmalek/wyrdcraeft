"""Bosworth-Toller dictionary index models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


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


@dataclass(frozen=True)
class BTSense:
    """
    One English gloss sense for a consolidated dictionary entry.

    Attributes:
        sense_label: Roman-numeral or letter label (for example ``I.``).
        gloss_en: English definition text with attestations stripped.

    """

    #: Sense label such as ``I.`` or ``II.``.
    sense_label: str
    #: English gloss only; no OE/Latin citation tails.
    gloss_en: str


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
        pos: Normalized part of speech.
        genders: Noun genders when applicable; empty otherwise.
        variants: Alternate spellings from the headword prefix.
        senses: Ordered English gloss senses.
        etymology: Bracket etymology blocks as plain text.
        see_also: Cross-reference targets from ``v.`` / ``vide`` lines.
        source_line_nos: Contributing ``oe_bt.txt`` line numbers.

    """

    #: Normalized Old English lookup key.
    norm_key: str
    #: First bold headword from contributing main line(s).
    headword_raw: str
    #: Macronized display form of ``headword_raw``.
    headword_macronized: str
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
