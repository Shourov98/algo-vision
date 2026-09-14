"""Shared router helpers for the problems module.

Houses query-string -> filter parsing so every problems
router file uses the same construction. Routers stay
focused on endpoint shape; the parsing logic lives here
next to the filter dataclasses it constructs.

Refs: PUKU_BACKEND_AGENT.md §7 (Router Conventions)
"""

from __future__ import annotations

from fastapi import Query

from src.modules.problems.filters.companies import (
    CompanyFilters,
    CompanySortField,
)
from src.modules.problems.filters.problems import (
    ProblemFilters,
    ProblemSortField,
)
from src.shared.filters import SortOrder
from src.shared.pagination import Pagination


def build_problem_filters(
    search: str | None = None,
    difficulty: str | None = Query(
        None,
        description="Filter by difficulty. Must be one of: easy, medium, hard.",
    ),
    topic: str | None = Query(
        None, description="Filter by topic slug."
    ),
    company: str | None = Query(
        None, description="Filter by company slug."
    ),
    visualization_available: bool | None = Query(
        None,
        description=(
            "Filter by the visualization_available flag. "
            "true -> only visualizable problems; "
            "false -> only editor-only problems; "
            "omitted -> no filter."
        ),
    ),
    sort_by: ProblemSortField = ProblemSortField.UPDATED_AT,
    sort_order: SortOrder = SortOrder.DESC,
    page: int = Query(1, ge=1, description="1-indexed page number."),
    page_size: int = Query(
        20, ge=1, le=100, description="Items per page (max 100)."
    ),
) -> ProblemFilters:
    """Parse ``GET /problems`` query params into ``ProblemFilters``.

    Default sort is ``updated_at`` DESC so the listing page
    surfaces the most recently added problem first — the
    interview-preparation surface is more like a feed than
    a browsable catalog.
    """
    return ProblemFilters(
        search=search,
        difficulty=difficulty,
        topic=topic,
        company=company,
        visualization_available=visualization_available,
        sort_by=sort_by,
        sort_order=sort_order,
        pagination=Pagination.from_query(page, page_size),
    )


def build_company_filters(
    search: str | None = None,
    sort_by: CompanySortField = CompanySortField.NAME,
    sort_order: SortOrder = SortOrder.ASC,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> CompanyFilters:
    """Parse ``GET /problems/companies`` query params."""
    return CompanyFilters(
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        pagination=Pagination.from_query(page, page_size),
    )


__all__ = [
    "build_company_filters",
    "build_problem_filters",
]
