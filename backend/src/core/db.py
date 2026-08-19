"""Async SQLAlchemy 2.x engine, session factory, and FastAPI dependency.

Single ``init_engine(settings)`` builds the engine from
``settings.database_url``. ``get_session()`` is the FastAPI
dependency that yields a scoped ``AsyncSession`` for a request.

Why a single engine per process
-------------------------------
SQLAlchemy recommends one engine per process and one session per
unit of work. We never create ad-hoc engines inside request
handlers (that defeats the connection pool).

Why a custom dependency, not ``AsyncSessionLocal``
--------------------------------------------------
FastAPI expects async-generator dependencies that yield a session
and clean up after the request. The wrapper below handles
begin/commit/rollback correctly without leaking sessions.

Refs: PUKU_BACKEND_AGENT.md §3.3 (Database)
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 1.5)
Refs: DATABASE_DESIGN.md §3
Refs: AlgoVision_BACKEND.md §3 (no SQL in routers)
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.settings import Settings

# Module-level holders. They are set by init_engine() at app boot.
# Tests that need a fresh engine call init_engine() again.
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_engine(settings: Settings) -> AsyncEngine:
    """Build (or rebuild) the async engine + session factory.

    Idempotent: calling again with different settings replaces the
    module-level engine and session factory. Useful in tests that
    swap settings between cases.

    Pool sizing comes from settings.db_pool_size /
    settings.db_max_overflow / settings.db_pool_timeout_seconds.
    """
    global _engine, _session_factory

    if _engine is not None:
        # Dispose old engine so its pool connections are closed.
        _engine.sync_engine.dispose()  # type: ignore[attr-defined]

    _engine = create_async_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout_seconds,
        pool_pre_ping=True,  # detect dead connections before use
        future=True,
    )

    _session_factory = async_sessionmaker(
        bind=_engine,
        expire_on_commit=False,
        autoflush=False,
        class_=AsyncSession,
    )
    return _engine


def get_engine() -> AsyncEngine:
    """Return the module-level engine.

    Raises RuntimeError if init_engine() has not been called yet.
    """
    if _engine is None:
        raise RuntimeError(
            "DB engine not initialized. Call init_engine(settings) "
            "during application startup."
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the module-level session factory."""
    if _session_factory is None:
        raise RuntimeError(
            "Session factory not initialized. Call init_engine(settings) "
            "during application startup."
        )
    return _session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: yield a session, commit on success, rollback on error.

    Usage in a router:
        @router.post("/things")
        async def create_thing(
            session: AsyncSession = Depends(get_session),
        ): ...

    The dependency does not commit explicitly — that is the
    service layer's job. This wrapper only handles teardown so we
    never leak sessions on unhandled exceptions.
    """
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def dispose_engine() -> None:
    """Close all pool connections. Call on application shutdown."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None


def engine_status() -> dict[str, Any]:
    """Return a small dict for /health checks.

    Does NOT open a new connection — reports what we know about
    the configured engine without performing I/O.
    """
    if _engine is None:
        return {"initialized": False}
    pool = _engine.pool
    return {
        "initialized": True,
        "driver": _engine.url.drivername,
        "host": _engine.url.host,
        "database": _engine.url.database,
        "pool_size": pool.size(),  # type: ignore[attr-defined]
        "checked_out": pool.checkedout(),  # type: ignore[attr-defined]
    }