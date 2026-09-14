"""create_algorithm_categories

Adds the ``algorithm_categories`` table per DATABASE_DESIGN.md §1, §4.

Schema
------
- id          : UUID PK, gen_random_uuid() (from pgcrypto, 0001).
- slug        : UNIQUE. URL-safe category key.
- name        : Display name.
- description : Optional long-form description (TEXT, nullable).
- sort_order  : INT NOT NULL DEFAULT 0. Drives sidebar order.
- created_at  : TIMESTAMPTZ NOT NULL DEFAULT now().

Ordering decision
-----------------
We deliberately store ``sort_order`` here (not a separate
``category_order`` table) because the set of categories is small
(<50 per §2) and admin re-ordering is rare. A join table would be
premature complexity.

Refs: DATABASE_DESIGN.md §1 (ERD: algorithm_categories), §4
       (constraints), §5 (indexes), §6 (0004)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "7e8f9a0b1c2d"
down_revision: str | Sequence[str] | None = "6d7e8f9a0b1c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "algorithm_categories",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "sort_order",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_algorithm_categories"),
        sa.UniqueConstraint("slug", name="uq_algorithm_categories_slug"),
    )
    op.create_index(
        "ix_algorithm_categories_slug",
        "algorithm_categories",
        ["slug"],
        unique=True,
    )
    # Sort-order index — the browse page lists categories by
    # sort_order ASC. Cheap to maintain, supports a single-column
    # ORDER BY without a sort step.
    op.create_index(
        "ix_algorithm_categories_sort_order",
        "algorithm_categories",
        ["sort_order"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_algorithm_categories_sort_order", table_name="algorithm_categories"
    )
    op.drop_index("ix_algorithm_categories_slug", table_name="algorithm_categories")
    op.drop_table("algorithm_categories")
