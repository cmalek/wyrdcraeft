from __future__ import annotations

import logging
import os
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING

import httpx

from wyrdcraeft.services.ocr_proxy.config import (
    DEFAULT_MAX_TOKENS_CAP,
    DEFAULT_MIN_BODY_CHARS_AFTER_YAML,
    DEFAULT_MIN_BODY_LINES_AFTER_YAML,
    DEFAULT_OVERRIDE_LENGTH_TO_STOP,
    DEFAULT_PROXY_HOST,
    DEFAULT_UPSTREAM_BASE_URL,
    DEFAULT_UPSTREAM_TIMEOUT_SECONDS,
)

#: Grace period in seconds for proxy readiness checks.
PROXY_STARTUP_TIMEOUT_SECONDS = 15.0
#: Poll interval in seconds while waiting for proxy readiness.
PROXY_STARTUP_POLL_SECONDS = 0.2
#: Grace period in seconds before force-killing proxy on shutdown.
PROXY_SHUTDOWN_TIMEOUT_SECONDS = 5.0
#: Maximum upstream status code considered "proxy is alive" in readiness checks.
MAX_READY_STATUS_CODE_EXCLUSIVE = 500

#: Logger for managed proxy lifecycle and olmocr wrapper execution.
LOGGER = logging.getLogger("wyrdcraeft.ocr_proxy.runtime")

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence


@dataclass(frozen=True)
class ProxyLaunchConfig:
    """
    Runtime launch parameters for one managed proxy process.

    Args:
        upstream_base_url: Upstream OpenAI-compatible base URL, usually llama.cpp.
        host: Local bind host for the managed proxy process.
        max_tokens_cap: Completion token cap applied by the proxy.
        override_length_to_stop: Enables conservative ``length`` to ``stop`` rewrites.
        min_body_chars_after_yaml: Minimum post-YAML body chars for rewrite heuristic.
        min_body_lines_after_yaml: Minimum post-YAML body lines for rewrite heuristic.
        clamp_both_token_fields: Forces both token fields to one synchronized value.
        temperature_override: Optional forced ``temperature`` sent upstream.
        top_p_override: Optional forced ``top_p`` sent upstream.
        upstream_timeout_seconds: Timeout for upstream HTTP calls from proxy.
        startup_timeout_seconds: Timeout while waiting for local proxy readiness.

    """

    #: Upstream OpenAI-compatible base URL, usually llama.cpp.
    upstream_base_url: str = DEFAULT_UPSTREAM_BASE_URL
    #: Local bind host for the managed proxy process.
    host: str = DEFAULT_PROXY_HOST
    #: Completion token cap applied by the proxy.
    max_tokens_cap: int = DEFAULT_MAX_TOKENS_CAP
    #: Enables conservative ``length`` to ``stop`` rewrites.
    override_length_to_stop: bool = DEFAULT_OVERRIDE_LENGTH_TO_STOP
    #: Minimum post-YAML body chars for rewrite heuristic.
    min_body_chars_after_yaml: int = DEFAULT_MIN_BODY_CHARS_AFTER_YAML
    #: Minimum post-YAML body lines for rewrite heuristic.
    min_body_lines_after_yaml: int = DEFAULT_MIN_BODY_LINES_AFTER_YAML
    #: Forces both token fields to one synchronized value.
    clamp_both_token_fields: bool = False
    #: Optional forced ``temperature`` sent upstream.
    temperature_override: float | None = None
    #: Optional forced ``top_p`` sent upstream.
    top_p_override: float | None = None
    #: Timeout for upstream HTTP calls from proxy.
    upstream_timeout_seconds: float = DEFAULT_UPSTREAM_TIMEOUT_SECONDS
    #: Timeout while waiting for local proxy readiness.
    startup_timeout_seconds: float = PROXY_STARTUP_TIMEOUT_SECONDS


def _pick_unused_local_port(host: str) -> int:
    """
    Reserve and release one ephemeral local TCP port.

    Args:
        host: Host/interface used for ephemeral bind.

    Returns:
        A currently unused local port.

    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def _bool_env_value(value: bool) -> str:
    """
    Convert a boolean value to lowercase environment-string form.

    Args:
        value: Boolean value to convert.

    Returns:
        ``"true"`` when true, otherwise ``"false"``.

    """
    return "true" if value else "false"


def _build_proxy_env(
    config: ProxyLaunchConfig,
    *,
    port: int,
) -> dict[str, str]:
    """
    Build environment variables for one proxy subprocess launch.

    Args:
        config: Proxy launch settings.

    Keyword Args:
        port: Reserved local proxy port.

    Returns:
        Process environment dictionary for the proxy subprocess.

    """
    env = dict(os.environ)
    env["UPSTREAM_BASE_URL"] = config.upstream_base_url
    env["PROXY_HOST"] = config.host
    env["PROXY_PORT"] = str(port)
    env["PROXY_MAX_TOKENS_CAP"] = str(config.max_tokens_cap)
    env["OVERRIDE_LENGTH_TO_STOP"] = _bool_env_value(config.override_length_to_stop)
    env["MIN_BODY_CHARS_AFTER_YAML"] = str(config.min_body_chars_after_yaml)
    env["MIN_BODY_LINES_AFTER_YAML"] = str(config.min_body_lines_after_yaml)
    env["CLAMP_BOTH_TOKEN_FIELDS"] = _bool_env_value(config.clamp_both_token_fields)
    env["PROXY_UPSTREAM_TIMEOUT_SECONDS"] = str(config.upstream_timeout_seconds)

    if config.temperature_override is not None:
        env["PROXY_TEMPERATURE_OVERRIDE"] = str(config.temperature_override)
    else:
        env.pop("PROXY_TEMPERATURE_OVERRIDE", None)

    if config.top_p_override is not None:
        env["PROXY_TOP_P_OVERRIDE"] = str(config.top_p_override)
    else:
        env.pop("PROXY_TOP_P_OVERRIDE", None)

    return env


def _wait_for_proxy_ready(
    proxy_base_url: str,
    *,
    process: subprocess.Popen[str],
    timeout_seconds: float,
) -> None:
    """
    Poll the proxy health endpoint until it starts accepting requests.

    Args:
        proxy_base_url: Base URL for the just-launched local proxy (includes ``/v1``).

    Keyword Args:
        process: Child process handle for early-exit detection.
        timeout_seconds: Maximum seconds to wait before giving up.

    Raises:
        RuntimeError: If process exits early or readiness timeout elapses.

    """
    deadline = time.monotonic() + timeout_seconds
    readiness_url = f"{proxy_base_url}/models"

    while time.monotonic() < deadline:
        return_code = process.poll()
        if return_code is not None:
            message = (
                "Proxy process exited before readiness check "
                f"(code {return_code})."
            )
            raise RuntimeError(message)

        try:
            response = httpx.get(readiness_url, timeout=1.0)
            if response.status_code < MAX_READY_STATUS_CODE_EXCLUSIVE:
                return
        except httpx.RequestError:
            pass

        time.sleep(PROXY_STARTUP_POLL_SECONDS)

    message = (
        "Timed out waiting for local proxy readiness at "
        f"{readiness_url} after {timeout_seconds:.1f}s."
    )
    raise RuntimeError(message)


def _with_overridden_server_arg(
    olmocr_args: Sequence[str],
    *,
    server_url: str,
) -> tuple[list[str], bool]:
    """
    Ensure one definitive ``--server`` argument is present for olmocr.

    Args:
        olmocr_args: Raw CLI args intended for ``python -m olmocr.pipeline``.

    Keyword Args:
        server_url: Proxy server URL to inject.

    Returns:
        Tuple ``(rewritten_args, replaced_existing_server_arg)``.

    """
    rewritten: list[str] = []
    replaced_existing = False
    skip_next = False

    for index, arg in enumerate(olmocr_args):
        if skip_next:
            skip_next = False
            continue

        if arg == "--server":
            replaced_existing = True
            if index + 1 < len(olmocr_args):
                skip_next = True
            continue

        if arg.startswith("--server="):
            replaced_existing = True
            continue

        rewritten.append(arg)

    rewritten.extend(["--server", server_url])
    return rewritten, replaced_existing


@contextmanager
def managed_ocr_proxy(config: ProxyLaunchConfig) -> Iterator[str]:
    """
    Start a local proxy subprocess and tear it down automatically.

    Side Effects:
        Launches and terminates a child Python process for proxy serving.

    Args:
        config: Proxy launch configuration.

    Yields:
        Proxy base URL ending in ``/v1`` for OpenAI-compatible requests.

    Raises:
        RuntimeError: If proxy startup fails or readiness times out.

    """
    port = _pick_unused_local_port(config.host)
    proxy_base_url = f"http://{config.host}:{port}/v1"
    env = _build_proxy_env(config, port=port)
    command = [sys.executable, "-m", "wyrdcraeft.services.ocr_proxy.server"]

    LOGGER.info("starting managed olmocr proxy at %s", proxy_base_url)
    process = subprocess.Popen(command, env=env, text=True)

    try:
        _wait_for_proxy_ready(
            proxy_base_url,
            process=process,
            timeout_seconds=config.startup_timeout_seconds,
        )
        yield proxy_base_url
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=PROXY_SHUTDOWN_TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=PROXY_SHUTDOWN_TIMEOUT_SECONDS)
        LOGGER.info("stopped managed olmocr proxy at %s", proxy_base_url)


def run_olmocr_pipeline_with_managed_proxy(
    olmocr_args: Sequence[str],
    *,
    launch_config: ProxyLaunchConfig | None = None,
) -> int:
    """
    Run ``olmocr.pipeline`` while auto-managing the local proxy lifecycle.

    Side Effects:
        Starts a proxy subprocess and executes ``python -m olmocr.pipeline``.

    Args:
        olmocr_args: CLI arguments forwarded to ``olmocr.pipeline``.

    Keyword Args:
        launch_config: Optional explicit proxy launch settings.

    Returns:
        Exit code from the ``olmocr.pipeline`` process.

    """
    config = launch_config or ProxyLaunchConfig()
    with managed_ocr_proxy(config) as proxy_url:
        rewritten_args, replaced = _with_overridden_server_arg(
            olmocr_args,
            server_url=proxy_url,
        )
        if replaced:
            LOGGER.info("replaced user-provided --server with managed proxy URL")

        command = [sys.executable, "-m", "olmocr.pipeline", *rewritten_args]
        LOGGER.info("running olmocr.pipeline with managed proxy endpoint")
        result = subprocess.run(command, check=False)
        return int(result.returncode)
