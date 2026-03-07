from __future__ import annotations

import io
from typing import TYPE_CHECKING

from wyrdcraeft.services.morphology.generation.dispatch import (
    generate_adjforms,
    generate_advforms,
    generate_nounforms,
    generate_numforms,
    generate_vbforms,
    output_manual_forms,
)

from .snapshot_io import (
    canonicalize_form_rows,
    parse_form_output,
    read_jsonl_gz,
    stable_json_sha256,
)

if TYPE_CHECKING:
    from pathlib import Path

    from wyrdcraeft.services.morphology.session import GeneratorSession


def full_flow_rows(session: GeneratorSession) -> list[dict[str, str]]:
    """
    Generate canonicalized full-flow rows for parity assertions.

    Args:
        session: Prepared morphology generation session.

    Returns:
        Canonicalized emitted rows with unstable counters removed.

    """
    output = io.StringIO()
    output_manual_forms(session, output)
    generate_vbforms(session, output)
    generate_adjforms(session, output)
    generate_advforms(session, output)
    generate_numforms(session, output)
    generate_nounforms(session, output)
    return canonicalize_form_rows(parse_form_output(output.getvalue()))


def assert_snapshot_parity(
    session: GeneratorSession,
    snapshot_path: Path,
) -> None:
    """
    Assert full-flow parity against a canonical snapshot file.

    Args:
        session: Prepared morphology generation session.
        snapshot_path: Gzipped JSONL snapshot path.

    """
    observed = full_flow_rows(session)
    expected = read_jsonl_gz(snapshot_path)
    assert len(observed) == len(expected)
    assert stable_json_sha256(observed) == stable_json_sha256(expected)
    assert observed == expected
