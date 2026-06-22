"""Bosworth-Toller dictionary indexing CLI commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import click

from wyrdcraeft.paths import resolve_dictionary_index_db_path
from wyrdcraeft.services.dictionary.llm_fix_pass import (
    DEFAULT_OLLAMA_ENDPOINT,
    BTLLMFixPass,
)
from wyrdcraeft.services.dictionary.pipeline import BTIndexPipeline
from wyrdcraeft.services.dictionary.query import BTQueryService, entry_to_dict
from wyrdcraeft.services.dictionary.sinks import BTSqliteSink
from wyrdcraeft.services.markup import normalize_old_english

if TYPE_CHECKING:
    from wyrdcraeft.models.dictionary import BTConsolidatedEntry
    from wyrdcraeft.settings import Settings


def _default_source_path() -> Path:
    """
    Resolve the default Bosworth-Toller source file path.

    Returns:
        Path to ``data/oe_bt.txt`` relative to the current working directory.

    """
    return Path("data/oe_bt.txt")


@click.group(
    name="dictionary",
    help="Bosworth-Toller dictionary indexing commands.",
)
def dictionary_group() -> None:
    """Dictionary command group."""


@dictionary_group.command(
    name="index-bt",
    help="Build the Bosworth-Toller dictionary SQLite index from oe_bt.txt.",
)
@click.option(
    "--source",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=_default_source_path,
    show_default="data/oe_bt.txt",
    help="Bosworth-Toller source file to index.",
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
    help="Directory for dictionary.sqlite3 (overrides the OS app-data default).",
)
@click.option(
    "--attach-morphology-db",
    type=click.Path(path_type=Path),
    default=None,
    help=(
        "Write bt_* tables into an existing morphology.sqlite3 without modifying "
        "forms (mutually exclusive with --index-db and --index-dir)."
    ),
)
@click.option(
    "--report",
    type=click.Path(path_type=Path),
    default=None,
    help="Optional JSON report path with parse/merge statistics.",
)
@click.option(
    "--llm-fix-pass",
    is_flag=True,
    default=False,
    help="Re-parse warning lines with a local LLM before merge.",
)
@click.option(
    "--llm-model",
    default="qwen2.5:14b-instruct",
    show_default=True,
    help="Ollama model for --llm-fix-pass.",
)
@click.option(
    "--llm-endpoint",
    default=DEFAULT_OLLAMA_ENDPOINT,
    show_default=True,
    help="Ollama /api/generate endpoint for --llm-fix-pass.",
)
@click.option(
    "--warnings-file",
    type=click.Path(path_type=Path),
    default=None,
    help="Optional parse_warnings.jsonl path (default: alongside index DB).",
)
@click.pass_context
def index_bt(  # noqa: PLR0913
    ctx: click.Context,
    source: Path,
    index_db: Path | None,
    index_dir: Path | None,
    attach_morphology_db: Path | None,
    report: Path | None,
    llm_fix_pass: bool,
    llm_model: str,
    llm_endpoint: str,
    warnings_file: Path | None,
) -> None:
    """
    Parse, merge, and persist Bosworth-Toller dictionary entries to SQLite.

    Args:
        ctx: Click context carrying loaded settings and global flags.
        source: Bosworth-Toller source file to index.
        index_db: Optional SQLite index output file path override.
        index_dir: Optional SQLite index output directory override.
        attach_morphology_db: Optional morphology SQLite file for attach mode.
        report: Optional JSON statistics report path.
        llm_fix_pass: When true, repair warning lines with a local LLM.
        llm_model: Ollama model identifier for the repair pass.
        llm_endpoint: Ollama generate endpoint URL.
        warnings_file: Optional parse warnings JSONL output path.

    Side Effects:
        Reads the source dictionary file and writes ``dictionary.sqlite3`` or
        attaches ``bt_*`` tables to ``morphology.sqlite3``.

    Raises:
        click.ClickException: Source reading or SQLite writing fails.

    """
    if attach_morphology_db is not None and (
        index_db is not None or index_dir is not None
    ):
        msg = (
            "Provide either --attach-morphology-db or one of --index-db / "
            "--index-dir, not both."
        )
        raise click.ClickException(msg)

    settings: Settings | None = ctx.obj.get("settings")
    app_data_dir = settings.app_data_dir if settings is not None else None
    if attach_morphology_db is not None:
        resolved_index_db = attach_morphology_db.expanduser().resolve()
        attach_mode = True
    else:
        resolved_index_db = resolve_dictionary_index_db_path(
            index_db=index_db,
            index_dir=index_dir,
            app_data_dir=app_data_dir,
        )
        attach_mode = False

    resolved_warnings_file = (
        warnings_file.expanduser().resolve()
        if warnings_file is not None
        else resolved_index_db.parent / "parse_warnings.jsonl"
    )
    llm_repair = (
        BTLLMFixPass(model=llm_model, endpoint=llm_endpoint)
        if llm_fix_pass
        else None
    )

    pipeline = BTIndexPipeline()
    sqlite_sink: BTSqliteSink | None = None
    try:
        sqlite_sink = BTSqliteSink(resolved_index_db, attach_mode=attach_mode)
        index_report = pipeline.run(
            source.resolve(),
            sqlite_sink,
            warnings_path=resolved_warnings_file,
            llm_fix_pass=llm_repair,
        )
    except OSError as exc:
        msg = f"Failed to index dictionary source {source}: {exc}"
        raise click.ClickException(msg) from exc
    finally:
        if sqlite_sink is not None:
            sqlite_sink.close()

    if report is not None:
        index_report.write_json(report.resolve())

    click.echo(
        "\n".join(
            [
                "Dictionary index complete.",
                f"source={source.resolve()}",
                f"index_db={resolved_index_db}",
                f"attach_mode={'yes' if attach_mode else 'no'}",
                f"entries_written={index_report.merged}",
                f"senses_written={index_report.senses_written}",
                f"variants_written={index_report.variants_written}",
                f"parsed={index_report.parsed}",
                f"skipped={index_report.skipped}",
                f"warnings_file={resolved_warnings_file}",
                f"llm_fix_pass={'yes' if llm_fix_pass else 'no'}",
            ]
        )
    )


def _format_sense_label(label: str) -> str:
    """
    Render one sense label with trailing punctuation for text output.

    Args:
        label: Stored sense label such as ``I`` or ``II``.

    Returns:
        Display label such as ``I.`` when punctuation is missing.

    """
    stripped = label.strip()
    if not stripped:
        return ""
    if stripped.endswith("."):
        return stripped
    return f"{stripped}."


def _format_entry_text(
    entry: BTConsolidatedEntry,
    *,
    lookup_key: str,
) -> str:
    """
    Render one consolidated dictionary entry as human-readable text.

    Args:
        entry: Consolidated dictionary record.

    Keyword Args:
        lookup_key: Normalized lookup key used for the query.

    Returns:
        Multi-line text block without attestations or editorial refs.

    """
    if lookup_key != entry.norm_key:
        lemma_line = f"Lemma: {lookup_key} ({entry.headword_macronized})"
    else:
        lemma_line = f"Lemma: {entry.headword_macronized}"

    pos_bits = [f"POS: {entry.pos.value}"]
    if entry.genders:
        gender_text = ", ".join(gender.value for gender in entry.genders)
        pos_bits.append(f"Gender: {gender_text}")

    lines = [lemma_line, "  ".join(pos_bits), "Senses:"]
    for sense in entry.senses:
        label = _format_sense_label(sense.sense_label)
        prefix = f"  {label} " if label else "  "
        lines.append(f"{prefix}{sense.gloss_en}".rstrip())

    if entry.etymology.strip():
        lines.append(f"Etymology: {entry.etymology.strip()}")

    variant_forms = [entry.headword_macronized, *entry.variants]
    deduped_variants: list[str] = []
    seen: set[str] = set()
    for form in variant_forms:
        if form in seen:
            continue
        seen.add(form)
        deduped_variants.append(form)
    if deduped_variants:
        lines.append(f"Variants: {', '.join(deduped_variants)}")

    return "\n".join(lines)


@dictionary_group.command(
    name="lookup",
    help="Look up consolidated Bosworth-Toller dictionary entries.",
)
@click.argument("lemma")
@click.option(
    "--pos",
    type=str,
    default=None,
    help="Optional POS filter (for example noun, adv, verb).",
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
    help="Directory for dictionary.sqlite3 (overrides the OS app-data default).",
)
@click.option(
    "--json-output/--no-json-output",
    default=False,
    show_default=True,
    help="Render query output as JSON.",
)
@click.pass_context
def lookup(  # noqa: PLR0913
    ctx: click.Context,
    lemma: str,
    pos: str | None,
    index_db: Path | None,
    index_dir: Path | None,
    json_output: bool,
) -> None:
    """
    Query consolidated dictionary entries by lemma or variant spelling.

    Args:
        ctx: Click context carrying loaded settings and global flags.
        lemma: Headword or alternate spelling to resolve.
        pos: Optional POS filter.
        index_db: Optional SQLite index file path override.
        index_dir: Optional SQLite index directory override.
        json_output: When true, print JSON instead of formatted text.

    Side Effects:
        Reads the dictionary SQLite index and writes entries to stdout.

    Raises:
        click.ClickException: The index database cannot be opened.

    """
    settings: Settings | None = ctx.obj.get("settings")
    app_data_dir = settings.app_data_dir if settings is not None else None
    resolved_index_db = resolve_dictionary_index_db_path(
        index_db=index_db,
        index_dir=index_dir,
        app_data_dir=app_data_dir,
    )
    if not resolved_index_db.is_file():
        msg = f"Dictionary index not found: {resolved_index_db}"
        raise click.ClickException(msg)

    lookup_key = normalize_old_english(lemma) or ""
    query_service = BTQueryService(resolved_index_db)
    try:
        entries = query_service.lookup_lemma(lemma, pos=pos)
    except OSError as exc:
        msg = f"Failed to query dictionary index {resolved_index_db}: {exc}"
        raise click.ClickException(msg) from exc
    finally:
        query_service.close()

    if json_output:
        click.echo(
            json.dumps(
                [entry_to_dict(entry) for entry in entries],
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if not entries:
        click.echo(f"No dictionary entries found for {lemma!r}.")
        return

    rendered_blocks = [
        _format_entry_text(entry, lookup_key=lookup_key) for entry in entries
    ]
    click.echo("\n\n".join(rendered_blocks))
