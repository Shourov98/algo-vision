"""Progress HTTP routers.

A single router file (``progress.py``) because all six
endpoints share the same prefix and there are no
literal-path siblings to order around.

Refs: PUKU_BACKEND_AGENT.md §7 (Router Conventions)
Refs: ALGOVISION_BACKEND_PLAN.md §5 (Phase 5 - B5.7)
"""

from __future__ import annotations

from fastapi import APIRouter

from src.modules.progress.router.progress import (
    router as progress_router,
)

all_routers: list[APIRouter] = [progress_router]


__all__ = ["all_routers"]
