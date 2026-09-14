"""Dashboard HTTP routers.

A single router file (``dashboard.py``) because the
dashboard has only one endpoint (``/summary``) in v1.

Refs: PUKU_BACKEND_AGENT.md §7 (Router Conventions)
Refs: ALGOVISION_BACKEND_PLAN.md §5 (Phase 5 — B5.12)
"""

from __future__ import annotations

from fastapi import APIRouter

from src.modules.dashboard.router.dashboard import (
    router as dashboard_router,
)

all_routers: list[APIRouter] = [dashboard_router]


__all__ = ["all_routers"]
