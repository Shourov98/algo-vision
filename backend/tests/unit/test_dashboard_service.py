"""DashboardService — unit tests for the orchestrator.

The service composes four calculator Protocols + a
ProgressServiceProtocol + a catalog session factory. We
inject AsyncMock-backed stubs and verify the orchestrator
wires them correctly into a DashboardSummary.

Refs: ALGOVISION_BACKEND_PLAN.md §5 (Phase 5 — B5.13)
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from src.modules.dashboard.calculators import (
    FocusAreaSelectorProtocol,
    ReadinessCalculatorProtocol,
    SkillMapperProtocol,
    StreakCalculatorProtocol,
)
from src.modules.dashboard.schemas import (
    ActivityPoint,
    DashboardSummary,
    FocusArea,
    ReadinessBreakdownEntry,
    ReadinessMetric,
    RecentItem,
    SkillMetric,
)
from src.modules.dashboard.service import DashboardService
from src.modules.progress.schemas import (
    ProgressOverviewCounts,
    ProgressOverviewResponse,
    RecentItemResponse,
    RecentsListResponse,
)

# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


async def test_get_summary_composes_all_calculator_outputs() -> None:
    """A fully-populated fan-out produces the right shape."""
    progress = _progress_stub(
        overview=ProgressOverviewResponse(
            algorithms=ProgressOverviewCounts(
                completed=3, in_progress=1, total=4
            ),
            problems=ProgressOverviewCounts(
                completed=2, in_progress=0, total=2
            ),
        ),
        recents=RecentsListResponse(
            items=[
                RecentItemResponse(
                    id=_uuid(),
                    item_type="algorithm",
                    item_id=_uuid(),
                    viewed_at=datetime.now(UTC),
                ),
            ]
        ),
    )
    readiness = _readiness_stub(
        ReadinessMetric(
            score=72,
            breakdown=[
                ReadinessBreakdownEntry(
                    category_slug="sorting",
                    category_name="Sorting",
                    score=80,
                    weight=0.5,
                ),
                ReadinessBreakdownEntry(
                    category_slug="graph",
                    category_name="Graph",
                    score=64,
                    weight=0.5,
                ),
            ],
        )
    )
    skill = _skill_stub(
        [
            SkillMetric(
                topic_slug="dp",
                topic_name="DP",
                mastery=42,
                algorithms_completed=2,
                algorithms_total=5,
            ),
        ]
    )
    focus = _focus_stub(
        [
            FocusArea(
                topic_slug="dp",
                topic_name="DP",
                severity="medium",
                mastery=42,
                rationale="...",
            )
        ]
    )
    streak = _streak_stub(
        current=5,
        activity=[ActivityPoint(date=date(2026, 9, 6), count=3)],
    )
    catalog_factory = _catalog_factory(algorithms_total=12, problems_total=8)

    svc = DashboardService(
        progress_service=progress,
        readiness=readiness,
        skill_mapper=skill,
        focus_selector=focus,
        streak=streak,
        catalog_session_factory=catalog_factory,
    )

    summary = await svc.get_summary(user_id=_uuid())
    assert isinstance(summary, DashboardSummary)
    assert summary.algorithms_learned == 3
    assert summary.algorithms_total == 12
    assert summary.problems_solved == 2
    assert summary.problems_total == 8
    assert summary.interview_readiness.score == 72
    assert summary.skill_mapping[0].topic_slug == "dp"
    assert summary.focus_areas[0].topic_slug == "dp"
    assert summary.current_streak == 5
    assert len(summary.activity) == 1
    assert len(summary.recently_viewed) == 1


# ---------------------------------------------------------------------------
# Empty / zero edge cases
# ---------------------------------------------------------------------------


async def test_get_summary_handles_zero_progress() -> None:
    """No progress anywhere produces a zeroed summary."""
    progress = _progress_stub(
        overview=ProgressOverviewResponse(
            algorithms=ProgressOverviewCounts(
                completed=0, in_progress=0, total=0
            ),
            problems=ProgressOverviewCounts(
                completed=0, in_progress=0, total=0
            ),
        ),
        recents=RecentsListResponse(items=[]),
    )
    readiness = _readiness_stub(ReadinessMetric(score=0, breakdown=[]))
    skill = _skill_stub([])
    focus = _focus_stub([])
    streak = _streak_stub(current=0, activity=[])
    catalog_factory = _catalog_factory(algorithms_total=0, problems_total=0)

    svc = DashboardService(
        progress_service=progress,
        readiness=readiness,
        skill_mapper=skill,
        focus_selector=focus,
        streak=streak,
        catalog_session_factory=catalog_factory,
    )
    summary = await svc.get_summary(user_id=_uuid())
    assert summary.algorithms_learned == 0
    assert summary.problems_solved == 0
    assert summary.current_streak == 0
    assert summary.focus_areas == []
    assert summary.recently_viewed == []


# ---------------------------------------------------------------------------
# Wiring verification
# ---------------------------------------------------------------------------


async def test_get_summary_invokes_every_dependency() -> None:
    """Sanity: every calculator and progress method is awaited."""
    progress = _progress_stub(
        overview=ProgressOverviewResponse(
            algorithms=ProgressOverviewCounts(
                completed=0, in_progress=0, total=0
            ),
            problems=ProgressOverviewCounts(
                completed=0, in_progress=0, total=0
            ),
        ),
        recents=RecentsListResponse(items=[]),
    )
    readiness = _readiness_stub(ReadinessMetric(score=0, breakdown=[]))
    skill = _skill_stub([])
    focus = _focus_stub([])
    streak = _streak_stub(current=0, activity=[])
    catalog_factory = _catalog_factory(0, 0)

    svc = DashboardService(
        progress_service=progress,
        readiness=readiness,
        skill_mapper=skill,
        focus_selector=focus,
        streak=streak,
        catalog_session_factory=catalog_factory,
    )
    user_id = _uuid()
    await svc.get_summary(user_id=user_id)
    readiness.compute.assert_awaited_once_with(user_id)
    skill.compute.assert_awaited_once_with(user_id)
    focus.select_focus_areas.assert_awaited_once_with(user_id)
    streak.activity_feed.assert_awaited_once_with(user_id)
    streak.current_streak.assert_awaited_once_with(user_id)
    progress.get_overview.assert_awaited_once_with(user_id)
    progress.list_recents.assert_awaited_once_with(user_id)


async def test_recents_are_converted_to_dashboard_shape() -> None:
    """``recently_viewed`` carries RecentItem (not RecentItemResponse)."""
    progress = _progress_stub(
        overview=ProgressOverviewResponse(
            algorithms=ProgressOverviewCounts(
                completed=0, in_progress=0, total=0
            ),
            problems=ProgressOverviewCounts(
                completed=0, in_progress=0, total=0
            ),
        ),
        recents=RecentsListResponse(
            items=[
                RecentItemResponse(
                    id=_uuid(),
                    item_type="problem",
                    item_id=_uuid(),
                    viewed_at=datetime.now(UTC),
                )
            ]
        ),
    )
    svc = DashboardService(
        progress_service=progress,
        readiness=_readiness_stub(ReadinessMetric(score=0, breakdown=[])),
        skill_mapper=_skill_stub([]),
        focus_selector=_focus_stub([]),
        streak=_streak_stub(current=0, activity=[]),
        catalog_session_factory=_catalog_factory(0, 0),
    )
    summary = await svc.get_summary(user_id=_uuid())
    assert len(summary.recently_viewed) == 1
    assert isinstance(summary.recently_viewed[0], RecentItem)
    assert summary.recently_viewed[0].item_type == "problem"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _uuid() -> Any:
    from uuid import uuid4

    return uuid4()


def _progress_stub(
    *, overview: ProgressOverviewResponse, recents: RecentsListResponse
) -> Any:
    class _Stub:
        def __init__(self) -> None:
            self.get_overview = AsyncMock(return_value=overview)
            self.list_recents = AsyncMock(return_value=recents)

    return _Stub()


def _readiness_stub(metric: ReadinessMetric) -> ReadinessCalculatorProtocol:
    class _Stub:
        def __init__(self) -> None:
            self.compute = AsyncMock(return_value=metric)

    return _Stub()


def _skill_stub(metrics: list[SkillMetric]) -> SkillMapperProtocol:
    class _Stub:
        def __init__(self) -> None:
            self.compute = AsyncMock(return_value=metrics)

    return _Stub()


def _focus_stub(focus_areas: list[FocusArea]) -> FocusAreaSelectorProtocol:
    class _Stub:
        def __init__(self) -> None:
            self.select_focus_areas = AsyncMock(return_value=focus_areas)

    return _Stub()


def _streak_stub(
    *, current: int, activity: list[ActivityPoint]
) -> StreakCalculatorProtocol:
    class _Stub:
        def __init__(self) -> None:
            self.current_streak = AsyncMock(return_value=current)
            self.activity_feed = AsyncMock(return_value=activity)

    return _Stub()


def _catalog_factory(
    algorithms_total: int, problems_total: int
) -> Any:
    """Build a no-arg callable that yields an AsyncSession-shaped
    object whose ``.execute(...).scalar_one()`` returns the
    requested counts (in order: algorithms, problems).
    """
    from contextlib import asynccontextmanager

    values = iter([algorithms_total, problems_total])

    @asynccontextmanager
    async def _ctx() -> Any:
        session = MagicMock()
        proxy = MagicMock()
        proxy.scalar_one = MagicMock(side_effect=lambda: next(values))
        session.execute = AsyncMock(return_value=proxy)
        yield session

    def _factory() -> Any:
        return _ctx()

    return _factory
