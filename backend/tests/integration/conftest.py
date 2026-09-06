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
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from src.core.db import Base
from src.core.settings import get_settings
from src.main import create_app
from src.modules.auth.dependencies import get_auth_service
from src.modules.catalog.dependencies import (
    get_catalog_service,
    get_optional_user,
)
from src.modules.catalog.models import (
    Algorithm,
    AlgorithmCodeVersion,
    Category,
    DataStructure,
    Topic,
)
from src.modules.catalog.repository import (
    AlgorithmCodeVersionRepository,
    AlgorithmRepository,
    CategoryRepository,
    DataStructureRepository,
    TopicRepository,
)
from src.modules.catalog.service import CatalogService
from src.modules.problems.models import (
    Company,
    Problem,
    ProblemCompany,
    ProblemTopic,
)
from src.shared.events import InProcessEventDispatcher, NoopEventDispatcher

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


# ---------------------------------------------------------------------------
# Catalog-specific fixtures + seed helpers
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def catalog_client(
    engine,
) -> AsyncIterator[tuple[AsyncClient, AsyncSession]]:
    """Yield (httpx client, raw DB session) wired to the same engine.

    ``get_catalog_service`` is overridden so the catalog
    service uses the test session — the app's default
    engine (pointed at the production DB) is bypassed.
    ``get_optional_user`` is overridden to a no-op so detail
    reads don't try to resolve a real auth flow.

    Used by ``test_catalog_endpoints.py`` to exercise the
    full HTTP stack against a real Postgres test database.
    """
    settings = get_settings()
    application = create_app(settings)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async def _catalog_service_dep() -> AsyncIterator[CatalogService]:
        async with Session() as session:
            yield CatalogService(
                categories_repo=CategoryRepository(session),
                topics_repo=TopicRepository(session),
                algorithms_repo=AlgorithmRepository(session),
                code_versions_repo=AlgorithmCodeVersionRepository(session),
                data_structures_repo=DataStructureRepository(session),
                events=InProcessEventDispatcher(),
            )

    async def _no_user() -> None:
        return None

    application.dependency_overrides[get_catalog_service] = _catalog_service_dep
    application.dependency_overrides[get_optional_user] = _no_user

    async with Session() as session:
        transport = ASGITransport(app=application)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            yield client, session

    application.dependency_overrides.clear()


async def seed_category(
    session: AsyncSession,
    slug: str = "sorting",
    name: str = "Sorting",
) -> Category:
    """Insert a Category row in ``session`` and return it."""
    cat = Category(slug=slug, name=name, sort_order=1)
    session.add(cat)
    await session.commit()
    await session.refresh(cat)
    return cat


async def seed_algorithm(
    session: AsyncSession,
    *,
    slug: str = "quick-sort",
    category_id: object,
    difficulty: str = "medium",
    is_published: bool = True,
    updated_at: object = None,
) -> Algorithm:
    """Insert an Algorithm row in ``session`` and return it."""
    alg = Algorithm(
        slug=slug,
        name=slug.replace("-", " ").title(),
        category_id=category_id,
        difficulty=difficulty,
        visualization_type="array",
        is_published=is_published,
    )
    session.add(alg)
    await session.commit()
    await session.refresh(alg)
    if updated_at is not None:
        alg.updated_at = updated_at  # type: ignore[assignment]
        await session.commit()
        await session.refresh(alg)
    return alg


async def seed_data_structure(
    session: AsyncSession, slug: str = "stack"
) -> DataStructure:
    """Insert a DataStructure row in ``session`` and return it."""
    ds = DataStructure(
        slug=slug,
        name=slug.title(),
        difficulty="easy",
        visualization_type="linear",
    )
    session.add(ds)
    await session.commit()
    await session.refresh(ds)
    return ds


async def seed_topic(
    session: AsyncSession, slug: str = "dp", name: str = "DP"
) -> Topic:
    """Insert a Topic row in ``session`` and return it."""
    topic = Topic(slug=slug, name=name)
    session.add(topic)
    await session.commit()
    await session.refresh(topic)
    return topic


async def seed_code_version(
    session: AsyncSession,
    *,
    algorithm_id: object,
    language: str = "python",
    version: int = 1,
    is_current: bool = True,
) -> AlgorithmCodeVersion:
    """Insert an AlgorithmCodeVersion row in ``session`` and return it."""
    cv = AlgorithmCodeVersion(
        algorithm_id=algorithm_id,
        language=language,
        source_code="def f(): pass",
        version=version,
        is_current=is_current,
    )
    session.add(cv)
    await session.commit()
    await session.refresh(cv)
    return cv


# ---------------------------------------------------------------------------
# Problems-specific fixtures + seed helpers
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def problems_client(
    engine,
) -> AsyncIterator[tuple[AsyncClient, AsyncSession]]:
    """Yield (httpx client, raw DB session) wired to the same engine.

    ``get_problems_service`` is overridden so the problems
    service uses the test session — the app's default
    engine (pointed at the production DB) is bypassed.

    Used by ``test_problems_endpoints.py`` to exercise the
    full HTTP stack against a real Postgres test database.
    """
    from src.modules.problems.dependencies import (
        get_problems_service,
    )
    from src.modules.problems.repository import (
        CompanyRepository,
        ProblemRepository,
    )
    from src.modules.problems.service import ProblemsService

    settings = get_settings()
    application = create_app(settings)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async def _problems_service_dep() -> AsyncIterator[ProblemsService]:
        async with Session() as session:
            yield ProblemsService(
                problems_repo=ProblemRepository(session),
                companies_repo=CompanyRepository(session),
                events=NoopEventDispatcher(),
            )

    application.dependency_overrides[
        get_problems_service
    ] = _problems_service_dep

    async with Session() as session:
        transport = ASGITransport(app=application)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            yield client, session

    application.dependency_overrides.clear()


async def seed_problem(
    session: AsyncSession,
    *,
    slug: str = "two-sum",
    title: str | None = None,
    difficulty: str = "easy",
    visualization_available: bool = True,
) -> Problem:
    """Insert a Problem row in ``session`` and return it."""
    p = Problem(
        slug=slug,
        title=title or slug.replace("-", " ").title(),
        description=f"The {slug} problem.",
        difficulty=difficulty,
        solution_explanation="O(n) solution.",
        external_reference="LC-1",
        visualization_available=visualization_available,
    )
    session.add(p)
    await session.commit()
    await session.refresh(p)
    return p


async def seed_company(
    session: AsyncSession,
    *,
    slug: str = "google",
    name: str | None = None,
) -> Company:
    """Insert a Company row in ``session`` and return it."""
    c = Company(slug=slug, name=name or slug.title())
    session.add(c)
    await session.commit()
    await session.refresh(c)
    return c


async def link_problem_to_company(
    session: AsyncSession,
    *,
    problem_id: object,
    company_id: object,
) -> None:
    """Insert a problem_companies join row."""
    session.add(
        ProblemCompany(
            problem_id=problem_id, company_id=company_id
        )
    )
    await session.commit()


async def link_problem_to_topic(
    session: AsyncSession,
    *,
    problem_id: object,
    topic_id: object,
) -> None:
    """Insert a problem_topics join row."""
    session.add(
        ProblemTopic(problem_id=problem_id, topic_id=topic_id)
    )
    await session.commit()
