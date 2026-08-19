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

from fastapi import FastAPI

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

    Later phase-1 commits wire middleware (CORS, request-id),
    logging, error handlers, the DB engine, and feature routers.
    """
    if settings is None:
        settings = get_settings()

    application = FastAPI(
        title=DEFAULT_TITLE,
        version=DEFAULT_VERSION,
        description=DEFAULT_DESCRIPTION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

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


# Module-level singleton used by ``uvicorn src.main:app``.
app: FastAPI = create_app()