"""Insert function for ``algorithm_code_versions``.

The catalog of code snippets lives in
``algorithm_code_versions_data.py`` (split out to keep this
file under the 400-line cap, GIT_WORKFLOW §12).

Idempotency strategy
--------------------
Each (algorithm, language, version) tuple is identified in
the DB by a deterministic UUID seeded from
``NAMESPACE_CODE_VERSION``. Re-runs hit
``ON CONFLICT (id) DO NOTHING`` so they are safe. Updating
source code in the seed (a content edit) requires bumping
the version — that lands when the edit flow ships.

Refs: DATABASE_DESIGN.md §7 (Seed Plan), §7.2 (Idempotency)
Refs: ALGOVISION_BACKEND_PLAN.md §3.10 (B3.10 seeds)
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.catalog.models import Algorithm, AlgorithmCodeVersion
from src.seeds._common import (
    NAMESPACE_ALGORITHM,
    NAMESPACE_CODE_VERSION,
    SeedCounts,
    deterministic_uuid,
    log_seed_done,
)
from src.seeds.algorithm_code_versions_data import CODE_VERSIONS


async def seed_algorithm_code_versions(
    session: AsyncSession,
    *,
    known_algorithm_slugs: set[str],
) -> SeedCounts:
    """Upsert ``CODE_VERSIONS`` rows.

    Rows whose ``algorithm_slug`` isn't in
    ``known_algorithm_slugs`` are skipped — they would
    violate the FK anyway.
    """
    qualifying = [
        c for c in CODE_VERSIONS if c.algorithm_slug in known_algorithm_slugs
    ]
    skipped_missing_alg = len(CODE_VERSIONS) - len(qualifying)
    if not qualifying:
        counts = SeedCounts(inserted=0, skipped=len(CODE_VERSIONS))
        log_seed_done("algorithm_code_versions", counts)
        return counts

    rows = [
        {
            "id": deterministic_uuid(
                NAMESPACE_CODE_VERSION,
                f"{c.algorithm_slug}:{c.language}:1",
            ),
            "algorithm_id": deterministic_uuid(
                NAMESPACE_ALGORITHM, c.algorithm_slug
            ),
            "language": c.language,
            "version": 1,
            "source_code": c.source_code,
            "is_current": True,
        }
        for c in qualifying
    ]
    stmt = (
        pg_insert(AlgorithmCodeVersion)
        .values(rows)
        .on_conflict_do_nothing(index_elements=["id"])
    )
    result = await session.execute(stmt)
    await session.commit()

    inserted = int(result.rowcount or 0)  # type: ignore[attr-defined]
    counts = SeedCounts(
        inserted=inserted,
        skipped=(len(CODE_VERSIONS) - inserted) + skipped_missing_alg,
    )
    log_seed_done("algorithm_code_versions", counts)
    return counts


async def existing_algorithm_slugs(session: AsyncSession) -> set[str]:
    """Return the set of algorithm slugs already present.

    Used by the code-version seed to verify the FK target.
    """
    result = await session.execute(select(Algorithm.slug))
    return {row[0] for row in result.all()}


__all__ = [
    "existing_algorithm_slugs",
    "seed_algorithm_code_versions",
]
