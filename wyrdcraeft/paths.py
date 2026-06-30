"""Platform-specific application data path resolution for wyrdcraeft."""

from __future__ import annotations

import sys
from pathlib import Path

import click

#: Canonical SQLite database filename stored under the app data directory.
CANONICAL_DB_FILENAME = "wyrdcraeft.sqlite3"
#: Legacy morphology SQLite filename retained for compatibility with callers.
MORPHOLOGY_INDEX_FILENAME = CANONICAL_DB_FILENAME
#: Default Bosworth-Toller dictionary SQLite index filename.
DICTIONARY_INDEX_FILENAME = "dictionary.sqlite3"


def get_app_data_path(*, app_data_dir: Path | None = None) -> Path:
    """
    Resolve the base application data directory.

    Keyword Args:
        app_data_dir: Optional settings override for the app data directory.

    Returns:
        Expanded application data directory path.

    Raises:
        ValueError: The current platform is not supported.

    """
    if app_data_dir is not None:
        return app_data_dir.expanduser().resolve()

    home = Path.home()
    if sys.platform == "win32":
        return home / "AppData" / "Local" / "wyrdcraeft"
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "wyrdcraeft"
    if sys.platform == "linux":
        return home / ".config" / "wyrdcraeft"
    msg = f"Unsupported platform: {sys.platform}"
    raise ValueError(msg)


def get_canonical_db_path(*, app_data_dir: Path | None = None) -> Path:
    """
    Resolve the canonical SQLite database path under app data.

    Keyword Args:
        app_data_dir: Optional settings override for the app data directory.

    Returns:
        Absolute path to ``wyrdcraeft.sqlite3`` under the app data directory.

    Side Effects:
        Creates the parent application data directory when missing.

    """
    db_path = get_app_data_path(app_data_dir=app_data_dir) / CANONICAL_DB_FILENAME
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path.resolve()


def _resolve_db_path(
    *,
    index_db: Path | None,
    index_dir: Path | None,
    default_path: Path,
    filename: str,
) -> Path:
    """
    Resolve one SQLite database path from explicit overrides or a default path.

    Keyword Args:
        index_db: Optional explicit SQLite file path override.
        index_dir: Optional explicit directory override.
        default_path: Fallback path used when no explicit override is provided.
        filename: SQLite filename appended when resolving ``index_dir``.

    Returns:
        Absolute SQLite path with parent directories created.

    Raises:
        click.ClickException: Both explicit overrides were provided.

    """
    if index_db is not None and index_dir is not None:
        msg = "Provide at most one of --index-db or --index-dir."
        raise click.ClickException(msg)

    if index_db is not None:
        resolved = index_db.expanduser().resolve()
        resolved.parent.mkdir(parents=True, exist_ok=True)
        return resolved
    if index_dir is not None:
        resolved_dir = index_dir.expanduser().resolve()
        resolved_dir.mkdir(parents=True, exist_ok=True)
        return (resolved_dir / filename).resolve()

    default_path.parent.mkdir(parents=True, exist_ok=True)
    return default_path.resolve()


def get_dictionary_index_db_path(*, app_data_dir: Path | None = None) -> Path:
    """
    Resolve the default dictionary SQLite index path under app data.

    Keyword Args:
        app_data_dir: Optional settings override for the app data directory.

    Returns:
        Absolute path to ``dictionary.sqlite3`` under the app data directory.

    Side Effects:
        Creates the parent application data directory when missing.

    """
    db_path = get_app_data_path(app_data_dir=app_data_dir) / DICTIONARY_INDEX_FILENAME
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path.resolve()
