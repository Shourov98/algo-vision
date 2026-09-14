"""Common filter builders for the progress router.

Progress filters are simple (status + sort + pagination).
One builder per entity mirrors the catalog / problems
convention (``ProblemFilters`` / ``CompanyFilters``).

Refs: ALGOVISION_BACKEND_PLAN.md §7 (Filtering)
"""

from __future__ import annotations

from fastapi import Query

from src.modules.progress.filters import (
    AlgorithmProgressFilters,
    ProblemProgressFilters,
    ProgressSortField,
)
from src.shared.filters import SortOrder
from src.shared.pagination import DEFAULT_PAGE_SIZE, Pagination


def build_algorithm_progress_filters(
    status: str | None = Query(
        default=None,
        description="Filter by status (not_started|in_progress|completed).",
    ),
    sort_by: ProgressSortField = Query(default=ProgressSortField.LAST_VIEWED_AT),
    sort_order: SortOrder = Query(default=SortOrder.DESC),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1),
) -> AlgorithmProgressFilters:
    """Parse query string into AlgorithmProgressFilters."""
    return AlgorithmProgressFilters(
        status=status,
        sort_by=sort_by,
        sort_order=sort_order,
        pagination=Pagination(page=page, page_size=page_size),
    )


def build_problem_progress_filters(
    status: str | None = Query(
        default=None,
        description="Filter by status (not_started|in_progress|completed).",
    ),
    sort_by: ProgressSortField = Query(default=ProgressSortField.LAST_VIEWED_AT),
    sort_order: SortOrder = Query(default=SortOrder.DESC),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1),
) -> ProblemProgressFilters:
    """Parse query string into ProblemProgressFilters."""
    return ProblemProgressFilters(
        status=status,
        sort_by=sort_by,
        sort_order=sort_order,
        pagination=Pagination(page=page, page_size=page_size),
    )


__all__ = [
    "build_algorithm_progress_filters",
    "build_problem_progress_filters",
]
