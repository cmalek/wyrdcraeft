"""
Tests for the main module.
"""

from __future__ import annotations

from unittest.mock import patch

from oe_json_extractor.main import main


class TestMain:
    """Test the main function."""

    @patch("oe_json_extractor.main.cli")
    def test_main_calls_cli(self, mock_cli):
        """Test that main function calls the CLI."""
        main()
        mock_cli.assert_called_once()

    @patch("oe_json_extractor.main.cli")
    def test_main_importable(self, mock_cli):
        """Test that main function can be imported and called."""
        # This test ensures the module can be imported without errors

        main()
        mock_cli.assert_called_once()

    @patch("oe_json_extractor.main.cli")
    def test_main_function_exists(self, mock_cli):
        """Test that main function exists and is callable."""
        assert callable(main)
        main()
        mock_cli.assert_called_once()
