"""Pydantic schemas for the problems API.

These models shape the wire format for the problems
endpoints (B4.8). They validate response shape and are the
ONLY way ORM rows leave the problems module — routers never
return SQLAlchemy objects directly (PUKU_BACKEND_AGENT §3.1).

Embedded summaries
------------------
The detail response embeds two compact summary shapes —
``TopicSummary`` and ``CompanySummary`` — so the frontend
can render a problem detail page (with topic chips and
"asked by" pills) in a single round-trip. The summary shapes
mirror the catalog pattern (see
``src.modules.catalog.schemas.algorithms``).

Why we define ``CompanySummary`` here (and not in companies.py)
--------------------------------------------------------------
It is embedded in the problem detail and is therefore part
of the problems-API contract. Putting it in ``companies.py``
would force ``companies.py`` to be imported by anyone
modelling a problem detail — the dependency direction should
flow: problems → companies (problems depend on companies for
display), never the other way. The catalog module does the
same with ``TopicSummary`` (lives in ``algorithms.py``).

Refs: ALGOVISION_BACKEND_PLAN.md §4 (B4.4 schemas)
Refs: PUKU_BACKEND_AGENT.md §8 (Pydantic Schema Conventions)
Refs: AlgoVision_BACKEND.md §26 (Response Models)
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Mirrors the catalog ``Difficulty`` literal — kept in sync
# with ``DIFFICULTY_VALUES`` on the model side. Declared here
# (not imported) so the wire-format vocabulary can evolve
# independently of the storage vocabulary.
Difficulty = Literal["easy", "medium", "hard"]


class TopicSummary(BaseModel):
    """Compact topic representation embedded in the problem detail.

    Mirrors ``catalog.schemas.algorithms.TopicSummary`` — same
    shape, no description, because the frontend renders topics
    as chips / tags and the slug is the visual key.
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    slug: str
    name: str


class CompanySummary(BaseModel):
    """Compact company representation embedded in the problem detail.

    Mirrors the catalog pattern of embedding slim "summary"
    shapes inside detail responses. Lives here (not in
    companies.py) because the problems API owns the detail
    contract.
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    slug: str
    name: str


class ProblemSummaryResponse(BaseModel):
    """List-row representation.

    Returned by ``GET /problems``. Deliberately omits the
    long-form editorial (``solution_explanation``) and the
    free-form external reference so list responses stay small
    and serialise fast — the detail endpoint fills them in.

    Includes the ``visualization_available`` flag because the
    frontend uses it to choose the route (visualization flow
    vs editor flow) on the listing page itself.
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    slug: str
    title: str
    description: str | None = None
    difficulty: Difficulty
    visualization_available: bool
    created_at: datetime
    updated_at: datetime


class ProblemDetailResponse(BaseModel):
    """Detail representation.

    Returned by ``GET /problems/{slug}``. Includes the
    embedded topic + company lists so the frontend can render
    the detail page (description, editorial, topic chips,
    "asked by" pills) in a single round-trip.

    Why ``solution_explanation`` is ``str | None``
    ---------------------------------------------
    The seed ships with empty bodies for problems without
    an editorial yet (see ``models/problem.py``); the schema
    must accept null so the detail endpoint doesn't have to
    synthesize a placeholder.

    Why ``external_reference`` is ``str | None``
    ---------------------------------------------
    Same reason — the column is nullable at the DB level and
    may hold anything from ``"LC-1"`` to a long URL to a
    book chapter reference.
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    slug: str
    title: str
    description: str | None = None
    difficulty: Difficulty
    solution_explanation: str | None = None
    external_reference: str | None = None
    visualization_available: bool
    topics: list[TopicSummary] = Field(
        default_factory=list,
        description="Topics tagged on this problem.",
    )
    companies: list[CompanySummary] = Field(
        default_factory=list,
        description="Companies that ask this problem.",
    )
    created_at: datetime
    updated_at: datetime


class ProblemListResponse(BaseModel):
    """Paginated envelope for problem listings."""

    items: list[ProblemSummaryResponse]
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    total: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=1)


__all__ = [
    "CompanySummary",
    "Difficulty",
    "ProblemDetailResponse",
    "ProblemListResponse",
    "ProblemSummaryResponse",
    "TopicSummary",
]
