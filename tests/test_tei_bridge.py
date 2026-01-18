from __future__ import annotations

from oe_json_extractor.models.schema import (
    OldEnglishText,
    TextMetadata,
    Section,
    Paragraph,
    Sentence,
    Line,
)
from oe_json_extractor.ingest.exporters import to_tei, from_tei


def test_tei_roundtrip_minimal_prose() -> None:
    doc = OldEnglishText(
        metadata=TextMetadata(title="T", source="S"),
        content=Section(
            title=None,
            number=None,
            sections=[
                Section(
                    title="Cap. I",
                    number="I",
                    paragraphs=[
                        Paragraph(
                            sentences=[Sentence(text="Her onginneð...")], speaker=None
                        )
                    ],
                )
            ],
        ),
    )
    xml = to_tei(doc)
    parsed = from_tei(xml)
    assert parsed.metadata.title == "T"
    assert parsed.content.sections
    assert parsed.content.sections[0].title == "Cap. I"
    assert parsed.content.sections[0].paragraphs
    assert parsed.content.sections[0].paragraphs[0].sentences[0].text.startswith("Her")


def test_tei_roundtrip_minimal_verse_dialogue() -> None:
    doc = OldEnglishText(
        metadata=TextMetadata(title="D", source="S"),
        content=Section(
            title=None,
            number=None,
            sections=[
                Section(
                    title=None,
                    number=None,
                    lines=[
                        Line(text="Saga mē...", number=1, speaker="Saturnus"),
                        Line(text="Ic þe secge...", number=2, speaker="Salomon"),
                    ],
                )
            ],
        ),
    )
    xml = to_tei(doc)
    parsed = from_tei(xml)
    assert parsed.content.sections
    sec = parsed.content.sections[0]
    assert sec.lines
    assert sec.lines[0].text.startswith("Saga")
