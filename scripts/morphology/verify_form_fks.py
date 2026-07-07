"""CLI helper to verify normalized morphology form foreign keys after build."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from wyrdcraeft.paths import get_canonical_db_path
from wyrdcraeft.services.morphology.generation.form_fk_verification import (
    FormFkVerificationService,
    format_form_fk_verification_report,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Sample morphology forms rows and verify FK columns against legacy "
            "wordclass/function fields."
        ),
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help="Canonical SQLite database path (default: app-data wyrdcraeft.sqlite3).",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=500,
        help="Maximum number of form rows to compare (default: 500).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for deterministic sampling (default: 0).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run form FK verification and print a summary report."""
    args = _build_parser().parse_args(argv)
    db_path = args.db_path or get_canonical_db_path()
    if not db_path.exists():
        print(f"database not found: {db_path}", file=sys.stderr)
        return 2

    service = FormFkVerificationService.from_db_path(
        db_path,
        sample_size=args.sample_size,
        rng_seed=args.seed,
    )
    try:
        report = service.verify()
    finally:
        service.close()

    print(format_form_fk_verification_report(report))
    return 1 if not report.ok else 0


if __name__ == "__main__":
    raise SystemExit(main())
