"""HTTP endpoints for interview-preparation companies.

Mounted at ``/api/v1/problems/companies`` (problems are
the parent resource; companies are children of the
interview-preparation surface).

Endpoints
---------
- ``GET    /api/v1/problems/companies``           - list
- ``GET    /api/v1/problems/companies/{slug}``    - detail

Refs: ALGOVISION_BACKEND_PLAN.md §4 (B4.8)
Refs: PUKU_BACKEND_AGENT.md §7
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path

from src.modules.problems.dependencies import get_problems_service
from src.modules.problems.router._common import build_company_filters
from src.modules.problems.schemas import (
    CompanyListResponse,
    CompanyResponse,
)
from src.modules.problems.service import ProblemsServiceProtocol

router = APIRouter(
    prefix="/api/v1/problems/companies",
    tags=["problems-companies"],
)


@router.get(
    "",
    response_model=CompanyListResponse,
    summary="List interview-preparation companies",
)
async def list_companies(
    filters=Depends(build_company_filters),
    service: ProblemsServiceProtocol = Depends(get_problems_service),
) -> CompanyListResponse:
    page = await service.list_companies(filters)
    return CompanyListResponse(
        items=list(page.items),
        page=page.page,
        page_size=page.page_size,
        total=page.total,
        total_pages=page.total_pages,
    )


@router.get(
    "/{slug}",
    response_model=CompanyResponse,
    summary="Get a company by slug",
)
async def get_company(
    slug: str = Path(..., min_length=1, max_length=96),
    service: ProblemsServiceProtocol = Depends(get_problems_service),
) -> CompanyResponse:
    return await service.get_company_by_slug(slug)


__all__ = ["router"]
