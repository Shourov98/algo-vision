"""HTTP endpoints for topics.

Endpoints
---------
- ``GET /api/v1/topics``           — list topics
- ``GET /api/v1/topics/{slug}``    — get one topic

Topics live at their own top-level prefix (not under
``/algorithms``) because they are shared between catalog
(Phase 3) and problems (Phase 4) modules.

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 3)
Refs: PUKU_BACKEND_AGENT.md §7
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path

from src.modules.catalog.dependencies import get_catalog_service
from src.modules.catalog.filters import TopicFilters
from src.modules.catalog.router._common import build_topic_filters
from src.modules.catalog.schemas import (
    TopicListResponse,
    TopicResponse,
)
from src.modules.catalog.service import CatalogServiceProtocol

router = APIRouter(prefix="/api/v1/topics", tags=["catalog-topics"])


@router.get(
    "",
    response_model=TopicListResponse,
    summary="List topics",
)
async def list_topics(
    filters: TopicFilters = Depends(build_topic_filters),
    service: CatalogServiceProtocol = Depends(get_catalog_service),
) -> TopicListResponse:
    page = await service.list_topics(filters)
    return TopicListResponse(
        items=list(page.items),
        page=page.page,
        page_size=page.page_size,
        total=page.total,
        total_pages=page.total_pages,
    )


@router.get(
    "/{slug}",
    response_model=TopicResponse,
    summary="Get a topic by slug",
)
async def get_topic(
    slug: str = Path(..., min_length=1, max_length=64),
    service: CatalogServiceProtocol = Depends(get_catalog_service),
) -> TopicResponse:
    return await service.get_topic_by_slug(slug)


__all__ = ["router"]
