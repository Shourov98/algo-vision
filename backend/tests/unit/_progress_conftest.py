"""Shared test fixtures for the progress unit tests.

Mirrors the ``_catalog_conftest`` and ``_problems_conftest``
patterns: lives next to the test files so only progress
tests pick it up.

Refs: PUKU_BACKEND_AGENT.md §13 (Test Conventions)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

from src.modules.progress.models import (
    UserAlgorithmProgress,
    UserProblemProgress,
    UserRecentItem,
)
from src.modules.progress.service import ProgressService
from src.shared.pagination import Page


class FakeProgressRepo:
    """AsyncMock-shaped fake that records calls."""

    def __init__(self) -> None:
        self.upsert_algorithm_progress = AsyncMock(
            return_value=_make_alg_progress()
        )
        self.upsert_problem_progress = AsyncMock(
            return_value=_make_prob_progress()
        )
        self.list_algorithm_progress = AsyncMock(
            return_value=Page(items=[], page=1, page_size=20, total=0)
        )
        self.list_problem_progress = AsyncMock(
            return_value=Page(items=[], page=1, page_size=20, total=0)
        )
        self.get_overview = AsyncMock(
            return_value={
                "algorithms_completed": 0,
                "algorithms_in_progress": 0,
                "algorithms_total": 0,
                "problems_completed": 0,
                "problems_in_progress": 0,
                "problems_total": 0,
            }
        )
        self.record_view = AsyncMock(return_value=None)
        self.list_recents = AsyncMock(return_value=[])


def make_service() -> tuple[ProgressService, dict[str, Any]]:
    """Return (service, repos_by_name) for direct poking."""
    repo = FakeProgressRepo()
    svc = ProgressService(repo=repo)  # type: ignore[arg-type]
    return svc, {"repo": repo}


def _make_alg_progress(
    *,
    user_id: Any | None = None,
    algorithm_id: Any | None = None,
    status: str = "in_progress",
    completion_percentage: int = 0,
    total_sessions: int = 1,
) -> UserAlgorithmProgress:
    row = UserAlgorithmProgress(
        user_id=user_id or uuid4(),
        algorithm_id=algorithm_id or uuid4(),
        status=status,
        completion_percentage=completion_percentage,
        total_sessions=total_sessions,
    )
    now = datetime.now(UTC)
    row.first_viewed_at = now
    row.last_viewed_at = now
    row.completed_at = now if status == "completed" else None
    return row


def _make_prob_progress(
    *,
    user_id: Any | None = None,
    problem_id: Any | None = None,
    status: str = "in_progress",
    attempts: int = 1,
) -> UserProblemProgress:
    row = UserProblemProgress(
        user_id=user_id or uuid4(),
        problem_id=problem_id or uuid4(),
        status=status,
        attempts=attempts,
    )
    now = datetime.now(UTC)
    row.first_viewed_at = now
    row.last_viewed_at = now
    row.completed_at = now if status == "completed" else None
    return row


def make_recent(
    *,
    user_id: Any | None = None,
    item_type: str = "algorithm",
    item_id: Any | None = None,
) -> UserRecentItem:
    row = UserRecentItem(
        id=uuid4(),
        user_id=user_id or uuid4(),
        item_type=item_type,
        item_id=item_id or uuid4(),
    )
    row.viewed_at = datetime.now(UTC)
    return row


__all__ = [
    "FakeProgressRepo",
    "make_recent",
    "make_service",
]
