from __future__ import annotations

import json
from unittest.mock import patch
import pytest
from wyrdcraeft.ingest.extractors import LLMExtractor
from wyrdcraeft.models import AnyLLMConfig, TextMetadata


class TestLLMExtractor:
    def test_init_default(self):
        extractor = LLMExtractor()
        assert isinstance(extractor.config, AnyLLMConfig)
        assert extractor.config.provider == "ollama"

    def test_init_custom(self):
        config = AnyLLMConfig(provider="openai", model_id="gpt-4")
        extractor = LLMExtractor(config=config)
        assert extractor.config == config

    def test_prepare(self):
        extractor = LLMExtractor()
        messages = extractor.prepare("System prompt", "Old English text")
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "System prompt"
        assert messages[1]["role"] == "user"
        assert "Old English text" in messages[1]["content"]

    def test_parse_json_with_markdown(self):
        extractor = LLMExtractor()
        raw = 'Some text before\n```json\n{"key": "value"}\n```\nSome text after'
        obj = extractor.parse(raw)
        assert obj == {"key": "value"}

    def test_parse_json_direct(self):
        extractor = LLMExtractor()
        raw = '{"key": "value"}'
        obj = extractor.parse(raw)
        assert obj == {"key": "value"}

    def test_parse_json_in_text(self):
        extractor = LLMExtractor()
        raw = 'Here is the result: {"key": "value"} hope it helps'
        obj = extractor.parse(raw)
        assert obj == {"key": "value"}

    def test_parse_invalid_json(self):
        extractor = LLMExtractor()
        raw = "No JSON here"
        with pytest.raises(ValueError, match="No JSON object found in output"):
            extractor.parse(raw)

    def test_parse_incomplete_json(self):
        extractor = LLMExtractor()
        raw = '{"key": "value"'
        with pytest.raises(
            ValueError, match="Could not extract JSON object from output"
        ):
            extractor.parse(raw)

    @patch("wyrdcraeft.ingest.extractors.completion")
    def test_extract(self, mock_completion):
        mock_completion.return_value = json.dumps(
            {
                "content": {
                    "sections": [
                        {
                            "title": "Section 1",
                            "paragraphs": [{"sentences": [{"text": "Hwæt!"}]}],
                        }
                    ]
                }
            }
        )

        extractor = LLMExtractor()
        metadata = TextMetadata(title="Test", author="Author")
        result = extractor.extract(text="Hwæt!", metadata=metadata, prompt="Prompt")

        assert result.metadata.title == "Test"
        assert result.content.sections[0].title == "Section 1"
        assert result.content.sections[0].paragraphs[0].sentences[0].text == "Hwæt!"

        mock_completion.assert_called_once()
        args, kwargs = mock_completion.call_args
        assert kwargs["model"] == extractor.config.model_id
        assert kwargs["provider"] == extractor.config.provider

    @patch("wyrdcraeft.ingest.extractors.completion")
    def test_extract_with_preamble(self, mock_completion):
        mock_completion.return_value = json.dumps(
            {
                "content": {
                    "sections": [
                        {"title": "S1", "paragraphs": [{"sentences": [{"text": "T"}]}]}
                    ]
                }
            }
        )

        extractor = LLMExtractor()
        metadata = TextMetadata(title="Test")
        extractor.extract(
            text="T", metadata=metadata, prompt="Prompt", prompt_preamble="Preamble"
        )

        mock_completion.assert_called_once()
        args, kwargs = mock_completion.call_args
        # Prompt should include preamble
        system_msg = kwargs["messages"][0]["content"]
        assert "Preamble" in system_msg
        assert "Prompt" in system_msg
