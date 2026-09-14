"""create_problems

Adds the ``problems`` table per DATABASE_DESIGN.md §1, §4, §5.

Schema
------
- id                    : UUID PK, gen_random_uuid() (0001).
- slug                  : UNIQUE. URL key (B4.4 router uses it
                          as the detail endpoint key).
- title                 : Display name (NOT NULL).
- description           : Optional long description (TEXT).
- difficulty            : VARCHAR(16) NOT NULL, CHECK
                          ('easy' | 'medium' | 'hard').
- solution_explanation  : Optional long-form editorial (TEXT).
- external_reference    : Optional free-text tag / URL pointing
                          at the canonical source (LeetCode /
                          HackerRank / book chapter). Not
                          validated as a URL — see model
                          docstring.
- visualization_available : BOOL NOT NULL DEFAULT FALSE.
                          When true, the frontend routes the
                          problem to the visualization flow;
                          otherwise the editor flow.
- created_at            : TIMESTAMPTZ NOT NULL DEFAULT now().
- updated_at            : TIMESTAMPTZ NOT NULL DEFAULT now().

No FKs in this migration
------------------------
DATABASE_DESIGN §1: problems participate in two M:N joins
(``problem_topics``, ``problem_companies``) that ship in
B4.3. We don't introduce those FKs here because the join
tables don't exist yet — adding orphan-pointing FKs would
fail ``alembic upgrade``.

Indexes (per DATABASE_DESIGN §5)
--------------------------------
- ix_problems_slug         : UNIQUE — get_by_slug, ETag, slug
                             rewrite. The UNIQUE constraint is
                             also expressed at table level for
                             defense in depth.
- ix_problems_difficulty   : filter by difficulty on the list
                             endpoint.

CHECK on difficulty
-------------------
Mirrors ``algorithms.difficulty`` (§4.3) — the closed
vocabulary is enforced by Postgres, not the Python ``str``
column. ``DIFFICULTY_VALUES`` in the model module is the
Python-side mirror consumed by seeds + tests.

Why no ``is_published``
-----------------------
The catalog uses ``is_published`` to hide drafts from the
public read endpoint. Problems follow the same convention in
v2, but in v1 the problems API is staff-only (no public read
endpoint per ALGOVISION_BACKEND_PLAN §4). Adding the column
without a public surface to gate would be premature; we ship
the column when the public read endpoint lands.

Refs: DATABASE_DESIGN.md §1 (ERD: problems), §4 (constraints),
       §5 (indexes), §6 (0010)
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 4 — Problems, B4.1)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2d3e4f5a6b7c"
down_revision: str | Sequence[str] | None = "1c2d3e4f5a6b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "problems",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("slug", sa.String(length=96), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("difficulty", sa.String(length=16), nullable=False),
        sa.Column("solution_explanation", sa.Text(), nullable=True),
        sa.Column("external_reference", sa.Text(), nullable=True),
        sa.Column(
            "visualization_available",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
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
        sa.PrimaryKeyConstraint("id", name="pk_problems"),
        sa.UniqueConstraint("slug", name="uq_problems_slug"),
        sa.CheckConstraint(
            "difficulty IN ('easy', 'medium', 'hard')",
            name="ck_problems_difficulty",
        ),
    )
    op.create_index(
        "ix_problems_slug",
        "problems",
        ["slug"],
        unique=True,
    )
    op.create_index(
        "ix_problems_difficulty",
        "problems",
        ["difficulty"],
    )


def downgrade() -> None:
    op.drop_index("ix_problems_difficulty", table_name="problems")
    op.drop_index("ix_problems_slug", table_name="problems")
    op.drop_table("problems")
