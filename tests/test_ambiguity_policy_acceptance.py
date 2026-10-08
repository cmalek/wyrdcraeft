"""
Measure the ``auto`` ambiguity policy against the user's past decisions.

The labels are the user's own resolutions recovered from the index's git history
(ADR 0019 decision 8; scripts/diacritic/extract_ambiguity_labels.py). The floors
below are the measured values; tighten them when the rule improves and re-run the
script when more keys have been curated.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from wyrdcraeft.services.markup import MacronApplicator

FIXTURE = Path(__file__).parent / "fixtures" / "ambiguity_labels.json"

#: Most homograph keys the ``auto`` policy may wrongly mark (measured).
MAX_WRONGLY_MARKED = 10
#: Fewest same-word keys the ``auto`` policy must mark (measured).
MIN_CORRECTLY_MARKED = 29


@pytest.fixture(scope="module")
def marked_by_label(tmp_path_factory: pytest.TempPathFactory) -> dict[str, list[str]]:
    labels = json.loads(FIXTURE.read_text(encoding="utf-8"))["labels"]
    index_path = tmp_path_factory.mktemp("labels") / "index.json"
    index_path.write_text(
        json.dumps(
            {
                "unique": {},
                "ambiguous": {k: v["options"] for k, v in labels.items()},
                "ambiguous_completed": [],
                "ambiguous_metadata": {},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    applicator = MacronApplicator(index_path, policy="auto")
    marked: dict[str, list[str]] = {"same_word": [], "homograph": []}
    for key, entry in labels.items():
        transformed, _, _, _ = applicator.apply(key, 1, 1)
        if transformed != key:
            marked[entry["label"]].append(key)
    return marked


def test_auto_policy_rarely_marks_a_homograph(marked_by_label):
    assert len(marked_by_label["homograph"]) <= MAX_WRONGLY_MARKED, sorted(
        marked_by_label["homograph"]
    )


def test_auto_policy_still_covers_same_word_keys(marked_by_label):
    assert len(marked_by_label["same_word"]) >= MIN_CORRECTLY_MARKED
