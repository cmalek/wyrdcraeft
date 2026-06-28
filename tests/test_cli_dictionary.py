"""CLI smoke tests for Bosworth-Toller dictionary commands."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from wyrdcraeft.cli.cli import cli
from wyrdcraeft.paths import DICTIONARY_INDEX_FILENAME, MORPHOLOGY_INDEX_FILENAME

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
    assert "lookup" in result.output


def test_dictionary_lookup_help(runner) -> None:
    result = runner.invoke(cli, ["dictionary", "lookup", "--help"])
    assert result.exit_code == 0
    assert "--pos" in result.output
    assert "--index-db" in result.output
    assert "--index-dir" in result.output
    assert "--standalone" in result.output
    assert "--json-output" in result.output


def test_dictionary_lookup_smoke(runner, temp_dir) -> None:
    index_db = temp_dir / DICTIONARY_INDEX_FILENAME
    index_result = runner.invoke(
        cli,
        [
            "dictionary",
            "index-bt",
            "--source",
            str(_SAMPLE_LINES),
            "--standalone",
            "--index-db",
            str(index_db),
        ],
    )
    assert index_result.exit_code == 0, index_result.output

    lookup_result = runner.invoke(
        cli,
        [
            "dictionary",
            "lookup",
            "abbod",
            "--standalone",
            "--index-db",
            str(index_db),
        ],
    )
    assert lookup_result.exit_code == 0, lookup_result.output
    assert "Lemma:" in lookup_result.output
    assert "POS: noun" in lookup_result.output
    assert "Senses:" in lookup_result.output
    assert "Variants:" in lookup_result.output


def test_dictionary_lookup_json_output(runner, temp_dir) -> None:
    index_db = temp_dir / DICTIONARY_INDEX_FILENAME
    runner.invoke(
        cli,
        [
            "dictionary",
            "index-bt",
            "--source",
            str(_SAMPLE_LINES),
            "--standalone",
            "--index-db",
            str(index_db),
        ],
    )

    lookup_result = runner.invoke(
        cli,
        [
            "dictionary",
            "lookup",
            "abbod",
            "--standalone",
            "--index-db",
            str(index_db),
            "--json-output",
        ],
    )
    assert lookup_result.exit_code == 0, lookup_result.output
    payload = json.loads(lookup_result.output)
    assert payload[0]["norm_key"] == "abbad"
    assert payload[0]["pos"] == "noun"


def test_dictionary_index_bt_help(runner) -> None:
    result = runner.invoke(cli, ["dictionary", "index-bt", "--help"])
    assert result.exit_code == 0
    assert "--source" in result.output
    assert "--index-db" in result.output
    assert "--index-dir" in result.output
    assert "--standalone" in result.output
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
            "--standalone",
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


def test_dictionary_lookup_morphology_default(runner, temp_dir) -> None:
    morphology_db = temp_dir / MORPHOLOGY_INDEX_FILENAME
    sqlite3.connect(morphology_db).close()
    runner.invoke(
        cli,
        [
            "dictionary",
            "index-bt",
            "--source",
            str(_SAMPLE_LINES),
            "--index-db",
            str(morphology_db),
        ],
    )

    lookup_result = runner.invoke(
        cli,
        [
            "dictionary",
            "lookup",
            "abbod",
            "--index-db",
            str(morphology_db),
        ],
    )
    assert lookup_result.exit_code == 0, lookup_result.output
    assert "Lemma:" in lookup_result.output


def test_dictionary_lookup_missing_morphology_db_fails(runner, temp_dir) -> None:
    morphology_db = temp_dir / "missing.sqlite3"
    assert not morphology_db.exists()

    result = runner.invoke(
        cli,
        [
            "dictionary",
            "lookup",
            "abbod",
            "--index-db",
            str(morphology_db),
        ],
    )

    assert result.exit_code != 0
    assert "Morphology index not found" in result.output
