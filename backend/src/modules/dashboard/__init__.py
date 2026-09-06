"""Dashboard feature module.

Aggregates read-only analytics for the home dashboard. DashboardService
is a thin orchestrator (DIP); the formulas live in dedicated calculator
classes, each owning one reason to change.

Canonical layered structure:

    models.py       (none — dashboard is read-only aggregation)
    schemas.py      readiness, skill_map, focus_area, streak, overview
    calculators/    segregated subpackage — one formula per file
        readiness.py        ReadinessCalculator
        skill_map.py        SkillMapper
        focus_area.py       FocusAreaSelector
        streak.py           StreakCalculator
    service.py      DashboardService (orchestrator only)
    router.py       /dashboard
    tests/          unit tests for each calculator + aggregator

Each calculator exposes a Protocol so the orchestrator depends on the
abstraction (Dependency Inversion) and tests can inject stubs.

Refs: PUKU_BACKEND_AGENT.md §3.2 (SOLID — orchestrator vs. formulas)
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 5)
Refs: ARCHITECTURE.md §7 (ADR-002 — calculator pattern)
"""