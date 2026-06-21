"""Platform-specific application data path resolution for wyrdcraeft."""

from __future__ import annotations

import sys
from pathlib import Path

import click

#: Default morphology SQLite index filename written by ``morphology generate``.
MORPHOLOGY_INDEX_FILENAME = "morphology.sqlite3"


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


def get_morphology_index_db_path(*, app_data_dir: Path | None = None) -> Path:
    """
    Resolve the default morphology SQLite index path under app data.

    Keyword Args:
        app_data_dir: Optional settings override for the app data directory.

    Returns:
        Absolute path to ``morphology.sqlite3`` under the app data directory.

    Side Effects:
        Creates the parent application data directory when missing.

    """
    db_path = get_app_data_path(app_data_dir=app_data_dir) / MORPHOLOGY_INDEX_FILENAME
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path.resolve()


def resolve_morphology_index_db_path(
    *,
    index_db: Path | None = None,
    index_dir: Path | None = None,
    app_data_dir: Path | None = None,
) -> Path:
    """
    Resolve the morphology SQLite index path from CLI and settings overrides.

    Keyword Args:
        index_db: Optional explicit SQLite index file path from ``--index-db``.
        index_dir: Optional index directory override from ``--index-dir``.
        app_data_dir: Optional settings override for the app data directory.

    Returns:
        Absolute path to the morphology SQLite index file.

    Raises:
        click.ClickException: Both ``--index-db`` and ``--index-dir`` were provided.

    Side Effects:
        Creates parent directories for the resolved index path when missing.

    """
    if index_db is not None and index_dir is not None:
        msg = "Provide at most one of --index-db or --index-dir."
        raise click.ClickException(msg)

    if index_db is not None:
        resolved = index_db.expanduser().resolve()
    elif index_dir is not None:
        resolved = (
            index_dir.expanduser().resolve() / MORPHOLOGY_INDEX_FILENAME
        )
    else:
        resolved = get_morphology_index_db_path(app_data_dir=app_data_dir)

    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved
