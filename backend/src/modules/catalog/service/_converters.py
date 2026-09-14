"""ORM-to-response converters for the catalog module.

These functions are the boundary between the persistence layer
(SQLAlchemy ORM rows) and the HTTP layer (Pydantic response
schemas). They live in the service package — NOT the routers
— so the rule "ORM rows never escape the service layer" is
enforced by where the code physically lives, not by a code
review checklist.

Why per-entity functions instead of one generic helper
------------------------------------------------------
The conversion is straightforward today but is the obvious
place for cross-cutting changes (e.g. embedding derived
fields, transforming dates to client timezone, redacting
internal fields). One helper per entity keeps that future
diff small and localized.

Refs: PUKU_BACKEND_AGENT.md §3.1 (ORM never escapes service),
      §8 (Pydantic schemas)
"""

from __future__ import annotations

from src.modules.catalog.models import (
    Algorithm,
    AlgorithmCodeVersion,
    Category,
    DataStructure,
    Topic,
)
from src.modules.catalog.schemas import (
    AlgorithmCodeResponse,
    AlgorithmDetailResponse,
    AlgorithmSummaryResponse,
    CategoryResponse,
    DataStructureResponse,
    TopicResponse,
)


def category_to_response(category: Category) -> CategoryResponse:
    """Convert an ORM Category row to a public-safe response."""
    return CategoryResponse.model_validate(category)


def topic_to_response(topic: Topic) -> TopicResponse:
    return TopicResponse.model_validate(topic)


def data_structure_to_response(ds: DataStructure) -> DataStructureResponse:
    return DataStructureResponse.model_validate(ds)


def algorithm_to_summary(
    algorithm: Algorithm,
) -> AlgorithmSummaryResponse:
    return AlgorithmSummaryResponse.model_validate(algorithm)


def code_version_to_response(
    cv: AlgorithmCodeVersion,
) -> AlgorithmCodeResponse:
    return AlgorithmCodeResponse.model_validate(cv)


def algorithm_to_detail(algorithm: Algorithm) -> AlgorithmDetailResponse:
    """Build the detail response from an Algorithm row.

    Placeholder shape used until the B3.8 detail repo helper
    (with category/topic selectinload) lands. The category and
    topics fields are populated from the algorithm row itself
    if the relationships are loaded; otherwise the caller
    (router) is responsible for supplying them via a separate
    fetch. This keeps B3.7 from changing the repository's
    ``get_by_slug`` contract.

    The category summary uses the FK column to satisfy the
    required ``category`` field; slug/name are blank until the
    full detail loader lands.
    """
    return AlgorithmDetailResponse.model_validate(
        {
            "id": algorithm.id,
            "slug": algorithm.slug,
            "name": algorithm.name,
            "description": algorithm.description,
            "difficulty": algorithm.difficulty,
            "visualization_type": algorithm.visualization_type,
            "best_time": algorithm.best_time,
            "average_time": algorithm.average_time,
            "worst_time": algorithm.worst_time,
            "space_complexity": algorithm.space_complexity,
            "is_published": algorithm.is_published,
            "category": {
                "id": algorithm.category_id,
                "slug": "",
                "name": "",
            },
            "topics": [],
            "current_code": None,
            "created_at": algorithm.created_at,
            "updated_at": algorithm.updated_at,
        }
    )


__all__ = [
    "algorithm_to_detail",
    "algorithm_to_summary",
    "category_to_response",
    "code_version_to_response",
    "data_structure_to_response",
    "topic_to_response",
]
