from __future__ import annotations

import json
import os
import sys
from importlib.metadata import Distribution

import click
from rich.table import Table

import oe_json_extractor

from ..settings import Settings
from .utils import console, print_error, print_info


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
    oe_json_extractor command line interface.
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
        os.environ["OE_JSON_EXTRACTOR_CONFIG_FILE"] = config_file

    # Load settings
    try:
        settings = Settings()
        ctx.obj["settings"] = settings
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
    table = Table(title="oe_json_extractor Version Info")
    table.add_column("Package", justify="left", style="cyan", no_wrap=True)
    table.add_column("Version", justify="left", style="yellow", no_wrap=True)

    table.add_row("oe_json_extractor", str(oe_json_extractor.__version__))
    table.add_row("click", str(Distribution.from_name("click").version))
    table.add_row("rich", str(Distribution.from_name("rich").version))
    table.add_row("pydantic", str(Distribution.from_name("pydantic").version))

    console.print(table)


@cli.group(name="settings", invoke_without_command=True)
@click.pass_context
def settings_group(ctx: click.Context):
    """
    Settings-related commands.
    """
    if ctx.invoked_subcommand is None:
        ctx.invoke(show_settings)


@settings_group.command(name="show", help="Show the current settings.")
@click.pass_context
def show_settings(ctx: click.Context):
    """
    Settings-related commands.
    """
    output_format = ctx.obj.get("output", "table")
    verbose = ctx.obj.get("verbose", False)
    settings = ctx.obj.get("settings")

    if output_format == "json":
        click.echo(json.dumps(settings.model_dump()))
    elif output_format == "table":
        table = Table(title="Settings", show_header=True, header_style="bold magenta")
        table.add_column("Setting Name", style="cyan")
        table.add_column("Value", style="green")

        for setting_name, setting_value in settings.model_dump().items():
            table.add_row(setting_name, str(setting_value))

        console.print(table)
    else:  # text format
        for setting_name, setting_value in settings.model_dump().items():
            click.echo(f"{setting_name}: {setting_value}")
            click.echo()

    if verbose:
        print_info(f"Found {len(settings.model_dump())} settings")


@settings_group.command(name="create", help="Create a new settings file.")
@click.pass_context
def create_settings(ctx: click.Context):
    """
    Create a new settings file.
    """
    settings_path = Settings.default_settings_path()
    settings_path.touch()

    # Write all the non-frozen settings to the file with the default TOML format
    # and our Settings default values
    with settings_path.open("w", encoding="utf-8") as f:
        f.write(Settings().model_dump_json(indent=2))

    print_info(f"Settings file created at {settings_path}")
    if ctx.obj.get("verbose"):
        # print a table with the settings and their values
        table = Table(title="Settings", show_header=True, header_style="bold magenta")
        table.add_column("Setting Name", style="cyan")
        table.add_column("Value", style="green")

        for setting_name, setting_value in Settings().model_dump().items():
            # skip the frozen settings
            if setting_name in ["app_name", "app_version"]:
                continue
            table.add_row(setting_name, str(setting_value))

        console.print(table)
