from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import click
import pytest

from wyrdcraeft import paths
from wyrdcraeft.paths import (
    CANONICAL_DB_FILENAME,
    DICTIONARY_INDEX_FILENAME,
    get_app_data_path,
    get_canonical_db_path,
)
from wyrdcraeft.settings import Settings


@pytest.mark.parametrize(
    ("platform", "expected_suffix"),
    [
        ("win32", Path("AppData") / "Local" / "wyrdcraeft"),
        ("darwin", Path("Library") / "Application Support" / "wyrdcraeft"),
        ("linux", Path(".config") / "wyrdcraeft"),
    ],
)
def test_get_app_data_path_platform_defaults(
    tmp_path: Path,
    platform: str,
    expected_suffix: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    with (
        patch.object(sys, "platform", platform),
        patch.object(Path, "home", return_value=home),
    ):
        assert get_app_data_path() == home / expected_suffix


def test_get_app_data_path_settings_override(tmp_path: Path) -> None:
    override = tmp_path / "custom-app-data"
    assert get_app_data_path(app_data_dir=override) == override.resolve()


def test_get_app_data_path_unsupported_platform() -> None:
    with (
        patch.object(sys, "platform", "freebsd"),
        pytest.raises(ValueError, match="Unsupported platform"),
    ):
        get_app_data_path()


def test_get_canonical_db_path_creates_parent(tmp_path: Path) -> None:
    app_data = tmp_path / "app-data"
    db_path = get_canonical_db_path(app_data_dir=app_data)
    assert db_path == (app_data / CANONICAL_DB_FILENAME).resolve()
    assert app_data.exists()


def test_canonical_db_filename_is_wyrdcraeft_sqlite3() -> None:
    assert CANONICAL_DB_FILENAME == "wyrdcraeft.sqlite3"


def test_resolve_db_path_explicit_file_mkdirs_parent(tmp_path: Path) -> None:
    explicit = tmp_path / "nested" / "custom.sqlite3"
    resolved = paths._resolve_db_path(
        index_db=explicit,
        index_dir=None,
        default_path=get_canonical_db_path(app_data_dir=tmp_path / "app-data"),
        filename=CANONICAL_DB_FILENAME,
    )
    assert resolved == explicit.resolve()
    assert resolved.parent.exists()


def test_resolve_db_path_explicit_dir_mkdirs_target(tmp_path: Path) -> None:
    index_dir = tmp_path / "index-dir"
    resolved = paths._resolve_db_path(
        index_db=None,
        index_dir=index_dir,
        default_path=tmp_path / "unused.sqlite3",
        filename=DICTIONARY_INDEX_FILENAME,
    )
    assert resolved == (index_dir / DICTIONARY_INDEX_FILENAME).resolve()
    assert index_dir.exists()


def test_resolve_db_path_rejects_both_explicit_overrides(tmp_path: Path) -> None:
    with pytest.raises(click.ClickException, match="at most one"):
        paths._resolve_db_path(
            index_db=tmp_path / "one.sqlite3",
            index_dir=tmp_path / "dir",
            default_path=get_canonical_db_path(app_data_dir=tmp_path / "app-data"),
            filename=CANONICAL_DB_FILENAME,
        )


def test_isolated_morphology_index_db_uses_canonical_filename(
    isolated_morphology_index_db: Path,
) -> None:
    assert isolated_morphology_index_db.name == CANONICAL_DB_FILENAME


def test_paths_module_has_no_per_command_db_override_helper() -> None:
    assert not hasattr(paths, "resolve_morphology_index_db_path")
    assert not hasattr(paths, "resolve_dictionary_index_db_path")
    assert not hasattr(paths, "get_morphology_index_db_path")


def test_settings_app_data_dir_env_override(tmp_path: Path) -> None:
    override = tmp_path / "env-app-data"
    os.environ["WYRDCRAEFT_APP_DATA_DIR"] = str(override)
    try:
        settings = Settings()
        assert settings.app_data_dir == override
    finally:
        del os.environ["WYRDCRAEFT_APP_DATA_DIR"]
