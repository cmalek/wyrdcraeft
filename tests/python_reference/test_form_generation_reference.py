from __future__ import annotations

import io
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from wyrdcraeft.services.morphology.generators.common import (
    generate_adjforms,
    generate_advforms,
    generate_nounforms,
    generate_numforms,
    generate_vbforms,
    output_manual_forms,
)

from .snapshot_io import canonicalize_form_rows, parse_form_output, read_jsonl_gz

if TYPE_CHECKING:
    from wyrdcraeft.services.morphology.session import GeneratorSession

pytestmark = pytest.mark.morphology

DATA_DIR = Path(__file__).resolve().parent / "data"

STAGE_TO_PATH = {
    "manual": DATA_DIR / "forms_manual_subset.jsonl.gz",
    "verb": DATA_DIR / "forms_verb_subset.jsonl.gz",
    "adj": DATA_DIR / "forms_adj_subset.jsonl.gz",
    "adv": DATA_DIR / "forms_adv_subset.jsonl.gz",
    "num": DATA_DIR / "forms_num_subset.jsonl.gz",
    "noun": DATA_DIR / "forms_noun_subset.jsonl.gz",
}


def _stage_rows(session: GeneratorSession, *, stage: str) -> list[dict[str, str]]:
    output = io.StringIO()
    if stage == "manual":
        output_manual_forms(session, output)
    elif stage == "verb":
        generate_vbforms(session, output)
    elif stage == "adj":
        generate_adjforms(session, output)
    elif stage == "adv":
        generate_advforms(session, output)
    elif stage == "num":
        generate_numforms(session, output)
    elif stage == "noun":
        generate_nounforms(session, output)
    else:
        msg = f"Unknown stage: {stage}"
        raise ValueError(msg)

    return canonicalize_form_rows(parse_form_output(output.getvalue()))


@pytest.mark.parametrize(
    "stage",
    ["manual", "verb", "adj", "adv", "num", "noun"],
)
def test_stage_output_matches_snapshot(
    subset_session: GeneratorSession,
    stage: str,
) -> None:
    observed = _stage_rows(subset_session, stage=stage)
    expected = read_jsonl_gz(STAGE_TO_PATH[stage])

    assert len(observed) == len(expected)
    assert observed == expected
