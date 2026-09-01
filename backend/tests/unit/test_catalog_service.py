"""Unit tests for CatalogService.

These tests use AsyncMock-backed fakes (no DB) so we can
exercise every branch of the service in isolation. End-to-end
behavior — including SQL constraints, transaction boundaries,
and Alembic migrations — is covered by the integration tests
added in B3.11.

What we verify here
-------------------
- Each ``list_*`` method delegates to its repository and
  returns the page unchanged.
- ``get_*_by_slug`` raises the right NotFound error when the
  repository returns ``None`` and returns the row otherwise.
- ``get_algorithm_by_slug`` raises ``NotPublished`` when the
  row is hidden and ``include_unpublished`` is False.
- ``get_algorithm_by_slug`` returns the row and skips the
  event dispatch when no user_id is provided.
- ``get_algorithm_by_slug`` dispatches ``ItemViewedEvent``
  with the right payload when a user_id is provided.
- The same event-dispatch contract holds for
  ``get_data_structure_by_slug``.
- ``get_current_code`` raises ``AlgorithmCodeVersionNotFound``
  when the repository returns ``None``.

Refs: ALGOVISION_BACKEND_PLAN.md §3.5 (B3.6 catalog services),
      §6.7 (event dispatch)
Refs: PUKU_BACKEND_AGENT.md §13 (Test Conventions)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from src.modules.catalog.exceptions import (
    AlgorithmCodeVersionNotFound,
    AlgorithmNotFound,
    CategoryNotFound,
    DataStructureNotFound,
    NotPublished,
    TopicNotFound,
)
from src.modules.catalog.models import (
    Algorithm,
    AlgorithmCodeVersion,
    Category,
    DataStructure,
    Topic,
)
from src.modules.catalog.service import CatalogService
from src.shared.events import EventDispatcherProtocol, ItemViewedEvent

# ---------------------------------------------------------------------------
# Fakes — minimal Protocol-satisfying stand-ins
# ---------------------------------------------------------------------------


class _FakeAlgorithmRepo:
    """AsyncMock-shaped fake that records calls."""

    def __init__(self) -> None:
        self.get_by_slug = AsyncMock(return_value=None)
        self.list = AsyncMock(return_value=[])


class _FakeCategoryRepo:
    def __init__(self) -> None:
        self.get_by_slug = AsyncMock(return_value=None)
        self.list = AsyncMock(return_value=[])


class _FakeTopicRepo:
    def __init__(self) -> None:
        self.get_by_slug = AsyncMock(return_value=None)
        self.list = AsyncMock(return_value=[])


class _FakeCodeVersionRepo:
    def __init__(self) -> None:
        self.get_current = AsyncMock(return_value=None)
        self.list = AsyncMock(return_value=[])


class _FakeDataStructureRepo:
    def __init__(self) -> None:
        self.get_by_slug = AsyncMock(return_value=None)
        self.list = AsyncMock(return_value=[])


class _RecordingDispatcher:
    """Captures every dispatched event for assertion."""

    def __init__(self) -> None:
        self.events: list[Any] = []
        self.register = lambda *a, **kw: None

    async def dispatch(self, event: Any) -> None:
        self.events.append(event)


def _make_service() -> tuple[CatalogService, dict[str, Any], _RecordingDispatcher]:
    """Return (service, repos_by_name, dispatcher) for direct poking."""
    algos = _FakeAlgorithmRepo()
    cats = _FakeCategoryRepo()
    topics = _FakeTopicRepo()
    codes = _FakeCodeVersionRepo()
    ds = _FakeDataStructureRepo()
    dispatcher = _RecordingDispatcher()
    svc = CatalogService(
        categories_repo=cats,  # type: ignore[arg-type]
        topics_repo=topics,  # type: ignore[arg-type]
        algorithms_repo=algos,  # type: ignore[arg-type]
        code_versions_repo=codes,  # type: ignore[arg-type]
        data_structures_repo=ds,  # type: ignore[arg-type]
        events=dispatcher,
    )
    repos = {
        "algos": algos,
        "cats": cats,
        "topics": topics,
        "codes": codes,
        "ds": ds,
    }
    return svc, repos, dispatcher


# ---------------------------------------------------------------------------
# list_* delegation
# ---------------------------------------------------------------------------


async def test_list_categories_delegates_to_repo() -> None:
    svc, repos, _ = _make_service()
    page = await svc.list_categories(filters=object())  # type: ignore[arg-type]
    repos["cats"].list.assert_awaited_once()
    assert page == []


async def test_list_topics_delegates_to_repo() -> None:
    svc, repos, _ = _make_service()
    await svc.list_topics(filters=object())  # type: ignore[arg-type]
    repos["topics"].list.assert_awaited_once()


async def test_list_algorithms_delegates_to_repo() -> None:
    svc, repos, _ = _make_service()
    await svc.list_algorithms(filters=object())  # type: ignore[arg-type]
    repos["algos"].list.assert_awaited_once()


async def test_list_data_structures_delegates_to_repo() -> None:
    svc, repos, _ = _make_service()
    await svc.list_data_structures(filters=object())  # type: ignore[arg-type]
    repos["ds"].list.assert_awaited_once()


async def test_list_code_versions_delegates_to_repo() -> None:
    svc, repos, _ = _make_service()
    await svc.list_code_versions(filters=object())  # type: ignore[arg-type]
    repos["codes"].list.assert_awaited_once()


# ---------------------------------------------------------------------------
# get_*_by_slug — happy path & 404
# ---------------------------------------------------------------------------


async def test_get_category_by_slug_returns_row_when_present() -> None:
    svc, repos, _ = _make_service()
    category = Category(slug="sorting", name="Sorting")
    repos["cats"].get_by_slug.return_value = category
    result = await svc.get_category_by_slug("sorting")
    assert result is category


async def test_get_category_by_slug_raises_when_missing() -> None:
    svc, repos, _ = _make_service()
    repos["cats"].get_by_slug.return_value = None
    with pytest.raises(CategoryNotFound):
        await svc.get_category_by_slug("nope")


async def test_get_topic_by_slug_returns_row_when_present() -> None:
    svc, repos, _ = _make_service()
    topic = Topic(slug="dp", name="Dynamic Programming")
    repos["topics"].get_by_slug.return_value = topic
    result = await svc.get_topic_by_slug("dp")
    assert result is topic


async def test_get_topic_by_slug_raises_when_missing() -> None:
    svc, repos, _ = _make_service()
    repos["topics"].get_by_slug.return_value = None
    with pytest.raises(TopicNotFound):
        await svc.get_topic_by_slug("nope")


async def test_get_data_structure_by_slug_returns_row_when_present() -> None:
    svc, repos, _ = _make_service()
    ds = DataStructure(slug="stack", name="Stack")
    repos["ds"].get_by_slug.return_value = ds
    result = await svc.get_data_structure_by_slug("stack")
    assert result is ds


async def test_get_data_structure_by_slug_raises_when_missing() -> None:
    svc, repos, _ = _make_service()
    repos["ds"].get_by_slug.return_value = None
    with pytest.raises(DataStructureNotFound):
        await svc.get_data_structure_by_slug("nope")


# ---------------------------------------------------------------------------
# Algorithm get_by_slug — 404 / 403 / event dispatch
# ---------------------------------------------------------------------------


def _make_algorithm(*, slug: str, is_published: bool) -> Algorithm:
    """Build an Algorithm ORM row without going through the DB."""
    alg = Algorithm(
        slug=slug,
        name=slug.replace("-", " ").title(),
        category_id=uuid4(),
        is_published=is_published,
    )
    # ``id`` and ``created_at`` are server defaults; set them
    # explicitly so we can assert on them.
    alg.id = uuid4()
    alg.created_at = datetime.now(UTC)
    return alg


async def test_get_algorithm_by_slug_raises_404_when_missing() -> None:
    svc, repos, _ = _make_service()
    repos["algos"].get_by_slug.return_value = None
    with pytest.raises(AlgorithmNotFound):
        await svc.get_algorithm_by_slug("nope")


async def test_get_algorithm_by_slug_raises_not_published_for_draft() -> None:
    svc, repos, _ = _make_service()
    repos["algos"].get_by_slug.return_value = _make_algorithm(
        slug="draft", is_published=False
    )
    with pytest.raises(NotPublished):
        await svc.get_algorithm_by_slug("draft")


async def test_get_algorithm_by_slug_returns_draft_when_allowed() -> None:
    svc, repos, _ = _make_service()
    draft = _make_algorithm(slug="draft", is_published=False)
    repos["algos"].get_by_slug.return_value = draft
    result = await svc.get_algorithm_by_slug("draft", include_unpublished=True)
    assert result is draft


async def test_get_algorithm_by_slug_skips_event_when_anonymous() -> None:
    svc, repos, dispatcher = _make_service()
    published = _make_algorithm(slug="quick-sort", is_published=True)
    repos["algos"].get_by_slug.return_value = published
    result = await svc.get_algorithm_by_slug("quick-sort")
    assert result is published
    assert dispatcher.events == []


async def test_get_algorithm_by_slug_dispatches_item_viewed_event() -> None:
    svc, repos, dispatcher = _make_service()
    published = _make_algorithm(slug="quick-sort", is_published=True)
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
    # Timestamp must fall within the test window.
    assert before <= event.viewed_at <= after


async def test_get_algorithm_by_slug_does_not_dispatch_for_draft() -> None:
    """The 403 path short-circuits before the dispatch — callers
    who aren't allowed to see the draft shouldn't generate a view
    event."""
    svc, repos, dispatcher = _make_service()
    repos["algos"].get_by_slug.return_value = _make_algorithm(
        slug="draft", is_published=False
    )
    with pytest.raises(NotPublished):
        await svc.get_algorithm_by_slug("draft", user_id=uuid4())
    assert dispatcher.events == []


# ---------------------------------------------------------------------------
# Data structure event dispatch
# ---------------------------------------------------------------------------


def _make_data_structure(slug: str) -> DataStructure:
    ds = DataStructure(slug=slug, name=slug.title())
    ds.id = uuid4()
    ds.created_at = datetime.now(UTC)
    return ds


async def test_get_data_structure_by_slug_skips_event_when_anonymous() -> None:
    svc, repos, dispatcher = _make_service()
    ds = _make_data_structure("stack")
    repos["ds"].get_by_slug.return_value = ds
    await svc.get_data_structure_by_slug("stack")
    assert dispatcher.events == []


async def test_get_data_structure_by_slug_dispatches_item_viewed_event() -> None:
    svc, repos, dispatcher = _make_service()
    ds = _make_data_structure("stack")
    repos["ds"].get_by_slug.return_value = ds
    user_id = uuid4()
    await svc.get_data_structure_by_slug("stack", user_id=user_id)
    assert len(dispatcher.events) == 1
    event = dispatcher.events[0]
    assert isinstance(event, ItemViewedEvent)
    assert event.user_id == user_id
    assert event.item_type == "data_structure"
    assert event.item_id == ds.id


# ---------------------------------------------------------------------------
# get_current_code
# ---------------------------------------------------------------------------


def _make_code_version(algorithm_id: UUID, language: str) -> AlgorithmCodeVersion:
    cv = AlgorithmCodeVersion(
        algorithm_id=algorithm_id,
        language=language,
        version=1,
        source_code="def f(): pass",
        is_current=True,
    )
    cv.id = uuid4()
    cv.created_at = datetime.now(UTC)
    return cv


async def test_get_current_code_returns_row_when_present() -> None:
    svc, repos, _ = _make_service()
    algorithm_id = uuid4()
    cv = _make_code_version(algorithm_id, "python")
    repos["codes"].get_current.return_value = cv
    result = await svc.get_current_code(algorithm_id, "python")
    assert result is cv
    repos["codes"].get_current.assert_awaited_once_with(algorithm_id, "python")


async def test_get_current_code_raises_when_missing() -> None:
    svc, _repos, _ = _make_service()
    with pytest.raises(AlgorithmCodeVersionNotFound):
        await svc.get_current_code(uuid4(), "rust")


# ---------------------------------------------------------------------------
# Dispatcher protocol sanity
# ---------------------------------------------------------------------------


async def test_dispatcher_protocol_satisfied_by_recording() -> None:
    """Sanity check: the fake dispatcher is a Protocol
    substitutable for the real one (Liskov)."""
    dispatcher: EventDispatcherProtocol = _RecordingDispatcher()
    await dispatcher.dispatch(
        ItemViewedEvent(
            user_id=uuid4(),
            item_type="algorithm",
            item_id=uuid4(),
            viewed_at=datetime.now(UTC),
        )
    )
