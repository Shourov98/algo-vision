"""Seed data + insert function for ``algorithm_categories``.

The list is small (8 entries per DATABASE_DESIGN §2). Each row
gets a deterministic UUID so re-runs don't drift FK references
elsewhere.

Why a fixed list, not a fixture file
------------------------------------
Categories are catalog-level vocabulary; they evolve rarely
and any change is a product decision (add/remove a category).
Keeping them in code makes the seed reviewable in PRs and
version-controlled alongside the migrations.

Refs: DATABASE_DESIGN.md §7 (Seed Plan)
Refs: ALGOVISION_BACKEND_PLAN.md §3.10 (B3.10 seeds)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.catalog.models import Category
from src.seeds._common import (
    NAMESPACE_CATEGORY,
    SeedCounts,
    deterministic_uuid,
    log_seed_done,
)


@dataclass(frozen=True, slots=True)
class CategorySeed:
    """A single category seed row.

    ``sort_order`` drives the sidebar / browse order (smaller
    first). ``description`` is optional long-form text.
    """

    slug: str
    name: str
    description: str | None
    sort_order: int


# ---------------------------------------------------------------------------
# The list. Order = display order; keep stable across edits.
# ---------------------------------------------------------------------------

CATEGORIES: Final[tuple[CategorySeed, ...]] = (
    CategorySeed(
        slug="sorting",
        name="Sorting",
        description=(
            "Algorithms that arrange elements in a defined order. "
            "Core to countless interview problems."
        ),
        sort_order=10,
    ),
    CategorySeed(
        slug="searching",
        name="Searching",
        description=(
            "Algorithms that locate an element in a data structure."
        ),
        sort_order=20,
    ),
    CategorySeed(
        slug="graph",
        name="Graph",
        description=(
            "Algorithms that traverse or compute over graphs and "
            "networks."
        ),
        sort_order=30,
    ),
    CategorySeed(
        slug="dynamic-programming",
        name="Dynamic Programming",
        description=(
            "Algorithms that solve sub-problems and cache the "
            "results."
        ),
        sort_order=40,
    ),
    CategorySeed(
        slug="greedy",
        name="Greedy",
        description=(
            "Algorithms that make locally optimal choices at each "
            "step."
        ),
        sort_order=50,
    ),
    CategorySeed(
        slug="divide-and-conquer",
        name="Divide & Conquer",
        description=(
            "Algorithms that recursively split the input and "
            "combine results."
        ),
        sort_order=60,
    ),
    CategorySeed(
        slug="string",
        name="String",
        description=(
            "Algorithms that operate on text and character "
            "sequences."
        ),
        sort_order=70,
    ),
    CategorySeed(
        slug="tree",
        name="Tree",
        description=(
            "Algorithms specialized for tree-shaped data "
            "structures."
        ),
        sort_order=80,
    ),
)


# ---------------------------------------------------------------------------
# Insert
# ---------------------------------------------------------------------------


async def seed_categories(session: AsyncSession) -> SeedCounts:
    """Upsert ``CATEGORIES`` into ``algorithm_categories``.

    Idempotent: uses ``ON CONFLICT (slug) DO NOTHING`` so
    re-runs against an already-seeded database are no-ops
    (DATABASE_DESIGN §7.2).
    """
    rows = [
        {
            "id": deterministic_uuid(NAMESPACE_CATEGORY, c.slug),
            "slug": c.slug,
            "name": c.name,
            "description": c.description,
            "sort_order": c.sort_order,
        }
        for c in CATEGORIES
    ]
    stmt = (
        pg_insert(Category)
        .values(rows)
        .on_conflict_do_nothing(index_elements=["slug"])
    )
    result = await session.execute(stmt)
    await session.commit()

    # ``result.rowcount`` counts only newly inserted rows; the
    # remainder are skipped-on-conflict.
    inserted = int(result.rowcount or 0)  # type: ignore[attr-defined]
    skipped = len(rows) - inserted
    counts = SeedCounts(inserted=inserted, skipped=skipped)
    log_seed_done("categories", counts)
    return counts


async def existing_category_slugs(session: AsyncSession) -> set[str]:
    """Return the set of slugs already present in the DB.

    Used by the algorithm seed to verify FK targets exist
    before insert. Returns an empty set if the categories
    seed hasn't run yet — the algorithm seed then skips
    itself to avoid an FK violation on cold databases.
    """
    result = await session.execute(select(Category.slug))
    return {row[0] for row in result.all()}


__all__ = [
    "CATEGORIES",
    "CategorySeed",
    "existing_category_slugs",
    "seed_categories",
]
