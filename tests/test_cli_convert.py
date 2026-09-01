from __future__ import annotations

import json

from wyrdcraeft.cli.cli import cli


def test_convert_command_no_llm(runner, temp_dir):
    """Test the convert command without LLM (heuristic mode)."""
    source_file = temp_dir / "test.txt"
    source_file.write_text("þæt wæs god cyning.", encoding="utf-8")
    output_file = temp_dir / "output.json"

    result = runner.invoke(cli, ["source", "convert", str(source_file), str(output_file)])

    assert result.exit_code == 0
    assert output_file.exists()

    # Verify the output is valid JSON and contains expected content
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert "metadata" in data
    assert "content" in data
    assert data["metadata"]["title"] == "test"


def test_convert_rejects_use_llm_flag(runner, temp_dir):
    source_file = temp_dir / "test.txt"
    source_file.write_text("þæt wæs god cyning.", encoding="utf-8")
    output_file = temp_dir / "output.json"
    result = runner.invoke(
        cli,
        ["source", "convert", str(source_file), str(output_file), "--use-llm"],
    )
    assert result.exit_code != 0


def test_convert_rejects_http_source(runner, temp_dir):
    output_file = temp_dir / "output.json"
    result = runner.invoke(
        cli,
        ["source", "convert", "https://example.com/a.txt", str(output_file)],
    )
    assert result.exit_code != 0


def test_convert_command_missing_source(runner, temp_dir):
    """Test the convert command with a missing source file."""
    output_file = temp_dir / "output.json"
    result = runner.invoke(
        cli, ["source", "convert", "non_existent.txt", str(output_file)]
    )
    assert result.exit_code != 0
    # The error message depends on whether it's caught by click or our try-except
    # Currently it seems to be caught by our try-except and printed via print_error
    # We'll check for the filename in the output
    assert "non_existent.txt" in result.output or "non_existent.txt" in result.stderr
