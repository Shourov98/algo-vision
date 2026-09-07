"""Pydantic schemas for the data-structures API.

Mirrors the algorithms API shape but without the versioned-
code detail endpoint — data structures are not code-versioned.

Refs: ALGOVISION_BACKEND_PLAN.md §3.7 (B3.7 schemas),
      §3.15 (data-structure endpoints)
Refs: PUKU_BACKEND_AGENT.md §8
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# Same convention as algorithms — Literal over enum so the
# OpenAPI schema carries the exact set.
Difficulty = Literal["easy", "medium", "hard"]


class DataStructureResponse(BaseModel):
    """Public-safe data-structure representation.

    Returned by:
    - ``GET /data-structures`` (paginated)
    - ``GET /data-structures/{slug}``
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    slug: str
    name: str
    description: str | None = None
    difficulty: Difficulty
    visualization_type: str
    created_at: datetime


class DataStructureListResponse(BaseModel):
    """Paginated envelope for data-structure listings."""

    items: list[DataStructureResponse]
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    total: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=1)


__all__ = ["DataStructureListResponse", "DataStructureResponse", "Difficulty"]
