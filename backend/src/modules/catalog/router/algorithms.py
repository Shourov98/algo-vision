"""HTTP endpoints for algorithms.

Endpoints
---------
- ``GET    /api/v1/algorithms``                  — list (paginated)
- ``GET    /api/v1/algorithms/{slug}``           — detail
- ``GET    /api/v1/algorithms/{slug}/code``      — current code in
                                                  a given language
- ``GET    /api/v1/algorithms/{slug}/code/versions`` — version history

Detail reads dispatch ``ItemViewedEvent`` when a user is
authenticated so progress can attribute the view.

Refs: ALGOVISION_BACKEND_PLAN.md §3.12, §3.13
Refs: PUKU_BACKEND_AGENT.md §7
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Query

from src.modules.catalog.dependencies import (
    get_catalog_service,
    get_optional_user,
)
from src.modules.catalog.filters import AlgorithmFilters
from src.modules.catalog.router._common import (
    build_algorithm_filters,
    build_code_version_filters,
)
from src.modules.catalog.schemas import (
    AlgorithmCodeResponse,
    AlgorithmDetailResponse,
    AlgorithmListResponse,
)
from src.modules.catalog.service import CatalogServiceProtocol
from src.modules.users.models import User

router = APIRouter(prefix="/api/v1/algorithms", tags=["algorithms"])


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=AlgorithmListResponse,
    summary="List algorithms",
)
async def list_algorithms(
    filters: AlgorithmFilters = Depends(build_algorithm_filters),
    service: CatalogServiceProtocol = Depends(get_catalog_service),
) -> AlgorithmListResponse:
    page = await service.list_algorithms(filters)
    return AlgorithmListResponse(
        items=list(page.items),
        page=page.page,
        page_size=page.page_size,
        total=page.total,
        total_pages=page.total_pages,
    )


# ---------------------------------------------------------------------------
# Detail
# ---------------------------------------------------------------------------


@router.get(
    "/{slug}",
    response_model=AlgorithmDetailResponse,
    summary="Get an algorithm by slug",
)
async def get_algorithm(
    slug: str = Path(..., min_length=1, max_length=128),
    service: CatalogServiceProtocol = Depends(get_catalog_service),
    user: User | None = Depends(get_optional_user),
) -> AlgorithmDetailResponse:
    return await service.get_algorithm_by_slug(
        slug, user_id=user.id if user is not None else None
    )


# ---------------------------------------------------------------------------
# Current code in a given language
# ---------------------------------------------------------------------------


@router.get(
    "/{slug}/code",
    response_model=AlgorithmCodeResponse,
    summary="Get the current code for an algorithm in a language",
)
async def get_current_code(
    slug: str = Path(..., min_length=1, max_length=128),
    language: str = Query(
        ..., min_length=1, max_length=32, description="Language slug."
    ),
    service: CatalogServiceProtocol = Depends(get_catalog_service),
) -> AlgorithmCodeResponse:
    """Resolve slug → algorithm_id, then return the current
    code in ``language``.

    The two-step resolution (slug → id, id + language → code)
    is intentional: the partial UNIQUE index on
    ``(algorithm_id, language) WHERE is_current = TRUE`` is
    keyed by id, not slug, so we keep the index lookup while
    still exposing the human-friendly slug in the URL.
    """
    detail = await service.get_algorithm_by_slug(slug)
    return await service.get_current_code(detail.id, language)


# ---------------------------------------------------------------------------
# Code version history
# ---------------------------------------------------------------------------


@router.get(
    "/{slug}/code/versions",
    response_model=list[AlgorithmCodeResponse],
    summary="List code versions for an algorithm",
)
async def list_code_versions(
    slug: str = Path(..., min_length=1, max_length=128),
    language: str | None = Query(
        None, min_length=1, max_length=32, description="Filter to one language."
    ),
    is_current: bool | None = Query(
        None, description="Filter to current-only or historical-only."
    ),
    service: CatalogServiceProtocol = Depends(get_catalog_service),
) -> list[AlgorithmCodeResponse]:
    """Return the full version history for ``slug``.

    The current-row lookup uses the algorithm_id + language
    partial UNIQUE index. The version history is a separate
    query (no partial filter) and is paginated server-side
    only when the response grows past a sensible threshold —
    that paginator lands in B3.11.
    """
    detail = await service.get_algorithm_by_slug(slug)
    filters = build_code_version_filters(
        algorithm_id=str(detail.id),
        language=language,
        is_current=is_current,
    )
    page = await service.list_code_versions(filters)
    return list(page.items)


__all__ = ["router"]
