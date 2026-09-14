"""Overview aggregation + recent-items append-log.

Two operations that don't fit naturally next to the
upserts/listing in ``_upserts_listings.py``:

- ``get_overview`` : two parallel ``GROUP BY status``
  aggregations (one per table) producing the per-entity
  completed / in_progress / total counts. The service
  turns the result into ``ProgressOverviewResponse``
  (B5.4 schema).

- ``record_view`` / ``list_recents`` : the append-log on
  ``user_recent_items``. The cap-to-50 enforcement is a
  second statement after the INSERT — DELETE the rows
  that fall outside the newest 50. Doing it in SQL keeps
  the cost bounded by a single ORDER BY indexed scan
  (the ``(user_id, viewed_at DESC)`` index from B5.3).

Why no UPSERT in record_view
----------------------------
Re-viewing the same item is a fresh event with its own
``viewed_at`` timestamp. The DB has no UNIQUE on
(user_id, item_id, item_type) — duplicates on those
three columns are legitimate ("3 separate views today").
Surrogate PK with separate append-only semantics is the
simpler design.

Refs: ALGOVISION_BACKEND_PLAN.md §5 (Phase 5 — B5.5),
       §6.7 (ItemViewedEvent consumer)
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, desc, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.progress.models import (
    UserAlgorithmProgress,
    UserProblemProgress,
    UserRecentItem,
)
from src.modules.progress.repository.protocol import RECENT_ITEMS_CAP


class ProgressOverviewAndRecents:
    """Overview aggregation + recent-items append-log.

    Mixed into ``ProgressRepository``. Split into a
    separate module so the file stays under the 400-line
    cap.
    """

    _session: AsyncSession

    # ------------------------------------------------------------------
    # Overview
    # ------------------------------------------------------------------

    async def get_overview(self, user_id: UUID) -> dict[str, int]:
        """Return completed/in_progress/total counts for both entities.

        Two parallel aggregations — one per table — each a
        single GROUP BY status query. Keeping this in the
        repository (not the service) keeps the SQL localised
        and lets the dashboard integration test run a known
        set of expected aggregates against seeded data.
        """
        alg_stmt = select(
            UserAlgorithmProgress.status,
            func.count(UserAlgorithmProgress.user_id),
        ).where(UserAlgorithmProgress.user_id == user_id)
        alg_stmt = alg_stmt.group_by(UserAlgorithmProgress.status)
        alg_rows = (await self._session.execute(alg_stmt)).all()

        prob_stmt = select(
            UserProblemProgress.status,
            func.count(UserProblemProgress.user_id),
        ).where(UserProblemProgress.user_id == user_id)
        prob_stmt = prob_stmt.group_by(UserProblemProgress.status)
        prob_rows = (await self._session.execute(prob_stmt)).all()

        result: dict[str, int] = {
            "algorithms_completed": 0,
            "algorithms_in_progress": 0,
            "algorithms_total": 0,
            "problems_completed": 0,
            "problems_in_progress": 0,
            "problems_total": 0,
        }
        for status_val, count in alg_rows:
            result["algorithms_total"] += count
            if status_val == "completed":
                result["algorithms_completed"] += count
            elif status_val == "in_progress":
                result["algorithms_in_progress"] += count
        for status_val, count in prob_rows:
            result["problems_total"] += count
            if status_val == "completed":
                result["problems_completed"] += count
            elif status_val == "in_progress":
                result["problems_in_progress"] += count
        return result

    # ------------------------------------------------------------------
    # Recent items
    # ------------------------------------------------------------------

    async def record_view(
        self,
        user_id: UUID,
        item_type: str,
        item_id: UUID,
    ) -> None:
        """Append a view event + trim older rows to the cap."""
        # INSERT
        insert_stmt = pg_insert(UserRecentItem).values(
            user_id=user_id,
            item_type=item_type,
            item_id=item_id,
        )
        await self._session.execute(insert_stmt)

        # DELETE anything past the cap. ORDER BY viewed_at
        # DESC, LIMIT (count - 50) OFFSET 50. We use a
        # subquery + IN because Postgres doesn't allow
        # ORDER BY/LIMIT directly in DELETE in all versions.
        over_cap_subq = (
            select(UserRecentItem.id)
            .where(UserRecentItem.user_id == user_id)
            .order_by(desc(UserRecentItem.viewed_at))
            .offset(RECENT_ITEMS_CAP)
        )
        delete_stmt = delete(UserRecentItem).where(
            UserRecentItem.id.in_(over_cap_subq)
        )
        await self._session.execute(delete_stmt)

    async def list_recents(
        self,
        user_id: UUID,
    ) -> Sequence[UserRecentItem]:
        """Return up to ``RECENT_ITEMS_CAP`` newest items for the dashboard."""
        stmt = (
            select(UserRecentItem)
            .where(UserRecentItem.user_id == user_id)
            .order_by(desc(UserRecentItem.viewed_at))
            .limit(RECENT_ITEMS_CAP)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return list(rows)


__all__ = ["ProgressOverviewAndRecents"]
