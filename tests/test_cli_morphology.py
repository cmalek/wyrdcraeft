from __future__ import annotations

from pathlib import Path

from wyrdcraeft.cli.cli import cli


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


def test_morphology_group_help(runner) -> None:
    result = runner.invoke(cli, ["morphology", "--help"])
    assert result.exit_code == 0
    assert "generate" in result.output
    assert "query" in result.output
    assert "generate-reference-snapshots" in result.output


def test_morphology_generate_help(runner) -> None:
    result = runner.invoke(cli, ["morphology", "generate", "--help"])
    assert result.exit_code == 0
    assert "--full / --no-full" in result.output
    assert "--data-dir" in result.output


def test_morphology_generate_limit(runner, temp_dir) -> None:
    output_file = temp_dir / "morph.tsv"
    index_db = output_file.with_suffix(".sqlite3")
    result = runner.invoke(
        cli,
        [
            "morphology",
            "generate",
            "--limit",
            "50",
            "--data-dir",
            str(_morphology_data_dir()),
            "--dictionary",
            str(_subset_dictionary()),
            "--output",
            str(output_file),
        ],
    )
    assert result.exit_code == 0
    assert output_file.exists()
    assert index_db.exists()
    assert f"index_db={index_db}" in result.output
    assert "forms_written=" in result.output


def test_morphology_generate_full_with_subset_inputs(runner, temp_dir) -> None:
    output_file = temp_dir / "morph_full.tsv"
    data_dir = _morphology_data_dir()
    result = runner.invoke(
        cli,
        [
            "morphology",
            "generate",
            "--full",
            "--dictionary",
            str(_subset_dictionary()),
            "--manual-forms",
            str(data_dir / "manual_forms.txt"),
            "--verbal-paradigms",
            str(data_dir / "para_vb.txt"),
            "--prefixes",
            str(data_dir / "prefixes.txt"),
            "--output",
            str(output_file),
        ],
    )
    assert result.exit_code == 0
    assert output_file.exists()
    assert "full_mode=True" in result.output


def test_morphology_query_by_form(runner, temp_dir) -> None:
    output_file = temp_dir / "morph_query.tsv"
    index_db = output_file.with_suffix(".sqlite3")

    generate_result = runner.invoke(
        cli,
        [
            "morphology",
            "generate",
            "--limit",
            "50",
            "--data-dir",
            str(_morphology_data_dir()),
            "--dictionary",
            str(_subset_dictionary()),
            "--output",
            str(output_file),
        ],
    )
    assert generate_result.exit_code == 0
    assert output_file.exists()
    assert index_db.exists()

    first_row = output_file.read_text(encoding="utf-8").splitlines()[0].split("\t")
    form_value = first_row[5]
    query_result = runner.invoke(
        cli,
        [
            "morphology",
            "query",
            "--db",
            str(index_db),
            "--form",
            form_value,
            "--limit",
            "5",
        ],
    )
    assert query_result.exit_code == 0
    assert query_result.output.strip()


def test_morphology_generate_reference_snapshots_help(runner) -> None:
    result = runner.invoke(
        cli,
        ["morphology", "generate-reference-snapshots", "--help"],
    )
    assert result.exit_code == 0
    assert "--include-full" in result.output
