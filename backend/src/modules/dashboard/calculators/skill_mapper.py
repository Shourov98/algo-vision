"""Skill-mapping calculator — per-topic mastery.

Owns ONE reason to change: how a user's progress across
algorithms is summarised at the *topic* level (Hashing,
Dynamic Programming, Graphs, …). The frontend renders the
result as a heatmap: every topic becomes a coloured cell
where the colour intensity is the mastery score.

Formula
-------
For every topic T:

- ``mastery[T]`` = round( average
  ``completion_percentage`` across the user's progress rows
  whose algorithm has T as one of its topics ).
- ``algorithms_total[T]`` = number of published algorithms
  that have T as a topic.
- ``algorithms_completed[T]`` = number of the user's progress
  rows in T where ``status == 'completed'``.

If the user has zero progress in a topic, that topic is
omitted from the response — the dashboard heatmap only
shows topics the user has *touched* (otherwise the heatmap
fills with zeroes for every topic in the seed and drowns
the signal). The frontend interprets an absent cell as
"no data yet" and renders a neutral colour.

Why average, not last-viewed
----------------------------
A user may bounce between algorithms in a topic; the
*average* mastery reflects sustained exposure. ``last_*
viewed_at`` is more appropriate for "recently viewed"
feeds (which live in their own calculator territory —
``recently_viewed`` on the dashboard summary).

Why omit topics with zero progress (not render score=0)
-------------------------------------------------------
Returning a score=0 row for every seed topic on day 0 would
tell the user they are failing every topic — which is the
wrong UX. Absence is meaningful: "you haven't started
this".

Refs: ALGOVISION_BACKEND_PLAN.md §5 (B5.10 — SkillMapper)
Refs: ARCHITECTURE.md §7 (ADR-002)
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.catalog.models import Topic, algorithm_topics
from src.modules.dashboard.schemas import SkillMetric
from src.modules.progress.models import UserAlgorithmProgress


class SkillMapperProtocol(Protocol):
    """Interface the orchestrator depends on (DIP)."""

    async def compute(self, user_id: UUID) -> list[SkillMetric]: ...


class SkillMapper:
    """Async SQLAlchemy implementation of the skill-mapping formula.

    Two SQL queries: one for ``mastery[T]`` averages, one for
    per-topic completion counters. Both are aggregated
    server-side so the wire payload stays compact.
    """

    def __init__(self, session_factory: Callable[[], AsyncSession]) -> None:
        self._session_factory = session_factory

    async def compute(self, user_id: UUID) -> list[SkillMetric]:
        """Return one ``SkillMetric`` per topic the user has touched.

        Sorted by ``mastery`` descending so the heatmap can
        render strongest topics first; the frontend is free
        to re-sort visually.
        """
        async with self._session_factory() as session:
            mastery_rows = await self._mastery_per_topic(
                session, user_id
            )
            completion_counts = await self._completion_counts(
                session, user_id
            )
            topic_labels = await self._topic_labels(session)

        metrics: list[SkillMetric] = []
        for slug, avg in mastery_rows:
            name = topic_labels.get(slug, slug)
            completed, total = completion_counts.get(slug, (0, 0))
            metrics.append(
                SkillMetric(
                    topic_slug=slug,
                    topic_name=name,
                    mastery=avg,
                    algorithms_completed=completed,
                    algorithms_total=total,
                )
            )
        # Strongest first.
        metrics.sort(key=lambda m: m.mastery, reverse=True)
        return metrics

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _mastery_per_topic(
        self, session: AsyncSession, user_id: UUID
    ) -> list[tuple[str, int]]:
        """Per-topic average mastery for ``user_id``.

        Joins ``topics -> algorithm_topics -> algorithms ->
        user_algorithm_progress`` (filtered by user_id).
        Returns a list of (slug, rounded_avg) pairs; topics
        without user progress simply don't appear.
        """
        stmt = (
            select(
                Topic.slug,
                func.avg(UserAlgorithmProgress.completion_percentage),
            )
            .select_from(Topic)
            .join(
                algorithm_topics,
                algorithm_topics.c.topic_id == Topic.id,
            )
            .join(
                UserAlgorithmProgress,
                UserAlgorithmProgress.algorithm_id
                == algorithm_topics.c.algorithm_id,
            )
            .where(UserAlgorithmProgress.user_id == user_id)
            .group_by(Topic.slug)
        )
        rows = (await session.execute(stmt)).all()
        result: list[tuple[str, int]] = []
        for slug, avg in rows:
            if avg is None:
                continue
            result.append((slug, round(float(avg))))
        return result

    async def _completion_counts(
        self, session: AsyncSession, user_id: UUID
    ) -> dict[str, tuple[int, int]]:
        """{topic_slug: (completed, total_user_algorithms)}.

        ``completed`` = count of progress rows in the topic
        with ``status='completed'``. ``total_user_algorithms``
        = count of progress rows in the topic regardless of
        status. The dashboard uses ``total`` as the
        denominator when rendering the heatmap's progress
        ring; we deliberately do NOT use the total published
        algorithms in the topic because the user's
        ``total_sessions`` is per their exposure.
        """
        completed_expr = func.sum(
            case(
                (
                    UserAlgorithmProgress.status == "completed",
                    1,
                ),
                else_=0,
            )
        )
        stmt = (
            select(
                Topic.slug,
                completed_expr,
                func.count(UserAlgorithmProgress.user_id),
            )
            .select_from(Topic)
            .join(
                algorithm_topics,
                algorithm_topics.c.topic_id == Topic.id,
            )
            .join(
                UserAlgorithmProgress,
                UserAlgorithmProgress.algorithm_id
                == algorithm_topics.c.algorithm_id,
            )
            .where(UserAlgorithmProgress.user_id == user_id)
            .group_by(Topic.slug)
        )
        rows = (await session.execute(stmt)).all()
        return {
            slug: (int(completed or 0), int(total))
            for slug, completed, total in rows
        }

    async def _topic_labels(
        self, session: AsyncSession
    ) -> dict[str, str]:
        """Return {topic_slug: topic_name} for every topic in the catalog."""
        stmt = select(Topic.slug, Topic.name)
        rows = (await session.execute(stmt)).all()
        return {slug: name for slug, name in rows}


__all__ = ["SkillMapper", "SkillMapperProtocol"]
