from __future__ import annotations

import os
from io import StringIO
from pathlib import Path

from rich.console import Console

from wyrdcraeft.cli.cli import cli
from wyrdcraeft.paths import MORPHOLOGY_INDEX_FILENAME
from wyrdcraeft.services.morphology.progress import (
    MorphologyGenerateProgressCoordinator,
    MorphologySetupStep,
    MorphologyStage,
    MorphologyStageCounts,
    MorphologyStageSnapshot,
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


def _isolated_generate_args(temp_dir: Path) -> list[str]:
    return [
        "--data-dir",
        str(_morphology_data_dir()),
        "--dictionary",
        str(_subset_dictionary()),
        "--index-dir",
        str(temp_dir),
    ]


def _index_db_path(temp_dir: Path) -> Path:
    return temp_dir / MORPHOLOGY_INDEX_FILENAME


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
    assert "--index-dir" in result.output
    assert "--progress-every INTEGER" in result.output


def test_morphology_generate_limit(runner, temp_dir) -> None:
    output_file = temp_dir / "morph.tsv"
    index_db = _index_db_path(temp_dir)
    result = runner.invoke(
        cli,
        [
            "morphology",
            "generate",
            "--limit",
            "50",
            *_isolated_generate_args(temp_dir),
            "--output",
            str(output_file),
        ],
    )
    assert result.exit_code == 0
    assert output_file.exists()
    assert index_db.exists()
    assert f"index_db={index_db.resolve()}" in result.output
    assert "forms_written=" in result.output
    assert "Morphology generation complete." in result.output
    assert "verbs" in result.stderr


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
            "--index-dir",
            str(temp_dir),
            "--output",
            str(output_file),
        ],
    )
    assert result.exit_code == 0
    assert output_file.exists()
    assert "full_mode=True" in result.output


def test_morphology_generate_quiet_suppresses_progress(runner, temp_dir) -> None:
    output_file = temp_dir / "morph.tsv"
    result = runner.invoke(
        cli,
        [
            "--quiet",
            "morphology",
            "generate",
            "--limit",
            "20",
            *_isolated_generate_args(temp_dir),
            "--output",
            str(output_file),
        ],
    )
    assert result.exit_code == 0
    assert result.stderr == ""


def test_morphology_generate_rejects_non_positive_progress_every(
    runner,
    temp_dir,
) -> None:
    output_file = temp_dir / "morph.tsv"
    result = runner.invoke(
        cli,
        [
            "morphology",
            "generate",
            "--limit",
            "20",
            "--progress-every",
            "0",
            *_isolated_generate_args(temp_dir),
            "--output",
            str(output_file),
        ],
    )
    assert result.exit_code != 0
    assert "positive" in result.output.lower()


def test_morphology_generate_progress_stays_on_stderr(runner, temp_dir) -> None:
    output_file = temp_dir / "morph.tsv"
    result = runner.invoke(
        cli,
        [
            "morphology",
            "generate",
            "--limit",
            "20",
            *_isolated_generate_args(temp_dir),
            "--output",
            str(output_file),
        ],
    )
    assert result.exit_code == 0
    assert "Morphology generation complete." in result.output
    assert "forms_written=" in result.output
    assert "Morphology generation complete." not in result.stderr
    assert "setup" in result.stderr
    assert "load data" in result.stderr
    assert "assign noun paradigms" in result.stderr
    assert "verbs" in result.stderr


def test_morphology_generate_progress_shows_wright_when_present(
    runner,
    temp_dir,
) -> None:
    output_file = temp_dir / "morph.tsv"
    result = runner.invoke(
        cli,
        [
            "morphology",
            "generate",
            "--limit",
            "20",
            "--progress-every",
            "1",
            *_isolated_generate_args(temp_dir),
            "--output",
            str(output_file),
        ],
    )
    assert result.exit_code == 0
    assert "wright=" in result.stderr


def test_progress_coordinator_omits_empty_wright_and_throttles_lemma() -> None:
    stream = StringIO()
    console = Console(file=stream, force_terminal=False, color_system=None)
    progress = MorphologyGenerateProgressCoordinator(
        console=console,
        progress_every_words=5,
    )

    progress.start()
    progress.start_stage(MorphologyStage.ADJECTIVES, total=7)
    progress.advance(
        MorphologyStage.ADJECTIVES,
        lemma="word-1",
        wright="",
        forms_written=3,
    )
    assert progress._visible_lemmas[MorphologyStage.ADJECTIVES] == "word-1"
    progress.advance(
        MorphologyStage.ADJECTIVES,
        lemma="word-2",
        wright="",
        forms_written=4,
    )
    assert progress._visible_lemmas[MorphologyStage.ADJECTIVES] == "word-1"
    progress.advance(
        MorphologyStage.ADJECTIVES,
        lemma="word-3",
        wright="",
        forms_written=5,
    )
    progress.advance(
        MorphologyStage.ADJECTIVES,
        lemma="word-4",
        wright="",
        forms_written=7,
    )
    assert progress._visible_lemmas[MorphologyStage.ADJECTIVES] == "word-1"
    progress.advance(
        MorphologyStage.ADJECTIVES,
        lemma="word-5",
        wright="",
        forms_written=9,
    )
    assert progress._visible_lemmas[MorphologyStage.ADJECTIVES] == "word-5"
    progress.advance(
        MorphologyStage.ADJECTIVES,
        lemma="word-6",
        wright="",
        forms_written=11,
    )
    progress.advance(
        MorphologyStage.ADJECTIVES,
        lemma="word-7",
        wright="",
        forms_written=12,
    )
    assert progress._visible_lemmas[MorphologyStage.ADJECTIVES] == "word-7"
    progress.finish_stage(MorphologyStage.ADJECTIVES)
    progress.stop()

    description = progress._build_description(
        stage=MorphologyStage.ADJECTIVES,
        snapshot=MorphologyStageSnapshot(
            completed=7,
            total=7,
            lemma="word-7",
            wright="",
            forms_written=12,
        ),
    )
    assert "wright=" not in description


def test_progress_coordinator_stage_totals() -> None:
    progress = MorphologyGenerateProgressCoordinator(progress_every_words=5)

    totals = progress.compute_stage_totals_from_counts(
        MorphologyStageCounts(
            manual_forms=3,
            verbs=4,
            adjectives=5,
            adverbs=6,
            numerals=7,
            nouns=8,
        )
    )

    assert totals == {
        MorphologyStage.MANUAL: 3,
        MorphologyStage.VERBS: 4,
        MorphologyStage.ADJECTIVES: 5,
        MorphologyStage.ADVERBS: 6,
        MorphologyStage.NUMERALS: 7,
        MorphologyStage.NOUNS: 8,
    }


def test_progress_coordinator_setup_descriptions() -> None:
    progress = MorphologyGenerateProgressCoordinator(progress_every_words=5)

    description = progress._build_setup_description(
        step=MorphologySetupStep.COUNT_SYLLABLES,
    )

    assert description == "setup | count syllables"


def test_morphology_query_by_form(runner, temp_dir) -> None:
    output_file = temp_dir / "morph_query.tsv"
    index_db = _index_db_path(temp_dir)

    generate_result = runner.invoke(
        cli,
        [
            "morphology",
            "generate",
            "--limit",
            "50",
            *_isolated_generate_args(temp_dir),
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


def test_morphology_generate_default_index_uses_app_data_dir(
    runner,
    temp_dir,
) -> None:
    app_data_dir = temp_dir / "app-data"
    output_file = temp_dir / "morph.tsv"
    index_db = app_data_dir / MORPHOLOGY_INDEX_FILENAME
    os.environ["WYRDCRAEFT_APP_DATA_DIR"] = str(app_data_dir)
    try:
        result = runner.invoke(
            cli,
            [
                "morphology",
                "generate",
                "--limit",
                "20",
                "--data-dir",
                str(_morphology_data_dir()),
                "--dictionary",
                str(_subset_dictionary()),
                "--output",
                str(output_file),
            ],
        )
    finally:
        del os.environ["WYRDCRAEFT_APP_DATA_DIR"]

    assert result.exit_code == 0
    assert index_db.exists()
    assert f"index_db={index_db.resolve()}" in result.output


def test_morphology_generate_index_dir_writes_morphology_sqlite3(
    runner,
    temp_dir,
) -> None:
    index_dir = temp_dir / "custom-index"
    output_file = temp_dir / "morph.tsv"
    index_db = index_dir / MORPHOLOGY_INDEX_FILENAME
    result = runner.invoke(
        cli,
        [
            "morphology",
            "generate",
            "--limit",
            "20",
            "--data-dir",
            str(_morphology_data_dir()),
            "--dictionary",
            str(_subset_dictionary()),
            "--index-dir",
            str(index_dir),
            "--output",
            str(output_file),
        ],
    )
    assert result.exit_code == 0
    assert index_db.exists()
    assert f"index_db={index_db.resolve()}" in result.output


def test_morphology_generate_rejects_index_db_and_index_dir(
    runner,
    temp_dir,
) -> None:
    output_file = temp_dir / "morph.tsv"
    result = runner.invoke(
        cli,
        [
            "morphology",
            "generate",
            "--limit",
            "20",
            *_isolated_generate_args(temp_dir),
            "--index-db",
            str(temp_dir / "custom.sqlite3"),
            "--output",
            str(output_file),
        ],
    )
    assert result.exit_code != 0
    assert "at most one" in result.output.lower()


def test_morphology_generate_reference_snapshots_help(runner) -> None:
    result = runner.invoke(
        cli,
        ["morphology", "generate-reference-snapshots", "--help"],
    )
    assert result.exit_code == 0
    assert "--include-full" in result.output
