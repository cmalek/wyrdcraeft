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
    assert "generate-reference-snapshots" in result.output


def test_morphology_generate_help(runner) -> None:
    result = runner.invoke(cli, ["morphology", "generate", "--help"])
    assert result.exit_code == 0
    assert "--full / --no-full" in result.output
    assert "--data-dir" in result.output


def test_morphology_generate_limit(runner, temp_dir) -> None:
    output_file = temp_dir / "morph.tsv"
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


def test_morphology_generate_reference_snapshots_help(runner) -> None:
    result = runner.invoke(
        cli,
        ["morphology", "generate-reference-snapshots", "--help"],
    )
    assert result.exit_code == 0
    assert "--include-full" in result.output
