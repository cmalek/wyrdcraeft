from __future__ import annotations

import json

import click
from rich.table import Table

from ..settings import Settings
from .utils import console, print_info


@click.group(name="settings", invoke_without_command=True)
@click.pass_context
def settings_group(ctx: click.Context) -> None:
    """
    Settings-related commands.
    """
    if ctx.invoked_subcommand is None:
        ctx.invoke(show_settings)


@settings_group.command(name="show", help="Show the current settings.")
@click.pass_context
def show_settings(ctx: click.Context) -> None:
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
def create_settings(ctx: click.Context) -> None:
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
