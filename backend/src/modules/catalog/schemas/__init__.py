"""Catalog HTTP schemas.

Pydantic models for every catalog endpoint (B3.8). Per-entity
files keep each under 100 lines; this ``__init__`` re-exports
the public names so callers can do
``from src.modules.catalog.schemas import AlgorithmResponse``.
"""

from __future__ import annotations

from src.modules.catalog.schemas.algorithms import (
    AlgorithmCodeResponse,
    AlgorithmDetailResponse,
    AlgorithmListResponse,
    AlgorithmSummaryResponse,
    CategorySummary,
    Difficulty,
    TopicSummary,
)
from src.modules.catalog.schemas.categories import (
    CategoryListResponse,
    CategoryResponse,
)
from src.modules.catalog.schemas.data_structures import (
    DataStructureListResponse,
    DataStructureResponse,
)
from src.modules.catalog.schemas.topics import (
    TopicListResponse,
    TopicResponse,
)

__all__ = [
    "AlgorithmCodeResponse",
    "AlgorithmDetailResponse",
    "AlgorithmListResponse",
    "AlgorithmSummaryResponse",
    "CategoryListResponse",
    "CategoryResponse",
    "CategorySummary",
    "DataStructureListResponse",
    "DataStructureResponse",
    "Difficulty",
    "TopicListResponse",
    "TopicResponse",
    "TopicSummary",
]
