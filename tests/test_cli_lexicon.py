"""CLI smoke tests for lexicon browse workflow commands."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

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


def test_lexicon_build_smoke(runner, lexicon_source_db: Path) -> None:
    result = runner.invoke(
        cli,
        [
            "lexicon",
            "build",
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


def test_lexicon_browse_help(runner) -> None:
    result = runner.invoke(cli, ["lexicon", "browse", "--help"])
    assert result.exit_code == 0
    assert "--index-db" in result.output
    assert "--index-dir" in result.output
