from __future__ import annotations

import logging
import os
import sys
from importlib.metadata import Distribution

import click
from rich.table import Table

import wyrdcraeft

from ..settings import Settings
from .utils import console, print_error


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


@click.group()
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

    # Configure console based on quiet mode
    if quiet:
        console.quiet = True


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
from .morphology import morphology_group
from .settings import settings_group
from .source import reading_group

cli.add_command(settings_group)
cli.add_command(diacritic_group)
cli.add_command(reading_group)
cli.add_command(morphology_group)
diacritic_group.add_command(diacritic_disambiguate)
