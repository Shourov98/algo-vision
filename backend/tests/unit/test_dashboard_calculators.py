"""Dashboard calculators — unit tests for the four formulas.

Pure helper tests where possible (focus_selector, streak).
SQL-touching tests use AsyncMock-backed sessions so the
calculators can be exercised without a real DB.

Refs: ALGOVISION_BACKEND_PLAN.md §5 (Phase 5 — B5.13)
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from src.modules.dashboard.calculators.focus_selector import (
    FOCUS_LIMIT,
    FocusAreaSelector,
    _build_rationale,
    _classify_severity,
)
from src.modules.dashboard.calculators.streak import (
    StreakCalculator,
    _count_consecutive,
)
from src.modules.dashboard.schemas import SkillMetric

# ---------------------------------------------------------------------------
# focus_selector — severity classification (pure)
# ---------------------------------------------------------------------------


def test_classify_severity_high_below_threshold() -> None:
    assert _classify_severity(0) == "high"
    assert _classify_severity(30) == "high"


def test_classify_severity_medium_between_thresholds() -> None:
    assert _classify_severity(31) == "medium"
    assert _classify_severity(60) == "medium"


def test_classify_severity_low_above_threshold() -> None:
    assert _classify_severity(61) == "low"
    assert _classify_severity(99) == "low"


# ---------------------------------------------------------------------------
# focus_selector — rationale builder (pure)
# ---------------------------------------------------------------------------


def test_build_rationale_with_progress() -> None:
    metric = SkillMetric(
        topic_slug="dp",
        topic_name="Dynamic Programming",
        mastery=42,
        algorithms_completed=2,
        algorithms_total=5,
    )
    text = _build_rationale(metric)
    assert "Dynamic Programming" in text
    assert "42%" in text
    assert "2 of 5" in text


def test_build_rationale_with_zero_total() -> None:
    metric = SkillMetric(
        topic_slug="dp",
        topic_name="Dynamic Programming",
        mastery=0,
        algorithms_completed=0,
        algorithms_total=0,
    )
    text = _build_rationale(metric)
    assert "haven't completed" in text.lower()


# ---------------------------------------------------------------------------
# focus_selector — selector integration
# ---------------------------------------------------------------------------


async def test_focus_selector_returns_top_n_weakest() -> None:
    """Weakest topics come first, FOCUS_LIMIT caps the result."""
    skill = _skill_stub(
        [
            SkillMetric(
                topic_slug="hash",
                topic_name="Hashing",
                mastery=90,
                algorithms_completed=3,
                algorithms_total=3,
            ),
            SkillMetric(
                topic_slug="dp",
                topic_name="DP",
                mastery=20,
                algorithms_completed=0,
                algorithms_total=5,
            ),
            SkillMetric(
                topic_slug="graph",
                topic_name="Graph",
                mastery=45,
                algorithms_completed=1,
                algorithms_total=4,
            ),
            SkillMetric(
                topic_slug="greedy",
                topic_name="Greedy",
                mastery=70,
                algorithms_completed=2,
                algorithms_total=3,
            ),
        ]
    )
    selector = FocusAreaSelector(skill_mapper=skill)
    focus = await selector.select_focus_areas(user_id=_user_id())
    # Weakest first (mastery ASC), capped at FOCUS_LIMIT.
    assert [f.topic_slug for f in focus] == ["dp", "graph", "greedy"]
    assert len(focus) == FOCUS_LIMIT


async def test_focus_selector_excludes_completed_topics() -> None:
    """Topics at mastery=100 are excluded entirely."""
    skill = _skill_stub(
        [
            SkillMetric(
                topic_slug="hash",
                topic_name="Hashing",
                mastery=100,
                algorithms_completed=1,
                algorithms_total=1,
            ),
            SkillMetric(
                topic_slug="dp",
                topic_name="DP",
                mastery=20,
                algorithms_completed=0,
                algorithms_total=5,
            ),
        ]
    )
    selector = FocusAreaSelector(skill_mapper=skill)
    focus = await selector.select_focus_areas(user_id=_user_id())
    assert len(focus) == 1
    assert focus[0].topic_slug == "dp"


async def test_focus_selector_severity_classification() -> None:
    """Each focus entry has the right severity for its mastery."""
    skill = _skill_stub(
        [
            SkillMetric(
                topic_slug="weak",
                topic_name="Weak",
                mastery=10,
                algorithms_completed=0,
                algorithms_total=5,
            ),
            SkillMetric(
                topic_slug="mid",
                topic_name="Mid",
                mastery=50,
                algorithms_completed=1,
                algorithms_total=4,
            ),
        ]
    )
    selector = FocusAreaSelector(skill_mapper=skill)
    focus = await selector.select_focus_areas(user_id=_user_id())
    severities = {f.topic_slug: f.severity for f in focus}
    assert severities["weak"] == "high"
    assert severities["mid"] == "medium"


async def test_focus_selector_empty_when_skill_mapper_empty() -> None:
    skill = _skill_stub([])
    selector = FocusAreaSelector(skill_mapper=skill)
    focus = await selector.select_focus_areas(user_id=_user_id())
    assert focus == []


# ---------------------------------------------------------------------------
# streak — pure helper
# ---------------------------------------------------------------------------


def test_count_consecutive_zero_when_no_activity() -> None:
    assert _count_consecutive(set(), today=date(2026, 9, 6)) == 0


def test_count_consecutive_walks_back_from_today() -> None:
    today = date(2026, 9, 6)
    days = {today, today - timedelta(days=1), today - timedelta(days=2)}
    assert _count_consecutive(days, today=today) == 3


def test_count_consecutive_stops_at_first_gap() -> None:
    today = date(2026, 9, 6)
    days = {
        today,
        today - timedelta(days=1),
        # gap on day -2
        today - timedelta(days=3),
    }
    assert _count_consecutive(days, today=today) == 2


def test_count_consecutive_falls_back_to_most_recent_active_day() -> None:
    """User active 5 days ago but not today: walk back from day -5."""
    today = date(2026, 9, 6)
    days = {
        today - timedelta(days=5),
        today - timedelta(days=4),
        today - timedelta(days=3),
    }
    assert _count_consecutive(days, today=today) == 3


# ---------------------------------------------------------------------------
# skill_mapper — pure shape verification (DB-touching path is integration)
# ---------------------------------------------------------------------------


def test_skill_metric_round_trip() -> None:
    """SkillMetric is constructible and serialisable."""
    metric = SkillMetric(
        topic_slug="dp",
        topic_name="DP",
        mastery=42,
        algorithms_completed=2,
        algorithms_total=5,
    )
    assert metric.topic_slug == "dp"
    assert metric.algorithms_completed == 2


# ---------------------------------------------------------------------------
# streak — ActivityPoint count via AsyncMock session
# ---------------------------------------------------------------------------


async def test_streak_activity_feed_zero_fills_window() -> None:
    """activity_feed returns ACTIVITY_WINDOW_DAYS points, even on empty."""
    from src.modules.dashboard.calculators.streak import (
        ACTIVITY_WINDOW_DAYS,
    )

    session = _async_session_returning([])
    factory = session
    calc = StreakCalculator(session_factory=factory)
    feed = await calc.activity_feed(user_id=_user_id())
    # ACTIVITY_WINDOW_DAYS points regardless of activity.
    assert len(feed) == ACTIVITY_WINDOW_DAYS
    # Sorted ascending by date.
    assert feed[0].date < feed[-1].date


async def test_streak_current_streak_zero_when_no_activity() -> None:
    """Empty result set -> current_streak == 0."""
    session = _async_session_returning([])
    factory = session
    calc = StreakCalculator(session_factory=factory)
    assert await calc.current_streak(user_id=_user_id()) == 0


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _user_id() -> Any:
    from uuid import uuid4

    return uuid4()


def _skill_stub(metrics: list[SkillMetric]) -> Any:
    """Return a SkillMapperProtocol stub that returns ``metrics``."""

    class _Stub:
        async def compute(self, user_id: Any) -> list[SkillMetric]:
            return metrics

    return _Stub()


def _async_session_returning(rows: list[Any]) -> Any:
    """Return a no-arg callable that yields a session-like object.

    The session has an async ``execute()`` method that returns
    a result whose ``.all()`` returns ``rows``. The returned
    callable behaves like ``async_sessionmaker``: ``async with
    factory() as session:`` works.
    """
    from contextlib import asynccontextmanager

    result_proxy = MagicMock()
    result_proxy.all.return_value = rows
    execute = AsyncMock(return_value=result_proxy)
    session = MagicMock()
    session.execute = execute

    @asynccontextmanager
    async def _ctx() -> Any:
        yield session

    def _factory() -> Any:
        return _ctx()

    return _factory
