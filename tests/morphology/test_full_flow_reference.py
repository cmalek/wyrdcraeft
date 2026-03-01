from __future__ import annotations

import hashlib
import io
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest

from wyrdcraeft.services.morphology.generators.common import (
    generate_adjforms,
    generate_advforms,
    generate_nounforms,
    generate_numforms,
    generate_vbforms,
    output_manual_forms,
)

from .conftest import FULL_DICTIONARY, build_session
from .snapshot_io import canonicalize_form_rows, parse_form_output, read_jsonl_gz

if TYPE_CHECKING:
    from wyrdcraeft.services.morphology.session import GeneratorSession

DATA_DIR = Path(__file__).resolve().parent / "data"
FULL_FLOW_SUBSET_PATH = DATA_DIR / "full_flow_subset.jsonl.gz"
FULL_FLOW_FULL_SMOKE_PATH = DATA_DIR / "full_flow_full_smoke.jsonl.gz"


def _full_flow_rows(session: GeneratorSession) -> list[dict[str, str]]:
    output = io.StringIO()
    output_manual_forms(session, output)
    generate_vbforms(session, output)
    generate_adjforms(session, output)
    generate_advforms(session, output)
    generate_numforms(session, output)
    generate_nounforms(session, output)
    return canonicalize_form_rows(parse_form_output(output.getvalue()))


def _full_flow_metadata(session: GeneratorSession) -> dict[str, str]:
    hasher = hashlib.sha256()
    line_count = 0
    byte_count = 0

    with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8") as handle:
        output = cast("io.StringIO", handle)
        output_manual_forms(session, output)
        generate_vbforms(session, output)
        generate_adjforms(session, output)
        generate_advforms(session, output)
        generate_numforms(session, output)
        generate_nounforms(session, output)
        handle.flush()
        handle.seek(0)

        for line in handle:
            encoded = line.encode("utf-8")
            hasher.update(encoded)
            line_count += 1
            byte_count += len(encoded)

    return {
        "line_count": str(line_count),
        "byte_count": str(byte_count),
        "sha256": hasher.hexdigest(),
    }


@pytest.mark.morphology
def test_full_flow_subset_matches_snapshot(subset_session: GeneratorSession) -> None:
    observed = _full_flow_rows(subset_session)
    expected = read_jsonl_gz(FULL_FLOW_SUBSET_PATH)

    assert len(observed) == len(expected)
    assert observed == expected


@pytest.mark.morphology_full
@pytest.mark.morphology
def test_full_flow_full_dataset_smoke_snapshot() -> None:
    if not FULL_FLOW_FULL_SMOKE_PATH.exists():
        msg = "Full-dataset smoke snapshot missing. Generate with --include-full."
        pytest.skip(msg)

    full_session = build_session(dictionary_path=FULL_DICTIONARY)
    expected_rows = read_jsonl_gz(FULL_FLOW_FULL_SMOKE_PATH)
    assert len(expected_rows) == 1

    observed = _full_flow_metadata(full_session)
    assert observed == expected_rows[0]
