"""create_topics

Adds the ``topics`` table per DATABASE_DESIGN.md §1, §4.

Topics are reusable tags shared between algorithms (B3.4's
``algorithm_topics`` M:N) and problems (Phase 4's
``problem_topics``). Keeping topics as a standalone table — rather
than a column on algorithms or a free-text field — avoids the
vocabulary-drift problem where the same concept ("dynamic
programming") ends up tagged multiple ways.

Schema
------
- id     : UUID PK, gen_random_uuid() from pgcrypto (0001).
- slug   : UNIQUE. URL-safe identifier.
- name   : Display name.

Notes
-----
- No ``description``: topics are short labels; longer context
  lives on the algorithm/problem itself.
- No ``created_at``: topics are static catalog content. Seeded
  once; no creation API in v1.

Refs: DATABASE_DESIGN.md §1 (ERD: topics), §4 (constraints),
       §5 (indexes), §6 (0003)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "6d7e8f9a0b1c"
down_revision: str | Sequence[str] | None = "5c6d7e8f9a0b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "topics",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_topics"),
        sa.UniqueConstraint("slug", name="uq_topics_slug"),
    )
    # The UniqueConstraint already creates a btree on slug, which
    # is the access path for "filter by topic slug" (Q in
    # DATABASE_DESIGN §5). Naming it explicitly so the index name
    # matches the documented plan and so future migrations can
    # reference it by name.
    op.create_index(
        "ix_topics_slug",
        "topics",
        ["slug"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_topics_slug", table_name="topics")
    op.drop_table("topics")
