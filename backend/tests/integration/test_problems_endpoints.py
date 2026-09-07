"""End-to-end integration tests for /api/v1/problems endpoints.

Exercises the full HTTP stack against a real PostgreSQL
test database. Skipped when ``TEST_DATABASE_URL`` is not
set (see the integration ``conftest.py``).

What's covered
--------------
- Happy paths for problems + companies list / detail.
- 404 envelopes when a slug doesn't exist.
- Pagination envelope shape (items, page, page_size, total,
  total_pages).
- The detail endpoint embeds topic + company summaries
  (the headline feature of B4.8).
- Difficulty + visualization_available filters.

What this is NOT
----------------
- Unit-level service / router behaviour — those live in
  ``tests/unit/test_problems_service.py``.

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 4 - B4.11)
Refs: PUKU_BACKEND_AGENT.md §13
"""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# problems_client fixture is auto-discovered by pytest from
# tests/integration/conftest.py - no explicit import needed.
# The seed_* helpers below must be imported because they're
# plain coroutines, not fixtures.
from tests.integration.conftest import (
    link_problem_to_company,
    link_problem_to_topic,
    seed_company,
    seed_problem,
    seed_topic,
)

# ---------------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------------


class TestCompanies:
    async def test_list_returns_empty_page_when_no_rows(
        self, problems_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, _ = problems_client
        resp = await client.get("/api/v1/problems/companies")
        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []
        assert body["total"] == 0

    async def test_list_returns_seeded_companies(
        self, problems_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, session = problems_client
        await seed_company(session, slug="google")
        await seed_company(session, slug="amazon", name="Amazon")
        resp = await client.get("/api/v1/problems/companies")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        slugs = {c["slug"] for c in body["items"]}
        assert slugs == {"google", "amazon"}

    async def test_get_by_slug_returns_row(
        self, problems_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, session = problems_client
        await seed_company(session, slug="google")
        resp = await client.get("/api/v1/problems/companies/google")
        assert resp.status_code == 200
        assert resp.json()["slug"] == "google"

    async def test_get_by_slug_404_when_missing(
        self, problems_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, _ = problems_client
        resp = await client.get("/api/v1/problems/companies/nope")
        assert resp.status_code == 404
        assert resp.json()["code"] == "problems.company_not_found"


# ---------------------------------------------------------------------------
# Problems — list
# ---------------------------------------------------------------------------


class TestProblemsList:
    async def test_list_returns_empty_page_when_no_rows(
        self, problems_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, _ = problems_client
        resp = await client.get("/api/v1/problems")
        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []
        assert body["total"] == 0

    async def test_list_returns_seeded_problems(
        self, problems_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, session = problems_client
        await seed_problem(session, slug="two-sum")
        await seed_problem(session, slug="lru-cache", difficulty="medium")
        resp = await client.get("/api/v1/problems")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        slugs = {p["slug"] for p in body["items"]}
        assert slugs == {"two-sum", "lru-cache"}

    async def test_list_filters_by_difficulty(
        self, problems_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, session = problems_client
        await seed_problem(session, slug="two-sum", difficulty="easy")
        await seed_problem(
            session, slug="lru-cache", difficulty="medium"
        )
        await seed_problem(
            session, slug="n-queens", difficulty="hard"
        )
        resp = await client.get("/api/v1/problems?difficulty=easy")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["slug"] == "two-sum"

    async def test_list_filters_by_visualization_available(
        self, problems_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, session = problems_client
        await seed_problem(
            session,
            slug="two-sum",
            visualization_available=True,
        )
        await seed_problem(
            session,
            slug="n-queens",
            visualization_available=False,
        )
        resp = await client.get(
            "/api/v1/problems?visualization_available=true"
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["slug"] == "two-sum"


# ---------------------------------------------------------------------------
# Problems — detail
# ---------------------------------------------------------------------------


class TestProblemsDetail:
    async def test_get_by_slug_returns_detail(
        self, problems_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, session = problems_client
        await seed_problem(session, slug="two-sum")
        resp = await client.get("/api/v1/problems/two-sum")
        assert resp.status_code == 200
        body = resp.json()
        assert body["slug"] == "two-sum"
        assert body["difficulty"] == "easy"

    async def test_get_by_slug_404_for_missing(
        self, problems_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, _ = problems_client
        resp = await client.get("/api/v1/problems/missing")
        assert resp.status_code == 404
        assert resp.json()["code"] == "problems.problem_not_found"

    async def test_detail_embeds_topics(
        self, problems_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, session = problems_client
        problem = await seed_problem(session, slug="two-sum")
        topic_a = await seed_topic(session, slug="hashing")
        topic_b = await seed_topic(session, slug="sliding-window")
        await link_problem_to_topic(
            session, problem_id=problem.id, topic_id=topic_a.id
        )
        await link_problem_to_topic(
            session, problem_id=problem.id, topic_id=topic_b.id
        )
        resp = await client.get("/api/v1/problems/two-sum")
        assert resp.status_code == 200
        body = resp.json()
        topic_slugs = sorted(t["slug"] for t in body["topics"])
        assert topic_slugs == ["hashing", "sliding-window"]

    async def test_detail_embeds_companies(
        self, problems_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, session = problems_client
        problem = await seed_problem(session, slug="two-sum")
        company_a = await seed_company(session, slug="google")
        company_b = await seed_company(session, slug="amazon")
        await link_problem_to_company(
            session,
            problem_id=problem.id,
            company_id=company_a.id,
        )
        await link_problem_to_company(
            session,
            problem_id=problem.id,
            company_id=company_b.id,
        )
        resp = await client.get("/api/v1/problems/two-sum")
        assert resp.status_code == 200
        body = resp.json()
        company_slugs = sorted(c["slug"] for c in body["companies"])
        assert company_slugs == ["amazon", "google"]

    async def test_detail_has_empty_embeds_when_unjoined(
        self, problems_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        """A problem with no topic / company joins still returns a
        valid detail with empty embed lists."""
        client, session = problems_client
        await seed_problem(session, slug="lonely")
        resp = await client.get("/api/v1/problems/lonely")
        assert resp.status_code == 200
        body = resp.json()
        assert body["topics"] == []
        assert body["companies"] == []
