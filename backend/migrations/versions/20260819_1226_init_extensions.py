"""init_extensions

Installs PostgreSQL extensions required by the rest of the schema:

- pgcrypto : gen_random_uuid() — used for all UUID primary keys.
- citext   : case-insensitive TEXT — used by users.email so a unique
             constraint on email is case-insensitive by default.

Refs: DATABASE_DESIGN.md §6 (Migration Plan — 0001_init_extensions)
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "884179f9a223"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Both extensions are required by later migrations; install them
    # unconditionally. IF NOT EXISTS makes the migration idempotent on
    # databases that already have them (e.g. managed Postgres from
    # Supabase ships pgcrypto by default).
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "citext"')


def downgrade() -> None:
    # Extensions are cluster-wide; dropping them here would affect
    # every database on the cluster. We deliberately do not drop them
    # on downgrade — once a database depends on citext or pgcrypto,
    # removing the extension is unsafe.
    pass