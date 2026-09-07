"""ProgressService — unit tests for the per-user progress orchestrator.

Covers the four user-facing operations + the event handler
that subscribes to ItemViewedEvent. Mirrors the catalog
service test conventions (AsyncMock-backed repos).

Refs: ALGOVISION_BACKEND_PLAN.md §5 (Phase 5 — B5.13)
Refs: PUKU_BACKEND_AGENT.md §13
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from src.modules.progress.filters import (
    AlgorithmProgressFilters,
    ProblemProgressFilters,
    ProgressSortField,
    SortOrder,
)
from src.modules.progress.schemas import (
    ProgressOverviewResponse,
    UserAlgorithmProgressResponse,
)
from src.shared.events import ItemViewedEvent

from tests.unit._progress_conftest import (
    make_recent,
    make_service,
)

# ---------------------------------------------------------------------------
# mark_algorithm
# ---------------------------------------------------------------------------


async def test_mark_algorithm_returns_response_from_upsert() -> None:
    svc, repos = make_service()
    repos["repo"].upsert_algorithm_progress.return_value = (
        _alg_with_status("in_progress", 50)
    )
    response = await svc.mark_algorithm(
        user_id=uuid4(),
        algorithm_id=uuid4(),
        status="in_progress",
        completion_percentage=50,
    )
    assert isinstance(response, UserAlgorithmProgressResponse)
    assert response.status == "in_progress"
    assert response.completion_percentage == 50


async def test_mark_algorithm_passes_args_to_repo() -> None:
    svc, repos = make_service()
    user_id = uuid4()
    algo_id = uuid4()
    await svc.mark_algorithm(
        user_id=user_id,
        algorithm_id=algo_id,
        status="completed",
        completion_percentage=100,
    )
    repos["repo"].upsert_algorithm_progress.assert_awaited_once_with(
        user_id=user_id,
        algorithm_id=algo_id,
        status="completed",
        completion_percentage=100,
    )


# ---------------------------------------------------------------------------
# mark_problem
# ---------------------------------------------------------------------------


async def test_mark_problem_returns_response_from_upsert() -> None:
    svc, repos = make_service()
    repos["repo"].upsert_problem_progress.return_value = (
        _prob_with_status("completed", attempts=3)
    )
    response = await svc.mark_problem(
        user_id=uuid4(),
        problem_id=uuid4(),
        status="completed",
        attempts=3,
    )
    assert response.status == "completed"
    assert response.attempts == 3


# ---------------------------------------------------------------------------
# list_algorithm_progress / list_problem_progress
# ---------------------------------------------------------------------------


async def test_list_algorithm_progress_delegates_to_repo() -> None:
    svc, repos = make_service()
    repos["repo"].list_algorithm_progress.return_value = _page([])
    filters = AlgorithmProgressFilters(
        status="in_progress",
        sort_by=ProgressSortField.LAST_VIEWED_AT,
        sort_order=SortOrder.DESC,
    )
    page = await svc.list_algorithm_progress(
        user_id=uuid4(), filters=filters
    )
    repos["repo"].list_algorithm_progress.assert_awaited_once()
    assert page.items == []


async def test_list_problem_progress_delegates_to_repo() -> None:
    svc, repos = make_service()
    repos["repo"].list_problem_progress.return_value = _page([])
    filters = ProblemProgressFilters(
        sort_by=ProgressSortField.LAST_VIEWED_AT,
        sort_order=SortOrder.DESC,
    )
    await svc.list_problem_progress(
        user_id=uuid4(), filters=filters
    )
    repos["repo"].list_problem_progress.assert_awaited_once()


# ---------------------------------------------------------------------------
# get_overview
# ---------------------------------------------------------------------------


async def test_get_overview_returns_response_with_counts() -> None:
    svc, repos = make_service()
    repos["repo"].get_overview.return_value = {
        "algorithms_completed": 5,
        "algorithms_in_progress": 3,
        "algorithms_total": 8,
        "problems_completed": 2,
        "problems_in_progress": 1,
        "problems_total": 3,
    }
    overview = await svc.get_overview(user_id=uuid4())
    assert isinstance(overview, ProgressOverviewResponse)
    assert overview.algorithms.completed == 5
    assert overview.algorithms.in_progress == 3
    assert overview.algorithms.total == 8
    assert overview.problems.completed == 2


async def test_get_overview_handles_zero_counts() -> None:
    svc, repos = make_service()
    repos["repo"].get_overview.return_value = {
        "algorithms_completed": 0,
        "algorithms_in_progress": 0,
        "algorithms_total": 0,
        "problems_completed": 0,
        "problems_in_progress": 0,
        "problems_total": 0,
    }
    overview = await svc.get_overview(user_id=uuid4())
    assert overview.algorithms.total == 0
    assert overview.problems.total == 0


# ---------------------------------------------------------------------------
# list_recents
# ---------------------------------------------------------------------------


async def test_list_recents_returns_capped_feed() -> None:
    svc, repos = make_service()
    repos["repo"].list_recents.return_value = [
        make_recent(item_type="algorithm"),
        make_recent(item_type="problem"),
    ]
    recents = await svc.list_recents(user_id=uuid4())
    assert len(recents.items) == 2


async def test_list_recents_empty_when_repo_empty() -> None:
    svc, repos = make_service()
    repos["repo"].list_recents.return_value = []
    recents = await svc.list_recents(user_id=uuid4())
    assert recents.items == []


# ---------------------------------------------------------------------------
# handle_item_viewed (event handler)
# ---------------------------------------------------------------------------


async def test_handle_item_viewed_records_when_user_present() -> None:
    svc, repos = make_service()
    user_id = uuid4()
    item_id = uuid4()
    event = ItemViewedEvent(
        item_type="algorithm",
        item_id=item_id,
        user_id=user_id,
        viewed_at=datetime.now(UTC),
    )
    await svc.handle_item_viewed(event)
    repos["repo"].record_view.assert_awaited_once_with(
        user_id=user_id,
        item_type="algorithm",
        item_id=item_id,
    )


async def test_handle_item_viewed_drops_anonymous() -> None:
    """Anonymous views (user_id is None) must not be recorded."""
    svc, repos = make_service()
    event = ItemViewedEvent(
        item_type="algorithm",
        item_id=uuid4(),
        user_id=None,
        viewed_at=datetime.now(UTC),
    )
    await svc.handle_item_viewed(event)
    repos["repo"].record_view.assert_not_called()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _alg_with_status(status: str, completion_percentage: int = 0):
    from datetime import UTC, datetime

    from src.modules.progress.models import UserAlgorithmProgress

    user_id = uuid4()
    algo_id = uuid4()
    now = datetime.now(UTC)
    row = UserAlgorithmProgress(
        user_id=user_id,
        algorithm_id=algo_id,
        status=status,
        completion_percentage=completion_percentage,
        total_sessions=1,
    )
    row.first_viewed_at = now
    row.last_viewed_at = now
    row.completed_at = now if status == "completed" else None
    return row


def _prob_with_status(status: str, *, attempts: int = 1):
    from datetime import UTC, datetime

    from src.modules.progress.models import UserProblemProgress

    user_id = uuid4()
    prob_id = uuid4()
    now = datetime.now(UTC)
    row = UserProblemProgress(
        user_id=user_id,
        problem_id=prob_id,
        status=status,
        attempts=attempts,
    )
    row.first_viewed_at = now
    row.last_viewed_at = now
    row.completed_at = now if status == "completed" else None
    return row


def _page(rows):
    from src.shared.pagination import Page

    return Page(items=rows, page=1, page_size=20, total=len(rows))
