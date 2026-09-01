"""Shared test fixtures for the problems unit tests.

Lives next to the test files (rather than in the top-level
``conftest.py``) so only problems tests pick it up. Mirrors
the ``_catalog_conftest`` pattern.

Refs: PUKU_BACKEND_AGENT.md §13 (Test Conventions)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

from src.modules.catalog.models import Topic
from src.modules.problems.models import Company, Problem
from src.modules.problems.service import ProblemsService
from src.shared.pagination import Page


class FakeProblemRepo:
    """AsyncMock-shaped fake that records calls."""

    def __init__(self) -> None:
        self.list = AsyncMock(return_value=[])
        self.get_by_slug = AsyncMock(return_value=None)
        self.get_by_id = AsyncMock(return_value=None)
        self.list_topics = AsyncMock(return_value=[])
        self.list_companies = AsyncMock(return_value=[])


class FakeCompanyRepo:
    def __init__(self) -> None:
        self.list = AsyncMock(return_value=[])
        self.get_by_slug = AsyncMock(return_value=None)
        self.get_by_id = AsyncMock(return_value=None)


def empty_page(rows: list[Any]) -> Page[Any]:
    """Wrap ``rows`` in a Page[T] with default pagination."""
    return Page(items=rows, page=1, page_size=20, total=len(rows))


def make_service() -> tuple[
    ProblemsService, dict[str, Any]
]:
    """Return (service, repos_by_name) for direct poking."""
    problems = FakeProblemRepo()
    companies = FakeCompanyRepo()
    svc = ProblemsService(
        problems_repo=problems,  # type: ignore[arg-type]
        companies_repo=companies,  # type: ignore[arg-type]
    )
    return svc, {"problems": problems, "companies": companies}


# Row builders -- fully populated so schema conversion succeeds.
def make_problem(
    *,
    slug: str = "two-sum",
    difficulty: str = "easy",
    visualization_available: bool = True,
) -> Problem:
    p = Problem(
        slug=slug,
        title=slug.replace("-", " ").title(),
        description=f"The {slug} problem.",
        difficulty=difficulty,
        solution_explanation="O(n) solution.",
        external_reference="LC-1",
        visualization_available=visualization_available,
    )
    p.id = uuid4()
    p.created_at = datetime.now(UTC)
    p.updated_at = datetime.now(UTC)
    return p


def make_topic(slug: str = "hashing") -> Topic:
    t = Topic(slug=slug, name=slug.title())
    t.id = uuid4()
    return t


def make_company(slug: str = "google") -> Company:
    c = Company(slug=slug, name=slug.title())
    c.id = uuid4()
    return c


__all__ = [
    "FakeCompanyRepo",
    "FakeProblemRepo",
    "empty_page",
    "make_company",
    "make_problem",
    "make_service",
    "make_topic",
]
