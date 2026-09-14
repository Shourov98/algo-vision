"""create_algorithms

Adds the ``algorithms`` table per DATABASE_DESIGN.md §1, §4.

Schema
------
- id                  : UUID PK, gen_random_uuid() (0001).
- category_id         : UUID NOT NULL, FK → algorithm_categories.id
                        ON DELETE RESTRICT.
- slug                : UNIQUE. URL key.
- name                : Display name.
- description         : Optional long description (TEXT).
- difficulty          : VARCHAR(16) NOT NULL, CHECK
                        ('easy' | 'medium' | 'hard').
- visualization_type  : VARCHAR(64) NOT NULL. Frontend discriminator.
- best_time           : VARCHAR(32) NULL. Free-text complexity.
- average_time        : VARCHAR(32) NULL.
- worst_time          : VARCHAR(32) NULL.
- space_complexity    : VARCHAR(32) NULL.
- is_published        : BOOL NOT NULL DEFAULT TRUE.
- created_at          : TIMESTAMPTZ NOT NULL DEFAULT now().
- updated_at          : TIMESTAMPTZ NOT NULL DEFAULT now().

Indexes (per DATABASE_DESIGN §5)
--------------------------------
- ix_algorithms_slug           : UNIQUE — get_by_slug, ETag.
- ix_algorithms_category_id    : filter by category.
- ix_algorithms_difficulty     : filter by difficulty.
- ix_algorithms_is_published   : partial-friendly; most queries
                                  carry ``WHERE is_published = true``.
- ix_algorithms_updated_at     : ETag, ordered listings.

Why RESTRICT on category FK
---------------------------
DATABASE_DESIGN §4.2: prevent orphaning published algorithms by
silently deleting a category. CASCADE here would let an admin
take down the catalog with one click; RESTRICT forces the
explicit "delete the algorithms first" step.

Complexity columns as strings
-----------------------------
We deliberately do not parse "O(n log n)" into a structured form.
The catalog renders these as text; structured complexity is a
future feature (DATABASE_DESIGN §10). Storing free text avoids
premature commitment to a numeric representation that would be
hard to evolve.

Refs: DATABASE_DESIGN.md §1 (ERD: algorithms), §4 (constraints),
       §5 (indexes), §6 (0005)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "8f9a0b1c2d3e"
down_revision: str | Sequence[str] | None = "7e8f9a0b1c2d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "algorithms",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "category_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("slug", sa.String(length=96), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("difficulty", sa.String(length=16), nullable=False),
        sa.Column("visualization_type", sa.String(length=64), nullable=False),
        sa.Column("best_time", sa.String(length=32), nullable=True),
        sa.Column("average_time", sa.String(length=32), nullable=True),
        sa.Column("worst_time", sa.String(length=32), nullable=True),
        sa.Column("space_complexity", sa.String(length=32), nullable=True),
        sa.Column(
            "is_published",
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
        sa.PrimaryKeyConstraint("id", name="pk_algorithms"),
        sa.UniqueConstraint("slug", name="uq_algorithms_slug"),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["algorithm_categories.id"],
            name="fk_algorithms_category_id",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "difficulty IN ('easy', 'medium', 'hard')",
            name="ck_algorithms_difficulty",
        ),
    )
    op.create_index(
        "ix_algorithms_slug",
        "algorithms",
        ["slug"],
        unique=True,
    )
    op.create_index(
        "ix_algorithms_category_id",
        "algorithms",
        ["category_id"],
    )
    op.create_index(
        "ix_algorithms_difficulty",
        "algorithms",
        ["difficulty"],
    )
    op.create_index(
        "ix_algorithms_is_published",
        "algorithms",
        ["is_published"],
    )
    op.create_index(
        "ix_algorithms_updated_at",
        "algorithms",
        ["updated_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_algorithms_updated_at", table_name="algorithms")
    op.drop_index("ix_algorithms_is_published", table_name="algorithms")
    op.drop_index("ix_algorithms_difficulty", table_name="algorithms")
    op.drop_index("ix_algorithms_category_id", table_name="algorithms")
    op.drop_index("ix_algorithms_slug", table_name="algorithms")
    op.drop_table("algorithms")
