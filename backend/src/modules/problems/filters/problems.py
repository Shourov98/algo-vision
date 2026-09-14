"""ProblemFilters — query parameters for the problems list.

Parsed from the ``GET /problems`` query string by the router
(B4.8), consumed by the repository (B4.5).

Why filter by slug, not by FK id
--------------------------------
Mirrors the catalog algorithm filter: clients only see
slugs, not UUIDs. Filtering by topic_slug / company_slug lets
the repository do the join internally — the router never
sees a UUID translation.

Why ``difficulty`` is a plain ``str | None`` (not a Literal)
-------------------------------------------------------------
Keeping the wire format loose lets new vocabulary land in
the DB CHECK constraint first (with a migration) without
breaking the API. The repository validates against
``DIFFICULTY_VALUES`` and returns the raw rows; a malformed
value would still be rejected by the CHECK constraint at
insert time and by the migration tests. The Pydantic
schemas re-tighten the type on the response side via the
``Difficulty`` literal.

Why sort defaults to ``UPDATED_AT``
-----------------------------------
The interview-preparation surface benefits from "recently
added" surfacing — staff will add new problems during
the interview-prep phase and want them to bubble up
without manual ordering. The catalog uses alphabetical
default because the catalog is browsable; the problems
list is more like a feed.

Refs: ALGOVISION_BACKEND_PLAN.md §7 (Filtering)
Refs: DATABASE_DESIGN.md §1 (problems, problem_topics,
       problem_companies)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from src.shared.filters import SortOrder
from src.shared.pagination import DEFAULT_PAGE_SIZE, Pagination


class ProblemSortField(StrEnum):
    """Sortable fields for the problems list."""

    TITLE = "title"
    UPDATED_AT = "updated_at"
    CREATED_AT = "created_at"


@dataclass(frozen=True, slots=True)
class ProblemFilters:
    """Parsed query parameters for ``GET /problems``."""

    search: str | None = None
    difficulty: str | None = None  # "easy" | "medium" | "hard"
    topic: str | None = None  # topic slug filter
    company: str | None = None  # company slug filter
    visualization_available: bool | None = None
    sort_by: ProblemSortField = ProblemSortField.UPDATED_AT
    sort_order: SortOrder = SortOrder.DESC
    pagination: Pagination = field(
        default_factory=lambda: Pagination(page=1, page_size=DEFAULT_PAGE_SIZE)
    )


__all__ = ["ProblemFilters", "ProblemSortField"]
