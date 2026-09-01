"""``problem_topics`` M:N table — problems tagged with topics.

Many-to-many between ``problems`` and ``topics``. A problem can
be tagged with multiple topics (e.g. "LRU Cache" is both
"hash-map" and "linked-list"), and a topic aggregates many
problems (e.g. "dynamic-programming" → 30+ problems).

Schema overview
---------------
- problem_id : UUID NOT NULL, FK → problems.id, part of
               composite PK.
- topic_id   : UUID NOT NULL, FK → topics.id, part of
               composite PK.

Composite PK enforcement is the only constraint beyond the
FKs — there is no separate UNIQUE because the PK already
guarantees uniqueness (§4.2 of DATABASE_DESIGN).

Mirrors ``algorithm_topics`` semantics, FKs are the only
difference. Why CASCADE on both is documented in the
migration.

Refs: DATABASE_DESIGN.md §1 (ERD: problem_topics), §4
       (constraints), §6 (0012)
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 4 — Problems, B4.3)
"""

from __future__ import annotations

from uuid import UUID as _UUID

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class ProblemTopic(Base):
    """M:N row associating a problem with a topic."""

    __tablename__ = "problem_topics"

    # ----- FK columns (also form the composite PK) -------------------------
    problem_id: Mapped[_UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("problems.id", ondelete="CASCADE"),
        primary_key=True,
    )
    topic_id: Mapped[_UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("topics.id", ondelete="CASCADE"),
        primary_key=True,
    )

    def __repr__(self) -> str:
        """Identity-only repr — PK pair is the only diagnostic worth showing."""
        return f"<ProblemTopic problem_id={self.problem_id} topic_id={self.topic_id}>"

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)


__all__ = ["ProblemTopic"]
