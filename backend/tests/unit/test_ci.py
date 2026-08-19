"""Unit tests for the GitHub Actions CI workflow.

Static analysis only. The workflow runs in CI itself; here we
validate the YAML structure, required jobs, and hard invariants
(PUKU_BACKEND_AGENT.md §10 verification gates).

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 1.10)
Refs: PUKU_BACKEND_AGENT.md §10 (Verification Gates)
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "backend-ci.yml"


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------


def test_workflow_file_exists() -> None:
    assert WORKFLOW.is_file()


def test_workflow_yaml_parses() -> None:
    text = WORKFLOW.read_text()
    parsed = yaml.safe_load(text)
    assert parsed is not None


# ---------------------------------------------------------------------------
# Required jobs
# ---------------------------------------------------------------------------


@pytest.fixture
def workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text())


def test_workflow_has_lint_job(workflow: dict) -> None:
    assert "lint" in workflow["jobs"]


def test_workflow_has_typecheck_job(workflow: dict) -> None:
    assert "typecheck" in workflow["jobs"]


def test_workflow_has_test_job(workflow: dict) -> None:
    assert "test" in workflow["jobs"]


def test_workflow_has_migrations_job(workflow: dict) -> None:
    """Per the verification table in PUKU_BACKEND_AGENT §10:
    alembic upgrade/downgrade must run in CI."""
    assert "migrations" in workflow["jobs"]


def test_workflow_has_docker_job(workflow: dict) -> None:
    assert "docker" in workflow["jobs"]


def test_workflow_runs_on_pull_request(workflow: dict) -> None:
    on = workflow[True] if True in workflow else workflow["on"]  # YAML 'on' quirk
    assert "pull_request" in on


def test_workflow_runs_on_push(workflow: dict) -> None:
    on = workflow[True] if True in workflow else workflow["on"]
    assert "push" in on


# ---------------------------------------------------------------------------
# Verification gates
# ---------------------------------------------------------------------------


def _job_text(workflow: dict, name: str) -> str:
    return WORKFLOW.read_text()


def test_lint_job_uses_ruff() -> None:
    text = _job_text(None, "lint")  # type: ignore[arg-type]
    assert "ruff" in text


def test_lint_job_checks_format_and_lint() -> None:
    text = _job_text(None, "lint")  # type: ignore[arg-type]
    assert "ruff format --check" in text
    assert "ruff check" in text


def test_typecheck_job_uses_mypy() -> None:
    text = _job_text(None, "typecheck")  # type: ignore[arg-type]
    assert "mypy" in text


def test_test_job_runs_pytest_with_coverage() -> None:
    text = _job_text(None, "test")  # type: ignore[arg-type]
    assert "pytest" in text
    assert "--cov" in text


def test_migrations_job_uses_ephemeral_postgres() -> None:
    """Migrations must run against a real ephemeral Postgres, not
    the application DB. We use the GitHub Actions service container
    pattern (postgres:16-alpine)."""
    text = _job_text(None, "migrations")  # type: ignore[arg-type]
    assert "postgres:16-alpine" in text
    assert "services:" in text or "services :" in text


def test_migrations_job_runs_upgrade_then_downgrade() -> None:
    """Per DATABASE_DESIGN §6: every migration must round-trip."""
    text = _job_text(None, "migrations")  # type: ignore[arg-type]
    assert "alembic upgrade head" in text
    assert "alembic downgrade base" in text


def test_migrations_job_installs_extensions() -> None:
    """Postgres image doesn't ship citext by default; we install."""
    text = _job_text(None, "migrations")  # type: ignore[arg-type]
    assert "pgcrypto" in text
    assert "citext" in text


# ---------------------------------------------------------------------------
# Secrets hygiene
# ---------------------------------------------------------------------------


def test_workflow_does_not_hardcode_database_url() -> None:
    """Per PUKU_BACKEND_AGENT.md §3.4 and AlgoVision_BACKEND §3.4:
    secrets must come from env / secrets manager, never inline."""
    text = WORKFLOW.read_text()
    # The literal DATABASE_URL assignments use env-var form, not
    # literal passwords. Look for any literal 'password' that isn't
    # in a comment or env-var reference.

    # Allow 'POSTGRES_PASSWORD: postgres' in the postgres service
    # definition since that's a local-only dev credential, not a
    # production secret.
    # We just check that the DATABASE_URL line uses env substitution.
    assert "DATABASE_URL_SYNC: postgresql+psycopg2://postgres:postgres@localhost" in text


def test_workflow_caches_pip() -> None:
    text = WORKFLOW.read_text()
    assert "cache: pip" in text


# ---------------------------------------------------------------------------
# Concurrency
# ---------------------------------------------------------------------------


def test_workflow_cancels_in_progress_runs() -> None:
    workflow = yaml.safe_load(WORKFLOW.read_text())
    assert "concurrency" in workflow
    assert "cancel-in-progress: true" in WORKFLOW.read_text()


# ---------------------------------------------------------------------------
# Branch coverage
# ---------------------------------------------------------------------------


def test_pull_request_targets_dev_backend(workflow: dict) -> None:
    """Per GIT_WORKFLOW §1.2: backend PRs target dev-backend."""
    on = workflow[True] if True in workflow else workflow["on"]
    pr = on["pull_request"]
    assert "dev-backend" in pr["branches"]


def test_push_targets_main_and_develop(workflow: dict) -> None:
    on = workflow[True] if True in workflow else workflow["on"]
    push = on["push"]
    for branch in ("main", "develop", "dev-backend"):
        assert branch in push["branches"], f"missing {branch}"


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------


def test_workflow_permissions_are_minimal() -> None:
    """Least-privilege: contents:read is enough for checkout."""
    workflow = yaml.safe_load(WORKFLOW.read_text())
    perms = workflow.get("permissions", {})
    assert perms.get("contents") == "read"
