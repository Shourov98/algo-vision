"""ProblemsService — unit tests for the read orchestration.

Mirrors the catalog service tests: AsyncMock-backed
repos drive the service through happy paths, miss paths,
and embed orchestration (problem detail embeds topics +
companies).

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 4 - B4.7)
Refs: PUKU_BACKEND_AGENT.md §13
"""

from __future__ import annotations

from src.modules.problems.exceptions import (
    CompanyNotFound,
    ProblemNotFound,
)
from src.modules.problems.schemas import (
    CompanyResponse,
    ProblemDetailResponse,
    ProblemSummaryResponse,
)
from src.shared.pagination import Page

from tests.unit._problems_conftest import (
    empty_page,
    make_company,
    make_problem,
    make_service,
    make_topic,
)

# ---------------------------------------------------------------------------
# list_problems
# ---------------------------------------------------------------------------


async def test_list_problems_delegates_to_repo() -> None:
    svc, repos = make_service()
    repos["problems"].list.return_value = empty_page(
        [make_problem(slug="two-sum")]
    )
    page = await svc.list_problems(filters=object())  # type: ignore[arg-type]
    repos["problems"].list.assert_awaited_once()
    assert len(page.items) == 1
    assert isinstance(page.items[0], ProblemSummaryResponse)
    assert page.items[0].slug == "two-sum"


async def test_list_problems_returns_empty_page_when_repo_is_empty() -> None:
    svc, repos = make_service()
    repos["problems"].list.return_value = empty_page([])
    page = await svc.list_problems(filters=object())  # type: ignore[arg-type]
    assert page.items == []
    assert page.total == 0


async def test_list_problems_preserves_pagination_envelope() -> None:
    svc, repos = make_service()
    repos["problems"].list.return_value = Page(
        items=[make_problem()],
        page=2,
        page_size=5,
        total=42,
    )
    page = await svc.list_problems(filters=object())  # type: ignore[arg-type]
    assert page.page == 2
    assert page.page_size == 5
    assert page.total == 42


# ---------------------------------------------------------------------------
# get_problem_by_slug — happy path
# ---------------------------------------------------------------------------


async def test_get_problem_by_slug_returns_detail_when_present() -> None:
    svc, repos = make_service()
    repos["problems"].get_by_slug.return_value = make_problem()
    repos["problems"].list_topics.return_value = [
        make_topic("hashing"),
    ]
    repos["problems"].list_companies.return_value = [
        make_company("google"),
        make_company("amazon"),
    ]
    result = await svc.get_problem_by_slug("two-sum")
    assert isinstance(result, ProblemDetailResponse)
    assert result.slug == "two-sum"


async def test_get_problem_by_slug_embeds_topics_and_companies() -> None:
    """The detail payload embeds topic + company summaries."""
    svc, repos = make_service()
    repos["problems"].get_by_slug.return_value = make_problem()
    repos["problems"].list_topics.return_value = [
        make_topic("hashing"),
        make_topic("heap"),
    ]
    repos["problems"].list_companies.return_value = [
        make_company("google"),
        make_company("amazon"),
        make_company("meta"),
    ]
    result = await svc.get_problem_by_slug("two-sum")
    assert [t.slug for t in result.topics] == ["hashing", "heap"]
    assert [c.slug for c in result.companies] == [
        "google",
        "amazon",
        "meta",
    ]


async def test_get_problem_by_slug_returns_empty_embeds_when_unjoined() -> None:
    """A problem with no topic / company joins still returns a
    valid detail with empty embed lists."""
    svc, repos = make_service()
    repos["problems"].get_by_slug.return_value = make_problem()
    repos["problems"].list_topics.return_value = []
    repos["problems"].list_companies.return_value = []
    result = await svc.get_problem_by_slug("two-sum")
    assert result.topics == []
    assert result.companies == []


async def test_get_problem_by_slug_calls_list_topics_and_list_companies() -> None:
    """The detail endpoint triggers both embed lookups."""
    svc, repos = make_service()
    problem = make_problem()
    repos["problems"].get_by_slug.return_value = problem
    await svc.get_problem_by_slug("two-sum")
    repos["problems"].list_topics.assert_awaited_once_with(problem.id)
    repos["problems"].list_companies.assert_awaited_once_with(problem.id)


# ---------------------------------------------------------------------------
# get_problem_by_slug — miss
# ---------------------------------------------------------------------------


async def test_get_problem_by_slug_raises_when_missing() -> None:
    svc, repos = make_service()
    repos["problems"].get_by_slug.return_value = None
    import pytest

    with pytest.raises(ProblemNotFound):
        await svc.get_problem_by_slug("nope")


async def test_get_problem_by_slug_does_not_call_embeds_when_missing() -> None:
    """404 short-circuits before touching the embed queries."""
    from contextlib import suppress

    svc, repos = make_service()
    repos["problems"].get_by_slug.return_value = None
    with suppress(ProblemNotFound):
        await svc.get_problem_by_slug("nope")
    repos["problems"].list_topics.assert_not_called()
    repos["problems"].list_companies.assert_not_called()


# ---------------------------------------------------------------------------
# list_companies
# ---------------------------------------------------------------------------


async def test_list_companies_delegates_to_repo() -> None:
    svc, repos = make_service()
    repos["companies"].list.return_value = empty_page(
        [make_company("google")]
    )
    page = await svc.list_companies(filters=object())  # type: ignore[arg-type]
    repos["companies"].list.assert_awaited_once()
    assert len(page.items) == 1
    assert isinstance(page.items[0], CompanyResponse)


async def test_list_companies_returns_empty_page_when_repo_is_empty() -> None:
    svc, repos = make_service()
    repos["companies"].list.return_value = empty_page([])
    page = await svc.list_companies(filters=object())  # type: ignore[arg-type]
    assert page.items == []


# ---------------------------------------------------------------------------
# get_company_by_slug
# ---------------------------------------------------------------------------


async def test_get_company_by_slug_returns_response_when_present() -> None:
    svc, repos = make_service()
    repos["companies"].get_by_slug.return_value = make_company("google")
    result = await svc.get_company_by_slug("google")
    assert isinstance(result, CompanyResponse)
    assert result.slug == "google"


async def test_get_company_by_slug_raises_when_missing() -> None:
    svc, repos = make_service()
    repos["companies"].get_by_slug.return_value = None
    import pytest

    with pytest.raises(CompanyNotFound):
        await svc.get_company_by_slug("nope")


# ---------------------------------------------------------------------------
# Independence — problems list does not touch companies repo
# ---------------------------------------------------------------------------


async def test_list_problems_does_not_touch_companies_repo() -> None:
    svc, repos = make_service()
    repos["problems"].list.return_value = empty_page([])
    await svc.list_problems(filters=object())  # type: ignore[arg-type]
    repos["companies"].list.assert_not_called()
    repos["companies"].get_by_slug.assert_not_called()
