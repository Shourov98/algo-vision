"""Filters for the progress endpoints.

Parsed from query strings by the router (B5.7), consumed by
the repository (B5.5). One frozen dataclass per entity,
following the catalog / problems convention.

Why filter only by status (no slug, no topic)
--------------------------------------------
Progress is per-user; there is no public catalog-style
listing. The only useful filter is "show me my in-progress
items" vs "show me my completed items". Slugs/topics
would just complicate the URL without helping the
dashboard's render.

Refs: ALGOVISION_BACKEND_PLAN.md §7 (Filtering)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from src.shared.filters import SortOrder
from src.shared.pagination import DEFAULT_PAGE_SIZE, Pagination


class ProgressSortField(StrEnum):
    """Sortable fields for progress listings.

    Default sort is LAST_VIEWED_AT DESC — "what did I most
    recently touch?" — because the dashboard's "recently
    viewed" sidebar uses the same ordering (and shares the
    last_viewed_at column).
    """

    LAST_VIEWED_AT = "last_viewed_at"
    FIRST_VIEWED_AT = "first_viewed_at"
    COMPLETED_AT = "completed_at"


@dataclass(frozen=True, slots=True)
class AlgorithmProgressFilters:
    """Parsed query parameters for ``GET /progress/algorithms``."""

    status: str | None = None  # "not_started" | "in_progress" | "completed"
    sort_by: ProgressSortField = ProgressSortField.LAST_VIEWED_AT
    sort_order: SortOrder = SortOrder.DESC
    pagination: Pagination = field(
        default_factory=lambda: Pagination(page=1, page_size=DEFAULT_PAGE_SIZE)
    )


@dataclass(frozen=True, slots=True)
class ProblemProgressFilters:
    """Parsed query parameters for ``GET /progress/problems``."""

    status: str | None = None
    sort_by: ProgressSortField = ProgressSortField.LAST_VIEWED_AT
    sort_order: SortOrder = SortOrder.DESC
    pagination: Pagination = field(
        default_factory=lambda: Pagination(page=1, page_size=DEFAULT_PAGE_SIZE)
    )


__all__ = [
    "AlgorithmProgressFilters",
    "ProblemProgressFilters",
    "ProgressSortField",
]
