"""``user_problem_progress`` — per-user progress on a single problem.

Mirrors ``user_algorithm_progress`` but problem progress is
simpler: there is no percentage ring (problems are atomic
— either you've solved it or you haven't), so we carry
``attempts`` instead of ``completion_percentage``.

Schema overview
---------------
- user_id                 : UUID NOT NULL, FK → users.id
                            ON DELETE CASCADE, part of PK.
- problem_id              : UUID NOT NULL, FK → problems.id
                            ON DELETE CASCADE, part of PK.
- status                  : VARCHAR(16) NOT NULL, CHECK
                            ('not_started' | 'in_progress'
                             | 'completed').
- attempts                : INT NOT NULL DEFAULT 1. Counts
                            distinct solve attempts; bumped
                            by the service, never by SQL.
- first_viewed_at         : TIMESTAMPTZ NOT NULL DEFAULT now().
                            Preserved across upserts.
- last_viewed_at          : TIMESTAMPTZ NOT NULL DEFAULT now().
                            Bumped on every interaction.
- completed_at            : TIMESTAMPTZ NULLABLE.

Why no completion_percentage
----------------------------
Problems are atomic questions ("reverse a linked list"), not
progressive skills like algorithms ("master quicksort").
A problem either has a solution the user wrote or doesn't —
percentage would be misleading. ``attempts`` captures the
useful signal: how many tries before they got it.

Shares STATUS_VALUES with user_algorithm_progress
------------------------------------------------
Same vocabulary across the two tables lets the dashboard
render a single combined "progress by status" overview. We
keep one Python constant in this module that mirrors the
CHECK; the model file is the canonical Python mirror even
though the constant exists in ``user_algorithm_progress``
too. Importing from the sibling module would create a
cross-model dependency that is incidental, not
architectural.

Refs: DATABASE_DESIGN.md §1 (ERD: user_problem_progress),
       §4 (constraints), §5 (indexes), §6 (0015)
Refs: ALGOVISION_BACKEND_PLAN.md §5 (Phase 5 — B5.2)
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID as _UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, text
from sqlalchemy import String as SA_String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class UserProblemProgress(Base):
    """Per-user progress row for one problem.

    Persistence-only — never returned from a router. The
    progress service converts to ``UserProblemProgressResponse``
    (B5.4) before handing to the router.
    """

    __tablename__ = "user_problem_progress"

    # ----- FK columns (also form the composite PK) -----------------------
    user_id: Mapped[_UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    problem_id: Mapped[_UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("problems.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # ----- Progress state ------------------------------------------------
    status: Mapped[str] = mapped_column(
        SA_String(16),
        nullable=False,
    )

    # ----- Attempts + timestamps ----------------------------------------
    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("1"),
    )

    first_viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    last_viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ----- Table-level CHECKs --------------------------------------------
    __table_args__ = (
        CheckConstraint(
            "status IN ('not_started', 'in_progress', 'completed')",
            name="ck_user_problem_progress_status",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<UserProblemProgress user_id={self.user_id} "
            f"problem_id={self.problem_id}>"
        )

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)


__all__ = ["UserProblemProgress"]
