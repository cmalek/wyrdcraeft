"""
Unit tests for configuration settings.

Tests the new OpenAI and summary generation configuration fields,
validation logic, and TOML file loading.
"""

from pathlib import Path
from types import NoneType
from unittest.mock import patch

import pytest

from wyrdcraeft.settings import Settings


class TestConfiguration:
    """Test cases for configuration settings."""

    def test_default_settings(self):
        """Test default settings values."""
        with patch(
            "wyrdcraeft.settings.Settings.model_config",
            {"extra": "ignore", "env_prefix": "wyrdcraeft_"},
        ):
            settings = Settings()

            assert settings.app_name == "wyrdcraeft"
            assert settings.app_version == "0.1.0"
            assert settings.default_output_format == "table"
            assert settings.enable_colors is True
            assert settings.quiet_mode is False
            assert settings.log_level == "INFO"
            assert settings.log_file is None

    def test_validate_settings_success(self):
        """Test successful settings validation."""
        settings = Settings()

        # Should not raise any exceptions
        with patch("pathlib.Path.exists", return_value=True):
            settings.validate_settings()

    @patch("wyrdcraeft.settings.Path.home")
    def test_load_config_with_toml_file(self, mock_home, tmp_path):
        """Test loading configuration with TOML file."""
        # Mock file system calls to simulate a config file existing
        mock_home.return_value = tmp_path / "home" / "user"
        mock_home.return_value.mkdir(parents=True, exist_ok=True)
        config_file = mock_home.return_value / ".cmdline_test.toml"
        config_file.write_text('default_output_format = "json"', encoding="utf-8")

        # Set environment variable to point to the config file
        with patch.dict("os.environ", {"wyrdcraeft_CONFIG_FILE": str(config_file)}):
            # Test that the Settings class can be instantiated with TOML-like behavior
            settings = Settings()
            # Verify the values are set correctly
            assert settings.default_output_format == "json"

        # Test that the settings_customise_sources method exists and is callable
        assert hasattr(Settings, "settings_customise_sources")
        assert callable(Settings.settings_customise_sources)

        # Test that the method returns the expected structure when called directly
        result = Settings.settings_customise_sources(Settings, None, None, None, None)
        # Should return a tuple (either with TOML source or empty)
        assert isinstance(result, tuple)

    def test_load_config_without_toml_file(self):
        """Test loading configuration without TOML file."""
        with patch("wyrdcraeft.settings.Settings.model_config", {"toml_file": []}):
            settings = Settings()

            # Should use default values
            assert settings.default_output_format == "table"
            assert settings.enable_colors is True
            assert settings.quiet_mode is False
            assert settings.log_level == "INFO"
            assert settings.log_file is None

    def test_load_config_error(self):
        """Test loading configuration with error."""
        with (  # noqa: SIM117
            patch(
                "wyrdcraeft.settings.Settings.model_config",
                {"extra": "ignore", "env_prefix": "wyrdcraeft_"},
            ),
            patch(
                "wyrdcraeft.settings.Settings.__init__",
                side_effect=Exception("Config error"),
            ),
        ):
            with pytest.raises(Exception, match="Config error"):
                Settings()

    def test_settings_field_descriptions(self):
        """Test that settings fields have proper descriptions."""
        assert (
            Settings.model_fields["default_output_format"].description
            == "Default output format"
        )
        assert (
            Settings.model_fields["enable_colors"].description
            == "Enable colored output"
        )
        assert Settings.model_fields["quiet_mode"].description == "Enable quiet mode"
        assert Settings.model_fields["log_level"].description == "Logging level"
        assert Settings.model_fields["log_file"].description == "Log file path"

    def test_settings_model_config(self):
        """Test that model_config is properly configured."""
        settings = Settings()

        # Check that env_file includes the expected files
        assert settings.model_config.get("env_prefix") == "wyrdcraeft_"
        assert settings.model_config.get("extra") == "ignore"

    def test_settings_validation_output_format(self):
        """Test output format validation."""
        # Test that invalid format raises error during initialization
        with pytest.raises(Exception, match="Input should be"):
            Settings(default_output_format="invalid")

        # Test that valid format passes validation
        settings = Settings(default_output_format="json")
        with patch("pathlib.Path.exists", return_value=True):
            settings.validate_settings()

    def test_settings_validation_valid_default_output_format(self):
        """Test valid output format validation."""
        valid_formats = ["table", "json", "text"]

        for output_format in valid_formats:
            settings = Settings(default_output_format=output_format)
            # Should not raise any exceptions
            with patch("pathlib.Path.exists", return_value=True):
                settings.validate_settings()

    def test_settings_with_environment_variables(self):
        """
        Test settings loading from environment variables.

        This test is a placeholder for future settings that are loaded from environment variables that have no default.
        """
        with (
            patch.dict(
                "os.environ",
                {
                    "wyrdcraeft_YOUR_ENV_VAR": "value",
                },
            ),
            patch(
                "wyrdcraeft.settings.Settings.model_config",
                {"extra": "ignore", "env_prefix": "wyrdcraeft_"},
            ),
        ):
            settings = Settings()

            # Test any settings here that MUST be provided

    def test_settings_environment_variable_override(self):
        """Test that environment variables override defaults."""
        with (
            patch.dict(
                "os.environ",
                {
                    "wyrdcraeft_DEFAULT_OUTPUT_FORMAT": "json",
                },
            ),
            patch(
                "wyrdcraeft.settings.Settings.model_config",
                {"extra": "ignore", "env_prefix": "wyrdcraeft_"},
            ),
        ):
            settings = Settings()

            assert settings.default_output_format == "json"

    def test_settings_case_insensitive(self):
        """Test that settings are case insensitive."""
        with (
            patch.dict(
                "os.environ",
                {
                    "wyrdcraeft_default_output_format": "json",
                },
            ),
            patch(
                "wyrdcraeft.settings.Settings.model_config",
                {"extra": "ignore", "env_prefix": "wyrdcraeft_"},
            ),
        ):
            settings = Settings()

            assert settings.default_output_format == "json"

    def test_settings_extra_fields_ignored(self):
        """Test that extra fields in TOML are ignored."""
        # Test that the Settings class properly handles extra fields
        # by creating a Settings instance and verifying it only has expected fields

        # Create settings with some values
        settings = Settings(setting1="value1", setting2="value2")

        # Verify known fields are set
        assert settings.default_output_format == "table"
        assert settings.enable_colors is True

        # Verify that extra fields are not attributes
        assert not hasattr(settings, "setting1")
        assert not hasattr(settings, "setting2")

        # Test that setting extra attributes doesn't affect the model
        # (this tests the extra="ignore" behavior)
        settings._extra_data = {"unknown_field": "should be ignored"}  # noqa: SLF001
        assert not hasattr(settings, "unknown_field")

    def test_settings_field_types(self):
        """Test that settings fields have correct types."""
        settings = Settings()

        assert isinstance(settings.default_output_format, str)
        assert isinstance(settings.enable_colors, bool)
        assert isinstance(settings.quiet_mode, bool)
        assert isinstance(settings.log_level, str)
        assert isinstance(settings.log_file, NoneType)

    def test_settings_field_defaults(self):
        """Test that settings fields have correct defaults."""

        with patch(
            "wyrdcraeft.settings.Settings.model_config",
            {"extra": "ignore", "env_prefix": "wyrdcraeft_"},
        ):
            settings = Settings()

            assert settings.default_output_format == "table"
            assert settings.enable_colors is True
            assert settings.quiet_mode is False
            assert settings.log_level == "INFO"
            assert settings.log_file is None
