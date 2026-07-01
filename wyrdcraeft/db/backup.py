"""SQLite backup helpers for startup migrations."""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def create_backup(
    db_path: Path,
    *,
    migration_version: str,
    retention: int = 1,
    now: datetime | None = None,
) -> Path:
    """
    Copy one SQLite database to a timestamped backup file.

    Args:
        db_path: SQLite database path to copy.

    Keyword Args:
        migration_version: Version string causing the backup.
        retention: Number of backups to keep for this database.
        now: Optional timestamp override for deterministic tests.

    Returns:
        Filesystem path to the newly created backup copy.

    Raises:
        FileNotFoundError: The source database does not exist.
        ValueError: ``retention`` is less than one.

    """
    del migration_version
    if retention < 1:
        msg = "retention must be at least 1"
        raise ValueError(msg)

    resolved = db_path.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(resolved)

    timestamp = (now or datetime.now(UTC)).strftime("%Y%m%d-%H%M%S")
    backup_path = resolved.with_name(f"{resolved.name}.{timestamp}.bak")
    shutil.copy2(resolved, backup_path)
    _prune_old_backups(resolved, keep=retention, preserve=backup_path)
    return backup_path


def restore_backup(backup_path: Path, db_path: Path) -> None:
    """
    Replace one SQLite database with a backup copy.

    Args:
        backup_path: Backup copy to restore from.
        db_path: Destination SQLite database path.

    Side Effects:
        Overwrites ``db_path`` with the contents of ``backup_path``.

    """
    resolved_db = db_path.expanduser().resolve()
    resolved_db.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup_path.expanduser().resolve(), resolved_db)


def list_backups(db_path: Path) -> list[Path]:
    """
    List timestamped backup files for one SQLite database.

    Args:
        db_path: Database whose sibling ``.bak`` files should be listed.

    Returns:
        Sorted backup paths from oldest to newest.

    """
    resolved = db_path.expanduser().resolve()
    pattern = f"{resolved.name}.*.bak"
    return sorted(resolved.parent.glob(pattern))


def _prune_old_backups(db_path: Path, *, keep: int, preserve: Path) -> None:
    """
    Delete old backups beyond the configured retention count.

    Args:
        db_path: Database whose backups should be pruned.

    Keyword Args:
        keep: Number of backups to preserve.
        preserve: Newly created backup that must not be deleted.

    Side Effects:
        Removes older sibling ``.bak`` files.

    """
    backups = [path for path in list_backups(db_path) if path != preserve]
    for old_backup in backups[: max(0, len(backups) - (keep - 1))]:
        old_backup.unlink(missing_ok=True)
