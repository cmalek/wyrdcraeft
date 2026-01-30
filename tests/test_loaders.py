from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from wyrdcraeft.ingest.loaders import (
    FileSourceLoader,
    HTTPSourceLoader,
    SourceLoader,
    TEISourceLoader,
)


@pytest.fixture
def source_loader():
    return SourceLoader()


def test_load_from_file_text(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("Hello World", encoding="utf-8")

    loader = FileSourceLoader()
    with patch("wyrdcraeft.ingest.loaders.partition_text") as mock_partition:
        mock_partition.return_value = [MagicMock(text="Hello World")]
        elements = loader.load_from_file(file_path)
        assert len(elements) == 1
        assert elements[0].text == "Hello World"
        mock_partition.assert_called_once_with(filename=str(file_path))


def test_load_from_file_unsupported():
    loader = FileSourceLoader()
    with pytest.raises(ValueError, match="Unsupported source format"):
        loader.load_from_file(Path("test.unknown"))


def test_source_loader_load_file(tmp_path, source_loader):
    file_path = tmp_path / "test.txt"
    file_path.write_text("Hello World", encoding="utf-8")

    with patch.object(FileSourceLoader, "load") as mock_load:
        mock_load.return_value = [MagicMock(text="Hello World")]
        elements = source_loader.load(file_path)
        assert len(elements) == 1
        mock_load.assert_called_once_with(file_path)


def test_source_loader_load_url(source_loader):
    url = "https://example.com/test.txt"
    mock_response = MagicMock()
    mock_response.content = b"Hello from URL"
    mock_response.status_code = 200
    mock_response.headers = {}

    with (
        patch("httpx.Client.get", return_value=mock_response) as mock_get,
        patch.object(HTTPSourceLoader, "load_from_file") as mock_load_file,
    ):
        mock_load_file.return_value = [MagicMock(text="Hello from URL")]

        elements = source_loader.load(url)

        assert len(elements) == 1
        mock_get.assert_called_once_with(url)
        # Verify that load_from_file was called with a path in a temporary directory
        args, _ = mock_load_file.call_args
        temp_file_path = args[0]
        assert isinstance(temp_file_path, Path)
        assert ".txt" in temp_file_path.suffix


def test_source_loader_load_url_content_type(source_loader):
    url = "https://example.com/test"
    mock_response = MagicMock()
    mock_response.content = b"<html><body>Hello</body></html>"
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "text/html"}

    with (
        patch("httpx.Client.get", return_value=mock_response) as mock_get,
        patch.object(HTTPSourceLoader, "load_from_file") as mock_load_file,
    ):
        mock_load_file.return_value = [MagicMock(text="Hello")]

        elements = source_loader.load(url)

        assert len(elements) == 1
        mock_get.assert_called_once_with(url)
        args, _ = mock_load_file.call_args
        temp_file_path = args[0]
        assert temp_file_path.suffix == ".html"


def test_tei_source_loader_load_tei():
    tei_content = '<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader><titleStmt><title>Test</title></titleStmt></teiHeader><body><div><p>Hello</p></div></body></TEI>'
    loader = TEISourceLoader()
    doc = loader.load_from_tei(tei_content)
    assert doc.metadata.title == "Test"
    assert doc.content.paragraphs[0].sentences[0].text == "Hello"
