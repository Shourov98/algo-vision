"""HTTP endpoints for data structures.

Endpoints
---------
- ``GET /api/v1/data-structures``         — list
- ``GET /api/v1/data-structures/{slug}``  — detail

The detail endpoint dispatches ``ItemViewedEvent`` when a
user is authenticated so progress tracking can attribute
the view.

Refs: ALGOVISION_BACKEND_PLAN.md §3.15
Refs: PUKU_BACKEND_AGENT.md §7
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path

from src.modules.catalog.dependencies import (
    get_catalog_service,
    get_optional_user,
)
from src.modules.catalog.filters import DataStructureFilters
from src.modules.catalog.router._common import build_data_structure_filters
from src.modules.catalog.schemas import (
    DataStructureListResponse,
    DataStructureResponse,
)
from src.modules.catalog.service import CatalogServiceProtocol
from src.modules.users.models import User

router = APIRouter(prefix="/api/v1/data-structures", tags=["data-structures"])


@router.get(
    "",
    response_model=DataStructureListResponse,
    summary="List data structures",
)
async def list_data_structures(
    filters: DataStructureFilters = Depends(build_data_structure_filters),
    service: CatalogServiceProtocol = Depends(get_catalog_service),
) -> DataStructureListResponse:
    page = await service.list_data_structures(filters)
    return DataStructureListResponse(
        items=list(page.items),
        page=page.page,
        page_size=page.page_size,
        total=page.total,
        total_pages=page.total_pages,
    )


@router.get(
    "/{slug}",
    response_model=DataStructureResponse,
    summary="Get a data structure by slug",
)
async def get_data_structure(
    slug: str = Path(..., min_length=1, max_length=64),
    service: CatalogServiceProtocol = Depends(get_catalog_service),
    user: User | None = Depends(get_optional_user),
) -> DataStructureResponse:
    return await service.get_data_structure_by_slug(
        slug, user_id=user.id if user is not None else None
    )


__all__ = ["router"]
