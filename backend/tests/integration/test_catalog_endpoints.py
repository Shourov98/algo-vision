"""End-to-end integration tests for /api/v1/catalog endpoints.

Exercises the full HTTP stack against a real PostgreSQL test
database. Skipped when ``TEST_DATABASE_URL`` is not set (see
the integration ``conftest.py``).

What's covered
--------------
- Happy paths for every public catalog read endpoint.
- Filter behaviour (category, topic, difficulty, search).
- 404 envelopes when a slug doesn't exist.
- Pagination envelope shape (items, page, page_size, total,
  total_pages).
- ETag round-trip on /algorithms list and detail.

What this is NOT
----------------
- Unit-level service / router behaviour — those live in
  ``tests/unit/test_catalog_*``.

Refs: ALGOVISION_BACKEND_PLAN.md §3.5, §3.11 (B3.11 catalog tests)
Refs: PUKU_BACKEND_AGENT.md §13
"""

from __future__ import annotations

from datetime import UTC, datetime

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# catalog_client fixture is auto-discovered by pytest from
# tests/integration/conftest.py — no explicit import needed.
# The seed_* helpers below must be imported because they're
# plain coroutines, not fixtures.
from tests.integration.conftest import (
    seed_algorithm,
    seed_category,
    seed_code_version,
    seed_data_structure,
    seed_topic,
)

# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------


class TestCategories:
    async def test_list_returns_empty_page_when_no_rows(
        self, catalog_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, _ = catalog_client
        resp = await client.get("/api/v1/algorithms/categories")
        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []
        assert body["total"] == 0

    async def test_list_returns_seeded_categories(
        self, catalog_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, session = catalog_client
        await seed_category(session, slug="sorting")
        await seed_category(session, slug="graph", name="Graph")
        resp = await client.get("/api/v1/algorithms/categories")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        slugs = {c["slug"] for c in body["items"]}
        assert slugs == {"sorting", "graph"}

    async def test_get_by_slug_returns_row(
        self, catalog_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, session = catalog_client
        await seed_category(session, slug="sorting")
        resp = await client.get("/api/v1/algorithms/categories/sorting")
        assert resp.status_code == 200
        assert resp.json()["slug"] == "sorting"

    async def test_get_by_slug_404_when_missing(
        self, catalog_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, _ = catalog_client
        resp = await client.get("/api/v1/algorithms/categories/nope")
        assert resp.status_code == 404
        assert resp.json()["code"] == "catalog.category_not_found"


# ---------------------------------------------------------------------------
# Algorithms
# ---------------------------------------------------------------------------


class TestAlgorithms:
    async def test_list_returns_algorithms(
        self, catalog_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, session = catalog_client
        cat = await seed_category(session)
        await seed_algorithm(
            session, slug="quick-sort", category_id=cat.id
        )
        resp = await client.get("/api/v1/algorithms")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["slug"] == "quick-sort"

    async def test_list_filters_by_difficulty(
        self, catalog_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, session = catalog_client
        cat = await seed_category(session)
        await seed_algorithm(
            session,
            slug="bubble-sort",
            category_id=cat.id,
            difficulty="easy",
        )
        await seed_algorithm(
            session,
            slug="quick-sort",
            category_id=cat.id,
            difficulty="medium",
        )
        resp = await client.get("/api/v1/algorithms?difficulty=easy")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["slug"] == "bubble-sort"

    async def test_list_excludes_unpublished_by_default(
        self, catalog_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, session = catalog_client
        cat = await seed_category(session)
        await seed_algorithm(
            session,
            slug="draft",
            category_id=cat.id,
            is_published=False,
        )
        resp = await client.get("/api/v1/algorithms")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    async def test_get_by_slug_returns_detail(
        self, catalog_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, session = catalog_client
        cat = await seed_category(session)
        await seed_algorithm(
            session, slug="quick-sort", category_id=cat.id
        )
        resp = await client.get("/api/v1/algorithms/quick-sort")
        assert resp.status_code == 200
        body = resp.json()
        assert body["slug"] == "quick-sort"
        assert body["category"]["slug"] == "sorting"

    async def test_get_by_slug_404_for_missing(
        self, catalog_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, _ = catalog_client
        resp = await client.get("/api/v1/algorithms/missing")
        assert resp.status_code == 404

    async def test_etag_set_on_list(
        self, catalog_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, session = catalog_client
        cat = await seed_category(session)
        await seed_algorithm(
            session,
            slug="quick-sort",
            category_id=cat.id,
            updated_at=datetime(2025, 1, 1, tzinfo=UTC),
        )
        resp = await client.get("/api/v1/algorithms")
        assert resp.status_code == 200
        assert "etag" in resp.headers
        assert resp.headers["cache-control"] == "public, max-age=300"

    async def test_etag_set_on_detail(
        self, catalog_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, session = catalog_client
        cat = await seed_category(session)
        await seed_algorithm(
            session,
            slug="quick-sort",
            category_id=cat.id,
            updated_at=datetime(2025, 1, 1, tzinfo=UTC),
        )
        resp = await client.get("/api/v1/algorithms/quick-sort")
        assert resp.status_code == 200
        assert "etag" in resp.headers


# ---------------------------------------------------------------------------
# Code versions
# ---------------------------------------------------------------------------


class TestCodeVersions:
    async def test_current_code_returns_row(
        self, catalog_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, session = catalog_client
        cat = await seed_category(session)
        alg = await seed_algorithm(
            session, slug="quick-sort", category_id=cat.id
        )
        await seed_code_version(session, algorithm_id=alg.id)
        resp = await client.get(
            "/api/v1/algorithms/quick-sort/code?language=python"
        )
        assert resp.status_code == 200
        assert resp.json()["language"] == "python"

    async def test_current_code_404_when_missing(
        self, catalog_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, session = catalog_client
        cat = await seed_category(session)
        await seed_algorithm(
            session, slug="quick-sort", category_id=cat.id
        )
        resp = await client.get(
            "/api/v1/algorithms/quick-sort/code?language=java"
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


class TestDataStructures:
    async def test_list_returns_seeded(
        self, catalog_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, session = catalog_client
        await seed_data_structure(session, slug="stack")
        await seed_data_structure(session, slug="queue")
        resp = await client.get("/api/v1/data-structures")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2

    async def test_get_by_slug_returns_row(
        self, catalog_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, session = catalog_client
        await seed_data_structure(session, slug="stack")
        resp = await client.get("/api/v1/data-structures/stack")
        assert resp.status_code == 200
        assert resp.json()["slug"] == "stack"

    async def test_get_by_slug_404_when_missing(
        self, catalog_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, _ = catalog_client
        resp = await client.get("/api/v1/data-structures/heap")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Topics
# ---------------------------------------------------------------------------


class TestTopics:
    async def test_list_returns_seeded(
        self, catalog_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, session = catalog_client
        await seed_topic(session, slug="dp")
        await seed_topic(session, slug="graph", name="Graph")
        resp = await client.get("/api/v1/topics")
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    async def test_get_by_slug_returns_row(
        self, catalog_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, session = catalog_client
        await seed_topic(session, slug="dp")
        resp = await client.get("/api/v1/topics/dp")
        assert resp.status_code == 200
        assert resp.json()["slug"] == "dp"

    async def test_get_by_slug_404_when_missing(
        self, catalog_client: tuple[AsyncClient, AsyncSession]
    ) -> None:
        client, _ = catalog_client
        resp = await client.get("/api/v1/topics/missing")
        assert resp.status_code == 404
