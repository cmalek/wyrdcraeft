from __future__ import annotations

import json
import os
from pathlib import Path

from wyrdcraeft.ingest.extractors.langextract_runner import (
    AnyLLMConfig,
    run_anyllm_to_canonical,
)
from wyrdcraeft.models import AnyLLMConfig

from wyrdcraeft.models import TextMetadata

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures"
PROMPTS = ROOT / "oe_ingest" / "prompts"

CASES = [
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
]


def main() -> None:
    cfg = AnyLLMConfig(
        provider=os.environ.get("ANYLLM_PROVIDER", "ollama"),
        model_id=os.environ.get("ANYLLM_MODEL", "qwen2.5:14b-instruct"),
        temperature=float(os.environ.get("ANYLLM_TEMPERATURE", "0.0")),
    )
    for txt, out, prompt, title in CASES:
        doc = run_anyllm_to_canonical(
            text=(FIX / txt).read_text(encoding="utf-8").strip(),
            metadata=TextMetadata(title=title, source="tests/fixtures"),
            prompt_path=(PROMPTS / prompt),
            config=cfg,
        )
        (FIX / out).write_text(
            json.dumps(
                doc.model_dump(mode="json", exclude_none=False),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print("Wrote", out)


if __name__ == "__main__":
    main()
