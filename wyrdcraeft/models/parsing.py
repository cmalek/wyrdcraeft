from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class RawBlock:
    """
    A raw block is a block of text that has been extracted from the source document.
    """

    #: The text of the block.
    text: str
    #: The category of the block.
    category: str
    #: The estimated kind of the block.
    kind: Literal["prose", "verse"]
    #: The page number of the block.
    page: int | None = None


@dataclass(frozen=True)
class ProvisionalSection:
    """
    A provisional section is a section that has been parsed from the raw blocks,
    but not yet validated or structured.
    """

    #: The title of the section.
    title: str | None
    #: The number of the section.
    number: str | int | None
    #: The kind of the section: prose or verse.
    kind: Literal["prose", "verse"]
    #: Any :class:`RawBlock` objects that make up the section.
    blocks: list[RawBlock]
    #: The page number of the section.
    page: int | None = None
    #: An optional hint for dialogue chunks.
    speaker_hint: str | None = None  # Optional hint for dialogue chunks


@dataclass(frozen=True)
class PreParsedDocument:
    """
    A pre-parsed document is a document that has been parsed from the raw blocks,
    but not yet validated or structured.
    """

    #: The provisional sections of the document.
    sections: list[ProvisionalSection]
