"""Pydantic schemas for the progress API.

These models shape the wire format for the progress
endpoints (B5.7). They validate response shape and are the
ONLY way ORM rows leave the progress module — routers never
return SQLAlchemy objects directly (PUKU_BACKEND_AGENT §3.1).

Request bodies
--------------
``MarkAlgorithmProgressRequest`` and ``MarkProblemProgressRequest``
are the payload for POST /progress/algorithms/{id} and
/progress/problems/{id} respectively. Both are intentionally
sparse — the path supplies user_id (from the JWT) and
algorithm_id/problem_id (from the URL); the body only carries
state the user is updating.

Response bodies
---------------
The detail responses wrap the ORM row verbatim (id fields,
timestamps, status). The list responses are paginated
envelopes following the catalog convention
(``src.modules.catalog.schemas``).

ProgressOverviewResponse
------------------------
Composite shape covering both entities: a single endpoint
gives the dashboard a "completed counts at a glance" view
without separate queries per entity.

Refs: ALGOVISION_BACKEND_PLAN.md §5 (Phase 5 — B5.4)
Refs: PUKU_BACKEND_AGENT.md §8 (Pydantic Schema Conventions)
Refs: AlgoVision_BACKEND.md §26 (Response Models)
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# Closed vocabulary for progress status. Mirrors the model
# STATUS_VALUES constant and the DB CHECK constraint.
# Single source of truth for the API surface.
ProgressStatus = Literal["not_started", "in_progress", "completed"]
ProgressItemType = Literal["algorithm", "data_structure", "problem"]


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------


class MarkAlgorithmProgressRequest(BaseModel):
    """POST body for ``/progress/algorithms/{algorithm_id}``.

    Only the state the user is updating lives here; the
    path captures ``algorithm_id``, the JWT captures
    ``user_id``.

    Why ``completion_percentage`` is required
    -----------------------------------------
    The ring on the dashboard needs a value to render. If
    the client omits it the service assumes "still 0%".
    Sending a value always is also explicit and forces the
    client to commit to a progress number.
    """

    model_config = ConfigDict(extra="forbid")

    status: ProgressStatus
    completion_percentage: int = Field(..., ge=0, le=100)


class MarkProblemProgressRequest(BaseModel):
    """POST body for ``/progress/problems/{problem_id}``.

    No completion_percentage field (problems are atomic).
    The body carries status and an ``attempts`` bump
    (incremented client-side when the user clicks "Try
    again" so the dashboard can render "tried 3 times
    before solving").
    """

    model_config = ConfigDict(extra="forbid")

    status: ProgressStatus
    attempts: int = Field(default=1, ge=1)


# ---------------------------------------------------------------------------
# Response bodies
# ---------------------------------------------------------------------------


class UserAlgorithmProgressResponse(BaseModel):
    """One progress row for one algorithm."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    user_id: UUID
    algorithm_id: UUID
    status: ProgressStatus
    completion_percentage: int = Field(..., ge=0, le=100)
    first_viewed_at: datetime
    last_viewed_at: datetime
    completed_at: datetime | None = None
    total_sessions: int


class UserProblemProgressResponse(BaseModel):
    """One progress row for one problem."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    user_id: UUID
    problem_id: UUID
    status: ProgressStatus
    attempts: int
    first_viewed_at: datetime
    last_viewed_at: datetime
    completed_at: datetime | None = None


class AlgorithmProgressListResponse(BaseModel):
    """Paginated envelope for ``GET /progress/algorithms``."""

    items: list[UserAlgorithmProgressResponse]
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    total: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=1)


class ProblemProgressListResponse(BaseModel):
    """Paginated envelope for ``GET /progress/problems``."""

    items: list[UserProblemProgressResponse]
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    total: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=1)


# ---------------------------------------------------------------------------
# Recent items
# ---------------------------------------------------------------------------


class RecentItemResponse(BaseModel):
    """One entry on the dashboard's "recently viewed" panel.

    The polymorphic item_id lives here without being joined
    to its source table — the frontend interprets the
    item_type and routes accordingly. Embedding the full
    catalog row would be expensive and rarely useful; the
    dashboard re-fetches the row when the user clicks.
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    item_type: ProgressItemType
    item_id: UUID
    viewed_at: datetime


class RecentsListResponse(BaseModel):
    """Capped at 50 items per DATABASE_DESIGN §1."""

    items: list[RecentItemResponse]


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------


class ProgressOverviewCounts(BaseModel):
    """Per-entity counts (completed / in_progress / total)."""

    completed: int = Field(..., ge=0)
    in_progress: int = Field(..., ge=0)
    total: int = Field(..., ge=0)


class ProgressOverviewResponse(BaseModel):
    """Composite overview returned by ``GET /progress/overview``.

    Each entity (algorithms, problems) gets its own
    ProgressOverviewCounts so the dashboard can render two
    independent rings without two HTTP calls.

    Why no separate "not_started" count
    -----------------------------------
    ``not_started`` = ``total - completed - in_progress`` is
    trivially derived on the client. Sending it would
    duplicate information and risk drift between the three
    numbers.
    """

    algorithms: ProgressOverviewCounts
    problems: ProgressOverviewCounts


__all__ = [
    "AlgorithmProgressListResponse",
    "MarkAlgorithmProgressRequest",
    "MarkProblemProgressRequest",
    "ProblemProgressListResponse",
    "ProgressItemType",
    "ProgressOverviewCounts",
    "ProgressOverviewResponse",
    "ProgressStatus",
    "RecentItemResponse",
    "RecentsListResponse",
    "UserAlgorithmProgressResponse",
    "UserProblemProgressResponse",
]
