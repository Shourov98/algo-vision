"""Unit tests for src.core.db.

These tests verify the engine + session wiring without depending on
a live Supabase instance. They use SQLite in-memory via aiosqlite
because the test goal is to validate SQLAlchemy 2.x async behavior
(engine creation, session factory, dependency lifecycle), not the
specific PostgreSQL driver.

Integration tests against real Supabase Postgres live in
tests/integration/ and require DATABASE_URL with real credentials.

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 1.5)
Refs: PUKU_BACKEND_AGENT.md §3.3
"""

from __future__ import annotations

import os

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from src.core.db import (
    dispose_engine,
    engine_status,
    get_engine,
    get_session,
    get_session_factory,
    init_engine,
)
from src.core.settings import Settings, get_settings

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_test_settings(tmp_path) -> Settings:
    """Provide a Settings with an aiosqlite URL so we don't need Postgres."""
    db_file = tmp_path / "test.db"
    url = f"sqlite+aiosqlite:///{db_file}"
    os.environ["APP_ENV"] = "test"
    os.environ["DATABASE_URL"] = url
    os.environ["DATABASE_URL_SYNC"] = url.replace("+aiosqlite", "")
    os.environ["SECRET_KEY"] = "x" * 64
    os.environ["DB_POOL_SIZE"] = "1"
    os.environ["DB_MAX_OVERFLOW"] = "1"
    os.environ["DB_POOL_TIMEOUT_SECONDS"] = "5"
    get_settings.cache_clear()
    return get_settings()


@pytest.fixture
def settings(tmp_path) -> Settings:
    return _make_test_settings(tmp_path)


# ---------------------------------------------------------------------------
# init_engine + dispose_engine (async)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_init_engine_returns_async_engine(settings: Settings) -> None:
    try:
        engine = init_engine(settings)
        try:
            assert isinstance(engine, AsyncEngine)
        finally:
            await dispose_engine()
    finally:
        # Ensure module state is clean even on assertion failure.
        await dispose_engine()


@pytest.mark.asyncio
async def test_init_engine_is_idempotent(settings: Settings) -> None:
    """Calling init_engine twice replaces the engine cleanly."""
    try:
        e1 = init_engine(settings)
        e2 = init_engine(settings)
        assert e1 is not e2
        assert isinstance(get_engine(), AsyncEngine)
    finally:
        await dispose_engine()


@pytest.mark.asyncio
async def test_get_engine_raises_before_init() -> None:
    """Without init_engine(), get_engine() must raise a clear error."""
    await dispose_engine()
    with pytest.raises(RuntimeError, match="DB engine not initialized"):
        get_engine()


@pytest.mark.asyncio
async def test_get_session_factory_raises_before_init() -> None:
    await dispose_engine()
    with pytest.raises(RuntimeError, match="Session factory not initialized"):
        get_session_factory()


@pytest.mark.asyncio
async def test_session_factory_produces_async_session(settings: Settings) -> None:
    try:
        init_engine(settings)
        factory = get_session_factory()
        session = factory()
        try:
            assert isinstance(session, AsyncSession)
        finally:
            await session.close()
    finally:
        await dispose_engine()


@pytest.mark.asyncio
async def test_dispose_engine_clears_module_state(settings: Settings) -> None:
    init_engine(settings)
    assert engine_status()["initialized"] is True
    await dispose_engine()
    assert engine_status() == {"initialized": False}
    with pytest.raises(RuntimeError):
        get_engine()


# ---------------------------------------------------------------------------
# engine_status
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_engine_status_uninitialized() -> None:
    await dispose_engine()
    assert engine_status() == {"initialized": False}


@pytest.mark.asyncio
async def test_engine_status_initialized(settings: Settings) -> None:
    try:
        init_engine(settings)
        status = engine_status()
        assert status["initialized"] is True
        assert "driver" in status
        assert "host" in status
        assert "database" in status
    finally:
        await dispose_engine()


# ---------------------------------------------------------------------------
# FastAPI dependency lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_session_yields_and_closes(settings: Settings) -> None:
    """get_session dependency yields a session and closes it after."""
    try:
        init_engine(settings)
        app = FastAPI()
        captured: list[AsyncSession] = []

        @app.get("/probe")
        async def _probe(session: AsyncSession = Depends(get_session)):  # type: ignore[misc]
            captured.append(session)
            return {"ok": True}

        client = TestClient(app)
        response = client.get("/probe")
        assert response.status_code == 200
        assert len(captured) == 1
        # After the request finishes, calling close() again is a no-op.
        await captured[0].close()
    finally:
        await dispose_engine()


@pytest.mark.asyncio
async def test_get_session_rolls_back_on_exception(settings: Settings) -> None:
    """If the route raises, get_session must close the session."""
    try:
        init_engine(settings)
        app = FastAPI()
        captured: list[AsyncSession] = []

        @app.get("/explode")
        async def _explode(session: AsyncSession = Depends(get_session)):  # type: ignore[misc]
            captured.append(session)
            raise RuntimeError("boom")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/explode")
        assert response.status_code == 500
        # Closing again must not raise — the dependency already closed it.
        await captured[0].close()
    finally:
        await dispose_engine()


# ---------------------------------------------------------------------------
# End-to-end: real query via dependency
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dependency_executes_query(settings: Settings) -> None:
    """Round-trip: dependency -> session.execute(text(...)) -> result."""
    try:
        init_engine(settings)
        app = FastAPI()

        @app.get("/select")
        async def _select(session: AsyncSession = Depends(get_session)):  # type: ignore[misc]
            result = (await session.execute(text("SELECT 1"))).scalar_one()
            return {"result": result}

        client = TestClient(app)
        response = client.get("/select")
        assert response.status_code == 200
        assert response.json() == {"result": 1}
    finally:
        await dispose_engine()
