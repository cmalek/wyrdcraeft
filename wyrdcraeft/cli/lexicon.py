"""Lexicon browse workflow CLI commands."""

from __future__ import annotations

import click

from wyrdcraeft.paths import (
    get_canonical_db_path,
)
from wyrdcraeft.services.lexicon.tui import (
    LexiconBrowseDataError,
    run_lexicon_browse,
)


@click.group(
    name="lexicon",
    help="Lexicon browse commands.",
)
def lexicon_group() -> None:
    """Lexicon command group."""


@lexicon_group.command(
    name="browse",
    help="Open the lexicon browse Textual shell.",
)
@click.pass_context
def browse(
    ctx: click.Context,
) -> None:
    """
    Launch the lexicon browse shell against the resolved morphology SQLite path.

    Args:
        ctx: Click context carrying loaded settings and global flags.

    Raises:
        click.ClickException: Path resolution or browse app startup fails.

    """
    settings = ctx.obj.get("settings")
    resolved_index_db = get_canonical_db_path(
        app_data_dir=settings.app_data_dir if settings is not None else None
    )

    try:
        run_lexicon_browse(resolved_index_db)
    except LexiconBrowseDataError as exc:
        raise click.ClickException(str(exc)) from exc
    except OSError as exc:
        msg = f"Failed to launch lexicon browse from {resolved_index_db}: {exc}"
        raise click.ClickException(msg) from exc
