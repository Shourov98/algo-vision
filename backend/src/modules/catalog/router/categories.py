"""HTTP endpoints for algorithm categories.

Mounted at ``/api/v1/algorithms/categories`` (the prefix is
chosen to match the public API surface in
ALGOVISION_BACKEND_PLAN §3.14 — the categories endpoint is
sibling to /algorithms, not nested under it).

Endpoints
---------
- ``GET    /api/v1/algorithms/categories``     — list
- ``GET    /api/v1/algorithms/categories/{slug}`` — detail

Refs: ALGOVISION_BACKEND_PLAN.md §3.14
Refs: PUKU_BACKEND_AGENT.md §7
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Response

from src.modules.catalog.dependencies import get_catalog_service
from src.modules.catalog.filters import CategoryFilters
from src.modules.catalog.router._common import build_category_filters
from src.modules.catalog.schemas import (
    CategoryListResponse,
    CategoryResponse,
)
from src.modules.catalog.service import CatalogServiceProtocol
from src.shared.http_cache import set_public_cache

router = APIRouter(
    prefix="/api/v1/algorithms/categories",
    tags=["catalog-categories"],
)


@router.get(
    "",
    response_model=CategoryListResponse,
    summary="List algorithm categories",
)
async def list_categories(
    response: Response,
    filters: CategoryFilters = Depends(build_category_filters),
    service: CatalogServiceProtocol = Depends(get_catalog_service),
) -> CategoryListResponse:
    set_public_cache(response, max_age=3600)
    page = await service.list_categories(filters)
    return CategoryListResponse(
        items=list(page.items),
        page=page.page,
        page_size=page.page_size,
        total=page.total,
        total_pages=page.total_pages,
    )


@router.get(
    "/{slug}",
    response_model=CategoryResponse,
    summary="Get an algorithm category by slug",
)
async def get_category(
    response: Response,
    slug: str = Path(..., min_length=1, max_length=64),
    service: CatalogServiceProtocol = Depends(get_catalog_service),
) -> CategoryResponse:
    set_public_cache(response, max_age=3600)
    return await service.get_category_by_slug(slug)


__all__ = ["router"]
