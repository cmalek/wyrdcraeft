from __future__ import annotations

import os
from dataclasses import dataclass

#: Default upstream OpenAI-compatible base URL.
DEFAULT_UPSTREAM_BASE_URL = "http://127.0.0.1:8080/v1"
#: Default host interface for the local proxy server.
DEFAULT_PROXY_HOST = "127.0.0.1"
#: Default TCP port for the local proxy server.
DEFAULT_PROXY_PORT = 8001
#: Default maximum completion token cap applied to forwarded requests.
DEFAULT_MAX_TOKENS_CAP = 1500
#: Default behavior to allow conservative length->stop overrides.
DEFAULT_OVERRIDE_LENGTH_TO_STOP = True
#: Minimum body characters after YAML front matter for "good enough" detection.
DEFAULT_MIN_BODY_CHARS_AFTER_YAML = 50
#: Minimum non-empty body lines after YAML front matter for "good enough" detection.
DEFAULT_MIN_BODY_LINES_AFTER_YAML = 5
#: Default timeout in seconds for upstream HTTP calls.
DEFAULT_UPSTREAM_TIMEOUT_SECONDS = 120.0
#: String values interpreted as true in boolean environment flags.
TRUE_ENV_VALUES = {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class ProxyConfig:
    """
    Immutable runtime configuration for the local olmocr proxy service.

    Args:
        upstream_base_url:
            Base upstream OpenAI-compatible URL, expected to include ``/v1``.
        host: Local bind interface for the proxy process.
        port: Local bind port for the proxy process.
        max_tokens_cap: Global token cap applied to completion request payloads.
        override_length_to_stop: Enables conservative ``length`` to ``stop`` rewrite.
        min_body_chars_after_yaml:
            Minimum body character threshold for rewrite heuristic.
        min_body_lines_after_yaml:
            Minimum non-empty line threshold for rewrite heuristic.
        clamp_both_token_fields:
            If true, set both token fields to one shared clamped value.
        temperature_override:
            Optional forced ``temperature`` value in forwarded requests.
        top_p_override: Optional forced ``top_p`` value in forwarded requests.
        upstream_timeout_seconds: HTTP timeout applied to upstream calls.

    """

    #: Base upstream OpenAI-compatible URL, expected to include ``/v1``.
    upstream_base_url: str = DEFAULT_UPSTREAM_BASE_URL
    #: Local bind interface for the proxy process.
    host: str = DEFAULT_PROXY_HOST
    #: Local bind port for the proxy process.
    port: int = DEFAULT_PROXY_PORT
    #: Global token cap applied to completion request payloads.
    max_tokens_cap: int = DEFAULT_MAX_TOKENS_CAP
    #: Enables conservative ``length`` to ``stop`` rewrite.
    override_length_to_stop: bool = DEFAULT_OVERRIDE_LENGTH_TO_STOP
    #: Minimum body character threshold for rewrite heuristic.
    min_body_chars_after_yaml: int = DEFAULT_MIN_BODY_CHARS_AFTER_YAML
    #: Minimum non-empty line threshold for rewrite heuristic.
    min_body_lines_after_yaml: int = DEFAULT_MIN_BODY_LINES_AFTER_YAML
    #: If true, set both token fields to one shared clamped value.
    clamp_both_token_fields: bool = False
    #: Optional forced ``temperature`` value in forwarded requests.
    temperature_override: float | None = None
    #: Optional forced ``top_p`` value in forwarded requests.
    top_p_override: float | None = None
    #: HTTP timeout applied to upstream calls.
    upstream_timeout_seconds: float = DEFAULT_UPSTREAM_TIMEOUT_SECONDS


def _parse_bool_env(name: str, default: bool) -> bool:
    """
    Parse a boolean environment variable.

    Args:
        name: Environment variable name.
        default: Fallback value when variable is absent.

    Raises:
        ValueError: If value is present but not a recognized boolean literal.

    Returns:
        Parsed boolean value.

    """
    raw = os.getenv(name)
    if raw is None:
        return default

    normalized = raw.strip().lower()
    if normalized in TRUE_ENV_VALUES:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False

    message = f"Invalid boolean value for {name}: {raw!r}"
    raise ValueError(message)


def _parse_int_env(name: str, default: int, *, minimum: int = 1) -> int:
    """
    Parse an integer environment variable with a lower bound.

    Args:
        name: Environment variable name.
        default: Fallback value when variable is absent.

    Keyword Args:
        minimum: Inclusive minimum accepted value.

    Raises:
        ValueError: If value is non-integer or below the minimum.

    Returns:
        Parsed integer value.

    """
    raw = os.getenv(name)
    if raw is None:
        return default

    try:
        parsed = int(raw.strip())
    except ValueError as exc:
        message = f"Invalid integer value for {name}: {raw!r}"
        raise ValueError(message) from exc

    if parsed < minimum:
        message = f"Invalid value for {name}: {parsed}. Expected >= {minimum}."
        raise ValueError(message)
    return parsed


def _parse_optional_float_env(name: str) -> float | None:
    """
    Parse an optional float environment variable.

    Args:
        name: Environment variable name.

    Raises:
        ValueError: If value is present but cannot be parsed as float.

    Returns:
        Float value when present, otherwise ``None``.

    """
    raw = os.getenv(name)
    if raw is None:
        return None

    try:
        return float(raw.strip())
    except ValueError as exc:
        message = f"Invalid float value for {name}: {raw!r}"
        raise ValueError(message) from exc


def _parse_float_env(name: str, default: float, *, minimum: float = 0.0) -> float:
    """
    Parse a required float environment variable with a lower bound.

    Args:
        name: Environment variable name.
        default: Fallback value when variable is absent.

    Keyword Args:
        minimum: Inclusive minimum accepted value.

    Raises:
        ValueError: If value is non-float or below the minimum.

    Returns:
        Parsed float value.

    """
    raw = os.getenv(name)
    if raw is None:
        return default

    try:
        parsed = float(raw.strip())
    except ValueError as exc:
        message = f"Invalid float value for {name}: {raw!r}"
        raise ValueError(message) from exc

    if parsed < minimum:
        message = f"Invalid value for {name}: {parsed}. Expected >= {minimum}."
        raise ValueError(message)
    return parsed


def load_proxy_config() -> ProxyConfig:
    """
    Load proxy runtime configuration from environment variables.

    Environment Variables:
        UPSTREAM_BASE_URL: Upstream OpenAI-compatible base URL.
        PROXY_HOST: Local bind host.
        PROXY_PORT: Local bind port.
        PROXY_MAX_TOKENS_CAP: Completion token clamp ceiling.
        OVERRIDE_LENGTH_TO_STOP: Enables conservative finish-reason override.
        MIN_BODY_CHARS_AFTER_YAML: Minimum body character threshold.
        MIN_BODY_LINES_AFTER_YAML: Minimum non-empty line threshold.
        CLAMP_BOTH_TOKEN_FIELDS:
            Synchronize ``max_tokens`` and ``max_completion_tokens``.
        PROXY_TEMPERATURE_OVERRIDE: Optional forced ``temperature``.
        PROXY_TOP_P_OVERRIDE: Optional forced ``top_p``.
        PROXY_UPSTREAM_TIMEOUT_SECONDS: Upstream request timeout in seconds.

    Returns:
        Parsed immutable proxy configuration.

    """
    return ProxyConfig(
        upstream_base_url=os.getenv("UPSTREAM_BASE_URL", DEFAULT_UPSTREAM_BASE_URL),
        host=os.getenv("PROXY_HOST", DEFAULT_PROXY_HOST),
        port=_parse_int_env("PROXY_PORT", DEFAULT_PROXY_PORT),
        max_tokens_cap=_parse_int_env(
            "PROXY_MAX_TOKENS_CAP",
            DEFAULT_MAX_TOKENS_CAP,
        ),
        override_length_to_stop=_parse_bool_env(
            "OVERRIDE_LENGTH_TO_STOP",
            DEFAULT_OVERRIDE_LENGTH_TO_STOP,
        ),
        min_body_chars_after_yaml=_parse_int_env(
            "MIN_BODY_CHARS_AFTER_YAML",
            DEFAULT_MIN_BODY_CHARS_AFTER_YAML,
            minimum=0,
        ),
        min_body_lines_after_yaml=_parse_int_env(
            "MIN_BODY_LINES_AFTER_YAML",
            DEFAULT_MIN_BODY_LINES_AFTER_YAML,
            minimum=0,
        ),
        clamp_both_token_fields=_parse_bool_env(
            "CLAMP_BOTH_TOKEN_FIELDS", default=False
        ),
        temperature_override=_parse_optional_float_env("PROXY_TEMPERATURE_OVERRIDE"),
        top_p_override=_parse_optional_float_env("PROXY_TOP_P_OVERRIDE"),
        upstream_timeout_seconds=_parse_float_env(
            "PROXY_UPSTREAM_TIMEOUT_SECONDS",
            DEFAULT_UPSTREAM_TIMEOUT_SECONDS,
            minimum=0.001,
        ),
    )
