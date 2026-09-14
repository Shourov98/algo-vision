"""Shared test fixtures for the catalog unit tests.

Lives next to the test files (rather than in the top-level
``conftest.py``) so only catalog tests pick it up. Pytest
discovers conftest.py files up the tree; we use the explicit
import pattern (``from ._catalog_conftest import ...``) so
the location is unambiguous.

Refs: PUKU_BACKEND_AGENT.md §13 (Test Conventions)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

from src.modules.catalog.models import (
    Algorithm,
    AlgorithmCodeVersion,
    Category,
    DataStructure,
    Topic,
)
from src.modules.catalog.service import CatalogService
from src.shared.pagination import Page


class FakeAlgorithmRepo:
    """AsyncMock-shaped fake that records calls."""

    def __init__(self) -> None:
        self.get_by_slug = AsyncMock(return_value=None)
        self.list = AsyncMock(return_value=[])


class FakeCategoryRepo:
    def __init__(self) -> None:
        self.get_by_slug = AsyncMock(return_value=None)
        self.list = AsyncMock(return_value=[])


class FakeTopicRepo:
    def __init__(self) -> None:
        self.get_by_slug = AsyncMock(return_value=None)
        self.list = AsyncMock(return_value=[])


class FakeCodeVersionRepo:
    def __init__(self) -> None:
        self.get_current = AsyncMock(return_value=None)
        self.list = AsyncMock(return_value=[])


class FakeDataStructureRepo:
    def __init__(self) -> None:
        self.get_by_slug = AsyncMock(return_value=None)
        self.list = AsyncMock(return_value=[])


class RecordingDispatcher:
    """Captures every dispatched event for assertion."""

    def __init__(self) -> None:
        self.events: list[Any] = []
        self.register = lambda *a, **kw: None

    async def dispatch(self, event: Any) -> None:
        self.events.append(event)


def empty_page(rows: list[Any]) -> Page[Any]:
    """Wrap ``rows`` in a Page[T] with default pagination."""
    return Page(items=rows, page=1, page_size=20, total=len(rows))


def make_service() -> tuple[
    CatalogService, dict[str, Any], RecordingDispatcher
]:
    """Return (service, repos_by_name, dispatcher) for direct poking."""
    algos = FakeAlgorithmRepo()
    cats = FakeCategoryRepo()
    topics = FakeTopicRepo()
    codes = FakeCodeVersionRepo()
    ds = FakeDataStructureRepo()
    dispatcher = RecordingDispatcher()
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


# Row builders — fully populated so schema conversion succeeds.
def make_category(slug: str = "sorting") -> Category:
    cat = Category(
        slug=slug,
        name=slug.title(),
        description=f"{slug} algorithms",
        sort_order=1,
    )
    cat.id = uuid4()
    cat.created_at = datetime.now(UTC)
    return cat


def make_topic(slug: str = "dp") -> Topic:
    topic = Topic(slug=slug, name=slug.title())
    topic.id = uuid4()
    return topic


def make_algorithm(
    *, slug: str = "quick-sort", is_published: bool = True
) -> Algorithm:
    alg = Algorithm(
        slug=slug,
        name=slug.replace("-", " ").title(),
        category_id=uuid4(),
        description="An algorithm.",
        difficulty="medium",
        visualization_type="array",
        is_published=is_published,
    )
    alg.id = uuid4()
    alg.created_at = datetime.now(UTC)
    alg.updated_at = datetime.now(UTC)
    return alg


def make_data_structure(slug: str = "stack") -> DataStructure:
    ds = DataStructure(
        slug=slug,
        name=slug.title(),
        description="A data structure.",
        difficulty="easy",
        visualization_type="linear",
    )
    ds.id = uuid4()
    ds.created_at = datetime.now(UTC)
    return ds


def make_code_version(
    algorithm_id: Any, language: str = "python"
) -> AlgorithmCodeVersion:
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


__all__ = [
    "FakeAlgorithmRepo",
    "FakeCategoryRepo",
    "FakeCodeVersionRepo",
    "FakeDataStructureRepo",
    "FakeTopicRepo",
    "RecordingDispatcher",
    "empty_page",
    "make_algorithm",
    "make_category",
    "make_code_version",
    "make_data_structure",
    "make_service",
    "make_topic",
]
