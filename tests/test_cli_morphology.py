"""CLI tests for remaining morphology commands after build moved to dictionary."""

from __future__ import annotations

from io import StringIO

from rich.console import Console

from wyrdcraeft.cli.cli import cli
from wyrdcraeft.services.morphology.progress import (
    MorphologyGenerateProgressCoordinator,
    MorphologySetupStep,
    MorphologyStage,
    MorphologyStageCounts,
    MorphologyStageSnapshot,
)


def test_morphology_group_help(runner) -> None:
    result = runner.invoke(cli, ["morphology", "--help"])
    assert result.exit_code == 0
    assert "audit-wright" not in result.output
    assert "build" not in result.output
    assert "query" in result.output
    assert "generate-reference-snapshots" not in result.output
    assert "ingest-wright-text" not in result.output


def test_morphology_wright_commands_moved_to_dictionary(runner) -> None:
    ingest = runner.invoke(cli, ["morphology", "ingest-wright-text", "--help"])
    assert ingest.exit_code != 0
    assert "No such command 'ingest-wright-text'" in ingest.output

    audit = runner.invoke(cli, ["morphology", "audit-wright", "--help"])
    assert audit.exit_code != 0
    assert "No such command 'audit-wright'" in audit.output


def test_morphology_build_command_moved_to_dictionary(runner) -> None:
    result = runner.invoke(cli, ["morphology", "build", "--help"])
    assert result.exit_code != 0
    assert "No such command 'build'" in result.output


def test_morphology_generate_command_is_gone(runner) -> None:
    result = runner.invoke(cli, ["morphology", "generate", "--help"])
    assert result.exit_code != 0
    assert "No such command 'generate'" in result.output


def test_morphology_query_help(runner) -> None:
    result = runner.invoke(cli, ["morphology", "query", "--help"])
    assert result.exit_code == 0
    assert "--db" in result.output
    assert "--lemma" in result.output
    assert "--form" in result.output


def test_morphology_query_requires_exactly_one_lookup_mode(runner, tmp_path) -> None:
    db_path = tmp_path / "placeholder.sqlite3"
    db_path.write_text("", encoding="utf-8")
    result = runner.invoke(
        cli,
        ["morphology", "query", "--db", str(db_path), "--lemma", "foo", "--form", "bar"],
    )
    assert result.exit_code != 0
    assert "Provide exactly one of --lemma or --form." in result.output


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
