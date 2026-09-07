"""CatalogService — algorithms + code versions tests.

Covers the read paths with event-dispatch assertions:
- Algorithm detail dispatches ``ItemViewedEvent`` when a
  user_id is supplied and skips dispatch when anonymous.
- The 403 (NotPublished) short-circuit prevents dispatch.
- ``get_current_code`` returns the AlgorithmCodeResponse
  and raises ``AlgorithmCodeVersionNotFound`` when missing.

Refs: ALGOVISION_BACKEND_PLAN.md §3.5, §6.7
Refs: PUKU_BACKEND_AGENT.md §13
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from src.modules.catalog.exceptions import (
    AlgorithmCodeVersionNotFound,
    AlgorithmNotFound,
    NotPublished,
)
from src.modules.catalog.schemas import (
    AlgorithmCodeResponse,
    AlgorithmDetailResponse,
    AlgorithmSummaryResponse,
)
from src.shared.events import ItemViewedEvent

from tests.unit._catalog_conftest import (
    empty_page,
    make_algorithm,
    make_code_version,
    make_service,
)

# ---------------------------------------------------------------------------
# list_algorithms
# ---------------------------------------------------------------------------


async def test_list_algorithms_delegates_to_repo() -> None:
    svc, repos, _ = make_service()
    repos["algos"].list.return_value = empty_page(
        [make_algorithm(slug="quick-sort")]
    )
    page = await svc.list_algorithms(filters=object())  # type: ignore[arg-type]
    repos["algos"].list.assert_awaited_once()
    assert len(page.items) == 1
    assert isinstance(page.items[0], AlgorithmSummaryResponse)
    assert page.items[0].slug == "quick-sort"


# ---------------------------------------------------------------------------
# get_algorithm_by_slug
# ---------------------------------------------------------------------------


async def test_get_algorithm_by_slug_raises_404_when_missing() -> None:
    svc, repos, _ = make_service()
    repos["algos"].get_by_slug.return_value = None
    with pytest.raises(AlgorithmNotFound):
        await svc.get_algorithm_by_slug("nope")


async def test_get_algorithm_by_slug_raises_not_published_for_draft() -> None:
    svc, repos, _ = make_service()
    repos["algos"].get_by_slug.return_value = make_algorithm(
        slug="draft", is_published=False
    )
    with pytest.raises(NotPublished):
        await svc.get_algorithm_by_slug("draft")


async def test_get_algorithm_by_slug_returns_draft_when_allowed() -> None:
    svc, repos, _ = make_service()
    repos["algos"].get_by_slug.return_value = make_algorithm(
        slug="draft", is_published=False
    )
    result = await svc.get_algorithm_by_slug("draft", include_unpublished=True)
    assert isinstance(result, AlgorithmDetailResponse)
    assert result.slug == "draft"
    assert result.is_published is False


async def test_get_algorithm_by_slug_skips_event_when_anonymous() -> None:
    svc, repos, dispatcher = make_service()
    repos["algos"].get_by_slug.return_value = make_algorithm(
        slug="quick-sort", is_published=True
    )
    result = await svc.get_algorithm_by_slug("quick-sort")
    assert isinstance(result, AlgorithmDetailResponse)
    assert result.slug == "quick-sort"
    assert dispatcher.events == []


async def test_get_algorithm_by_slug_dispatches_item_viewed_event() -> None:
    svc, repos, dispatcher = make_service()
    published = make_algorithm(slug="quick-sort", is_published=True)
    repos["algos"].get_by_slug.return_value = published
    user_id = uuid4()
    before = datetime.now(UTC)
    await svc.get_algorithm_by_slug("quick-sort", user_id=user_id)
    after = datetime.now(UTC)

    assert len(dispatcher.events) == 1
    event = dispatcher.events[0]
    assert isinstance(event, ItemViewedEvent)
    assert event.user_id == user_id
    assert event.item_type == "algorithm"
    assert event.item_id == published.id
    assert before <= event.viewed_at <= after


async def test_get_algorithm_by_slug_does_not_dispatch_for_draft() -> None:
    """The 403 path short-circuits before dispatch — callers
    who aren't allowed to see the draft shouldn't generate a
    view event."""
    svc, repos, dispatcher = make_service()
    repos["algos"].get_by_slug.return_value = make_algorithm(
        slug="draft", is_published=False
    )
    with pytest.raises(NotPublished):
        await svc.get_algorithm_by_slug("draft", user_id=uuid4())
    assert dispatcher.events == []


# ---------------------------------------------------------------------------
# get_current_code
# ---------------------------------------------------------------------------


async def test_get_current_code_returns_response_when_present() -> None:
    svc, repos, _ = make_service()
    algorithm_id = uuid4()
    repos["codes"].get_current.return_value = make_code_version(
        algorithm_id, "python"
    )
    result = await svc.get_current_code(algorithm_id, "python")
    assert isinstance(result, AlgorithmCodeResponse)
    assert result.algorithm_id == algorithm_id
    assert result.language == "python"
    repos["codes"].get_current.assert_awaited_once_with(algorithm_id, "python")


async def test_get_current_code_raises_when_missing() -> None:
    svc, _repos, _ = make_service()
    with pytest.raises(AlgorithmCodeVersionNotFound):
        await svc.get_current_code(uuid4(), "rust")


# ---------------------------------------------------------------------------
# list_code_versions
# ---------------------------------------------------------------------------


async def test_list_code_versions_delegates_to_repo() -> None:
    svc, repos, _ = make_service()
    algorithm_id = uuid4()
    repos["codes"].list.return_value = empty_page(
        [make_code_version(algorithm_id, "python")]
    )
    page = await svc.list_code_versions(filters=object())  # type: ignore[arg-type]
    repos["codes"].list.assert_awaited_once()
    assert len(page.items) == 1
    assert isinstance(page.items[0], AlgorithmCodeResponse)
    assert page.items[0].language == "python"
