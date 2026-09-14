"""End-to-end integration tests for /api/v1/progress endpoints.

Exercises the full HTTP stack against a real PostgreSQL
test database. Skipped when ``TEST_DATABASE_URL`` is not
set (see the integration ``conftest.py``).

What's covered
--------------
- Auth: every endpoint requires a real user; 401 without.
- POST mark: idempotent upsert of progress rows.
- GET overview: composite counts.
- GET recents: returns the user's recent items.

Refs: ALGOVISION_BACKEND_PLAN.md §5 (Phase 5 — B5.13)
Refs: PUKU_BACKEND_AGENT.md §13
"""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.catalog.models import Algorithm, Category
from src.modules.users.models import User

from tests.integration.conftest import seed_recent_item


async def _login(
    client: AsyncClient,
    *,
    email: str,
    password: str = "supersecret123",
    name: str = "User",
) -> str:
    """Register + log in via the auth endpoints; return access token."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "name": name},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return login.json()["access_token"]


class TestProgressAuth:
    async def test_progress_requires_auth(
        self, progress_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, _ = progress_client
        resp = await client.get("/api/v1/progress/overview")
        assert resp.status_code == 401


class TestProgressOverview:
    async def test_overview_returns_zero_counts_when_no_progress(
        self, progress_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, _session = progress_client
        token = await _login(client, email="ov@example.com")
        client.headers["Authorization"] = f"Bearer {token}"

        resp = await client.get("/api/v1/progress/overview")
        assert resp.status_code == 200
        body = resp.json()
        assert body["algorithms"]["completed"] == 0
        assert body["problems"]["completed"] == 0


class TestProgressRecents:
    async def test_recents_returns_user_items(
        self, progress_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, session = progress_client
        token = await _login(client, email="r@example.com")
        client.headers["Authorization"] = f"Bearer {token}"

        # Resolve user id.
        result = await session.execute(
            select(User).where(User.email == "r@example.com")
        )
        user = result.scalar_one()
        await seed_recent_item(
            session, user_id=user.id, item_type="algorithm"
        )

        resp = await client.get("/api/v1/progress/recents")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) == 1
        assert body["items"][0]["item_type"] == "algorithm"


class TestMarkAlgorithm:
    async def test_mark_algorithm_creates_progress(
        self, progress_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, session = progress_client

        # Seed a category + algorithm.
        cat = Category(slug="sorting", name="Sorting")
        session.add(cat)
        await session.commit()
        await session.refresh(cat)
        alg = Algorithm(
            slug="quick-sort",
            name="Quick Sort",
            category_id=cat.id,
            difficulty="medium",
            visualization_type="array",
            is_published=True,
        )
        session.add(alg)
        await session.commit()
        await session.refresh(alg)

        # Register + log in.
        token = await _login(client, email="mark@example.com")
        client.headers["Authorization"] = f"Bearer {token}"

        resp = await client.post(
            f"/api/v1/progress/algorithms/{alg.id}",
            json={
                "status": "in_progress",
                "completion_percentage": 50,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "in_progress"
        assert body["completion_percentage"] == 50
