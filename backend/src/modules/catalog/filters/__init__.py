"""Typed filter dataclasses for the catalog domain.

Each filter class is a frozen, slotted dataclass with explicit
fields — routers parse query params into one of these and hand
it to the matching repository.

Why a package (per-entity files)
--------------------------------
Same split-by-responsibility rationale as ``models/``:
- ``categories.py`` : CategoryFilters
- ``topics.py``    : TopicFilters
- ``algorithms.py`` : AlgorithmFilters (the largest; search,
                       difficulty, category slug, topic slug,
                       is_published, sort, pagination)
- ``data_structures.py`` : DataStructureFilters
- ``code_versions.py``   : AlgorithmCodeVersionFilters

Refs: ALGOVISION_BACKEND_PLAN §7 (Filtering)
Refs: PUKU_BACKEND_AGENT §8.3 (Filters)
"""

from src.modules.catalog.filters.algorithms import (
    AlgorithmFilters,
    AlgorithmSortField,
)
from src.modules.catalog.filters.categories import CategoryFilters, CategorySortField
from src.modules.catalog.filters.code_versions import AlgorithmCodeVersionFilters
from src.modules.catalog.filters.data_structures import (
    DataStructureFilters,
    DataStructureSortField,
)
from src.modules.catalog.filters.topics import TopicFilters, TopicSortField

__all__ = [
    "AlgorithmCodeVersionFilters",
    "AlgorithmFilters",
    "AlgorithmSortField",
    "CategoryFilters",
    "CategorySortField",
    "DataStructureFilters",
    "DataStructureSortField",
    "TopicFilters",
    "TopicSortField",
]
