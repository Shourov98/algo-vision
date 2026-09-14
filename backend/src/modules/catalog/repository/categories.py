"""CategoryRepository — persistence for ``algorithm_categories``.

The smallest repository in the module: a single table, no joins,
a handful of filters. The patterns here are reused (mostly
verbatim) by the larger repos for topics and data_structures.

Why ``selectinload`` is not used here
-------------------------------------
``Category`` has no relationships to eager-load. There is
nothing to optimize.

Refs: PUKU_BACKEND_AGENT §9
Refs: DATABASE_DESIGN.md §1 (algorithm_categories), §5 (indexes)
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.catalog.filters import CategoryFilters
from src.modules.catalog.models import Category
from src.shared.pagination import Page


class CategoryRepositoryProtocol(Protocol):
    """Interface the catalog service depends on.

    Liskov substitution: any class implementing this contract
    can stand in for the real repository in unit tests.
    """

    async def list(self, filters: CategoryFilters) -> Page[Category]: ...
    async def get_by_slug(self, slug: str) -> Category | None: ...
    async def get_by_id(self, category_id: UUID) -> Category | None: ...


class CategoryRepository:
    """Async SQLAlchemy 2.x implementation."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, filters: CategoryFilters) -> Page[Category]:
        """List categories matching ``filters``.

        Sort mapping lives in the repository (not the service)
        because it's the layer that owns the SQL — keeping the
        mapping close to the column names makes the contract
        auditable.
        """
        stmt = select(Category)
        count_stmt = select(func.count()).select_from(Category)

        if filters.search:
            pattern = f"%{filters.search}%"
            stmt = stmt.where(Category.name.ilike(pattern))
            count_stmt = count_stmt.where(Category.name.ilike(pattern))

        sort_column = (
            Category.sort_order
            if filters.sort_by.value == "sort_order"
            else Category.name
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

    async def get_by_slug(self, slug: str) -> Category | None:
        """Lookup by slug — UNIQUE-indexed per DATABASE_DESIGN §5."""
        stmt = select(Category).where(Category.slug == slug)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_by_id(self, category_id: UUID) -> Category | None:
        stmt = select(Category).where(Category.id == category_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()
