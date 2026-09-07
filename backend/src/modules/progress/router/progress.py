"""HTTP endpoints for per-user progress.

Mounted at ``/api/v1/progress`` (per ALGOVISION_BACKEND_PLAN
§5 — progress is the write-side per-user surface).

Endpoints
---------
- ``POST /api/v1/progress/algorithms/{algorithm_id}`` - mark progress on an algorithm
- ``POST /api/v1/progress/problems/{problem_id}``     - mark progress on a problem
- ``GET  /api/v1/progress/algorithms``                - list caller's algorithm progress
- ``GET  /api/v1/progress/problems``                  - list caller's problem progress
- ``GET  /api/v1/progress/overview``                  - composite counts for the dashboard
- ``GET  /api/v1/progress/recents``                   - capped at 50 most-recent views

Auth
----
All endpoints require an authenticated user. ``user_id``
comes from the auth module's ``get_current_user``
dependency (Phase 2). The router passes ``user_id`` into
the service — the service never reads from the request
directly (DIP).

Order
-----
This router has only variable-path endpoints under the
/progress prefix; no literal-path siblings to collide with.
We mount all six here so the per-router tag stays focused.

Refs: ALGOVISION_BACKEND_PLAN.md §5 (Phase 5 - B5.7)
Refs: PUKU_BACKEND_AGENT.md §7 (Router Conventions)
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_session
from src.modules.auth.dependencies import get_current_user
from src.modules.progress.dependencies import get_progress_service
from src.modules.progress.router._common import (
    build_algorithm_progress_filters,
    build_problem_progress_filters,
)
from src.modules.progress.schemas import (
    AlgorithmProgressListResponse,
    MarkAlgorithmProgressRequest,
    MarkProblemProgressRequest,
    ProblemProgressListResponse,
    ProgressOverviewResponse,
    RecentsListResponse,
    UserAlgorithmProgressResponse,
    UserProblemProgressResponse,
)
from src.modules.progress.service import ProgressServiceProtocol
from src.modules.users.models import User

router = APIRouter(
    prefix="/api/v1/progress",
    tags=["progress"],
)


# ---------------------------------------------------------------------------
# Reads (listings + overview + recents)
# ---------------------------------------------------------------------------


@router.get(
    "/algorithms",
    response_model=AlgorithmProgressListResponse,
    summary="List caller's algorithm progress",
)
async def list_algorithm_progress(
    filters=Depends(build_algorithm_progress_filters),
    user: User = Depends(get_current_user),
    service: ProgressServiceProtocol = Depends(get_progress_service),
) -> AlgorithmProgressListResponse:
    page = await service.list_algorithm_progress(user.id, filters)
    return AlgorithmProgressListResponse(
        items=list(page.items),
        page=page.page,
        page_size=page.page_size,
        total=page.total,
        total_pages=page.total_pages,
    )


@router.get(
    "/problems",
    response_model=ProblemProgressListResponse,
    summary="List caller's problem progress",
)
async def list_problem_progress(
    filters=Depends(build_problem_progress_filters),
    user: User = Depends(get_current_user),
    service: ProgressServiceProtocol = Depends(get_progress_service),
) -> ProblemProgressListResponse:
    page = await service.list_problem_progress(user.id, filters)
    return ProblemProgressListResponse(
        items=list(page.items),
        page=page.page,
        page_size=page.page_size,
        total=page.total,
        total_pages=page.total_pages,
    )


@router.get(
    "/overview",
    response_model=ProgressOverviewResponse,
    summary="Composite progress counts for the dashboard",
)
async def get_overview(
    user: User = Depends(get_current_user),
    service: ProgressServiceProtocol = Depends(get_progress_service),
) -> ProgressOverviewResponse:
    return await service.get_overview(user.id)


@router.get(
    "/recents",
    response_model=RecentsListResponse,
    summary="Caller's recently viewed items (capped at 50)",
)
async def list_recents(
    user: User = Depends(get_current_user),
    service: ProgressServiceProtocol = Depends(get_progress_service),
) -> RecentsListResponse:
    return await service.list_recents(user.id)


# ---------------------------------------------------------------------------
# Writes (idempotent upserts)
# ---------------------------------------------------------------------------


@router.post(
    "/algorithms/{algorithm_id}",
    response_model=UserAlgorithmProgressResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark progress on an algorithm",
)
async def mark_algorithm(
    payload: MarkAlgorithmProgressRequest,
    algorithm_id: UUID = Path(...),
    user: User = Depends(get_current_user),
    service: ProgressServiceProtocol = Depends(get_progress_service),
    session: AsyncSession = Depends(get_session),
) -> UserAlgorithmProgressResponse:
    response = await service.mark_algorithm(
        user_id=user.id,
        algorithm_id=algorithm_id,
        status=payload.status,
        completion_percentage=payload.completion_percentage,
    )
    await session.commit()
    return response


@router.post(
    "/problems/{problem_id}",
    response_model=UserProblemProgressResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark progress on a problem",
)
async def mark_problem(
    payload: MarkProblemProgressRequest,
    problem_id: UUID = Path(...),
    user: User = Depends(get_current_user),
    service: ProgressServiceProtocol = Depends(get_progress_service),
    session: AsyncSession = Depends(get_session),
) -> UserProblemProgressResponse:
    response = await service.mark_problem(
        user_id=user.id,
        problem_id=problem_id,
        status=payload.status,
        attempts=payload.attempts,
    )
    await session.commit()
    return response


__all__ = ["router"]
