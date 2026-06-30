"""CLI smoke tests for lexicon browse workflow commands."""

from __future__ import annotations

import sqlite3
from types import SimpleNamespace
from typing import TYPE_CHECKING

from wyrdcraeft.cli import lexicon as lexicon_module
from wyrdcraeft.cli.cli import cli
from wyrdcraeft.paths import MORPHOLOGY_INDEX_FILENAME

if TYPE_CHECKING:
    from pathlib import Path


def test_lexicon_group_help(runner) -> None:
    result = runner.invoke(cli, ["lexicon", "--help"])
    assert result.exit_code == 0
    assert "build" in result.output


def test_lexicon_build_help(runner) -> None:
    result = runner.invoke(cli, ["lexicon", "build", "--help"])
    assert result.exit_code == 0
    assert "--index-db" in result.output
    assert "--index-dir" in result.output
    assert "--no-tui" in result.output
    assert "--quiet" in result.output
    assert "--force" in result.output
    assert "--no-progress" not in result.output


def test_lexicon_build_smoke(runner, lexicon_source_db: Path) -> None:
    result = runner.invoke(
        cli,
        [
            "lexicon",
            "build",
            "--no-tui",
            "--force",
            "--index-db",
            str(lexicon_source_db),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Lexicon build complete." in result.output
    assert f"index_db={lexicon_source_db.resolve()}" in result.output
    assert "built_at=" in result.output
    assert "forms_source_count=" in result.output
    assert "bt_entries_source_count=" in result.output
    assert "entries_written=" in result.output
    assert "forms_written=" in result.output
    assert "search_keys_written=" in result.output

    with sqlite3.connect(lexicon_source_db) as connection:
        assert connection.execute("SELECT COUNT(*) FROM lexicon_entries").fetchone()[0] > 0
        assert connection.execute("SELECT COUNT(*) FROM lexicon_forms").fetchone()[0] > 0
        assert (
            connection.execute("SELECT COUNT(*) FROM lexicon_search_keys").fetchone()[0]
            > 0
        )
    assert "[info] stage started:" in result.stderr


def test_lexicon_build_quiet_smoke(runner, lexicon_source_db: Path) -> None:
    result = runner.invoke(
        cli,
        [
            "lexicon",
            "build",
            "--no-tui",
            "--quiet",
            "--force",
            "--index-db",
            str(lexicon_source_db),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Lexicon build complete." in result.output
    assert "[info] stage started:" not in result.stderr


def test_lexicon_build_uses_tui_on_tty(
    runner,
    lexicon_source_db: Path,
    monkeypatch,
) -> None:
    called: list[bool] = []

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
            "--index-db",
            str(lexicon_source_db),
        ],
    )

    assert result.exit_code == 0, result.output
    assert called == [True]


def test_lexicon_build_index_dir_smoke(runner, lexicon_source_db: Path, tmp_path: Path) -> None:
    index_dir = tmp_path / "morphology-index"
    index_dir.mkdir()
    morphology_db = index_dir / MORPHOLOGY_INDEX_FILENAME
    morphology_db.write_bytes(lexicon_source_db.read_bytes())

    result = runner.invoke(
        cli,
        [
            "lexicon",
            "build",
            "--force",
            "--index-dir",
            str(index_dir),
        ],
    )
    assert result.exit_code == 0, result.output
    assert f"index_db={morphology_db.resolve()}" in result.output


def test_lexicon_build_fails_on_missing_bt_tables(runner, tmp_path: Path) -> None:
    db_path = tmp_path / "forms-only.sqlite3"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE forms (id INTEGER PRIMARY KEY)")
        connection.commit()

    result = runner.invoke(
        cli,
        [
            "lexicon",
            "build",
            "--index-db",
            str(db_path),
        ],
    )
    assert result.exit_code != 0
    assert "Lexicon rebuild requires source tables:" in result.output
    assert "bt_entries" in result.output


def test_lexicon_build_refuses_existing_data_without_force(
    runner,
    lexicon_source_db: Path,
) -> None:
    first = runner.invoke(
        cli,
        [
            "lexicon",
            "build",
            "--no-tui",
            "--index-db",
            str(lexicon_source_db),
        ],
    )
    assert first.exit_code == 0, first.output

    blocked = runner.invoke(
        cli,
        [
            "lexicon",
            "build",
            "--no-tui",
            "--index-db",
            str(lexicon_source_db),
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
            "--index-db",
            str(lexicon_source_db),
        ],
    )
    assert forced.exit_code == 0, forced.output


def test_lexicon_browse_help(runner) -> None:
    result = runner.invoke(cli, ["lexicon", "browse", "--help"])
    assert result.exit_code == 0
    assert "--index-db" in result.output
    assert "--index-dir" in result.output
