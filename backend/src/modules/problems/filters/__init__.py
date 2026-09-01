"""Problems module filters - package root.

Per-entity filter dataclasses. Re-exports the public names
so callers can do
``from src.modules.problems.filters import ProblemFilters``.
"""

from __future__ import annotations

from src.modules.problems.filters.companies import (
    CompanyFilters,
    CompanySortField,
)
from src.modules.problems.filters.problems import (
    ProblemFilters,
    ProblemSortField,
)

__all__ = [
    "CompanyFilters",
    "CompanySortField",
    "ProblemFilters",
    "ProblemSortField",
]
