"""Dashboard calculators (one formula per file).

Each calculator owns exactly one reason to change and exposes a
Protocol so DashboardAggregator (the orchestrator) depends on the
abstraction (DIP).

- readiness.py   ReadinessCalculatorProtocol  -- compute skill readiness %
- skill_map.py   SkillMapperProtocol          -- map skills -> categories
- focus_area.py  FocusAreaSelectorProtocol     -- choose weakest area
- streak.py      StreakCalculatorProtocol      -- count consecutive days

Refs: PUKU_BACKEND_AGENT.md §3.2 (SOLID — ISP + DIP)
Refs: ALGOVISION_BACKEND_PLAN.md §5 (DashboardService split)
Refs: ARCHITECTURE.md §7 (ADR-002)
"""