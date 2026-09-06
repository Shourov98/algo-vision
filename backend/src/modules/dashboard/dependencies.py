"""FastAPI dependencies for the dashboard module.

Wires the HTTP layer to the orchestrator (B5.11) and, via
it, to the four calculator protocols (B5.10) and the
progress service (B5.6).

Why the calculator factories take a sessionmaker
------------------------------------------------
Each calculator opens its own session via the injected
sessionmaker (``async with factory() as session:``). The
sessionmaker is the same ``get_session_factory`` the
dispatcher handlers use (B5.7); we just take the
reference at dependency-build time so each calculator
ends up bound to the same per-request engine.

Why a per-request DashboardService
----------------------------------
The service holds no state — its constructor injects
calculator Protocols and the progress service. Building a
fresh service per request is cheap (no I/O) and keeps the
service stateless across requests, which makes Liskov
substitution in tests trivial.

Refs: ALGOVISION_BACKEND_PLAN.md §5 (B5.12)
Refs: PUKU_BACKEND_AGENT.md §7 (Router Conventions)
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_session, get_session_factory
from src.modules.dashboard.calculators import (
    FocusAreaSelector,
    ReadinessCalculator,
    SkillMapper,
    StreakCalculator,
)
from src.modules.dashboard.schemas import DashboardSummary
from src.modules.dashboard.service import (
    DashboardService,
    DashboardServiceProtocol,
)
from src.modules.progress.dependencies import get_progress_service
from src.modules.progress.service import ProgressServiceProtocol


def get_dashboard_service(
    session: AsyncSession = Depends(get_session),
    progress_service: ProgressServiceProtocol = Depends(
        get_progress_service
    ),
) -> DashboardServiceProtocol:
    """Build a per-request DashboardService.

    Each calculator receives ``get_session_factory`` (an
    ``async_sessionmaker``) so it can open a fresh
    session per invocation: ``async with factory() as
    session:``. The progress service already holds its
    own request-scoped session via ``get_progress_service``.

    The dashboard service also receives the same
    sessionmaker so its two COUNT(*) queries can run
    independently of the request-scoped session on the
    same engine. Using the same engine avoids pooling two
    engines in the same process.
    """
    factory = get_session_factory()

    readiness = ReadinessCalculator(session_factory=factory)
    skill = SkillMapper(session_factory=factory)
    focus = FocusAreaSelector(skill_mapper=skill)
    streak = StreakCalculator(session_factory=factory)

    # ``session`` is unused directly by the orchestrator
    # but pulling it via Depends() guarantees the request
    # has an open DB transaction for any future direct
    # session-bound work the service might grow into.
    _ = session

    return DashboardService(
        progress_service=progress_service,
        readiness=readiness,
        skill_mapper=skill,
        focus_selector=focus,
        streak=streak,
        catalog_session_factory=factory,
    )


__all__ = ["DashboardSummary", "get_dashboard_service"]

