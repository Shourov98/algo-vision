"""Request-ID propagation for HTTP responses, errors, and logs.

Each request uses an inbound ``X-Request-ID`` when present, otherwise
receives a generated UUID. The value is exposed through ``request.state``
and structlog context variables for the lifetime of that request only.

Refs: PUKU_BACKEND_AGENT.md §17.1 (Request ID)
Refs: ALGOVISION_BACKEND_PLAN.md §13 (B6.2)
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from uuid import uuid4

import structlog
from fastapi import FastAPI, Request, Response

REQUEST_ID_HEADER = "X-Request-ID"

RequestHandler = Callable[[Request], Awaitable[Response]]


def resolve_request_id(incoming_request_id: str | None) -> str:
    """Return an inbound request ID or create a UUID for the request."""
    return incoming_request_id or str(uuid4())


def get_request_id(request: Request) -> str | None:
    """Return the request ID stored by the HTTP middleware, if any."""
    return getattr(request.state, "request_id", None)


async def request_id_middleware(
    request: Request,
    call_next: RequestHandler,
) -> Response:
    """Bind a request ID while handling one request and return it to clients."""
    request_id = resolve_request_id(request.headers.get(REQUEST_ID_HEADER))
    request.state.request_id = request_id
    tokens = structlog.contextvars.bind_contextvars(request_id=request_id)

    try:
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
    finally:
        structlog.contextvars.reset_contextvars(**tokens)


def install_request_id_middleware(application: FastAPI) -> None:
    """Register request-ID handling once during application construction."""
    application.middleware("http")(request_id_middleware)
