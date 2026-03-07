from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

import click

from wyrdcraeft.services.morphology.generation.dispatch import (
    generate_adjforms,
    generate_advforms,
    generate_nounforms,
    generate_numforms,
    generate_vbforms,
    output_manual_forms,
)
from wyrdcraeft.services.morphology.generation.query import MorphologyQueryService
from wyrdcraeft.services.morphology.generation.sinks import (
    CompositeSink,
    SqliteIndexSink,
    TsvParitySink,
)
from wyrdcraeft.services.morphology.processors import (
    set_adj_paradigm,
    set_noun_paradigm,
    set_verb_paradigm,
)
from wyrdcraeft.services.morphology.reference_snapshots import (
    format_reference_snapshot_result,
    generate_reference_snapshots,
)
from wyrdcraeft.services.morphology.session import GeneratorSession


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
        "Old English morphology generator commands. "
        "Default data files are loaded from wyrdcraeft/etc/morphology."
    ),
)
def morphology_group() -> None:
    """Morphology command group."""


@morphology_group.command(
    name="generate",
    help="Generate Old English morphological forms.",
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
    help="Dictionary file path.",
)
@click.option(
    "--manual-forms",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Manual forms file path.",
)
@click.option(
    "--verbal-paradigms",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Verbal paradigms file path.",
)
@click.option(
    "--prefixes",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Prefixes file path.",
)
@click.option(
    "--output",
    default=Path("output.txt"),
    type=click.Path(path_type=Path),
    help="Output file path.",
)
@click.option(
    "--index-db",
    type=click.Path(path_type=Path),
    default=None,
    help="SQLite index output path (defaults to output path with .sqlite3 suffix).",
)
@click.option(
    "--limit",
    default=None,
    type=int,
    help="Limit number of words processed.",
)
@click.option(
    "--enable-r-stem-nouns",
    is_flag=True,
    default=False,
    help="Enable opt-in non-parity r-stem noun generation.",
)
@click.option(
    "--full/--no-full",
    default=False,
    show_default=True,
    help="Generate full dictionary output (equivalent to legacy generate-full).",
)
def generate(  # noqa: PLR0913
    data_dir: Path | None,
    dictionary: Path | None,
    manual_forms: Path | None,
    verbal_paradigms: Path | None,
    prefixes: Path | None,
    output: Path,
    index_db: Path | None,
    limit: int | None,
    enable_r_stem_nouns: bool,
    full: bool,
) -> None:
    """
    Generate Old English morphological forms and parity index artifacts.

    Note:
        Generation behavior is parity-locked to grammar expectations documented in
        ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
        In plain terms, this generates inflected forms for verbs, nouns,
        adjectives, adverbs, and numerals.

    Args:
        data_dir: Optional base directory for default morphology files.
        dictionary: Optional dictionary file path override.
        manual_forms: Optional manual forms file path override.
        verbal_paradigms: Optional verbal paradigms file path override.
        prefixes: Optional prefixes file path override.
        output: TSV output file path.
        index_db: Optional SQLite index output file path override.
        limit: Optional cap for non-full mode processed words.
        enable_r_stem_nouns: Enables non-parity r-stem noun generation.
        full: Enables full-dictionary generation mode.

    Side Effects:
        Reads morphology source files and writes TSV/SQLite output artifacts.

    Raises:
        click.ClickException: Input files are missing or output writing fails.

    """
    resolved_data_dir = data_dir or _default_morphology_data_dir()
    resolved_paths = _resolve_input_paths(
        data_dir=resolved_data_dir,
        dictionary=dictionary,
        manual_forms=manual_forms,
        verbal_paradigms=verbal_paradigms,
        prefixes=prefixes,
    )
    _validate_inputs(resolved_paths)

    session = GeneratorSession()
    try:
        session.load_all(*(str(path) for path in resolved_paths))
    except OSError as e:
        msg = f"Unable to read morphology input data: {e}"
        raise click.ClickException(msg) from e

    session.enable_r_stem_nouns = enable_r_stem_nouns

    if not full and limit:
        session.words = session.words[:limit]
        session.verbs = [
            w for w in session.words if w.verb == 1 and (w.pspart + w.papart == 0)
        ]
        session.adjectives = [
            w
            for w in session.words
            if w.adjective == 1 and (w.pspart + w.papart + w.numeral == 0)
        ]
        session.nouns = [w for w in session.words if w.noun == 1]

    session.remove_prefixes()
    session.remove_hyphens()
    session.count_syllables()

    set_verb_paradigm(session)
    set_adj_paradigm(session)
    set_noun_paradigm(session)

    resolved_index_db = index_db or output.with_suffix(".sqlite3")
    sqlite_sink: SqliteIndexSink | None = None
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        sqlite_sink = SqliteIndexSink(resolved_index_db)
        with output.open("w", encoding="utf-8") as out_handle:
            output_sink = CompositeSink(TsvParitySink(out_handle), sqlite_sink)
            output_manual_forms(session, output_sink)
            generate_vbforms(session, output_sink)
            generate_adjforms(session, output_sink)
            generate_advforms(session, output_sink)
            generate_numforms(session, output_sink)
            generate_nounforms(session, output_sink)
    except OSError as e:
        msg = f"Failed to write morphology output to {output}: {e}"
        raise click.ClickException(msg) from e
    finally:
        if sqlite_sink is not None:
            sqlite_sink.close()

    click.echo(
        "\n".join(
            [
                "Morphology generation complete.",
                f"output={output}",
                f"index_db={resolved_index_db}",
                f"forms_written={session.output_counter}",
                f"limit_applied={'none' if full or not limit else limit}",
                f"full_mode={full}",
            ]
        )
    )


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
def query(
    db_path: Path,
    lemma: str | None,
    surface_form: str | None,
    limit: int,
    json_output: bool,
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
        else:
            rows = query_service.lookup_by_form(surface_form or "", limit=max(1, limit))
    finally:
        query_service.close()

    if json_output:
        click.echo(
            json.dumps([row.model_dump() for row in rows], ensure_ascii=False, indent=2)
        )
        return

    for row in rows:
        click.echo(
            f"{row.counter}\t{row.form}\t{row.BT}\t{row.function}\t{row.probability}"
        )


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
