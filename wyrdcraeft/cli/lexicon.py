"""Lexicon browse workflow CLI commands."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import click

from wyrdcraeft.paths import resolve_morphology_index_db_path
from wyrdcraeft.services.lexicon.build import (
    MissingLexiconSourceTablesError,
    rebuild_lexicon,
)
from wyrdcraeft.services.lexicon.tui import (
    LexiconBrowseDataError,
    run_lexicon_browse,
)

if TYPE_CHECKING:
    from wyrdcraeft.settings import Settings


@click.group(
    name="lexicon",
    help="Lexicon browse workflow commands.",
)
def lexicon_group() -> None:
    """Lexicon command group."""


@lexicon_group.command(
    name="build",
    help="Rebuild lexicon read-model tables from morphology and dictionary sources.",
)
@click.option(
    "--index-db",
    type=click.Path(path_type=Path),
    default=None,
    help=(
        "SQLite index file path (overrides --index-dir and the OS app-data default)."
    ),
)
@click.option(
    "--index-dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help=(
        "Directory for morphology.sqlite3 (overrides the OS app-data default)."
    ),
)
@click.pass_context
def build(
    ctx: click.Context,
    index_db: Path | None,
    index_dir: Path | None,
) -> None:
    """
    Rebuild ``lexicon_*`` tables from ``forms`` and ``bt_*`` source tables.

    Args:
        ctx: Click context carrying loaded settings and global flags.
        index_db: Optional SQLite index file path override.
        index_dir: Optional SQLite index directory override.

    Side Effects:
        Replaces ``lexicon_*`` rows in the target morphology SQLite database.

    Raises:
        click.ClickException: Required source tables are missing or rebuild fails.

    """
    settings: Settings | None = ctx.obj.get("settings")
    app_data_dir = settings.app_data_dir if settings is not None else None
    resolved_index_db = resolve_morphology_index_db_path(
        index_db=index_db,
        index_dir=index_dir,
        app_data_dir=app_data_dir,
    )

    try:
        report = rebuild_lexicon(resolved_index_db)
    except MissingLexiconSourceTablesError as exc:
        raise click.ClickException(str(exc)) from exc
    except OSError as exc:
        msg = f"Failed to rebuild lexicon tables in {resolved_index_db}: {exc}"
        raise click.ClickException(msg) from exc

    click.echo(
        "\n".join(
            [
                "Lexicon build complete.",
                f"index_db={resolved_index_db}",
                f"built_at={report.built_at}",
                f"forms_source_count={report.forms_source_count}",
                f"bt_entries_source_count={report.bt_entries_source_count}",
                f"entries_written={report.entries_written}",
                f"forms_written={report.forms_written}",
                f"search_keys_written={report.search_keys_written}",
            ]
        )
    )


@lexicon_group.command(
    name="browse",
    help="Open the lexicon browse Textual shell.",
)
@click.option(
    "--index-db",
    type=click.Path(path_type=Path),
    default=None,
    help=(
        "SQLite index file path (overrides --index-dir and the OS app-data default)."
    ),
)
@click.option(
    "--index-dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help=(
        "Directory for morphology.sqlite3 (overrides the OS app-data default)."
    ),
)
@click.pass_context
def browse(
    ctx: click.Context,
    index_db: Path | None,
    index_dir: Path | None,
) -> None:
    """
    Launch the lexicon browse shell against the resolved morphology SQLite path.

    Args:
        ctx: Click context carrying loaded settings and global flags.
        index_db: Optional SQLite index file path override.
        index_dir: Optional SQLite index directory override.

    Raises:
        click.ClickException: Path resolution or browse app startup fails.

    """
    settings: Settings | None = ctx.obj.get("settings")
    app_data_dir = settings.app_data_dir if settings is not None else None
    resolved_index_db = resolve_morphology_index_db_path(
        index_db=index_db,
        index_dir=index_dir,
        app_data_dir=app_data_dir,
    )

    try:
        run_lexicon_browse(resolved_index_db)
    except LexiconBrowseDataError as exc:
        raise click.ClickException(str(exc)) from exc
    except OSError as exc:
        msg = f"Failed to launch lexicon browse from {resolved_index_db}: {exc}"
        raise click.ClickException(msg) from exc
