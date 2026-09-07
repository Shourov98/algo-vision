"""DashboardService — read-side orchestrator for the home dashboard.

Single responsibility
---------------------
The service is the ONLY layer that knows how the dashboard
projection is assembled. Per ALGOVISION_BACKEND_PLAN §5 the
service is an *orchestrator only* — every formula lives in
a dedicated calculator (B5.10) and the progress overview
comes from ProgressService (B5.6). The service:

1. Fans out to the calculators and the progress reads
   concurrently via ``asyncio.gather`` so the round-trip
   stays bounded by the slowest feed, not the sum.
2. Merges the calculator outputs + the progress overview +
   the recents feed into a single ``DashboardSummary``
   (B5.9 schema).
3. Pulls the two catalog totals (algorithms_total,
   problems_total) via two cheap ``COUNT(*)`` queries — these
   are not part of any calculator because they're not
   user-specific.

Why this is NOT an HTTP-level fan-out
-------------------------------------
Each calculator opens its own DB session via the injected
session factory; running them concurrently in one Python
task keeps the response assembly in a single place. The
HTTP client still gets one round-trip.

What this class does NOT own
----------------------------
- HTTP concerns (status codes, request parsing). Routers do.
- Formulas. Calculators do.
- ORM → response translation for progress reads.
  ProgressService does (the dashboard reuses the
  ``RecentItemResponse`` shape directly — see B5.9).

Refs: ALGOVISION_BACKEND_PLAN.md §5 (B5.11)
Refs: PUKU_BACKEND_AGENT.md §6 (Service Conventions)
Refs: ARCHITECTURE.md §7 (ADR-002 — orchestrator pattern)
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Protocol
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.catalog.models import Algorithm
from src.modules.dashboard.calculators import (
    FocusAreaSelectorProtocol,
    ReadinessCalculatorProtocol,
    SkillMapperProtocol,
    StreakCalculatorProtocol,
)
from src.modules.dashboard.schemas import (
    DashboardSummary,
    RecentItem,
)
from src.modules.progress.service import ProgressServiceProtocol

# ---------------------------------------------------------------------------
# Service protocol
# ---------------------------------------------------------------------------


class DashboardServiceProtocol(Protocol):
    """Interface the dashboard router depends on (DIP)."""

    async def get_summary(self, user_id: UUID) -> DashboardSummary: ...


# ---------------------------------------------------------------------------
# Concrete orchestrator
# ---------------------------------------------------------------------------


class DashboardService:
    """Async orchestrator for the dashboard projection.

    Composition is constructor injection. The service is
    given:

    - a ``ProgressServiceProtocol`` for the overview counts
      + recents feed (the progress module owns that SQL).
    - four calculator protocols (B5.10) for the formulas.
    - a session factory for the catalog ``COUNT(*)``
      queries that drive the ``*_total`` denominators.

    Test fakes swap any subset of the dependencies for
    AsyncMock-backed stubs; production wiring (B5.12
    dependency factory) wires the concrete classes from
    the request-scoped session.
    """

    def __init__(
        self,
        progress_service: ProgressServiceProtocol,
        readiness: ReadinessCalculatorProtocol,
        skill_mapper: SkillMapperProtocol,
        focus_selector: FocusAreaSelectorProtocol,
        streak: StreakCalculatorProtocol,
        catalog_session_factory: Callable[[], AsyncSession],
    ) -> None:
        self._progress = progress_service
        self._readiness = readiness
        self._skill_mapper = skill_mapper
        self._focus_selector = focus_selector
        self._streak = streak
        self._catalog_session_factory = catalog_session_factory

    async def get_summary(self, user_id: UUID) -> DashboardSummary:
        """Build the full ``DashboardSummary`` for ``user_id``.

        Runs six reads concurrently:
        - readiness (calculator)
        - skill mapping (calculator)
        - focus areas (calculator; depends on skill mapper)
        - current streak (calculator)
        - progress overview (ProgressService)
        - recent items (ProgressService)

        Then awaits two small catalog COUNTs sequentially
        (they're fast and run on the same session). The
        parallel gather is the optimisation: an
        end-to-end serial build would be 6x slower.
        """
        (
            readiness, skill_mapping, activity,
            overview, recents,
        ) = await asyncio.gather(
            self._readiness.compute(user_id),
            self._skill_mapper.compute(user_id),
            self._streak.activity_feed(user_id),
            self._progress.get_overview(user_id),
            self._progress.list_recents(user_id),
        )

        # Focus areas depend on the skill mapping, so we
        # compute them after the gather. ``select_focus_areas``
        # calls the skill mapper again — it shares its
        # session factory and is cheap.
        focus_areas = await self._focus_selector.select_focus_areas(
            user_id
        )

        current_streak = await self._streak.current_streak(user_id)

        algorithms_total, problems_total = await self._catalog_totals()

        return DashboardSummary(
            algorithms_learned=overview.algorithms.completed,
            algorithms_total=algorithms_total,
            problems_solved=overview.problems.completed,
            problems_total=problems_total,
            interview_readiness=readiness,
            skill_mapping=skill_mapping,
            focus_areas=focus_areas,
            current_streak=current_streak,
            activity=activity,
            recently_viewed=[
                RecentItem(
                    id=r.id,
                    item_type=r.item_type,
                    item_id=r.item_id,
                    viewed_at=r.viewed_at,
                )
                for r in recents.items
            ],
        )

    # ------------------------------------------------------------------
    # Catalog totals (small, runs sequentially after the gather)
    # ------------------------------------------------------------------

    async def _catalog_totals(self) -> tuple[int, int]:
        """Return ``(algorithms_total, problems_total)``.

        Two ``COUNT(*)`` queries against published /
        non-deleted rows. Problems don't have an
        ``is_published`` flag in v1 — DATABASE_DESIGN §1
        treats every problem row as catalog-visible, so we
        count all rows.

        Why we open our own session
        ---------------------------
        The catalog is owned by the catalog module; the
        dashboard only needs aggregate counts, not the
        full repository API. A dedicated session here
        keeps the orchestrator decoupled from the catalog
        repository module while still using the same
        engine.
        """
        async with self._catalog_session_factory() as session:
            alg_stmt = (
                select(func.count(Algorithm.id))
                .where(Algorithm.is_published.is_(True))
            )
            algorithms_total = int(
                (await session.execute(alg_stmt)).scalar_one()
            )
            # Problems table is independent — count directly.
            # We import inside the method to avoid a module-
            # level coupling to problems.
            from src.modules.problems.models import Problem

            prob_stmt = select(func.count(Problem.id))
            problems_total = int(
                (await session.execute(prob_stmt)).scalar_one()
            )
        return algorithms_total, problems_total


__all__ = ["DashboardService", "DashboardServiceProtocol"]
