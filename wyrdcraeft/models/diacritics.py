"""
Models for diacritic restoration output.
"""

from __future__ import annotations

from typing import Any, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

#: Supported part-of-speech code labels for ambiguity annotations.
POS_CODE_LABELS: Final[dict[str, str]] = {
    "N": "noun",
    "V": "verb",
    "PRO": "pronoun",
    "ADJ": "adjective",
    "ADV": "adverb",
    "CONJ": "conjunction",
    "PREP": "preposition",
    "INTJ": "interjection",
    "NUM": "number",
    "DET": "determiner/article",
}

#: Ordered part-of-speech codes for interactive selectors.
POS_CODES: Final[tuple[str, ...]] = tuple(POS_CODE_LABELS)

#: Supported POS literal type.
POSCodeLiteral = Literal[
    "N",
    "V",
    "PRO",
    "ADJ",
    "ADV",
    "CONJ",
    "PREP",
    "INTJ",
    "NUM",
    "DET",
]


class AmbiguityOption(BaseModel):
    """
    One candidate form for an ambiguous token, with POS and definitions when available.
    """

    model_config = ConfigDict(extra="forbid")

    #: The marked form (candidate the user may choose).
    form: str = Field(..., min_length=1)
    #: Human-readable part-of-speech label(s), or None if unknown.
    part_of_speech: str | None = None
    #: Modern English definitions from the macron index, when available.
    definitions: list[str] = Field(default_factory=list)


class MacronAmbiguity(BaseModel):
    """
    Ambiguity row for a token with multiple macron candidates.
    """

    model_config = ConfigDict(extra="forbid")

    #: 1-based line number in the source text.
    line_number: int = Field(..., ge=1)
    #: 1-based lexical word index within the source line.
    word_number: int = Field(..., ge=1)
    #: Verbatim source token.
    word: str = Field(..., min_length=1)
    #: Candidate forms with POS and definitions attached to each option.
    options: list[AmbiguityOption] = Field(default_factory=list)


class UnknownToken(BaseModel):
    """
    Token that was not found in the macron index (unrecognized word).
    """

    model_config = ConfigDict(extra="forbid")

    #: 1-based line number in the source text.
    line_number: int = Field(..., ge=1)
    #: 1-based lexical word index within the source line.
    word_number: int = Field(..., ge=1)
    #: Verbatim source token.
    word: str = Field(..., min_length=1)


class DiacriticRestorationResult(BaseModel):
    """
    Full diacritic restoration result payload.
    """

    model_config = ConfigDict(extra="forbid")

    #: Fully transformed marked text.
    marked_text: str = Field(..., description="Marked output text.")
    #: Ambiguity rows generated during macron application.
    ambiguities: list[MacronAmbiguity] = Field(default_factory=list)
    #: Tokens not found in the macron index (unrecognized words).
    unknowns: list[UnknownToken] = Field(default_factory=list)


class MacronFormAnnotation(BaseModel):
    """
    Per-form annotation for an ambiguous normalized entry.
    """

    model_config = ConfigDict(extra="forbid")

    #: One or more POS+meaning senses for this attested form.
    senses: list[MacronFormSense] = Field(default_factory=list)
    #: Legacy primary POS code retained for compatibility.
    part_of_speech_code: POSCodeLiteral | None = None
    #: Legacy primary meaning retained for compatibility.
    modern_english_meaning: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _normalize_senses(self) -> MacronFormAnnotation:
        """
        Normalize old/new annotation shapes into multi-sense form.

        Returns:
            Updated annotation with at least one populated sense.

        """
        if not self.senses:
            if self.part_of_speech_code is None or self.modern_english_meaning is None:
                msg = (
                    "MacronFormAnnotation requires at least one sense or legacy "
                    "part_of_speech_code + modern_english_meaning."
                )
                raise ValueError(msg)
            self.senses = [
                MacronFormSense(
                    part_of_speech_code=self.part_of_speech_code,
                    modern_english_meaning=self.modern_english_meaning,
                )
            ]

        if self.part_of_speech_code is None:
            self.part_of_speech_code = self.senses[0].part_of_speech_code
        if self.modern_english_meaning is None:
            self.modern_english_meaning = self.senses[0].modern_english_meaning
        return self


class MacronFormSense(BaseModel):
    """
    One POS+meaning sense for a single attested form.
    """

    model_config = ConfigDict(extra="forbid")

    #: Encoded part-of-speech tag.
    part_of_speech_code: POSCodeLiteral
    #: Modern English gloss/meaning.
    modern_english_meaning: str = Field(..., min_length=1)


class MacronIndexPayload(BaseModel):
    """
    On-disk macron index payload.
    """

    model_config = ConfigDict(extra="allow")

    #: Optional source/build metadata.
    meta: dict[str, Any] = Field(default_factory=dict)
    #: Deterministic normalized -> display mapping.
    unique: dict[str, str] = Field(default_factory=dict)
    #: Ambiguous normalized -> attested display forms mapping.
    ambiguous: dict[str, list[str]] = Field(default_factory=dict)
    #: Ambiguous keys that are fully annotated and excluded from default iteration.
    ambiguous_completed: set[str] = Field(default_factory=set)
    #: Optional per-form annotations for ambiguous entries.
    ambiguous_metadata: dict[str, dict[str, MacronFormAnnotation]] = Field(
        default_factory=dict
    )
