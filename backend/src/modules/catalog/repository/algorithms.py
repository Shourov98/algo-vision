"""AlgorithmRepository — persistence for ``algorithms``.

The most complex catalog repository: it filters on category slug
AND topic slug via joins, and supports the documented published-
algorithms query (DATABASE_DESIGN §8.1 Q1).

Why the topic-filter join is here, not in the service
-----------------------------------------------------
The service layer is HTTP-agnostic and ORM-agnostic. The join
is an implementation detail of "given a topic slug, which
algorithms?" — the service just hands the repository a
``TopicFilters``-shaped value (in our case ``algorithm.topic``
field) and the repository translates to SQL. Putting the join
in the service would force the service to know about the
``algorithm_topics`` table — coupling it to a schema detail.

Why DISTINCT for the topic-filtered query
-----------------------------------------
The ``algorithm_topics`` join multiplies rows: an algorithm
tagged with three topics appears three times. DISTINCT keeps
the count honest and the pagination math correct.

Refs: PUKU_BACKEND_AGENT §9
Refs: DATABASE_DESIGN.md §1 (algorithms), §5 (indexes), §8.1
      (Q1: published-algorithms query)
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.catalog.filters import AlgorithmFilters
from src.modules.catalog.models import Algorithm, Topic, algorithm_topics
from src.shared.pagination import Page


class AlgorithmRepositoryProtocol(Protocol):
    """Interface the catalog service depends on."""

    async def list(self, filters: AlgorithmFilters) -> Page[Algorithm]: ...
    async def get_by_slug(self, slug: str) -> Algorithm | None: ...
    async def get_by_id(self, algorithm_id: UUID) -> Algorithm | None: ...


class AlgorithmRepository:
    """Async SQLAlchemy 2.x implementation."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, filters: AlgorithmFilters) -> Page[Algorithm]:
        stmt = select(Algorithm).where(
            Algorithm.is_published == filters.is_published
        )
        count_stmt = (
            select(func.count(distinct(Algorithm.id)))
            .select_from(Algorithm)
            .where(Algorithm.is_published == filters.is_published)
        )

        if filters.search:
            pattern = f"%{filters.search}%"
            stmt = stmt.where(Algorithm.name.ilike(pattern))
            count_stmt = count_stmt.where(Algorithm.name.ilike(pattern))

        if filters.difficulty:
            stmt = stmt.where(Algorithm.difficulty == filters.difficulty)
            count_stmt = count_stmt.where(
                Algorithm.difficulty == filters.difficulty
            )

        if filters.category:
            # Subquery: algorithm.category_id ∈ Category ids with
            # the requested slug. IN is friendlier to the
            # planner than a JOIN when the categories table is
            # tiny.
            from src.modules.catalog.models import Category

            cat_subq = select(Category.id).where(
                Category.slug == filters.category
            )
            stmt = stmt.where(Algorithm.category_id.in_(cat_subq))
            count_stmt = count_stmt.where(
                Algorithm.category_id.in_(cat_subq)
            )

        if filters.topic:
            # JOIN to algorithm_topics + topics. DISTINCT avoids
            # duplicate algorithm rows when an algorithm has
            # multiple topic tags.
            stmt = stmt.join(
                algorithm_topics, algorithm_topics.c.algorithm_id == Algorithm.id
            ).join(
                Topic, Topic.id == algorithm_topics.c.topic_id
            ).where(
                Topic.slug == filters.topic
            )
            count_stmt = count_stmt.join(
                algorithm_topics, algorithm_topics.c.algorithm_id == Algorithm.id
            ).join(
                Topic, Topic.id == algorithm_topics.c.topic_id
            ).where(
                Topic.slug == filters.topic
            )
            stmt = stmt.distinct()
            count_stmt = count_stmt.distinct()

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
        if name == "updated_at":
            return Algorithm.updated_at
        if name == "created_at":
            return Algorithm.created_at
        return Algorithm.name

    async def get_by_slug(self, slug: str) -> Algorithm | None:
        stmt = select(Algorithm).where(Algorithm.slug == slug)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_by_id(self, algorithm_id: UUID) -> Algorithm | None:
        stmt = select(Algorithm).where(Algorithm.id == algorithm_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()
