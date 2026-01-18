from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch
import pytest
from oe_json_extractor.settings import Settings
from oe_json_extractor.models.llm import AnyLLMConfig


class TestSettings:
    def test_default_settings(self):
        settings = Settings()
        assert settings.app_name == "oe_json_extractor"
        assert settings.llm_provider == "ollama"
        assert settings.llm_model_id == "qwen2.5:14b-instruct"
        assert settings.llm_timeout_s == 120

    def test_llm_config_property(self):
        settings = Settings(
            llm_provider="openai",
            llm_model_id="gpt-4",
            llm_temperature=0.5,
            llm_max_tokens=1000,
            llm_timeout_s=60,
        )
        config = settings.llm_config
        assert isinstance(config, AnyLLMConfig)
        assert config.provider == "openai"
        assert config.model_id == "gpt-4"
        assert config.temperature == 0.5
        assert config.max_tokens == 1000
        assert config.timeout_s == 60

    def test_validate_settings_valid(self):
        settings = Settings()
        # Should not raise
        settings.validate_settings()

    def test_validate_settings_invalid_provider(self):
        # We use Any because Pydantic might catch it early if we use literal
        from typing import Any

        settings = Settings()
        settings.llm_provider = "invalid"  # type: ignore
        with pytest.raises(Exception):  # ConfigurationError
            settings.validate_settings()

    def test_validate_settings_invalid_timeout(self):
        settings = Settings(llm_timeout_s=0)
        with pytest.raises(Exception):  # ConfigurationError
            settings.validate_settings()

    def test_validate_settings_invalid_output_format(self):
        settings = Settings()
        # Bypass pydantic validation to test our own validation
        settings.__dict__["default_output_format"] = "invalid"
        with pytest.raises(Exception):  # ConfigurationError
            settings.validate_settings()

    def test_env_override(self):
        os.environ["OE_JSON_EXTRACTOR_LLM_PROVIDER"] = "gemini"
        try:
            settings = Settings()
            assert settings.llm_provider == "gemini"
        finally:
            del os.environ["OE_JSON_EXTRACTOR_LLM_PROVIDER"]

    def test_get_config_paths(self, tmp_path):
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            with patch("pathlib.Path.home", return_value=tmp_path / "home"):
                local_config = tmp_path / ".oe_json_extractor.toml"
                local_config.touch()

                settings = Settings()
                paths = settings.get_config_paths()
                assert any(p.name == ".oe_json_extractor.toml" for p in paths)
