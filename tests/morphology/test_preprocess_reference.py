from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from .snapshot_io import canonical_sort_rows, read_jsonl_gz, stable_json_lines_digest

if TYPE_CHECKING:
    from wyrdcraeft.services.morphology.session import GeneratorSession

pytestmark = pytest.mark.morphology

DATA_DIR = Path(__file__).resolve().parent / "data"
SNAPSHOT_PATH = DATA_DIR / "preprocess_subset.jsonl.gz"


def _preprocess_rows(session: GeneratorSession) -> list[dict[str, str]]:
    rows = [
        {
            "nid": str(word.nid),
            "title": word.title,
            "prefix": word.prefix,
            "stem": word.stem,
            "syllables": str(word.syllables),
        }
        for word in session.words
    ]
    return canonical_sort_rows(rows, sort_fields=["nid", "title", "stem", "prefix"])


def test_preprocess_subset_matches_snapshot(subset_session: GeneratorSession) -> None:
    expected = read_jsonl_gz(SNAPSHOT_PATH)
    observed = _preprocess_rows(subset_session)

    assert len(observed) == len(expected)
    assert stable_json_lines_digest(observed) == stable_json_lines_digest(expected)
