from __future__ import annotations

import json
from contextlib import suppress
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from any_llm import completion

from oe_ingest.schema.models import OldEnglishText, TextMetadata

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class AnyLLMConfig:
    """Configuration for Python any-llm."""

    #: The provider to use for any-llm.
    provider: str = "ollama"
    #: The model ID to use for any-llm.
    model_id: str = "qwen2.5:14b-instruct"
    #: The temperature to use for any-llm.
    temperature: float = 0.0
    #: The maximum number of tokens to use for any-llm.
    max_tokens: int = 4096
    #: The timeout in seconds for any-llm.
    timeout_s: int = 120


def _load_prompt(prompt_path: Path) -> str:
    """
    Load a prompt from a file.

    Args:
        prompt_path: The path to the prompt to load.

    Returns:
        The prompt as a string.

    """
    return prompt_path.read_text(encoding="utf-8").strip()


def _messages(prompt: str, text: str) -> list[dict[str, str]]:
    """
    Create a list of messages for any-llm.

    Args:
        prompt: The prompt to use.
        text: The text to use.

    Returns:
        A list of messages.

    """
    return [
        {"role": "system", "content": prompt},
        {"role": "user", "content": "INPUT TEXT (Old English only):\n\n" + text},
    ]


def _extract_json_object(raw: str) -> dict[str, Any]:
    """
    Extract a JSON object from a string.

    Args:
        raw: The string to extract the JSON object from.

    Returns:
        The JSON object as a dictionary.

    """
    s = raw.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s
        s = s.rsplit("```", 1)[0].strip()
    with suppress(json.JSONDecodeError):
        obj = json.loads(s)
        if isinstance(obj, dict):
            return obj
    start = s.find("{")
    if start < 0:
        msg = "No JSON object found in output"
        raise ValueError(msg)
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(s)):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":  # escape
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(s[start : i + 1])
    msg = "Could not extract JSON object from output"
    raise ValueError(msg)


def run_anyllm_to_canonical(
    *,
    text: str,
    metadata: TextMetadata,
    prompt_path: Path,
    prompt_preamble: str | None = None,
    config: AnyLLMConfig | None = None,
) -> OldEnglishText:
    """
    Run any-llm over `text` and return a validated
    :class:`~oe_ingest.schema.models.OldEnglishText`.

    Keyword Args:
        text: The text to extract from.
        metadata: The metadata for the text.
        prompt_path: The path to the prompt to use.
        prompt_preamble: The preamble to use for the prompt.
        config: The configuration for any-llm.

    Returns:
        A validated :class:`~oe_ingest.schema.models.OldEnglishText`.

    """
    cfg = config or AnyLLMConfig()
    prompt = _load_prompt(prompt_path)
    if prompt_preamble:
        prompt = prompt_preamble.rstrip() + "\n\n" + prompt
    raw = completion(
        model=cfg.model_id,
        messages=_messages(prompt, text),
        provider=cfg.provider,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        timeout=cfg.timeout_s,
    )
    if not isinstance(raw, str):
        raw = str(raw)
    obj = _extract_json_object(raw)
    if "metadata" not in obj:
        obj["metadata"] = metadata.model_dump(mode="json", exclude_none=True)
    return OldEnglishText.model_validate(obj)
