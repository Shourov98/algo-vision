"""Seed runner — orchestrates the per-entity seed scripts.

Why a separate orchestrator (instead of inlining in each file)
--------------------------------------------------------------
The seed scripts must run in FK-dependency order:

1. Categories (no deps)
2. Topics (no deps)
3. Algorithms (depends on categories + topics)
4. Data structures (no deps — runs after Algorithms only to
   keep the log lines grouped chronologically)
5. Algorithm code versions (depends on algorithms)

Putting the order in one place makes the dependency explicit
and makes the runner a single entry point for CI.

Usage
-----
::

    python -m src.seeds.runner

Reads ``DATABASE_URL`` from the configured ``Settings`` (the
same one the app uses). The runner initialises the engine +
session factory via ``init_engine`` so seeds work whether
invoked from a unit test, a one-off script, or CI.

Failure policy
--------------
The runner is **best-effort**: an exception in one entity
seed is logged and the runner continues with the next. CI
uses exit codes 1 for failure, but the runner always exits
0 unless a catastrophic init error happens (engine can't
start). Individual seed failures are visible in the structured
log output.

Refs: DATABASE_DESIGN.md §7 (Seed Plan), §7.3 (Seed File Layout)
Refs: PUKU_BACKEND_AGENT.md §11 (Seed)
Refs: ALGOVISION_BACKEND_PLAN.md §3.10 (B3.10 seeds)
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Final

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import init_engine
from src.core.logging import log
from src.core.settings import get_settings
from src.seeds._common import SeedCounts, seed_session
from src.seeds.algorithm_code_versions import (
    seed_algorithm_code_versions,
)
from src.seeds.algorithms import seed_algorithms
from src.seeds.categories import (
    existing_category_slugs,
    seed_categories,
)
from src.seeds.companies import (
    existing_company_slugs,
    seed_companies,
)
from src.seeds.data_structures import seed_data_structures
from src.seeds.problems import seed_problems
from src.seeds.topics import (
    existing_topic_slugs,
    seed_topics,
)

# A seed step is an async callable that takes a session and
# returns the counts it produced. The runner logs the
# outcome regardless of return value.
SeedStep = Callable[[AsyncSession], Awaitable[SeedCounts]]


async def _run_step(
    name: str,
    step: SeedStep,
    session: AsyncSession,
) -> SeedCounts:
    """Run one seed step with error logging.

    Failures are logged and a zero-count result is returned
    so the runner can continue. CI can scrape the structured
    logs to detect partial seed failures.
    """
    try:
        return await step(session)
    except Exception as exc:
        log.error(
            "seed.failed",
            entity=name,
            error=type(exc).__name__,
            error_message=str(exc),
        )
        return SeedCounts(inserted=0, skipped=0)


async def run_seeds() -> None:
    """Run every seed in dependency order.

    Each step runs in its own transaction (commit at the end
    of the per-entity seed function). The session is created
    once and threaded through every step to keep the
    orchestrator cheap — there's no need to spin a fresh
    connection per step.
    """
    settings = get_settings()
    init_engine(settings)
    log.info(
        "seed.start",
        environment=settings.app_env,
        database=settings.database_url.split("@")[-1],
    )

    factory = seed_session()
    session = await factory.__anext__()
    try:
        # ---- Categories -------------------------------------------------
        await _run_step(
            "categories",
            seed_categories,
            session,
        )
        category_slugs = await existing_category_slugs(session)

        # ---- Topics -----------------------------------------------------
        await _run_step(
            "topics",
            seed_topics,
            session,
        )
        topic_slugs = await existing_topic_slugs(session)

        # ---- Algorithms (depends on categories + topics) --------------
        await _run_step(
            "algorithms",
            lambda s: seed_algorithms(
                s,
                known_category_slugs=category_slugs,
                known_topic_slugs=topic_slugs,
            ),
            session,
        )

        # ---- Data structures (independent) -----------------------------
        await _run_step(
            "data_structures",
            seed_data_structures,
            session,
        )

        # ---- Code versions (depends on algorithms) --------------------
        from src.seeds.algorithm_code_versions import (
            existing_algorithm_slugs,
        )

        algorithm_slugs = await existing_algorithm_slugs(session)
        await _run_step(
            "algorithm_code_versions",
            lambda s: seed_algorithm_code_versions(
                s,
                known_algorithm_slugs=algorithm_slugs,
            ),
            session,
        )

        # ---- Companies (independent) ------------------------------------
        await _run_step(
            "companies",
            seed_companies,
            session,
        )
        company_slugs = await existing_company_slugs(session)

        # ---- Problems (depends on topics + companies) ------------------
        await _run_step(
            "problems",
            lambda s: seed_problems(
                s,
                known_company_slugs=company_slugs,
                known_topic_slugs=topic_slugs,
            ),
            session,
        )
    finally:
        await session.close()
        log.info("seed.done")


def main() -> None:
    """Synchronous entry point for ``python -m src.seeds.runner``."""
    asyncio.run(run_seeds())


__all__: Final[tuple[str, ...]] = ("main", "run_seeds")
