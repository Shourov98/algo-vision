"""create_problem_topics

Adds the ``problem_topics`` M:N table per DATABASE_DESIGN.md
§1, §4, §5.

Schema
------
- problem_id : UUID NOT NULL, FK → problems.id
                ON DELETE CASCADE, part of composite PK.
- topic_id   : UUID NOT NULL, FK → topics.id
                ON DELETE CASCADE, part of composite PK.

No payload columns. The PK is (problem_id, topic_id) per
§4.2 — composite PK enforcement is the only constraint we
need beyond the FKs; there's no UNIQUE separately because
the PK already guarantees uniqueness.

Indexes (per DATABASE_DESIGN §5)
--------------------------------
- ix_problem_topics_topic_id — reverse lookup: "which
  problems tag this topic". Without it, every topic-detail
  page does a sequential scan of the join.

Why CASCADE on both FKs
-----------------------
DATABASE_DESIGN §4.2: junction tables follow the parent. When
either a problem or a topic is deleted, the corresponding
join rows must go with it. RESTRICT would force explicit
teardown that no caller wants.

Why no ``ix_problem_topics_problem_id``
---------------------------------------
The composite PK already covers ``problem_id``-first lookups
(problem detail → "what topics does this problem carry?").
Adding a second index would be duplicate work — Postgres can
use the leftmost-prefix of the PK for that read.

Refs: DATABASE_DESIGN.md §1 (ERD: problem_topics), §4
       (constraints), §5 (indexes), §6 (0012)
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 4 — Problems, B4.3)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4f5a6b7c8d9e"
down_revision: str | Sequence[str] | None = "3e4f5a6b7c8d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "problem_topics",
        sa.Column(
            "problem_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "topic_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "problem_id",
            "topic_id",
            name="pk_problem_topics",
        ),
        sa.ForeignKeyConstraint(
            ["problem_id"],
            ["problems.id"],
            name="fk_problem_topics_problem_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["topics.id"],
            name="fk_problem_topics_topic_id",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_problem_topics_topic_id",
        "problem_topics",
        ["topic_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_problem_topics_topic_id", table_name="problem_topics")
    op.drop_table("problem_topics")
