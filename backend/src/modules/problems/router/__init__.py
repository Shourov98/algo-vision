"""Problems HTTP routers.

Two per-entity files, each focused on its endpoint shape:

- ``problems``  : /api/v1/problems/*
- ``companies`` : /api/v1/problems/companies/*

Both are aggregated into the ``all_routers`` list so
``main.py`` can include them in one statement.

Order matters: routers with static-path siblings
(``/problems/companies``) must be included BEFORE routers
with variable path params (``/problems/{slug}``) so the
latter does not swallow the former as a slug literal.

Refs: PUKU_BACKEND_AGENT.md §7 (Router Conventions)
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 4 - B4.8)
"""

from __future__ import annotations

from fastapi import APIRouter

from src.modules.problems.router.companies import (
    router as companies_router,
)
from src.modules.problems.router.problems import (
    router as problems_router,
)

# Order: companies BEFORE problems so ``/problems/{slug}``
# does not match the literal ``companies`` segment.
all_routers: list[APIRouter] = [
    companies_router,
    problems_router,
]


__all__ = ["all_routers"]
