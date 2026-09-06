"""Readiness calculator — composite interview-readiness score.

Owns ONE reason to change: the formula that turns a user's
algorithm completion state into a single 0..100 score with a
per-category breakdown. The orchestrator (DashboardAggregator)
delegates here so this file is the only place that needs to
be touched when the readiness formula evolves.

Formula
-------
1. For every category C in ``algorithm_categories``:
   - ``score[C]`` = average ``completion_percentage`` of the
     user's published algorithms in C. If the user has no
     algorithms in C, that category contributes 0 to the
     weighted sum and is still listed in the breakdown
     (with score=0).
2. ``weight[C]`` = (number of published algorithms in C) /
   (total published algorithms across all categories). This
   gives heavier categories (more material to learn) more
   pull on the composite score.
3. ``readiness.score`` = round( sum(score[C] * weight[C])
   for C with positive weight ). Returned as int 0..100.

Why weighted by algorithm count, not user activity
--------------------------------------------------
A user's progress inside a category is the *quality* signal;
the category's algorithm count is the *quantity* signal.
Weighting by quantity keeps the score interpretable: a
category with 30 algorithms can dominate a category with 2.

Why we keep ``is_published`` algorithms only
--------------------------------------------
Draft algorithms aren't part of the public curriculum. They
should not contribute to readiness until they're shipped.
DATABASE_DESIGN §1 says ``algorithms.is_published`` is the
gating flag.

Refs: ALGOVISION_BACKEND_PLAN.md §5 (B5.10 — ReadinessCalculator)
Refs: ARCHITECTURE.md §7 (ADR-002 — calculator pattern)
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.catalog.models import Algorithm, Category
from src.modules.dashboard.schemas import (
    ReadinessBreakdownEntry,
    ReadinessMetric,
)
from src.modules.progress.models import UserAlgorithmProgress


class ReadinessCalculatorProtocol(Protocol):
    """Interface the orchestrator depends on (DIP)."""

    async def compute(self, user_id: UUID) -> ReadinessMetric: ...


class ReadinessCalculator:
    """Async SQLAlchemy implementation of the readiness formula.

    The constructor takes a session factory function (not a
    session) so the orchestrator — which is request-scoped —
    can pass ``lambda: get_session()`` without coupling this
    class to FastAPI. Unit tests pass a session-bound factory
    that returns their own session for full introspection.
    """

    def __init__(self, session_factory: Callable[[], AsyncSession]) -> None:
        # Kept as a structural attribute so tests can assert
        # the orchestrator passed the right factory.
        self._session_factory = session_factory

    async def compute(self, user_id: UUID) -> ReadinessMetric:
        """Return the composite readiness score + per-category slice.

        Always returns a metric — even for users with zero
        progress, in which case every breakdown entry has
        score=0 and the composite is 0. The frontend can
        render the ring without a special "empty" state.
        """
        async with self._session_factory() as session:
            totals = await self._category_totals(session)
            per_category = await self._per_category_scores(
                session, user_id
            )

        if not totals:
            # No published algorithms at all — empty
            # breakdown, score 0. Frontend should treat
            # this as "curriculum not seeded yet".
            return ReadinessMetric(score=0, breakdown=[])

        grand_total = sum(
            count for _name, count in totals.values()
        )
        breakdown: list[ReadinessBreakdownEntry] = []
        weighted_sum = 0.0
        for cat_slug, (cat_name, count) in sorted(totals.items()):
            score = per_category.get(cat_slug, 0)
            weight = (
                count / grand_total if grand_total > 0 else 0.0
            )
            breakdown.append(
                ReadinessBreakdownEntry(
                    category_slug=cat_slug,
                    category_name=cat_name,
                    score=score,
                    weight=round(weight, 4),
                )
            )
            weighted_sum += score * weight

        composite = round(weighted_sum)
        # Clamp into [0, 100] even though the formula is
        # bounded by construction — defensive against future
        # weighting changes that might exceed the range.
        composite = max(0, min(100, composite))
        return ReadinessMetric(
            score=composite, breakdown=breakdown
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _category_totals(
        self, session: AsyncSession
    ) -> dict[str, tuple[str, int]]:
        """Return {slug: (name, published_algorithm_count)}.

        Returns the human-readable name as well so the
        breakdown can carry it without a second lookup. The
        dict preserves insertion order; the caller sorts
        for determinism.
        """
        stmt = (
            select(
                Category.slug,
                Category.name,
                func.count(Algorithm.id),
            )
            .join(Algorithm, Algorithm.category_id == Category.id)
            .where(Algorithm.is_published.is_(True))
            .group_by(Category.slug, Category.name)
        )
        rows = (await session.execute(stmt)).all()
        return {
            slug: (name, int(count)) for slug, name, count in rows
        }

    async def _per_category_scores(
        self, session: AsyncSession, user_id: UUID
    ) -> dict[str, int]:
        """Return {category_slug: avg_completion_pct} for ``user_id``.

        Categories where the user has no algorithm progress
        are simply absent from the result — the caller treats
        absence as 0. The average is rounded to int because
        ``ReadinessBreakdownEntry.score`` is constrained
        0..100.
        """
        stmt = (
            select(
                Category.slug,
                func.avg(UserAlgorithmProgress.completion_percentage),
            )
            .join(
                Algorithm,
                Algorithm.id == UserAlgorithmProgress.algorithm_id,
            )
            .where(
                UserAlgorithmProgress.user_id == user_id,
                Algorithm.is_published.is_(True),
            )
            .group_by(Category.slug)
        )
        rows = (await session.execute(stmt)).all()
        return {
            slug: round(float(avg))
            for slug, avg in rows
            if avg is not None
        }


__all__ = ["ReadinessCalculator", "ReadinessCalculatorProtocol"]
