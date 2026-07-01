"""Tests for attaching Bosworth-Toller dictionary tables to morphology SQLite."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from wyrdcraeft.cli.cli import cli
from wyrdcraeft.services.dictionary.pipeline import BTIndexPipeline
from wyrdcraeft.services.dictionary.sinks import BTSqliteSink

_SAMPLE_LINES = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "dictionary"
    / "sample_lines.txt"
)


def _seed_forms_table(db_path: Path, row_count: int) -> int:
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE forms (
                id INTEGER PRIMARY KEY,
                lemma TEXT NOT NULL
            );
            """
        )
        for index in range(row_count):
            conn.execute(
                "INSERT INTO forms (lemma) VALUES (?)",
                (f"lemma-{index}",),
            )
        conn.commit()
    return row_count


def _index_with_attach(source: Path, db_path: Path) -> int:
    sink = BTSqliteSink(db_path, attach_mode=True)
    try:
        report = BTIndexPipeline().run(source, sink)
    finally:
        sink.close()
    return report.merged


def test_attach_preserves_forms_and_writes_bt_entries(temp_dir: Path) -> None:
    morphology_db = temp_dir / "morphology.sqlite3"
    initial_forms = _seed_forms_table(morphology_db, row_count=5)

    merged = _index_with_attach(_SAMPLE_LINES, morphology_db)

    with sqlite3.connect(morphology_db) as conn:
        forms_count = conn.execute("SELECT COUNT(*) FROM forms").fetchone()[0]
        bt_count = conn.execute("SELECT COUNT(*) FROM bt_entries").fetchone()[0]
        abbad = conn.execute(
            """
            SELECT norm_key, pos, headword_raw
            FROM bt_entries
            WHERE norm_key = ? AND pos = ?
            """,
            ("abbad", "noun"),
        ).fetchone()

    assert forms_count == initial_forms
    assert bt_count == merged
    assert bt_count > 0
    assert abbad is not None


def test_attach_rerun_is_idempotent_and_preserves_forms(temp_dir: Path) -> None:
    morphology_db = temp_dir / "morphology.sqlite3"
    initial_forms = _seed_forms_table(morphology_db, row_count=4)

    first_merged = _index_with_attach(_SAMPLE_LINES, morphology_db)
    second_merged = _index_with_attach(_SAMPLE_LINES, morphology_db)

    with sqlite3.connect(morphology_db) as conn:
        forms_count = conn.execute("SELECT COUNT(*) FROM forms").fetchone()[0]
        bt_count = conn.execute("SELECT COUNT(*) FROM bt_entries").fetchone()[0]
        senses_count = conn.execute("SELECT COUNT(*) FROM bt_senses").fetchone()[0]
        variants_count = conn.execute("SELECT COUNT(*) FROM bt_variants").fetchone()[0]
        edit_log_count = conn.execute("SELECT COUNT(*) FROM bt_edit_log").fetchone()[0]

    assert first_merged == second_merged
    assert forms_count == initial_forms
    assert bt_count == second_merged
    assert senses_count > 0
    assert variants_count > 0
    assert edit_log_count >= 0


def test_attach_missing_db_creates_bt_only(temp_dir: Path) -> None:
    morphology_db = temp_dir / "new_morphology.sqlite3"
    assert not morphology_db.exists()

    merged = _index_with_attach(_SAMPLE_LINES, morphology_db)

    with sqlite3.connect(morphology_db) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        bt_count = conn.execute("SELECT COUNT(*) FROM bt_entries").fetchone()[0]

    assert "forms" not in tables
    assert {"bt_entries", "bt_senses", "bt_variants", "bt_edit_log"} <= tables
    assert bt_count == merged
    assert merged > 0


def test_cli_index_bt_defaults_to_morphology_attach(
    runner,
    temp_dir: Path,
    isolated_morphology_app_data: Path,
) -> None:
    isolated_morphology_app_data.mkdir(parents=True, exist_ok=True)
    morphology_db = temp_dir / "morphology.sqlite3"
    initial_forms = _seed_forms_table(morphology_db, row_count=3)

    result = runner.invoke(
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

    assert result.exit_code == 0, result.output
    assert "attach_mode=yes" in result.output
    assert f"index_db={morphology_db.resolve()}" in result.output

    with sqlite3.connect(morphology_db) as conn:
        forms_count = conn.execute("SELECT COUNT(*) FROM forms").fetchone()[0]
        bt_count = conn.execute("SELECT COUNT(*) FROM bt_entries").fetchone()[0]

    assert forms_count == initial_forms
    assert bt_count > 0


def test_cli_index_bt_missing_morphology_db_fails(
    runner,
    temp_dir: Path,
    isolated_morphology_app_data: Path,
) -> None:
    isolated_morphology_app_data.mkdir(parents=True, exist_ok=True)
    morphology_db = temp_dir / "missing.sqlite3"
    assert not morphology_db.exists()

    result = runner.invoke(
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

    assert result.exit_code != 0
    assert "Canonical database not found" in result.output
    assert "morphology generate" in result.output


def test_cli_standalone_writes_dictionary_db(
    runner,
    temp_dir: Path,
    isolated_morphology_app_data: Path,
) -> None:
    isolated_morphology_app_data.mkdir(parents=True, exist_ok=True)
    dictionary_db = temp_dir / "dictionary.sqlite3"

    result = runner.invoke(
        cli,
        [
            "dictionary",
            "index-bt",
            "--source",
            str(_SAMPLE_LINES),
            "--standalone",
            "--index-db",
            str(dictionary_db),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "attach_mode=no" in result.output
    assert dictionary_db.is_file()

    with sqlite3.connect(dictionary_db) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    assert "forms" not in tables
    assert "bt_entries" in tables
