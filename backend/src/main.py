"""AlgoVision backend application entrypoint.

This module exposes the FastAPI app factory ``create_app`` and the
default ``app`` singleton bound to module-level settings. The
factory form is what tests use (so they can construct fresh app
instances per test with overridden settings).

Run locally:
    uvicorn src.main:app --reload

Refs: ALGOVISION_BACKEND_PLAN.md §3 (Tech Stack)
Refs: AlgoVision_BACKEND.md §3 (Hard Rules — routers own no logic)
Refs: PUKU_BACKEND_AGENT.md §3.1 (Architecture)
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.core.errors import AppError
from src.core.logging import configure_logging, log
from src.core.settings import Settings, get_settings

DEFAULT_TITLE = "AlgoVision API"
DEFAULT_VERSION = "0.1.0"
DEFAULT_DESCRIPTION = (
    "Interactive algorithm & data structure visualization platform. "
    "See /docs for OpenAPI, /openapi.json for the raw schema."
)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build a FastAPI app bound to the given (or default) Settings.

    The factory exists so tests can pass a custom Settings instance
    (e.g. with rate-limit overrides or a test database URL) without
    polluting the process-global ``get_settings`` cache.

    Wiring order:
    1. logging (B1.3) — first so every later record is formatted.
    2. error handler (B1.4) — next so unexpected exceptions still
       get logged in our format.
    3. CORS / middleware / DB engine / routers — later phase-1 commits.
    """
    if settings is None:
        settings = get_settings()

    configure_logging(settings)
    log.info("application.start", phase="1.4", environment=settings.app_env)

    application = FastAPI(
        title=DEFAULT_TITLE,
        version=DEFAULT_VERSION,
        description=DEFAULT_DESCRIPTION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    _register_error_handlers(application)

    @application.get("/", include_in_schema=False)
    def _root() -> dict[str, str]:
        """Lightweight landing endpoint for smoke checks.

        Real health endpoint arrives in B1.8 (/health) with DB probe.
        """
        return {
            "service": "algovision-backend",
            "status": "scaffold",
            "environment": settings.app_env,
        }

    return application


def _register_error_handlers(application: FastAPI) -> None:
    """Register the AppError -> JSON envelope handler.

    Domain errors raised by services become uniform JSON responses
    with our stable schema (code, message, details, request_id).
    Unexpected exceptions keep their default 500 behavior so bugs are
    never hidden behind a friendly envelope.

    The request_id field is filled when middleware (B6.3) lands; for
    now we leave it None so the schema is stable.
    """

    @application.exception_handler(AppError)
    async def _handle_app_error(
        request: Request,
        exc: AppError,
    ) -> JSONResponse:
        # Log at the right level for the severity.
        log_method: Any = log.warning if exc.status_code < 500 else log.error
        log_method(
            "request.failed",
            code=exc.code,
            status_code=exc.status_code,
            path=request.url.path,
            method=request.method,
            message=exc.message,
        )
        payload = exc.to_payload(request_id=None)
        return JSONResponse(
            status_code=exc.status_code,
            content=payload.model_dump(exclude_none=True),
        )


# Module-level singleton used by ``uvicorn src.main:app``.
app: FastAPI = create_app()