from __future__ import annotations

from pathlib import Path

from oe_json_extractor.ingest.exporters import TEIExporter
from oe_json_extractor.ingest.loaders import TEISourceLoader
from oe_json_extractor.models import (
    Line,
    OldEnglishText,
    Paragraph,
    Section,
    Sentence,
    TextMetadata,
)


def test_tei_import_beowulf() -> None:
    """Test importing Beowulf from TEI XML."""
    fixture_path = Path(__file__).parent / "fixtures" / "beowulfOE.xml"
    doc = TEISourceLoader().load(fixture_path)

    assert doc.metadata.title == "Beowulf : a digital edition"
    assert doc.content is not None
    # The Beowulf fixture may have content in lines or nested sections
    assert doc.content.lines or doc.content.sections

    if doc.content.lines:
        assert len(doc.content.lines) > 0
        # Check first line text - the fixture seems to use entities
        # Ðā cōm of mōre...
        first_line = doc.content.lines[0].text
        assert "Ðā" in first_line or "HWÆT" in first_line


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
    xml = TEIExporter().export(doc)
    parsed = TEISourceLoader().load_from_tei(xml)
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
    xml = TEIExporter().export(doc)
    parsed = TEISourceLoader().load_from_tei(xml)
    assert parsed.content.sections
    sec = parsed.content.sections[0]
    assert sec.lines
    assert sec.lines[0].text.startswith("Saga")
