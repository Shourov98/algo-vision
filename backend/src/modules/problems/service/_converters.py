"""ORM-to-response converters for the problems module.

These functions are the boundary between the persistence
layer (SQLAlchemy ORM rows) and the HTTP layer (Pydantic
response schemas). They live in the service package - NOT
the routers - so the rule "ORM rows never escape the
service layer" is enforced by where the code physically
lives, not by a code review checklist.

Why per-entity functions instead of one generic helper
------------------------------------------------------
The conversion is straightforward today but is the
obvious place for cross-cutting changes (embedding derived
fields, transforming dates, redacting internal fields).
One helper per entity keeps that future diff small and
localized.

The problem detail converter is the interesting one: it
embeds two extra summaries (TopicSummary, CompanySummary)
that come from separate repository calls (B4.5). Manual
dict construction is used because the embedded shapes come
from different tables than the Problem row itself.

Refs: PUKU_BACKEND_AGENT.md §3.1 (ORM never escapes service),
      §8 (Pydantic schemas)
"""

from __future__ import annotations

from collections.abc import Sequence

from src.modules.catalog.models import Topic
from src.modules.problems.models import Company, Problem
from src.modules.problems.schemas import (
    CompanyResponse,
    CompanySummary,
    ProblemDetailResponse,
    ProblemSummaryResponse,
    TopicSummary,
)


def company_to_response(company: Company) -> CompanyResponse:
    """Convert an ORM Company row to a public-safe response."""
    return CompanyResponse.model_validate(company)


def company_to_summary(company: Company) -> CompanySummary:
    """Compact company shape for the problem-detail embed."""
    return CompanySummary.model_validate(company)


def topic_to_summary(topic: Topic) -> TopicSummary:
    """Compact topic shape for the problem-detail embed.

    The catalog module owns the ``Topic`` model; the
    problems API owns the embed definition. The mapping
    here is the boundary between them.
    """
    return TopicSummary.model_validate(topic)


def problem_to_summary(problem: Problem) -> ProblemSummaryResponse:
    """List-row representation."""
    return ProblemSummaryResponse.model_validate(problem)


def problem_to_detail(
    problem: Problem,
    topics: Sequence[Topic],
    companies: Sequence[Company],
) -> ProblemDetailResponse:
    """Build the detail response from a Problem row + side fetches.

    The detail embeds topic + company summaries. Both come
    from separate repository calls (B4.5 ``list_topics`` /
    ``list_companies``) rather than a single SQL JOIN +
    aggregation, so the constructor takes them as
    pre-resolved sequences. The sequences are already
    ordered by the repository (slug ASC).
    """
    return ProblemDetailResponse.model_validate(
        {
            "id": problem.id,
            "slug": problem.slug,
            "title": problem.title,
            "description": problem.description,
            "difficulty": problem.difficulty,
            "solution_explanation": problem.solution_explanation,
            "external_reference": problem.external_reference,
            "visualization_available": problem.visualization_available,
            "topics": [topic_to_summary(t) for t in topics],
            "companies": [company_to_summary(c) for c in companies],
            "created_at": problem.created_at,
            "updated_at": problem.updated_at,
        }
    )


__all__ = [
    "company_to_response",
    "company_to_summary",
    "problem_to_detail",
    "problem_to_summary",
    "topic_to_summary",
]
