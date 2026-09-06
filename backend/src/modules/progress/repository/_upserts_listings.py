"""Upserts + paginated listings for the progress tables.

This file owns the INSERT/UPDATE/SELECT-LIMIT paths on
``user_algorithm_progress`` and ``user_problem_progress``.
The overview aggregation + recents live in
``_overview_recents.py`` — split because the two halves of
the repository have very different query shapes (mutations
+ LIMIT/OFFSET vs GROUP BY + append-log).

ON CONFLICT idempotency
-----------------------
Both upserts use Postgres ``ON CONFLICT (…) DO UPDATE``:

- ``status``, ``completion_percentage``, ``completed_at``
  come from the new payload (client-driven).
- ``first_viewed_at`` is preserved via ``GREATEST(...)``
  (the original first-view timestamp wins against a later
  INSERT attempt that omits it).
- ``last_viewed_at = now()`` (refresh on every re-mark).
- ``total_sessions`` is incremented by 1 on conflict; the
  INSERT path uses the server default of 1.
- ``completed_at`` is set when the new status is
  'completed' and cleared otherwise (advanced status
  transitions are out of scope in Phase 5).

Refs: ALGOVISION_BACKEND_PLAN.md §5 (Phase 5 — B5.5)
Refs: AlgoVision_BACKEND.md §10 (Repository Conventions)
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.progress.filters import (
    AlgorithmProgressFilters,
    ProblemProgressFilters,
)
from src.modules.progress.models import (
    UserAlgorithmProgress,
    UserProblemProgress,
)
from src.shared.pagination import Page


class ProgressUpsertsAndListings:
    """Upserts + paginated listings for the progress tables.

    Mixed into ``ProgressRepository``. Split into a
    separate module so the file stays under the 400-line
    cap (``GitWorktree §12.4``).
    """

    _session: AsyncSession

    # ------------------------------------------------------------------
    # Upserts
    # ------------------------------------------------------------------

    async def upsert_algorithm_progress(
        self,
        user_id,
        algorithm_id,
        status: str,
        completion_percentage: int,
    ) -> UserAlgorithmProgress:
        """Idempotent upsert of one algorithm-progress row."""
        now = datetime.now(UTC)
        completed_at = now if status == "completed" else None

        stmt = (
            pg_insert(UserAlgorithmProgress)
            .values(
                user_id=user_id,
                algorithm_id=algorithm_id,
                status=status,
                completion_percentage=completion_percentage,
                last_viewed_at=now,
                completed_at=completed_at,
                # total_sessions + first_viewed_at use the
                # server defaults on INSERT.
            )
            .on_conflict_do_update(
                index_elements=[
                    UserAlgorithmProgress.user_id,
                    UserAlgorithmProgress.algorithm_id,
                ],
                set_={
                    "status": status,
                    "completion_percentage": completion_percentage,
                    "last_viewed_at": now,
                    "completed_at": completed_at,
                    "total_sessions": (
                        UserAlgorithmProgress.total_sessions + 1
                    ),
                    # Preserve the original first-view timestamp.
                    "first_viewed_at": func.greatest(
                        UserAlgorithmProgress.first_viewed_at,
                        UserAlgorithmProgress.first_viewed_at,
                    ),
                },
            )
            .returning(UserAlgorithmProgress)
        )
        row = (await self._session.execute(stmt)).scalar_one()
        return row

    async def upsert_problem_progress(
        self,
        user_id,
        problem_id,
        status: str,
        attempts: int,
    ) -> UserProblemProgress:
        """Mirror the algorithm upsert; no completion_percentage."""
        now = datetime.now(UTC)
        completed_at = now if status == "completed" else None

        stmt = (
            pg_insert(UserProblemProgress)
            .values(
                user_id=user_id,
                problem_id=problem_id,
                status=status,
                attempts=attempts,
                last_viewed_at=now,
                completed_at=completed_at,
            )
            .on_conflict_do_update(
                index_elements=[
                    UserProblemProgress.user_id,
                    UserProblemProgress.problem_id,
                ],
                set_={
                    "status": status,
                    "attempts": attempts,
                    "last_viewed_at": now,
                    "completed_at": completed_at,
                    "first_viewed_at": func.greatest(
                        UserProblemProgress.first_viewed_at,
                        UserProblemProgress.first_viewed_at,
                    ),
                },
            )
            .returning(UserProblemProgress)
        )
        row = (await self._session.execute(stmt)).scalar_one()
        return row

    # ------------------------------------------------------------------
    # Listings
    # ------------------------------------------------------------------

    async def list_algorithm_progress(
        self,
        user_id,
        filters: AlgorithmProgressFilters,
    ) -> Page[UserAlgorithmProgress]:
        """List the caller's progress rows, filtered."""
        stmt = select(UserAlgorithmProgress).where(
            UserAlgorithmProgress.user_id == user_id
        )
        count_stmt = select(func.count(UserAlgorithmProgress.user_id)).where(
            UserAlgorithmProgress.user_id == user_id
        )

        if filters.status:
            stmt = stmt.where(UserAlgorithmProgress.status == filters.status)
            count_stmt = count_stmt.where(
                UserAlgorithmProgress.status == filters.status
            )

        sort_column = self._sort_column_alg(filters.sort_by.value)
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

    async def list_problem_progress(
        self,
        user_id,
        filters: ProblemProgressFilters,
    ) -> Page[UserProblemProgress]:
        """Mirror algorithm listing for problems."""
        stmt = select(UserProblemProgress).where(
            UserProblemProgress.user_id == user_id
        )
        count_stmt = select(func.count(UserProblemProgress.user_id)).where(
            UserProblemProgress.user_id == user_id
        )

        if filters.status:
            stmt = stmt.where(UserProblemProgress.status == filters.status)
            count_stmt = count_stmt.where(
                UserProblemProgress.status == filters.status
            )

        sort_column = self._sort_column_prob(filters.sort_by.value)
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

    # ------------------------------------------------------------------
    # Sort field dispatch (static, no per-instance state)
    # ------------------------------------------------------------------

    @staticmethod
    def _sort_column_alg(name: str):
        """Map public sort field to SQLAlchemy column on algo table."""
        if name == "first_viewed_at":
            return UserAlgorithmProgress.first_viewed_at
        if name == "completed_at":
            return UserAlgorithmProgress.completed_at
        return UserAlgorithmProgress.last_viewed_at

    @staticmethod
    def _sort_column_prob(name: str):
        """Map public sort field to SQLAlchemy column on problem table."""
        if name == "first_viewed_at":
            return UserProblemProgress.first_viewed_at
        if name == "completed_at":
            return UserProblemProgress.completed_at
        return UserProblemProgress.last_viewed_at


__all__ = ["ProgressUpsertsAndListings"]
