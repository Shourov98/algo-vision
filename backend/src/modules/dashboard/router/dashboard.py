"""HTTP endpoints for the home dashboard.

Mounted at ``/api/v1/dashboard`` (per ALGOVISION_BACKEND_PLAN
§5 — dashboard is the read-side composition surface).

Endpoints
---------
- ``GET /api/v1/dashboard/summary`` - the full home dashboard
  projection: progress counts, interview readiness,
  per-skill heatmap, focus areas, streak, activity feed,
  recents.

Auth
----
The endpoint requires an authenticated user. ``user_id``
comes from the auth module's ``get_current_user``
dependency (Phase 2). The router passes ``user_id`` into
the service — the service never reads from the request
directly (DIP).

Why one endpoint (not many)
---------------------------
The dashboard renders from a single object; splitting the
projection across many endpoints would multiply round-trips
and create the risk of partial-render states when the
client fetches in parallel. The summary endpoint is one
coherent read; the orchestrator handles the fan-out.

Refs: ALGOVISION_BACKEND_PLAN.md §5 (B5.12)
Refs: PUKU_BACKEND_AGENT.md §7 (Router Conventions)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from src.core.rate_limit import RATE_LIMIT_DASHBOARD, make_rate_limit_dependency
from src.modules.auth.dependencies import get_current_user
from src.modules.dashboard.dependencies import get_dashboard_service
from src.modules.dashboard.schemas import DashboardSummary
from src.modules.dashboard.service import DashboardServiceProtocol
from src.modules.users.models import User

router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["dashboard"],
)


@router.get(
    "/summary",
    response_model=DashboardSummary,
    summary="Home dashboard projection",
    dependencies=[Depends(make_rate_limit_dependency(RATE_LIMIT_DASHBOARD))],
)
async def get_dashboard_summary(
    user: User = Depends(get_current_user),
    service: DashboardServiceProtocol = Depends(get_dashboard_service),
) -> DashboardSummary:
    """Return the full home dashboard projection for the caller.

    Composed from the four dashboard calculators, the
    progress service, and the catalog totals. See
    ``DashboardService.get_summary`` (B5.11) for the
    orchestration details.
    """
    return await service.get_summary(user.id)


__all__ = ["router"]
