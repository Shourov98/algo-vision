"""create_problem_companies

Adds the ``problem_companies`` M:N table per DATABASE_DESIGN.md
§1, §4, §5.

Schema
------
- problem_id : UUID NOT NULL, FK → problems.id
                ON DELETE CASCADE, part of composite PK.
- company_id : UUID NOT NULL, FK → companies.id
                ON DELETE CASCADE, part of composite PK.

No payload columns. The PK is (problem_id, company_id) per
§4.2 — composite PK enforcement is the only constraint we
need beyond the FKs; there's no UNIQUE separately because
the PK already guarantees uniqueness.

Indexes (per DATABASE_DESIGN §5)
--------------------------------
- ix_problem_companies_company_id — "problems per company"
  reverse lookup. Per §5, this index is high-priority:
  the company-detail page (B4.4 router) reads "every
  problem asked by Google" and would otherwise sequential-
  scan the join.

Why CASCADE on both FKs
-----------------------
DATABASE_DESIGN §4.2: junction tables follow the parent. When
either a problem or a company is deleted, the corresponding
join rows must go with it. RESTRICT would force explicit
teardown that no caller wants.

Why no ``ix_problem_companies_problem_id``
-----------------------------------------
The composite PK already covers problem_id-first lookups
(problem detail → "what companies ask this problem?").
Postgres uses the leftmost-prefix of the PK for that read;
a separate index would be duplicate work.

Refs: DATABASE_DESIGN.md §1 (ERD: problem_companies), §4
       (constraints), §5 (indexes), §6 (0013)
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 4 — Problems, B4.3)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5a6b7c8d9e0f"
down_revision: str | Sequence[str] | None = "4f5a6b7c8d9e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "problem_companies",
        sa.Column(
            "problem_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "company_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "problem_id",
            "company_id",
            name="pk_problem_companies",
        ),
        sa.ForeignKeyConstraint(
            ["problem_id"],
            ["problems.id"],
            name="fk_problem_companies_problem_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_problem_companies_company_id",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_problem_companies_company_id",
        "problem_companies",
        ["company_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_problem_companies_company_id", table_name="problem_companies"
    )
    op.drop_table("problem_companies")
