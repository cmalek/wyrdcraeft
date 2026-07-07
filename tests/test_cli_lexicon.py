"""CLI tests for lexicon commands after build moved to dictionary."""

from __future__ import annotations

from wyrdcraeft.cli.cli import cli


def test_lexicon_group_help(runner) -> None:
    result = runner.invoke(cli, ["lexicon", "--help"])
    assert result.exit_code == 0
    assert "build" not in result.output
    assert "browse" in result.output


def test_lexicon_build_command_moved_to_dictionary(runner) -> None:
    result = runner.invoke(cli, ["lexicon", "build", "--help"])
    assert result.exit_code != 0
    assert "No such command 'build'" in result.output


def test_lexicon_browse_help(runner) -> None:
    result = runner.invoke(cli, ["lexicon", "browse", "--help"])
    assert result.exit_code == 0
    assert "--index-db" not in result.output
    assert "--index-dir" not in result.output
