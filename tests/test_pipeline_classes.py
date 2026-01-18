from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from oe_json_extractor.ingest.pipeline import (
    StructureParser,
    OEFilter,
    CanonicalConverter,
    DocumentIngestor,
    HeuristicDocumentIngestor,
    LLMDocumentIngestor,
    TEIDocumentIngestor,
)
from oe_json_extractor.models.parsing import RawBlock
from oe_json_extractor.models import OldEnglishText, TextMetadata, Section

FIX = Path(__file__).parent / "fixtures"


def _t(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8").strip()


@pytest.fixture
def prose_text():
    return _t("fixture_prose.txt")


@pytest.fixture
def verse_text():
    return _t("fixture_poetry.txt")


@pytest.fixture
def dialogue_text():
    return _t("fixture_dialogue.txt")


def test_oe_filter():
    oe_filter = OEFilter()
    assert oe_filter.looks_like_old_english("Hwæt! We Gardena in geardagum") is True
    assert oe_filter.looks_like_old_english("This is modern English") is False


def test_structure_parser_prose(prose_text):
    parser = StructureParser()
    blocks = [RawBlock(text=prose_text, category="NarrativeText", page=1)]
    doc = parser.parse(blocks)
    assert len(doc.sections) == 1
    assert doc.sections[0].kind == "prose"


def test_structure_parser_verse(verse_text):
    parser = StructureParser()
    blocks = [RawBlock(text=verse_text, category="NarrativeText", page=1)]
    doc = parser.parse(blocks)
    assert len(doc.sections) == 1
    assert doc.sections[0].kind == "verse"


def test_canonical_converter_prose(prose_text):
    parser = StructureParser()
    blocks = [RawBlock(text=prose_text, category="NarrativeText", page=1)]
    pre_doc = parser.parse(blocks)
    converter = CanonicalConverter()
    meta = TextMetadata(title="Test Prose", source="Test Source")
    oe_text = converter.build(meta, pre_doc)
    assert oe_text.metadata.title == "Test Prose"
    assert len(oe_text.content.sections) == 1
    assert oe_text.content.sections[0].paragraphs is not None


def test_canonical_converter_verse(verse_text):
    parser = StructureParser()
    blocks = [RawBlock(text=verse_text, category="NarrativeText", page=1)]
    pre_doc = parser.parse(blocks)
    converter = CanonicalConverter()
    meta = TextMetadata(title="Test Verse", source="Test Source")
    oe_text = converter.build(meta, pre_doc)
    assert oe_text.metadata.title == "Test Verse"
    assert len(oe_text.content.sections) == 1
    assert oe_text.content.sections[0].lines is not None


@patch("oe_json_extractor.ingest.pipeline.LLMExtractor")
@patch("oe_json_extractor.ingest.pipeline.load_elements")
@patch("oe_json_extractor.ingest.pipeline.normalize_elements_to_blocks")
def test_llm_document_ingestor(mock_normalize, mock_load, mock_extractor_class):
    # Setup mocks
    mock_load.return_value = []
    mock_normalize.return_value = [
        RawBlock(
            text="Hwæt! We Gardena\nin geardagum", category="NarrativeText", page=1
        )
    ]

    mock_extractor = MagicMock()
    mock_extractor_class.return_value = mock_extractor

    # Mock return of extractor.extract
    meta = TextMetadata(title="Mocked Title", source="Mocked Source")
    root_section = Section(
        title=None,
        number=None,
        sections=[Section(title="Mocked Section", paragraphs=[])],
        paragraphs=None,
        lines=None,
    )
    mock_extractor.extract.return_value = OldEnglishText(
        metadata=meta, content=root_section
    )

    # Run ingest
    with patch("oe_json_extractor.ingest.pipeline.Path.exists", return_value=True):
        ingestor = LLMDocumentIngestor()
        result = ingestor.ingest(Path("dummy.txt"), meta)

    assert result.metadata.title == "Mocked Title"
    assert len(result.content.sections) == 1
    assert result.content.sections[0].title == "Mocked Section"
    mock_extractor.extract.assert_called_once()


@patch("oe_json_extractor.ingest.pipeline.load_elements")
@patch("oe_json_extractor.ingest.pipeline.normalize_elements_to_blocks")
def test_document_ingestor_dispatch(mock_normalize, mock_load):
    mock_load.return_value = []
    mock_normalize.return_value = [
        RawBlock(text="Hwæt! We Gardena", category="NarrativeText", page=1)
    ]

    ingestor = DocumentIngestor()
    meta = TextMetadata(title="Deterministic Title", source="Source")
    # Should use HeuristicDocumentIngestor
    result = ingestor.ingest(Path("dummy.txt"), meta, use_llm=False)

    assert result.metadata.title == "Deterministic Title"
    assert result.content.sections is not None
