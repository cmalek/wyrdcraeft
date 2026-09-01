"""
Prompt regression and schema validation tests.

These tests stay runnable without external LLM access by validating expected
JSON fixtures against the Pydantic schema.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from wyrdcraeft.models import Section

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
