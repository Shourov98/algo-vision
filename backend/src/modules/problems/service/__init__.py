"""Problems service - orchestrator for problems + companies reads.

Single responsibility
--------------------
The service is the only layer that knows how problems reads
flow:

1. Consume the filter objects (constructed by the router -
   service does NOT parse query strings).
2. Delegate persistence to the per-entity repository.
3. Translate ORM rows to public responses via the schema
   converters (in ``service/_converters.py``). ORM rows
   NEVER escape this layer (PUKU_BACKEND_AGENT §3.1).

What this class does NOT own
----------------------------
- HTTP concerns (status codes, request parsing). Routers do.
- SQL. Repositories do.
- Cache headers / ETag (B4.8 router concern).
- View-event side effects (problems API is staff-only in v1;
  analytics / recent-items events land in Phase 5 when there
  is a public read surface to track).

Why services depend on PROTOCOLS, not concrete repos
----------------------------------------------------
Liskov substitution: any class implementing
``ProblemRepositoryProtocol`` can stand in for the real
repo. Tests inject AsyncMock-backed fakes. The router
constructs the concrete class from the request-scoped
session via the FastAPI dependency in B4.8.

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 4 - Problems)
Refs: PUKU_BACKEND_AGENT.md §6, §10
Refs: AlgoVision_BACKEND.md §8
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from src.modules.problems.exceptions import CompanyNotFound, ProblemNotFound
from src.modules.problems.filters import (
    CompanyFilters,
    ProblemFilters,
)
from src.modules.problems.repository import (
    CompanyRepositoryProtocol,
    ProblemRepositoryProtocol,
)
from src.modules.problems.schemas import (
    CompanyResponse,
    ProblemDetailResponse,
    ProblemSummaryResponse,
)
from src.modules.problems.service._converters import (
    company_to_response,
    problem_to_detail,
    problem_to_summary,
)
from src.shared.events import EventDispatcherProtocol, ItemViewedEvent
from src.shared.pagination import Page

# Item-type discriminator for ItemViewedEvent (Phase 5).
# Plain string so cross-module handlers don't have to
# import a problems-side enum to switch on it (mirrors
# ALGOVISION_BACKEND_PLAN §6.7).
_ITEM_TYPE_PROBLEM = "problem"


class ProblemsServiceProtocol(Protocol):
    """Read-side problems + companies operations.

    Each method maps to one router endpoint in B4.8 and
    returns Pydantic response objects - ORM rows never
    escape the service layer.
    """

    async def list_problems(
        self, filters: ProblemFilters
    ) -> Page[ProblemSummaryResponse]: ...

    async def get_problem_by_slug(
        self,
        slug: str,
        user_id: UUID | None = None,
    ) -> ProblemDetailResponse: ...

    async def list_companies(
        self, filters: CompanyFilters
    ) -> Page[CompanyResponse]: ...

    async def get_company_by_slug(self, slug: str) -> CompanyResponse: ...


class ProblemsService:
    """Concrete problems + companies read service.

    Composition is constructor injection: the service is
    given the per-entity repositories. Tests pass
    AsyncMock-backed fakes; the production wiring (B4.8
    dependency factory) passes the concrete repos with the
    request-scoped session.

    Why one service, not two
    ------------------------
    The problems + companies domain is small and reads are
    uniformly shaped (list-with-filters OR get-by-slug).
    The two entities are joined through ``problem_companies``
    in the read path (problem detail embeds companies), so
    splitting into separate services would multiply
    constructor injection without adding testability. One
    class keeps the wiring simple; per-entity repositories
    preserve the boundary where it matters.
    """

    def __init__(
        self,
        problems_repo: ProblemRepositoryProtocol,
        companies_repo: CompanyRepositoryProtocol,
        events: EventDispatcherProtocol,
    ) -> None:
        self._problems = problems_repo
        self._companies = companies_repo
        self._events = events

    # ------------------------------------------------------------------
    # Problems
    # ------------------------------------------------------------------

    async def list_problems(
        self, filters: ProblemFilters
    ) -> Page[ProblemSummaryResponse]:
        page = await self._problems.list(filters)
        return Page(
            items=[problem_to_summary(p) for p in page.items],
            page=page.page,
            page_size=page.page_size,
            total=page.total,
        )

    async def get_problem_by_slug(
        self,
        slug: str,
        user_id: UUID | None = None,
    ) -> ProblemDetailResponse:
        """Return the problem with ``slug`` or raise 404.

        Embeds topic + company summaries via two extra repo
        calls. The two extra queries are bounded (one row
        per topic/company tagged on the problem) and
        ordered by slug, so the response is stable across
        calls. We do NOT issue a single JOIN + GROUP BY
        because the JSON shape requires nested arrays; the
        two-query approach is simpler and equally fast at
        this scale.

        Dispatches ``ItemViewedEvent`` with
        ``item_type="problem"`` when ``user_id`` is supplied
        so progress tracking can attribute the view
        consistently across catalog entities.
        """
        problem = await self._problems.get_by_slug(slug)
        if problem is None:
            raise ProblemNotFound(f"No problem with slug {slug!r}.")
        topics = await self._problems.list_topics(problem.id)
        companies = await self._problems.list_companies(problem.id)
        if user_id is not None:
            await self._events.dispatch(
                ItemViewedEvent(
                    user_id=user_id,
                    item_type=_ITEM_TYPE_PROBLEM,
                    item_id=problem.id,
                    viewed_at=datetime.now(UTC),
                )
            )
        return problem_to_detail(problem, topics, companies)

    # ------------------------------------------------------------------
    # Companies
    # ------------------------------------------------------------------

    async def list_companies(
        self, filters: CompanyFilters
    ) -> Page[CompanyResponse]:
        page = await self._companies.list(filters)
        return Page(
            items=[company_to_response(c) for c in page.items],
            page=page.page,
            page_size=page.page_size,
            total=page.total,
        )

    async def get_company_by_slug(self, slug: str) -> CompanyResponse:
        company = await self._companies.get_by_slug(slug)
        if company is None:
            raise CompanyNotFound(f"No company with slug {slug!r}.")
        return company_to_response(company)


__all__ = [
    "ProblemsService",
    "ProblemsServiceProtocol",
]
