"""ProgressRepository — Protocol the progress service depends on.

Liskov substitution: any class implementing this contract
can stand in for the real repository in unit tests.

The five operations covered:

- upsert_algorithm_progress / upsert_problem_progress :
  idempotent INSERT … ON CONFLICT DO UPDATE.
- list_algorithm_progress / list_problem_progress :
  paginated listings with status filter.
- get_overview : aggregate counts for the dashboard.
- record_view  : append + cap-to-50 for user_recent_items.

Refs: ALGOVISION_BACKEND_PLAN.md §5 (Phase 5 — B5.5)
Refs: AlgoVision_BACKEND.md §10 (Repository Conventions)
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from src.modules.progress.filters import (
    AlgorithmProgressFilters,
    ProblemProgressFilters,
)
from src.modules.progress.models import (
    UserAlgorithmProgress,
    UserProblemProgress,
    UserRecentItem,
)
from src.shared.pagination import Page

# Cap on the recently-viewed feed (DATABASE_DESIGN §1).
# The repository enforces the cap after each INSERT by
# trimming the older rows; the DB has no trigger.
RECENT_ITEMS_CAP = 50


class ProgressRepositoryProtocol(Protocol):
    """Interface the progress service depends on."""

    async def upsert_algorithm_progress(
        self,
        user_id: UUID,
        algorithm_id: UUID,
        status: str,
        completion_percentage: int,
    ) -> UserAlgorithmProgress: ...

    async def upsert_problem_progress(
        self,
        user_id: UUID,
        problem_id: UUID,
        status: str,
        attempts: int,
    ) -> UserProblemProgress: ...

    async def list_algorithm_progress(
        self,
        user_id: UUID,
        filters: AlgorithmProgressFilters,
    ) -> Page[UserAlgorithmProgress]: ...

    async def list_problem_progress(
        self,
        user_id: UUID,
        filters: ProblemProgressFilters,
    ) -> Page[UserProblemProgress]: ...

    async def get_overview(self, user_id: UUID) -> dict[str, int]: ...

    async def record_view(
        self,
        user_id: UUID,
        item_type: str,
        item_id: UUID,
    ) -> None: ...

    async def list_recents(
        self,
        user_id: UUID,
    ) -> Sequence[UserRecentItem]: ...


__all__ = ["RECENT_ITEMS_CAP", "ProgressRepositoryProtocol"]
