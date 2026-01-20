from __future__ import annotations

import pytest

from oe_json_extractor.ingest.exporters import TEIExporter
from oe_json_extractor.models import (
    Line,
    OldEnglishText,
    Paragraph,
    Section,
    Sentence,
    TextMetadata,
)


@pytest.fixture
def sample_doc() -> OldEnglishText:
    return OldEnglishText(
        metadata=TextMetadata(
            title="Sample Text", author="Chris Malek", source="Original"
        ),
        content=Section(
            title="Introduction",
            number=1,
            paragraphs=[
                Paragraph(
                    sentences=[
                        Sentence(text="This is a sentence.", number=1),
                        Sentence(text="This is another sentence.", number=2),
                    ],
                    speaker="Narrator",
                )
            ],
            sections=[
                Section(
                    title="Verse Section",
                    lines=[
                        Line(text="Line one of verse.", number=1, speaker="Poet"),
                        Line(text="Line two of verse.", number=2, speaker="Poet"),
                        Line(
                            text="Line three from another.", number=3, speaker="Other"
                        ),
                    ],
                )
            ],
        ),
    )


def test_tei_exporter_interface() -> None:
    exporter = TEIExporter()
    assert hasattr(exporter, "export")


def test_tei_export_basic(sample_doc: OldEnglishText) -> None:
    exporter = TEIExporter()
    xml = exporter.export(sample_doc)

    assert '<?xml version="1.0" encoding="UTF-8"?>' in xml or "<TEI" in xml
    assert "Sample Text" in xml
    assert "Chris Malek" in xml
    assert "Narrator" in xml
    assert "Poet" in xml
    assert "Other" in xml
    assert "Line one of verse." in xml


def test_tei_export_structure(sample_doc: OldEnglishText) -> None:
    exporter = TEIExporter()
    xml = exporter.export(sample_doc)

    # Check for TEI namespace
    assert 'xmlns="http://www.tei-c.org/ns/1.0"' in xml

    # Check for specific tags (allowing for potential namespace prefixes)
    assert "teiHeader" in xml
    assert "titleStmt" in xml
    assert "body" in xml
    assert "div" in xml
    assert "sp" in xml
    assert "p" in xml
    assert "s" in xml
    assert "lg" in xml
    assert "l" in xml


def test_tei_export_attributes(sample_doc: OldEnglishText) -> None:
    exporter = TEIExporter()
    xml = exporter.export(sample_doc)

    # Check attributes
    assert 'who="Narrator"' in xml
    assert 'n="1"' in xml
    assert 'who="Poet"' in xml
    assert 'who="Other"' in xml
