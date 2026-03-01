from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from .snapshot_io import canonical_sort_rows, read_jsonl_gz, stable_json_lines_digest

if TYPE_CHECKING:
    from wyrdcraeft.services.morphology.session import GeneratorSession

pytestmark = pytest.mark.morphology

DATA_DIR = Path(__file__).resolve().parent / "data"
SNAPSHOT_PATH = DATA_DIR / "paradigms_subset.jsonl.gz"


def _paradigm_rows(session: GeneratorSession) -> list[dict[str, str]]:
    rows = [
        {
            "nid": str(word.nid),
            "title": word.title,
            "verb": str(word.verb),
            "adjective": str(word.adjective),
            "noun": str(word.noun),
            "numeral": str(word.numeral),
            "pspart": str(word.pspart),
            "papart": str(word.papart),
            "vb_paradigm": ";".join(vp.ID for vp in word.vb_paradigm),
            "adj_paradigm": ";".join(word.adj_paradigm),
            "noun_paradigm": ";".join(word.noun_paradigm),
        }
        for word in session.words
    ]
    return canonical_sort_rows(rows, sort_fields=["nid", "title"])


def test_paradigm_assignment_subset_matches_snapshot(
    subset_session: GeneratorSession,
) -> None:
    expected = read_jsonl_gz(SNAPSHOT_PATH)
    observed = _paradigm_rows(subset_session)

    assert len(observed) == len(expected)
    assert stable_json_lines_digest(observed) == stable_json_lines_digest(expected)
