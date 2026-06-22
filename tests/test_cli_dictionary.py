"""CLI smoke tests for Bosworth-Toller dictionary commands."""

from __future__ import annotations

from pathlib import Path

from wyrdcraeft.cli.cli import cli
from wyrdcraeft.paths import DICTIONARY_INDEX_FILENAME

_SAMPLE_LINES = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "dictionary"
    / "sample_lines.txt"
)


def test_dictionary_group_help(runner) -> None:
    result = runner.invoke(cli, ["dictionary", "--help"])
    assert result.exit_code == 0
    assert "index-bt" in result.output


def test_dictionary_index_bt_help(runner) -> None:
    result = runner.invoke(cli, ["dictionary", "index-bt", "--help"])
    assert result.exit_code == 0
    assert "--source" in result.output
    assert "--index-db" in result.output
    assert "--index-dir" in result.output
    assert "--attach-morphology-db" in result.output
    assert "--report" in result.output


def test_dictionary_index_bt_smoke(runner, temp_dir) -> None:
    report_path = temp_dir / "report.json"
    index_db = temp_dir / DICTIONARY_INDEX_FILENAME
    result = runner.invoke(
        cli,
        [
            "dictionary",
            "index-bt",
            "--source",
            str(_SAMPLE_LINES),
            "--index-db",
            str(index_db),
            "--report",
            str(report_path),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Dictionary index complete." in result.output
    assert f"index_db={index_db.resolve()}" in result.output
    assert index_db.is_file()
    assert report_path.is_file()
    assert '"pos_counts"' in report_path.read_text(encoding="utf-8")
