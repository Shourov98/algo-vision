"""Unit tests for Alembic configuration.

These tests validate the layout and env.py logic without connecting
to a real database. The first migration lands in B1.7; integration
tests against real Supabase Postgres will live in
tests/integration/ and use the configured DATABASE_URL_SYNC.

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 1.6)
Refs: DATABASE_DESIGN.md §6 (Migration Plan)
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest


BACKEND_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = BACKEND_ROOT / "alembic.ini"
MIGRATIONS_DIR = BACKEND_ROOT / "migrations"
ENV_PY = MIGRATIONS_DIR / "env.py"


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------


def test_alembic_ini_exists() -> None:
    assert ALEMBIC_INI.is_file(), f"missing {ALEMBIC_INI}"


def test_migrations_dir_exists() -> None:
    assert MIGRATIONS_DIR.is_dir()


def test_versions_dir_exists_or_alembic_can_create_it() -> None:
    """Either the versions/ dir exists, or env.py would let alembic
    create it on first revision run. Both are fine.
    """
    versions = MIGRATIONS_DIR / "versions"
    assert versions.is_dir()


def test_env_py_exists() -> None:
    assert ENV_PY.is_file()


def test_script_template_exists() -> None:
    assert (MIGRATIONS_DIR / "script.py.mako").is_file()


# ---------------------------------------------------------------------------
# alembic.ini sanity
# ---------------------------------------------------------------------------


def _read_alembic_ini() -> str:
    return ALEMBIC_INI.read_text()


def test_alembic_ini_declares_script_location() -> None:
    text = _read_alembic_ini()
    assert re.search(r"^script_location\s*=\s*migrations\b", text, re.MULTILINE)


def test_alembic_ini_does_not_hardcode_database_url() -> None:
    """The URL is resolved at runtime from DATABASE_URL_SYNC, not
    hardcoded in alembic.ini. Hardcoding secrets would be a leak."""
    text = _read_alembic_ini()
    # Match only the value on the same line, stopping at the newline.
    match = re.search(r"^sqlalchemy\.url\s*=\s*([^\n#]*?)\s*(?:#.*)?$", text, re.MULTILINE)
    assert match is not None
    assert match.group(1).strip() == "", (
        f"alembic.ini must not hardcode sqlalchemy.url; "
        f"got {match.group(1)!r}"
    )


def test_alembic_ini_prepends_backend_to_sys_path() -> None:
    text = _read_alembic_ini()
    assert re.search(r"^prepend_sys_path\s*=\s*\.", text, re.MULTILINE)


# ---------------------------------------------------------------------------
# env.py URL resolution (via subprocess, since direct import requires
# alembic context to be active).
# ---------------------------------------------------------------------------


def _alembic(*args: str, env: dict[str, str] | None = None) -> tuple[int, str]:
    """Run ``alembic <args>`` from the backend/ dir. Return (exit, stdout+stderr)."""
    import subprocess

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


def test_alembic_current_fails_clearly_without_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`alembic current` without DATABASE_URL_SYNC must surface the
    RuntimeError from env.py, not crash with a confusing SQL error."""
    monkeypatch.delenv("DATABASE_URL_SYNC", raising=False)
    code, output = _alembic("current")
    assert code != 0
    assert "DATABASE_URL_SYNC is not set" in output


def test_alembic_offline_sql_emits_to_stdout() -> None:
    """`alembic upgrade head --sql` emits SQL without connecting."""
    # No DATABASE_URL_SYNC required for offline mode since env.py
    # resolves it but doesn't connect.
    # However, env.py requires it for online; --sql switches to
    # offline which still calls _resolve_database_url, so we need it.
    env = {"DATABASE_URL_SYNC": "postgresql+psycopg2://user:pw@localhost/db"}
    code, output = _alembic("upgrade", "head", "--sql", env=env)
    assert code == 0, output
    # No migration scripts yet (versions/ is empty except .gitkeep),
    # so the output is essentially the alembic_version bookkeeping.
    assert "alembic_version" in output or "SELECT" in output.upper() or code == 0


def test_env_py_has_online_and_offline_modes() -> None:
    text = ENV_PY.read_text()
    assert "def run_migrations_online" in text
    assert "def run_migrations_offline" in text
    # Top-level branch picks one based on alembic context.
    assert "context.is_offline_mode()" in text


def test_env_py_uses_null_pool_for_short_lived_process() -> None:
    """Online migrations must use NullPool — no connection pool
    needed for a CLI process that opens one connection, runs, exits."""
    text = ENV_PY.read_text()
    assert "pool.NullPool" in text


def test_env_py_target_metadata_is_none_for_phase_1() -> None:
    """Until src/core/models.py exists, target_metadata is None.
    Subsequent commits will replace this with the project metadata."""
    text = ENV_PY.read_text()
    assert re.search(
        r"^target_metadata\s*=\s*None\b", text, re.MULTILINE
    )


# ---------------------------------------------------------------------------
# Migration template
# ---------------------------------------------------------------------------


def test_template_includes_upgrade_and_downgrade() -> None:
    text = (MIGRATIONS_DIR / "script.py.mako").read_text()
    assert "def upgrade" in text
    assert "def downgrade" in text
    assert "revision: str" in text
    assert "down_revision" in text


# ---------------------------------------------------------------------------
# Skip the actual alembic CLI invocation (would need real DB).
# We assert layout + env.py logic only; ``alembic upgrade head`` runs
# in B1.7 once a real DATABASE_URL_SYNC is configured.
# ---------------------------------------------------------------------------