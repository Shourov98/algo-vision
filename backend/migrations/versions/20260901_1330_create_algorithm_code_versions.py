"""create_algorithm_code_versions

Adds the ``algorithm_code_versions`` table per DATABASE_DESIGN.md §1, §4.

Schema
------
- id            : UUID PK.
- algorithm_id  : UUID NOT NULL, FK → algorithms.id
                  ON DELETE CASCADE.
- language      : VARCHAR(32) NOT NULL. e.g. 'python', 'java',
                  'javascript', 'cpp', 'go'.
- source_code   : TEXT NOT NULL.
- version       : INTEGER NOT NULL. Monotonic per (algorithm,
                  language) — strictly increasing on insert.
- is_current    : BOOL NOT NULL DEFAULT FALSE. Exactly one row
                  per (algorithm_id, language) is current (enforced
                  by a partial unique index, see below).
- created_at    : TIMESTAMPTZ NOT NULL DEFAULT now().

Constraints (per DATABASE_DESIGN §4.3)
-----------------------------------------
- UNIQUE (algorithm_id, language, version) — no duplicate
  versions of the same code in the same language.

Indexes (per DATABASE_DESIGN §5)
--------------------------------
- uq_algorithm_code_versions_algo_lang_version (UNIQUE) —
  enforces the version uniqueness.
- ix_algorithm_code_versions_algo_lang — partial UNIQUE on
  (algorithm_id, language) WHERE is_current — guarantees
  exactly-one-current invariant without a join.

Why a partial UNIQUE index, not a CHECK + trigger
------------------------------------------------
A partial UNIQUE index is the simplest database-enforced
guarantee that exactly one row per (algorithm_id, language) is
``is_current = TRUE``. Triggers add complexity and runtime cost;
CHECK constraints can't reference other rows. The partial index
is the right tool for this invariant.

Why ON DELETE CASCADE
---------------------
DATABASE_DESIGN §4.2: code versions are useless without their
parent algorithm. When an algorithm is deleted (e.g. via a
future admin tool), all its code versions must go with it.
RESTRICT would force explicit teardown that no caller wants.

Refs: DATABASE_DESIGN.md §1 (ERD: algorithm_code_versions),
       §4 (constraints), §5 (indexes), §6 (0006)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0b1c2d3e4f5a"
down_revision: str | Sequence[str] | None = "9a0b1c2d3e4f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "algorithm_code_versions",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "algorithm_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("language", sa.String(length=32), nullable=False),
        sa.Column("source_code", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "is_current",
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
        sa.PrimaryKeyConstraint("id", name="pk_algorithm_code_versions"),
        sa.ForeignKeyConstraint(
            ["algorithm_id"],
            ["algorithms.id"],
            name="fk_algorithm_code_versions_algorithm_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "algorithm_id",
            "language",
            "version",
            name="uq_algorithm_code_versions_algo_lang_version",
        ),
    )
    # Partial UNIQUE index enforcing exactly-one-current per
    # (algorithm_id, language).
    op.create_index(
        "uq_algorithm_code_versions_algo_lang_current",
        "algorithm_code_versions",
        ["algorithm_id", "language"],
        unique=True,
        postgresql_where=sa.text("is_current = TRUE"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_algorithm_code_versions_algo_lang_current",
        table_name="algorithm_code_versions",
    )
    op.drop_table("algorithm_code_versions")