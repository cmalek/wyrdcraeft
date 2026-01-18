"""
Pydantic v2 schema models for canonical Old English text representation.

Design goals:

- Strict validation (no silent acceptance of unknown fields)
- Lossless structure representation without embedding editorial markers in text
- Optional confidence metadata for downstream tooling (e.g., highlighting
  uncertain parses)
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

# -----------------------------------------------------------------------------
# Types
# -----------------------------------------------------------------------------

#: A number (integer or string) for metadata.
Number = int | str
#: Confidence score for an extraction (0.0-1.0 recommended, but not enforced to
#: #allow upstream variance).
Confidence = float | None

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------


class Sentence(BaseModel):
    """
    A sentence in an Old English text.
    """

    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., description="Old English sentence text only.")
    number: Number | None = Field(None, description="Sentence/verse number (metadata).")
    source_page: Number | None = Field(
        None, description="Source page/folio identifier."
    )
    confidence: Confidence = Field(
        None,
        description=(
            "Optional confidence score for this sentence extraction "
            "(0.0-1.0 recommended).",
        ),
    )


class Paragraph(BaseModel):
    """
    A paragraph in an Old English text.

    Invariant:
        - A paragraph must contain only one speaker.
        - A paragraph must contain at least one sentence.
        - A paragraph cannot contain both prose and verse.

    Returns:
        A paragraph.

    """

    model_config = ConfigDict(extra="forbid")

    speaker: str | None = Field(None, description="Speaker label if dialogue.")
    sentences: list[Sentence] = Field(..., min_length=1)
    source_page: Number | None = Field(
        None, description="Source page/folio where paragraph begins."
    )
    confidence: Confidence = Field(
        None,
        description=(
            "Optional confidence score for this paragraph extraction "
            "(0.0-1.0 recommended).",
        ),
    )


class Line(BaseModel):
    """
    A line in an Old English poem.

    Returns:
        A line.

    """

    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., description="Old English poetic line text only.")
    number: int | None = Field(None, description="Poem line number (metadata).")
    speaker: str | None = Field(None, description="Speaker label for dialogue poetry.")
    source_page: Number | None = Field(
        None, description="Source page/folio identifier."
    )
    confidence: Confidence = Field(
        None,
        description=(
            "Optional confidence score for this line extraction (0.0-1.0 recommended).",
        ),
    )


class Section(BaseModel):
    """
    A recursive container for structural divisions:
    book/chapter/section/year-entry/etc.

    Invariant:
        - A single Section should not mix prose (`paragraphs`) and verse (`lines`)
          at the same level.  If a source interleaves prose+verse, represent as
          subsections.
    """

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(None, description="Title or heading of the section.")
    number: Number | None = Field(
        None, description="Section/chapter number or identifier."
    )
    sections: list[Section] | None = Field(None, description="Nested subsections.")
    paragraphs: list[Paragraph] | None = Field(None, description="Prose content.")
    lines: list[Line] | None = Field(None, description="Verse content.")
    source_page: Number | None = Field(
        None, description="Source page/folio where section begins."
    )
    confidence: Confidence = Field(
        None, description="Optional confidence score for section extraction."
    )

    @model_validator(mode="after")
    def _no_mixed_prose_and_verse(self) -> Section:
        """
        Validate that a section does not contain both prose and verse.  This
        means that a section cannot contain both paragraphs and lines.

        Returns:
            The section.

        """
        if self.paragraphs and self.lines:
            msg = (
                "Section cannot contain both paragraphs and lines; "
                "use subsections instead."
            )
            raise ValueError(msg)
        return self


Section.model_rebuild()


class TextMetadata(BaseModel):
    """
    Metadata for an Old English text.
    """

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., description="Title of the text.")
    author: str | None = Field(None, description="Author of the text.")
    source: str | None = Field(None, description="Bibliographic source or URL.")
    year: str | None = Field(None, description="Date/period of composition.")
    language: str = Field("Old English", description="Language of the text.")
    editor: str | None = Field(None, description="Editor of the text.")
    license: str | None = Field(None, description="License of the text.")


class OldEnglishText(BaseModel):
    #: The current canonical schema version of our models.
    schema_version: str = "1.5"

    model_config = ConfigDict(extra="forbid")

    metadata: TextMetadata = Field(..., description="Metadata for the text.")
    content: Section = Field(..., description="Content of the text.")

    def all_sentences(self) -> list[Sentence]:
        """
        Get all sentences in the text.

        Returns:
            A list of sentences.

        """
        out: list[Sentence] = []

        def walk(sec: Section) -> None:
            if sec.paragraphs:
                for p in sec.paragraphs:
                    out.extend(p.sentences)
            if sec.sections:
                for s in sec.sections:
                    walk(s)

        walk(self.content)
        return out

    def all_lines(self) -> list[Line]:
        """
        Get all lines in the text.

        Returns:
            A list of lines.

        """
        out: list[Line] = []

        def walk(sec: Section) -> None:
            if sec.lines:
                out.extend(sec.lines)
            if sec.sections:
                for s in sec.sections:
                    walk(s)

        walk(self.content)
        return out
