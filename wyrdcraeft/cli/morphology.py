from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING

import click

from wyrdcraeft.db.runtime import create_engine
from wyrdcraeft.paths import get_canonical_db_path
from wyrdcraeft.services.morphology.build_profile import MorphologyBuildProfiler
from wyrdcraeft.services.morphology.catalog.loader import MorphologyCatalogLoader
from wyrdcraeft.services.morphology.generation.dispatch import (
    generate_adjforms,
    generate_advforms,
    generate_nounforms,
    generate_numforms,
    generate_vbforms,
    output_manual_forms,
)
from wyrdcraeft.services.morphology.generation.query import (
    MorphologyQueryService,
)
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
from wyrdcraeft.services.morphology.progress import (
    MorphologyGenerateProgressCoordinator,
    MorphologySetupStep,
    MorphologyStage,
)
from wyrdcraeft.services.morphology.reference_snapshots import (
    format_reference_snapshot_result,
    generate_reference_snapshots,
)
from wyrdcraeft.services.morphology.session import GeneratorSession

if TYPE_CHECKING:
    from collections.abc import Callable

    from wyrdcraeft.services.morphology.contracts import ParityFormOutput
    from wyrdcraeft.settings import Settings


def _current_stage_total(
    session: GeneratorSession,
    stage: MorphologyStage,
) -> int:
    """
    Return the current input-word total for one progress stage.

    Args:
        session: Active morphology generation session.
        stage: Stage whose current total should be computed.

    Returns:
        Source-word total for the requested stage.

    """
    return MorphologyGenerateProgressCoordinator.compute_stage_totals_for_session(
        session
    )[stage]


def _run_generation_stage(  # noqa: PLR0913
    *,
    session: GeneratorSession,
    output_sink: ParityFormOutput,
    progress: MorphologyGenerateProgressCoordinator,
    stage: MorphologyStage,
    generator: Callable[..., None],
    profiler: MorphologyBuildProfiler,
) -> None:
    """
    Run one morphology stage with synchronized progress start and finish hooks.

    Keyword Args:
        session: Active morphology generation session.
        output_sink: Composite sink receiving generated rows.
        progress: Live progress coordinator.
        stage: Stage being executed.
        generator: Callable that performs the stage work.
        profiler: Build profiler collecting stage wall times.

    Side Effects:
        Updates stderr progress and writes generated rows to output sinks.

    """
    profiler.begin_stage(stage, forms_written=session.output_counter)
    try:
        progress.start_stage(stage, total=_current_stage_total(session, stage))
        generator(session, output_sink, progress=progress)
        progress.finish_stage(stage)
    finally:
        profiler.end_stage(stage, forms_written=session.output_counter)


def _run_build_stages(
    *,
    session: GeneratorSession,
    output_sink: ParityFormOutput,
    progress: MorphologyGenerateProgressCoordinator,
    profiler: MorphologyBuildProfiler,
) -> None:
    """
    Run all morphology generation stages against one output sink.

    Keyword Args:
        session: Active morphology generation session.
        output_sink: Sink receiving generated rows.
        progress: Live progress coordinator.
        profiler: Build profiler collecting stage wall times.

    Side Effects:
        Writes generated rows to the configured output sink.

    """
    _run_generation_stage(
        session=session,
        output_sink=output_sink,
        progress=progress,
        stage=MorphologyStage.MANUAL,
        generator=output_manual_forms,
        profiler=profiler,
    )
    _run_generation_stage(
        session=session,
        output_sink=output_sink,
        progress=progress,
        stage=MorphologyStage.VERBS,
        generator=generate_vbforms,
        profiler=profiler,
    )
    _run_generation_stage(
        session=session,
        output_sink=output_sink,
        progress=progress,
        stage=MorphologyStage.ADJECTIVES,
        generator=generate_adjforms,
        profiler=profiler,
    )
    _run_generation_stage(
        session=session,
        output_sink=output_sink,
        progress=progress,
        stage=MorphologyStage.ADVERBS,
        generator=generate_advforms,
        profiler=profiler,
    )
    _run_generation_stage(
        session=session,
        output_sink=output_sink,
        progress=progress,
        stage=MorphologyStage.NUMERALS,
        generator=generate_numforms,
        profiler=profiler,
    )
    _run_generation_stage(
        session=session,
        output_sink=output_sink,
        progress=progress,
        stage=MorphologyStage.NOUNS,
        generator=generate_nounforms,
        profiler=profiler,
    )


def _apply_limit(session: GeneratorSession, *, full: bool, limit: int | None) -> None:
    """
    Apply optional subset limiting and recategorize cached POS pools.

    Keyword Args:
        session: Active morphology generation session.
        full: Whether full-dataset generation is enabled.
        limit: Optional cap for non-full mode processed words.

    Side Effects:
        Mutates session word pools when subset limiting is active.

    """
    if full or not limit:
        return

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
    name="build",
    help="Build Old English morphological forms.",
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
    default=None,
    type=click.Path(path_type=Path),
    help="Optional TSV output file path.",
)
@click.option(
    "--limit",
    default=None,
    type=int,
    help="Limit number of words processed.",
)
@click.option(
    "--progress-every",
    type=int,
    default=None,
    metavar="INTEGER",
    help="Update visible lemma banner every N processed words.",
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
@click.option(
    "--profile",
    is_flag=True,
    default=False,
    help="Print stage and SQLite timing summary to stderr when the build finishes.",
)
@click.option(
    "--refresh-catalog",
    is_flag=True,
    default=False,
    help="Re-load Wright morph catalog from packaged fixture.",
)
@click.pass_context
def build(  # noqa: PLR0913, PLR0915
    ctx: click.Context,
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
    Generate Old English morphological forms and parity index artifacts.

    Note:
        Generation behavior is parity-locked to grammar expectations documented in
        ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
        In plain terms, this generates inflected forms for verbs, nouns,
        adjectives, adverbs, and numerals.

    Args:
        ctx: Click context carrying loaded settings and global flags.
        data_dir: Optional base directory for default morphology files.
        dictionary: Optional dictionary file path override.
        manual_forms: Optional manual forms file path override.
        verbal_paradigms: Optional verbal paradigms file path override.
        prefixes: Optional prefixes file path override.
        output: Optional TSV output file path.
        limit: Optional cap for non-full mode processed words.
        progress_every: Optional visible-lemma update cadence override.
        enable_r_stem_nouns: Enables non-parity r-stem noun generation.
        full: Enables full-dictionary generation mode.
        profile: Enables stderr timing summary output when the build finishes.
        refresh_catalog: Reloads the Wright morph catalog from the packaged
            fixture even when catalog rows already exist.

    Side Effects:
        Reads morphology source files, seeds the Wright catalog when needed,
        and writes SQLite output artifacts.

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

    settings = ctx.obj.get("settings")
    resolved_progress_every = _resolve_progress_every(
        settings=settings,
        progress_every=progress_every,
    )
    progress = MorphologyGenerateProgressCoordinator(
        progress_every_words=resolved_progress_every,
        enabled=not bool(ctx.obj.get("quiet")),
    )
    progress.start()

    profiler = MorphologyBuildProfiler(enabled=profile)
    session = GeneratorSession()
    try:
        with profiler.time_setup("load data"):
            session.load_all(*(str(path) for path in resolved_paths))
        progress.advance_setup(MorphologySetupStep.LOAD_DATA)
    except OSError as e:
        progress.stop()
        msg = f"Unable to read morphology input data: {e}"
        raise click.ClickException(msg) from e

    with profiler.time_setup("apply limit"):
        session.enable_r_stem_nouns = enable_r_stem_nouns
        _apply_limit(session, full=full, limit=limit)
    progress.advance_setup(MorphologySetupStep.APPLY_LIMIT)

    with profiler.time_setup("normalize forms"):
        session.remove_prefixes()
        session.remove_hyphens()
    progress.advance_setup(MorphologySetupStep.NORMALIZE_FORMS)
    with profiler.time_setup("count syllables"):
        session.count_syllables()
    progress.advance_setup(MorphologySetupStep.COUNT_SYLLABLES)

    with profiler.time_setup("assign verb paradigms"):
        set_verb_paradigm(session)
    progress.advance_setup(MorphologySetupStep.ASSIGN_VERB_PARADIGMS)
    with profiler.time_setup("assign adjective paradigms"):
        set_adj_paradigm(session)
    progress.advance_setup(MorphologySetupStep.ASSIGN_ADJ_PARADIGMS)
    with profiler.time_setup("assign noun paradigms"):
        set_noun_paradigm(session)
    progress.advance_setup(MorphologySetupStep.ASSIGN_NOUN_PARADIGMS)

    resolved_index_db = get_canonical_db_path(
        app_data_dir=settings.app_data_dir if settings is not None else None
    )
    default_fixture_path = resolved_data_dir / "wright_paradigms.json"
    try:
        with profiler.time_setup("seed catalog"):
            catalog_engine = create_engine(resolved_index_db)
            try:
                catalog_loader = MorphologyCatalogLoader(catalog_engine)
                catalog_loader.ensure_seeded(
                    default_fixture_path,
                    refresh=refresh_catalog,
                )
            finally:
                catalog_engine.dispose()
    except (OSError, ValueError) as e:
        progress.stop()
        msg = (
            f"Failed to seed Wright morph catalog from {default_fixture_path}: {e}"
        )
        raise click.ClickException(msg) from e

    sqlite_sink: SqliteIndexSink | None = None
    try:
        sqlite_sink = SqliteIndexSink(
            resolved_index_db,
            sqlite_flush_observer=profiler.sqlite_flush_observer(),
        )
        if output is not None:
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("w", encoding="utf-8") as out_handle:
                output_sink = CompositeSink(
                    TsvParitySink(out_handle),
                    sqlite_sink,
                )
                _run_build_stages(
                    session=session,
                    output_sink=output_sink,
                    progress=progress,
                    profiler=profiler,
                )
        else:
            _run_build_stages(
                session=session,
                output_sink=sqlite_sink,
                progress=progress,
                profiler=profiler,
            )
    except OSError as e:
        destination = output if output is not None else resolved_index_db
        msg = f"Failed to write morphology output to {destination}: {e}"
        raise click.ClickException(msg) from e
    finally:
        progress.stop()
        if sqlite_sink is not None:
            sqlite_sink.close()

    profiler.emit_summary(forms_written=session.output_counter)

    completion_lines = [
        "Morphology generation complete.",
        f"index_db={resolved_index_db}",
        f"forms_written={session.output_counter}",
        f"limit_applied={'none' if full or not limit else limit}",
        f"full_mode={full}",
    ]
    if output is not None:
        completion_lines.insert(1, f"output={output}")
    click.echo("\n".join(completion_lines))


def _resolve_progress_every(
    *,
    settings: Settings | None,
    progress_every: int | None,
) -> int:
    """
    Resolve morphology progress cadence from CLI override or settings.

    Keyword Args:
        settings: Loaded application settings, when available.
        progress_every: Optional CLI override value.

    Returns:
        Positive cadence used for visible lemma updates.

    Raises:
        click.ClickException: The resolved value is not positive.

    """
    resolved = progress_every
    if resolved is None:
        resolved = (
            settings.morphology_progress_every_words
            if settings is not None
            else 5
        )
    if resolved <= 0:
        msg = "--progress-every must be a positive integer."
        raise click.ClickException(msg)
    return resolved


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
