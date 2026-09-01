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

from wyrdcraeft.paths import CANONICAL_DB_FILENAME


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
def isolated_morphology_app_data(tmp_path, monkeypatch) -> Path:
    """
    Relocate the canonical SQLite database to a temporary app-data directory.

    Side Effects:
        Sets ``WYRDCRAEFT_APP_DATA_DIR`` for the duration of the test.

    Returns:
        Directory that will contain ``wyrdcraeft.sqlite3`` when generate runs
        without ``--index-dir`` or ``--index-db``.

    """
    app_data_dir = tmp_path / "wyrdcraeft-app-data"
    monkeypatch.setenv("WYRDCRAEFT_APP_DATA_DIR", str(app_data_dir))
    return app_data_dir


@pytest.fixture
def isolated_morphology_index_db(isolated_morphology_app_data: Path) -> Path:
    """
    Expected canonical SQLite path under ``isolated_morphology_app_data``.

    Returns:
        Path to ``wyrdcraeft.sqlite3`` inside the isolated app-data directory.

    """
    return isolated_morphology_app_data / CANONICAL_DB_FILENAME


@pytest.fixture
def lexicon_source_db(tmp_path: Path) -> Path:
    """
    Morphology SQLite seeded with both ``forms`` and attached ``bt_*`` tables.

    Returns:
        Path to a source database ready for lexicon CLI and rebuild tests.

    """
    from tests.lexicon.source_db import make_lexicon_source_db

    return make_lexicon_source_db(tmp_path / "lexicon-source.sqlite3")


@pytest.fixture
def mock_console():
    """Create a mock console for testing."""
    return Mock(spec=Console)


@pytest.fixture
def mock_settings():
    """Create a mock settings object for testing."""
    mock = Mock()
    mock.model_dump.return_value = {
        "app_name": "wyrdcraeft",
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

