from __future__ import annotations

from pathlib import Path

import pytest

from .parity_harness import assert_snapshot_parity

pytestmark = pytest.mark.morphology


DATA_DIR = Path(__file__).resolve().parent / "data"
FULL_FLOW_SUBSET_PATH = DATA_DIR / "full_flow_subset.jsonl.gz"


def test_parity_harness_matches_subset_snapshot(subset_session) -> None:
    assert_snapshot_parity(subset_session, FULL_FLOW_SUBSET_PATH)
