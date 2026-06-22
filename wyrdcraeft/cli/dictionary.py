"""Bosworth-Toller dictionary indexing CLI commands."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import click

from wyrdcraeft.paths import resolve_dictionary_index_db_path
from wyrdcraeft.services.dictionary.pipeline import BTIndexPipeline
from wyrdcraeft.services.dictionary.sinks import BTSqliteSink

if TYPE_CHECKING:
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
@click.pass_context
def index_bt(  # noqa: PLR0913
    ctx: click.Context,
    source: Path,
    index_db: Path | None,
    index_dir: Path | None,
    attach_morphology_db: Path | None,
    report: Path | None,
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

    pipeline = BTIndexPipeline()
    sqlite_sink: BTSqliteSink | None = None
    try:
        sqlite_sink = BTSqliteSink(resolved_index_db, attach_mode=attach_mode)
        index_report = pipeline.run(source.resolve(), sqlite_sink)
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
            ]
        )
    )
