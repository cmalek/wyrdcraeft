from __future__ import annotations

import importlib
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest
from click.testing import CliRunner

from wyrdcraeft.cli.cli import cli, should_run_database_readiness_gate
from wyrdcraeft.db.runtime import (
    DatabaseMigrationError,
    DatabaseStartupRuntime,
    LegacyDatabaseResetRequired,
)
from wyrdcraeft.db.state import write_backup_state
from wyrdcraeft.settings import Settings


def _make_settings(tmp_path: Path) -> Settings:
    return Settings(app_data_dir=tmp_path / "app-data")


def _create_pre_alembic_forms_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE forms (
                id INTEGER PRIMARY KEY,
                lemma TEXT NOT NULL
            );
            INSERT INTO forms (lemma) VALUES ('legacy');
            """
        )
        connection.commit()


def test_fresh_missing_db_bootstraps_with_alembic_path(tmp_path: Path) -> None:
    messages: list[str] = []
    settings = _make_settings(tmp_path)
    runtime = DatabaseStartupRuntime(
        settings=settings,
        interactive=False,
        echo=messages.append,
    )

    def bootstrap() -> None:
        runtime.db_path.write_text("bootstrapped", encoding="utf-8")

    runtime._apply_migrations = bootstrap

    runtime.ensure_ready()

    assert runtime.db_path.read_text(encoding="utf-8") == "bootstrapped"
    assert messages == [
        "checking canonical database",
        "checking alembic revision",
        "applying migrations",
        "migration complete",
    ]


def test_pre_alembic_canonical_db_resets_and_requires_rebuild(
    tmp_path: Path,
) -> None:
    messages: list[str] = []
    settings = _make_settings(tmp_path)
    runtime = DatabaseStartupRuntime(
        settings=settings,
        interactive=False,
        echo=messages.append,
        now=lambda: datetime(2026, 6, 30, 12, 0, tzinfo=UTC),
    )
    runtime.db_path.write_text("before", encoding="utf-8")
    runtime._get_current_revision = lambda: None
    runtime._get_head_revision = lambda: None

    def migrate() -> None:
        runtime.db_path.write_text("fresh", encoding="utf-8")

    runtime._apply_migrations = migrate

    with pytest.raises(LegacyDatabaseResetRequired) as excinfo:
        runtime.ensure_ready()

    assert runtime.db_path.read_text(encoding="utf-8") == "fresh"
    assert Path(excinfo.value.backup_path).read_text(encoding="utf-8") == "before"
    assert excinfo.value.rebuild_instructions == ("wyrdcraeft dictionary build",)
    assert messages == [
        "checking canonical database",
        "found canonical database",
        "checking alembic revision",
        "creating backup",
        "applying migrations",
        "migration complete",
        "rebuild required",
    ]


def test_pre_alembic_canonical_db_resets_before_real_initial_migration(
    tmp_path: Path,
) -> None:
    messages: list[str] = []
    settings = _make_settings(tmp_path)
    runtime = DatabaseStartupRuntime(
        settings=settings,
        interactive=False,
        echo=messages.append,
        now=lambda: datetime(2026, 6, 30, 12, 0, tzinfo=UTC),
    )
    _create_pre_alembic_forms_db(runtime.db_path)

    with pytest.raises(LegacyDatabaseResetRequired) as excinfo:
        runtime.ensure_ready()

    with sqlite3.connect(runtime.db_path) as connection:
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()
        forms_columns = {
            str(row[1])
            for row in connection.execute("PRAGMA table_info(forms)").fetchall()
        }

    assert revision is not None
    assert "bt_key" in forms_columns
    assert "lemma" not in forms_columns
    assert "wordclass_id" in forms_columns
    assert "wordclass" not in forms_columns
    assert "function" not in forms_columns
    assert Path(excinfo.value.backup_path).exists()
    assert Path(excinfo.value.backup_path) != runtime.db_path
    assert messages == [
        "checking canonical database",
        "found canonical database",
        "checking alembic revision",
        "creating backup",
        "applying migrations",
        "migration complete",
        "rebuild required",
    ]


def test_legacy_morphology_db_creates_fresh_canonical_db_with_real_migration(
    tmp_path: Path,
) -> None:
    messages: list[str] = []
    settings = _make_settings(tmp_path)
    runtime = DatabaseStartupRuntime(
        settings=settings,
        interactive=False,
        echo=messages.append,
        now=lambda: datetime(2026, 6, 30, 12, 0, tzinfo=UTC),
    )
    _create_pre_alembic_forms_db(runtime.legacy_db_path)

    with pytest.raises(LegacyDatabaseResetRequired) as excinfo:
        runtime.ensure_ready()

    with sqlite3.connect(runtime.db_path) as connection:
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()
        forms_columns = {
            str(row[1])
            for row in connection.execute("PRAGMA table_info(forms)").fetchall()
        }

    assert revision is not None
    assert "bt_key" in forms_columns
    assert "lemma" not in forms_columns
    assert "wordclass_id" in forms_columns
    assert "wordclass" not in forms_columns
    assert "function" not in forms_columns
    assert Path(excinfo.value.backup_path).exists()
    assert Path(excinfo.value.backup_path) != runtime.db_path
    assert messages == [
        "checking canonical database",
        "found legacy database",
        "creating backup",
        "applying migrations",
        "migration complete",
        "rebuild required",
    ]


def test_stale_canonical_db_creates_backup_then_migrates(tmp_path: Path) -> None:
    messages: list[str] = []
    settings = _make_settings(tmp_path)
    runtime = DatabaseStartupRuntime(
        settings=settings,
        interactive=False,
        echo=messages.append,
        now=lambda: datetime(2026, 6, 30, 12, 0, tzinfo=UTC),
    )
    runtime.db_path.write_text("before", encoding="utf-8")
    runtime._get_current_revision = lambda: "old"
    runtime._get_head_revision = lambda: "new"

    def migrate() -> None:
        runtime.db_path.write_text("after", encoding="utf-8")

    runtime._apply_migrations = migrate

    runtime.ensure_ready()

    assert runtime.db_path.read_text(encoding="utf-8") == "after"
    state = runtime.state_store.load()
    assert state is not None
    assert Path(state["backup_path"]).exists()
    assert state["migration_version"] == runtime.version
    assert messages == [
        "checking canonical database",
        "found canonical database",
        "checking alembic revision",
        "creating backup",
        "applying migrations",
        "migration complete",
    ]


def test_migration_failure_restores_backup_and_surfaces_traceback(
    tmp_path: Path,
) -> None:
    messages: list[str] = []
    settings = _make_settings(tmp_path)
    runtime = DatabaseStartupRuntime(
        settings=settings,
        interactive=False,
        echo=messages.append,
        now=lambda: datetime(2026, 6, 30, 12, 0, tzinfo=UTC),
    )
    runtime.db_path.write_text("before", encoding="utf-8")
    runtime._get_current_revision = lambda: "old"
    runtime._get_head_revision = lambda: "new"

    def explode() -> None:
        runtime.db_path.write_text("broken", encoding="utf-8")
        message = "boom"
        raise RuntimeError(message)

    runtime._apply_migrations = explode

    with pytest.raises(DatabaseMigrationError) as excinfo:
        runtime.ensure_ready()

    assert runtime.db_path.read_text(encoding="utf-8") == "before"
    assert "boom" in excinfo.value.traceback_text
    assert excinfo.value.rebuild_instructions == ("wyrdcraeft dictionary build",)
    assert messages == [
        "checking canonical database",
        "found canonical database",
        "checking alembic revision",
        "creating backup",
        "applying migrations",
        "restoring backup after migration failure",
    ]


def test_fresh_bootstrap_failure_raises_typed_error_and_cleans_partial_db(
    tmp_path: Path,
) -> None:
    messages: list[str] = []
    settings = _make_settings(tmp_path)
    runtime = DatabaseStartupRuntime(
        settings=settings,
        interactive=False,
        echo=messages.append,
    )

    def explode() -> None:
        runtime.db_path.write_text("partial", encoding="utf-8")
        message = "fresh boom"
        raise RuntimeError(message)

    runtime._apply_migrations = explode

    with pytest.raises(DatabaseMigrationError) as excinfo:
        runtime.ensure_ready()

    assert not runtime.db_path.exists()
    assert "fresh boom" in excinfo.value.traceback_text
    assert excinfo.value.rebuild_instructions == ("wyrdcraeft dictionary build",)
    assert messages == [
        "checking canonical database",
        "checking alembic revision",
        "applying migrations",
        "restoring backup after migration failure",
    ]


def test_non_interactive_invocation_keeps_backup_and_prints_reminder(
    tmp_path: Path,
) -> None:
    messages: list[str] = []
    settings = _make_settings(tmp_path)
    runtime = DatabaseStartupRuntime(
        settings=settings,
        interactive=False,
        echo=messages.append,
    )
    runtime.db_path.write_text("canonical", encoding="utf-8")
    runtime._get_current_revision = lambda: "head"
    runtime._get_head_revision = lambda: "head"
    backup_path = tmp_path / "app-data" / "wyrdcraeft.sqlite3.20260630-120000.bak"
    backup_path.write_text("backup", encoding="utf-8")
    write_backup_state(
        runtime.db_path,
        {
            "backup_path": str(backup_path),
            "created_at": "2026-06-30T12:00:00+00:00",
            "migration_version": runtime.version,
        },
    )

    runtime.ensure_ready()

    assert backup_path.exists()
    assert any("Found backup database from 2026-06-30" in message for message in messages)


def test_interactive_prompt_matches_locked_wording_and_deletes_backup(
    tmp_path: Path,
) -> None:
    prompts: list[str] = []
    settings = _make_settings(tmp_path)
    runtime = DatabaseStartupRuntime(
        settings=settings,
        interactive=True,
        prompt=lambda text: prompts.append(text) or "y",
    )
    runtime.db_path.write_text("canonical", encoding="utf-8")
    runtime._get_current_revision = lambda: "head"
    runtime._get_head_revision = lambda: "head"
    backup_path = tmp_path / "app-data" / "wyrdcraeft.sqlite3.20260630-120000.bak"
    backup_path.write_text("backup", encoding="utf-8")
    write_backup_state(
        runtime.db_path,
        {
            "backup_path": str(backup_path),
            "created_at": "2026-06-30T12:00:00+00:00",
            "migration_version": runtime.version,
        },
    )

    runtime.ensure_ready()

    assert prompts == [
        "Found backup database from 2026-06-30, caused by migration to 0.1.0. "
        "Delete it? Answer `y` if you have used wyrdcraeft successfully since "
        "the last migration. [y/N]"
    ]
    assert not backup_path.exists()
    assert runtime.state_store.load() is None


def test_interactive_blank_prompt_keeps_backup_without_retry(
    tmp_path: Path,
) -> None:
    prompts: list[str] = []
    settings = _make_settings(tmp_path)
    runtime = DatabaseStartupRuntime(
        settings=settings,
        interactive=True,
        prompt=lambda text: prompts.append(text) or "",
    )
    runtime.db_path.write_text("canonical", encoding="utf-8")
    runtime._get_current_revision = lambda: "head"
    runtime._get_head_revision = lambda: "head"
    backup_path = tmp_path / "app-data" / "wyrdcraeft.sqlite3.20260630-120000.bak"
    backup_path.write_text("backup", encoding="utf-8")
    write_backup_state(
        runtime.db_path,
        {
            "backup_path": str(backup_path),
            "created_at": "2026-06-30T12:00:00+00:00",
            "migration_version": runtime.version,
        },
    )

    runtime.ensure_ready()

    assert prompts == [
        "Found backup database from 2026-06-30, caused by migration to 0.1.0. "
        "Delete it? Answer `y` if you have used wyrdcraeft successfully since "
        "the last migration. [y/N]"
    ]
    assert backup_path.exists()
    assert runtime.state_store.load() is not None


@pytest.mark.parametrize(
    ("command_name", "expected"),
    [
        (None, False),
        ("version", False),
        ("settings", False),
        ("source", False),
        ("diacritic", False),
        ("morphology", True),
        ("dictionary", True),
        ("lexicon", True),
    ],
)
def test_should_run_database_readiness_gate(
    command_name: str | None,
    expected: bool,
) -> None:
    assert should_run_database_readiness_gate(command_name) is expected


def test_child_help_skips_database_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    calls: list[str] = []
    cli_module = importlib.import_module("wyrdcraeft.cli.cli")

    def fail_if_called(**_: object) -> None:
        calls.append("called")
        msg = "db gate should not run for help"
        raise AssertionError(msg)

    monkeypatch.setattr(cli_module, "ensure_database_ready", fail_if_called)

    result = runner.invoke(cli, ["morphology", "--help"])

    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert calls == []
