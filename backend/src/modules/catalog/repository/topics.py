"""TopicRepository — persistence for ``topics``.

Same shape as CategoryRepository (single table, no joins) but
lives in its own file for the per-entity split pattern.

Refs: PUKU_BACKEND_AGENT §9
Refs: DATABASE_DESIGN.md §1 (topics), §5 (indexes)
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.catalog.filters import TopicFilters
from src.modules.catalog.models import Topic
from src.shared.pagination import Page


class TopicRepositoryProtocol(Protocol):
    """Interface the catalog service depends on."""

    async def list(self, filters: TopicFilters) -> Page[Topic]: ...
    async def get_by_slug(self, slug: str) -> Topic | None: ...
    async def get_by_id(self, topic_id: UUID) -> Topic | None: ...


class TopicRepository:
    """Async SQLAlchemy 2.x implementation."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, filters: TopicFilters) -> Page[Topic]:
        stmt = select(Topic)
        count_stmt = select(func.count()).select_from(Topic)

        if filters.search:
            pattern = f"%{filters.search}%"
            stmt = stmt.where(Topic.name.ilike(pattern))
            count_stmt = count_stmt.where(Topic.name.ilike(pattern))

        sort_column = (
            Topic.name
            if filters.sort_by.value == "name"
            else Topic.slug
        )
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

    async def get_by_slug(self, slug: str) -> Topic | None:
        stmt = select(Topic).where(Topic.slug == slug)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_by_id(self, topic_id: UUID) -> Topic | None:
        stmt = select(Topic).where(Topic.id == topic_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()
