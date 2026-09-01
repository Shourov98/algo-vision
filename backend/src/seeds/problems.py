"""Insert function for ``problems`` + ``problem_topics`` /
``problem_companies`` join rows.

Mirrors the ``algorithms.py`` seed pattern: insert the
problem rows, then build the M:N join rows in a single
batch.

Why M:N joins live here (not in the data file)
---------------------------------------------
The data file (``problems_data.py``) lists every problem
+ its topic/company slug tuples - the product surface.
The insert logic (this file) resolves those slugs to
actual UUIDs and writes the join rows. Keeping the two
concerns separate lets reviewers see the catalog surface
without paging through SQL.

Why FKs are resolved against the live DB (not computed locally)
---------------------------------------------------------------
Topic IDs come from the catalog ``topics`` seed; we
re-query rather than computing deterministic UUIDs
locally because the topics table can be augmented by
future admin endpoints. Same rationale as
``algorithms.py``: a live query is robust to
non-deterministic IDs.

``problem_companies`` references the problems
``companies`` seed (also deterministic via
NAMESPACE_COMPANY). The companies seed runs immediately
before this one (B4.10 runner), so we can rely on the
deterministic UUID pattern here too.

Refs: DATABASE_DESIGN.md §7 (Seed Plan), §7.2
       (Idempotency)
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 4 - B4.10)
"""

from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.catalog.models import Topic
from src.modules.problems.models import (
    Company,
    Problem,
    ProblemCompany,
    ProblemTopic,
)
from src.seeds._common import (
    NAMESPACE_PROBLEM,
    SeedCounts,
    deterministic_uuid,
    log_seed_done,
)
from src.seeds.problems_data import PROBLEMS


async def seed_problems(
    session: AsyncSession,
    *,
    known_company_slugs: set[str],
    known_topic_slugs: set[str],
) -> SeedCounts:
    """Upsert ``PROBLEMS`` + their topic + company joins.

    ``known_*_slugs`` are the sets returned by
    ``existing_company_slugs`` / ``existing_topic_slugs``
    from the earlier seed passes. Rows referencing unknown
    slugs are skipped silently so the seed is robust to a
    partially-seeded database.

    Idempotent on the problem insert via ``ON CONFLICT
    (slug) DO NOTHING``. Topic / company joins are
    deleted-then-inserted so re-runs reflect the current
    ``topic_slugs`` / ``company_slugs`` tuples (not just
    additive).
    """
    rows = [
        {
            "id": deterministic_uuid(NAMESPACE_PROBLEM, p.slug),
            "slug": p.slug,
            "title": p.title,
            "description": p.description,
            "difficulty": p.difficulty,
            "solution_explanation": p.solution_explanation,
            "external_reference": p.external_reference,
            "visualization_available": p.visualization_available,
        }
        for p in PROBLEMS
    ]
    stmt = (
        pg_insert(Problem)
        .values(rows)
        .on_conflict_do_nothing(index_elements=["slug"])
    )
    result = await session.execute(stmt)
    await session.commit()
    inserted = int(result.rowcount or 0)  # type: ignore[attr-defined]

    # ---- Topic joins (M:N) ----------------------------------------------
    # Strategy: replace existing joins for each seeded
    # problem. Mirrors the algorithms.py topic-join
    # pattern.
    topic_lookup = await _topic_id_map(session, known_topic_slugs)
    company_lookup = await _company_id_map(
        session, known_company_slugs
    )

    problem_ids = [
        deterministic_uuid(NAMESPACE_PROBLEM, p.slug) for p in PROBLEMS
    ]
    topic_join_rows: list[dict[str, object]] = []
    company_join_rows: list[dict[str, object]] = []

    for problem in PROBLEMS:
        problem_id = deterministic_uuid(NAMESPACE_PROBLEM, problem.slug)
        for topic_slug in problem.topic_slugs:
            topic_id = topic_lookup.get(topic_slug)
            if topic_id is None:
                continue
            topic_join_rows.append(
                {"problem_id": problem_id, "topic_id": topic_id}
            )
        for company_slug in problem.company_slugs:
            company_id = company_lookup.get(company_slug)
            if company_id is None:
                continue
            company_join_rows.append(
                {"problem_id": problem_id, "company_id": company_id}
            )

    if topic_join_rows:
        # Replace all topic joins for these problem IDs.
        await session.execute(
            delete(ProblemTopic).where(
                ProblemTopic.problem_id.in_(problem_ids)
            )
        )
        await session.execute(
            pg_insert(ProblemTopic).values(topic_join_rows)
        )
        await session.commit()

    if company_join_rows:
        # Replace all company joins for these problem IDs.
        await session.execute(
            delete(ProblemCompany).where(
                ProblemCompany.problem_id.in_(problem_ids)
            )
        )
        await session.execute(
            pg_insert(ProblemCompany).values(company_join_rows)
        )
        await session.commit()

    counts = SeedCounts(
        inserted=inserted,
        skipped=len(PROBLEMS) - inserted,
    )
    log_seed_done("problems", counts)
    return counts


async def _topic_id_map(
    session: AsyncSession, known_slugs: set[str]
) -> dict[str, uuid.UUID]:
    """Map topic slugs to actual UUIDs in the DB.

    Re-queries the DB rather than computing deterministic
    UUIDs locally - protects against the topics table
    having rows whose UUIDs were assigned by a prior non-
    seed insert (e.g. an admin via a future endpoint).
    """
    if not known_slugs:
        return {}
    result = await session.execute(
        select(Topic.id, Topic.slug).where(Topic.slug.in_(known_slugs))
    )
    return {row.slug: row.id for row in result.all()}


async def _company_id_map(
    session: AsyncSession, known_slugs: set[str]
) -> dict[str, uuid.UUID]:
    """Map company slugs to actual UUIDs in the DB.

    Same rationale as ``_topic_id_map``.
    """
    if not known_slugs:
        return {}
    result = await session.execute(
        select(Company.id, Company.slug).where(
            Company.slug.in_(known_slugs)
        )
    )
    return {row.slug: row.id for row in result.all()}


__all__ = ["seed_problems"]
