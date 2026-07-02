"""CLI smoke tests for Bosworth-Toller dictionary commands."""

from __future__ import annotations

import json
from pathlib import Path

from wyrdcraeft.cli.cli import cli

_SAMPLE_LINES = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "dictionary"
    / "sample_lines.txt"
)


def _morphology_data_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "wyrdcraeft" / "etc" / "morphology"


def _subset_dictionary() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "tests"
        / "fixtures"
        / "morphology"
        / "test_dict.txt"
    )


def _build_morphology_source_db(runner, target_db: Path) -> None:
    target_db.parent.mkdir(parents=True, exist_ok=True)
    result = runner.invoke(
        cli,
        [
            "morphology",
            "build",
            "--limit",
            "50",
            "--data-dir",
            str(_morphology_data_dir()),
            "--dictionary",
            str(_subset_dictionary()),
            "--output",
            str(target_db.parent / "morphology.tsv"),
        ],
    )
    assert result.exit_code == 0, result.output


def test_dictionary_group_help(runner) -> None:
    result = runner.invoke(cli, ["dictionary", "--help"])
    assert result.exit_code == 0
    assert "build" in result.output
    assert "lookup" in result.output


def test_dictionary_lookup_help(runner) -> None:
    result = runner.invoke(cli, ["dictionary", "lookup", "--help"])
    assert result.exit_code == 0
    assert "--pos" in result.output
    assert "--index-db" not in result.output
    assert "--index-dir" not in result.output
    assert "--standalone" not in result.output
    assert "--json-output" in result.output


def test_dictionary_index_bt_command_is_gone(runner) -> None:
    result = runner.invoke(cli, ["dictionary", "index-bt", "--help"])
    assert result.exit_code != 0
    assert "No such command 'index-bt'" in result.output


def test_dictionary_lookup_smoke(
    runner,
    isolated_morphology_index_db: Path,
) -> None:
    _build_morphology_source_db(runner, isolated_morphology_index_db)
    index_result = runner.invoke(
        cli,
        [
            "dictionary",
            "build",
            "--source",
            str(_SAMPLE_LINES),
        ],
    )
    assert index_result.exit_code == 0, index_result.output
    assert isolated_morphology_index_db.exists()

    lookup_result = runner.invoke(
        cli,
        [
            "dictionary",
            "lookup",
            "abbad",
        ],
    )
    assert lookup_result.exit_code == 0, lookup_result.output
    assert "No dictionary entries found" not in lookup_result.output
    assert "Lemma:" in lookup_result.output
    assert "POS: noun" in lookup_result.output
    assert "Senses:" in lookup_result.output
    assert "Variants:" in lookup_result.output


def test_dictionary_lookup_json_output(
    runner,
    isolated_morphology_index_db: Path,
) -> None:
    _build_morphology_source_db(runner, isolated_morphology_index_db)
    build_result = runner.invoke(
        cli,
        [
            "dictionary",
            "build",
            "--source",
            str(_SAMPLE_LINES),
        ],
    )
    assert build_result.exit_code == 0, build_result.output
    assert isolated_morphology_index_db.exists()

    lookup_result = runner.invoke(
        cli,
        [
            "dictionary",
            "lookup",
            "abbod",
            "--json-output",
        ],
    )
    assert lookup_result.exit_code == 0, lookup_result.output
    json_start = next(
        index for index, line in enumerate(lookup_result.output.splitlines()) if line.startswith("[")
    )
    payload = json.loads("\n".join(lookup_result.output.splitlines()[json_start:]))
    assert payload[0]["norm_key"] == "abbad"
    assert payload[0]["pos"] == "noun"


def test_dictionary_build_help(runner) -> None:
    result = runner.invoke(cli, ["dictionary", "build", "--help"])
    assert result.exit_code == 0
    assert "--source" in result.output
    assert "--index-db" not in result.output
    assert "--index-dir" not in result.output
    assert "--standalone" not in result.output
    assert "--report" in result.output


def test_dictionary_build_smoke(
    runner,
    isolated_morphology_index_db: Path,
    temp_dir,
) -> None:
    _build_morphology_source_db(runner, isolated_morphology_index_db)
    report_path = temp_dir / "report.json"
    result = runner.invoke(
        cli,
        [
            "dictionary",
            "build",
            "--source",
            str(_SAMPLE_LINES),
            "--report",
            str(report_path),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Dictionary index complete." in result.output
    assert f"index_db={isolated_morphology_index_db.resolve()}" in result.output
    assert isolated_morphology_index_db.is_file()
    assert report_path.is_file()
    assert '"pos_counts"' in report_path.read_text(encoding="utf-8")


def test_dictionary_lookup_morphology_default(
    runner,
    isolated_morphology_index_db: Path,
) -> None:
    _build_morphology_source_db(runner, isolated_morphology_index_db)
    build_result = runner.invoke(
        cli,
        [
            "dictionary",
            "build",
            "--source",
            str(_SAMPLE_LINES),
        ],
    )
    assert build_result.exit_code == 0, build_result.output
    assert isolated_morphology_index_db.exists()

    lookup_result = runner.invoke(
        cli,
        [
            "dictionary",
            "lookup",
            "abbod",
        ],
    )
    assert lookup_result.exit_code == 0, lookup_result.output
    assert "No dictionary entries found" not in lookup_result.output
    assert "Lemma:" in lookup_result.output
    assert "POS:" in lookup_result.output


def test_dictionary_lookup_missing_morphology_db_fails(
    runner,
    isolated_morphology_app_data: Path,
) -> None:
    assert not (isolated_morphology_app_data / "wyrdcraeft.sqlite3").exists()

    result = runner.invoke(
        cli,
        [
            "dictionary",
            "lookup",
            "abbod",
        ],
    )

    assert result.exit_code != 0
    assert "missing required source tables: bt_entries, bt_senses, bt_variants" in result.output
    assert "wyrdcraeft dictionary build" in result.output
    assert "wyrdcraeft morphology build" in result.output
