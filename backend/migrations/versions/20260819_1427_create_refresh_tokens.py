"""create refresh_tokens

Adds the refresh-token store so AuthService can support single-use
rotation and explicit revocation (logout, password change,
suspicious activity).

Schema highlights
-----------------
- id            : UUID PK, defaulted by gen_random_uuid() (pgcrypto).
- user_id       : UUID NOT NULL, FK -> users(id) ON DELETE CASCADE.
                  Deleting a user removes their refresh tokens.
- token_hash    : TEXT NOT NULL UNIQUE. SHA-256 hex of the opaque
                  refresh-token string (see src/core/tokens.py).
                  UNIQUE so duplicate presentation of the same
                  token is rejected at the DB layer.
- expires_at    : TIMESTAMPTZ NOT NULL. Used by the service to
                  reject expired tokens before they would even
                  match a row (defense in depth — also enforce in
                  code).
- used_at       : TIMESTAMPTZ NULL. Single-use rotation: when the
                  token is exchanged for a new pair, we mark
                  ``used_at = now()``. The service rejects
                  refresh on a token that already has a non-null
                  used_at.
- revoked_at    : TIMESTAMPTZ NULL. Explicit revocation path
                  (logout, account compromise). The service
                  rejects refresh on a token whose revoked_at
                  is set.
- created_at    : TIMESTAMPTZ NOT NULL DEFAULT now().

Indexes
-------
- ix_refresh_tokens_user_id        : service filters by user_id on
                                     logout-all-sessions.
- The UNIQUE on token_hash provides the lookup path during the
  refresh hot path (one indexed equality check).

Rotation semantics (enforced in service layer, B2.5)
----------------------------------------------------
On successful refresh, the service:
1. Reads the row by token_hash, in a transaction with FOR UPDATE.
2. Validates not expired, not used, not revoked.
3. Issues a NEW pair, inserts a new row.
4. Marks the OLD row's used_at = now().
5. Commits.

This is single-use rotation: re-presenting an already-used token
within the same window will fail at step 2 and the service can
then revoke the user's entire token family (theirs and any
descendants). That logic lives in B2.5 / B2.9.

Refs: ALGOVISION_BACKEND_PLAN.md §8 (Refresh token rotation)
Refs: AlgoVision_BACKEND.md §29 (Authentication)
Refs: DATABASE_DESIGN.md §21 (Recently viewed — pattern analog)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3b4e5f6a7c8d"
down_revision: str | Sequence[str] | None = "1107a23d5a7d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "refresh_tokens",
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
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "used_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_refresh_tokens"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_refresh_tokens_user_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
    )
    op.create_index(
        "ix_refresh_tokens_user_id",
        "refresh_tokens",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
