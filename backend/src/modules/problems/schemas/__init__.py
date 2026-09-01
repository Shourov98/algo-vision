"""Problems HTTP schemas — package root.

Pydantic models for every problems + companies endpoint
(B4.4). Per-entity files keep each under 100 lines; this
``__init__`` re-exports the public names so callers can do
``from src.modules.problems.schemas import ProblemDetailResponse``.
"""

from __future__ import annotations

from src.modules.problems.schemas.companies import (
    CompanyListResponse,
    CompanyResponse,
)
from src.modules.problems.schemas.problems import (
    CompanySummary,
    Difficulty,
    ProblemDetailResponse,
    ProblemListResponse,
    ProblemSummaryResponse,
    TopicSummary,
)

__all__ = [
    "CompanyListResponse",
    "CompanyResponse",
    "CompanySummary",
    "Difficulty",
    "ProblemDetailResponse",
    "ProblemListResponse",
    "ProblemSummaryResponse",
    "TopicSummary",
]
