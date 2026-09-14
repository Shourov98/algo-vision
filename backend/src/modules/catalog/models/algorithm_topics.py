"""``algorithm_topics`` association table — pure M:N.

This is a pure join table between ``algorithms`` and ``topics``.
No mapped class is declared because there are no per-row
attributes — every column is part of the FK or PK. SQLAlchemy
2.x idiom for this case is a ``Table`` registered on the shared
``Base.metadata``.

Why no mapped class
-------------------
- The table has no payload columns to read or write beyond the
  composite PK.
- We never query ``algorithm_topics`` as ORM objects; we always
  traverse the relationship via ``algorithm.topics`` /
  ``topic.algorithms`` (the latter arriving when we add the
  ``relationship`` in B3.5/Phase 4 if needed).
- Treating it as a ``Table`` keeps autogenerate clean and
  avoids leaking a useless mapped class.

Why a separate file
-------------------
The 400-line file-size rule (GIT_WORKFLOW.md §12) and the
per-entity split pattern (PUKU_BACKEND_AGENT §3.7) keep every
model in its own file. This file is small but it owns the
association schema, so it gets its own home.

Refs: DATABASE_DESIGN.md §1 (ERD: algorithm_topics), §4
       (constraints), §5 (indexes), §6 (0007)
"""

from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Table

from src.core.db import Base

algorithm_topics = Table(
    "algorithm_topics",
    Base.metadata,
    Column(
        "algorithm_id",
        # PostgreSQL UUID matches Algorithm.id. We intentionally
        # do NOT use a Python-side type (no as_uuid=True) here:
        # the table is never queried as ORM, and the FK is
        # emitted verbatim by migrations and Alembic.
        # The exact type is handled by the migration's
        # sa.dialects.postgresql.UUID(as_uuid=True) emission.
        ForeignKey("algorithms.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "topic_id",
        ForeignKey("topics.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
)


__all__ = ["algorithm_topics"]
