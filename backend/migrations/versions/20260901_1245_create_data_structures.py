"""create_data_structures

Adds the ``data_structures`` table per DATABASE_DESIGN.md §1, §4.

Schema
------
- id                 : UUID PK, gen_random_uuid() (0001).
- slug               : UNIQUE. URL key.
- name               : Display name.
- description        : Optional long description (TEXT).
- difficulty         : VARCHAR(16) NOT NULL, CHECK
                       ('easy' | 'medium' | 'hard').
- visualization_type : VARCHAR(64) NOT NULL. Frontend discriminator.
- created_at         : TIMESTAMPTZ NOT NULL DEFAULT now() .

Why no FK parent
----------------
Data structures are a sibling catalog to algorithms — they have no
hierarchical parent (unlike algorithms which live under
algorithm_categories). Keeping the table flat supports the
"browse all data structures" UX without a forced categorization
that the frontend doesn't need yet.

No ``updated_at``
-----------------
Data structures are static catalog content (seeded once,
occasionally updated by admin tools). We don't need row-level
write tracking the way algorithms do, where the latest edit
matters for ETag support.

Indexes (per DATABASE_DESIGN §5)
--------------------------------
- ix_data_structures_slug (UNIQUE) : get_by_slug.
- ix_data_structures_difficulty    : filter by difficulty.

Note: data_structures is much smaller than algorithms (<50 rows
per §2), so we don't add as many indexes. Filtering by difficulty
is the only common filter for this table.

Refs: DATABASE_DESIGN.md §1 (ERD: data_structures), §4
       (constraints), §5 (indexes), §6 (0008)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "9a0b1c2d3e4f"
down_revision: str | Sequence[str] | None = "8f9a0b1c2d3e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "data_structures",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("slug", sa.String(length=96), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("difficulty", sa.String(length=16), nullable=False),
        sa.Column("visualization_type", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_data_structures"),
        sa.UniqueConstraint("slug", name="uq_data_structures_slug"),
        sa.CheckConstraint(
            "difficulty IN ('easy', 'medium', 'hard')",
            name="ck_data_structures_difficulty",
        ),
    )
    op.create_index(
        "ix_data_structures_slug",
        "data_structures",
        ["slug"],
        unique=True,
    )
    op.create_index(
        "ix_data_structures_difficulty",
        "data_structures",
        ["difficulty"],
    )


def downgrade() -> None:
    op.drop_index("ix_data_structures_difficulty", table_name="data_structures")
    op.drop_index("ix_data_structures_slug", table_name="data_structures")
    op.drop_table("data_structures")
