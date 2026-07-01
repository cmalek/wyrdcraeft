from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from wyrdcraeft.db.backup import create_backup, restore_backup
from wyrdcraeft.db.state import load_backup_state, write_backup_state

if TYPE_CHECKING:
    from pathlib import Path


def test_create_backup_copies_database_and_keeps_latest_by_default(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "wyrdcraeft.sqlite3"
    db_path.write_text("first", encoding="utf-8")

    first_backup = create_backup(
        db_path,
        migration_version="0.1.0",
        now=datetime(2026, 6, 30, 12, 0, tzinfo=UTC),
    )
    db_path.write_text("second", encoding="utf-8")
    second_backup = create_backup(
        db_path,
        migration_version="0.1.1",
        now=datetime(2026, 6, 30, 12, 1, tzinfo=UTC),
    )

    assert not first_backup.exists()
    assert second_backup.exists()
    assert second_backup.read_text(encoding="utf-8") == "second"


def test_restore_backup_overwrites_database_contents(tmp_path: Path) -> None:
    db_path = tmp_path / "wyrdcraeft.sqlite3"
    db_path.write_text("before", encoding="utf-8")
    backup_path = create_backup(
        db_path,
        migration_version="0.1.0",
        now=datetime(2026, 6, 30, 12, 0, tzinfo=UTC),
    )
    db_path.write_text("after", encoding="utf-8")

    restore_backup(backup_path, db_path)

    assert db_path.read_text(encoding="utf-8") == "before"


def test_backup_state_round_trip_uses_sidecar_beside_canonical_db(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "wyrdcraeft.sqlite3"
    backup_path = tmp_path / "wyrdcraeft.sqlite3.20260630-120000.bak"
    expected_state = {
        "backup_path": str(backup_path),
        "created_at": "2026-06-30T12:00:00+00:00",
        "migration_version": "0.1.0",
    }

    write_backup_state(db_path, expected_state)

    assert load_backup_state(db_path) == expected_state
    assert db_path.with_name("wyrdcraeft.sqlite3.backup-state.json").exists()
