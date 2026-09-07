"""create_companies

Adds the ``companies`` table per DATABASE_DESIGN.md §1, §4.

Schema
------
- id    : UUID PK, gen_random_uuid() (0001).
- slug  : UNIQUE. URL key.
- name  : Display name (NOT NULL).

Why a dedicated table (not an enum on problems)
-----------------------------------------------
"Asked by Google, Meta, Amazon" is naturally a tagged list —
the frontend renders a row of company pills on a problem
detail page. The M:N semantics (``problem_companies``, B4.3)
require the entity to be its own table so problems and
companies can move independently.

Why no indexes beyond the implicit PK + UNIQUE slug
--------------------------------------------------
``ix_problem_companies_company_id`` (§5) is created in the
``problem_companies`` migration (B4.3) — that index already
covers "problems per company" reads, the only meaningful
filter on the company table at this point.

Why no ``logo_url`` / ``website`` columns
-----------------------------------------
Out of v1 scope. Visual assets land when the frontend asks
for them; adding columns without a consumer is premature.

Refs: DATABASE_DESIGN.md §1 (ERD: companies), §4
       (constraints), §6 (0010)
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 4 — Problems, B4.2)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3e4f5a6b7c8d"
down_revision: str | Sequence[str] | None = "2d3e4f5a6b7c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("slug", sa.String(length=96), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_companies"),
        sa.UniqueConstraint("slug", name="uq_companies_slug"),
    )


def downgrade() -> None:
    op.drop_table("companies")
