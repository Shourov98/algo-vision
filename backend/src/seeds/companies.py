"""Seed data + insert function for ``companies``.

Companies are an independent entity (no FKs into them
until ``problem_companies`` lands). They appear in the
catalog of "X asked Y problem" tags.

Why a fixed list, not a fixture file
------------------------------------
Companies are catalog-level vocabulary; they evolve rarely
and any change is a product decision (add/remove a
company). Keeping them in code makes the seed reviewable
in PRs and version-controlled alongside the migrations.

Count rationale
---------------
DATABASE_DESIGN §3 caps companies at <200 rows. The seed
ships a starter set of 8 well-known companies so the
problems API has content to render; the rest land as
content decisions land.

Refs: DATABASE_DESIGN.md §7 (Seed Plan), §3 (volume)
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 4 - B4.10)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.problems.models import Company
from src.seeds._common import (
    NAMESPACE_COMPANY,
    SeedCounts,
    deterministic_uuid,
    log_seed_done,
)


@dataclass(frozen=True, slots=True)
class CompanySeed:
    """A single company seed row.

    Companies are intentionally tiny — slug + display name
    only (no logo / website / description) per
    ``models/company.py`` docstring rationale.
    """

    slug: str
    name: str


# ---------------------------------------------------------------------------
# The list. Order = display order; keep stable across edits.
# ---------------------------------------------------------------------------

COMPANIES: Final[tuple[CompanySeed, ...]] = (
    CompanySeed(slug="google", name="Google"),
    CompanySeed(slug="meta", name="Meta"),
    CompanySeed(slug="amazon", name="Amazon"),
    CompanySeed(slug="microsoft", name="Microsoft"),
    CompanySeed(slug="apple", name="Apple"),
    CompanySeed(slug="netflix", name="Netflix"),
    CompanySeed(slug="uber", name="Uber"),
    CompanySeed(slug="linkedin", name="LinkedIn"),
)


# ---------------------------------------------------------------------------
# Insert
# ---------------------------------------------------------------------------


async def seed_companies(session: AsyncSession) -> SeedCounts:
    """Upsert ``COMPANIES`` into ``companies``.

    Idempotent: uses ``ON CONFLICT (slug) DO NOTHING`` so
    re-runs against an already-seeded database are no-ops
    (DATABASE_DESIGN §7.2).
    """
    rows = [
        {
            "id": deterministic_uuid(NAMESPACE_COMPANY, c.slug),
            "slug": c.slug,
            "name": c.name,
        }
        for c in COMPANIES
    ]
    stmt = (
        pg_insert(Company)
        .values(rows)
        .on_conflict_do_nothing(index_elements=["slug"])
    )
    result = await session.execute(stmt)
    await session.commit()

    inserted = int(result.rowcount or 0)  # type: ignore[attr-defined]
    skipped = len(rows) - inserted
    counts = SeedCounts(inserted=inserted, skipped=skipped)
    log_seed_done("companies", counts)
    return counts


async def existing_company_slugs(session: AsyncSession) -> set[str]:
    """Return the set of slugs already present in the DB.

    Used by the problems seed to verify FK targets exist
    before building the ``problem_companies`` join rows.
    """
    result = await session.execute(select(Company.slug))
    return {row[0] for row in result.all()}


__all__ = [
    "COMPANIES",
    "CompanySeed",
    "existing_company_slugs",
    "seed_companies",
]
