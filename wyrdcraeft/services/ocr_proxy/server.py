from __future__ import annotations

import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from wyrdcraeft.services.ocr_proxy.config import ProxyConfig, load_proxy_config
from wyrdcraeft.services.ocr_proxy.proxy import (
    clamp_chat_request_payload,
    maybe_override_finish_reason,
    summarize_chat_request,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

#: Header names that should not be copied directly from upstream responses.
HOP_BY_HOP_HEADERS = {
    "connection",
    "content-length",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}
#: Header names that should be filtered from incoming requests before forwarding.
REQUEST_HEADER_FILTER = {"host", "content-length", "connection"}
#: Canonical HTTP success status used for upstream chat-completions passthrough.
HTTP_STATUS_OK = 200
#: Upstream statuses that should be retried as transient failures.
TRANSIENT_UPSTREAM_STATUS_CODES = {429, 500, 502, 503, 504}
#: Maximum retry backoff delay in seconds.
MAX_RETRY_BACKOFF_SECONDS = 5.0

#: Logger for proxy lifecycle and mutation events.
LOGGER = logging.getLogger("wyrdcraeft.ocr_proxy")


def _build_upstream_url(base_url: str, endpoint: str) -> str:
    """
    Build a full upstream URL using a known endpoint suffix.

    Args:
        base_url: Configured upstream base URL.
        endpoint: Endpoint suffix beginning with ``/``.

    Returns:
        Fully-qualified upstream request URL.

    """
    return f"{base_url.rstrip('/')}{endpoint}"


def _filter_response_headers(headers: httpx.Headers) -> dict[str, str]:
    """
    Copy upstream response headers while removing hop-by-hop fields.

    Args:
        headers: Upstream response header mapping.

    Returns:
        Sanitized header dictionary safe for proxy response emission.

    """
    return {
        key: value
        for key, value in headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }


def _filter_forward_headers(headers: Mapping[str, str]) -> dict[str, str]:
    """
    Copy incoming request headers for upstream forwarding.

    Args:
        headers: Incoming request headers.

    Returns:
        Filtered header dictionary for upstream requests.

    """
    return {
        key: value
        for key, value in headers.items()
        if key.lower() not in REQUEST_HEADER_FILTER
    }


def _openai_compatible_error(message: str, error_type: str) -> dict[str, Any]:
    """
    Build an OpenAI-style JSON error payload.

    Args:
        message: Human-readable error message.
        error_type: Machine-readable error type string.

    Returns:
        OpenAI-compatible error response object.

    """
    return {
        "error": {
            "message": message,
            "type": error_type,
            "param": None,
            "code": None,
        }
    }


def _compute_retry_backoff_seconds(
    base_backoff_seconds: float, retry_attempt: int
) -> float:
    """
    Compute one exponential retry backoff delay with a capped upper bound.

    Args:
        base_backoff_seconds: Base backoff for first retry attempt.
        retry_attempt: One-based retry attempt number.

    Returns:
        Delay in seconds for the current retry.

    """
    if base_backoff_seconds <= 0:
        return 0.0
    exponent = max(retry_attempt - 1, 0)
    raw_delay = base_backoff_seconds * (2**exponent)
    return min(raw_delay, MAX_RETRY_BACKOFF_SECONDS)


async def _request_upstream_with_retry(  # noqa: PLR0913
    *,
    method: str,
    url: str,
    headers: Mapping[str, str],
    config: ProxyConfig,
    upstream_client: httpx.AsyncClient,
    json_payload: Mapping[str, Any] | None = None,
) -> httpx.Response:
    """
    Execute one upstream request with bounded retries for transient failures.

    Args:
        method: HTTP method to issue upstream.
        url: Fully qualified upstream URL.
        headers: Forwarded request headers.
        config: Runtime proxy configuration.
        upstream_client: Shared async upstream HTTP client.

    Keyword Args:
        json_payload: Optional JSON payload for POST requests.

    Raises:
        httpx.RequestError: If transport errors persist past retry budget.

    Returns:
        Final upstream response after retries or first non-transient result.

    """
    max_retries = max(config.upstream_max_retries, 0)
    attempts = max_retries + 1
    for attempt_index in range(attempts):
        retry_attempt = attempt_index + 1
        try:
            response = await upstream_client.request(
                method=method,
                url=url,
                headers=headers,
                json=json_payload,
            )
        except httpx.RequestError:
            if retry_attempt > max_retries:
                raise
            backoff = _compute_retry_backoff_seconds(
                config.upstream_retry_backoff_seconds, retry_attempt
            )
            LOGGER.warning(
                "transient upstream transport error on %s %s (attempt %d/%d), "
                "retrying in %.2fs",
                method,
                url,
                retry_attempt,
                attempts,
                backoff,
            )
            await asyncio.sleep(backoff)
            continue

        if (
            response.status_code in TRANSIENT_UPSTREAM_STATUS_CODES
            and retry_attempt <= max_retries
        ):
            backoff = _compute_retry_backoff_seconds(
                config.upstream_retry_backoff_seconds, retry_attempt
            )
            LOGGER.warning(
                "transient upstream status %d on %s %s (attempt %d/%d), "
                "retrying in %.2fs",
                response.status_code,
                method,
                url,
                retry_attempt,
                attempts,
                backoff,
            )
            await asyncio.sleep(backoff)
            continue
        return response

    message = "upstream retry loop exhausted unexpectedly"
    raise RuntimeError(message)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """
    Manage startup/shutdown resources for the proxy application.

    Side Effects:
        Creates and closes one shared async upstream HTTP client.

    Args:
        app: FastAPI application instance.

    Yields:
        None.

    """
    config: ProxyConfig = app.state.proxy_config
    timeout = httpx.Timeout(config.upstream_timeout_seconds)
    app.state.upstream_client = httpx.AsyncClient(timeout=timeout)
    try:
        yield
    finally:
        await app.state.upstream_client.aclose()


def create_app(config: ProxyConfig | None = None) -> FastAPI:  # noqa: PLR0915
    """
    Create a FastAPI application for local olmocr proxying.

    Args:
        config: Optional explicit runtime configuration.

    Returns:
        Configured FastAPI app instance.

    """
    resolved_config = config or load_proxy_config()

    app = FastAPI(
        title="wyrdcraeft olmocr local proxy",
        docs_url=None,
        redoc_url=None,
        lifespan=_lifespan,
    )
    app.state.proxy_config = resolved_config

    @app.get("/v1/models")
    async def get_models(request: Request) -> Response:
        """
        Proxy ``GET /v1/models`` to the configured upstream server.

        Args:
            request: FastAPI request object.

        Returns:
            Upstream response payload and status code.

        """
        upstream_url = _build_upstream_url(
            app.state.proxy_config.upstream_base_url, "/models"
        )
        config: ProxyConfig = app.state.proxy_config
        upstream_client: httpx.AsyncClient = request.app.state.upstream_client
        forward_headers = _filter_forward_headers(dict(request.headers))

        try:
            upstream_response = await _request_upstream_with_retry(
                method="GET",
                url=upstream_url,
                headers=forward_headers,
                config=config,
                upstream_client=upstream_client,
            )
        except httpx.RequestError as exc:
            message = f"Upstream /v1/models request failed: {exc}"
            LOGGER.exception(message)
            return JSONResponse(
                status_code=502,
                content=_openai_compatible_error(message, "upstream_connection_error"),
            )

        return Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
            headers=_filter_response_headers(upstream_response.headers),
            media_type=upstream_response.headers.get("content-type"),
        )

    @app.post("/v1/chat/completions")
    async def post_chat_completions(  # noqa: PLR0911
        request: Request,
    ) -> Response:
        """
        Proxy ``POST /v1/chat/completions`` with request/response normalization.

        Args:
            request: FastAPI request object.

        Returns:
            OpenAI-compatible chat completion response.

        """
        try:
            request_json = await request.json()
        except json.JSONDecodeError:
            message = "Invalid JSON body for /v1/chat/completions request."
            return JSONResponse(
                status_code=400,
                content=_openai_compatible_error(message, "invalid_request_error"),
            )

        if not isinstance(request_json, dict):
            message = "Expected JSON object body for /v1/chat/completions request."
            return JSONResponse(
                status_code=400,
                content=_openai_compatible_error(message, "invalid_request_error"),
            )

        if request_json.get("stream") is True:
            message = (
                "Streaming is not currently supported by this proxy. "
                "Set stream=false and retry."
            )
            return JSONResponse(
                status_code=400,
                content=_openai_compatible_error(message, "stream_not_supported"),
            )

        redacted_summary = summarize_chat_request(request_json)
        LOGGER.info("chat request summary: %s", redacted_summary)

        forward_json, mutation_notes = clamp_chat_request_payload(
            request_json, app.state.proxy_config
        )
        for note in mutation_notes:
            LOGGER.info("request mutation: %s", note)

        upstream_url = _build_upstream_url(
            app.state.proxy_config.upstream_base_url, "/chat/completions"
        )
        config: ProxyConfig = app.state.proxy_config
        upstream_client: httpx.AsyncClient = request.app.state.upstream_client
        forward_headers = _filter_forward_headers(dict(request.headers))

        try:
            request_started = time.monotonic()
            upstream_response = await _request_upstream_with_retry(
                method="POST",
                url=upstream_url,
                headers=forward_headers,
                config=config,
                upstream_client=upstream_client,
                json_payload=forward_json,
            )
        except httpx.RequestError as exc:
            message = f"Upstream /v1/chat/completions request failed: {exc}"
            LOGGER.exception(message)
            return JSONResponse(
                status_code=502,
                content=_openai_compatible_error(message, "upstream_connection_error"),
            )

        if upstream_response.status_code != HTTP_STATUS_OK:
            return Response(
                content=upstream_response.content,
                status_code=upstream_response.status_code,
                headers=_filter_response_headers(upstream_response.headers),
                media_type=upstream_response.headers.get("content-type"),
            )

        try:
            upstream_json = upstream_response.json()
        except ValueError:
            return Response(
                content=upstream_response.content,
                status_code=upstream_response.status_code,
                headers=_filter_response_headers(upstream_response.headers),
                media_type=upstream_response.headers.get("content-type"),
            )

        if not isinstance(upstream_json, dict):
            return JSONResponse(
                status_code=502,
                content=_openai_compatible_error(
                    "Upstream returned a non-object JSON payload.",
                    "upstream_invalid_response",
                ),
            )

        rewritten_json, did_override = maybe_override_finish_reason(
            upstream_json, app.state.proxy_config
        )
        if did_override:
            LOGGER.info("response mutation: overridden finish_reason length -> stop")

        elapsed_seconds = time.monotonic() - request_started
        usage = rewritten_json.get("usage")
        if isinstance(usage, dict):
            prompt_tokens = int(usage.get("prompt_tokens", 0))
            completion_tokens = int(usage.get("completion_tokens", 0))
            total_tokens = int(usage.get("total_tokens", 0))
            completion_tps = (
                completion_tokens / elapsed_seconds if elapsed_seconds > 0 else 0.0
            )
            LOGGER.info(
                "chat completion stats: request_s=%.3f prompt_tokens=%d "
                "completion_tokens=%d total_tokens=%d completion_tps=%.3f",
                elapsed_seconds,
                prompt_tokens,
                completion_tokens,
                total_tokens,
                completion_tps,
            )

        return JSONResponse(
            status_code=upstream_response.status_code,
            content=rewritten_json,
            headers=_filter_response_headers(upstream_response.headers),
        )

    return app


def main() -> None:
    """
    Run the local proxy server process.

    Side Effects:
        Starts a long-running ASGI HTTP server bound to configured host/port.

    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    config = load_proxy_config()

    uvicorn.run(
        create_app(config),
        host=config.host,
        port=config.port,
        log_level="info",
    )


#: ASGI application instance for direct server hosting.
app = create_app()

if __name__ == "__main__":
    main()
