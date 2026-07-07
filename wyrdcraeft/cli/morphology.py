from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

import click
from sqlalchemy.exc import SQLAlchemyError

from wyrdcraeft.db.runtime import create_engine
from wyrdcraeft.paths import get_canonical_db_path
from wyrdcraeft.services.morphology.catalog.wright_audit import (
    WrightAuditService,
    format_wright_audit_text,
)
from wyrdcraeft.services.morphology.catalog.wright_text import WrightSectionTextIngester
from wyrdcraeft.services.morphology.generation.query import (
    MorphologyQueryService,
)
from wyrdcraeft.services.morphology.reference_snapshots import (
    format_reference_snapshot_result,
    generate_reference_snapshots,
)


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


def _resolve_input_paths(
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


def _validate_inputs(paths: tuple[Path, Path, Path, Path]) -> None:
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


@click.group(
    name="morphology",
    help=(
        "Old English morphology query and reference commands. "
        "Default data files are loaded from wyrdcraeft/etc/morphology."
    ),
)
def morphology_group() -> None:
    """Morphology command group."""


def _format_dictionary_join_text(entry: dict[str, object]) -> str:
    """
    Render one dictionary join entry as human-readable text.

    Args:
        entry: Dictionary join payload from ``dictionary_join_entry_to_dict``.

    Returns:
        Multi-line text block without attestations.

    """
    headword = str(entry["headword"])
    pos = str(entry["pos"])
    genders = entry.get("genders", [])
    gender_text = ""
    if isinstance(genders, list) and genders:
        gender_text = f"  Gender: {', '.join(str(value) for value in genders)}"

    lines = [f"Dictionary: {headword}", f"POS: {pos}{gender_text}", "Senses:"]
    senses = entry.get("senses", [])
    if isinstance(senses, list):
        for sense in senses:
            if not isinstance(sense, dict):
                continue
            label = str(sense.get("sense_label", "")).strip()
            gloss = str(sense.get("gloss_en", "")).strip()
            prefix = f"  {label}. " if label and not label.endswith(".") else "  "
            if label and label.endswith("."):
                prefix = f"  {label} "
            lines.append(f"{prefix}{gloss}".rstrip())

    etymology = str(entry.get("etymology", "")).strip()
    if etymology:
        lines.append(f"Etymology: {etymology}")

    return "\n".join(lines)


@morphology_group.command(
    name="query",
    help="Query generated morphology rows from a SQLite index.",
)
@click.option(
    "--db",
    "db_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="Path to morphology SQLite index database.",
)
@click.option("--lemma", default=None, help="Lookup rows by lemma/root token.")
@click.option(
    "--form",
    "surface_form",
    default=None,
    help="Lookup rows by surface form.",
)
@click.option("--limit", default=200, type=int, show_default=True, help="Maximum rows.")
@click.option(
    "--json-output/--no-json-output",
    default=False,
    show_default=True,
    help="Render query output as JSON.",
)
@click.option(
    "--with-dictionary",
    is_flag=True,
    default=False,
    help="Attach matching Bosworth-Toller dictionary entries to the output.",
)
@click.option(
    "--dictionary-db",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help=(
        "Dictionary SQLite index path (defaults to sibling dictionary.sqlite3 "
        "or bt_* tables inside the morphology database)."
    ),
)
def query(  # noqa: PLR0913
    db_path: Path,
    lemma: str | None,
    surface_form: str | None,
    limit: int,
    json_output: bool,
    with_dictionary: bool,
    dictionary_db: Path | None,
) -> None:
    """
    Query morphology rows by lemma or surface form.

    Note:
        Query keys are normalized in line with morphology conventions from
        ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
        In plain terms, this searches inflected forms across all Parts of Speech.

    Args:
        db_path: SQLite morphology index path.
        lemma: Optional lemma/root lookup key.
        surface_form: Optional surface form lookup key.
        limit: Maximum number of rows to emit.
        json_output: When true, print JSON instead of tab-separated rows.
        with_dictionary: When true, attach Bosworth-Toller dictionary entries.
        dictionary_db: Optional explicit dictionary SQLite index path.

    Side Effects:
        Reads the SQLite morphology index and writes rows to stdout.

    Raises:
        click.ClickException: Neither or both lookup modes are requested.

    """
    if (lemma is None) == (surface_form is None):
        msg = "Provide exactly one of --lemma or --form."
        raise click.ClickException(msg)

    query_service = MorphologyQueryService(db_path)
    try:
        if lemma is not None:
            rows = query_service.lookup_by_lemma(lemma, limit=max(1, limit))
            lookup_token = lemma
        else:
            rows = query_service.lookup_by_form(surface_form or "", limit=max(1, limit))
            lookup_token = rows[0].BT if rows else (surface_form or "")

        dictionary_entries: list[dict[str, object]] = []
        if with_dictionary:
            dictionary_entries = query_service.lookup_dictionary_entries(
                lookup_token,
                rows,
                dictionary_db_path=dictionary_db,
            )
    finally:
        query_service.close()

    if json_output:
        if with_dictionary:
            payload: dict[str, object] = {
                "forms": [row.model_dump() for row in rows],
                "dictionary": dictionary_entries,
            }
            click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            click.echo(
                json.dumps(
                    [row.model_dump() for row in rows],
                    ensure_ascii=False,
                    indent=2,
                )
            )
        return

    for row in rows:
        click.echo(
            f"{row.counter}\t{row.form}\t{row.BT}\t{row.function}\t{row.probability}"
        )

    if with_dictionary and dictionary_entries:
        click.echo("")
        for index, entry in enumerate(dictionary_entries):
            if index:
                click.echo("")
            click.echo(_format_dictionary_join_text(entry))


@morphology_group.command(
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
    full_dictionary, manual_forms, verbal_paradigms, prefixes = _resolve_input_paths(
        data_dir=resolved_data_dir,
        dictionary=None,
        manual_forms=None,
        verbal_paradigms=None,
        prefixes=None,
    )
    _validate_inputs((full_dictionary, manual_forms, verbal_paradigms, prefixes))

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


@morphology_group.command(
    name="ingest-wright-text",
    help="Ingest Wright section paragraph text from markdown into the catalog.",
)
@click.option(
    "--source",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help=(
        "Markdown file containing Wright section headings "
        "(for example data/sources/wright.md)."
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


@morphology_group.command(
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
