"""CompanyFilters — query parameters for the companies list.

Companies are a tiny, flat set (<200 rows per
DATABASE_DESIGN §3). The only sensible filters are
search-by-name and sort by display name.

Why this is a separate file from ``problems.py``
------------------------------------------------
Per-entity filter files keep each filter's dependencies
explicit. Companies are independent of problems (the
problems repo references companies but the companies
repo has no knowledge of problems), so the dependency
direction is problems → companies, not the other way.

Refs: ALGOVISION_BACKEND_PLAN §7 (Filtering)
Refs: DATABASE_DESIGN.md §1 (companies)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from src.shared.filters import SortOrder
from src.shared.pagination import DEFAULT_PAGE_SIZE, Pagination


class CompanySortField(StrEnum):
    """Sortable fields for the companies list."""

    NAME = "name"
    SLUG = "slug"


@dataclass(frozen=True, slots=True)
class CompanyFilters:
    """Parsed query parameters for ``GET /problems/companies``."""

    search: str | None = None
    sort_by: CompanySortField = CompanySortField.NAME
    sort_order: SortOrder = SortOrder.ASC
    pagination: Pagination = field(
        default_factory=lambda: Pagination(page=1, page_size=DEFAULT_PAGE_SIZE)
    )


__all__ = ["CompanyFilters", "CompanySortField"]
