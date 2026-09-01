"""
Tests for CLI commands with low coverage.
"""

from __future__ import annotations

import json

from wyrdcraeft.cli.cli import cli
from wyrdcraeft.cli.utils import console


class TestCLIVersion:
    """Test the version command."""

    def test_version_command(self, runner):
        """Test the version command displays version information."""
        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0
        # The command should run successfully without errors
        # Rich console output may not be captured in test environment

    def test_version_command_with_verbose(self, runner):
        """Test the version command with verbose flag."""
        result = runner.invoke(cli, ["--verbose", "version"])
        assert result.exit_code == 0

    def test_version_command_with_quiet(self, runner):
        """Test the version command with quiet flag."""
        result = runner.invoke(cli, ["--quiet", "version"])
        assert result.exit_code == 0


class TestCLISettings:
    """Test the settings command."""

    def test_settings_command_table_output(self, runner):
        """Test the settings command with table output."""
        result = runner.invoke(cli, ["settings"])
        assert result.exit_code == 0

    def test_settings_command_json_output(self, runner):
        """Test the settings command with JSON output."""
        result = runner.invoke(cli, ["--output", "json", "settings"])
        assert result.exit_code == 0
        # Should be valid JSON
        data = json.loads(result.output)
        assert isinstance(data, dict)

    def test_settings_command_text_output(self, runner):
        """Test the settings command with text output."""
        result = runner.invoke(cli, ["--output", "text", "settings"])
        assert result.exit_code == 0

    def test_settings_command_with_verbose(self, runner):
        """Test the settings command with verbose flag."""
        result = runner.invoke(cli, ["--verbose", "settings"])
        assert result.exit_code == 0

    def test_settings_command_with_config_file(self, runner, temp_dir):
        """Test the settings command with custom config file."""
        config_file = temp_dir / "test_config.toml"
        config_file.write_text('default_output_format = "json"', encoding="utf-8")

        result = runner.invoke(cli, ["--config-file", str(config_file), "settings"])
        assert result.exit_code == 0


class TestCLIGlobalOptions:
    """Test global CLI options."""

    def test_verbose_flag(self, runner):
        """Test verbose flag is properly set."""
        result = runner.invoke(cli, ["--verbose", "version"])
        assert result.exit_code == 0

    def test_quiet_flag(self, runner):
        """Test quiet flag is properly set."""
        result = runner.invoke(cli, ["--quiet", "version"])
        assert result.exit_code == 0

    def test_quiet_flag_does_not_leak_between_invocations(self, runner):
        """Quiet mode should reset on next non-quiet CLI invocation."""
        quiet_result = runner.invoke(cli, ["--quiet", "version"])
        assert quiet_result.exit_code == 0
        assert console.quiet is True

        normal_result = runner.invoke(cli, ["version"])
        assert normal_result.exit_code == 0
        assert console.quiet is False

    def test_output_format_default(self, runner):
        """Test default output format is table."""
        result = runner.invoke(cli, ["settings"])
        assert result.exit_code == 0

    def test_output_format_json(self, runner):
        """Test JSON output format."""
        result = runner.invoke(cli, ["--output", "json", "settings"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, dict)

    def test_output_format_text(self, runner):
        """Test text output format."""
        result = runner.invoke(cli, ["--output", "text", "settings"])
        assert result.exit_code == 0

    def test_invalid_output_format(self, runner):
        """Test invalid output format."""
        result = runner.invoke(cli, ["--output", "invalid", "settings"])
        assert result.exit_code != 0


class TestCLIErrorHandling:
    """Test CLI error handling."""

    def test_cli_without_arguments(self, runner):
        """Test CLI without arguments shows help."""
        result = runner.invoke(cli, [])
        # Click expects a command, so exit code 2 is correct for missing command
        assert result.exit_code == 2
        assert "Usage:" in result.output

    def test_invalid_command(self, runner):
        """Test invalid command shows error."""
        result = runner.invoke(cli, ["invalid-command"])
        assert result.exit_code != 0
        assert "No such command" in result.output


def test_ocr_command_group_removed():
    """Test that the OCR command group has been removed from the CLI."""
    from click.testing import CliRunner

    from wyrdcraeft.cli.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["ocr", "--help"])
    assert result.exit_code != 0
    assert "ocr" not in cli.commands


def test_settings_has_no_ocr_fields():
    """Test that Settings has no ocr_ fields."""
    from wyrdcraeft.settings import Settings

    field_names = Settings.model_fields.keys()
    ocr_fields = [name for name in field_names if name.startswith("ocr_")]
    assert ocr_fields == []
