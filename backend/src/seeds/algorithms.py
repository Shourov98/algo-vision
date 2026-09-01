"""Insert function for ``algorithms`` + ``algorithm_topics``.

Why insert logic lives apart from the data
------------------------------------------
The catalog list (``ALGORITHMS``) is the product surface —
reviewers see it in PRs. The insert logic is plumbing. We
keep them in separate files so each stays readable and under
the 400-line cap (GIT_WORKFLOW §12).

Algorithm count rationale
-------------------------
DATABASE_DESIGN §2 caps the catalog at ~50 algorithms in v1;
we ship 13 across the major categories so the frontend has
content to render. The remaining ~37 land as Phase 3 closes
when content decisions are made (not as a tech task).

Why we resolve FKs in the seed (not the model)
----------------------------------------------
Algorithms have an FK to ``algorithm_categories``. We resolve
the category UUID here (not in the model) so the same
``deterministic_uuid`` namespace produces identical FK
references across re-runs. The model layer stays declarative.

Refs: DATABASE_DESIGN.md §7 (Seed Plan), §7.2 (Idempotency)
Refs: ALGOVISION_BACKEND_PLAN.md §3.10 (B3.10 seeds)
"""

from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.catalog.models import Algorithm, Topic
from src.modules.catalog.models.algorithm_topics import algorithm_topics
from src.seeds._common import (
    NAMESPACE_ALGORITHM,
    NAMESPACE_CATEGORY,
    SeedCounts,
    deterministic_uuid,
    log_seed_done,
)
from src.seeds.algorithms_data import ALGORITHMS


async def seed_algorithms(
    session: AsyncSession,
    *,
    known_category_slugs: set[str],
    known_topic_slugs: set[str],
) -> SeedCounts:
    """Upsert ``ALGORITHMS`` + their topic links.

    ``known_category_slugs`` and ``known_topic_slugs`` are
    the sets returned by ``existing_category_slugs`` and
    ``existing_topic_slugs`` from the earlier seed passes.
    Rows referencing unknown slugs are skipped (so the seed
    is robust to a partially-seeded database).

    Idempotent on the algorithm insert via ``ON CONFLICT
    (slug) DO NOTHING``. Topic joins are deleted-then-inserted
    so re-runs reflect the current ``topic_slugs`` tuple.
    """
    qualifying = [
        a for a in ALGORITHMS if a.category_slug in known_category_slugs
    ]
    skipped_missing_category = len(ALGORITHMS) - len(qualifying)
    if not qualifying:
        counts = SeedCounts(inserted=0, skipped=len(ALGORITHMS))
        log_seed_done("algorithms", counts)
        return counts

    rows = [
        {
            "id": deterministic_uuid(NAMESPACE_ALGORITHM, a.slug),
            "slug": a.slug,
            "name": a.name,
            "category_id": deterministic_uuid(
                NAMESPACE_CATEGORY, a.category_slug
            ),
            "description": a.description,
            "difficulty": a.difficulty,
            "visualization_type": a.visualization_type,
            "best_time": a.best_time,
            "average_time": a.average_time,
            "worst_time": a.worst_time,
            "space_complexity": a.space_complexity,
            "is_published": True,
        }
        for a in qualifying
    ]
    stmt = (
        pg_insert(Algorithm)
        .values(rows)
        .on_conflict_do_nothing(index_elements=["slug"])
    )
    result = await session.execute(stmt)
    await session.commit()
    inserted = int(result.rowcount or 0)  # type: ignore[attr-defined]

    # ---- Topic joins (M:N) ------------------------------------------------
    # Strategy: replace existing joins for each seeded
    # algorithm. This makes the seed reflect the current
    # ``topic_slugs`` tuple (not just additive), so editing
    # the topic list here updates the DB on the next run.
    topic_lookup = await _topic_id_map(session, known_topic_slugs)
    join_rows: list[dict[str, object]] = []
    for a in qualifying:
        alg_id = deterministic_uuid(NAMESPACE_ALGORITHM, a.slug)
        for topic_slug in a.topic_slugs:
            if topic_slug not in topic_lookup:
                # Topic seed hasn't run / doesn't include this
                # slug — skip silently rather than failing
                # the whole batch.
                continue
            join_rows.append(
                {
                    "algorithm_id": alg_id,
                    "topic_id": topic_lookup[topic_slug],
                }
            )

    if join_rows:
        # Delete existing joins for these algorithm IDs then
        # re-insert from the seed tuples. The deletion uses
        # the deterministic IDs we just computed; combined
        # with the FK CASCADE on algorithm_topics, this is
        # safe even if the row was never inserted.
        alg_ids = list({r["algorithm_id"] for r in join_rows})
        await session.execute(
            delete(algorithm_topics).where(
                algorithm_topics.c.algorithm_id.in_(alg_ids)
            )
        )
        await session.execute(algorithm_topics.insert(), join_rows)
        await session.commit()

    counts = SeedCounts(
        inserted=inserted,
        skipped=(len(ALGORITHMS) - inserted) + skipped_missing_category,
    )
    log_seed_done("algorithms", counts)
    return counts


async def _topic_id_map(
    session: AsyncSession, known_slugs: set[str]
) -> dict[str, uuid.UUID]:
    """Map topic slugs to actual UUIDs in the DB.

    Re-queries the DB rather than computing deterministic
    UUIDs locally — protects against the topics table having
    rows whose UUIDs were assigned by a prior non-seed
    insert (e.g. an admin via a future endpoint).
    """
    if not known_slugs:
        return {}
    result = await session.execute(
        select(Topic.id, Topic.slug).where(Topic.slug.in_(known_slugs))
    )
    return {row.slug: row.id for row in result.all()}


__all__ = ["seed_algorithms"]
