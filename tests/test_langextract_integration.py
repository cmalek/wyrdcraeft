from __future__ import annotations

import os
from pathlib import Path

import pytest

from oe_json_extractor.schema.models import TextMetadata
from oe_json_extractor.ingest.extractors.langextract_runner import (
    run_langextract_to_canonical,
    LangExtractConfig,
)


@pytest.mark.skipif(
    not os.environ.get("LANGEXTRACT_API_KEY"),
    reason="LANGEXTRACT_API_KEY not set; skipping live langextract integration test.",
)
def test_langextract_fixtures_smoke() -> None:
    fixtures = Path(__file__).parent / "fixtures"
    prompt = (
        Path(__file__).resolve().parents[1]
        / "oe_json_extractor"
        / "prompts"
        / "oe_extract_v1.1.md"
    )

    text = (fixtures / "fixture_dialogue.txt").read_text(encoding="utf-8").strip()
    meta = TextMetadata(title="Fixture Dialogue", source="tests/fixtures")

    doc = run_langextract_to_canonical(
        text=text,
        metadata=meta,
        prompt_path=prompt,
        config=LangExtractConfig(model_id="gemini-2.5-flash", show_progress=False),
        fixtures_dir=fixtures,
    )

    assert doc.metadata.title == "Fixture Dialogue"
    # Should produce some content
    assert doc.content.sections and len(doc.content.sections) >= 1
