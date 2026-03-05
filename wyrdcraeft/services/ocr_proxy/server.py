from __future__ import annotations

import json
import logging
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


def create_app(config: ProxyConfig | None = None) -> FastAPI:
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
        upstream_client: httpx.AsyncClient = request.app.state.upstream_client
        forward_headers = _filter_forward_headers(dict(request.headers))

        try:
            upstream_response = await upstream_client.get(
                upstream_url,
                headers=forward_headers,
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
        upstream_client: httpx.AsyncClient = request.app.state.upstream_client
        forward_headers = _filter_forward_headers(dict(request.headers))

        try:
            upstream_response = await upstream_client.post(
                upstream_url,
                json=forward_json,
                headers=forward_headers,
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
