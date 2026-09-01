"""Shared helpers for catalog seed scripts.

What this module owns
---------------------
- Deterministic UUIDs for stable references across runs (so
  re-running the seed doesn't change foreign keys).
- The session factory entry point (``seed_session``) that opens
  an ``AsyncSession`` against the configured database.
- A ``SeedPayload`` dataclass capturing the (slug, ...) tuples
  for each entity so individual seed files can stay declarative.

What this module does NOT own
-----------------------------
- The per-entity insert logic (lives in the entity seed files).
- Idempotency strategy (``ON CONFLICT (slug) DO NOTHING`` is
  applied per-entity where appropriate; the shared helpers
  don't impose a policy).

Why deterministic UUIDs
-----------------------
DATABASE_DESIGN.md §7.2 mandates that re-running seeds is safe.
Two strategies are listed there; we use BOTH:

1. ``ON CONFLICT (slug) DO NOTHING`` for the insert itself so
   duplicate slugs don't raise.
2. Deterministic UUIDs derived from a namespace UUID + the slug
   so the FK columns (algorithm.category_id, etc.) are stable
   across re-runs — even if a seed script is re-run on a
   partially-populated database, the foreign-key reference
   always points to the same row.

Refs: DATABASE_DESIGN.md §7 (Seed Plan), §7.2 (Idempotency),
       §7.3 (Seed File Layout)
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_session_factory
from src.core.logging import log

# Stable namespace UUIDs keep seed FKs reproducible across
# machines and re-runs. The values are arbitrary; pick them
# once and never change them.
_NAMESPACE_CATEGORY = uuid.UUID("3f8e4d2a-1b6c-4a8f-9e7d-2c5b3a1d4e8f")
_NAMESPACE_TOPIC = uuid.UUID("7a2b8c1d-4e9f-4c3a-8b5d-1f6e9d2c3a4b")
_NAMESPACE_ALGORITHM = uuid.UUID("9c3d4e5f-6a7b-4c8d-9e0f-1a2b3c4d5e6f")
_NAMESPACE_DATA_STRUCTURE = uuid.UUID(
    "5d6e7f8a-9b0c-4d1e-8f2a-3b4c5d6e7f8a"
)
_NAMESPACE_CODE_VERSION = uuid.UUID(
    "1a2b3c4d-5e6f-4789-8abc-def012345678"
)

# Public aliases (without the leading underscore) so callers
# can import them via ``from src.seeds._common import NAMESPACE_CATEGORY``.
NAMESPACE_CATEGORY = _NAMESPACE_CATEGORY
NAMESPACE_TOPIC = _NAMESPACE_TOPIC
NAMESPACE_ALGORITHM = _NAMESPACE_ALGORITHM
NAMESPACE_DATA_STRUCTURE = _NAMESPACE_DATA_STRUCTURE
NAMESPACE_CODE_VERSION = _NAMESPACE_CODE_VERSION


def deterministic_uuid(namespace: uuid.UUID, key: str) -> uuid.UUID:
    """Return a UUID5 derived from ``(namespace, key)``.

    Deterministic for a given (namespace, key) pair, so the
    same seed row always gets the same UUID across re-runs.
    UUID5 uses SHA-1 over the namespace + key bytes.
    """
    return uuid.uuid5(namespace, key)


async def seed_session() -> AsyncIterator[AsyncSession]:
    """Yield an ``AsyncSession`` for the seed scripts.

    Mirrors the FastAPI dependency in ``core/db.py`` but
    without the FastAPI dependency machinery — seeds run
    from ``python -m src.seeds.runner`` outside a request.

    Commits at the end of each entity seed so a partial
    failure doesn't roll back the whole batch. The runner
    calls ``session.begin()`` explicitly per entity to keep
    the commit boundaries visible at the orchestrator level.
    """
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


@dataclass(frozen=True, slots=True)
class SeedCounts:
    """Per-entity insert counts returned by each seed function.

    Used by the runner to log "seeded X (skipped Y)" lines.
    """

    inserted: int
    skipped: int

    def as_log_fields(self) -> dict[str, Any]:
        return {
            "inserted": self.inserted,
            "skipped": self.skipped,
        }


def log_seed_done(entity: str, counts: SeedCounts) -> None:
    """Emit a single ``seed.done`` log record per entity.

    Keeps log output consistent across the runner — easier to
    grep in CI than ad-hoc prints.
    """
    log.info(
        "seed.done",
        entity=entity,
        **counts.as_log_fields(),
    )


__all__ = [
    "NAMESPACE_ALGORITHM",
    "NAMESPACE_CATEGORY",
    "NAMESPACE_CODE_VERSION",
    "NAMESPACE_DATA_STRUCTURE",
    "NAMESPACE_TOPIC",
    "SeedCounts",
    "deterministic_uuid",
    "log_seed_done",
    "seed_session",
]
