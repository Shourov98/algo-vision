"""Pydantic schemas for the dashboard API.

The dashboard is the highest-level read-side projection in
the system. It composes:

- ProgressOverviewCounts (B5.4) - per-entity completed /
  in_progress / total counts.
- ReadinessMetric - 0..100 interview-readiness score with
  a breakdown by category so the frontend can render a
  stacked progress ring.
- SkillMetric - per-topic mastery score (0..100).
- FocusArea - top-N weakest topics with severity.
- ActivityPoint - one day on the activity heatmap.
- RecentItem - one row on the recently-viewed sidebar.

The dashboard's ``/summary`` endpoint returns
``DashboardSummary`` which composes all of the above.

Calculator decomposition
------------------------
``ALGOVISION_BACKEND_PLAN §5`` mandates that the dashboard
be an *orchestrator only*. Each metric is owned by a
calculator that exposes a Protocol — these schemas are
the wire-format types those calculators return. The
Service builds the ``DashboardSummary`` from the
calculator results.

Refs: ALGOVISION_BACKEND_PLAN.md §5 (Dashboard Composition)
Refs: AlgoVision_BACKEND.md §26 (Response Models)
Refs: PUKU_BACKEND_AGENT.md §8
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Literals
# ---------------------------------------------------------------------------

# Severity of a FocusArea entry. Drives the colour the
# frontend uses to render the chip.
FocusSeverity = Literal["low", "medium", "high"]

# Item type discriminator on the recently-viewed feed.
# Mirrors the ProgressItemType literal in progress.schemas.
DashboardItemType = Literal[
    "algorithm",
    "data_structure",
    "problem",
]


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------


class ReadinessBreakdownEntry(BaseModel):
    """One slice of the readiness ring (per category)."""

    model_config = ConfigDict(extra="forbid")

    category_slug: str = Field(
        ..., description="Stable identifier for the category.",
    )
    category_name: str = Field(
        ..., description="Display name for the category.",
    )
    score: int = Field(
        ..., ge=0, le=100,
        description="0..100 score within this category.",
    )
    weight: float = Field(
        ..., ge=0.0, le=1.0,
        description=(
            "Relative weight of this category in the "
            "composite readiness score (sum across "
            "categories = 1.0)."
        ),
    )


class ReadinessMetric(BaseModel):
    """Composite interview-readiness score.

    The score is a weighted average of the per-category
    scores, normalised to 0..100. The breakdown lists each
    contributing category so the frontend can render the
    ring and tooltips.
    """

    model_config = ConfigDict(extra="forbid")

    score: int = Field(..., ge=0, le=100)
    breakdown: list[ReadinessBreakdownEntry] = Field(
        default_factory=list,
        description="Per-category contribution to the score.",
    )


class SkillMetric(BaseModel):
    """One entry on the skill-mapping heatmap.

    A skill corresponds to a topic (e.g. "Hashing",
    "Dynamic Programming"). The mastery score is 0..100 and
    drives the heatmap colour.
    """

    model_config = ConfigDict(extra="forbid")

    topic_slug: str
    topic_name: str
    mastery: int = Field(..., ge=0, le=100)
    algorithms_completed: int = Field(..., ge=0)
    algorithms_total: int = Field(..., ge=0)


class FocusArea(BaseModel):
    """A topic the dashboard suggests the user work on next.

    Severity is derived from the mastery gap: low mastery
    + few completions → high severity.
    """

    model_config = ConfigDict(extra="forbid")

    topic_slug: str
    topic_name: str
    severity: FocusSeverity
    mastery: int = Field(..., ge=0, le=100)
    rationale: str = Field(
        ..., description="Human-readable reason this topic was selected.",
    )


class ActivityPoint(BaseModel):
    """One day on the activity heatmap.

    ``date`` is the UTC day the activity occurred; ``count``
    is the number of progress marks + view events the user
    emitted that day.
    """

    model_config = ConfigDict(extra="forbid")

    date: date
    count: int = Field(..., ge=0)


class RecentItem(BaseModel):
    """One entry on the recently-viewed sidebar.

    Polymorphic item_id — the frontend interprets item_type
    and routes accordingly. We deliberately do NOT embed
    the full catalog row (the dashboard re-fetches on
    click); the sidebar is meant to be a cheap surface.
    """

    model_config = ConfigDict(extra="forbid")

    id: UUID
    item_type: DashboardItemType
    item_id: UUID
    viewed_at: datetime


# ---------------------------------------------------------------------------
# Top-level summary
# ---------------------------------------------------------------------------


class ProgressCountsBlock(BaseModel):
    """Per-entity completed / in_progress / total.

    Mirrors ``ProgressOverviewCounts`` from progress.schemas
    but redefined here so the dashboard summary can stand
    alone (no cross-module wire-type coupling at the
    dashboard endpoint).
    """

    model_config = ConfigDict(extra="forbid")

    completed: int = Field(..., ge=0)
    in_progress: int = Field(..., ge=0)
    total: int = Field(..., ge=0)


class DashboardSummary(BaseModel):
    """Top-level dashboard projection.

    Composes every calculator output + the progress
    overview + the recents feed into a single
    round-trip response. The frontend renders the
    home dashboard from this object alone — no
    additional fetches needed for the v1 layout.
    """

    model_config = ConfigDict(extra="forbid")

    # Counts (mirrors ProgressOverviewResponse but flat).
    algorithms_learned: int = Field(
        ..., ge=0,
        description="Number of algorithms the user has completed.",
    )
    algorithms_total: int = Field(
        ..., ge=0,
        description="Total published algorithms in the catalog.",
    )
    problems_solved: int = Field(
        ..., ge=0,
        description="Number of problems the user has completed.",
    )
    problems_total: int = Field(
        ..., ge=0,
        description="Total problems in the catalog.",
    )

    # Calculators.
    interview_readiness: ReadinessMetric
    skill_mapping: list[SkillMetric] = Field(default_factory=list)
    focus_areas: list[FocusArea] = Field(default_factory=list)
    current_streak: int = Field(..., ge=0)
    activity: list[ActivityPoint] = Field(
        default_factory=list,
        description="Activity heatmap, sorted by date ascending.",
    )
    recently_viewed: list[RecentItem] = Field(
        default_factory=list,
        description="Up to 50 most-recent view events.",
    )


__all__ = [
    "ActivityPoint",
    "DashboardItemType",
    "DashboardSummary",
    "FocusArea",
    "FocusSeverity",
    "ProgressCountsBlock",
    "ReadinessBreakdownEntry",
    "ReadinessMetric",
    "RecentItem",
    "SkillMetric",
]
