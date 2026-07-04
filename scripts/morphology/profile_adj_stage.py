"""Run cProfile against the morphology adjective generation stage."""

from __future__ import annotations

import argparse
import cProfile
import io
import pstats
import sys
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING

import wyrdcraeft.cli.cli as _bootstrap_cli  # noqa: F401

from tests.morphology.conftest import FULL_DICTIONARY, SUBSET_DICTIONARY, build_session
from wyrdcraeft.services.morphology.generation.dispatch import (
    generate_adjforms,
    generate_vbforms,
    output_manual_forms,
)
from wyrdcraeft.services.morphology.generation.sinks import (
    CompositeSink,
    SqliteIndexSink,
    TsvParitySink,
)

if TYPE_CHECKING:
    from wyrdcraeft.services.morphology.session import GeneratorSession


def _build_output_sink(
    *,
    with_sqlite: bool,
) -> tuple[
    TsvParitySink | CompositeSink,
    tempfile.TemporaryDirectory[str] | None,
    SqliteIndexSink | None,
]:
    """
    Build the output sink used while profiling adjective generation.

    Keyword Args:
        with_sqlite: When ``True``, include ``SqliteIndexSink`` like production builds.

    Returns:
        Tuple of ``(sink, temp_directory)``. ``temp_directory`` is non-``None`` only
        when SQLite profiling is enabled and must stay alive until the sink closes.

    """
    if not with_sqlite:
        return TsvParitySink(io.StringIO()), None, None

    temp_directory = tempfile.TemporaryDirectory(prefix="wyrdcraeft-adj-profile-")
    db_path = Path(temp_directory.name) / "profile.sqlite3"
    sqlite_sink = SqliteIndexSink(db_path)
    return (
        CompositeSink(TsvParitySink(io.StringIO()), sqlite_sink),
        temp_directory,
        sqlite_sink,
    )


def _run_prerequisite_stages(
    session: GeneratorSession,
    sink: TsvParitySink,
) -> None:
    """
    Run manual and verb stages needed before adjective generation.

    Args:
        session: Prepared morphology session.
        sink: Output sink receiving prerequisite stage rows.

    """
    output_manual_forms(session, sink)
    generate_vbforms(session, sink)


def _parse_args() -> argparse.Namespace:
    """
    Parse CLI arguments for adjective-stage profiling.

    Returns:
        Parsed command-line arguments.

    """
    parser = argparse.ArgumentParser(
        description=(
            "Profile morphology adjective generation after manual and verb stages."
        ),
    )
    parser.add_argument(
        "--subset",
        action="store_true",
        help="Use the subset dictionary fixture instead of the full dictionary.",
    )
    parser.add_argument(
        "--with-sqlite",
        action="store_true",
        help="Include SqliteIndexSink during the profiled adjective stage.",
    )
    parser.add_argument(
        "--prof-out",
        type=Path,
        default=Path(tempfile.gettempdir()) / "wyrdcraeft_adj_stage.prof",
        help="Path for the cProfile stats file.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=40,
        help="Number of cumulative-time rows to print from pstats.",
    )
    return parser.parse_args()


def main() -> None:
    """
    Profile ``generate_adjforms`` and print cumulative-time hotspots.

    Side Effects:
        Writes a ``.prof`` file and prints pstats output to stdout.

    """
    args = _parse_args()
    dictionary_path = SUBSET_DICTIONARY if args.subset else FULL_DICTIONARY
    session = build_session(dictionary_path=dictionary_path)

    prereq_sink = TsvParitySink(io.StringIO())
    prereq_started = time.perf_counter()
    _run_prerequisite_stages(session, prereq_sink)
    prereq_elapsed = time.perf_counter() - prereq_started

    output_sink, temp_directory, sqlite_sink = _build_output_sink(
        with_sqlite=args.with_sqlite,
    )
    forms_before = session.output_counter

    profiler = cProfile.Profile()
    profiler.enable()
    adj_started = time.perf_counter()
    generate_adjforms(session, output_sink)
    adj_elapsed = time.perf_counter() - adj_started
    profiler.disable()

    if sqlite_sink is not None:
        sqlite_sink.close()
    if temp_directory is not None:
        temp_directory.cleanup()

    args.prof_out.parent.mkdir(parents=True, exist_ok=True)
    profiler.dump_stats(str(args.prof_out))

    stats = pstats.Stats(profiler, stream=sys.stdout)
    stats.sort_stats("cumtime")
    stats.print_stats(args.top)

    rows_written = session.output_counter - forms_before
    rows_per_second = rows_written / adj_elapsed if adj_elapsed else 0.0
    print(
        "\n".join(
            [
                "",
                "Adj stage profile summary",
                f"dictionary={dictionary_path}",
                f"prerequisite_seconds={prereq_elapsed:.2f}",
                f"adj_seconds={adj_elapsed:.2f}",
                f"adj_rows={rows_written}",
                f"adj_rows_per_second={rows_per_second:.1f}",
                f"with_sqlite={args.with_sqlite}",
                f"prof_out={args.prof_out.resolve()}",
            ]
        )
    )


if __name__ == "__main__":
    main()
