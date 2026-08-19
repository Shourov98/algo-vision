"""Alembic environment script.

Runs Alembic migrations against the configured database. Two modes:

- **online** (default): opens a real DBAPI connection using the sync
  ``DATABASE_URL_SYNC`` (psycopg2). Used for both local dev and CI.
- **offline**: emits SQL to stdout/file without connecting. Useful
  for review and for SQL-only deployment pipelines.

Why psycopg2 (sync) here
------------------------
Alembic's core is sync. The application uses asyncpg via the
SQLAlchemy async engine, but migrations are short-lived CLI
processes that benefit from sync drivers. DATABASE_URL_SYNC is the
psycopg2 URL specifically for this purpose.

Why metadata is empty here
--------------------------
SQLAlchemy 2.x ``target_metadata`` should be the project's combined
``MetaData`` so autogenerate detects drift. We don't yet have models
because phase 1 is foundation; the first model import (User in B2.1)
will populate ``src.core.models.metadata`` and env.py will import it
here. Until then, autogenerate is a no-op (no tables to compare).
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Alembic Config object provides access to alembic.ini values.
config = context.config

# Configure stdlib logging from alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Target metadata
# ---------------------------------------------------------------------------
# Importing src.core.db pulls in the DeclarativeBase and every module
# that registers models on it (currently src.modules.users). This
# gives Alembic a complete picture for autogenerate, while keeping
# env.py unaware of specific models.
#
# NOTE: src.core.db also opens a SQLAlchemy engine at import time if
# anything triggers init_engine(); we import the module only for the
# Base, not the engine, so no connection is opened here.
from src.core.db import Base as _SQLAlchemyBase  # noqa: E402

target_metadata = _SQLAlchemyBase.metadata


def _resolve_database_url() -> str:
    """Pull the sync DB URL from env, with a clear error if missing."""
    url = os.environ.get("DATABASE_URL_SYNC") or config.get_main_option(
        "sqlalchemy.url"
    )
    if not url:
        raise RuntimeError(
            "DATABASE_URL_SYNC is not set. Copy backend/.env.example to "
            "backend/.env and fill in your Supabase connection details, "
            "or set DATABASE_URL_SYNC in your shell before running "
            "alembic."
        )
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without connecting)."""
    context.configure(
        url=_resolve_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # detect column type changes
        compare_server_default=True,  # detect default changes
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database connection."""
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _resolve_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # no pool — short-lived CLI process
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
