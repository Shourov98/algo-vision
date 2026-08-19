"""Unit tests for migrations/versions/*.

These tests validate the SQL emitted by our migrations without
requiring a real database. The actual upgrade/downgrade runs in CI
against an ephemeral Postgres (B1.10).

Refs: DATABASE_DESIGN.md §6 (Migration Plan)
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 1.7)
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest


BACKEND_ROOT = Path(__file__).resolve().parents[2]
VERSIONS_DIR = BACKEND_ROOT / "migrations" / "versions"


def _alembic(*args: str, env: dict[str, str] | None = None) -> tuple[int, str]:
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    proc = subprocess.run(
        ["alembic", *args],
        cwd=str(BACKEND_ROOT),
        capture_output=True,
        text=True,
        env=full_env,
        timeout=20,
    )
    return proc.returncode, proc.stdout + proc.stderr


# ---------------------------------------------------------------------------
# Migration files exist
# ---------------------------------------------------------------------------


def test_init_extensions_migration_exists() -> None:
    files = list(VERSIONS_DIR.glob("*_init_extensions.py"))
    assert files, "init_extensions migration is missing"


def test_create_users_migration_exists() -> None:
    files = list(VERSIONS_DIR.glob("*_create_users.py"))
    assert files, "create_users migration is missing"


def test_users_migration_depends_on_extensions() -> None:
    """Per DATABASE_DESIGN §6, 0002 depends on 0001."""
    users_files = list(VERSIONS_DIR.glob("*_create_users.py"))
    extensions_files = list(VERSIONS_DIR.glob("*_init_extensions.py"))
    assert users_files and extensions_files

    users_text = users_files[0].read_text()
    # Extract the extensions revision id.
    ext_text = extensions_files[0].read_text()
    ext_rev_match = re.search(r'^revision:\s*str\s*=\s*["\']([^"\']+)["\']', ext_text, re.MULTILINE)
    assert ext_rev_match
    ext_rev = ext_rev_match.group(1)

    # The users migration's down_revision must reference the extensions one.
    down_rev_match = re.search(
        r'^down_revision:\s*[^=]+=\s*["\']([^"\']+)["\']',
        users_text,
        re.MULTILINE,
    )
    assert down_rev_match
    assert down_rev_match.group(1) == ext_rev


# ---------------------------------------------------------------------------
# init_extensions upgrade SQL
# ---------------------------------------------------------------------------


def test_init_extensions_emits_pgcrypto_and_citext() -> None:
    """`alembic upgrade head --sql` must include both extensions."""
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    code, output = _alembic("upgrade", "head", "--sql", env=env)
    assert code == 0, output
    assert 'CREATE EXTENSION IF NOT EXISTS "pgcrypto"' in output
    assert 'CREATE EXTENSION IF NOT EXISTS "citext"' in output


def test_init_extensions_downgrade_is_no_op() -> None:
    """Downgrade must NOT drop extensions (cluster-wide, unsafe)."""
    ext_files = list(VERSIONS_DIR.glob("*_init_extensions.py"))
    text = ext_files[0].read_text()

    # The downgrade function body must be a no-op (just 'pass').
    # We check that there's no op.execute("DROP EXTENSION") inside.
    downgrade_match = re.search(
        r"def downgrade\(\).*?(?=^def |\Z)", text, re.MULTILINE | re.DOTALL
    )
    assert downgrade_match
    assert "DROP EXTENSION" not in downgrade_match.group(0)


# ---------------------------------------------------------------------------
# create_users upgrade SQL
# ---------------------------------------------------------------------------


def test_create_users_emits_correct_schema() -> None:
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    code, output = _alembic("upgrade", "head", "--sql", env=env)
    assert code == 0, output

    # The CREATE TABLE users statement must contain every documented column.
    users_ddl_match = re.search(
        r"CREATE TABLE users \((.*?)\);", output, re.DOTALL
    )
    assert users_ddl_match, output
    ddl = users_ddl_match.group(0)
    for col in ("id", "email", "password_hash", "display_name", "is_active",
                "created_at", "updated_at"):
        assert col in ddl, f"missing column {col} in users DDL"


def test_create_users_email_is_citext() -> None:
    """DATABASE_DESIGN §3 specifies email as CITEXT for case-insensitive unique."""
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    assert "email CITEXT" in output


def test_create_users_id_default_is_gen_random_uuid() -> None:
    """UUIDs come from pgcrypto.gen_random_uuid(), not uuid-ossp."""
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    assert "DEFAULT gen_random_uuid()" in output


def test_create_users_has_unique_email_constraint() -> None:
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    # citext makes the unique constraint case-insensitive by default.
    assert "CONSTRAINT uq_users_email UNIQUE (email)" in output


def test_create_users_has_email_lower_unique_index() -> None:
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    assert "CREATE UNIQUE INDEX ix_users_email_lower" in output
    assert "LOWER(email)" in output


def test_create_users_password_hash_is_text_not_varchar() -> None:
    """Argon2id hashes exceed any reasonable VARCHAR limit; use TEXT."""
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    assert "password_hash TEXT" in output


def test_create_users_timestamps_have_timezone() -> None:
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    assert "created_at TIMESTAMP WITH TIME ZONE" in output
    assert "updated_at TIMESTAMP WITH TIME ZONE" in output


# ---------------------------------------------------------------------------
# Downgrade SQL symmetry
# ---------------------------------------------------------------------------


def test_downgrade_emits_drop_table_users() -> None:
    """``alembic downgrade <head>:base --sql`` must drop the users table."""
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    # Use the explicit form: downgrade from head to base.
    _, output = _alembic(
        "downgrade", "head:base", "--sql", env=env
    )
    assert "DROP TABLE" in output
    assert re.search(r"DROP TABLE\s+users", output)


# ---------------------------------------------------------------------------
# Migration ordering / history
# ---------------------------------------------------------------------------


def test_alembic_history_lists_both_migrations() -> None:
    """`alembic history` must include both 0001 and 0002."""
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("history", env=env)
    assert "init_extensions" in output
    assert "create_users" in output


def test_alembic_heads_returns_users_migration() -> None:
    """The chain's head must be the users migration."""
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("heads", env=env)
    # We can't predict the exact revision id, but it must be there.
    assert "create_users" in output or "1107a23d5a7d" in output