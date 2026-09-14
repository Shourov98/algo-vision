"""``user_algorithm_progress`` — per-user progress on a single algorithm.

Each row is the persistent state of one user x one algorithm
pair (composite PK). The row is created or updated the first
time a user views / interacts with the algorithm, and is read
by ``ProgressService.mark_algorithm`` (B5.7),
``ProgressService.get_overview`` (B5.7), and the dashboard
calculators (B5.10). Idempotency is guaranteed by the
composite PK + an ``ON CONFLICT`` upsert in the repository.

Schema overview
---------------
- user_id                 : UUID NOT NULL, FK → users.id
                            ON DELETE CASCADE, part of PK.
- algorithm_id            : UUID NOT NULL, FK → algorithms.id
                            ON DELETE CASCADE, part of PK.
- status                  : VARCHAR(16) NOT NULL, CHECK
                            ('not_started' | 'in_progress'
                             | 'completed'). Same vocabulary
                            as ``user_problem_progress``.
- completion_percentage   : SMALLINT 0..100 (CHECK). Mirrors the
                            "0..100% ring" in the design SVG
                            (``AlgoVision — Dashboard.svg``).
- first_viewed_at         : TIMESTAMPTZ NOT NULL DEFAULT now().
                            Captures the *first* viewing only
                            (set on INSERT, never updated).
- last_viewed_at          : TIMESTAMPTZ NOT NULL DEFAULT now().
                            Refreshed on every interaction;
                            indexed for the dashboard's
                            "recently viewed" feed.
- completed_at            : TIMESTAMPTZ NULLABLE. Set when the
                            user transitions to 'completed';
                            cleared on regression (advanced
                            transitions are out of scope in
                            Phase 5 — see service rules).
- total_sessions          : INT NOT NULL DEFAULT 1. Counts
                            distinct visit sessions; bumped
                            by the service, never by SQL.

Why composite PK (user_id, algorithm_id) and not a surrogate id
---------------------------------------------------------------
This row has no business meaning outside the (user, algorithm)
combination — there is never a query "give me progress row 42".
The composite PK gives us:

- free uniqueness (no separate UNIQUE needed);
- free index on user_id-first scans (PK leftmost prefix);
- a clean ON CONFLICT (user_id, algorithm_id) DO UPDATE
  upsert without a separate unique index.

Why CASCADE on both FKs
-----------------------
DATABASE_DESIGN §4.2: deleting a user removes their progress
(GDPR right-to-erasure); deleting an algorithm removes
orphaned progress rows. RESTRICT would force explicit teardown
no caller wants. Mirrors ``problem_companies`` (B4.3).

Why ``first_viewed_at`` is NOT updated on upsert
-----------------------------------------------
The service uses ``ON CONFLICT ... DO UPDATE`` with an explicit
``GREATEST(first_viewed_at, EXCLUDED.first_viewed_at)`` so the
first-view timestamp is preserved across re-POSTs. The model
column itself just declares a default.

Why ``status`` is a free-text VARCHAR, not an Enum
--------------------------------------------------
Same vocabulary as ``algorithms.difficulty`` (Phase 3) and
``problems.difficulty`` (Phase 4): the CHECK lives in the
migration, ``STATUS_VALUES`` is the Python-side mirror.

Refs: DATABASE_DESIGN.md §1 (ERD: user_algorithm_progress),
       §4 (constraints), §5 (indexes), §6 (0014)
Refs: ALGOVISION_BACKEND_PLAN.md §5 (Phase 5 — B5.1)
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID as _UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, SmallInteger, text
from sqlalchemy import String as SA_String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base

# Status is a closed vocabulary on user_*_progress tables.
# Mirrors the DIFFICULTY_VALUES pattern from Phase 3 / 4.
STATUS_VALUES: tuple[str, ...] = (
    "not_started",
    "in_progress",
    "completed",
)


class UserAlgorithmProgress(Base):
    """Per-user progress row for one algorithm.

    Persistence-only — never returned from a router (per
    PUKU_BACKEND_AGENT.md §3.1: API responses use Pydantic
    schemas). The progress service converts to
    ``UserAlgorithmProgressResponse`` before handing to the
    router (B5.4).
    """

    __tablename__ = "user_algorithm_progress"

    # ----- FK columns (also form the composite PK) -----------------------
    user_id: Mapped[_UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    algorithm_id: Mapped[_UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("algorithms.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # ----- Progress state ------------------------------------------------
    status: Mapped[str] = mapped_column(
        SA_String(16),
        nullable=False,
    )

    # 0..100 ring; CHECK constraint enforces the range at the
    # DB layer (PUKU_BACKEND_AGENT §3.5 — defence in depth).
    completion_percentage: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        server_default=text("0"),
    )

    # ----- Timestamps + counters ----------------------------------------
    # first_viewed_at: set on INSERT, preserved on upsert by
    # the repository's GREATEST(...) expression. Model default
    # is now() for the initial insert path.
    first_viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    # last_viewed_at: bumped by the repository on every upsert.
    # Indexed separately so "recently viewed" doesn't scan the
    # full PK.
    last_viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    # completed_at: nullable; set when status transitions to
    # 'completed'. Cleared on regression (out of scope v1).
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # total_sessions: monotonically incremented by the service.
    total_sessions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("1"),
    )

    # ----- Table-level CHECKs --------------------------------------------
    # The CHECK constraints live in the migration (PUKU_BACKEND_AGENT
    # §3.5 — DB is the source of truth for invariants). This list
    # is here so the model is self-documenting and so tests can
    # introspect the declared constraints without parsing the
    # migration SQL.
    __table_args__ = (
        CheckConstraint(
            "status IN ('not_started', 'in_progress', 'completed')",
            name="ck_user_algorithm_progress_status",
        ),
        CheckConstraint(
            "completion_percentage BETWEEN 0 AND 100",
            name="ck_user_algorithm_progress_pct",
        ),
    )

    def __repr__(self) -> str:
        """Identity-only repr — composite PK is the only diagnostic
        worth showing."""
        return (
            f"<UserAlgorithmProgress user_id={self.user_id} "
            f"algorithm_id={self.algorithm_id}>"
        )

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)


__all__ = ["STATUS_VALUES", "UserAlgorithmProgress"]
