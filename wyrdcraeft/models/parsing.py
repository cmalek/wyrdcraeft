from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

MIN_VERSE_LINES = 2
MAX_VERSE_AVG_LINE_LEN = 60
MAX_PROSE_ENDING_RATIO = 0.8


@dataclass(frozen=True)
class RawBlock:
    """
    A raw block is a block of text that has been extracted from the source document.
    """

    #: The text of the block.
    text: str
    #: The category of the block.
    category: str | None
    #: The estimated kind of the block. If omitted, it will be inferred.
    kind: Literal["prose", "verse"] | None = None
    #: The page number of the block.
    page: int | None = None

    def __post_init__(self) -> None:
        """
        Backward-compatible kind inference for callers that only pass text/category.
        """
        if self.kind is not None:
            return

        lines = [ln.strip() for ln in self.text.splitlines() if ln.strip()]
        if len(lines) >= MIN_VERSE_LINES:
            avg_len = sum(len(ln) for ln in lines) / len(lines)
            prose_like = sum(1 for ln in lines if ln.endswith(".")) / len(lines)
            inferred: Literal["prose", "verse"] = (
                "verse"
                if avg_len <= MAX_VERSE_AVG_LINE_LEN
                and prose_like < MAX_PROSE_ENDING_RATIO
                else "prose"
            )
        else:
            inferred = "prose"

        object.__setattr__(self, "kind", inferred)


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
