"""Streak calculator — consecutive-days-active streak.

Owns ONE reason to change: how a user's "active days" are
collapsed into a single integer streak count. The
orchestrator delegates here so the streak rules (which
sources count? what's an "active day"?) live in a single
file.

Sources of activity
-------------------
A day is "active" if the user emitted any of the following
on it:

- ``user_algorithm_progress.last_viewed_at`` (every time
  they re-visit an algorithm they already have a row for,
  the row's last_viewed_at is bumped).
- ``user_problem_progress.last_viewed_at`` (same idea for
  problems).
- ``user_recent_items.viewed_at`` (every successful view
  event the dispatcher recorded).

We union all three sources by UTC date, dedupe, and count
back from *today* (UTC) while the dates are consecutive.

Why we count by UTC date
------------------------
Mixing user-local dates would require the user's timezone,
which we don't store on the user record. UTC is the
simplest defensible default; the frontend can render the
"active day" window in the user's local timezone by
adjusting the rendered bar position, but the streak
counter itself is timezone-agnostic.

Today's behaviour
----------------
If the user was active today, the streak starts at 1 and
walks back. If the user was NOT active today (their most
recent active day was yesterday or earlier), the streak
counter shows the most-recent run *consecutive up to and
including the most recent active day*. We do NOT force a
"must be active today" rule — that would punish users who
haven't been online today but are mid-run.

Activity feed
-------------
The calculator also produces the daily activity counts the
dashboard's heatmap renders — a ``list[ActivityPoint]``
covering the last ``ACTIVITY_WINDOW_DAYS`` days, even days
with zero activity (so the heatmap renders a continuous
bar of cells).

Refs: ALGOVISION_BACKEND_PLAN.md §5 (B5.10 — StreakCalculator)
Refs: ARCHITECTURE.md §7 (ADR-002)
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import UTC, date, datetime, timedelta
from typing import Protocol
from uuid import UUID

from sqlalchemy import func, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.dashboard.schemas import ActivityPoint
from src.modules.progress.models import (
    UserAlgorithmProgress,
    UserProblemProgress,
    UserRecentItem,
)

# 90 days of activity history drives the heatmap. Matches
# the design SVG window (Dashboard — AlgoVision.svg). The
# dashboard never asks for older than this.
ACTIVITY_WINDOW_DAYS = 90


class StreakCalculatorProtocol(Protocol):
    """Interface the orchestrator depends on (DIP)."""

    async def current_streak(self, user_id: UUID) -> int: ...

    async def activity_feed(
        self, user_id: UUID
    ) -> list[ActivityPoint]: ...


class StreakCalculator:
    """Async SQLAlchemy implementation of the streak rules.

    Constructed with a session factory like the other
    calculators so unit tests can swap in their own session.
    """

    def __init__(self, session_factory: Callable[[], AsyncSession]) -> None:
        self._session_factory = session_factory

    async def current_streak(self, user_id: UUID) -> int:
        """Return the count of consecutive days ending on the latest
        active day (inclusive)."""
        async with self._session_factory() as session:
            active_days = await self._active_days(session, user_id)
        if not active_days:
            return 0
        return _count_consecutive(active_days, today=date.today())

    async def activity_feed(
        self, user_id: UUID
    ) -> list[ActivityPoint]:
        """Return one ``ActivityPoint`` per day for the last
        ``ACTIVITY_WINDOW_DAYS`` days, zero-filled."""
        async with self._session_factory() as session:
            counts = await self._activity_counts(session, user_id)
        today = date.today()
        window_start = today - timedelta(days=ACTIVITY_WINDOW_DAYS - 1)
        points: list[ActivityPoint] = []
        for offset in range(ACTIVITY_WINDOW_DAYS):
            day = window_start + timedelta(days=offset)
            points.append(
                ActivityPoint(date=day, count=counts.get(day, 0))
            )
        return points

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _active_days(
        self, session: AsyncSession, user_id: UUID
    ) -> set[date]:
        """Return the set of UTC dates the user was active on.

        UNION ALL of three timestamp columns, projected to
        UTC date via ``func.date()`` (Postgres-style; the
        migration's column type is TIMESTAMPTZ so the
        truncation is correct).
        """
        # Three sub-queries — same projection shape
        # (event_date) — UNION ALL'd then deduped by Python.
        # The activity window is bounded; the volume per
        # user is small (rows touched in the last 90 days).
        alg_subq = (
            select(
                func.date(UserAlgorithmProgress.last_viewed_at).label(
                    "event_date"
                )
            )
            .where(UserAlgorithmProgress.user_id == user_id)
        )
        prob_subq = (
            select(
                func.date(UserProblemProgress.last_viewed_at).label(
                    "event_date"
                )
            )
            .where(UserProblemProgress.user_id == user_id)
        )
        rec_subq = (
            select(
                func.date(UserRecentItem.viewed_at).label("event_date")
            )
            .where(UserRecentItem.user_id == user_id)
        )
        unioned = union_all(alg_subq, prob_subq, rec_subq).subquery()
        stmt = select(func.distinct(unioned.c.event_date))
        rows = (await session.execute(stmt)).all()
        result: set[date] = set()
        for (day,) in rows:
            if day is None:
                continue
            # Postgres' DATE -> Python ``datetime.date``; SQLAlchemy
            # maps it directly. Defensive: handle datetime too.
            if isinstance(day, datetime):
                result.add(day.astimezone(UTC).date())
            else:
                result.add(day)
        return result

    async def _activity_counts(
        self, session: AsyncSession, user_id: UUID
    ) -> dict[date, int]:
        """{utc_date: event_count} across the activity window.

        Same UNION ALL structure as ``_active_days`` but
        GROUP BY date so we get raw counts. Days without
        activity are absent — the caller zero-fills.
        """
        alg_subq = (
            select(
                func.date(UserAlgorithmProgress.last_viewed_at).label(
                    "event_date"
                )
            )
            .where(UserAlgorithmProgress.user_id == user_id)
        )
        prob_subq = (
            select(
                func.date(UserProblemProgress.last_viewed_at).label(
                    "event_date"
                )
            )
            .where(UserProblemProgress.user_id == user_id)
        )
        rec_subq = (
            select(
                func.date(UserRecentItem.viewed_at).label("event_date")
            )
            .where(UserRecentItem.user_id == user_id)
        )
        unioned = union_all(alg_subq, prob_subq, rec_subq).subquery()
        stmt = (
            select(unioned.c.event_date, func.count())
            .group_by(unioned.c.event_date)
        )
        rows = (await session.execute(stmt)).all()
        result: dict[date, int] = {}
        for day, count in rows:
            if day is None:
                continue
            key = day.astimezone(UTC).date() if isinstance(day, datetime) else day
            result[key] = int(count)
        return result


# ---------------------------------------------------------------------------
# Pure helpers (testable without a session)
# ---------------------------------------------------------------------------


def _count_consecutive(
    active_days: Iterable[date], *, today: date
) -> int:
    """Count days back from the most recent active day, inclusive.

    Walks back from ``today`` if ``today`` is active,
    otherwise from the most recent active day found.
    Returns 0 when no active days exist.
    """
    days = set(active_days)
    if not days:
        return 0
    cursor = today if today in days else max(days)
    streak = 0
    while cursor in days:
        streak += 1
        cursor = cursor - timedelta(days=1)
    return streak


__all__ = [
    "ACTIVITY_WINDOW_DAYS",
    "StreakCalculator",
    "StreakCalculatorProtocol",
]
