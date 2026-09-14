"""Shared router helpers for the catalog module.

Houses query-string → filter parsing so every catalog router
file uses the same construction. Routers stay focused on
endpoint shape; the parsing logic lives here next to the
filter dataclasses it constructs.

Refs: PUKU_BACKEND_AGENT.md §7 (Router Conventions)
"""

from __future__ import annotations

from fastapi import Query

from src.modules.catalog.filters.algorithms import (
    AlgorithmFilters,
    AlgorithmSortField,
)
from src.modules.catalog.filters.categories import (
    CategoryFilters,
    CategorySortField,
)
from src.modules.catalog.filters.code_versions import (
    AlgorithmCodeVersionFilters,
    AlgorithmCodeVersionSortField,
)
from src.modules.catalog.filters.data_structures import (
    DataStructureFilters,
    DataStructureSortField,
)
from src.modules.catalog.filters.topics import TopicFilters, TopicSortField
from src.shared.filters import SortOrder
from src.shared.pagination import Pagination

# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------


def build_category_filters(
    search: str | None = None,
    sort_by: CategorySortField = CategorySortField.SORT_ORDER,
    sort_order: SortOrder = SortOrder.ASC,
    page: int = Query(1, ge=1, description="1-indexed page number."),
    page_size: int = Query(
        20, ge=1, le=100, description="Items per page (max 100)."
    ),
) -> CategoryFilters:
    """Parse query-string params into ``CategoryFilters``.

    Default sort is ``sort_order`` ASC so categories appear
    in their admin-defined display order.
    """
    return CategoryFilters(
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        pagination=Pagination.from_query(page, page_size),
    )


# ---------------------------------------------------------------------------
# Topics
# ---------------------------------------------------------------------------


def build_topic_filters(
    search: str | None = None,
    sort_by: TopicSortField = TopicSortField.NAME,
    sort_order: SortOrder = SortOrder.ASC,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> TopicFilters:
    return TopicFilters(
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        pagination=Pagination.from_query(page, page_size),
    )


# ---------------------------------------------------------------------------
# Algorithms
# ---------------------------------------------------------------------------


def build_algorithm_filters(
    search: str | None = None,
    category: str | None = None,
    topic: str | None = None,
    difficulty: str | None = None,
    is_published: bool = True,
    sort_by: AlgorithmSortField = AlgorithmSortField.NAME,
    sort_order: SortOrder = SortOrder.ASC,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> AlgorithmFilters:
    """Parse ``GET /algorithms`` query params into ``AlgorithmFilters``.

    ``is_published`` defaults to True (public catalog). Admin
    views pass ``?is_published=false`` to see drafts — that
    flow lands with the staff role in a later phase; the
    parameter is exposed now so the schema is stable.
    """
    return AlgorithmFilters(
        search=search,
        category=category,
        topic=topic,
        difficulty=difficulty,
        is_published=is_published,
        sort_by=sort_by,
        sort_order=sort_order,
        pagination=Pagination.from_query(page, page_size),
    )


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


def build_data_structure_filters(
    search: str | None = None,
    difficulty: str | None = None,
    sort_by: DataStructureSortField = DataStructureSortField.NAME,
    sort_order: SortOrder = SortOrder.ASC,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> DataStructureFilters:
    return DataStructureFilters(
        search=search,
        difficulty=difficulty,
        sort_by=sort_by,
        sort_order=sort_order,
        pagination=Pagination.from_query(page, page_size),
    )


# ---------------------------------------------------------------------------
# Code versions
# ---------------------------------------------------------------------------


def build_code_version_filters(
    algorithm_id: str | None = None,
    language: str | None = None,
    is_current: bool | None = None,
    version_min: int | None = None,
    version_max: int | None = None,
    sort_by: AlgorithmCodeVersionSortField = (
        AlgorithmCodeVersionSortField.VERSION
    ),
    sort_order: SortOrder = SortOrder.DESC,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> AlgorithmCodeVersionFilters:
    """Parse ``GET /algorithms/{slug}/code/versions`` query params.

    ``algorithm_id`` arrives as a string and is parsed to a
    UUID here (where the validation error belongs — a
    malformed UUID is a 422 from the router, not a 500 from
    the SQL layer).
    """
    from uuid import UUID

    algo_uuid: UUID | None = None
    if algorithm_id is not None:
        algo_uuid = UUID(algorithm_id)
    return AlgorithmCodeVersionFilters(
        algorithm_id=algo_uuid,
        language=language,
        is_current=is_current,
        version_min=version_min,
        version_max=version_max,
        sort_by=sort_by,
        sort_order=sort_order,
        pagination=Pagination.from_query(page, page_size),
    )


__all__ = [
    "build_algorithm_filters",
    "build_category_filters",
    "build_code_version_filters",
    "build_data_structure_filters",
    "build_topic_filters",
]
