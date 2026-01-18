"""
Prompt regression and schema validation tests.

These tests are designed to be stable and runnable without external LLM access by:
- Validating expected JSON fixtures against the Pydantic schema.

When you integrate langextract, add an integration test layer that:
- Runs langextract with oe_extract_vX prompt
- Produces JSON
- Validates against the schema
- Compares to expected snapshots (with approved diffs)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from oe_json_extractor.models.schema import Section


FIX = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(
    "expected_name",
    ["expected_prose.json", "expected_poetry.json", "expected_dialogue.json"],
)
def test_expected_json_is_schema_valid(expected_name: str) -> None:
    data = json.loads((FIX / expected_name).read_text(encoding="utf-8"))
    assert "sections" in data
    # Validate each top-level section
    for sec in data["sections"]:
        Section.model_validate(sec)


def _canonicalize(obj):
    "Deterministic ordering for stable snapshot comparisons."
    if isinstance(obj, dict):
        return {k: _canonicalize(obj[k]) for k in sorted(obj)}
    if isinstance(obj, list):
        return [_canonicalize(x) for x in obj]
    return obj


@pytest.mark.parametrize(
    ("text_name", "expected_name"),
    [
        ("fixture_prose.txt", "expected_prose.json"),
        ("fixture_poetry.txt", "expected_poetry.json"),
        ("fixture_dialogue.txt", "expected_dialogue.json"),
    ],
)
def test_snapshot_regression_contract(text_name: str, expected_name: str) -> None:
    """
    Placeholder regression test.

    Today: just ensures the expected snapshot is stable and canonicalizable.
    Future: replace `produced = ...` with langextract output and compare.
    """
    expected = json.loads((FIX / expected_name).read_text(encoding="utf-8"))
    produced = expected  # TODO: plug in langextract output here

    assert _canonicalize(produced) == _canonicalize(expected)
