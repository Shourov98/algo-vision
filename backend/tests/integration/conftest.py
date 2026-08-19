"""Pytest fixtures for the integration test suite.

Integration tests exercise the full HTTP stack against a real
PostgreSQL database. They are skipped when no test database
URL is available so the unit suite can run on a developer
laptop without Postgres.

How tests opt in
----------------
A test in this directory (or any subdir) is treated as
integration. It runs only when:

- ``TEST_DATABASE_URL`` is set in the environment, AND
- the URL responds to ``SELECT 1`` via asyncpg.

If either check fails, every integration test is **skipped**
(not failed) so the suite remains green on environments
without a database.

Why we require Postgres and not SQLite
--------------------------------------
Our migrations use Postgres-specific features (citext, pgcrypto
gen_random_uuid, ``CREATE UNIQUE INDEX ... LOWER(email)``).
SQLite would silently behave differently from production. The
agent doc (PUKU_BACKEND_AGENT §13.3) is explicit: use real
Postgres.

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 2 - B2.9)
Refs: PUKU_BACKEND_AGENT.md §13 (Test Conventions)
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from src.core.db import Base
from src.main import create_app
from src.modules.auth.dependencies import get_auth_service

# ---------------------------------------------------------------------------
# Skip-everything marker
# ---------------------------------------------------------------------------


def _postgres_available() -> bool:
    """Return True iff TEST_DATABASE_URL points at a reachable PG.

    Performs a lightweight asyncpg probe with a short timeout
    so the skip detection is fast even when nothing is running.
    """
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        return False
    # asyncpg expects ``postgresql://``, not the SQLAlchemy
    # ``postgresql+asyncpg://`` form.
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif url.startswith("postgresql+psycopg2://"):
        url = url.replace("postgresql+psycopg2://", "postgresql://", 1)

    async def _probe() -> bool:
        try:
            conn = await asyncpg.connect(url, timeout=2.0)
        except Exception:
            return False
        try:
            await conn.execute("SELECT 1")
            return True
        finally:
            await conn.close()

    try:
        return asyncio.run(_probe())
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _postgres_available(),
    reason=(
        "TEST_DATABASE_URL not set or Postgres unreachable; "
        "integration tests require a real test database."
    ),
)


def _require_db() -> None:
    """Raise a Skip exception when no DB is configured.

    Fixtures call this at the top so a missing TEST_DATABASE_URL
    surfaces as a per-test skip (rather than a fixture-load
    error that pytest reports as ``ERROR`` instead of ``SKIPPED``).
    """
    if not _postgres_available():
        pytest.skip(
            "TEST_DATABASE_URL not set or Postgres unreachable; "
            "integration tests require a real test database."
        )


# ---------------------------------------------------------------------------
# Database + schema fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def engine():
    """Yield a fresh async SQLAlchemy engine pointed at TEST_DATABASE_URL.

    Each test gets its own engine so pool state is isolated. The
    schema is dropped/recreated around the test so test runs are
    fully self-contained.
    """
    _require_db()
    url = os.environ["TEST_DATABASE_URL"]
    eng = create_async_engine(url, poolclass=NullPool)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield eng
    finally:
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncIterator:
    """Yield an async session bound to the test engine.

    ``expire_on_commit=False`` keeps ORM attributes accessible
    after commit (we use them to assert on persisted state).
    """
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        yield session


# ---------------------------------------------------------------------------
# HTTP client fixture
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def client(engine) -> AsyncIterator[AsyncClient]:
    """Yield an httpx AsyncClient wired to the real FastAPI app.

    The ``get_auth_service`` dependency is overridden so tests
    don't need to construct an AuthService manually — they get
    one bound to the same engine / session lifecycle as the
    request.

    Each HTTP request opens a fresh session via the factory;
    the session is closed in the dependency's finally clause
    so requests don't leak DB connections.
    """
    from src.core.settings import get_settings
    from src.modules.auth.repository import RefreshTokensRepository
    from src.modules.auth.service import AuthService
    from src.modules.users.repository import UsersRepository

    settings = get_settings()
    application = create_app(settings)

    Session = async_sessionmaker(engine, expire_on_commit=False)

    # FastAPI dependency overrides accept generator functions.
    # We ``yield`` the AuthService and let the session's context
    # manager keep it alive across the awaited request handler.
    async def _auth_service_dep():
        async with Session() as session:
            yield AuthService(
                session=session,
                users_repo=UsersRepository(session),
                refresh_tokens_repo=RefreshTokensRepository(session),
                settings=settings,
            )

    application.dependency_overrides[get_auth_service] = _auth_service_dep

    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    application.dependency_overrides.clear()
