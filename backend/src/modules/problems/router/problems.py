"""HTTP endpoints for interview-preparation problems.

Mounted at ``/api/v1/problems`` (per ALGOVISION_BACKEND_PLAN
§4 — problems are the top-level interview-preparation
resource).

Endpoints
---------
- ``GET    /api/v1/problems``           - list (paginated, filterable)
- ``GET    /api/v1/problems/{slug}``    - detail (embeds topics + companies)

Refs: ALGOVISION_BACKEND_PLAN.md §4 (B4.8)
Refs: PUKU_BACKEND_AGENT.md §7
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path

from src.modules.problems.dependencies import get_problems_service
from src.modules.problems.router._common import build_problem_filters
from src.modules.problems.schemas import (
    ProblemDetailResponse,
    ProblemListResponse,
)
from src.modules.problems.service import ProblemsServiceProtocol

router = APIRouter(
    prefix="/api/v1/problems",
    tags=["problems"],
)


@router.get(
    "",
    response_model=ProblemListResponse,
    summary="List interview-preparation problems",
)
async def list_problems(
    filters=Depends(build_problem_filters),
    service: ProblemsServiceProtocol = Depends(get_problems_service),
) -> ProblemListResponse:
    page = await service.list_problems(filters)
    return ProblemListResponse(
        items=list(page.items),
        page=page.page,
        page_size=page.page_size,
        total=page.total,
        total_pages=page.total_pages,
    )


@router.get(
    "/{slug}",
    response_model=ProblemDetailResponse,
    summary="Get a problem by slug",
)
async def get_problem(
    slug: str = Path(..., min_length=1, max_length=96),
    service: ProblemsServiceProtocol = Depends(get_problems_service),
) -> ProblemDetailResponse:
    return await service.get_problem_by_slug(slug)


__all__ = ["router"]
