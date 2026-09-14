"""Catalog seed scripts.

Lives at ``src/seeds/`` per DATABASE_DESIGN.md §7.3.
Idempotent re-runs are supported via
``ON CONFLICT (slug) DO NOTHING`` and deterministic UUIDs.

Run with::

    python -m src.seeds.runner

Refs: DATABASE_DESIGN.md §7 (Seed Plan)
Refs: ALGOVISION_BACKEND_PLAN.md §3.10 (B3.10 seeds)
"""

from __future__ import annotations

from src.seeds.runner import main, run_seeds

__all__ = ["main", "run_seeds"]
