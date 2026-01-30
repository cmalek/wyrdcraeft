from __future__ import annotations

import pytest
from wyrdcraeft.models.llm import AnyLLMConfig


class TestAnyLLMConfig:
    def test_default_config(self):
        config = AnyLLMConfig()
        assert config.provider == "ollama"
        assert config.model_id == "qwen2.5:14b-instruct"
        assert config.temperature == 0.0
        assert config.max_tokens == 4096
        assert config.timeout_s == 120

    def test_model_property_qwen(self):
        config = AnyLLMConfig(model_id="qwen2.5:14b-instruct")
        assert config.model == "qwen"

    def test_model_property_gemini(self):
        config = AnyLLMConfig(model_id="gemini-1.5-pro")
        assert config.model == "gemini"

    def test_model_property_openai(self):
        for model_id in ["gpt-4", "o1-mini", "o3-preview"]:
            config = AnyLLMConfig(model_id=model_id)
            assert config.model == "openai"

    def test_model_property_unknown(self):
        config = AnyLLMConfig(model_id="unknown-model")
        with pytest.raises(ValueError, match="Unknown model ID: unknown-model"):
            _ = config.model
