"""Unit tests for the health check module.

Covers:
- Liveness: always 200, no I/O.
- Readiness: 200 when DB reachable, 503 + error payload when not.
- HealthService is stateless and can be invoked directly without
  the FastAPI app.
- HealthStatus.to_dict() shape is stable.

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 1.8)
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import dispose_engine, init_engine
from src.core.settings import Settings, get_settings
from src.modules.health.router import router as health_router
from src.modules.health.service import HealthService, HealthStatus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_settings(tmp_path) -> Settings:
    db_file = tmp_path / "test.db"
    url = f"sqlite+aiosqlite:///{db_file}"
    os.environ["APP_ENV"] = "test"
    os.environ["DATABASE_URL"] = url
    os.environ["DATABASE_URL_SYNC"] = url.replace("+aiosqlite", "")
    os.environ["SECRET_KEY"] = "x" * 64
    get_settings.cache_clear()
    return get_settings()


@pytest.fixture
def settings(tmp_path) -> Settings:
    return _make_settings(tmp_path)


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    """Build a TestClient with health router mounted + engine initialized."""
    init_engine(settings)
    app = FastAPI()
    app.include_router(health_router)
    try:
        with TestClient(app) as c:
            yield c
    finally:
        # Clean up: dispose engine after the TestClient context exits.
        import asyncio

        async def _dispose() -> None:
            await dispose_engine()

        asyncio.run(_dispose())


# ---------------------------------------------------------------------------
# HealthService direct tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_liveness_always_ok() -> None:
    s = HealthService()
    result = await s.check_liveness()
    assert result.healthy is True
    assert result.components == {}


@pytest.mark.asyncio
async def test_readiness_with_real_db_returns_ok(settings: Settings) -> None:
    """With a real DB session, readiness reports healthy."""
    init_engine(settings)
    try:
        from src.core.db import get_session_factory

        factory = get_session_factory()
        async with factory() as session:
            result = await HealthService().check_readiness(session)
        assert result.healthy is True
        assert result.components["database"]["status"] == "ok"
    finally:
        await dispose_engine()


@pytest.mark.asyncio
async def test_readiness_with_broken_db_returns_degraded() -> None:
    """A failing query must produce a degraded payload, not raise."""
    from unittest.mock import AsyncMock, MagicMock

    broken_session = MagicMock()
    broken_session.execute = AsyncMock(
        side_effect=RuntimeError("connection refused")
    )

    result = await HealthService().check_readiness(broken_session)
    assert result.healthy is False
    db = result.components["database"]
    assert db["status"] == "down"
    assert "RuntimeError" in db["error"]
    assert "connection refused" in db["error"]


# ---------------------------------------------------------------------------
# HealthStatus shape
# ---------------------------------------------------------------------------


def test_health_status_to_dict_shape() -> None:
    s = HealthStatus(healthy=True, components={"db": {"status": "ok"}})
    d = s.to_dict()
    assert d == {"status": "ok", "components": {"db": {"status": "ok"}}}


def test_health_status_degraded_to_dict() -> None:
    s = HealthStatus(healthy=False, components={"db": {"status": "down"}})
    d = s.to_dict()
    assert d["status"] == "degraded"


# ---------------------------------------------------------------------------
# /health endpoint
# ---------------------------------------------------------------------------


def test_health_endpoint_returns_200(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body == {"status": "ok", "components": {}}


def test_health_endpoint_is_idempotent(client: TestClient) -> None:
    for _ in range(3):
        response = client.get("/health")
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# /health/db endpoint
# ---------------------------------------------------------------------------


def test_health_db_returns_200_when_db_ok(client: TestClient) -> None:
    response = client.get("/health/db")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["components"]["database"]["status"] == "ok"


def test_health_db_returns_503_when_db_down(settings: Settings) -> None:
    """When the engine isn't initialized, readiness must degrade."""
    import asyncio

    asyncio.run(dispose_engine())

    # Build a client WITHOUT calling init_engine, so get_session fails.
    app = FastAPI()
    app.include_router(health_router)
    with TestClient(app) as c:
        response = c.get("/health/db")
        assert response.status_code == 503
        body = response.json()
        assert body["status"] == "degraded"
        assert body["components"]["database"]["status"] == "down"
        assert "error" in body["components"]["database"]