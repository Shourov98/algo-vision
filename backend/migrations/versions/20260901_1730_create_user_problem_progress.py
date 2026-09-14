"""create_user_problem_progress

Adds the ``user_problem_progress`` table per DATABASE_DESIGN.md
§1, §4, §5.

Schema
------
- user_id                : UUID NOT NULL, FK → users.id
                           ON DELETE CASCADE, part of composite PK.
- problem_id             : UUID NOT NULL, FK → problems.id
                           ON DELETE CASCADE, part of composite PK.
- status                 : VARCHAR(16) NOT NULL, CHECK
                           ('not_started' | 'in_progress'
                            | 'completed').
- attempts               : INT NOT NULL DEFAULT 1.
- first_viewed_at        : TIMESTAMPTZ NOT NULL DEFAULT now().
- last_viewed_at         : TIMESTAMPTZ NOT NULL DEFAULT now().
- completed_at           : TIMESTAMPTZ NULL.

No completion_percentage
------------------------
DATABASE_DESIGN §1 omits a percentage column on problems
because problems are atomic questions (a binary "solved or
not" outcome), not progressive skills like algorithms. The
``attempts`` counter captures the relevant signal: how many
tries before the user got it.

Why CASCADE on both FKs
-----------------------
DATABASE_DESIGN §4.2: deleting a user erases their progress
(GDPR right-to-erasure); deleting a problem purges orphaned
progress rows.

Indexes (per DATABASE_DESIGN §5)
--------------------------------
- pk_user_problem_progress : composite PK on
  (user_id, problem_id). Postgres uses the leftmost prefix
  for user-scoped queries (dashboard, per-user progress
  list) — no separate user_id index is needed.
- ix_user_problem_progress_user_id is documented in §5 but
  duplicates the PK leftmost prefix for user-scoped reads.
  We still emit it explicitly to keep the index surface
  area consistent with the schema catalog and to give the
  planner a named choice.

Refs: DATABASE_DESIGN.md §1 (ERD: user_problem_progress),
       §4 (constraints), §5 (indexes), §6 (0015)
Refs: ALGOVISION_BACKEND_PLAN.md §5 (Phase 5 — B5.2)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7c8d9e0f1a2b"
down_revision: str | Sequence[str] | None = "6b7c8d9e0f1a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_problem_progress",
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "problem_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column(
            "attempts",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column(
            "first_viewed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "last_viewed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "user_id",
            "problem_id",
            name="pk_user_problem_progress",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_user_problem_progress_user_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["problem_id"],
            ["problems.id"],
            name="fk_user_problem_progress_problem_id",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "status IN ('not_started', 'in_progress', 'completed')",
            name="ck_user_problem_progress_status",
        ),
    )
    op.create_index(
        "ix_user_problem_progress_user_id",
        "user_problem_progress",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_user_problem_progress_user_id",
        table_name="user_problem_progress",
    )
    op.drop_table("user_problem_progress")
