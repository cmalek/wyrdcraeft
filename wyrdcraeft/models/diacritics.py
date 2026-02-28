"""
Models for diacritic restoration output.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


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
    #: Candidate marked forms for the token.
    options: list[str] = Field(default_factory=list)


class DiacriticRestorationResult(BaseModel):
    """
    Full diacritic restoration result payload.
    """

    model_config = ConfigDict(extra="forbid")

    #: Fully transformed marked text.
    marked_text: str = Field(..., description="Marked output text.")
    #: Ambiguity rows generated during macron application.
    ambiguities: list[MacronAmbiguity] = Field(default_factory=list)
