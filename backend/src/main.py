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
from slowapi.errors import RateLimitExceeded

from src.core.db import dispose_engine, engine_status, init_engine
from src.core.errors import AppError
from src.core.logging import configure_logging, log
from src.core.rate_limit import build_limiter
from src.core.settings import Settings, get_settings
from src.modules.auth.router import router as auth_router
from src.modules.catalog.router import all_routers as catalog_routers
from src.modules.dashboard.router import all_routers as dashboard_routers
from src.modules.health.router import router as health_router
from src.modules.problems.router import all_routers as problems_routers
from src.modules.progress.dependencies import register_progress_handlers
from src.modules.progress.router import all_routers as progress_routers
from src.shared.events import InProcessEventDispatcher

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
    3. DB engine (B1.5) — last so feature routers can rely on it.
    """
    if settings is None:
        settings = get_settings()

    configure_logging(settings)
    init_engine(settings)
    log.info(
        "application.start",
        phase="1.8",
        environment=settings.app_env,
        db=engine_status(),
    )

    application = FastAPI(
        title=DEFAULT_TITLE,
        version=DEFAULT_VERSION,
        description=DEFAULT_DESCRIPTION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    _register_error_handlers(application)
    _register_rate_limit_handlers(application, settings)
    _register_lifespan(application)
    application.include_router(health_router)
    application.include_router(auth_router)
    for router in catalog_routers:
        application.include_router(router)
    for router in problems_routers:
        application.include_router(router)
    for router in progress_routers:
        application.include_router(router)
    for router in dashboard_routers:
        application.include_router(router)

    # Wire the process-wide event dispatcher so catalog/problems
    # services can dispatch ItemViewedEvent without importing
    # subscribers. Progress (B5.7) is the first consumer; future
    # analytics/recommendation modules can register here too.
    dispatcher = InProcessEventDispatcher()
    register_progress_handlers(dispatcher)
    application.state.dispatcher = dispatcher

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


def _register_rate_limit_handlers(application: FastAPI, settings: Settings) -> None:
    """Install the slowapi Limiter on app.state and wire the
    RateLimitExceeded -> JSON handler.

    The Limiter is built fresh per app from ``Settings``. Routers
    read it via ``request.app.state.limiter`` from the rate-limit
    dependency in ``src.core.rate_limit``.

    Tests can swap ``app.state.limiter`` to a fresh in-memory
    Limiter for isolation; the rate-limit dependency reads it
    lazily at request time.
    """
    from src.core.errors import RateLimited
    from src.core.rate_limit import DEFAULT_RATE_LIMIT

    limiter = build_limiter(
        default_limit=settings.rate_limit_default or DEFAULT_RATE_LIMIT,
    )
    application.state.limiter = limiter

    @application.exception_handler(RateLimitExceeded)
    async def _handle_rate_limit(
        request: Request,
        exc: RateLimitExceeded,
    ) -> JSONResponse:
        # Map slowapi's exception to our AppError shape.
        log.warning(
            "request.rate_limited",
            path=request.url.path,
            method=request.method,
            detail=str(exc),
        )
        envelope = RateLimited(
            "Too many requests. Please slow down.",
            details={"limit": str(exc)},
        )
        return JSONResponse(
            status_code=envelope.status_code,
            content=envelope.to_payload().model_dump(exclude_none=True),
        )


def _register_lifespan(application: FastAPI) -> None:
    """Wire application lifespan so the DB pool is closed on shutdown.

    FastAPI's modern lifespan context manager replaces the
    deprecated @app.on_event('startup'/'shutdown') decorators.
    """

    @application.on_event("shutdown")
    async def _on_shutdown() -> None:
        log.info("application.shutdown")
        await dispose_engine()


# Module-level singleton used by ``uvicorn src.main:app``.
app: FastAPI = create_app()
