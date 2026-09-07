"""TopicFilters — query parameters for the topics endpoint.

Topics are a tiny vocabulary (<100 rows per DATABASE_DESIGN §2)
shared between algorithms and problems. Filters are
intentionally minimal: search by name, plus sort.

Refs: ALGOVISION_BACKEND_PLAN §7 (Filtering)
Refs: DATABASE_DESIGN.md §1 (topics)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from src.shared.filters import SortOrder
from src.shared.pagination import DEFAULT_PAGE_SIZE, Pagination


class TopicSortField(StrEnum):
    """Sortable fields for the topics list."""

    NAME = "name"
    SLUG = "slug"


@dataclass(frozen=True, slots=True)
class TopicFilters:
    """Parsed query parameters for ``GET /topics``."""

    search: str | None = None
    sort_by: TopicSortField = TopicSortField.NAME
    sort_order: SortOrder = SortOrder.ASC
    pagination: Pagination = field(
        default_factory=lambda: Pagination(page=1, page_size=DEFAULT_PAGE_SIZE)
    )
