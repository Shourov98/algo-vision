"""create_user_recent_items

Adds the ``user_recent_items`` table per DATABASE_DESIGN.md
§1, §4, §5.

Schema
------
- id          : UUID PK, gen_random_uuid() default.
- user_id     : UUID NOT NULL, FK → users.id ON DELETE CASCADE.
- item_type   : VARCHAR(32) NOT NULL, CHECK
                ('algorithm' | 'data_structure' | 'problem').
- item_id     : UUID NOT NULL. No FK — polymorphic reference
                (see model docstring for rationale).
- viewed_at   : TIMESTAMPTZ NOT NULL DEFAULT now().

Why no FK on item_id
--------------------
``item_id`` is polymorphic: depending on ``item_type`` it
points at one of three different tables. Postgres cannot
declare a single-column FK against three tables; the
``item_type`` CHECK + application invariant is the only
option. This is a deliberate trade-off — see
``models/user_recent_items.py``.

Indexes (per DATABASE_DESIGN §5)
--------------------------------
- pk_user_recent_items              : surrogate PK.
- ix_user_recent_items_user_viewed  : composite (user_id,
  viewed_at DESC) — covers the dashboard's "recently
  viewed" query (last 50 per user). Composite + DESC
  because the dashboard reads the most-recent-first.

The 50-row cap is enforced in the repository (B5.5),
not as a DB trigger — DATABASE_DESIGN §4 lists no
trigger constraints for this table.

Refs: DATABASE_DESIGN.md §1 (ERD: user_recent_items),
       §4 (constraints), §5 (indexes), §6 (0016)
Refs: ALGOVISION_BACKEND_PLAN.md §5 (Phase 5 — B5.3)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8d9e0f1a2b3c"
down_revision: str | Sequence[str] | None = "7c8d9e0f1a2b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_recent_items",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("item_type", sa.String(length=32), nullable=False),
        sa.Column(
            "item_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "viewed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_user_recent_items"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_user_recent_items_user_id",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "item_type IN ('algorithm', 'data_structure', 'problem')",
            name="ck_user_recent_items_type",
        ),
    )
    op.create_index(
        "ix_user_recent_items_user_viewed",
        "user_recent_items",
        ["user_id", sa.text("viewed_at DESC")],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_user_recent_items_user_viewed",
        table_name="user_recent_items",
    )
    op.drop_table("user_recent_items")
