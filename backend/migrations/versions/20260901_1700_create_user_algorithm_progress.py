"""create_user_algorithm_progress

Adds the ``user_algorithm_progress`` table per DATABASE_DESIGN.md
§1, §4, §5.

Schema
------
- user_id                : UUID NOT NULL, FK → users.id
                           ON DELETE CASCADE, part of composite PK.
- algorithm_id           : UUID NOT NULL, FK → algorithms.id
                           ON DELETE CASCADE, part of composite PK.
- status                 : VARCHAR(16) NOT NULL, CHECK
                           ('not_started' | 'in_progress'
                            | 'completed').
- completion_percentage  : SMALLINT NOT NULL DEFAULT 0,
                           CHECK (BETWEEN 0 AND 100).
- first_viewed_at        : TIMESTAMPTZ NOT NULL DEFAULT now().
                           Preserved across upserts.
- last_viewed_at         : TIMESTAMPTZ NOT NULL DEFAULT now().
                           Bumped on every interaction.
- completed_at           : TIMESTAMPTZ NULL. Set when status
                           transitions to 'completed'.
- total_sessions         : INT NOT NULL DEFAULT 1.

No payload surrogate
--------------------
DATABASE_DESIGN §1 has no surrogate id — every business query
is "for this user, what is the progress on this algorithm".
The composite PK is the natural key.

Why CASCADE on both FKs
-----------------------
DATABASE_DESIGN §4.2: deleting a user erases their progress
(GDPR right-to-erasure); deleting an algorithm purges orphaned
progress rows. Mirrors ``problem_companies`` (B4.3) and
``problem_topics`` (B4.3).

Indexes (per DATABASE_DESIGN §5)
--------------------------------
- pk_user_algorithm_progress  : composite PK on
  (user_id, algorithm_id).
  Postgres uses the leftmost prefix for user-scoped queries
  (dashboard, per-user progress list).
- ix_user_algorithm_progress_algo_id  : secondary index on
  algorithm_id alone — covers the rare "everyone progressing
  on algorithm X" admin query. The composite PK doesn't
  cover this direction.

CHECK on status and percentage
-------------------------------
DATABASE_DESIGN §4.3 mandates DB-level enforcement for
closed vocabularies and numeric ranges. The model file
declares them in ``__table_args__`` for introspection;
this migration is the authoritative DDL.

Refs: DATABASE_DESIGN.md §1 (ERD: user_algorithm_progress),
       §4 (constraints), §5 (indexes), §6 (0014)
Refs: ALGOVISION_BACKEND_PLAN.md §5 (Phase 5 — B5.1)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6b7c8d9e0f1a"
down_revision: str | Sequence[str] | None = "5a6b7c8d9e0f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_algorithm_progress",
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "algorithm_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column(
            "completion_percentage",
            sa.SmallInteger(),
            nullable=False,
            server_default=sa.text("0"),
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
        sa.Column(
            "total_sessions",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.PrimaryKeyConstraint(
            "user_id",
            "algorithm_id",
            name="pk_user_algorithm_progress",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_user_algorithm_progress_user_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["algorithm_id"],
            ["algorithms.id"],
            name="fk_user_algorithm_progress_algorithm_id",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "status IN ('not_started', 'in_progress', 'completed')",
            name="ck_user_algorithm_progress_status",
        ),
        sa.CheckConstraint(
            "completion_percentage BETWEEN 0 AND 100",
            name="ck_user_algorithm_progress_pct",
        ),
    )
    op.create_index(
        "ix_user_algorithm_progress_algo_id",
        "user_algorithm_progress",
        ["algorithm_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_user_algorithm_progress_algo_id",
        table_name="user_algorithm_progress",
    )
    op.drop_table("user_algorithm_progress")
