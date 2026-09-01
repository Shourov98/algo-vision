"""Pydantic schemas for the topics API.

Topics are deliberately minimal (slug + name + id). The
``topics`` table has no description column or created_at —
topics are static catalog content seeded once (DATABASE_DESIGN
§1), so no audit timestamps are kept.

Refs: ALGOVISION_BACKEND_PLAN.md §3.7 (B3.7 schemas)
Refs: PUKU_BACKEND_AGENT.md §8
Refs: DATABASE_DESIGN.md §1 (topics)
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TopicResponse(BaseModel):
    """Public-safe topic representation.

    Returned by:
    - ``GET /topics`` (paginated)
    - ``GET /topics/{slug}``
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    slug: str
    name: str


class TopicListResponse(BaseModel):
    """Paginated envelope for topic listings."""

    items: list[TopicResponse]
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    total: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=1)


__all__ = ["TopicListResponse", "TopicResponse"]
