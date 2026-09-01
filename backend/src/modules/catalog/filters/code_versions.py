"""AlgorithmCodeVersionFilters — query params for code-version lists.

Code versions are a per-algorithm detail; the public catalog
typically shows just the current version (one per language).
The list endpoint exists for "show all v1..vN for an algorithm"
admin views, so it includes version range filtering.

Refs: ALGOVISION_BACKEND_PLAN §7 (Filtering)
Refs: DATABASE_DESIGN.md §1 (algorithm_code_versions)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from src.shared.filters import SortOrder
from src.shared.pagination import DEFAULT_PAGE_SIZE, Pagination


class AlgorithmCodeVersionSortField(StrEnum):
    """Sortable fields for the code-versions list."""

    VERSION = "version"
    CREATED_AT = "created_at"
    LANGUAGE = "language"


@dataclass(frozen=True, slots=True)
class AlgorithmCodeVersionFilters:
    """Parsed query parameters for code-version list endpoints."""

    algorithm_id: str | None = None  # UUID, str for filter parsing
    language: str | None = None
    is_current: bool | None = None
    version_min: int | None = None
    version_max: int | None = None
    sort_by: AlgorithmCodeVersionSortField = AlgorithmCodeVersionSortField.VERSION
    sort_order: SortOrder = SortOrder.DESC
    pagination: Pagination = field(
        default_factory=lambda: Pagination(page=1, page_size=DEFAULT_PAGE_SIZE)
    )
