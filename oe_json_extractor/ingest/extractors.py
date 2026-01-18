from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import langextract as lx

from ..models import (
    OldEnglishText,
    TextMetadata,
)


@dataclass(frozen=True)
class LangExtractConfig:
    """
    Configuration for langextract integration.

    Notes:
        - For Gemini models, schema constraints are typically supported; keep
        use_schema_constraints=True.
        - For OpenAI models, langextract currently requires fence_output=True and
        use_schema_constraints=False (per upstream documentation).

    """

    #: The model ID to use for langextract.
    model_id: str = "gemini-2.5-flash"
    #: The API key to use for langextract.
    api_key: str | None = None
    #: The temperature to use for langextract.
    temperature: float | None = None
    #: The maximum character buffer to use for langextract.
    max_char_buffer: int = 1200
    #: The number of extraction passes to use for langextract.
    extraction_passes: int = 2
    #: The maximum number of workers to use for langextract.
    max_workers: int = 8
    #: The batch length to use for langextract.
    batch_length: int = 10
    #: Whether to show progress for langextract.
    show_progress: bool = True


def _provider_defaults_for_model(model_id: str) -> dict[str, Any]:
    """
    Choose conservative defaults based on provider capability.

    Source: langextract README notes that OpenAI requires fencing and no schema
    constraints.

    Args:
        model_id: The model ID to use for langextract.

    Returns:
        A dictionary of provider defaults.

    """
    lower = model_id.lower()
    if lower.startswith(("gpt-", "o1-", "o3-", "o4-")):
        return {"fence_output": True, "use_schema_constraints": False}
    return {"fence_output": None, "use_schema_constraints": True}


def _load_prompt(prompt_path: Path) -> str:
    return prompt_path.read_text(encoding="utf-8").strip()


def _build_examples_from_fixtures(fixtures_dir: Path) -> list[lx.data.ExampleData]:
    """
    Build few-shot examples that define the output schema via attributes.

    We use ONE extraction per example:
    - extraction_class: "oe_document"
    - extraction_text: the full example text (verbatim) for grounding/alignment
    - attributes: {"sections": <canonical section list>}

    Args:
        fixtures_dir: The directory to load the fixtures from.

    Returns:
        A list of few-shot examples.

    """
    expected_files = [
        ("fixture_prose.txt", "expected_prose.json"),
        ("fixture_poetry.txt", "expected_poetry.json"),
        ("fixture_dialogue.txt", "expected_dialogue.json"),
    ]

    examples: list[lx.data.ExampleData] = []
    for text_name, expected_name in expected_files:
        text = (fixtures_dir / text_name).read_text(encoding="utf-8").strip()
        expected = json.loads(
            (fixtures_dir / expected_name).read_text(encoding="utf-8")
        )
        sections = expected["sections"]

        examples.append(
            lx.data.ExampleData(
                text=text,
                extractions=[
                    lx.data.Extraction(
                        extraction_class="oe_document",
                        extraction_text=text,  # verbatim grounding for alignment
                        attributes={"sections": sections},
                    )
                ],
            )
        )
    return examples


def _wrap_sections_as_root_content(sections: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Our Pydantic model expects a single root Section (with optional
    subsections).  Wrap the extracted :paramref:`sections` list as
    ``root.content.sections``.

    Args:
        sections: The sections to wrap.

    Returns:
        A dictionary of the wrapped sections.

    """
    return {
        "title": None,
        "number": None,
        "sections": sections,
        "paragraphs": None,
        "lines": None,
        "source_page": None,
        "confidence": None,
    }


def run_langextract_to_canonical(
    *,
    text: str,
    metadata: TextMetadata,
    prompt_path: Path,
    config: LangExtractConfig | None = None,
    fixtures_dir: Path | None = None,
) -> OldEnglishText:
    """
    Run langextract over `text` and return a validated
    :class:`~oe_json_extractor.schema.models.OldEnglishText`.

    This function is intended to be called on reasonably-sized chunks (2-4k
    tokens / a few KB).  Use your rule-based pre-parser to chunk by section
    before calling this.

    Requirements:
        - :envvar:`LANGEXTRACT_API_KEY` env var is used by default if config.api_key
        is ``None``.
        - The prompt is loaded from :paramref:`prompt_path`.
        - Few-shot examples are built from :paramref:`fixtures_dir`; by default,
        this is the repository test fixtures directory.

    Keyword Args:
        text: The text to extract from.
        metadata: The metadata for the text.
        prompt_path: The path to the prompt to use.
        config: The configuration for langextract.
        fixtures_dir: The directory to load the fixtures from.

    Raises:
        ValueError: If langextract returned no extractions.
        TypeError: If langextract output missing ``attributes.sections`` list.

    Returns:
        A validated :class:`~oe_json_extractor.schema.models.OldEnglishText`.

    """
    cfg = config or LangExtractConfig()
    api_key = cfg.api_key or os.environ.get("LANGEXTRACT_API_KEY")

    prompt = _load_prompt(prompt_path)
    if fixtures_dir is None:
        # Default to the repository test fixtures
        fixtures_dir = Path(__file__).resolve().parents[3] / "tests" / "fixtures"
    examples = _build_examples_from_fixtures(fixtures_dir)

    provider_defaults = _provider_defaults_for_model(cfg.model_id)

    result = lx.extract(
        text_or_documents=text,
        prompt_description=prompt,
        examples=examples,
        model_id=cfg.model_id,
        api_key=api_key,
        temperature=cfg.temperature,
        max_char_buffer=cfg.max_char_buffer,
        extraction_passes=cfg.extraction_passes,
        max_workers=cfg.max_workers,
        batch_length=cfg.batch_length,
        show_progress=cfg.show_progress,
        **provider_defaults,
    )

    # langextract returns an AnnotatedDocument for single text input.
    extractions = getattr(result, "extractions", None)
    if not extractions:
        msg = "langextract returned no extractions"
        raise ValueError(msg)

    # We expect exactly one oe_document extraction. If multiple, take the first
    # matching class.
    chosen = None
    for ex in extractions:
        if getattr(ex, "extraction_class", None) == "oe_document":
            chosen = ex
            break
    if chosen is None:
        chosen = extractions[0]

    attrs = getattr(chosen, "attributes", None) or {}
    sections = attrs.get("sections")
    if not isinstance(sections, list):
        msg = "langextract output missing attributes.sections list"
        raise TypeError(msg)

    doc_payload = {
        "metadata": metadata.model_dump(mode="json", exclude_none=True),
        "content": _wrap_sections_as_root_content(sections),
    }
    return OldEnglishText.model_validate(doc_payload)
