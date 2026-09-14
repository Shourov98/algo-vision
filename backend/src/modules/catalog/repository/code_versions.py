"""AlgorithmCodeVersionRepository — persistence for code versions.

Two patterns coexist here:

- ``list(filters)`` follows the standard "list with filters +
  pagination" shape used everywhere else.
- ``get_current(algorithm_id, language)`` is the catalog
  hot-path: the detail endpoint asks "give me the current code
  for this algorithm in this language" and we return the row
  with ``is_current = TRUE``. The partial UNIQUE index
  ``uq_algorithm_code_versions_algo_lang_current`` makes this
  O(1) (B3.3).

Refs: PUKU_BACKEND_AGENT §9
Refs: DATABASE_DESIGN.md §1 (algorithm_code_versions), §5
      (indexes incl. partial UNIQUE on is_current)
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.catalog.filters import AlgorithmCodeVersionFilters
from src.modules.catalog.models import AlgorithmCodeVersion
from src.shared.pagination import Page


class AlgorithmCodeVersionRepositoryProtocol(Protocol):
    """Interface the catalog service depends on."""

    async def list(
        self, filters: AlgorithmCodeVersionFilters
    ) -> Page[AlgorithmCodeVersion]: ...
    async def get_by_id(self, version_id: UUID) -> AlgorithmCodeVersion | None: ...
    async def get_current(
        self, algorithm_id: UUID, language: str
    ) -> AlgorithmCodeVersion | None: ...


class AlgorithmCodeVersionRepository:
    """Async SQLAlchemy 2.x implementation."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(
        self, filters: AlgorithmCodeVersionFilters
    ) -> Page[AlgorithmCodeVersion]:
        stmt = select(AlgorithmCodeVersion)
        count_stmt = select(func.count()).select_from(AlgorithmCodeVersion)

        if filters.algorithm_id is not None:
            stmt = stmt.where(
                AlgorithmCodeVersion.algorithm_id == filters.algorithm_id
            )
            count_stmt = count_stmt.where(
                AlgorithmCodeVersion.algorithm_id == filters.algorithm_id
            )

        if filters.language:
            stmt = stmt.where(AlgorithmCodeVersion.language == filters.language)
            count_stmt = count_stmt.where(
                AlgorithmCodeVersion.language == filters.language
            )

        if filters.is_current is not None:
            stmt = stmt.where(
                AlgorithmCodeVersion.is_current == filters.is_current
            )
            count_stmt = count_stmt.where(
                AlgorithmCodeVersion.is_current == filters.is_current
            )

        if filters.version_min is not None:
            stmt = stmt.where(
                AlgorithmCodeVersion.version >= filters.version_min
            )
            count_stmt = count_stmt.where(
                AlgorithmCodeVersion.version >= filters.version_min
            )

        if filters.version_max is not None:
            stmt = stmt.where(
                AlgorithmCodeVersion.version <= filters.version_max
            )
            count_stmt = count_stmt.where(
                AlgorithmCodeVersion.version <= filters.version_max
            )

        sort_column = self._sort_column(filters.sort_by.value)
        order_by = (
            sort_column.asc()
            if filters.sort_order.value == "asc"
            else sort_column.desc()
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
        """Map public sort field name to SQLAlchemy column."""
        if name == "created_at":
            return AlgorithmCodeVersion.created_at
        if name == "language":
            return AlgorithmCodeVersion.language
        return AlgorithmCodeVersion.version

    async def get_by_id(
        self, version_id: UUID
    ) -> AlgorithmCodeVersion | None:
        stmt = select(AlgorithmCodeVersion).where(
            AlgorithmCodeVersion.id == version_id
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_current(
        self, algorithm_id: UUID, language: str
    ) -> AlgorithmCodeVersion | None:
        """Return the current code row for (algorithm, language).

        Uses the partial UNIQUE index
        ``uq_algorithm_code_versions_algo_lang_current`` for an
        O(1) lookup (DATABASE_DESIGN §5).
        """
        stmt = select(AlgorithmCodeVersion).where(
            AlgorithmCodeVersion.algorithm_id == algorithm_id,
            AlgorithmCodeVersion.language == language,
            AlgorithmCodeVersion.is_current.is_(True),
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()
