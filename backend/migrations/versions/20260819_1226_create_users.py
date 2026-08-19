"""create_users

Creates the ``users`` table and its indexes per DATABASE_DESIGN §3.

Schema highlights
-----------------
- id            : UUID PK, defaulted by gen_random_uuid() (from pgcrypto).
- email         : CITEXT (citext extension from migration 0001). UNIQUE
                  via the citext type — a unique constraint on a citext
                  column is case-insensitive automatically. Application
                  still lowercases email before insert (defense in depth).
- password_hash : TEXT. Argon2id hash from src/core/security.py.
- display_name  : TEXT NOT NULL.
- is_active     : BOOL NOT NULL DEFAULT TRUE.
- created_at    : TIMESTAMPTZ NOT NULL DEFAULT now().
- updated_at    : TIMESTAMPTZ NOT NULL DEFAULT now().

Indexes
-------
- ix_users_email_lower (UNIQUE, LOWER(email)) — listed in the index
  plan as the primary login lookup. Redundant with the citext unique
  constraint but kept for explicit query-plan control and so the
  index name matches the documented plan.

Refs: DATABASE_DESIGN.md §3 (users table), §5 (index plan), §6 (0002)
Refs: AlgoVision_BACKEND.md §3.4 (passwords never stored plaintext)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "1107a23d5a7d"
down_revision: str | Sequence[str] | None = "884179f9a223"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "email",
            sa.dialects.postgresql.CITEXT(),
            nullable=False,
        ),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("TRUE"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index(
        "ix_users_email_lower",
        "users",
        [sa.text("LOWER(email)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_users_email_lower", table_name="users")
    op.drop_table("users")