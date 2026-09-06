"""Dashboard calculators (one formula per file).

Each calculator owns exactly one reason to change and exposes a
Protocol so DashboardAggregator (the orchestrator) depends on the
abstraction (DIP).

- readiness.py   ReadinessCalculatorProtocol  -- weighted score
- skill_map.py   SkillMapperProtocol          -- per-topic mastery
- focus_area.py  FocusAreaSelectorProtocol     -- weakest topic(s)
- streak.py      StreakCalculatorProtocol      -- consecutive days

Refs: PUKU_BACKEND_AGENT.md §3.2 (SOLID — ISP + DIP)
Refs: ALGOVISION_BACKEND_PLAN.md §5 (DashboardService split)
Refs: ARCHITECTURE.md §7 (ADR-002)
"""

from src.modules.dashboard.calculators.focus_selector import (
    FOCUS_LIMIT,
    FocusAreaSelector,
    FocusAreaSelectorProtocol,
)
from src.modules.dashboard.calculators.readiness import (
    ReadinessCalculator,
    ReadinessCalculatorProtocol,
)
from src.modules.dashboard.calculators.skill_mapper import (
    SkillMapper,
    SkillMapperProtocol,
)
from src.modules.dashboard.calculators.streak import (
    ACTIVITY_WINDOW_DAYS,
    StreakCalculator,
    StreakCalculatorProtocol,
)

__all__ = [
    "ACTIVITY_WINDOW_DAYS",
    "FOCUS_LIMIT",
    "FocusAreaSelector",
    "FocusAreaSelectorProtocol",
    "ReadinessCalculator",
    "ReadinessCalculatorProtocol",
    "SkillMapper",
    "SkillMapperProtocol",
    "StreakCalculator",
    "StreakCalculatorProtocol",
]
