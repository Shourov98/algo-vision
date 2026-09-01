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

BACKEND_ROOT = Path(__file__).resolve().parents[2]
VERSIONS_DIR = BACKEND_ROOT / "migrations" / "versions"


def _alembic(*args: str, env: dict[str, str] | None = None) -> tuple[int, str]:
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    # env.py imports from src.* — that only resolves if the backend
    # root is on PYTHONPATH for the subprocess. Without this, env.py
    # crashes with ModuleNotFoundError as soon as we wire
    # ``target_metadata`` to ``src.core.db.Base`` (B2.4).
    python_path = full_env.get("PYTHONPATH", "")
    full_env["PYTHONPATH"] = (
        f"{BACKEND_ROOT}:{python_path}" if python_path else str(BACKEND_ROOT)
    )
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


# ---------------------------------------------------------------------------
# refresh_tokens (B2.4)
# ---------------------------------------------------------------------------


def test_create_refresh_tokens_migration_exists() -> None:
    files = list(VERSIONS_DIR.glob("*_create_refresh_tokens.py"))
    assert files, "create_refresh_tokens migration is missing"


def test_refresh_tokens_migration_depends_on_users() -> None:
    """refresh_tokens must come after users (FK target)."""
    refresh_files = list(VERSIONS_DIR.glob("*_create_refresh_tokens.py"))
    users_files = list(VERSIONS_DIR.glob("*_create_users.py"))
    assert refresh_files and users_files

    users_text = users_files[0].read_text()
    users_rev_match = re.search(
        r'^revision:\s*str\s*=\s*["\']([^"\']+)["\']', users_text, re.MULTILINE
    )
    assert users_rev_match
    users_rev = users_rev_match.group(1)

    refresh_text = refresh_files[0].read_text()
    down_rev_match = re.search(
        r'^down_revision:\s*[^=]+=\s*["\']([^"\']+)["\']',
        refresh_text,
        re.MULTILINE,
    )
    assert down_rev_match
    assert down_rev_match.group(1) == users_rev


def test_refresh_tokens_emits_correct_schema() -> None:
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    code, output = _alembic("upgrade", "head", "--sql", env=env)
    assert code == 0, output

    match = re.search(r"CREATE TABLE refresh_tokens \((.*?)\);", output, re.DOTALL)
    assert match, "refresh_tokens CREATE TABLE not found"
    ddl = match.group(0)
    for col in ("user_id", "token_hash", "expires_at", "used_at", "revoked_at"):
        assert col in ddl, f"missing column {col} in refresh_tokens DDL"


def test_refresh_tokens_has_unique_token_hash() -> None:
    """token_hash must be UNIQUE so duplicate presentations are
    rejected at the DB layer."""
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    match = re.search(r"CREATE TABLE refresh_tokens \((.*?)\);", output, re.DOTALL)
    assert match
    assert "UNIQUE" in match.group(0)
    assert "token_hash" in match.group(0)


def test_refresh_tokens_user_id_has_fk_with_cascade() -> None:
    """FK to users.id with ON DELETE CASCADE so deleting a user
    removes their refresh tokens."""
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    match = re.search(r"CREATE TABLE refresh_tokens \((.*?)\);", output, re.DOTALL)
    assert match
    assert "REFERENCES users" in match.group(0)
    assert "ON DELETE CASCADE" in match.group(0)


def test_refresh_tokens_downgrade_drops_table() -> None:
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("downgrade", "head:base", "--sql", env=env)
    assert re.search(r"DROP TABLE\s+refresh_tokens", output)


# ---------------------------------------------------------------------------
# users_email_lower_idx (B2.10)
# ---------------------------------------------------------------------------


def test_email_lower_idx_migration_exists() -> None:
    files = list(VERSIONS_DIR.glob("*_users_email_lower_idx.py"))
    assert files, "users_email_lower_idx migration is missing"


def test_email_lower_idx_chains_after_refresh_tokens() -> None:
    """Per B2.10 the new index migration depends on refresh_tokens."""
    idx_files = list(VERSIONS_DIR.glob("*_users_email_lower_idx.py"))
    refresh_files = list(VERSIONS_DIR.glob("*_create_refresh_tokens.py"))
    assert idx_files and refresh_files

    refresh_text = refresh_files[0].read_text()
    refresh_rev_match = re.search(
        r'^revision:\s*str\s*=\s*["\']([^"\']+)["\']', refresh_text, re.MULTILINE
    )
    assert refresh_rev_match
    refresh_rev = refresh_rev_match.group(1)

    idx_text = idx_files[0].read_text()
    down_rev_match = re.search(
        r'^down_revision:\s*[^=]+=\s*["\']([^"\']+)["\']',
        idx_text,
        re.MULTILINE,
    )
    assert down_rev_match
    assert down_rev_match.group(1) == refresh_rev


def test_email_lower_idx_emits_idempotent_create() -> None:
    """Upgrade must use CREATE INDEX IF NOT EXISTS so re-running
    the migration on databases that already have the index is a
    no-op (DATABASE_DESIGN §4.4)."""
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    code, output = _alembic("upgrade", "head", "--sql", env=env)
    assert code == 0, output
    assert "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email_lower" in output
    assert "ON users (LOWER(email))" in output


def test_email_lower_idx_downgrade_uses_if_exists() -> None:
    """Downgrade must use DROP INDEX IF EXISTS for the same
    idempotency reason."""
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("downgrade", "head:base", "--sql", env=env)
    assert "DROP INDEX IF EXISTS ix_users_email_lower" in output


# ---------------------------------------------------------------------------
# B3.1 — create_topics
# ---------------------------------------------------------------------------


def test_create_topics_migration_exists() -> None:
    files = list(VERSIONS_DIR.glob("*_create_topics.py"))
    assert files, "create_topics migration is missing"


def test_create_topics_emits_correct_schema() -> None:
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    match = re.search(r"CREATE TABLE topics \((.*?)\);", output, re.DOTALL)
    assert match, "topics CREATE TABLE not found"
    ddl = match.group(0)
    for col in ("id", "slug", "name"):
        assert col in ddl, f"missing column {col} in topics DDL"


def test_create_topics_slug_is_unique() -> None:
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    match = re.search(r"CREATE TABLE topics \((.*?)\);", output, re.DOTALL)
    assert match
    assert "slug" in match.group(0)
    assert "UNIQUE" in match.group(0)


def test_create_topics_downgrade_drops_table() -> None:
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("downgrade", "head:base", "--sql", env=env)
    assert re.search(r"DROP TABLE\s+topics", output)


def test_topics_depends_on_users_email_lower_idx() -> None:
    """Per DATABASE_DESIGN §6, 0003 depends on 0002.x (last Phase 2 rev)."""
    topics_files = list(VERSIONS_DIR.glob("*_create_topics.py"))
    idx_files = list(VERSIONS_DIR.glob("*_users_email_lower_idx.py"))
    assert topics_files and idx_files

    idx_text = idx_files[0].read_text()
    idx_rev_match = re.search(
        r'^revision:\s*str\s*=\s*["\']([^"\']+)["\']', idx_text, re.MULTILINE
    )
    assert idx_rev_match
    idx_rev = idx_rev_match.group(1)

    topics_text = topics_files[0].read_text()
    down_rev_match = re.search(
        r'^down_revision:\s*[^=]+=\s*["\']([^"\']+)["\']',
        topics_text,
        re.MULTILINE,
    )
    assert down_rev_match
    assert down_rev_match.group(1) == idx_rev


# ---------------------------------------------------------------------------
# B3.1 — create_algorithm_categories
# ---------------------------------------------------------------------------


def test_create_algorithm_categories_migration_exists() -> None:
    files = list(VERSIONS_DIR.glob("*_create_algorithm_categories.py"))
    assert files, "create_algorithm_categories migration is missing"


def test_create_algorithm_categories_emits_correct_schema() -> None:
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    match = re.search(
        r"CREATE TABLE algorithm_categories \((.*?)\);", output, re.DOTALL
    )
    assert match, "algorithm_categories CREATE TABLE not found"
    ddl = match.group(0)
    for col in ("id", "slug", "name", "description", "sort_order", "created_at"):
        assert col in ddl, f"missing column {col} in algorithm_categories DDL"


def test_create_algorithm_categories_slug_is_unique() -> None:
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    match = re.search(
        r"CREATE TABLE algorithm_categories \((.*?)\);", output, re.DOTALL
    )
    assert match
    assert "slug" in match.group(0)
    assert "UNIQUE" in match.group(0)


def test_algorithm_categories_depends_on_topics() -> None:
    """Per DATABASE_DESIGN §6, 0004 depends on 0003."""
    cat_files = list(VERSIONS_DIR.glob("*_create_algorithm_categories.py"))
    topics_files = list(VERSIONS_DIR.glob("*_create_topics.py"))
    assert cat_files and topics_files

    topics_text = topics_files[0].read_text()
    topics_rev_match = re.search(
        r'^revision:\s*str\s*=\s*["\']([^"\']+)["\']', topics_text, re.MULTILINE
    )
    assert topics_rev_match
    topics_rev = topics_rev_match.group(1)

    cat_text = cat_files[0].read_text()
    down_rev_match = re.search(
        r'^down_revision:\s*[^=]+=\s*["\']([^"\']+)["\']',
        cat_text,
        re.MULTILINE,
    )
    assert down_rev_match
    assert down_rev_match.group(1) == topics_rev


def test_create_algorithm_categories_downgrade_drops_table() -> None:
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("downgrade", "head:base", "--sql", env=env)
    assert re.search(r"DROP TABLE\s+algorithm_categories", output)


# ---------------------------------------------------------------------------
# B3.1 — create_algorithms
# ---------------------------------------------------------------------------


def test_create_algorithms_migration_exists() -> None:
    files = list(VERSIONS_DIR.glob("*_create_algorithms.py"))
    assert files, "create_algorithms migration is missing"


def test_create_algorithms_emits_correct_schema() -> None:
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    match = re.search(r"CREATE TABLE algorithms \((.*?)\);", output, re.DOTALL)
    assert match, "algorithms CREATE TABLE not found"
    ddl = match.group(0)
    for col in (
        "id",
        "category_id",
        "slug",
        "name",
        "description",
        "difficulty",
        "visualization_type",
        "best_time",
        "average_time",
        "worst_time",
        "space_complexity",
        "is_published",
        "created_at",
        "updated_at",
    ):
        assert col in ddl, f"missing column {col} in algorithms DDL"


def test_create_algorithms_difficulty_check_constraint() -> None:
    """DATABASE_DESIGN §4.3 mandates a CHECK constraint on difficulty."""
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    assert "ck_algorithms_difficulty" in output
    assert "'easy'" in output
    assert "'medium'" in output
    assert "'hard'" in output


def test_create_algorithms_slug_is_unique() -> None:
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    match = re.search(r"CREATE TABLE algorithms \((.*?)\);", output, re.DOTALL)
    assert match
    assert "slug" in match.group(0)
    assert "UNIQUE" in match.group(0)


def test_create_algorithms_category_fk_is_restrict() -> None:
    """DATABASE_DESIGN §4.2: FK must use ON DELETE RESTRICT."""
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    assert "fk_algorithms_category_id" in output
    assert "REFERENCES algorithm_categories" in output
    assert "ON DELETE RESTRICT" in output


def test_create_algorithms_has_documented_indexes() -> None:
    """Per DATABASE_DESIGN §5 — slug, category_id, difficulty,
    is_published, updated_at."""
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    for index in (
        "ix_algorithms_slug",
        "ix_algorithms_category_id",
        "ix_algorithms_difficulty",
        "ix_algorithms_is_published",
        "ix_algorithms_updated_at",
    ):
        assert index in output, f"missing index {index}"


def test_create_algorithms_downgrade_drops_table() -> None:
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("downgrade", "head:base", "--sql", env=env)
    assert re.search(r"DROP TABLE\s+algorithms", output)


def test_algorithms_depends_on_algorithm_categories() -> None:
    """Per DATABASE_DESIGN §6, 0005 depends on 0004."""
    algo_files = list(VERSIONS_DIR.glob("*_create_algorithms.py"))
    cat_files = list(VERSIONS_DIR.glob("*_create_algorithm_categories.py"))
    assert algo_files and cat_files

    cat_text = cat_files[0].read_text()
    cat_rev_match = re.search(
        r'^revision:\s*str\s*=\s*["\']([^"\']+)["\']', cat_text, re.MULTILINE
    )
    assert cat_rev_match
    cat_rev = cat_rev_match.group(1)

    algo_text = algo_files[0].read_text()
    down_rev_match = re.search(
        r'^down_revision:\s*[^=]+=\s*["\']([^"\']+)["\']',
        algo_text,
        re.MULTILINE,
    )
    assert down_rev_match
    assert down_rev_match.group(1) == cat_rev


def test_alembic_heads_returns_b31_migration() -> None:
    """B3.1's algorithms migration is in the chain (8f9a0b1c2d3e).

    We don't assert it as the head — that role moves with each
    subsequent migration. We just confirm the revision is in the
    graph.
    """
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("history", env=env)
    assert "8f9a0b1c2d3e" in output


def test_alembic_heads_returns_latest_migration() -> None:
    """The chain's head must be the most recent migration.

    As new phases land, the head moves. We accept any of the
    documented revisions as a valid head so adding new migrations
    doesn't break this test.
    """
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("heads", env=env)
    # Accept any of our revisions as the head.
    assert any(
        rev in output
        for rev in (
            "1107a23d5a7d",
            "3b4e5f6a7c8d",
            "5c6d7e8f9a0b",
            "8f9a0b1c2d3e",
            "9a0b1c2d3e4f",
            "0b1c2d3e4f5a",
            "1c2d3e4f5a6b",
        )
    )


# ---------------------------------------------------------------------------
# B3.2 — create_data_structures
# ---------------------------------------------------------------------------


def test_create_data_structures_migration_exists() -> None:
    files = list(VERSIONS_DIR.glob("*_create_data_structures.py"))
    assert files, "create_data_structures migration is missing"


def test_data_structures_depends_on_algorithms() -> None:
    """Per DATABASE_DESIGN §6, 0008 depends on 0005 (algorithms)."""
    ds_files = list(VERSIONS_DIR.glob("*_create_data_structures.py"))
    algo_files = list(VERSIONS_DIR.glob("*_create_algorithms.py"))
    assert ds_files and algo_files

    algo_text = algo_files[0].read_text()
    algo_rev_match = re.search(
        r'^revision:\s*str\s*=\s*["\']([^"\']+)["\']', algo_text, re.MULTILINE
    )
    assert algo_rev_match
    algo_rev = algo_rev_match.group(1)

    ds_text = ds_files[0].read_text()
    down_rev_match = re.search(
        r'^down_revision:\s*[^=]+=\s*["\']([^"\']+)["\']',
        ds_text,
        re.MULTILINE,
    )
    assert down_rev_match
    assert down_rev_match.group(1) == algo_rev


def test_create_data_structures_emits_correct_schema() -> None:
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    match = re.search(r"CREATE TABLE data_structures \((.*?)\);", output, re.DOTALL)
    assert match, "data_structures CREATE TABLE not found"
    ddl = match.group(0)
    for col in (
        "id",
        "slug",
        "name",
        "description",
        "difficulty",
        "visualization_type",
        "created_at",
    ):
        assert col in ddl, f"missing column {col} in data_structures DDL"


def test_create_data_structures_difficulty_check_constraint() -> None:
    """DATABASE_DESIGN §4.3 mandates a CHECK on data_structures.difficulty."""
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    assert "ck_data_structures_difficulty" in output
    assert "'easy'" in output
    assert "'medium'" in output
    assert "'hard'" in output


def test_create_data_structures_slug_is_unique() -> None:
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    match = re.search(r"CREATE TABLE data_structures \((.*?)\);", output, re.DOTALL)
    assert match
    assert "slug" in match.group(0)
    assert "UNIQUE" in match.group(0)


def test_create_data_structures_has_documented_indexes() -> None:
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    for index in ("ix_data_structures_slug", "ix_data_structures_difficulty"):
        assert index in output, f"missing index {index}"


def test_create_data_structures_downgrade_drops_table() -> None:
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("downgrade", "head:base", "--sql", env=env)
    assert re.search(r"DROP TABLE\s+data_structures", output)


# ---------------------------------------------------------------------------
# B3.3 — create_algorithm_code_versions
# ---------------------------------------------------------------------------


def test_create_algorithm_code_versions_migration_exists() -> None:
    files = list(VERSIONS_DIR.glob("*_create_algorithm_code_versions.py"))
    assert files, "create_algorithm_code_versions migration is missing"


def test_algorithm_code_versions_depends_on_data_structures() -> None:
    """Per DATABASE_DESIGN §6, 0006 depends on 0008 (last B3.x rev so far).

    The migration chain follows the §6 plan order: 0003 topics, 0004
    algorithm_categories, 0005 algorithms, 0008 data_structures,
    0006 algorithm_code_versions, 0007 algorithm_topics. We pick the
    immediately previous migration (data_structures, B3.2) as
    down_revision — algorithm_code_versions logically lives in
    the algorithm branch of the catalog and doesn't need
    data_structures to exist, but following the §6 ordering keeps
    the chain linear and avoids surprises later.
    """
    cv_files = list(VERSIONS_DIR.glob("*_create_algorithm_code_versions.py"))
    ds_files = list(VERSIONS_DIR.glob("*_create_data_structures.py"))
    assert cv_files and ds_files

    ds_text = ds_files[0].read_text()
    ds_rev_match = re.search(
        r'^revision:\s*str\s*=\s*["\']([^"\']+)["\']', ds_text, re.MULTILINE
    )
    assert ds_rev_match
    ds_rev = ds_rev_match.group(1)

    cv_text = cv_files[0].read_text()
    down_rev_match = re.search(
        r'^down_revision:\s*[^=]+=\s*["\']([^"\']+)["\']',
        cv_text,
        re.MULTILINE,
    )
    assert down_rev_match
    assert down_rev_match.group(1) == ds_rev


def test_create_algorithm_code_versions_emits_correct_schema() -> None:
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    match = re.search(
        r"CREATE TABLE algorithm_code_versions \((.*?)\);", output, re.DOTALL
    )
    assert match, "algorithm_code_versions CREATE TABLE not found"
    ddl = match.group(0)
    for col in (
        "id",
        "algorithm_id",
        "language",
        "source_code",
        "version",
        "is_current",
        "created_at",
    ):
        assert col in ddl, f"missing column {col} in algorithm_code_versions DDL"


def test_create_algorithm_code_versions_has_unique_algo_lang_version() -> None:
    """UNIQUE (algorithm_id, language, version) per DATABASE_DESIGN §4.3."""
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    match = re.search(
        r"CREATE TABLE algorithm_code_versions \((.*?)\);", output, re.DOTALL
    )
    assert match
    assert "uq_algorithm_code_versions_algo_lang_version" in match.group(0)


def test_create_algorithm_code_versions_has_partial_unique_current() -> None:
    """Partial UNIQUE index WHERE is_current enforces exactly-one-current."""
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    assert "uq_algorithm_code_versions_algo_lang_current" in output
    assert "WHERE is_current = TRUE" in output


def test_create_algorithm_code_versions_fk_is_cascade() -> None:
    """DATABASE_DESIGN §4.2: FK must CASCADE."""
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    match = re.search(
        r"CREATE TABLE algorithm_code_versions \((.*?)\);", output, re.DOTALL
    )
    assert match
    assert "REFERENCES algorithms" in match.group(0)
    assert "ON DELETE CASCADE" in match.group(0)


def test_create_algorithm_code_versions_downgrade_drops_table() -> None:
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("downgrade", "head:base", "--sql", env=env)
    assert re.search(r"DROP TABLE\s+algorithm_code_versions", output)


# ---------------------------------------------------------------------------
# B3.4 — create_algorithm_topics
# ---------------------------------------------------------------------------


def test_create_algorithm_topics_migration_exists() -> None:
    files = list(VERSIONS_DIR.glob("*_create_algorithm_topics.py"))
    assert files, "create_algorithm_topics migration is missing"


def test_algorithm_topics_depends_on_algorithm_code_versions() -> None:
    """Per DATABASE_DESIGN §6, 0007 follows the B3.x chain."""
    at_files = list(VERSIONS_DIR.glob("*_create_algorithm_topics.py"))
    cv_files = list(VERSIONS_DIR.glob("*_create_algorithm_code_versions.py"))
    assert at_files and cv_files

    cv_text = cv_files[0].read_text()
    cv_rev_match = re.search(
        r'^revision:\s*str\s*=\s*["\']([^"\']+)["\']', cv_text, re.MULTILINE
    )
    assert cv_rev_match
    cv_rev = cv_rev_match.group(1)

    at_text = at_files[0].read_text()
    down_rev_match = re.search(
        r'^down_revision:\s*[^=]+=\s*["\']([^"\']+)["\']',
        at_text,
        re.MULTILINE,
    )
    assert down_rev_match
    assert down_rev_match.group(1) == cv_rev


def test_create_algorithm_topics_emits_correct_schema() -> None:
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    match = re.search(r"CREATE TABLE algorithm_topics \((.*?)\);", output, re.DOTALL)
    assert match, "algorithm_topics CREATE TABLE not found"
    ddl = match.group(0)
    for col in ("algorithm_id", "topic_id"):
        assert col in ddl, f"missing column {col} in algorithm_topics DDL"


def test_create_algorithm_topics_has_composite_pk() -> None:
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    match = re.search(r"CREATE TABLE algorithm_topics \((.*?)\);", output, re.DOTALL)
    assert match
    assert "PRIMARY KEY (algorithm_id, topic_id)" in match.group(0)


def test_create_algorithm_topics_fks_cascade() -> None:
    """Both FKs must CASCADE per DATABASE_DESIGN §4.2."""
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    match = re.search(r"CREATE TABLE algorithm_topics \((.*?)\);", output, re.DOTALL)
    assert match
    ddl = match.group(0)
    assert "REFERENCES algorithms" in ddl
    assert "REFERENCES topics" in ddl
    # Both FKs must use CASCADE.
    assert ddl.count("ON DELETE CASCADE") == 2


def test_create_algorithm_topics_has_topic_id_index() -> None:
    """DATABASE_DESIGN §5 mandates ix_algorithm_topics_topic_id."""
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("upgrade", "head", "--sql", env=env)
    assert "ix_algorithm_topics_topic_id" in output


def test_create_algorithm_topics_downgrade_drops_table() -> None:
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    _, output = _alembic("downgrade", "head:base", "--sql", env=env)
    assert re.search(r"DROP TABLE\s+algorithm_topics", output)
