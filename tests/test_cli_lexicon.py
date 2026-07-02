"""CLI smoke tests for lexicon browse workflow commands."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace

from wyrdcraeft.cli import lexicon as lexicon_module
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


def _build_canonical_source_db(runner, target_db: Path) -> None:
    target_db.parent.mkdir(parents=True, exist_ok=True)
    morphology_result = runner.invoke(
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
    assert morphology_result.exit_code == 0, morphology_result.output

    dictionary_result = runner.invoke(
        cli,
        [
            "dictionary",
            "build",
            "--source",
            str(_SAMPLE_LINES),
        ],
    )
    assert dictionary_result.exit_code == 0, dictionary_result.output


def test_lexicon_group_help(runner) -> None:
    result = runner.invoke(cli, ["lexicon", "--help"])
    assert result.exit_code == 0
    assert "build" in result.output


def test_lexicon_build_help(runner) -> None:
    result = runner.invoke(cli, ["lexicon", "build", "--help"])
    assert result.exit_code == 0
    assert "--index-db" not in result.output
    assert "--index-dir" not in result.output
    assert "--no-tui" in result.output
    assert "--quiet" in result.output
    assert "--force" in result.output
    assert "--no-progress" not in result.output


def test_lexicon_build_smoke(
    runner,
    isolated_morphology_index_db: Path,
) -> None:
    _build_canonical_source_db(runner, isolated_morphology_index_db)
    result = runner.invoke(
        cli,
        [
            "lexicon",
            "build",
            "--no-tui",
            "--force",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Lexicon build complete." in result.output
    assert f"index_db={isolated_morphology_index_db.resolve()}" in result.output
    assert "built_at=" in result.output
    assert "forms_source_count=" in result.output
    assert "bt_entries_source_count=" in result.output
    assert "entries_written=" in result.output
    assert "forms_written=" in result.output
    assert "search_keys_written=" in result.output

    with sqlite3.connect(isolated_morphology_index_db) as connection:
        assert connection.execute("SELECT COUNT(*) FROM lexicon_entries").fetchone()[0] > 0
        assert connection.execute("SELECT COUNT(*) FROM lexicon_forms").fetchone()[0] > 0
        assert (
            connection.execute("SELECT COUNT(*) FROM lexicon_search_keys").fetchone()[0]
            > 0
        )
    assert "[info] stage started:" in result.stderr


def test_lexicon_build_quiet_smoke(
    runner,
    isolated_morphology_index_db: Path,
) -> None:
    _build_canonical_source_db(runner, isolated_morphology_index_db)
    result = runner.invoke(
        cli,
        [
            "lexicon",
            "build",
            "--no-tui",
            "--quiet",
            "--force",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Lexicon build complete." in result.output
    assert "[info] stage started:" not in result.stderr


def test_lexicon_build_uses_tui_on_tty(
    runner,
    isolated_morphology_index_db: Path,
    monkeypatch,
) -> None:
    called: list[bool] = []
    _build_canonical_source_db(runner, isolated_morphology_index_db)

    monkeypatch.setattr(
        lexicon_module,
        "sys",
        SimpleNamespace(
            stdout=SimpleNamespace(isatty=lambda: True),
            stderr=SimpleNamespace(isatty=lambda: True),
        ),
    )

    def fake_run(_self) -> int:
        called.append(True)
        return 0

    monkeypatch.setattr(lexicon_module.LexiconBuildMonitorApp, "run", fake_run)

    result = runner.invoke(
        cli,
        [
            "lexicon",
            "build",
            "--force",
        ],
    )

    assert result.exit_code == 0, result.output
    assert called == [True]


def test_lexicon_build_uses_default_app_data_path(
    runner,
    isolated_morphology_index_db: Path,
) -> None:
    _build_canonical_source_db(runner, isolated_morphology_index_db)
    result = runner.invoke(
        cli,
        [
            "lexicon",
            "build",
            "--force",
        ],
    )
    assert result.exit_code == 0, result.output
    assert f"index_db={isolated_morphology_index_db.resolve()}" in result.output


def test_lexicon_build_refuses_existing_data_without_force(
    runner,
    isolated_morphology_index_db: Path,
) -> None:
    _build_canonical_source_db(runner, isolated_morphology_index_db)
    first = runner.invoke(
        cli,
        [
            "lexicon",
            "build",
            "--no-tui",
        ],
    )
    assert first.exit_code == 0, first.output

    blocked = runner.invoke(
        cli,
        [
            "lexicon",
            "build",
            "--no-tui",
        ],
    )
    assert blocked.exit_code != 0
    assert "--force" in blocked.output

    forced = runner.invoke(
        cli,
        [
            "lexicon",
            "build",
            "--no-tui",
            "--force",
        ],
    )
    assert forced.exit_code == 0, forced.output


def test_lexicon_build_requires_bt_source_tables(
    runner,
    isolated_morphology_index_db: Path,
) -> None:
    _build_canonical_source_db(runner, isolated_morphology_index_db)
    with sqlite3.connect(isolated_morphology_index_db) as connection:
        connection.executescript(
            """
            DROP TABLE IF EXISTS bt_edit_log;
            DROP TABLE IF EXISTS bt_variants;
            DROP TABLE IF EXISTS bt_senses;
            DROP TABLE IF EXISTS bt_entries;
            """
        )

    result = runner.invoke(
        cli,
        [
            "lexicon",
            "build",
            "--no-tui",
            "--force",
        ],
    )

    assert result.exit_code != 0
    assert "Lexicon rebuild requires source tables:" in result.output
    assert "bt_entries" in result.output
    assert "bt_senses" in result.output
    assert "bt_variants" in result.output


def test_lexicon_browse_help(runner) -> None:
    result = runner.invoke(cli, ["lexicon", "browse", "--help"])
    assert result.exit_code == 0
    assert "--index-db" not in result.output
    assert "--index-dir" not in result.output
