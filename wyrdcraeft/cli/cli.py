from __future__ import annotations

import logging
import os
import sys
from importlib.metadata import Distribution

import click
from rich.table import Table
from rich.traceback import install

import wyrdcraeft

from ..db.runtime import (
    DatabaseMigrationError,
    LegacyDatabaseResetRequired,
    ensure_database_ready,
)
from ..settings import Settings
from .utils import console, print_error

# install(show_locals=True)

#: Top-level commands that never need the canonical DB readiness gate.
DATABASE_GATE_SKIP_COMMANDS = frozenset(
    {"version", "settings", "source", "ocr", "diacritic"}
)


class _RootCLIGroup(click.Group):
    """
    Click group that preserves the raw argv for help-aware gate decisions.

    Side Effects:
        Stores raw CLI arguments in ``ctx.meta`` before Click parsing consumes
        child help flags.

    """

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        """
        Persist the raw argv before delegating to Click's normal parser.

        Args:
            ctx: Click context being populated.
            args: Raw command-line arguments being parsed.

        Returns:
            Remaining unparsed arguments from Click.

        Side Effects:
            Saves the original argument vector in ``ctx.meta``.

        """
        ctx.meta["raw_argv"] = tuple(args)
        return super().parse_args(ctx, args)


def _configure_logging(settings: Settings) -> None:
    """
    Configure application logging from settings.

    Args:
        settings: Loaded application settings.

    """
    level = getattr(logging, settings.log_level, logging.INFO)
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(name)s %(levelname)s %(message)s",
        )
    root_logger.setLevel(level)
    logging.getLogger("wyrdcraeft").setLevel(level)


def should_run_database_readiness_gate(command_name: str | None) -> bool:
    """
    Return whether one top-level CLI command should trigger DB readiness.

    Args:
        command_name: First subcommand chosen by Click, if any.

    Returns:
        ``True`` for DB-using top-level commands, otherwise ``False``.

    """
    return command_name is not None and command_name not in DATABASE_GATE_SKIP_COMMANDS


def _prompt_backup_cleanup(text: str) -> str:
    """
    Read one backup-cleanup confirmation without forcing a re-prompt.

    Args:
        text: Full locked prompt text, including the ``[y/N]`` suffix.

    Returns:
        Raw trimmed user response, or an empty string when Enter is pressed.

    Side Effects:
        Writes the prompt once to stdout and reads a single stdin line.

    """
    click.echo(text, nl=False)
    response = click.get_text_stream("stdin").readline()
    click.echo()
    return response.rstrip("\r\n")


def _run_database_readiness_gate(ctx: click.Context) -> None:
    """
    Run the canonical DB startup gate once for DB-using command trees.

    Args:
        ctx: Root Click context for the current CLI invocation.

    Side Effects:
        Runs startup migration checks before DB-using commands are dispatched.

    Raises:
        click.ClickException: Startup migration work failed or requires rebuild.

    """
    if ctx.obj.get("_db_ready_checked"):
        return
    ctx.obj["_db_ready_checked"] = True

    raw_argv = ctx.meta.get("raw_argv", ())
    if ctx.resilient_parsing or any(arg in {"--help", "-h"} for arg in raw_argv):
        return
    if not should_run_database_readiness_gate(ctx.invoked_subcommand):
        return

    settings: Settings | None = ctx.obj.get("settings")
    if settings is None:
        return

    try:
        ensure_database_ready(
            settings=settings,
            interactive=sys.stdin.isatty() and sys.stdout.isatty(),
            echo=click.echo,
            prompt=_prompt_backup_cleanup,
        )
    except LegacyDatabaseResetRequired as exc:
        raise click.ClickException(str(exc)) from exc
    except DatabaseMigrationError as exc:
        recipe = "\n".join(exc.rebuild_instructions)
        msg = f"{exc}\n\n{exc.traceback_text}\nRebuild commands:\n{recipe}"
        raise click.ClickException(msg) from exc


@click.group(cls=_RootCLIGroup)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress all output except errors")
@click.option(
    "--config-file", type=click.Path(exists=True), help="Custom configuration file path"
)
@click.option(
    "--output",
    type=click.Choice(["json", "table", "text"]),
    default="table",
    help="Output format",
)
@click.pass_context
def cli(
    ctx: click.Context, verbose: bool, quiet: bool, config_file: str | None, output: str
):
    """
    Wyrdcraeft command line interface.

    Args:
        ctx: Root Click context for the current CLI invocation.
        verbose: Whether verbose mode is enabled.
        quiet: Whether normal output should be suppressed.
        config_file: Optional explicit configuration file path.
        output: Output rendering format name.

    """
    # Ensure context object exists
    ctx.ensure_object(dict)

    # Store global options in context
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    ctx.obj["output"] = output
    ctx.obj["config_file"] = config_file

    if config_file:
        # This will be picked up by the Settings class's
        # settings_customise_sources method
        os.environ["WYRDCRAEFT_CONFIG_FILE"] = config_file

    # Load settings
    try:
        settings = Settings()
        ctx.obj["settings"] = settings
        _configure_logging(settings)
    except Exception as e:  # noqa: BLE001
        print_error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Reset global console state on every invocation so one quiet run does not
    # leak into later commands in the same Python process.
    console.quiet = quiet
    _run_database_readiness_gate(ctx)


@cli.command(name="version", help="Print some version info.")
def version() -> None:
    """
    Print the some version info of this package,
    """
    table = Table(title="wyrdcraeft Version Info")
    table.add_column("Package", justify="left", style="cyan", no_wrap=True)
    table.add_column("Version", justify="left", style="yellow", no_wrap=True)

    table.add_row("wyrdcraeft", str(wyrdcraeft.__version__))
    table.add_row("click", str(Distribution.from_name("click").version))
    table.add_row("rich", str(Distribution.from_name("rich").version))
    table.add_row("pydantic", str(Distribution.from_name("pydantic").version))

    console.print(table)


from .diacritic import diacritic_group
from .diacritic_disambiguate import diacritic_disambiguate
from .dictionary import dictionary_group
from .morphology import morphology_group
from .ocr import ocr_group
from .settings import settings_group
from .source import reading_group

cli.add_command(settings_group)
cli.add_command(diacritic_group)
cli.add_command(reading_group)
cli.add_command(morphology_group)
cli.add_command(dictionary_group)
cli.add_command(ocr_group)
diacritic_group.add_command(diacritic_disambiguate)
