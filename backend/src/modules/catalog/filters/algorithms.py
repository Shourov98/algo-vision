"""AlgorithmFilters — query parameters for the algorithms list.

The most complex filter in the catalog: every documented
query parameter on ``GET /algorithms`` lives here. The router
constructs this from query strings; the repository consumes it.

Why filter by slug, not by FK id
--------------------------------
Clients never see UUIDs (server-generated, opaque). They have
a stable URL key (slug). Filtering by category_id / topic_id
would force a separate slug→id lookup that the router would
have to do for every request. Filtering by slug lets the
repository do the join internally.

Why is_published defaults to True
---------------------------------
The public catalog only shows published algorithms. Admin
views (future) will pass is_published=False to see drafts.
The default matches the public API contract.

Refs: ALGOVISION_BACKEND_PLAN §7 (Filtering), §8.3 (Filters)
Refs: DATABASE_DESIGN.md §1 (algorithms), §5 (indexes)
Refs: DATABASE_DESIGN.md §8.1 (Q1: published-algorithms query)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from src.shared.filters import SortOrder
from src.shared.pagination import DEFAULT_PAGE_SIZE, Pagination


class AlgorithmSortField(StrEnum):
    """Sortable fields for the algorithms list.

    NAME is the default — alphabetical sort is what users
    expect on a catalog page. UPDATED_AT powers the
    "recently updated" view.
    """

    NAME = "name"
    UPDATED_AT = "updated_at"
    CREATED_AT = "created_at"


@dataclass(frozen=True, slots=True)
class AlgorithmFilters:
    """Parsed query parameters for ``GET /algorithms``."""

    search: str | None = None
    category: str | None = None  # category slug
    topic: str | None = None  # topic slug
    difficulty: str | None = None  # "easy" | "medium" | "hard"
    is_published: bool = True
    sort_by: AlgorithmSortField = AlgorithmSortField.NAME
    sort_order: SortOrder = SortOrder.ASC
    pagination: Pagination = field(
        default_factory=lambda: Pagination(page=1, page_size=DEFAULT_PAGE_SIZE)
    )
