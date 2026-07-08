"""Bosworth-Toller dictionary indexing CLI commands."""

from __future__ import annotations

import json
import sqlite3
from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING

import click
from sqlalchemy.exc import SQLAlchemyError

from wyrdcraeft.db.runtime import create_engine
from wyrdcraeft.paths import get_canonical_db_path
from wyrdcraeft.services.dictionary.browse_tui import (
    DictionaryBrowseDataError,
    run_dictionary_browse,
)
from wyrdcraeft.services.dictionary.build_pipeline import (
    DictionaryBuildPipeline,
    MorphBuildOptions,
)
from wyrdcraeft.services.dictionary.llm_fix_pass import (
    DEFAULT_OLLAMA_ENDPOINT,
    BTLLMFixPass,
)
from wyrdcraeft.services.dictionary.query import BTQueryService, entry_to_dict
from wyrdcraeft.services.dictionary.resources import (
    default_bt_source_path,
    default_wright_source_path,
)
from wyrdcraeft.services.markup import normalize_old_english
from wyrdcraeft.services.morphology.catalog.wright_audit import (
    WrightAuditService,
    format_wright_audit_text,
)
from wyrdcraeft.services.morphology.catalog.wright_text import WrightSectionTextIngester
from wyrdcraeft.services.morphology.reference_snapshots import (
    format_reference_snapshot_result,
    generate_reference_snapshots,
)

if TYPE_CHECKING:
    from wyrdcraeft.models.dictionary import BTConsolidatedEntry
    from wyrdcraeft.settings import Settings


def _default_source_path() -> Path:
    """
    Resolve the default Bosworth-Toller source file path.

    Returns:
        Path to the packaged ``oe_bt.txt`` dictionary source file.

    """
    return default_bt_source_path()


def _default_morphology_data_dir() -> Path:
    """
    Resolve the packaged default morphology data directory.

    Note:
        Uses the bundled morphology dataset described by
        ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
        In plain terms, this picks the default grammar tables used for all Parts
        of Speech (verbs, nouns, adjectives, adverbs, and numerals).

    Returns:
        Directory containing bundled morphology source files.

    """
    return Path(str(resources.files("wyrdcraeft").joinpath("etc/morphology")))


def _resolve_morphology_input_paths(
    *,
    data_dir: Path,
    dictionary: Path | None,
    manual_forms: Path | None,
    verbal_paradigms: Path | None,
    prefixes: Path | None,
) -> tuple[Path, Path, Path, Path]:
    """
    Resolve morphology input file paths using CLI overrides or data-dir defaults.

    Note:
        This command wiring follows the morphology data model aligned with
        ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
        In plain terms, it chooses the input files for all Parts of Speech.

    Keyword Args:
        data_dir: Base directory containing bundled morphology source files.
        dictionary: Optional explicit dictionary file path.
        manual_forms: Optional explicit manual forms file path.
        verbal_paradigms: Optional explicit verbal paradigms file path.
        prefixes: Optional explicit prefixes file path.

    Returns:
        Tuple of resolved paths in dictionary/manual/paradigms/prefixes order.

    """
    resolved_dictionary = dictionary or (data_dir / "dict_adj-vb-part-num-adv-noun.txt")
    resolved_manual = manual_forms or (data_dir / "manual_forms.txt")
    resolved_para = verbal_paradigms or (data_dir / "para_vb.txt")
    resolved_prefixes = prefixes or (data_dir / "prefixes.txt")
    return resolved_dictionary, resolved_manual, resolved_para, resolved_prefixes


def _validate_morphology_inputs(paths: tuple[Path, Path, Path, Path]) -> None:
    """
    Ensure required morphology input files exist.

    Note:
        The required files contain paradigm data aligned with
        ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
        In plain terms, this ensures every Part of Speech has required source data.

    Args:
        paths: Resolved dictionary/manual/paradigms/prefixes paths.

    Raises:
        click.ClickException: A required file path is missing.

    """
    labels = ("dictionary", "manual forms", "verbal paradigms", "prefixes")
    for label, path in zip(labels, paths, strict=True):
        if not path.exists():
            msg = (
                f"Missing {label} file: {path}. "
                "Provide an explicit path via command flags or --data-dir."
            )
            raise click.ClickException(msg)


def _count_table_rows(db_path: Path, table_name: str) -> int:
    """
    Count rows in one SQLite table when it exists.

    Args:
        db_path: SQLite database path to inspect.
        table_name: Table whose rows should be counted.

    Returns:
        Row count, or ``0`` when the table is missing.

    """
    with sqlite3.connect(str(db_path)) as connection:
        try:
            row = connection.execute(
                f"SELECT COUNT(*) FROM {table_name}"  # noqa: S608
            ).fetchone()
        except sqlite3.OperationalError:
            return 0
    return int(row[0]) if row is not None else 0


def _missing_canonical_index_message(db_path: Path) -> str:
    """
    Build the CLI error shown when the canonical database is absent.

    Args:
        db_path: Resolved canonical SQLite path that was not found.

    Returns:
        User-facing error message with recovery steps.

    """
    return (
        f"Canonical database not found: {db_path}. "
        "Run a DB-using command to trigger startup readiness, then "
        "`wyrdcraeft dictionary build` to populate it."
    )


def _require_non_empty_tables(
    db_path: Path,
    table_names: tuple[str, ...],
    *,
    recovery_hint: str,
) -> None:
    """
    Fail when any required canonical source table is missing or empty.

    Args:
        db_path: Canonical SQLite database path to inspect.
        table_names: Required table names.

    Keyword Args:
        recovery_hint: User-facing command hint for rebuilding the source tables.

    Raises:
        click.ClickException: The required table is absent or has no rows.

    """
    missing = [
        table_name
        for table_name in table_names
        if _count_table_rows(db_path, table_name) == 0
    ]
    if not missing:
        return
    missing_text = ", ".join(missing)
    message = (
        f"Canonical database {db_path} is missing required source tables: "
        f"{missing_text}. {recovery_hint}"
    )
    raise click.ClickException(message)


@click.group(
    name="dictionary",
    help="Bosworth-Toller dictionary indexing commands.",
)
def dictionary_group() -> None:
    """Dictionary command group."""


@dictionary_group.command(
    name="build",
    help="Build the Bosworth-Toller dictionary SQLite index from oe_bt.txt.",
)
@click.option(
    "--source",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=_default_source_path,
    show_default="wyrdcraeft/etc/dictionary/oe_bt.txt",
    help="Bosworth-Toller source file to index.",
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
@click.option(
    "--with-morphology",
    is_flag=True,
    default=False,
    help="Force morphology regeneration after rebuilding dictionary entries.",
)
@click.option(
    "--data-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Directory containing default morphology data files.",
)
@click.option(
    "--dictionary",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Morphology dictionary file path.",
)
@click.option(
    "--manual-forms",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Manual morphology forms file path.",
)
@click.option(
    "--verbal-paradigms",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Verbal morphology paradigms file path.",
)
@click.option(
    "--prefixes",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Morphology prefixes file path.",
)
@click.option(
    "--output",
    default=None,
    type=click.Path(path_type=Path),
    help="Optional TSV output file path for regenerated morphology forms.",
)
@click.option(
    "--limit",
    default=None,
    type=int,
    help="Limit number of words processed during morphology regeneration.",
)
@click.option(
    "--progress-every",
    type=int,
    default=None,
    metavar="INTEGER",
    help=(
        "Update visible lemma banner every N processed words during "
        "morphology regeneration."
    ),
)
@click.option(
    "--enable-r-stem-nouns",
    is_flag=True,
    default=False,
    help=(
        "Enable opt-in non-parity r-stem noun generation during "
        "morphology regeneration."
    ),
)
@click.option(
    "--full/--no-full",
    default=False,
    show_default=True,
    help="Generate full dictionary output during morphology regeneration.",
)
@click.option(
    "--profile",
    is_flag=True,
    default=False,
    help="Print stage and SQLite timing summary when morphology regeneration runs.",
)
@click.option(
    "--refresh-catalog",
    is_flag=True,
    default=False,
    help="Re-load Wright morph catalog before morphology regeneration.",
)
@click.pass_context
def build(  # noqa: PLR0913
    ctx: click.Context,
    source: Path,
    report: Path | None,
    llm_fix_pass: bool,
    llm_model: str,
    llm_endpoint: str,
    warnings_file: Path | None,
    with_morphology: bool,
    data_dir: Path | None,
    dictionary: Path | None,
    manual_forms: Path | None,
    verbal_paradigms: Path | None,
    prefixes: Path | None,
    output: Path | None,
    limit: int | None,
    progress_every: int | None,
    enable_r_stem_nouns: bool,
    full: bool,
    profile: bool,
    refresh_catalog: bool,
) -> None:
    """
    Parse, merge, and persist Bosworth-Toller dictionary entries to SQLite.

    Args:
        ctx: Click context carrying loaded settings and global flags.
        source: Bosworth-Toller source file to index.
        report: Optional JSON statistics report path.
        llm_fix_pass: When true, repair warning lines with a local LLM.
        llm_model: Ollama model identifier for the repair pass.
        llm_endpoint: Ollama generate endpoint URL.
        warnings_file: Optional parse warnings JSONL output path.
        with_morphology: Forces morphology regeneration after dictionary rebuild.
        data_dir: Optional base directory for default morphology files.
        dictionary: Optional morphology dictionary file path override.
        manual_forms: Optional manual-forms file path override.
        verbal_paradigms: Optional verbal-paradigms file path override.
        prefixes: Optional prefixes file path override.
        output: Optional TSV output file path for regenerated morphology forms.
        limit: Optional cap for non-full morphology generation.
        progress_every: Optional visible-lemma update cadence override.
        enable_r_stem_nouns: Enables opt-in non-parity r-stem noun generation.
        full: Enables full-dictionary morphology generation mode.
        profile: Enables stderr timing summary output when morphology runs.
        refresh_catalog: Reloads the Wright morph catalog before morphology runs.

    Side Effects:
        Rebuilds canonical ``bt_*`` tables and optionally regenerates linked
        morphology rows inside ``wyrdcraeft.sqlite3``.

    Raises:
        click.ClickException: Source reading or SQLite writing fails.

    """
    settings: Settings | None = ctx.obj.get("settings")
    resolved_index_db = get_canonical_db_path(
        app_data_dir=settings.app_data_dir if settings is not None else None
    )

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
    morph_options = MorphBuildOptions(
        limit=limit,
        full=full,
        data_dir=data_dir,
        output=output,
        progress_every=progress_every,
        enable_r_stem_nouns=enable_r_stem_nouns,
        profile=profile,
        refresh_catalog=refresh_catalog,
        dictionary=dictionary,
        manual_forms=manual_forms,
        verbal_paradigms=verbal_paradigms,
        prefixes=prefixes,
    )

    try:
        build_report = DictionaryBuildPipeline(resolved_index_db).run(
            source=source.resolve(),
            with_morphology=with_morphology,
            morph_options=morph_options,
            warnings_path=resolved_warnings_file,
            llm_fix_pass=llm_repair,
            report_path=report.resolve() if report is not None else None,
        )
    except (OSError, RuntimeError) as exc:
        msg = f"Failed to index dictionary source {source}: {exc}"
        raise click.ClickException(msg) from exc

    click.echo(
        "\n".join(
            [
                "Dictionary index complete.",
                f"source={source.resolve()}",
                f"index_db={resolved_index_db}",
                f"built_at={build_report.built_at}",
                f"bt_entries_written={build_report.bt_entries_written}",
                f"forms_source_count={build_report.forms_source_count}",
                f"forms_regenerated={build_report.forms_regenerated}",
                f"entry_ids_linked={build_report.entry_ids_linked}",
                f"entry_ids_cleared={build_report.entry_ids_cleared}",
                f"pos_inferred={build_report.pos_inferred}",
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
        label = _format_sense_label(sense.display_label)
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
    name="query",
    help="Query consolidated Bosworth-Toller dictionary entries.",
)
@click.argument("lemma")
@click.option(
    "--pos",
    type=str,
    default=None,
    help="Optional POS filter (for example noun, adv, verb).",
)
@click.option(
    "--json-output/--no-json-output",
    default=False,
    show_default=True,
    help="Render query output as JSON.",
)
@click.pass_context
def query(
    ctx: click.Context,
    lemma: str,
    pos: str | None,
    json_output: bool,
) -> None:
    """
    Query consolidated dictionary entries by lemma or variant spelling.

    Args:
        ctx: Click context carrying loaded settings and global flags.
        lemma: Headword or alternate spelling to resolve.
        pos: Optional POS filter.
        json_output: When true, print JSON instead of formatted text.

    Side Effects:
        Reads Bosworth-Toller ``bt_*`` tables from the resolved SQLite database
        and writes entries to stdout.

    Raises:
        click.ClickException: The index database cannot be opened.

    """
    settings: Settings | None = ctx.obj.get("settings")
    resolved_index_db = get_canonical_db_path(
        app_data_dir=settings.app_data_dir if settings is not None else None
    )
    if not resolved_index_db.is_file():
        raise click.ClickException(_missing_canonical_index_message(resolved_index_db))
    _require_non_empty_tables(
        resolved_index_db,
        ("bt_entries", "bt_senses", "bt_variants"),
        recovery_hint="Run `wyrdcraeft dictionary build`.",
    )

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


@dictionary_group.command(
    name="lookup",
    hidden=True,
    help="Deprecated alias for dictionary query.",
)
@click.argument("lemma")
@click.option(
    "--pos",
    type=str,
    default=None,
    help="Optional POS filter (for example noun, adv, verb).",
)
@click.option(
    "--json-output/--no-json-output",
    default=False,
    show_default=True,
    help="Render query output as JSON.",
)
@click.pass_context
def lookup(
    ctx: click.Context,
    lemma: str,
    pos: str | None,
    json_output: bool,
) -> None:
    """
    Deprecated alias for :func:`query`.

    Args:
        ctx: Click context carrying loaded settings and global flags.
        lemma: Headword or alternate spelling to resolve.
        pos: Optional POS filter.
        json_output: When true, print JSON instead of formatted text.

    Side Effects:
        Emits a deprecation warning and delegates to ``dictionary query``.

    """
    click.echo(
        "Warning: 'dictionary lookup' is deprecated; use 'dictionary query'.",
        err=True,
    )
    ctx.invoke(query, lemma=lemma, pos=pos, json_output=json_output)


@dictionary_group.command(
    name="browse",
    help="Open the dictionary browse Textual shell.",
)
@click.pass_context
def browse(
    ctx: click.Context,
) -> None:
    """
    Launch the dictionary browse shell against the resolved canonical SQLite path.

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
        run_dictionary_browse(resolved_index_db)
    except DictionaryBrowseDataError as exc:
        raise click.ClickException(str(exc)) from exc
    except OSError as exc:
        msg = f"Failed to launch dictionary browse from {resolved_index_db}: {exc}"
        raise click.ClickException(msg) from exc


@dictionary_group.command(
    name="ingest-wright-text",
    help="Ingest Wright section paragraph text from markdown into the catalog.",
)
@click.option(
    "--source",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help=(
        "Markdown file containing Wright section headings "
        f"(for example {default_wright_source_path().name} from the packaged "
        "dictionary resources)."
    ),
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite existing non-null section_text values.",
)
@click.pass_context
def ingest_wright_text(
    ctx: click.Context,
    source: Path,
    force: bool,
) -> None:
    """
    Populate ``wright_sections.section_text`` from one Wright markdown source.

    Note:
        Wright paragraph text follows ``data/OldEnglishGrammar.pdf`` and the
        markdown corpus aligned with ``data/Ondej_Tich_40-54-1.pdf``. In plain
        terms, this is an explicit ingest step; dictionary build does not run it
        automatically. Part-of-speech scope: ``cross-PoS``.

    Args:
        ctx: Click context carrying loaded settings and global flags.
        source: Markdown file containing Wright ``§`` section headings.
        force: When true, overwrite rows that already contain section text.

    Side Effects:
        Updates ``wright_sections.section_text`` in the canonical SQLite database.

    Raises:
        click.ClickException: Markdown ingest or database update fails.

    """
    settings = ctx.obj.get("settings")
    resolved_index_db = get_canonical_db_path(
        app_data_dir=settings.app_data_dir if settings is not None else None
    )
    engine = create_engine(resolved_index_db)
    try:
        result = WrightSectionTextIngester().ingest(engine, source, force=force)
    except (OSError, ValueError, SQLAlchemyError) as exc:
        msg = f"Failed to ingest Wright section text from {source}: {exc}"
        raise click.ClickException(msg) from exc
    finally:
        engine.dispose()

    for warning in result.warnings:
        click.echo(f"warning: {warning}", err=True)

    click.echo(
        "\n".join(
            [
                "Wright section text ingest complete.",
                f"index_db={resolved_index_db}",
                f"updated={result.updated}",
                f"skipped={result.skipped}",
                f"markdown_not_in_catalog={len(result.markdown_not_in_catalog)}",
                f"catalog_still_null={len(result.catalog_still_null)}",
                f"coverage_percent={result.coverage_percent}",
            ]
        )
    )


@dictionary_group.command(
    name="audit-wright",
    help="Audit legacy Wright source values against deterministic assignments.",
)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    default=False,
    help="Render the full audit result as machine-readable JSON.",
)
@click.option(
    "--data-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Directory containing bundled morphology source files.",
)
@click.option(
    "--db",
    "db_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to the canonical SQLite database used for assignment lookups.",
)
@click.pass_context
def audit_wright(
    ctx: click.Context,
    json_output: bool,
    data_dir: Path | None,
    db_path: Path | None,
) -> None:
    """
    Audit legacy Wright source annotations without mutating source files.

    Note:
        The audit compares legacy source values with deterministic class
        assignments grounded in ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, it reports source-side
        Wright quality for verbs, nouns, adjectives, adverbs, and pronouns
        without rewriting the source files or blocking builds. Part-of-speech
        scope: ``cross-PoS``.

    Args:
        ctx: Click context carrying loaded settings and global flags.
        json_output: When true, print full JSON instead of a sample-capped
            human-readable summary.
        data_dir: Optional base directory for bundled morphology source files.
        db_path: Optional explicit canonical SQLite database path.

    Side Effects:
        Reads bundled morphology source files and deterministic assignment rows,
        then writes the report to stdout.

    Raises:
        click.ClickException: Required inputs are missing or the audit cannot be
            read from disk/database.

    """
    resolved_data_dir = data_dir or _default_morphology_data_dir()
    dictionary_path = resolved_data_dir / "dict_adj-vb-part-num-adv-noun.txt"
    manual_forms_path = resolved_data_dir / "manual_forms.txt"
    para_vb_path = resolved_data_dir / "para_vb.txt"
    required_paths = (
        ("dictionary", dictionary_path),
        ("manual forms", manual_forms_path),
        ("verbal paradigms", para_vb_path),
    )
    for label, path in required_paths:
        if not path.exists():
            msg = (
                f"Missing {label} file: {path}. "
                "Provide an explicit path via --data-dir."
            )
            raise click.ClickException(msg)

    settings = ctx.obj.get("settings")
    resolved_index_db = db_path or get_canonical_db_path(
        app_data_dir=settings.app_data_dir if settings is not None else None
    )
    engine = create_engine(resolved_index_db)
    try:
        result = WrightAuditService(engine).audit(
            dictionary_path=dictionary_path,
            manual_forms_path=manual_forms_path,
            para_vb_path=para_vb_path,
        )
    except (OSError, SQLAlchemyError) as exc:
        msg = f"Failed to audit legacy Wright values from {resolved_data_dir}: {exc}"
        raise click.ClickException(msg) from exc
    finally:
        engine.dispose()

    if json_output:
        click.echo(json.dumps(result.to_payload(), ensure_ascii=False, indent=2))
        return

    click.echo(
        format_wright_audit_text(
            result,
            index_db=resolved_index_db,
        )
    )


@dictionary_group.command(
    name="generate-reference-snapshots",
    help="Generate canonical Python-reference morphology snapshots.",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path("tests/python_reference/data"),
    show_default=True,
    help="Directory where compressed snapshot files are written.",
)
@click.option(
    "--update",
    is_flag=True,
    default=False,
    help="Allow overwriting existing snapshot files.",
)
@click.option(
    "--include-full",
    is_flag=True,
    default=False,
    help="Also generate optional full-dataset smoke metadata snapshot.",
)
@click.option(
    "--data-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Directory containing default morphology data files.",
)
@click.option(
    "--subset-dictionary",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=Path("tests/fixtures/morphology/test_dict.txt"),
    show_default=True,
    help="Subset dictionary for default reference snapshots.",
)
def generate_reference_snapshots_command(
    output_dir: Path,
    update: bool,
    include_full: bool,
    data_dir: Path | None,
    subset_dictionary: Path,
) -> None:
    """
    Generate Python-reference snapshot fixtures via CLI.

    Note:
        Snapshot baselines represent the morphology behavior grounded in
        ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
        In plain terms, this captures expected outputs for every Part of Speech.

    Args:
        output_dir: Directory where snapshot artifacts are written.
        update: Whether existing snapshot files may be overwritten.
        include_full: Whether to include the optional full-dataset smoke snapshot.
        data_dir: Optional base directory for default morphology files.
        subset_dictionary: Dictionary used for default reference snapshots.

    Side Effects:
        Reads morphology source files and writes snapshot artifacts to disk.

    Raises:
        click.ClickException: Required inputs are missing or snapshot generation fails.

    """
    resolved_data_dir = data_dir or _default_morphology_data_dir()
    (
        full_dictionary,
        manual_forms,
        verbal_paradigms,
        prefixes,
    ) = _resolve_morphology_input_paths(
        data_dir=resolved_data_dir,
        dictionary=None,
        manual_forms=None,
        verbal_paradigms=None,
        prefixes=None,
    )
    _validate_morphology_inputs(
        (full_dictionary, manual_forms, verbal_paradigms, prefixes)
    )

    if not subset_dictionary.exists():
        msg = f"Missing subset dictionary: {subset_dictionary}"
        raise click.ClickException(msg)

    try:
        result = generate_reference_snapshots(
            output_dir=output_dir,
            update=update,
            include_full=include_full,
            subset_dictionary=subset_dictionary,
            full_dictionary=full_dictionary,
            manual_forms=manual_forms,
            verbal_paradigms=verbal_paradigms,
            prefixes=prefixes,
        )
    except (OSError, ValueError, FileExistsError) as e:
        raise click.ClickException(str(e)) from e

    click.echo(format_reference_snapshot_result(result))
