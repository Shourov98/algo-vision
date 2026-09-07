"""CompanyRepository - persistence for ``companies``.

The smallest problems-module repository: a single table, no
joins, a handful of filters. Mirrors the
``CategoryRepository`` (catalog) pattern.

Why ``selectinload`` is not used here
-------------------------------------
``Company`` has no relationships to eager-load. There is
nothing to optimize.

Refs: PUKU_BACKEND_AGENT §9
Refs: DATABASE_DESIGN.md §1 (companies), §5 (indexes)
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.problems.filters import CompanyFilters
from src.modules.problems.models import Company
from src.shared.pagination import Page


class CompanyRepositoryProtocol(Protocol):
    """Interface the problems service depends on.

    Liskov substitution: any class implementing this contract
    can stand in for the real repository in unit tests.
    """

    async def list(self, filters: CompanyFilters) -> Page[Company]: ...
    async def get_by_slug(self, slug: str) -> Company | None: ...
    async def get_by_id(self, company_id: UUID) -> Company | None: ...


class CompanyRepository:
    """Async SQLAlchemy 2.x implementation."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, filters: CompanyFilters) -> Page[Company]:
        """List companies matching ``filters``.

        Sort mapping lives in the repository (not the service)
        because it's the layer that owns the SQL - keeping the
        mapping close to the column names makes the contract
        auditable.
        """
        stmt = select(Company)
        count_stmt = select(func.count()).select_from(Company)

        if filters.search:
            pattern = f"%{filters.search}%"
            stmt = stmt.where(Company.name.ilike(pattern))
            count_stmt = count_stmt.where(Company.name.ilike(pattern))

        sort_column = (
            Company.slug
            if filters.sort_by.value == "slug"
            else Company.name
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

    async def get_by_slug(self, slug: str) -> Company | None:
        """Lookup by slug - UNIQUE-indexed per DATABASE_DESIGN §5."""
        stmt = select(Company).where(Company.slug == slug)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_by_id(self, company_id: UUID) -> Company | None:
        stmt = select(Company).where(Company.id == company_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()
