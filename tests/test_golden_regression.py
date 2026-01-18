from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from oe_json_extractor.ingest.extractors import (
    AnyLLMConfig,
    LLMExtractor,
)
from oe_json_extractor.models import OldEnglishText, TextMetadata

FIX = Path(__file__).parent / "fixtures"


def _t(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8").strip()


def _j(name: str) -> dict:
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def test_goldens_are_schema_valid() -> None:
    for jf in ["expected_prose.json", "expected_verse.json", "expected_dialogue.json"]:
        OldEnglishText.model_validate(_j(jf))


@pytest.mark.skipif(
    os.environ.get("RUN_LIVE_LLM") != "1",
    reason="Set RUN_LIVE_LLM=1 to run live Qwen regression.",
)
@pytest.mark.parametrize(
    ("text_file", "expected_file", "prompt_file", "title"),
    [
        (
            "fixture_prose.txt",
            "expected_prose.json",
            "qwen_extract_prose_v1.md",
            "Fixture Prose",
        ),
        (
            "fixture_verse.txt",
            "expected_verse.json",
            "qwen_extract_verse_v1.md",
            "Fixture Verse",
        ),
        (
            "fixture_dialogue.txt",
            "expected_dialogue.json",
            "qwen_extract_verse_v1.md",
            "Fixture Dialogue",
        ),
    ],
)
def test_live_qwen_matches_golden(
    text_file: str, expected_file: str, prompt_file: str, title: str
) -> None:
    """
    Test that the live Qwen regression matches the golden regression.

    Args:
        text_file: The text file to test.
        expected_file: The expected file to test.
        prompt_file: The prompt file to test.
        title: The title of the text to test.

    """
    prompt_path = (
        Path(__file__).resolve().parents[1]
        / "oe_json_extractor"
        / "prompts"
        / prompt_file
    )
    config = AnyLLMConfig(
        provider=os.environ.get("ANYLLM_PROVIDER", "ollama"),
        model_id=os.environ.get("ANYLLM_MODEL", "qwen2.5:14b-instruct"),
        temperature=float(os.environ.get("ANYLLM_TEMPERATURE", "0.0")),
    )
    extractor = LLMExtractor(config=config)
    doc = extractor.extract(
        text=_t(text_file),
        metadata=TextMetadata(title=title, source="tests/fixtures"),
        prompt_path=prompt_path,
    )
    got = doc.model_dump(mode="json", exclude_none=False)
    expected = _j(expected_file)

    def strip_conf(x):
        if isinstance(x, dict):
            return {k: strip_conf(v) for k, v in x.items() if k != "confidence"}
        if isinstance(x, list):
            return [strip_conf(v) for v in x]
        return x

    assert strip_conf(got) == strip_conf(expected)
