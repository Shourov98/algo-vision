"""Pydantic schemas for the companies API.

These models shape the wire format for the companies
endpoints (B4.8). They validate response shape and are the
ONLY way ORM rows leave the problems module — routers never
return SQLAlchemy objects directly (PUKU_BACKEND_AGENT §3.1).

Why split per entity
--------------------
Two entities (Company, Problem) means two schemas. Keeping
them in one file would also approach the 400-line cap once
the detail-shape is fleshed out. Per-entity files keep each
under 100 lines and make schema ownership obvious.

Refs: ALGOVISION_BACKEND_PLAN.md §4 (B4.4 schemas)
Refs: PUKU_BACKEND_AGENT.md §8 (Pydantic Schema Conventions)
Refs: AlgoVision_BACKEND.md §26 (Response Models)
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CompanyResponse(BaseModel):
    """Public-safe company representation.

    Returned by:
    - ``GET /problems/companies`` (paginated)
    - ``GET /problems/companies/{slug}``

    Companies are intentionally tiny (id + slug + name) —
    there are no description / logo / website columns in v1
    (see ``models/company.py`` docstring for rationale).
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    slug: str
    name: str


class CompanyListResponse(BaseModel):
    """Paginated envelope for company listings.

    Mirrors the ``Page[T]`` shape used by every catalog list
    endpoint. Defined as its own Pydantic model (rather than
    reusing the runtime ``Page`` dataclass) so FastAPI can
    generate a typed OpenAPI schema for the envelope.
    """

    items: list[CompanyResponse]
    page: int = Field(..., ge=1, description="Current page (1-indexed).")
    page_size: int = Field(..., ge=1, description="Items per page.")
    total: int = Field(..., ge=0, description="Total items across all pages.")
    total_pages: int = Field(..., ge=1, description="Total pages (>= 1).")


__all__ = ["CompanyListResponse", "CompanyResponse"]
