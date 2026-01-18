"""
Test configuration and fixtures for the ai-coding project.

This file contains shared fixtures and configuration that can be used across
all test files in the project.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest
from click.testing import CliRunner
from rich.console import Console


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_console():
    """Create a mock console for testing."""
    return Mock(spec=Console)


@pytest.fixture
def mock_settings():
    """Create a mock settings object for testing."""
    mock = Mock()
    mock.model_dump.return_value = {
        "app_name": "oe_json_extractor",
        "app_version": "0.1.0",
        "default_output_format": "table",
        "enable_colors": True,
        "quiet_mode": False,
        "log_level": "INFO",
        "log_file": None,
    }
    return mock


@pytest.fixture
def cli_context(mock_settings, mock_console):
    """Create a mock CLI context for testing."""
    return {
        "settings": mock_settings,
        "utils": Mock(),
        "console": mock_console,
        "output": "table",
    }
