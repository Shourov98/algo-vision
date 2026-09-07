"""Unit tests for request-ID generation and propagation.

Refs: PUKU_BACKEND_AGENT.md §17.1 (Request ID)
Refs: ALGOVISION_BACKEND_PLAN.md §13 (B6.2)
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
import structlog
from fastapi import Request, Response
from src.core.request_id import (
    REQUEST_ID_HEADER,
    bind_user_id,
    get_request_id,
    request_id_middleware,
    resolve_request_id,
)


def _request(request_id: str | None = None) -> Request:
    headers = [] if request_id is None else [(b"x-request-id", request_id.encode())]
    return Request({"type": "http", "headers": headers})


def test_resolve_request_id_preserves_incoming_value() -> None:
    assert resolve_request_id("request-from-client") == "request-from-client"


def test_resolve_request_id_generates_uuid_when_header_is_absent() -> None:
    assert UUID(resolve_request_id(None)).version == 4


@pytest.mark.asyncio
async def test_middleware_propagates_request_id_to_response_and_log_context() -> None:
    request = _request("request-from-client")
    observed_context: dict[str, object] = {}

    async def _call_next(received_request: Request) -> Response:
        observed_context.update(structlog.contextvars.get_contextvars())
        assert get_request_id(received_request) == "request-from-client"
        return Response(status_code=204)

    response = await request_id_middleware(request, _call_next)

    assert response.headers[REQUEST_ID_HEADER] == "request-from-client"
    assert observed_context["request_id"] == "request-from-client"
    assert "request_id" not in structlog.contextvars.get_contextvars()


@pytest.mark.asyncio
async def test_middleware_clears_authenticated_user_context() -> None:
    request = _request()
    user_id = uuid4()
    observed_context: dict[str, object] = {}

    async def _call_next(_: Request) -> Response:
        bind_user_id(user_id)
        observed_context.update(structlog.contextvars.get_contextvars())
        return Response()

    await request_id_middleware(request, _call_next)

    assert observed_context["user_id"] == str(user_id)
    assert "user_id" not in structlog.contextvars.get_contextvars()
