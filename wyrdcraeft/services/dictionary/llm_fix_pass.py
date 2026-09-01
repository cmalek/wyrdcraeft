"""Optional LLM repair pass for Bosworth-Toller parse warnings."""

from __future__ import annotations

import dataclasses
import json
import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Final, cast

import httpx
from pydantic import BaseModel, ConfigDict, ValidationError

from wyrdcraeft.models.dictionary import legacy_bt_sense

if TYPE_CHECKING:
    from pathlib import Path

    from wyrdcraeft.services.dictionary.line_parser import ParsedBTLine

#: Module logger for LLM repair failures.
logger = logging.getLogger(__name__)

#: Default Ollama generate endpoint for local dictionary repair.
DEFAULT_OLLAMA_ENDPOINT: Final[str] = "http://localhost:11434/api/generate"
#: HTTP timeout for one LLM repair request.
_LLM_TIMEOUT_S: Final[float] = 120.0
#: Extracts JSON object from optional markdown code fences.
_JSON_FENCE_RE: Final[re.Pattern[str]] = re.compile(
    r"```(?:json)?\s*(\{.*?\})\s*```",
    re.DOTALL,
)


class LLMFixSenseModel(BaseModel):
    """One repaired sense returned by the local LLM."""

    #: Pydantic config rejecting hallucinated keys.
    model_config = ConfigDict(extra="forbid")

    #: Sense label such as ``I`` or ``II``.
    sense_label: str
    #: English gloss without attestations.
    gloss_en: str


class LLMFixResponseModel(BaseModel):
    """Strict JSON schema for dictionary repair LLM output."""

    #: Pydantic config rejecting hallucinated keys.
    model_config = ConfigDict(extra="forbid")

    #: Ordered repaired senses.
    senses: list[LLMFixSenseModel]
    #: Optional etymology text when the model can infer it.
    etymology: str | None = None


@dataclass(frozen=True)
class BTParseWarning:
    """
    One parse warning emitted during dictionary indexing.

    Attributes:
        line_no: One-based source line number in ``oe_bt.txt``.
        body: Raw HTML body field from the source line.
        headword: Display headword used as LLM context.
        pos_hint: Normalized POS label or ``unknown``.
        failure_reason: Diagnostic code describing the parse failure.
        detail: Optional human-readable diagnostic context.

    """

    #: One-based source line number.
    line_no: int
    #: Raw HTML body from the source line.
    body: str
    #: Display headword for LLM context.
    headword: str
    #: Normalized POS hint for the LLM prompt.
    pos_hint: str
    #: Machine-readable warning reason.
    failure_reason: str
    #: Optional human-readable diagnostic context.
    detail: str = ""

    def to_json(self) -> dict[str, object]:
        """
        Serialize the warning to a JSON-friendly mapping.

        Returns:
            Mapping suitable for one ``parse_warnings.jsonl`` record.

        """
        return {
            "line_no": self.line_no,
            "body": self.body,
            "headword": self.headword,
            "pos_hint": self.pos_hint,
            "failure_reason": self.failure_reason,
            **({"detail": self.detail} if self.detail else {}),
        }

    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> BTParseWarning:
        """
        Parse one warning record from JSONL.

        Args:
            payload: Decoded JSON object from ``parse_warnings.jsonl``.

        Returns:
            Parsed warning record.

        """
        return cls(
            line_no=int(payload["line_no"]),
            body=str(payload["body"]),
            headword=str(payload["headword"]),
            pos_hint=str(payload["pos_hint"]),
            failure_reason=str(payload["failure_reason"]),
            detail=str(payload.get("detail", "")),
        )


@dataclass
class LLMFixStats:
    """
    Summary counts from one optional LLM repair pass.

    Attributes:
        attempted: Warning records submitted to the LLM.
        succeeded: Warning records whose JSON validated and patched a line.
        failed: Warning records that could not be repaired.

    """

    #: Warning records submitted to the LLM.
    attempted: int = 0
    #: Warning records successfully repaired.
    succeeded: int = 0
    #: Warning records that failed validation or HTTP.
    failed: int = 0


class BTLLMFixPass:
    """
    Repair flagged dictionary parse lines using a local Ollama-compatible LLM.

    Args:
        model: Ollama model identifier.
        endpoint: Ollama ``/api/generate`` endpoint URL.
        timeout_s: HTTP timeout for one generate request.
        client: Optional injected HTTP client for tests.

    """

    def __init__(
        self,
        *,
        model: str | None = None,
        endpoint: str = DEFAULT_OLLAMA_ENDPOINT,
        timeout_s: float = _LLM_TIMEOUT_S,
        client: httpx.Client | None = None,
    ) -> None:
        """
        Initialize LLM repair settings.

        Keyword Args:
            model: Ollama model identifier.
            endpoint: Ollama ``/api/generate`` endpoint URL.
            timeout_s: HTTP timeout for one generate request.
            client: Optional injected HTTP client for tests.

        """
        #: Ollama model identifier.
        self.model: str = model or "qwen2.5:14b-instruct"
        #: Ollama generate endpoint URL.
        self.endpoint: str = endpoint
        #: HTTP timeout in seconds.
        self.timeout_s: float = timeout_s
        #: Optional injected HTTP client.
        self._client: httpx.Client | None = client

    def apply_fixes(
        self,
        warnings_path: Path,
        parsed_lines: list[ParsedBTLine],
    ) -> LLMFixStats:
        """
        Read warning records and patch matching parsed lines in place.

        Args:
            warnings_path: ``parse_warnings.jsonl`` path produced by indexing.
            parsed_lines: Parsed line list to mutate before editorial merge.

        Returns:
            Repair attempt statistics.

        Side Effects:
            Mutates ``parsed_lines`` entries when LLM repair succeeds.

        """
        stats = LLMFixStats()
        if not warnings_path.is_file():
            return stats

        line_index = {
            parsed.raw_line.line_no: index
            for index, parsed in enumerate(parsed_lines)
            if parsed.raw_line is not None
        }

        with warnings_path.open(encoding="utf-8") as handle:
            for raw in handle:
                stripped = raw.strip()
                if not stripped:
                    continue
                stats.attempted += 1
                try:
                    warning = BTParseWarning.from_json(json.loads(stripped))
                except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                    stats.failed += 1
                    logger.warning("Skipping invalid warning JSONL record")
                    continue

                parsed_index = line_index.get(warning.line_no)
                if parsed_index is None:
                    stats.failed += 1
                    logger.warning(
                        "No parsed line for warning line_no=%s",
                        warning.line_no,
                    )
                    continue

                fix = self.repair_warning(warning)
                if fix is None:
                    stats.failed += 1
                    continue

                parsed_lines[parsed_index] = self.patch_parsed_line(
                    parsed_lines[parsed_index],
                    fix,
                )
                stats.succeeded += 1

        return stats

    def repair_warning(self, warning: BTParseWarning) -> LLMFixResponseModel | None:
        """
        Call the configured LLM to repair one warning record.

        Args:
            warning: Parse warning emitted during indexing.

        Returns:
            Validated repair payload, or ``None`` when repair fails.

        """
        prompt = _build_prompt(warning)
        try:
            raw_response = self._call_ollama(prompt)
        except (httpx.HTTPError, OSError) as exc:
            logger.warning(
                "LLM HTTP failure for line_no=%s: %s",
                warning.line_no,
                exc,
            )
            return None

        try:
            payload = _extract_json_object(raw_response)
            return LLMFixResponseModel.model_validate(payload)
        except (ValidationError, ValueError, json.JSONDecodeError) as exc:
            logger.warning(
                "LLM JSON validation failure for line_no=%s: %s",
                warning.line_no,
                exc,
            )
            return None

    def patch_parsed_line(
        self,
        parsed: ParsedBTLine,
        fix: LLMFixResponseModel,
    ) -> ParsedBTLine:
        """
        Merge validated LLM senses and etymology into one parsed line.

        Args:
            parsed: Deterministic parse result to patch.
            fix: Validated LLM repair payload.

        Returns:
            Updated parsed line preserving deterministic fields.

        """
        senses = tuple(
            legacy_bt_sense(sense.sense_label, sense.gloss_en)
            for sense in fix.senses
        )
        if fix.etymology and not parsed.etymology_blocks:
            return dataclasses.replace(
                parsed,
                senses=senses,
                etymology_blocks=(fix.etymology,),
            )
        return dataclasses.replace(parsed, senses=senses)

    def _call_ollama(self, prompt: str) -> str:
        """
        POST one generate request to the configured Ollama endpoint.

        Args:
            prompt: Fully formatted repair prompt.

        Returns:
            Raw ``response`` text from Ollama.

        Raises:
            httpx.HTTPError: The HTTP request fails.
            OSError: The response body cannot be decoded.

        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }
        if self._client is not None:
            response = self._client.post(
                self.endpoint,
                json=payload,
                timeout=self.timeout_s,
            )
        else:
            with httpx.Client(timeout=self.timeout_s) as client:
                response = client.post(self.endpoint, json=payload)
        response.raise_for_status()
        body = response.json()
        return str(body.get("response", ""))


def write_parse_warnings(path: Path, warnings: list[BTParseWarning]) -> None:
    """
    Write parse warnings as JSONL.

    Args:
        path: Destination ``parse_warnings.jsonl`` path.
        warnings: Warning records collected during indexing.

    Side Effects:
        Creates parent directories and writes UTF-8 JSONL.

    """
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(warning.to_json(), ensure_ascii=False) for warning in warnings]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def append_parse_warnings(path: Path, warnings: list[BTParseWarning]) -> None:
    """
    Append parse warnings to an existing JSONL file.

    Args:
        path: Destination ``parse_warnings.jsonl`` path.
        warnings: Additional warning records to append.

    Side Effects:
        Creates parent directories when needed and appends UTF-8 JSONL rows.

    """
    if not warnings:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(warning.to_json(), ensure_ascii=False) for warning in warnings]
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def _build_prompt(warning: BTParseWarning) -> str:
    """
    Build the Ollama prompt for one warning record.

    Args:
        warning: Parse warning emitted during indexing.

    Returns:
        Prompt instructing the model to return strict JSON.

    """
    return (
        "You repair Bosworth-Toller Old English dictionary parse failures.\n"
        "Return ONLY valid JSON matching this schema:\n"
        '{"senses":[{"sense_label":"I","gloss_en":"English definition"}],'
        '"etymology":"optional bracket etymology text"}\n'
        "Rules:\n"
        "- senses must contain English-only glosses with no Old English citations.\n"
        "- sense_label may be empty or Roman numerals such as I, II, A.\n"
        "- omit etymology when unknown.\n"
        "- do not include any keys other than senses and etymology.\n\n"
        f"failure_reason: {warning.failure_reason}\n"
        f"headword: {warning.headword}\n"
        f"pos_hint: {warning.pos_hint}\n"
        f"line_no: {warning.line_no}\n"
        f"body: {warning.body}\n"
    )


def _extract_json_object(raw_response: str) -> dict[str, object]:
    """
    Parse a JSON object from raw LLM text.

    Args:
        raw_response: Model output, optionally wrapped in markdown fences.

    Returns:
        Decoded JSON object mapping.

    Raises:
        ValueError: No JSON object could be extracted.
        json.JSONDecodeError: The extracted text is not valid JSON.

    """
    text = raw_response.strip()
    fence_match = _JSON_FENCE_RE.search(text)
    if fence_match is not None:
        text = fence_match.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        msg = "LLM response did not contain a JSON object"
        raise ValueError(msg)
    return cast("dict[str, object]", json.loads(text[start : end + 1]))
