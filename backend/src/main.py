"""AlgoVision backend application entrypoint.

This module is the FastAPI app factory. It is intentionally minimal
in B1.1: it only exposes the app object so the project can be
imported and validated. Real wiring (settings, logging, error
handlers, CORS, middleware, routers) is added in later phase-1
commits (B1.2 - B1.10).

Run locally:
    uvicorn src.main:app --reload

Refs: ALGOVISION_BACKEND_PLAN.md §3 (Tech Stack)
Refs: AlgoVision_BACKEND.md §3 (Hard Rules — routers own no logic)
"""

from fastapi import FastAPI

app = FastAPI(
    title="AlgoVision API",
    version="0.1.0",
    description=(
        "Interactive algorithm & data structure visualization platform. "
        "See /docs for OpenAPI, /openapi.json for the raw schema."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    """Lightweight landing endpoint for smoke checks.

    Real health endpoint arrives in B1.8 (/health) with DB probe.
    """
    return {"service": "algovision-backend", "status": "scaffold"}