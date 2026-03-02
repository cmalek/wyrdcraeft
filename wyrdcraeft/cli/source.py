from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)

from ..ingest.pipeline import DocumentIngestor
from ..models import TextMetadata
from ..services.markup import DiacriticRestorer
from ..settings import Settings  # noqa: TC001
from .utils import console, print_error, print_info


@click.group(name="source")
@click.pass_context
def reading_group(ctx: click.Context) -> None:
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
) -> None:
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

        def progress_callback(
            current: int, total: int, message: str | None = None
        ) -> None:
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


def _mark_diacritics_derived_path(source: Path, infix: str) -> Path:
    """Derive output path from source: stem + infix + suffix (e.g. poem.fixed.txt)."""
    return source.parent / (source.stem + infix + source.suffix)


@reading_group.command(
    name="mark-diacritics",
    help="Restore macrons and dot diacritics in an Old English text file.",
)
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.argument(
    "output",
    required=False,
    default=None,
    type=click.Path(path_type=Path),
)
@click.option(
    "--ambiguities-output",
    type=click.Path(path_type=Path),
    default=None,
    help="Ambiguity report JSON path. Default: stem.anomalies + input extension.",
)
@click.option(
    "--unknown-output",
    type=click.Path(path_type=Path),
    default=None,
    help="Unrecognized-words JSON path. Default: stem.unknown + input extension.",
)
def reading_mark_diacritics(
    source: Path,
    output: Path | None,
    ambiguities_output: Path | None,
    unknown_output: Path | None,
) -> None:
    """
    Restore diacritics in a source text and emit ambiguity and unknown-word reports.

    When output paths are omitted, they default to the input directory using
    the input filename stem and extension (e.g. poem.txt -> poem.fixed.txt,
    poem.anomalies.txt, poem.unknown.txt).

    Args:
        source: Input text file path.
        output: Marked output text file path. Default: stem + '.fixed' + extension.
        ambiguities_output: Output path for ambiguity report JSON.
        unknown_output: Output path for unrecognized-words report JSON.

    """
    resolved_output = output if output is not None else _mark_diacritics_derived_path(
        source, ".fixed"
    )
    resolved_ambiguities = (
        ambiguities_output
        if ambiguities_output is not None
        else _mark_diacritics_derived_path(source, ".anomalies")
    )
    resolved_unknown = (
        unknown_output
        if unknown_output is not None
        else _mark_diacritics_derived_path(source, ".unknown")
    )

    try:
        text = source.read_text(encoding="utf-8")
    except OSError as e:
        msg = f"Failed to read source file {source}: {e}"
        raise click.ClickException(msg) from e

    restorer = DiacriticRestorer()
    result = restorer.restore_text(text)

    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    resolved_output.write_text(result.marked_text, encoding="utf-8")

    resolved_ambiguities.parent.mkdir(parents=True, exist_ok=True)
    resolved_ambiguities.write_text(
        json.dumps(
            [item.model_dump() for item in result.ambiguities],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    resolved_unknown.parent.mkdir(parents=True, exist_ok=True)
    resolved_unknown.write_text(
        json.dumps(
            [item.model_dump() for item in result.unknowns],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print_info(
        f"Successfully restored diacritics for {source} -> {resolved_output}. "
        f"Ambiguities: {len(result.ambiguities)}, Unknowns: {len(result.unknowns)}"
    )
