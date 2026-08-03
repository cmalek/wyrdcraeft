"""Service entrypoint for morphology generation builds."""

from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING, cast

from sqlalchemy.exc import SQLAlchemyError

from wyrdcraeft.db.runtime import create_engine
from wyrdcraeft.services.morphology.build_profile import MorphologyBuildProfiler
from wyrdcraeft.services.morphology.catalog.assigner import LemmaMorphClassAssigner
from wyrdcraeft.services.morphology.catalog.loader import MorphologyCatalogLoader
from wyrdcraeft.services.morphology.catalog.paradigm_map import ParadigmClassMapper
from wyrdcraeft.services.morphology.catalog.pos_seed import (
    ensure_inflection_codes,
    ensure_parts_of_speech,
)
from wyrdcraeft.services.morphology.generation.facade import (
    MorphologyGenerationFacade,
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
from wyrdcraeft.services.morphology.session import GeneratorSession

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Callable

    from sqlalchemy.engine import Connection

    from wyrdcraeft.services.morphology.contracts import ParityFormOutput
    from wyrdcraeft.settings import Settings


class MorphologyBuildRunnerError(RuntimeError):
    """Raised when service-level morphology generation setup or output fails."""


def _sqlite_connection(connection: Connection) -> sqlite3.Connection:
    """
    Unwrap SQLAlchemy's DB-API connection to the underlying SQLite driver.

    Args:
        connection: Active SQLAlchemy connection bound to the canonical database.

    Returns:
        Raw ``sqlite3.Connection`` used by reference seeding helpers.

    """
    dbapi_connection = connection.connection
    driver_connection = getattr(dbapi_connection, "driver_connection", None)
    if driver_connection is not None:
        return cast("sqlite3.Connection", driver_connection)
    return cast("sqlite3.Connection", dbapi_connection)


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
        session.word_pool
    )[stage]


def _run_generation_stage(
    *,
    session: GeneratorSession,
    progress: MorphologyGenerateProgressCoordinator,
    stage: MorphologyStage,
    generator: Callable[[], None],
    profiler: MorphologyBuildProfiler,
) -> None:
    """
    Run one morphology stage with synchronized progress start and finish hooks.

    Keyword Args:
        session: Active morphology generation session.
        progress: Live progress coordinator.
        stage: Stage being executed.
        generator: Bound facade method that performs the stage work.
        profiler: Build profiler collecting stage wall times.

    Side Effects:
        Updates stderr progress and writes generated rows to output sinks.

    """
    profiler.begin_stage(stage, forms_written=session.output_counter)
    try:
        progress.start_stage(stage, total=_current_stage_total(session, stage))
        generator()
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
    facade = MorphologyGenerationFacade(session, output_sink, progress=progress)
    _run_generation_stage(
        session=session,
        progress=progress,
        stage=MorphologyStage.MANUAL,
        generator=facade.output_manual_forms,
        profiler=profiler,
    )
    _run_generation_stage(
        session=session,
        progress=progress,
        stage=MorphologyStage.VERBS,
        generator=facade.generate_verbs,
        profiler=profiler,
    )
    _run_generation_stage(
        session=session,
        progress=progress,
        stage=MorphologyStage.ADJECTIVES,
        generator=facade.generate_adjectives,
        profiler=profiler,
    )
    _run_generation_stage(
        session=session,
        progress=progress,
        stage=MorphologyStage.ADVERBS,
        generator=facade.generate_adverbs,
        profiler=profiler,
    )
    _run_generation_stage(
        session=session,
        progress=progress,
        stage=MorphologyStage.NUMERALS,
        generator=facade.generate_numerals,
        profiler=profiler,
    )
    _run_generation_stage(
        session=session,
        progress=progress,
        stage=MorphologyStage.NOUNS,
        generator=facade.generate_nouns,
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
    session.word_pool.categorize()


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
    Resolve morphology input file paths using overrides or data-dir defaults.

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
        MorphologyBuildRunnerError: A required file path is missing.

    """
    labels = ("dictionary", "manual forms", "verbal paradigms", "prefixes")
    for label, path in zip(labels, paths, strict=True):
        if not path.exists():
            msg = (
                f"Missing {label} file: {path}. "
                "Provide an explicit path via command flags or --data-dir."
            )
            raise MorphologyBuildRunnerError(msg)


def _resolve_progress_every(
    *,
    settings: Settings | None,
    progress_every: int | None,
) -> int:
    """
    Resolve morphology progress cadence from override or settings.

    Keyword Args:
        settings: Loaded application settings, when available.
        progress_every: Optional explicit override value.

    Returns:
        Positive cadence used for visible lemma updates.

    Raises:
        MorphologyBuildRunnerError: The resolved value is not positive.

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
        raise MorphologyBuildRunnerError(msg)
    return resolved


def run_morphology_generation(  # noqa: PLR0913, PLR0915
    *,
    db_path: Path,
    settings: Settings | None = None,
    quiet: bool = False,
    data_dir: Path | None = None,
    dictionary: Path | None = None,
    manual_forms: Path | None = None,
    verbal_paradigms: Path | None = None,
    prefixes: Path | None = None,
    output: Path | None = None,
    limit: int | None = None,
    progress_every: int | None = None,
    enable_r_stem_nouns: bool = False,
    full: bool = False,
    profile: bool = False,
    refresh_catalog: bool = False,
) -> int:
    """
    Generate Old English morphological forms into one canonical database.

    Note:
        Generation behavior is parity-locked to grammar expectations documented in
        ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
        In plain terms, this generates inflected forms for verbs, nouns,
        adjectives, adverbs, and numerals.

    Keyword Args:
        db_path: Canonical SQLite database receiving morphology rows.
        settings: Loaded application settings, when available.
        quiet: Disables visible progress output when ``True``.
        data_dir: Optional base directory for default morphology files.
        dictionary: Optional dictionary file path override.
        manual_forms: Optional manual forms file path override.
        verbal_paradigms: Optional verbal paradigms file path override.
        prefixes: Optional prefixes file path override.
        output: Optional TSV parity output file path.
        limit: Optional cap for non-full mode processed words.
        progress_every: Optional visible-lemma update cadence override.
        enable_r_stem_nouns: Enables non-parity r-stem noun generation.
        full: Enables full-dictionary generation mode.
        profile: Enables stderr timing summary output when the build finishes.
        refresh_catalog: Reloads the Wright morph catalog from the packaged
            fixture even when catalog rows already exist.

    Returns:
        Number of morphology rows written during the build.

    Raises:
        MorphologyBuildRunnerError: Input files are missing or output writing fails.

    Side Effects:
        Reads morphology source files, seeds the Wright catalog when needed,
        and writes SQLite and optional TSV output artifacts.

    """
    resolved_db_path = db_path.expanduser().resolve()
    resolved_data_dir = data_dir or _default_morphology_data_dir()
    resolved_paths = _resolve_input_paths(
        data_dir=resolved_data_dir,
        dictionary=dictionary,
        manual_forms=manual_forms,
        verbal_paradigms=verbal_paradigms,
        prefixes=prefixes,
    )
    _validate_inputs(resolved_paths)

    resolved_progress_every = _resolve_progress_every(
        settings=settings,
        progress_every=progress_every,
    )
    progress = MorphologyGenerateProgressCoordinator(
        progress_every_words=resolved_progress_every,
        enabled=not quiet,
    )
    progress.start()

    profiler = MorphologyBuildProfiler(enabled=profile)
    session = GeneratorSession()
    try:
        try:
            with profiler.time_setup("load data"):
                session.load_all(*(str(path) for path in resolved_paths))
            progress.advance_setup(MorphologySetupStep.LOAD_DATA)
        except OSError as exc:
            msg = f"Unable to read morphology input data: {exc}"
            raise MorphologyBuildRunnerError(msg) from exc

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
            set_verb_paradigm(session.word_pool)
        progress.advance_setup(MorphologySetupStep.ASSIGN_VERB_PARADIGMS)
        with profiler.time_setup("assign adjective paradigms"):
            set_adj_paradigm(session.word_pool)
        progress.advance_setup(MorphologySetupStep.ASSIGN_ADJ_PARADIGMS)
        with profiler.time_setup("assign noun paradigms"):
            set_noun_paradigm(
                session.word_pool, enable_r_stem_nouns=session.enable_r_stem_nouns
            )
        progress.advance_setup(MorphologySetupStep.ASSIGN_NOUN_PARADIGMS)

        default_fixture_path = resolved_data_dir / "wright_paradigms.json"
        catalog_engine = create_engine(resolved_db_path)
        try:
            with (
                profiler.time_setup("seed references"),
                catalog_engine.begin() as connection,
            ):
                sqlite_connection = _sqlite_connection(connection)
                pos_map = ensure_parts_of_speech(sqlite_connection)
                ensure_inflection_codes(sqlite_connection, pos_map)
            with profiler.time_setup("seed catalog"):
                catalog_loader = MorphologyCatalogLoader(catalog_engine)
                catalog_loader.ensure_seeded(
                    default_fixture_path,
                    refresh=refresh_catalog,
                )
            with profiler.time_setup("assign lemma morph classes"):
                _dictionary, _manual, resolved_para_vb, _prefixes = resolved_paths
                lemma_assigner = LemmaMorphClassAssigner(
                    catalog_engine,
                    ParadigmClassMapper(
                        fixture_path=default_fixture_path,
                        para_vb_path=resolved_para_vb,
                    ),
                )
                lemma_assigner.assign_all(session.words)
        except (OSError, ValueError, SQLAlchemyError) as exc:
            msg = (
                "Failed to load Wright morph catalog or assign lemma classes "
                f"from {default_fixture_path}: {exc}"
            )
            raise MorphologyBuildRunnerError(msg) from exc
        finally:
            catalog_engine.dispose()

        sqlite_sink: SqliteIndexSink | None = None
        try:
            sqlite_sink = SqliteIndexSink(
                resolved_db_path,
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
        except OSError as exc:
            destination = output if output is not None else resolved_db_path
            msg = f"Failed to write morphology output to {destination}: {exc}"
            raise MorphologyBuildRunnerError(msg) from exc
        finally:
            if sqlite_sink is not None:
                sqlite_sink.close()
    finally:
        progress.stop()

    profiler.emit_summary(forms_written=session.output_counter)
    return session.output_counter
