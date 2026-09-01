"""ProblemRepository — persistence for ``problems``.

The largest problems-module repository: filters on
difficulty, topic slug, company slug, and visualization
flag. Joins across modules (``Topic`` from catalog,
``ProblemTopic``, ``ProblemCompany``) mirror the algorithm
repository's pattern (B3.5).

Why DISTINCT for topic / company joins
--------------------------------------
``problem_topics`` / ``problem_companies`` joins multiply
rows: a problem tagged with three topics appears three
times. DISTINCT keeps the count honest and the pagination
math correct. Mirrors the catalog ``AlgorithmRepository``
pattern.

Why ``visualization_available`` is a filter
-------------------------------------------
The interview-preparation surface splits into two routes
(B4.4 schema docstring). The frontend filter
"only visualizable problems" lets staff preview the
visualization flow without scrolling through editor-only
items. The flag is BOOLEAN NOT NULL, so a tri-state
filter (``True`` / ``False`` / ``None``) maps cleanly to
"include only true" / "include only false" / "no filter".

Why ``is_published`` is NOT a filter (yet)
------------------------------------------
The problems API is staff-only in v1
(ALGOVISION_BACKEND_PLAN §4) — there is no public read
endpoint, so the public/private dichotomy doesn't exist.
We don't synthesize the column until a public surface
exists (see ``models/problem.py`` docstring).

Refs: PUKU_BACKEND_AGENT §9
Refs: DATABASE_DESIGN.md §1 (problems, problem_topics,
       problem_companies), §5 (indexes)
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.catalog.models import Topic
from src.modules.problems.filters import ProblemFilters
from src.modules.problems.models import (
    Company,
    Problem,
    ProblemCompany,
    ProblemTopic,
)
from src.shared.pagination import Page


class ProblemRepositoryProtocol(Protocol):
    """Interface the problems service depends on.

    Liskov substitution: any class implementing this contract
    can stand in for the real repository in unit tests.
    """

    async def list(self, filters: ProblemFilters) -> Page[Problem]: ...
    async def get_by_slug(self, slug: str) -> Problem | None: ...
    async def get_by_id(self, problem_id: UUID) -> Problem | None: ...
    async def list_topics(self, problem_id: UUID) -> Sequence[Topic]: ...
    async def list_companies(self, problem_id: UUID) -> Sequence[Company]: ...


class ProblemRepository:
    """Async SQLAlchemy 2.x implementation."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, filters: ProblemFilters) -> Page[Problem]:
        """List problems matching ``filters``."""
        stmt = select(Problem)
        count_stmt = select(func.count(distinct(Problem.id))).select_from(
            Problem
        )

        if filters.search:
            pattern = f"%{filters.search}%"
            stmt = stmt.where(Problem.title.ilike(pattern))
            count_stmt = count_stmt.where(Problem.title.ilike(pattern))

        if filters.difficulty:
            stmt = stmt.where(Problem.difficulty == filters.difficulty)
            count_stmt = count_stmt.where(
                Problem.difficulty == filters.difficulty
            )

        if filters.visualization_available is not None:
            stmt = stmt.where(
                Problem.visualization_available
                == filters.visualization_available
            )
            count_stmt = count_stmt.where(
                Problem.visualization_available
                == filters.visualization_available
            )

        if filters.topic:
            # Subquery: Problem.id ∈ ProblemTopic rows where
            # Topic.slug = requested. The subquery approach is
            # used (not a JOIN) so the count_stmt can also
            # reuse it without re-joining.
            topic_subq = (
                select(ProblemTopic.problem_id)
                .join(Topic, Topic.id == ProblemTopic.topic_id)
                .where(Topic.slug == filters.topic)
            )
            stmt = stmt.where(Problem.id.in_(topic_subq))
            count_stmt = count_stmt.where(Problem.id.in_(topic_subq))

        if filters.company:
            company_subq = (
                select(ProblemCompany.problem_id)
                .join(Company, Company.id == ProblemCompany.company_id)
                .where(Company.slug == filters.company)
            )
            stmt = stmt.where(Problem.id.in_(company_subq))
            count_stmt = count_stmt.where(Problem.id.in_(company_subq))

        # Sort
        sort_column = self._sort_column(filters.sort_by.value)
        order_by = (
            sort_column.desc()
            if filters.sort_order.value == "desc"
            else sort_column.asc()
        )
        stmt = stmt.order_by(order_by)
        stmt = stmt.limit(filters.pagination.limit).offset(
            filters.pagination.offset
        )

        rows = (await self._session.execute(stmt)).scalars().all()
        total = (await self._session.execute(count_stmt)).scalar_one()

        return Page(
            items=list(rows),
            page=filters.pagination.page,
            page_size=filters.pagination.page_size,
            total=total,
        )

    @staticmethod
    def _sort_column(name: str):
        """Map the public sort field name to a SQLAlchemy column.

        Defined as a static method so it can be tested in
        isolation without instantiating the repository.
        """
        if name == "created_at":
            return Problem.created_at
        return Problem.updated_at  # default

    async def get_by_slug(self, slug: str) -> Problem | None:
        """Lookup by slug — UNIQUE-indexed per DATABASE_DESIGN §5."""
        stmt = select(Problem).where(Problem.slug == slug)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_by_id(self, problem_id: UUID) -> Problem | None:
        stmt = select(Problem).where(Problem.id == problem_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_topics(self, problem_id: UUID) -> Sequence[Topic]:
        """Topics tagged on this problem, ordered by slug.

        Used to build the embedded ``TopicSummary`` list on
        the detail response. Slug ordering keeps the
        response stable across calls.
        """
        stmt = (
            select(Topic)
            .join(ProblemTopic, ProblemTopic.topic_id == Topic.id)
            .where(ProblemTopic.problem_id == problem_id)
            .order_by(Topic.slug)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return list(rows)

    async def list_companies(self, problem_id: UUID) -> Sequence[Company]:
        """Companies that ask this problem, ordered by slug.

        Used to build the embedded ``CompanySummary`` list on
        the detail response. Slug ordering keeps the
        response stable across calls.
        """
        stmt = (
            select(Company)
            .join(ProblemCompany, ProblemCompany.company_id == Company.id)
            .where(ProblemCompany.problem_id == problem_id)
            .order_by(Company.slug)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return list(rows)
