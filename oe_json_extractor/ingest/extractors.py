from __future__ import annotations

import json
from contextlib import suppress
from typing import Any

from any_llm import completion

from ..models import AnyLLMConfig, OldEnglishText, TextMetadata


class LLMExtractor:
    """
    Extractor for Old English text using LLMs.

    Args:
        config: The configuration for any-llm.

    """

    def __init__(self, config: AnyLLMConfig | None = None) -> None:
        """
        Initialize the extractor.

        Args:
            config: The configuration for any-llm.

        """
        #: The configuration for any-llm.
        self.config = config or AnyLLMConfig()

    def prepare(self, prompt: str, text: str) -> list[dict[str, str]]:
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

    def parse(self, raw: str) -> dict[str, Any]:  # noqa: PLR0912
        """
        Extract a JSON object from a string. This method is used to parse the
        output of any-llm.

        This does th following:

        - Strips away any markdown or code fences.
        - Strips away any explanations or comments.
        - Strips away any metadata.
        - Strips away any schema version.
        - Loads the remaining JSON object from the string.

        Args:
            raw: The string to extract the JSON object from.

        Returns:
            The JSON object as a dictionary.

        """
        s = raw.strip()

        # Handle potential triple backticks or other markdown wrapping
        if s.startswith("```"):
            s = s.split("\n", 1)[1] if "\n" in s else s
            s = s.rsplit("```", 1)[0].strip()

        # Handle potential double-escaping (common with some LLM providers/proxies)
        # If the string starts with { but contains literal \n and \"
        if s.startswith("{") and "\\n" in s:
            try:
                # Try to see if replacing literal escapes makes it valid JSON
                s_unescaped = (
                    s.replace("\\n", "\n").replace('\\"', '"').replace("\\\\", "\\")
                )
                obj = json.loads(s_unescaped)
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                pass

        # Handle case where the entire response is a JSON-encoded string
        if s.startswith('"') and s.endswith('"'):
            with suppress(json.JSONDecodeError):
                s = json.loads(s)

        # Standard JSON attempt
        with suppress(json.JSONDecodeError):
            obj = json.loads(s)
            if isinstance(obj, dict):
                return obj

        # Find the first { and try to extract the JSON object
        start = s.find("{")
        if start < 0:
            msg = f"No JSON object found in output: {s[:100]}..."
            raise ValueError(msg)

        # If we found a {, but it's preceded by characters, or standard parsing failed,
        # try the depth-tracking extraction method
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
                    candidate = s[start : i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        # If depth-tracking candidate fails, it might still be escaped
                        try:
                            candidate_unescaped = (
                                candidate.replace("\\n", "\n")
                                .replace('\\"', '"')
                                .replace("\\\\", "\\")
                            )
                            return json.loads(candidate_unescaped)
                        except json.JSONDecodeError:
                            continue

        msg = "Could not extract JSON object from output"
        raise ValueError(msg)

    def extract(
        self,
        *,
        text: str,
        metadata: TextMetadata,
        prompt: str,
        prompt_preamble: str | None = None,
    ) -> OldEnglishText:
        """
        Run any-llm over `text` and return a validated
        :class:`~oe_ingest.schema.models.OldEnglishText`.

        Keyword Args:
            text: The text to extract from.
            metadata: The metadata for the text.
            prompt: The prompt to use.
            prompt_preamble: The preamble to use for the prompt.

        Returns:
            A validated :class:`~oe_ingest.schema.models.OldEnglishText`.

        """
        if prompt_preamble:
            prompt = prompt_preamble.rstrip() + "\n\n" + prompt
        raw = completion(
            model=self.config.model_id,
            messages=self.prepare(prompt, text),
            provider=self.config.provider,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            timeout=self.config.timeout_s,
            api_key=self.config.api_key,
        )
        if not isinstance(raw, str):
            raw = str(raw)
        obj = self.parse(raw)
        if not obj.get("metadata") or not obj["metadata"].get("title"):
            obj["metadata"] = metadata.model_dump(mode="json", exclude_none=True)
        return OldEnglishText.model_validate(obj)
