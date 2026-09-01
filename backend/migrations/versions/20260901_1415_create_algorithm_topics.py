"""create_algorithm_topics

Adds the ``algorithm_topics`` M:N table per DATABASE_DESIGN.md §1, §4.

Schema
------
- algorithm_id : UUID NOT NULL, FK → algorithms.id
                  ON DELETE CASCADE, part of composite PK.
- topic_id     : UUID NOT NULL, FK → topics.id
                  ON DELETE CASCADE, part of composite PK.

No payload columns. The PK is (algorithm_id, topic_id) per
§4.2 — composite PK enforcement is the only constraint we need
beyond the FKs; there's no UNIQUE separately because the PK
already guarantees uniqueness.

Indexes (per DATABASE_DESIGN §5)
--------------------------------
- ix_algorithm_topics_topic_id — reverse lookup: "which
  algorithms tag this topic". Without it, every topic-detail
  page does a sequential scan of the join.

Why CASCADE on both FKs
-----------------------
DATABASE_DESIGN §4.2: junction tables follow the parent. When
either an algorithm or a topic is deleted, the corresponding
join rows must go with it. RESTRICT would force explicit
teardown that no caller wants.

Refs: DATABASE_DESIGN.md §1 (ERD: algorithm_topics), §4
       (constraints), §5 (indexes), §6 (0007)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "1c2d3e4f5a6b"
down_revision: str | Sequence[str] | None = "0b1c2d3e4f5a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "algorithm_topics",
        sa.Column(
            "algorithm_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "topic_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "algorithm_id",
            "topic_id",
            name="pk_algorithm_topics",
        ),
        sa.ForeignKeyConstraint(
            ["algorithm_id"],
            ["algorithms.id"],
            name="fk_algorithm_topics_algorithm_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["topics.id"],
            name="fk_algorithm_topics_topic_id",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_algorithm_topics_topic_id",
        "algorithm_topics",
        ["topic_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_algorithm_topics_topic_id", table_name="algorithm_topics")
    op.drop_table("algorithm_topics")