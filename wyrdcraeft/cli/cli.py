from __future__ import annotations

import json
import logging
import os
import sys
from importlib.metadata import Distribution
from pathlib import Path

import click
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.table import Table

import wyrdcraeft

from ..ingest.pipeline import DocumentIngestor
from ..models import TextMetadata
from ..services.markup import DiacriticRestorer
from ..settings import Settings
from .utils import console, print_error, print_info


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


@cli.group(name="source")
@click.pass_context
def reading_group(ctx: click.Context):
    """
    OE Source text-related commands.
    """


@reading_group.command(name="convert", help="Convert a source document to JSON.")
@click.argument("source", type=str)
@click.argument("output", type=click.Path(path_type=Path))
@click.option(
    "--use-llm/--no-use-llm",
    is_flag=True,
    default=False,
    show_default=True,
    help="Use LLM for extraction",
)
@click.option(
    "--llm-model",
    type=click.Choice(["qwen2.5:14b-instruct", "gpt-4o", "gemini-3-flash-preview"]),
    help="LLM model ID",
)
@click.option("--llm-temperature", type=float, help="LLM temperature")
@click.option("--llm-max-tokens", type=int, help="LLM max tokens")
@click.option("--llm-timeout", type=int, help="LLM timeout in seconds")
@click.option("--title", type=str, help="Title of the text")
@click.pass_context
def reading_convert(  # noqa: PLR0913
    ctx: click.Context,
    source: str,
    output: Path,
    use_llm: bool,
    llm_model: str | None,
    llm_temperature: float | None,
    llm_max_tokens: int | None,
    llm_timeout: int | None,
    title: str | None,
):
    """
    Convert a source document to JSON.
    """
    settings: Settings = ctx.obj["settings"]
    source_ref: str | Path = source
    if not source.startswith(("http://", "https://")):
        source_ref = Path(source)
        if not source_ref.exists():
            msg = f"Source file not found: {source_ref}"
            raise click.ClickException(msg)

    # Override settings with flags
    if llm_model:
        settings.llm_model_id = llm_model
    if llm_temperature is not None:
        settings.llm_temperature = llm_temperature
    if llm_max_tokens is not None:
        settings.llm_max_tokens = llm_max_tokens
    if llm_timeout is not None:
        settings.llm_timeout_s = llm_timeout

    metadata = TextMetadata(
        title=title
        or (source_ref.stem if isinstance(source_ref, Path) else source_ref),
        source=str(source_ref),
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("{task.fields[phase]}"),
        console=console,
    ) as progress:
        task = progress.add_task("Processing...", total=1, phase="")

        def progress_callback(current: int, total: int, message: str | None = None):
            phase_label = ""
            if message:
                m_lower = message.lower()
                if any(
                    x in m_lower
                    for x in [
                        "loading",
                        "normalizing",
                        "filtering",
                        "parsing",
                        "pre-parsing",
                    ]
                ):
                    phase_label = "[bold blue]Analyzing[/bold blue]"
                elif "found" in m_lower and "chunks" in m_lower:
                    phase_label = "[bold cyan]Planning[/bold cyan]"
                elif "extracting" in m_lower or "extraction" in m_lower:
                    phase_label = "[bold green]Extracting[/bold green]"
                elif "complete" in m_lower:
                    phase_label = "[bold green]Complete[/bold green]"
                else:
                    phase_label = f"[dim]{message}[/dim]"

            progress.update(
                task,
                total=total,
                completed=current,
                description=message or "Processing...",
                phase=f" {phase_label}" if phase_label else "",
            )

        try:
            doc = DocumentIngestor().ingest(
                source_path=(
                    source_ref
                    if isinstance(source_ref, Path)
                    else Path(source_ref)
                ),
                metadata=metadata,
                use_llm=use_llm,
                progress_callback=progress_callback,
                llm_config=settings.llm_config,
            )

            output.write_text(doc.model_dump_json(indent=2), encoding="utf-8")

            if not ctx.obj.get("quiet"):
                print_info(f"Successfully converted {source_ref} to {output}")
        except Exception as e:
            if ctx.obj.get("verbose"):
                raise
            print_error(f"Conversion failed: {e}")
            sys.exit(1)


@reading_group.command(
    name="mark-diacritics",
    help="Restore macrons and dot diacritics in an Old English text file.",
)
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.argument("output", type=click.Path(path_type=Path))
@click.option(
    "--ambiguities-output",
    required=True,
    type=click.Path(path_type=Path),
    help="Output path for ambiguity report JSON.",
)
def reading_mark_diacritics(
    source: Path,
    output: Path,
    ambiguities_output: Path,
) -> None:
    """
    Restore diacritics in a source text and emit ambiguity report JSON.

    Args:
        source: Input text file path.
        output: Marked output text file path.
        ambiguities_output: Output path for ambiguity report JSON.

    """
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as e:
        msg = f"Failed to read source file {source}: {e}"
        raise click.ClickException(msg) from e

    restorer = DiacriticRestorer()
    result = restorer.restore_text(text)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result.marked_text, encoding="utf-8")

    ambiguities_output.parent.mkdir(parents=True, exist_ok=True)
    ambiguities_output.write_text(
        json.dumps(
            [item.model_dump() for item in result.ambiguities],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print_info(
        f"Successfully restored diacritics for {source} -> {output}. "
        f"Ambiguities: {len(result.ambiguities)}"
    )


@cli.command(name="convert", help="Convert a source document to JSON.")
@click.argument("source", type=str)
@click.argument("output", type=click.Path(path_type=Path))
@click.option(
    "--use-llm/--no-use-llm",
    is_flag=True,
    default=True,
    show_default=True,
    help="Use LLM for extraction",
)
@click.option(
    "--llm-model",
    type=click.Choice(["qwen2.5:14b-instruct", "gpt-4o", "gemini-3-flash-preview"]),
    help="LLM model ID",
)
@click.option("--llm-temperature", type=float, help="LLM temperature")
@click.option("--llm-max-tokens", type=int, help="LLM max tokens")
@click.option("--llm-timeout", type=int, help="LLM timeout in seconds")
@click.option("--title", type=str, help="Title of the text")
@click.pass_context
def convert(  # noqa: PLR0913
    ctx: click.Context,
    source: str,
    output: Path,
    use_llm: bool,
    llm_model: str | None,
    llm_temperature: float | None,
    llm_max_tokens: int | None,
    llm_timeout: int | None,
    title: str | None,
) -> None:
    """
    Backward-compatible top-level alias for ``source convert``.
    """
    ctx.invoke(
        reading_convert,
        source=source,
        output=output,
        use_llm=use_llm,
        llm_model=llm_model,
        llm_temperature=llm_temperature,
        llm_max_tokens=llm_max_tokens,
        llm_timeout=llm_timeout,
        title=title,
    )
