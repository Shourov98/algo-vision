"""Seed data + insert function for ``data_structures``.

Eight canonical entries per DATABASE_DESIGN §2 (covers the
common interview set: linear + tree + hash). The list is
small enough to keep inline; growing past 50 would justify a
data file.

Refs: DATABASE_DESIGN.md §7 (Seed Plan)
Refs: ALGOVISION_BACKEND_PLAN.md §3.10 (B3.10 seeds)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.catalog.models import DataStructure
from src.seeds._common import (
    NAMESPACE_DATA_STRUCTURE,
    SeedCounts,
    deterministic_uuid,
    log_seed_done,
)


@dataclass(frozen=True, slots=True)
class DataStructureSeed:
    """A single data-structure seed row.

    Note: the model has no ``updated_at`` column — see
    ``models/data_structure.py`` for the rationale. ETag
    support therefore doesn't apply (B3.9 / §3.9).
    """

    slug: str
    name: str
    description: str
    difficulty: str
    visualization_type: str


DATA_STRUCTURES: Final[tuple[DataStructureSeed, ...]] = (
    DataStructureSeed(
        slug="array",
        name="Array",
        description=(
            "Contiguous, index-addressable collection of elements "
            "with O(1) random access."
        ),
        difficulty="easy",
        visualization_type="linear",
    ),
    DataStructureSeed(
        slug="linked-list",
        name="Linked List",
        description=(
            "Linear collection where each element points to the next. "
            "O(1) insertion at a known position; O(n) random access."
        ),
        difficulty="easy",
        visualization_type="linear",
    ),
    DataStructureSeed(
        slug="stack",
        name="Stack",
        description=(
            "Last-in / first-out collection. O(1) push and pop."
        ),
        difficulty="easy",
        visualization_type="linear",
    ),
    DataStructureSeed(
        slug="queue",
        name="Queue",
        description=(
            "First-in / first-out collection. O(1) enqueue and "
            "dequeue."
        ),
        difficulty="easy",
        visualization_type="linear",
    ),
    DataStructureSeed(
        slug="hash-map",
        name="Hash Map",
        description=(
            "Key-value store with average-case O(1) lookup using "
            "a hash function."
        ),
        difficulty="medium",
        visualization_type="linear",
    ),
    DataStructureSeed(
        slug="binary-tree",
        name="Binary Tree",
        description=(
            "Hierarchical structure where each node has up to two "
            "children. Forms the basis for BST, AVL, and heaps."
        ),
        difficulty="medium",
        visualization_type="tree",
    ),
    DataStructureSeed(
        slug="binary-search-tree",
        name="Binary Search Tree",
        description=(
            "Ordered binary tree: left child < parent < right child. "
            "Average O(log n) lookup, worst O(n) unbalanced."
        ),
        difficulty="medium",
        visualization_type="tree",
    ),
    DataStructureSeed(
        slug="heap",
        name="Heap",
        description=(
            "Nearly-complete binary tree satisfying the heap "
            "property. O(1) peek, O(log n) insert / extract."
        ),
        difficulty="medium",
        visualization_type="tree",
    ),
)


async def seed_data_structures(session: AsyncSession) -> SeedCounts:
    """Upsert ``DATA_STRUCTURES`` into ``data_structures``.

    Idempotent via ``ON CONFLICT (slug) DO NOTHING``.
    """
    rows = [
        {
            "id": deterministic_uuid(NAMESPACE_DATA_STRUCTURE, d.slug),
            "slug": d.slug,
            "name": d.name,
            "description": d.description,
            "difficulty": d.difficulty,
            "visualization_type": d.visualization_type,
        }
        for d in DATA_STRUCTURES
    ]
    stmt = (
        pg_insert(DataStructure)
        .values(rows)
        .on_conflict_do_nothing(index_elements=["slug"])
    )
    result = await session.execute(stmt)
    await session.commit()

    inserted = int(result.rowcount or 0)  # type: ignore[attr-defined]
    skipped = len(rows) - inserted
    counts = SeedCounts(inserted=inserted, skipped=skipped)
    log_seed_done("data_structures", counts)
    return counts


__all__ = [
    "DATA_STRUCTURES",
    "DataStructureSeed",
    "seed_data_structures",
]
