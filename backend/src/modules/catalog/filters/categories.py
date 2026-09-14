"""CategoryFilters — query parameters for the categories endpoint.

Categories are a small, flat set (<50 rows per DATABASE_DESIGN
§2). The only sensible filters are search-by-name and sort by
display order vs alphabetical.

Refs: ALGOVISION_BACKEND_PLAN §7 (Filtering)
Refs: DATABASE_DESIGN.md §1 (algorithm_categories)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from src.shared.filters import SortOrder
from src.shared.pagination import DEFAULT_PAGE_SIZE, Pagination


class CategorySortField(StrEnum):
    """Sortable fields for the categories list."""

    SORT_ORDER = "sort_order"
    NAME = "name"


@dataclass(frozen=True, slots=True)
class CategoryFilters:
    """Parsed query parameters for ``GET /algorithms/categories``."""

    search: str | None = None
    sort_by: CategorySortField = CategorySortField.SORT_ORDER
    sort_order: SortOrder = SortOrder.ASC
    pagination: Pagination = field(
        default_factory=lambda: Pagination(page=1, page_size=DEFAULT_PAGE_SIZE)
    )
