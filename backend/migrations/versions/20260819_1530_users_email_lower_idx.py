"""users email_lower index (idempotent)

Ensures ``ix_users_email_lower`` exists on the ``users`` table.
This unique index is the primary login lookup path per
DATABASE_DESIGN.md §4.4 — it normalizes email to lowercase so
``Alice@Example.com`` and ``alice@example.com`` collide at
the index level.

The initial ``create_users`` migration (B2.1) already creates
this index. This follow-up is a no-op on fresh databases and a
backstop for any database that exists but predates that change.

Idempotency strategy
--------------------
PostgreSQL has no ``CREATE INDEX IF NOT EXISTS`` until PG 9.5+
(it does exist). We use the standard form and wrap it in a
``DO $$ ... EXCEPTION`` block so re-running the migration
silently skips the creation. Same approach for the downgrade
(``DROP INDEX IF EXISTS`` is natively supported).

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 2 - B2.10)
Refs: DATABASE_DESIGN.md §4.4 (Email uniqueness)
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5c6d7e8f9a0b"
down_revision: str | Sequence[str] | None = "3b4e5f6a7c8d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Idempotent: create the index only if it doesn't already exist.
    # ``CREATE INDEX IF NOT EXISTS`` (PG 9.5+) skips silently when
    # the named index is already present, which is what we want for
    # databases that already have it from the initial users
    # migration.
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email_lower "
        "ON users (LOWER(email))"
    )


def downgrade() -> None:
    # ``DROP INDEX IF EXISTS`` is natively idempotent.
    op.execute("DROP INDEX IF EXISTS ix_users_email_lower")
