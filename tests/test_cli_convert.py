from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from wyrdcraeft.cli.cli import cli
from wyrdcraeft.models import OldEnglishText, TextMetadata, Section


def test_convert_command_no_llm(runner, temp_dir):
    """Test the convert command without LLM (heuristic mode)."""
    source_file = temp_dir / "test.txt"
    source_file.write_text("þæt wæs god cyning.", encoding="utf-8")
    output_file = temp_dir / "output.json"

    # Use a real file and run with --no-use-llm
    result = runner.invoke(
        cli, ["convert", str(source_file), str(output_file), "--no-use-llm"]
    )

    assert result.exit_code == 0
    assert output_file.exists()

    # Verify the output is valid JSON and contains expected content
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert "metadata" in data
    assert "content" in data
    assert data["metadata"]["title"] == "test"


@patch("wyrdcraeft.cli.cli.DocumentIngestor.ingest")
def test_convert_command_llm_flags(mock_ingest, runner, temp_dir):
    """Test that LLM flags are correctly passed to the pipeline."""
    source_file = temp_dir / "test.txt"
    source_file.write_text("Some text", encoding="utf-8")
    output_file = temp_dir / "output.json"

    # Mock return value for ingest
    mock_doc = MagicMock(spec=OldEnglishText)
    mock_doc.model_dump_json.return_value = '{"test": "json"}'
    mock_ingest.return_value = mock_doc

    result = runner.invoke(
        cli,
        [
            "convert",
            str(source_file),
            str(output_file),
            "--llm-model",
            "gpt-4o",
            "--llm-temperature",
            "0.5",
            "--llm-max-tokens",
            "1000",
            "--llm-timeout",
            "60",
            "--title",
            "Custom Title",
        ],
    )

    assert result.exit_code == 0

    # Check if ingest was called with correct parameters
    args, kwargs = mock_ingest.call_args
    assert kwargs["use_llm"] is True
    assert kwargs["llm_config"].model_id == "gpt-4o"
    # Note: provider is derived from model_id in the settings or LLM config logic
    assert kwargs["llm_config"].temperature == 0.5
    assert kwargs["llm_config"].max_tokens == 1000
    assert kwargs["llm_config"].timeout_s == 60
    assert kwargs["metadata"].title == "Custom Title"

    assert output_file.exists()
    assert output_file.read_text(encoding="utf-8") == '{"test": "json"}'


def test_convert_command_missing_source(runner, temp_dir):
    """Test the convert command with a missing source file."""
    output_file = temp_dir / "output.json"
    result = runner.invoke(cli, ["convert", "non_existent.txt", str(output_file)])
    assert result.exit_code != 0
    # The error message depends on whether it's caught by click or our try-except
    # Currently it seems to be caught by our try-except and printed via print_error
    # We'll check for the filename in the output
    assert "non_existent.txt" in result.output or "non_existent.txt" in result.stderr
