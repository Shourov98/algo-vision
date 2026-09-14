"""DataStructureRepository — persistence for ``data_structures``.

Same pattern as the smaller catalog repos: list with filters,
get_by_slug, get_by_id.

Refs: PUKU_BACKEND_AGENT §9
Refs: DATABASE_DESIGN.md §1 (data_structures), §5 (indexes)
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.catalog.filters import DataStructureFilters
from src.modules.catalog.models import DataStructure
from src.shared.pagination import Page


class DataStructureRepositoryProtocol(Protocol):
    """Interface the catalog service depends on."""

    async def list(
        self, filters: DataStructureFilters
    ) -> Page[DataStructure]: ...
    async def get_by_slug(self, slug: str) -> DataStructure | None: ...
    async def get_by_id(self, ds_id: UUID) -> DataStructure | None: ...


class DataStructureRepository:
    """Async SQLAlchemy 2.x implementation."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(
        self, filters: DataStructureFilters
    ) -> Page[DataStructure]:
        stmt = select(DataStructure)
        count_stmt = select(func.count()).select_from(DataStructure)

        if filters.search:
            pattern = f"%{filters.search}%"
            stmt = stmt.where(DataStructure.name.ilike(pattern))
            count_stmt = count_stmt.where(DataStructure.name.ilike(pattern))

        if filters.difficulty:
            stmt = stmt.where(DataStructure.difficulty == filters.difficulty)
            count_stmt = count_stmt.where(
                DataStructure.difficulty == filters.difficulty
            )

        sort_column = (
            DataStructure.name
            if filters.sort_by.value == "name"
            else DataStructure.slug
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

    async def get_by_slug(self, slug: str) -> DataStructure | None:
        stmt = select(DataStructure).where(DataStructure.slug == slug)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_by_id(self, ds_id: UUID) -> DataStructure | None:
        stmt = select(DataStructure).where(DataStructure.id == ds_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()
