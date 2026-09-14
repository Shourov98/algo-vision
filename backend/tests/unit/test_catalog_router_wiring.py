"""Smoke tests for the catalog router wiring.

These tests verify the routers are mounted under the right
prefixes and declare the right response_model / status_code
metadata. They use FastAPI's TestClient with the service
dependency overridden by a fake so we don't need a database.

The full request/response cycle is exercised by the
integration tests added in B3.11.

Refs: ALGOVISION_BACKEND_PLAN.md §3.8 (B3.8 routers)
Refs: PUKU_BACKEND_AGENT.md §7
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.modules.catalog.dependencies import get_catalog_service
from src.modules.catalog.router import all_routers
from src.modules.catalog.schemas import (
    AlgorithmCodeResponse,
    AlgorithmDetailResponse,
    AlgorithmSummaryResponse,
    CategoryResponse,
    DataStructureResponse,
    TopicResponse,
)
from src.shared.pagination import Page

# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class _FakeService:
    """Minimal Protocol-satisfying fake for the wiring smoke tests."""

    def __init__(self) -> None:
        self.list_categories = AsyncMock(
            return_value=_empty_page(
                CategoryResponse(
                    id=uuid4(),
                    slug="sorting",
                    name="Sorting",
                    sort_order=1,
                    created_at=datetime.now(UTC),
                )
            )
        )
        self.get_category_by_slug = AsyncMock(
            return_value=CategoryResponse(
                id=uuid4(),
                slug="sorting",
                name="Sorting",
                sort_order=1,
                created_at=datetime.now(UTC),
            )
        )
        self.list_topics = AsyncMock(
            return_value=_empty_page(
                TopicResponse(id=uuid4(), slug="dp", name="DP")
            )
        )
        self.get_topic_by_slug = AsyncMock(
            return_value=TopicResponse(id=uuid4(), slug="dp", name="DP")
        )
        self.list_algorithms = AsyncMock(
            return_value=_empty_page(_make_algorithm_summary())
        )
        self.get_algorithm_by_slug = AsyncMock(
            return_value=_make_algorithm_detail()
        )
        self.get_current_code = AsyncMock(
            return_value=_make_algorithm_code()
        )
        self.list_code_versions = AsyncMock(
            return_value=_empty_page(_make_algorithm_code())
        )
        self.list_data_structures = AsyncMock(
            return_value=_empty_page(_make_data_structure_response())
        )
        self.get_data_structure_by_slug = AsyncMock(
            return_value=_make_data_structure_response()
        )


def _empty_page(item: Any) -> Page[Any]:
    return Page(items=[item], page=1, page_size=20, total=1)


def _make_algorithm_summary() -> AlgorithmSummaryResponse:
    return AlgorithmSummaryResponse(
        id=uuid4(),
        slug="quick-sort",
        name="Quick Sort",
        difficulty="medium",
        visualization_type="array",
        category_id=uuid4(),
        is_published=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_algorithm_detail() -> AlgorithmDetailResponse:
    alg_id = uuid4()
    cat_id = uuid4()
    return AlgorithmDetailResponse(
        id=alg_id,
        slug="quick-sort",
        name="Quick Sort",
        difficulty="medium",
        visualization_type="array",
        is_published=True,
        category={"id": cat_id, "slug": "sorting", "name": "Sorting"},
        topics=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_algorithm_code() -> AlgorithmCodeResponse:
    return AlgorithmCodeResponse(
        id=uuid4(),
        algorithm_id=uuid4(),
        language="python",
        version=1,
        source_code="def f(): pass",
        is_current=True,
        created_at=datetime.now(UTC),
    )


def _make_data_structure_response() -> DataStructureResponse:
    return DataStructureResponse(
        id=uuid4(),
        slug="stack",
        name="Stack",
        difficulty="easy",
        visualization_type="linear",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def client_with_fake_service() -> TestClient:
    app = FastAPI()
    for router in all_routers:
        app.include_router(router)
    app.dependency_overrides[get_catalog_service] = lambda: _FakeService()
    # Override get_optional_user so detail endpoints don't try
    # to resolve a real DB session. Smoke tests don't care
    # about user attribution; integration tests (B3.11) cover
    # the full auth flow.
    async def _no_user() -> None:
        return None

    from src.modules.catalog.dependencies import get_optional_user

    app.dependency_overrides[get_optional_user] = _no_user
    return TestClient(app)


# ---------------------------------------------------------------------------
# Endpoint smoke tests
# ---------------------------------------------------------------------------


def test_list_categories_returns_200(client_with_fake_service: TestClient) -> None:
    resp = client_with_fake_service.get("/api/v1/algorithms/categories")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert body["page"] == 1


def test_get_category_returns_200(client_with_fake_service: TestClient) -> None:
    resp = client_with_fake_service.get("/api/v1/algorithms/categories/sorting")
    assert resp.status_code == 200
    assert resp.json()["slug"] == "sorting"


def test_list_topics_returns_200(client_with_fake_service: TestClient) -> None:
    resp = client_with_fake_service.get("/api/v1/topics")
    assert resp.status_code == 200


def test_get_topic_returns_200(client_with_fake_service: TestClient) -> None:
    resp = client_with_fake_service.get("/api/v1/topics/dp")
    assert resp.status_code == 200
    assert resp.json()["slug"] == "dp"


def test_list_algorithms_returns_200(client_with_fake_service: TestClient) -> None:
    resp = client_with_fake_service.get("/api/v1/algorithms")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body


def test_list_algorithms_accepts_filters(client_with_fake_service: TestClient) -> None:
    resp = client_with_fake_service.get(
        "/api/v1/algorithms?category=sorting&difficulty=medium&page=2&page_size=10"
    )
    assert resp.status_code == 200


def test_get_algorithm_returns_200(client_with_fake_service: TestClient) -> None:
    resp = client_with_fake_service.get("/api/v1/algorithms/quick-sort")
    assert resp.status_code == 200
    body = resp.json()
    assert body["slug"] == "quick-sort"


def test_get_current_code_returns_200(client_with_fake_service: TestClient) -> None:
    resp = client_with_fake_service.get(
        "/api/v1/algorithms/quick-sort/code?language=python"
    )
    assert resp.status_code == 200
    assert resp.json()["language"] == "python"


def test_list_data_structures_returns_200(
    client_with_fake_service: TestClient,
) -> None:
    resp = client_with_fake_service.get("/api/v1/data-structures")
    assert resp.status_code == 200


def test_get_data_structure_returns_200(
    client_with_fake_service: TestClient,
) -> None:
    resp = client_with_fake_service.get("/api/v1/data-structures/stack")
    assert resp.status_code == 200
    assert resp.json()["slug"] == "stack"


# ---------------------------------------------------------------------------
# Schema envelope assertions
# ---------------------------------------------------------------------------


def test_list_categories_returns_list_response_envelope(
    client_with_fake_service: TestClient,
) -> None:
    resp = client_with_fake_service.get("/api/v1/algorithms/categories")
    body = resp.json()
    # The envelope keys must match CategoryListResponse.
    assert set(body.keys()) >= {"items", "page", "page_size", "total", "total_pages"}


def test_list_algorithms_returns_algorithm_list_envelope(
    client_with_fake_service: TestClient,
) -> None:
    resp = client_with_fake_service.get("/api/v1/algorithms")
    body = resp.json()
    assert set(body.keys()) >= {"items", "page", "page_size", "total", "total_pages"}


def test_404_status_is_returned_by_service() -> None:
    """When the service raises NotFound the global AppError
    handler should turn it into a 404 envelope.

    Uses ``create_app`` so the global exception handler is
    registered (a fresh ``FastAPI()`` would skip it).
    """
    from src.main import create_app

    app = create_app()

    async def _raising_service() -> Any:
        from src.modules.catalog.exceptions import CategoryNotFound

        raise CategoryNotFound("not found")

    app.dependency_overrides[get_catalog_service] = _raising_service

    # Override the optional-user dependency too so we don't
    # touch the DB for the auth path.
    async def _no_user() -> None:
        return None

    from src.modules.catalog.dependencies import get_optional_user

    app.dependency_overrides[get_optional_user] = _no_user

    test_client = TestClient(app)
    resp = test_client.get("/api/v1/algorithms/categories/sorting")
    assert resp.status_code == 404
    assert resp.json()["code"] == "catalog.category_not_found"
