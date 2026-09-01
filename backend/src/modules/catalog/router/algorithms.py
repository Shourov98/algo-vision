"""HTTP endpoints for algorithms.

Endpoints
---------
- ``GET    /api/v1/algorithms``                  — list (paginated)
- ``GET    /api/v1/algorithms/{slug}``           — detail
- ``GET    /api/v1/algorithms/{slug}/code``      — current code in
                                                  a given language
- ``GET    /api/v1/algorithms/{slug}/code/versions`` — version history

Caching
-------
List + detail set ``ETag`` (weak, keyed on max(updated_at)
+ filter hash) and ``Cache-Control: public, max-age=300``.
When the client sends ``If-None-Match`` matching the
current ETag, the router returns ``304 Not Modified`` with
no body — see ``router/_etag.py`` for the algorithm.

Detail reads dispatch ``ItemViewedEvent`` when a user is
authenticated so progress can attribute the view.

Refs: ALGOVISION_BACKEND_PLAN.md §3.9 (B3.9 ETag), §3.12, §3.13
Refs: PUKU_BACKEND_AGENT.md §7
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Query, Request, Response

from src.modules.catalog.dependencies import (
    get_catalog_service,
    get_optional_user,
)
from src.modules.catalog.filters import AlgorithmFilters
from src.modules.catalog.router._common import (
    build_algorithm_filters,
    build_code_version_filters,
)
from src.modules.catalog.router._etag import (
    etag_from_filters_and_max_updated_at,
    etag_from_updated_at,
    filter_hash,
    max_updated_at_from,
)
from src.modules.catalog.schemas import (
    AlgorithmCodeResponse,
    AlgorithmDetailResponse,
    AlgorithmListResponse,
)
from src.modules.catalog.service import CatalogServiceProtocol
from src.modules.users.models import User

router = APIRouter(prefix="/api/v1/algorithms", tags=["algorithms"])

# Cache-Control header for algorithm GETs. ``public`` lets
# shared caches (CDN, reverse proxy) cache the response;
# ``max-age=300`` is the freshness window per the plan
# (ALGOVISION_BACKEND_PLAN §3.9 / §7). The ETag is the
# revalidation key — max-age just bounds how often a
# conditional GET fires.
CACHE_CONTROL_ALGORITHMS = "public, max-age=300"

# Salt prefixes keep a single ``updated_at`` value from
# producing identical ETags across endpoints (e.g. the list
# endpoint and the detail endpoint must not share an ETag).
ETAG_SALT_LIST = "algorithms:list:"
ETAG_SALT_DETAIL = "algorithms:detail:"


def _etag_matches(client_tag: str | None, current_tag: str) -> bool:
    """RFC 7232 §3.2 weak comparison.

    Clients send a comma-separated list of ETags in
    ``If-None-Match``; each entry may be the wildcard ``*``
    or a (weak) ETag. We use weak comparison because our
    ETags are weak (``W/"..."``); per spec the comparison
    strips the ``W/`` prefix on both sides.
    """
    if client_tag is None:
        return False
    current_opaque = current_tag.removeprefix("W/")
    for raw in client_tag.split(","):
        candidate = raw.strip()
        if not candidate:
            continue
        if candidate == "*":
            return True
        if candidate.removeprefix("W/") == current_opaque:
            return True
    return False


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=AlgorithmListResponse,
    summary="List algorithms",
)
async def list_algorithms(
    request: Request,
    response: Response,
    filters: AlgorithmFilters = Depends(build_algorithm_filters),
    service: CatalogServiceProtocol = Depends(get_catalog_service),
) -> Response | AlgorithmListResponse:
    """List algorithms matching ``filters`` with HTTP caching.

    Conditional GET semantics: when the request carries an
    ``If-None-Match`` header matching the current ETag we
    return ``304 Not Modified`` with no body — saves the
    JSON serialization round-trip.

    The ETag is derived from the filter signature plus the
    max ``updated_at`` across the page (see
    ``router/_etag.py`` for the rationale).
    """
    page = await service.list_algorithms(filters)
    etag = etag_from_filters_and_max_updated_at(
        filter_hash=filter_hash(filters),
        max_updated_at=max_updated_at_from(page.items),
    )
    if _etag_matches(
        request.headers.get("if-none-match"),
        etag,
    ):
        return Response(
            status_code=304,
            headers={
                "ETag": etag,
                "Cache-Control": CACHE_CONTROL_ALGORITHMS,
            },
        )
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = CACHE_CONTROL_ALGORITHMS
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
    request: Request,
    response: Response,
    slug: str = Path(..., min_length=1, max_length=128),
    service: CatalogServiceProtocol = Depends(get_catalog_service),
    user: User | None = Depends(get_optional_user),
) -> Response | AlgorithmDetailResponse:
    """Return the algorithm with ``slug`` or raise 404/403.

    Conditional GET: when ``If-None-Match`` matches the
    ETag derived from ``detail.updated_at``, return
    ``304 Not Modified`` instead of the JSON body.
    """
    detail = await service.get_algorithm_by_slug(
        slug, user_id=user.id if user is not None else None
    )
    etag = etag_from_updated_at(
        detail.updated_at, salt=ETAG_SALT_DETAIL
    )
    if _etag_matches(
        request.headers.get("if-none-match"),
        etag,
    ):
        return Response(
            status_code=304,
            headers={
                "ETag": etag,
                "Cache-Control": CACHE_CONTROL_ALGORITHMS,
            },
        )
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = CACHE_CONTROL_ALGORITHMS
    return detail


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
