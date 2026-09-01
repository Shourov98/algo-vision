"""HTTP caching (ETag + Cache-Control) tests for /algorithms.

Covers B3.9 (ALGOVISION_BACKEND_PLAN §3.9):

- 200 responses on ``GET /algorithms`` and ``GET /algorithms/{slug}``
  carry an ``ETag`` header and a ``Cache-Control: public, max-age=300``
  header.
- When ``If-None-Match`` carries the current ETag, the endpoint
  returns ``304 Not Modified`` with no body and the same ETag +
  Cache-Control headers.
- When ``If-None-Match`` carries a different ETag, the endpoint
  returns the full 200 response (no shortcut).
- The wildcard ``*`` matches any current resource.
- The list ETag changes when the filter signature changes (two
  calls with different filters should produce two different ETags).

The fake service uses a fixed ``updated_at`` so the computed
ETag is stable across requests — otherwise the test would race
the wall clock and produce flaky comparisons.

Refs: ALGOVISION_BACKEND_PLAN.md §3.9 (B3.9 ETag), §7 (Caching)
Refs: PUKU_BACKEND_AGENT.md §13
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.modules.catalog.dependencies import (
    get_catalog_service,
    get_optional_user,
)
from src.modules.catalog.router import all_routers
from src.modules.catalog.router._etag import (
    etag_from_filters_and_max_updated_at,
    filter_hash,
    max_updated_at_from,
)
from src.modules.catalog.schemas import (
    AlgorithmDetailResponse,
    AlgorithmSummaryResponse,
    CategorySummary,
)
from src.shared.pagination import Page

# ---------------------------------------------------------------------------
# Stable fixtures
# ---------------------------------------------------------------------------

# Fixed timestamps so ETag derivation is deterministic. The
# detail's ``updated_at`` is the same for every call so the
# detail endpoint emits the same ETag on repeat requests.
_FIXED_UPDATED_AT = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)


def _make_summary(slug: str) -> AlgorithmSummaryResponse:
    return AlgorithmSummaryResponse(
        id=uuid4(),
        slug=slug,
        name=slug.replace("-", " ").title(),
        difficulty="medium",
        visualization_type="array",
        category_id=uuid4(),
        is_published=True,
        created_at=_FIXED_UPDATED_AT,
        updated_at=_FIXED_UPDATED_AT,
    )


def _make_detail(slug: str) -> AlgorithmDetailResponse:
    cat = CategorySummary(
        id=uuid4(), slug="sorting", name="Sorting"
    )
    return AlgorithmDetailResponse(
        id=uuid4(),
        slug=slug,
        name=slug.replace("-", " ").title(),
        difficulty="medium",
        visualization_type="array",
        is_published=True,
        category=cat,
        topics=[],
        created_at=_FIXED_UPDATED_AT,
        updated_at=_FIXED_UPDATED_AT,
    )


class _StableFakeService:
    """Fake service that returns stable updated_at values.

    The wiring smoke test uses ``datetime.now(UTC)`` which
    races the wall clock. We pin the timestamps here so ETag
    comparisons are deterministic.
    """

    def __init__(self) -> None:
        self.list_algorithms = AsyncMock(
            return_value=Page(
                items=[_make_summary("quick-sort")],
                page=1,
                page_size=20,
                total=1,
            )
        )
        self.get_algorithm_by_slug = AsyncMock(
            return_value=_make_detail("quick-sort")
        )
        # Unused but kept so the wiring smoke-style methods
        # don't trip on attribute errors if a test ever
        # calls them.
        self.list_categories = AsyncMock(return_value=Page(items=[], page=1, page_size=20, total=0))
        self.get_category_by_slug = AsyncMock(return_value=None)
        self.list_topics = AsyncMock(return_value=Page(items=[], page=1, page_size=20, total=0))
        self.get_topic_by_slug = AsyncMock(return_value=None)
        self.get_current_code = AsyncMock(return_value=None)
        self.list_code_versions = AsyncMock(return_value=Page(items=[], page=1, page_size=20, total=0))
        self.list_data_structures = AsyncMock(return_value=Page(items=[], page=1, page_size=20, total=0))
        self.get_data_structure_by_slug = AsyncMock(return_value=None)


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    for router in all_routers:
        app.include_router(router)
    app.dependency_overrides[get_catalog_service] = lambda: _StableFakeService()

    async def _no_user() -> None:
        return None

    app.dependency_overrides[get_optional_user] = _no_user
    return TestClient(app)


# ---------------------------------------------------------------------------
# 200 response: ETag + Cache-Control headers
# ---------------------------------------------------------------------------


def test_list_algorithms_sets_etag_and_cache_control(
    client: TestClient,
) -> None:
    """List endpoint must set ETag + Cache-Control on 200."""
    resp = client.get("/api/v1/algorithms")
    assert resp.status_code == 200
    assert "etag" in resp.headers
    assert resp.headers["cache-control"] == "public, max-age=300"


def test_get_algorithm_sets_etag_and_cache_control(
    client: TestClient,
) -> None:
    """Detail endpoint must set ETag + Cache-Control on 200."""
    resp = client.get("/api/v1/algorithms/quick-sort")
    assert resp.status_code == 200
    assert "etag" in resp.headers
    assert resp.headers["cache-control"] == "public, max-age=300"


def test_list_etag_is_weak_and_quoted(client: TestClient) -> None:
    """ETag must follow RFC 7232 weak-validator format."""
    resp = client.get("/api/v1/algorithms")
    etag = resp.headers["etag"]
    assert etag.startswith('W/"') and etag.endswith('"')
    # 16 hex chars inside the quotes (per _etag.py).
    inner = etag.removeprefix('W/"').rstrip('"')
    assert len(inner) == 16
    assert all(c in "0123456789abcdef" for c in inner)


# ---------------------------------------------------------------------------
# 304 conditional GET
# ---------------------------------------------------------------------------


def test_list_returns_304_when_if_none_match_matches(
    client: TestClient,
) -> None:
    """When ``If-None-Match`` matches the current ETag, return 304.

    Validates the conditional-GET contract: a well-cached
    client should never pay for the JSON body on a hit.
    """
    first = client.get("/api/v1/algorithms")
    assert first.status_code == 200
    etag = first.headers["etag"]

    second = client.get(
        "/api/v1/algorithms",
        headers={"If-None-Match": etag},
    )
    assert second.status_code == 304
    # ETag + Cache-Control must still be present on the 304
    # so the client can update its stored metadata.
    assert second.headers["etag"] == etag
    assert second.headers["cache-control"] == "public, max-age=300"
    # 304 must not carry a body.
    assert second.content == b""


def test_detail_returns_304_when_if_none_match_matches(
    client: TestClient,
) -> None:
    first = client.get("/api/v1/algorithms/quick-sort")
    assert first.status_code == 200
    etag = first.headers["etag"]

    second = client.get(
        "/api/v1/algorithms/quick-sort",
        headers={"If-None-Match": etag},
    )
    assert second.status_code == 304
    assert second.headers["etag"] == etag
    assert second.headers["cache-control"] == "public, max-age=300"
    assert second.content == b""


def test_list_returns_200_when_if_none_match_differs(
    client: TestClient,
) -> None:
    """When the cached ETag is stale, the server returns 200 + body."""
    resp = client.get(
        "/api/v1/algorithms",
        headers={"If-None-Match": 'W/"deadbeefdeadbeef"'},
    )
    assert resp.status_code == 200
    assert "items" in resp.json()


def test_detail_returns_200_when_if_none_match_differs(
    client: TestClient,
) -> None:
    resp = client.get(
        "/api/v1/algorithms/quick-sort",
        headers={"If-None-Match": 'W/"deadbeefdeadbeef"'},
    )
    assert resp.status_code == 200
    assert resp.json()["slug"] == "quick-sort"


# ---------------------------------------------------------------------------
# If-None-Match parsing edge cases
# ---------------------------------------------------------------------------


def test_if_none_match_wildcard_matches(client: TestClient) -> None:
    """RFC 7232: ``*`` matches any current representation."""
    resp = client.get(
        "/api/v1/algorithms",
        headers={"If-None-Match": "*"},
    )
    assert resp.status_code == 304


def test_if_none_match_accepts_multiple_etags(client: TestClient) -> None:
    """RFC 7232: ``If-None-Match`` is a comma-separated list."""
    first = client.get("/api/v1/algorithms/quick-sort")
    etag = first.headers["etag"]
    resp = client.get(
        "/api/v1/algorithms/quick-sort",
        headers={"If-None-Match": f'W/"stale1234567abcd", {etag}, W/"other1234567efgh"'},
    )
    assert resp.status_code == 304


def test_if_none_match_strips_weak_prefix(client: TestClient) -> None:
    """Weak comparison per RFC 7232 §3.2 — strip ``W/`` prefix."""
    first = client.get("/api/v1/algorithms/quick-sort")
    etag = first.headers["etag"]
    # Opaque form (no W/) should still match.
    opaque = etag.removeprefix("W/")
    resp = client.get(
        "/api/v1/algorithms/quick-sort",
        headers={"If-None-Match": opaque},
    )
    assert resp.status_code == 304


# ---------------------------------------------------------------------------
# List ETag stability across requests with same filters
# ---------------------------------------------------------------------------


def test_list_etag_is_stable_for_identical_filters(
    client: TestClient,
) -> None:
    """Two GETs with identical filters return the same ETag.

    If they didn't, the conditional-GET contract would be
    broken: a client that stores the first ETag would never
    re-use it on the second request.
    """
    a = client.get("/api/v1/algorithms?category=sorting")
    b = client.get("/api/v1/algorithms?category=sorting")
    assert a.status_code == b.status_code == 200
    assert a.headers["etag"] == b.headers["etag"]


def test_list_etag_changes_when_filters_change(
    client: TestClient,
) -> None:
    """Different filters must produce different ETags.

    The filter signature is mixed into the list ETag
    (``filter_hash`` in ``_etag.py``); changing any field
    changes the hash.
    """
    a = client.get("/api/v1/algorithms")
    b = client.get("/api/v1/algorithms?difficulty=hard")
    assert a.headers["etag"] != b.headers["etag"]


# ---------------------------------------------------------------------------
# Detail ETag salt
# ---------------------------------------------------------------------------


def test_list_etag_and_detail_etag_differ_for_same_updated_at(
    client: TestClient,
) -> None:
    """Salt prevents list / detail ETags from colliding.

    If the list and detail endpoints both derived an ETag
    purely from the timestamp, they could share an ETag —
    and a stale detail response could be served from a
    cached list request. The salt isolates them.
    """
    list_resp = client.get("/api/v1/algorithms")
    detail_resp = client.get("/api/v1/algorithms/quick-sort")
    assert list_resp.headers["etag"] != detail_resp.headers["etag"]


# ---------------------------------------------------------------------------
# Helper unit tests (focused on _etag.py utilities)
# ---------------------------------------------------------------------------


def test_max_updated_at_from_empty_returns_none() -> None:
    assert max_updated_at_from([]) is None


def test_max_updated_at_from_single_returns_that_value() -> None:
    ts = datetime(2025, 6, 1, tzinfo=UTC)
    item = _make_summary("a")
    item = item.model_copy(update={"updated_at": ts})
    assert max_updated_at_from([item]) == ts


def test_max_updated_at_from_returns_largest() -> None:
    older = datetime(2025, 1, 1, tzinfo=UTC)
    newer = datetime(2025, 6, 1, tzinfo=UTC)
    oldest = datetime(2024, 1, 1, tzinfo=UTC)
    items = [
        _make_summary("a").model_copy(update={"updated_at": older}),
        _make_summary("b").model_copy(update={"updated_at": newer}),
        _make_summary("c").model_copy(update={"updated_at": oldest}),
    ]
    assert max_updated_at_from(items) == newer


def test_etag_from_filters_with_no_updated_at_is_stable() -> None:
    """The empty-page ETag must be stable so repeated queries
    with the same filter share the same cache key."""
    a = etag_from_filters_and_max_updated_at(
        filter_hash="abc",
        max_updated_at=None,
    )
    b = etag_from_filters_and_max_updated_at(
        filter_hash="abc",
        max_updated_at=None,
    )
    assert a == b


def test_filter_hash_changes_with_field_value() -> None:
    """Changing a dataclass field must change the filter hash."""
    from src.modules.catalog.filters.categories import CategoryFilters
    from src.shared.pagination import Pagination

    base = CategoryFilters(
        pagination=Pagination(page=1, page_size=20),
    )
    same = CategoryFilters(
        pagination=Pagination(page=1, page_size=20),
    )
    different = CategoryFilters(
        pagination=Pagination(page=2, page_size=20),
    )
    assert filter_hash(base) == filter_hash(same)
    assert filter_hash(base) != filter_hash(different)

