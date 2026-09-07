"""Health check router.

Endpoints:
- GET /health        liveness (no DB)
- GET /health/db     readiness (DB probe)

Both return JSON with a ``status`` field and a ``components`` map.
The router does NOT contain business logic — HealthService owns it.

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 1.8)
Refs: PUKU_BACKEND_AGENT.md §3.1
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.health.service import HealthService

router = APIRouter(tags=["health"])


def _get_service() -> HealthService:
    """Dependency for HealthService.

    Stateless, so we return a fresh instance every call. If HealthService
    gains configuration later, swap to Depends with a singleton.
    """
    return HealthService()


async def _safe_session() -> AsyncIterator[AsyncSession | None]:
    """Yield a DB session if the engine is initialized, else None.

    The default ``get_session`` dependency raises RuntimeError when the
    engine isn't ready. For health checks we want a graceful degraded
    response (503), not a 500 — so we wrap the dependency.

    This is an async-generator dependency (FastAPI sees the ``yield`` and
    handles setup/teardown correctly).
    """
    from src.core.db import get_session_factory

    factory = None
    try:
        factory = get_session_factory()
    except RuntimeError:
        yield None
        return

    session = factory()
    try:
        yield session
    finally:
        await session.close()


@router.get("/health")
async def health(
    service: HealthService = Depends(_get_service),
) -> dict:
    """Liveness probe — always returns 200 if the process is up."""
    payload = (await service.check_liveness()).to_dict()
    return payload


@router.get("/health/db")
async def health_db(
    service: HealthService = Depends(_get_service),
    session: AsyncSession | None = Depends(_safe_session),
) -> JSONResponse:
    """Readiness probe — pings the database.

    Returns 200 with status="ok" if the DB is reachable, 503 with
    status="degraded" otherwise. Orchestrators should treat 503 as
    "do not route traffic here yet".
    """
    result = await service.check_readiness(session)
    http_status = 200 if result.healthy else 503
    return JSONResponse(status_code=http_status, content=result.to_dict())