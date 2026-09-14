"""Focus-area calculator — top-N weakest topics the user should work on next.

Owns ONE reason to change: the policy that decides which
topic(s) the dashboard surfaces as the user's "next focus".
The orchestrator delegates here so the selection policy
(rank by what? severity buckets? cap at N?) lives in a
single file.

Selection policy
----------------
1. Pull the per-topic mastery list (same shape as the skill
   mapper's output) for ``user_id``.
2. Sort ascending by mastery — weakest first.
3. Drop topics the user has fully completed (mastery >= 100);
   the dashboard does not re-suggest "finished" work.
4. Take the top ``FOCUS_LIMIT`` topics.
5. Compute severity per topic:
   - ``high``   : mastery <= 30
   - ``medium`` : mastery <= 60
   - ``low``    : mastery  > 60
6. Build a rationale string that the frontend renders as the
   chip tooltip.

Why FOCUS_LIMIT = 3
-------------------
The design SVG ("Dashboard — AlgoVision.svg") shows three
focus chips. The number is small on purpose: too many
suggestions dilute attention. If the design changes, change
this constant — the orchestrator doesn't need to know.

Why "mastery <= 100" completion filter
--------------------------------------
If a topic's average mastery is 100, every algorithm the
user has touched in it is at 100%. Suggesting "more focus
on DP" when DP is done is unhelpful. We exclude fully-
mastered topics from focus entirely.

Why severity thresholds are hard-coded here
------------------------------------------
A/B-testing different bands later would replace this file
in its entirety (it's the only one that owns the
thresholds). Keeping them here satisfies SRP: one reason to
change ("what counts as 'high severity'") = one file.

Refs: ALGOVISION_BACKEND_PLAN.md §5 (B5.10 — FocusAreaSelector)
Refs: ARCHITECTURE.md §7 (ADR-002)
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from src.modules.dashboard.calculators.skill_mapper import (
    SkillMapperProtocol,
)
from src.modules.dashboard.schemas import FocusArea, FocusSeverity, SkillMetric

# Top-N weak topics surfaced on the dashboard. Matches the
# three focus chips in the design SVG.
FOCUS_LIMIT = 3

# Mastery threshold below which a topic is "high" severity
# (the chip renders red). Tunable here, only here.
HIGH_SEVERITY_THRESHOLD = 30

# Mastery threshold below which a topic is "medium" severity
# (the chip renders amber). Above this and below 100 is
# "low" (grey).
MEDIUM_SEVERITY_THRESHOLD = 60


class FocusAreaSelectorProtocol(Protocol):
    """Interface the orchestrator depends on (DIP)."""

    async def select_focus_areas(
        self, user_id: UUID
    ) -> list[FocusArea]: ...


class FocusAreaSelector:
    """Re-uses the skill mapper's per-topic mastery summary.

    This is the only calculator that depends on another
    calculator — and the dependency is on the *Protocol*,
    not the concrete class, so it's still DIP-clean.
    """

    def __init__(self, skill_mapper: SkillMapperProtocol) -> None:
        self._skill_mapper = skill_mapper

    async def select_focus_areas(
        self, user_id: UUID
    ) -> list[FocusArea]:
        """Return up to ``FOCUS_LIMIT`` weakest topics (excl. done)."""
        skill_metrics = await self._skill_mapper.compute(user_id)

        # Filter out topics where mastery is already 100.
        in_progress = [m for m in skill_metrics if m.mastery < 100]

        # Weakest first.
        in_progress.sort(key=lambda m: m.mastery)

        chosen = in_progress[:FOCUS_LIMIT]
        return [
            FocusArea(
                topic_slug=m.topic_slug,
                topic_name=m.topic_name,
                severity=_classify_severity(m.mastery),
                mastery=m.mastery,
                rationale=_build_rationale(m),
            )
            for m in chosen
        ]


# ---------------------------------------------------------------------------
# Pure helpers (testable without a session)
# ---------------------------------------------------------------------------


def _classify_severity(mastery: int) -> FocusSeverity:
    """Bucket a mastery score into a severity tier.

    Pure function so unit tests can call it without
    constructing the calculator.
    """
    if mastery <= HIGH_SEVERITY_THRESHOLD:
        return "high"
    if mastery <= MEDIUM_SEVERITY_THRESHOLD:
        return "medium"
    return "low"


def _build_rationale(metric: SkillMetric) -> str:
    """Build the human-readable rationale shown on the focus chip.

    Pure function so unit tests can pass a hand-built
    ``SkillMetric`` and assert the string output without
    standing up a calculator.
    """
    if metric.algorithms_total == 0:
        return (
            f"You've started {metric.topic_name} but haven't "
            f"completed any algorithms yet."
        )
    return (
        f"Average mastery in {metric.topic_name} is "
        f"{metric.mastery}% across {metric.algorithms_completed} "
        f"of {metric.algorithms_total} algorithms you've "
        f"touched."
    )


__all__ = [
    "FOCUS_LIMIT",
    "FocusAreaSelector",
    "FocusAreaSelectorProtocol",
]
