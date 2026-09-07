"""ProgressRepository — public interface.

The concrete ``ProgressRepository`` mixes two responsibility
modules:

- ``_upserts_listings.py`` : idempotent INSERT/ON CONFLICT
  + paginated SELECT LIMIT/OFFSET on the progress tables.
- ``_overview_recents.py`` : GROUP BY aggregation +
  append-log with cap-to-50 on user_recent_items.

Plus the Protocol in ``protocol.py`` (the interface the
service depends on).

Why mixin split
---------------
The single-file version of this repository was 458 lines,
over the 400-line cap (PukuBackendAgent §3.7). Splitting
the concrete class across two files via mixin keeps the
public type as a single ``ProgressRepository`` while
letting each responsibility module stay under 200 lines.
Both mixins use the same ``_session`` attribute set on
the concrete class — declared as ``_session: AsyncSession``
annotations so type-checkers see it without an explicit
``__init__`` on the mixins.

Refs: ALGOVISION_BACKEND_PLAN.md §5 (Phase 5 — B5.5)
Refs: AlgoVision_BACKEND.md §10 (Repository Conventions)
Refs: PUKU_BACKEND_AGENT.md §3.7 (file size: split by responsibility)
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.progress.repository._overview_recents import (
    ProgressOverviewAndRecents,
)
from src.modules.progress.repository._upserts_listings import (
    ProgressUpsertsAndListings,
)
from src.modules.progress.repository.protocol import (
    RECENT_ITEMS_CAP,
    ProgressRepositoryProtocol,
)


class ProgressRepository(
    ProgressUpsertsAndListings,
    ProgressOverviewAndRecents,
):
    """Async SQLAlchemy 2.x implementation.

    Single concrete class; the two mixins split the
    methods by responsibility. Liskov-substitutable for
    ``ProgressRepositoryProtocol`` so unit tests can pass
    a fake.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session


__all__ = [
    "RECENT_ITEMS_CAP",
    "ProgressRepository",
    "ProgressRepositoryProtocol",
]
