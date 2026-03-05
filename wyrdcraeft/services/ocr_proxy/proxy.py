from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

import yaml  # type: ignore[import-untyped]

if TYPE_CHECKING:
    from wyrdcraeft.services.ocr_proxy.config import ProxyConfig

#: Prefix marker that must exist at content start for YAML front matter detection.
YAML_FRONT_MATTER_PREFIX = "---\n"
#: Closing marker used to terminate YAML front matter.
YAML_FRONT_MATTER_SUFFIX = "\n---\n"


def _coerce_non_negative_int(value: object) -> int | None:  # noqa: PLR0911
    """
    Coerce a value to a non-negative integer.

    Args:
        value: Candidate numeric value from request payload.

    Returns:
        Parsed integer when valid, else ``None``.

    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, float):
        if value.is_integer() and value >= 0:
            return int(value)
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            parsed = int(stripped)
        except ValueError:
            return None
        return parsed if parsed >= 0 else None
    return None


def summarize_chat_request(  # noqa: PLR0912
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Build a redacted request summary safe for operational logs.

    Args:
        payload: Incoming chat completion payload.

    Returns:
        Redacted summary including counts and token settings only.

    """
    text_segments = 0
    image_segments = 0
    image_url_total_chars = 0
    summary: dict[str, Any] = {
        "model": payload.get("model"),
        "message_count": 0,
        "text_segments": text_segments,
        "image_segments": image_segments,
        "image_url_total_chars": image_url_total_chars,
    }

    if "max_tokens" in payload:
        summary["max_tokens"] = payload["max_tokens"]
    if "max_completion_tokens" in payload:
        summary["max_completion_tokens"] = payload["max_completion_tokens"]
    if "temperature" in payload:
        summary["temperature"] = payload["temperature"]
    if "top_p" in payload:
        summary["top_p"] = payload["top_p"]

    messages = payload.get("messages")
    if not isinstance(messages, list):
        return summary

    summary["message_count"] = len(messages)
    for message in messages:
        if not isinstance(message, Mapping):
            continue
        content = message.get("content")
        if isinstance(content, str):
            text_segments += 1
            continue
        if not isinstance(content, list):
            continue

        for part in content:
            if not isinstance(part, Mapping):
                continue
            part_type = part.get("type")
            if part_type == "text":
                text_segments += 1
            if part_type != "image_url":
                continue

            image_segments += 1
            image_url_obj = part.get("image_url")
            if not isinstance(image_url_obj, Mapping):
                continue
            url_value = image_url_obj.get("url")
            if isinstance(url_value, str):
                image_url_total_chars += len(url_value)

    summary["text_segments"] = text_segments
    summary["image_segments"] = image_segments
    summary["image_url_total_chars"] = image_url_total_chars
    return summary


def clamp_chat_request_payload(
    payload: Mapping[str, Any], config: ProxyConfig
) -> tuple[dict[str, Any], list[str]]:
    """
    Apply request mutation policy before forwarding upstream.

    Args:
        payload: Original chat completion request payload.
        config: Runtime proxy configuration.

    Returns:
        Tuple of modified payload and human-readable mutation notes.

    """
    forwarded = copy.deepcopy(dict(payload))
    notes: list[str] = []

    max_tokens = _coerce_non_negative_int(forwarded.get("max_tokens"))
    max_completion_tokens = _coerce_non_negative_int(
        forwarded.get("max_completion_tokens")
    )
    has_token_field = max_tokens is not None or max_completion_tokens is not None

    if max_tokens is not None:
        clamped = min(max_tokens, config.max_tokens_cap)
        forwarded["max_tokens"] = clamped
        if clamped != max_tokens:
            notes.append(f"clamped max_tokens {max_tokens} -> {clamped}")
    if max_completion_tokens is not None:
        clamped = min(max_completion_tokens, config.max_tokens_cap)
        forwarded["max_completion_tokens"] = clamped
        if clamped != max_completion_tokens:
            notes.append(
                "clamped max_completion_tokens "
                f"{max_completion_tokens} -> {clamped}"
            )
    if not has_token_field:
        forwarded["max_tokens"] = config.max_tokens_cap
        notes.append(f"set max_tokens to cap {config.max_tokens_cap} (field missing)")

    if config.clamp_both_token_fields:
        synchronized = config.max_tokens_cap
        for key in ("max_tokens", "max_completion_tokens"):
            value = _coerce_non_negative_int(forwarded.get(key))
            if value is not None:
                synchronized = min(synchronized, value)
        synchronized = min(synchronized, config.max_tokens_cap)
        forwarded["max_tokens"] = synchronized
        forwarded["max_completion_tokens"] = synchronized
        notes.append(
            "synchronized max_tokens and "
            f"max_completion_tokens to {synchronized}"
        )

    if config.temperature_override is not None:
        previous = forwarded.get("temperature")
        forwarded["temperature"] = config.temperature_override
        if previous != config.temperature_override:
            notes.append(
                f"overrode temperature {previous!r} -> {config.temperature_override}"
            )
    if config.top_p_override is not None:
        previous = forwarded.get("top_p")
        forwarded["top_p"] = config.top_p_override
        if previous != config.top_p_override:
            notes.append(f"overrode top_p {previous!r} -> {config.top_p_override}")

    return forwarded, notes


def _extract_yaml_front_matter_and_body(content: str) -> tuple[str, str] | None:
    """
    Split assistant output into YAML front matter and trailing body text.

    Args:
        content: Assistant output content from upstream.

    Returns:
        Tuple of ``(yaml_text, body_text)`` when delimiters exist, else ``None``.

    """
    if not content.startswith(YAML_FRONT_MATTER_PREFIX):
        return None

    closing_index = content.find(
        YAML_FRONT_MATTER_SUFFIX,
        len(YAML_FRONT_MATTER_PREFIX),
    )
    if closing_index < 0:
        return None

    yaml_text = content[len(YAML_FRONT_MATTER_PREFIX) : closing_index]
    body_start = closing_index + len(YAML_FRONT_MATTER_SUFFIX)
    body_text = content[body_start:]
    return yaml_text, body_text


def is_good_enough_length_completion(
    content: str, min_body_chars: int, min_body_lines: int
) -> bool:
    """
    Evaluate whether a ``finish_reason=length`` completion is acceptable.

    Args:
        content: Assistant message text content.
        min_body_chars: Minimum post-YAML body character threshold.
        min_body_lines: Minimum post-YAML non-empty line threshold.

    Returns:
        ``True`` when content satisfies conservative YAML-plus-body requirements.

    """
    parts = _extract_yaml_front_matter_and_body(content)
    if parts is None:
        return False
    yaml_text, body_text = parts

    try:
        parsed = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        return False

    if not isinstance(parsed, Mapping):
        return False

    body_stripped = body_text.strip()
    non_empty_lines = [line for line in body_stripped.splitlines() if line.strip()]
    has_char_threshold = len(body_stripped) >= min_body_chars
    has_line_threshold = len(non_empty_lines) >= min_body_lines
    return has_char_threshold or has_line_threshold


def maybe_override_finish_reason(  # noqa: PLR0911
    response_json: Mapping[str, Any], config: ProxyConfig
) -> tuple[dict[str, Any], bool]:
    """
    Rewrite ``finish_reason`` from ``length`` to ``stop`` when safe.

    Args:
        response_json: Upstream chat completion response.
        config: Runtime proxy configuration.

    Returns:
        Tuple of response payload and a boolean indicating whether rewrite happened.

    """
    if not config.override_length_to_stop:
        return dict(response_json), False

    choices = response_json.get("choices")
    if not isinstance(choices, list) or not choices:
        return dict(response_json), False

    first_choice = choices[0]
    if not isinstance(first_choice, Mapping):
        return dict(response_json), False
    if first_choice.get("finish_reason") != "length":
        return dict(response_json), False

    message = first_choice.get("message")
    if not isinstance(message, Mapping):
        return dict(response_json), False

    content = message.get("content")
    if not isinstance(content, str):
        return dict(response_json), False

    if not is_good_enough_length_completion(
        content=content,
        min_body_chars=config.min_body_chars_after_yaml,
        min_body_lines=config.min_body_lines_after_yaml,
    ):
        return dict(response_json), False

    rewritten = copy.deepcopy(dict(response_json))
    rewritten_choices = rewritten.get("choices")
    if not isinstance(rewritten_choices, list):
        return rewritten, False

    rewrote = False
    for choice in rewritten_choices:
        if not isinstance(choice, dict):
            continue
        if choice.get("finish_reason") != "length":
            continue
        choice["finish_reason"] = "stop"
        rewrote = True

    return rewritten, rewrote
