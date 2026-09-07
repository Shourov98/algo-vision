"""Pydantic schemas for the algorithm-categories API.

These models shape the wire format for the algorithm-categories
endpoints (B3.8). They validate response shape and are the
ONLY way ORM rows leave the catalog module — routers never
return SQLAlchemy objects directly (PUKU_BACKEND_AGENT §3.1).

Why split per entity
--------------------
Five entities means five schemas. Keeping them in one file
hit the 400-line limit during draft; per-entity files keep
each under 100 lines and make schema ownership obvious.

Refs: ALGOVISION_BACKEND_PLAN.md §3.7 (B3.7 schemas)
Refs: PUKU_BACKEND_AGENT.md §8 (Pydantic Schema Conventions)
Refs: AlgoVision_BACKEND.md §26 (Response Models)
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CategoryResponse(BaseModel):
    """Public-safe category representation.

    Returned by:
    - ``GET /algorithms/categories`` (paginated)
    - ``GET /algorithms/categories/{slug}``
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    slug: str
    name: str
    description: str | None = None
    sort_order: int
    created_at: datetime


class CategoryListResponse(BaseModel):
    """Paginated envelope for category listings.

    Mirrors ``Page[T]`` shape used by every catalog list
    endpoint. Defined as its own Pydantic model (rather than
    reusing the runtime ``Page`` dataclass) so FastAPI can
    generate a typed OpenAPI schema for the envelope.
    """

    items: list[CategoryResponse]
    page: int = Field(..., ge=1, description="Current page (1-indexed).")
    page_size: int = Field(..., ge=1, description="Items per page.")
    total: int = Field(..., ge=0, description="Total items across all pages.")
    total_pages: int = Field(..., ge=1, description="Total pages (>= 1).")


__all__ = ["CategoryListResponse", "CategoryResponse"]
