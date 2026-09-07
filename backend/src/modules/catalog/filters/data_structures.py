"""DataStructureFilters — query parameters for /data-structures.

A small flat list (<50 rows per DATABASE_DESIGN §2). Filters:
search by name, difficulty, plus sort.

Refs: ALGOVISION_BACKEND_PLAN §7 (Filtering)
Refs: DATABASE_DESIGN.md §1 (data_structures)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from src.shared.filters import SortOrder
from src.shared.pagination import DEFAULT_PAGE_SIZE, Pagination


class DataStructureSortField(StrEnum):
    """Sortable fields for the data-structures list."""

    NAME = "name"
    SLUG = "slug"


@dataclass(frozen=True, slots=True)
class DataStructureFilters:
    """Parsed query parameters for ``GET /data-structures``."""

    search: str | None = None
    difficulty: str | None = None
    sort_by: DataStructureSortField = DataStructureSortField.NAME
    sort_order: SortOrder = SortOrder.ASC
    pagination: Pagination = field(
        default_factory=lambda: Pagination(page=1, page_size=DEFAULT_PAGE_SIZE)
    )
