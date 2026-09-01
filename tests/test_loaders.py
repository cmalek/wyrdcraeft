from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from wyrdcraeft.ingest.loaders import (
    FileSourceLoader,
    SourceLoader,
    TEISourceLoader,
)
from wyrdcraeft.models.parsing import RawBlock


@pytest.fixture
def source_loader():
    return SourceLoader()


def test_load_from_file_text(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("þæt wæs god cyning.\n", encoding="utf-8")

    blocks = FileSourceLoader().load(file_path)
    assert len(blocks) >= 1
    assert all(isinstance(b, RawBlock) for b in blocks)
    assert "þæt wæs god cyning" in "".join(b.text for b in blocks)


def test_source_loader_rejects_http_url():
    with pytest.raises(ValueError, match="local"):
        SourceLoader().get_loader("https://example.com/a.txt")


def test_load_from_file_rejects_pdf():
    loader = FileSourceLoader()
    with pytest.raises(ValueError, match="Unsupported source format"):
        loader.load(Path("scan.pdf"))


def test_load_from_file_unsupported():
    loader = FileSourceLoader()
    with pytest.raises(ValueError, match="Unsupported source format"):
        loader.load(Path("test.unknown"))


def test_source_loader_load_file(tmp_path, source_loader):
    file_path = tmp_path / "test.txt"
    file_path.write_text("Hello World", encoding="utf-8")

    with patch.object(FileSourceLoader, "load") as mock_load:
        mock_load.return_value = [MagicMock(text="Hello World")]
        elements = source_loader.load(file_path)
        assert len(elements) == 1
        mock_load.assert_called_once_with(file_path)


def test_tei_source_loader_load_tei():
    tei_content = '<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader><titleStmt><title>Test</title></titleStmt></teiHeader><body><div><p>Hello</p></div></body></TEI>'
    loader = TEISourceLoader()
    doc = loader.load_from_tei(tei_content)
    assert doc.metadata.title == "Test"
    assert doc.content.paragraphs[0].sentences[0].text == "Hello"
