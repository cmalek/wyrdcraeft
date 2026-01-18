from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from oe_json_extractor.ingest.pipeline import LLMDocumentIngestor
from oe_json_extractor.models import OldEnglishText, TextMetadata, Section


class TestLLMDocumentIngestor:
    @pytest.fixture
    def ingestor(self):
        return LLMDocumentIngestor()

    @pytest.fixture
    def mock_metadata(self):
        return TextMetadata(
            title="Test Title",
            author="Test Author",
            source="Test Source",
            year="1000",
            language="Old English",
        )

    @patch("oe_json_extractor.ingest.pipeline.Path.read_text")
    def test_model_prompt(self, mock_read_text, ingestor):
        from oe_json_extractor.models.llm import AnyLLMConfig

        mock_read_text.return_value = "Model Prompt Content"

        config = AnyLLMConfig(model_id="qwen2.5:14b-instruct")
        prompt = ingestor.model_prompt(config, "prose")
        assert prompt == "Model Prompt Content"
        # The mock is called on the Path instance, so call_args might not have positional args if encoding is passed as kwarg
        assert mock_read_text.called

        config = AnyLLMConfig(model_id="gemini-1.5-pro")
        ingestor.model_prompt(config, "prose")
        assert mock_read_text.called

        config = AnyLLMConfig(model_id="gpt-4")
        ingestor.model_prompt(config, "prose")
        assert mock_read_text.called

    @patch("oe_json_extractor.ingest.pipeline.Path.read_text")
    def test_general_prompt(self, mock_read_text, ingestor):
        mock_read_text.return_value = "General Prompt"
        assert ingestor.general_prompt() == "General Prompt"

    @patch("oe_json_extractor.ingest.pipeline.Path.read_text")
    def test_mode_prompt(self, mock_read_text, ingestor):
        mock_read_text.return_value = "Mode Prompt"
        assert ingestor.mode_prompt("verse") == "Mode Prompt"

    @patch.object(LLMDocumentIngestor, "model_prompt")
    @patch.object(LLMDocumentIngestor, "general_prompt")
    @patch.object(LLMDocumentIngestor, "mode_prompt")
    def test_build_prompt(self, mock_mode, mock_gen, mock_model, ingestor):
        mock_model.return_value = "PART1"
        mock_gen.return_value = "PART2"
        mock_mode.return_value = "PART3"

        from oe_json_extractor.models.llm import AnyLLMConfig

        config = AnyLLMConfig()
        prompt = ingestor._build_prompt(config, "prose")

        assert "PART1" in prompt
        assert "PART2" in prompt
        assert "PART3" in prompt

    @patch("oe_json_extractor.ingest.pipeline.LLMExtractor")
    @patch.object(LLMDocumentIngestor, "_get_preparsed_doc")
    @patch.object(LLMDocumentIngestor, "_build_prompt")
    def test_ingest_llm(
        self,
        mock_build_prompt,
        mock_get_pre,
        mock_extractor_cls,
        ingestor,
        mock_metadata,
        temp_dir,
    ):
        # Setup pre-parsed doc
        from oe_json_extractor.models.parsing import (
            PreParsedDocument,
            ProvisionalSection,
            RawBlock,
        )

        block = RawBlock(text="Hwæt!", page=1, category="Title")
        psec = ProvisionalSection(
            title="S1",
            number=1,
            kind="prose",
            blocks=[block],
            page=1,
            speaker_hint=None,
        )
        mock_get_pre.return_value = PreParsedDocument(sections=[psec])

        mock_build_prompt.return_value = "Full Prompt"

        # Setup extractor
        mock_extractor = MagicMock()
        mock_extractor_cls.return_value = mock_extractor

        # Result from extractor
        content_section = Section(title="S1", number=1, paragraphs=[])
        partial_doc = OldEnglishText(
            metadata=mock_metadata,
            content=Section(title=None, number=None, sections=[content_section]),
        )
        mock_extractor.extract.return_value = partial_doc

        source_path = temp_dir / "test.txt"
        source_path.write_text("dummy")

        result = ingestor.ingest(source_path, mock_metadata)

        assert isinstance(result, OldEnglishText)
        mock_extractor.extract.assert_called_once()
        assert result.metadata == mock_metadata

    @patch("oe_json_extractor.ingest.pipeline.LLMExtractor")
    @patch.object(LLMDocumentIngestor, "_get_preparsed_doc")
    @patch.object(LLMDocumentIngestor, "_build_prompt")
    def test_ingest_llm_with_speaker(
        self,
        mock_build_prompt,
        mock_get_pre,
        mock_extractor_cls,
        ingestor,
        mock_metadata,
        temp_dir,
    ):
        from oe_json_extractor.models.parsing import (
            PreParsedDocument,
            ProvisionalSection,
            RawBlock,
        )

        block = RawBlock(text="Saturnus: Hwæt!", page=1, category="Text")
        psec = ProvisionalSection(
            title="S1",
            number=1,
            kind="verse",
            blocks=[block],
            page=1,
            speaker_hint="Saturnus",
        )
        mock_get_pre.return_value = PreParsedDocument(sections=[psec])

        mock_build_prompt.return_value = "Full Prompt"

        mock_extractor = MagicMock()
        mock_extractor_cls.return_value = mock_extractor

        content_section = Section(title="S1", number=1, lines=[])
        partial_doc = OldEnglishText(
            metadata=mock_metadata,
            content=Section(title=None, number=None, sections=[content_section]),
        )
        mock_extractor.extract.return_value = partial_doc

        source_path = temp_dir / "test.txt"
        source_path.write_text("dummy")

        ingestor.ingest(source_path, mock_metadata)

        # Check that metadata passed to extract has speaker hint in source
        extract_kwargs = mock_extractor.extract.call_args.kwargs
        passed_metadata = extract_kwargs["metadata"]
        assert "speaker_hint=Saturnus" in passed_metadata.source
        assert "DIALOGUE CONTEXT" in extract_kwargs["prompt_preamble"]
