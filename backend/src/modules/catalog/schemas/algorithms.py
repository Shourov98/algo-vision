"""Pydantic schemas for the algorithms API.

Includes both the summary response (used in list endpoints)
and the detail response (used by ``GET /algorithms/{slug}``
which also exposes the current code in a chosen language).

Why two responses
-----------------
The list endpoint is on the hot path — it must be cheap to
serialize. We omit code blocks and topic tags from the
summary so list responses stay small. The detail endpoint
embeds the requested language's current code so the frontend
can render without a second round-trip.

Refs: ALGOVISION_BACKEND_PLAN.md §3.7 (B3.7 schemas),
      §3.8 (B3.8 routers), §3.13 (algorithm detail)
Refs: PUKU_BACKEND_AGENT.md §8
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# Difficulty values are stored as lowercase strings in the DB
# (DIFFICULTY_VALUES in models/algorithm.py). Using ``Literal``
# here lets OpenAPI publish the exact set without an enum
# dependency on the ORM side.
Difficulty = Literal["easy", "medium", "hard"]


class TopicSummary(BaseModel):
    """Compact topic representation embedded in the algorithm detail.

    Topics can be listed independently via ``GET /topics``;
    this shape is what the frontend renders inline on the
    detail page (chips / tags).
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    slug: str
    name: str


class CategorySummary(BaseModel):
    """Compact category representation embedded in the algorithm detail."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    slug: str
    name: str


class AlgorithmSummaryResponse(BaseModel):
    """List-row representation.

    Returned by ``GET /algorithms``. Deliberately omits
    description, complexity, code, and topic list so list
    responses stay small and serialise fast.
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    slug: str
    name: str
    difficulty: Difficulty
    visualization_type: str
    category_id: UUID
    is_published: bool
    created_at: datetime
    updated_at: datetime


class AlgorithmDetailResponse(BaseModel):
    """Detail representation.

    Returned by ``GET /algorithms/{slug}``. Includes the
    category summary and full topic list so the frontend
    does not need a second round-trip to render the detail
    page. The current code in the requested language is
    included via a separate ``AlgorithmCodeResponse`` (so
    the schema stays composable for multi-language views
    later).
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    slug: str
    name: str
    description: str | None = None
    difficulty: Difficulty
    visualization_type: str
    best_time: str | None = None
    average_time: str | None = None
    worst_time: str | None = None
    space_complexity: str | None = None
    is_published: bool
    category: CategorySummary
    topics: list[TopicSummary] = Field(
        default_factory=list,
        description="Topics tagged on this algorithm.",
    )
    current_code: AlgorithmCodeResponse | None = Field(
        default=None,
        description=(
            "Current code for the requested language. Null when no code "
            "version exists in that language yet."
        ),
    )
    created_at: datetime
    updated_at: datetime


class AlgorithmCodeResponse(BaseModel):
    """Code version representation.

    Returned:
    - embedded in ``AlgorithmDetailResponse`` (current code)
    - by ``GET /algorithms/{slug}/code?language=...`` (explicit fetch)
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    algorithm_id: UUID
    language: str = Field(..., min_length=1, max_length=32)
    version: int = Field(..., ge=1)
    source_code: str
    is_current: bool
    created_at: datetime


class AlgorithmListResponse(BaseModel):
    """Paginated envelope for algorithm listings."""

    items: list[AlgorithmSummaryResponse]
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    total: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=1)


# Resolve the forward reference for AlgorithmDetailResponse.
AlgorithmDetailResponse.model_rebuild()


__all__ = [
    "AlgorithmCodeResponse",
    "AlgorithmDetailResponse",
    "AlgorithmListResponse",
    "AlgorithmSummaryResponse",
    "CategorySummary",
    "Difficulty",
    "TopicSummary",
]
