from __future__ import annotations

import json
from pathlib import Path

import pytest
from wyrdcraeft.ingest.pipeline import ingest_auto
from wyrdcraeft.models import TextMetadata

FIX = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(
    ("text_file", "expected_json_file", "title"),
    [
        ("caedmon.txt", "caedmon.json", "Caedmon's Hymn"),
        ("seafarer.txt", "seafarer.json", "The Seafarer"),
        (
            "alfred-gregory-pastoral-care.txt",
            "alfred-gregory-pastoral-care.json",
            "King Alfred’s Preface to Gregory’s Pastoral Care",
        ),
        ("beowulf.txt", "beowulf.json", "Beowulf"),
    ],
)
def test_deterministic_ingestion_regression(
    text_file: str, expected_json_file: str, title: str
) -> None:
    """
    Test that deterministic ingestion of text files matches the golden JSON fixtures.
    """
    source_path = FIX / text_file
    expected_path = FIX / expected_json_file

    # We must match the 'source' path as it appears in the golden fixtures
    # which is relative to the workspace root: 'tests/fixtures/...'
    relative_source = f"tests/fixtures/{text_file}"

    metadata = TextMetadata(title=title, source=relative_source)

    # Ingest using the deterministic path (use_llm=False)
    doc = ingest_auto(source_path, metadata, use_llm=False)

    # Convert to dict for comparison
    # Use indent=2 to match the format saved by the CLI/fixtures
    got_json = doc.model_dump_json(indent=2)
    got = json.loads(got_json)

    expected_json = expected_path.read_text(encoding="utf-8")
    expected = json.loads(expected_json)

    # Compare
    assert got == expected
