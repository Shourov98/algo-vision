"""Seed data + insert function for ``topics``.

Topics are reusable tags shared between algorithms (Phase 3)
and problems (Phase 4). They are static catalog vocabulary —
no creation API in v1 (per the model docstring in
``modules/catalog/models/topic.py``).

Refs: DATABASE_DESIGN.md §7 (Seed Plan)
Refs: ALGOVISION_BACKEND_PLAN.md §3.10 (B3.10 seeds)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Final

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.catalog.models import Topic
from src.seeds._common import (
    NAMESPACE_TOPIC,
    SeedCounts,
    deterministic_uuid,
    log_seed_done,
)


@dataclass(frozen=True, slots=True)
class TopicSeed:
    """A single topic seed row.

    Topics are short labels — no description, no timestamp
    (see ``models/topic.py``).
    """

    slug: str
    name: str


# ---------------------------------------------------------------------------
# The list. Cross-cutting concepts likely to appear on many algorithms.
# ---------------------------------------------------------------------------

TOPICS: Final[tuple[TopicSeed, ...]] = (
    TopicSeed(slug="in-place", name="In-place"),
    TopicSeed(slug="stable", name="Stable"),
    TopicSeed(slug="divide-and-conquer", name="Divide & Conquer"),
    TopicSeed(slug="greedy", name="Greedy"),
    TopicSeed(slug="memoization", name="Memoization"),
    TopicSeed(slug="recursion", name="Recursion"),
    TopicSeed(slug="backtracking", name="Backtracking"),
    TopicSeed(slug="bit-manipulation", name="Bit Manipulation"),
    TopicSeed(slug="two-pointers", name="Two Pointers"),
    TopicSeed(slug="sliding-window", name="Sliding Window"),
    TopicSeed(slug="heap", name="Heap"),
    TopicSeed(slug="hashing", name="Hashing"),
    TopicSeed(slug="bfs", name="BFS"),
    TopicSeed(slug="dfs", name="DFS"),
    TopicSeed(slug="dijkstra", name="Dijkstra"),
    TopicSeed(slug="bellman-ford", name="Bellman-Ford"),
    TopicSeed(slug="floyd-warshall", name="Floyd-Warshall"),
    TopicSeed(slug="kruskal", name="Kruskal"),
    TopicSeed(slug="prim", name="Prim"),
    TopicSeed(slug="topological-sort", name="Topological Sort"),
    TopicSeed(slug="union-find", name="Union Find"),
    TopicSeed(slug="trie", name="Trie"),
    TopicSeed(slug="segment-tree", name="Segment Tree"),
    TopicSeed(slug="binary-search", name="Binary Search"),
    TopicSeed(slug="kmp", name="KMP"),
    TopicSeed(slug="rabin-karp", name="Rabin-Karp"),
)


async def seed_topics(session: AsyncSession) -> SeedCounts:
    """Upsert ``TOPICS`` into ``topics``.

    Idempotent: ``ON CONFLICT (slug) DO NOTHING`` per
    DATABASE_DESIGN §7.2.
    """
    rows = [
        {
            "id": deterministic_uuid(NAMESPACE_TOPIC, t.slug),
            "slug": t.slug,
            "name": t.name,
        }
        for t in TOPICS
    ]
    stmt = (
        pg_insert(Topic)
        .values(rows)
        .on_conflict_do_nothing(index_elements=["slug"])
    )
    result = await session.execute(stmt)
    await session.commit()

    inserted = int(result.rowcount or 0)  # type: ignore[attr-defined]
    skipped = len(rows) - inserted
    counts = SeedCounts(inserted=inserted, skipped=skipped)
    log_seed_done("topics", counts)
    return counts


async def existing_topic_slugs(session: AsyncSession) -> set[str]:
    """Return the set of topic slugs already present.

    Used by the algorithm seed to map topic_slug -> topic_id
    for the M:N join in ``algorithm_topics``. If the topics
    seed hasn't run yet, returns an empty set and the
    algorithm seed records zero topic links (without raising).
    """
    result = await session.execute(select(Topic.slug))
    return {row[0] for row in result.all()}


async def topic_id_by_slug(
    session: AsyncSession, slugs: set[str]
) -> dict[str, uuid.UUID]:
    """Map topic slugs to their deterministic UUIDs.

    Returns only the slugs that exist in the database — the
    caller (algorithm seed) is responsible for skipping any
    slug that didn't make the round-trip. Imported here
    rather than computed in algorithms.py so the seed code
    stays close to the entity it operates on.
    """
    from src.modules.catalog.models import Topic as TopicModel

    if not slugs:
        return {}
    result = await session.execute(
        select(TopicModel.slug).where(TopicModel.slug.in_(slugs))
    )
    present = {row[0] for row in result.all()}
    return {
        slug: deterministic_uuid(NAMESPACE_TOPIC, slug) for slug in present
    }


__all__ = [
    "TOPICS",
    "TopicSeed",
    "existing_topic_slugs",
    "seed_topics",
    "topic_id_by_slug",
]
