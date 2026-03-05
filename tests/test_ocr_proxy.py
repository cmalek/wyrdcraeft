from __future__ import annotations

from typing import Any

from wyrdcraeft.services.ocr_proxy.config import ProxyConfig
from wyrdcraeft.services.ocr_proxy.proxy import (
    clamp_chat_request_payload,
    maybe_override_finish_reason,
)

#: Sample YAML front matter that aligns with olmocr PageResponse fields.
SAMPLE_YAML_HEADER = (
    "---\n"
    "primary_language: en\n"
    "is_rotation_valid: true\n"
    "rotation_correction: 0\n"
    "is_table: false\n"
    "is_diagram: false\n"
    "---\n"
)
#: Maximum output tokens requested by olmocr in failing local scenarios.
ORIGINAL_MAX_TOKENS = 8000
#: Default proxy cap used in clamping behavior tests.
DEFAULT_PROXY_CAP = 1500


def _proxy_config(**kwargs) -> ProxyConfig:
    return ProxyConfig(**kwargs)


def test_rewrites_length_to_stop_for_valid_yaml_and_body() -> None:
    upstream_response: dict[str, Any] = {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 12345,
        "model": "olmocr-local",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": (
                        SAMPLE_YAML_HEADER
                        + "line 1\nline 2\nline 3\nline 4\nline 5\nline 6\n"
                    ),
                },
                "finish_reason": "length",
            }
        ],
        "usage": {"prompt_tokens": 100, "completion_tokens": 700, "total_tokens": 800},
    }

    rewritten, changed = maybe_override_finish_reason(
        upstream_response,
        _proxy_config(),
    )

    assert changed is True
    assert rewritten["choices"][0]["finish_reason"] == "stop"
    expected_content = upstream_response["choices"][0]["message"]["content"]
    assert rewritten["choices"][0]["message"]["content"] == expected_content
    assert upstream_response["choices"][0]["finish_reason"] == "length"


def test_does_not_rewrite_when_yaml_is_invalid() -> None:
    upstream_response: dict[str, Any] = {
        "choices": [
            {
                "message": {
                    "content": (
                        "---\n"
                        "primary_language: [\n"
                        "---\n"
                        "line 1\nline 2\nline 3\nline 4\nline 5\nline 6\n"
                    )
                },
                "finish_reason": "length",
            }
        ]
    }

    rewritten, changed = maybe_override_finish_reason(
        upstream_response,
        _proxy_config(),
    )

    assert changed is False
    assert rewritten["choices"][0]["finish_reason"] == "length"


def test_does_not_rewrite_when_finish_reason_is_stop() -> None:
    upstream_response: dict[str, Any] = {
        "choices": [
            {
                "message": {
                    "content": SAMPLE_YAML_HEADER
                    + "line 1\nline 2\nline 3\nline 4\nline 5\nline 6\n",
                },
                "finish_reason": "stop",
            }
        ]
    }

    rewritten, changed = maybe_override_finish_reason(
        upstream_response,
        _proxy_config(),
    )

    assert changed is False
    assert rewritten["choices"][0]["finish_reason"] == "stop"


def test_clamps_max_tokens_to_default_cap() -> None:
    incoming_payload = {
        "model": "olmocr-local",
        "messages": [{"role": "user", "content": "hello"}],
        "max_tokens": ORIGINAL_MAX_TOKENS,
    }

    forwarded_payload, notes = clamp_chat_request_payload(
        incoming_payload,
        _proxy_config(),
    )

    assert forwarded_payload["max_tokens"] == DEFAULT_PROXY_CAP
    assert incoming_payload["max_tokens"] == ORIGINAL_MAX_TOKENS
    assert notes == [
        f"clamped max_tokens {ORIGINAL_MAX_TOKENS} -> {DEFAULT_PROXY_CAP}"
    ]
