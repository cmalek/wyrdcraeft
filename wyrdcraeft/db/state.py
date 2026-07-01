"""JSON sidecar state for startup database backups."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

#: Sidecar filename suffix stored beside the canonical SQLite database.
BACKUP_STATE_SUFFIX = ".backup-state.json"


class BackupStateStore:
    """
    Persist backup prompt state beside one canonical SQLite database.

    Args:
        db_path: Canonical SQLite database whose sidecar should be managed.

    """

    #: Canonical SQLite database path whose sidecar state is managed.
    _db_path: Path

    def __init__(self, db_path: Path) -> None:
        """
        Store one canonical database path for later sidecar operations.

        Args:
            db_path: Canonical SQLite database whose sidecar should be managed.

        """
        #: Canonical SQLite database path whose sidecar state is managed.
        self._db_path = db_path.expanduser().resolve()

    def load(self) -> dict[str, str] | None:
        """
        Load the current backup sidecar contents.

        Returns:
            Parsed sidecar state, or ``None`` when no sidecar exists.

        """
        return load_backup_state(self._db_path)

    def save(self, state: dict[str, str]) -> None:
        """
        Save one backup sidecar payload.

        Args:
            state: JSON-serializable backup metadata.

        """
        write_backup_state(self._db_path, state)

    def clear(self) -> None:
        """
        Delete the current backup sidecar when present.

        Side Effects:
            Removes the backup sidecar file.

        """
        clear_backup_state(self._db_path)


def get_backup_state_path(db_path: Path) -> Path:
    """
    Resolve the JSON sidecar path for one canonical SQLite database.

    Args:
        db_path: Canonical SQLite database path.

    Returns:
        Absolute sidecar path beside ``db_path``.

    """
    resolved = db_path.expanduser().resolve()
    return resolved.with_name(f"{resolved.name}{BACKUP_STATE_SUFFIX}")


def load_backup_state(db_path: Path) -> dict[str, str] | None:
    """
    Load one backup sidecar payload.

    Args:
        db_path: Canonical SQLite database path owning the sidecar.

    Returns:
        Parsed sidecar mapping, or ``None`` when absent.

    """
    state_path = get_backup_state_path(db_path)
    if not state_path.exists():
        return None
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    return {str(key): str(value) for key, value in payload.items()}


def write_backup_state(db_path: Path, state: dict[str, Any]) -> None:
    """
    Write one backup sidecar payload.

    Args:
        db_path: Canonical SQLite database path owning the sidecar.
        state: JSON-serializable backup metadata.

    Side Effects:
        Creates or overwrites the sidecar JSON file beside ``db_path``.

    """
    state_path = get_backup_state_path(db_path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(state, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def clear_backup_state(db_path: Path) -> None:
    """
    Delete the backup sidecar for one canonical SQLite database.

    Args:
        db_path: Canonical SQLite database path owning the sidecar.

    Side Effects:
        Removes the sidecar file when it exists.

    """
    get_backup_state_path(db_path).unlink(missing_ok=True)
