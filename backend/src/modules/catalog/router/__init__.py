"""Catalog HTTP routers.

Four per-entity files, each focused on its endpoint shape:

- ``algorithms``        : /api/v1/algorithms/*
- ``categories``        : /api/v1/algorithms/categories/*
- ``data_structures``   : /api/v1/data-structures/*
- ``topics``            : /api/v1/topics/*

All four are aggregated into the ``all_routers`` list so
``main.py`` can include them in one statement.

Refs: PUKU_BACKEND_AGENT.md §7 (Router Conventions)
Refs: ALGOVISION_BACKEND_PLAN.md §3.8 (B3.8 routers)
"""

from __future__ import annotations

from fastapi import APIRouter

from src.modules.catalog.router.algorithms import router as algorithms_router
from src.modules.catalog.router.categories import router as categories_router
from src.modules.catalog.router.data_structures import (
    router as data_structures_router,
)
from src.modules.catalog.router.topics import router as topics_router

# Per-prefix list — ``main.py`` iterates and includes each.
# Order matters: routers with static paths (categories) must
# be included BEFORE routers with variable path params
# (algorithms /{slug}) so the latter does not swallow the
# former.
all_routers: list[APIRouter] = [
    categories_router,
    algorithms_router,
    data_structures_router,
    topics_router,
]


__all__ = ["all_routers"]
