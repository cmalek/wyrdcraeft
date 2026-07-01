from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from wyrdcraeft.db.runtime import (
    DatabaseMigrationError,
    DatabaseStartupRuntime,
    LegacyDatabaseResetRequired,
)
from wyrdcraeft.settings import Settings


def test_legacy_morphology_db_is_backed_up_then_requires_rebuild(
    tmp_path: Path,
) -> None:
    messages: list[str] = []
    settings = Settings(app_data_dir=tmp_path / "app-data")
    runtime = DatabaseStartupRuntime(
        settings=settings,
        interactive=False,
        echo=messages.append,
        now=lambda: datetime(2026, 6, 30, 12, 0, tzinfo=UTC),
    )
    runtime.legacy_db_path.parent.mkdir(parents=True, exist_ok=True)
    runtime.legacy_db_path.write_text("legacy", encoding="utf-8")

    def bootstrap() -> None:
        runtime.db_path.write_text("canonical", encoding="utf-8")

    runtime._apply_migrations = bootstrap

    with pytest.raises(LegacyDatabaseResetRequired) as excinfo:
        runtime.ensure_ready()

    assert runtime.db_path.read_text(encoding="utf-8") == "canonical"
    assert excinfo.value.rebuild_instructions == (
        "wyrdcraeft morphology build",
        "wyrdcraeft dictionary build",
        "wyrdcraeft lexicon build",
    )
    assert Path(excinfo.value.backup_path).read_text(encoding="utf-8") == "legacy"
    assert messages == [
        "checking canonical database",
        "found legacy database",
        "creating backup",
        "applying migrations",
        "migration complete",
        "rebuild required",
    ]


def test_legacy_bootstrap_failure_restores_cleanly_and_raises_typed_error(
    tmp_path: Path,
) -> None:
    messages: list[str] = []
    settings = Settings(app_data_dir=tmp_path / "app-data")
    runtime = DatabaseStartupRuntime(
        settings=settings,
        interactive=False,
        echo=messages.append,
        now=lambda: datetime(2026, 6, 30, 12, 0, tzinfo=UTC),
    )
    runtime.legacy_db_path.parent.mkdir(parents=True, exist_ok=True)
    runtime.legacy_db_path.write_text("legacy", encoding="utf-8")

    def explode() -> None:
        runtime.db_path.write_text("partial", encoding="utf-8")
        message = "legacy boom"
        raise RuntimeError(message)

    runtime._apply_migrations = explode

    with pytest.raises(DatabaseMigrationError) as excinfo:
        runtime.ensure_ready()

    assert not runtime.db_path.exists()
    assert runtime.legacy_db_path.read_text(encoding="utf-8") == "legacy"
    assert "legacy boom" in excinfo.value.traceback_text
    assert excinfo.value.rebuild_instructions == (
        "wyrdcraeft morphology build",
        "wyrdcraeft dictionary build",
        "wyrdcraeft lexicon build",
    )
    assert messages == [
        "checking canonical database",
        "found legacy database",
        "creating backup",
        "applying migrations",
        "restoring backup after migration failure",
    ]
