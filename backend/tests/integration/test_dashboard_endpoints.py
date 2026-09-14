"""End-to-end integration tests for /api/v1/dashboard endpoints.

Exercises the full HTTP stack against a real PostgreSQL
test database. Skipped when ``TEST_DATABASE_URL`` is not
set (see the integration ``conftest.py``).

What's covered
--------------
- Auth: dashboard requires a real user; 401 without.
- Summary shape: all top-level keys present.
- Empty-state: a brand-new user gets a zeroed summary.
- Catalog totals: algorithms_total / problems_total reflect
  the seeded catalog.

Refs: ALGOVISION_BACKEND_PLAN.md §5 (Phase 5 — B5.13)
Refs: PUKU_BACKEND_AGENT.md §13
"""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.catalog.models import Algorithm, Category


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


class TestDashboardAuth:
    async def test_dashboard_requires_auth(
        self, progress_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, _ = progress_client
        resp = await client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 401


class TestDashboardSummary:
    async def test_summary_shape_for_new_user(
        self, progress_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        """A fresh user gets a fully-shaped but zeroed summary."""
        client, session = progress_client

        # Seed at least one published algorithm so the
        # catalog COUNT returns > 0.
        cat = Category(slug="sorting", name="Sorting")
        session.add(cat)
        await session.commit()
        await session.refresh(cat)
        alg = Algorithm(
            slug="bubble-sort",
            name="Bubble Sort",
            category_id=cat.id,
            difficulty="easy",
            visualization_type="array",
            is_published=True,
        )
        session.add(alg)
        await session.commit()

        token = await _login(client, email="dash@example.com")
        client.headers["Authorization"] = f"Bearer {token}"

        resp = await client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 200
        body = resp.json()
        # Top-level keys present.
        for key in (
            "algorithms_learned",
            "algorithms_total",
            "problems_solved",
            "problems_total",
            "interview_readiness",
            "skill_mapping",
            "focus_areas",
            "current_streak",
            "activity",
            "recently_viewed",
        ):
            assert key in body, f"missing key {key!r}"
        # Empty-state numerics.
        assert body["algorithms_learned"] == 0
        assert body["problems_solved"] == 0
        assert body["current_streak"] == 0
        # Catalog totals reflect seeded data.
        assert body["algorithms_total"] == 1
        assert body["problems_total"] == 0
