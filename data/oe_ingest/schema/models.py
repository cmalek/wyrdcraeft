from __future__ import annotations

from pydantic import BaseModel


class TextMetadata(BaseModel):
    title: str
    source: str | None = None
    author: str | None = None
    year: str | None = None
    editor: str | None = None
    license: str | None = None
    language: str = "ang"


class Sentence(BaseModel):
    text: str
    number: str | int | None = None
    source_page: int | str | None = None
    confidence: float | None = None


class Paragraph(BaseModel):
    speaker: str | None = None
    sentences: list[Sentence]
    source_page: int | str | None = None
    confidence: float | None = None


class Line(BaseModel):
    text: str
    number: int | str | None = None
    speaker: str | None = None
    source_page: int | str | None = None
    confidence: float | None = None


class Section(BaseModel):
    title: str | None = None
    number: str | int | None = None
    sections: list["Section"] | None = None  # noqa: UP037
    paragraphs: list[Paragraph] | None = None
    lines: list[Line] | None = None
    source_page: int | str | None = None
    confidence: float | None = None


Section.model_rebuild()


class OldEnglishText(BaseModel):
    schema_version: str = "1.0"
    metadata: TextMetadata
    content: Section
