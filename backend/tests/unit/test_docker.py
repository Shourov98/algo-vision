"""Unit tests for Dockerfile + docker-compose layout.

Static analysis only — actual container builds run in CI (B1.10).
We verify that the files exist, parse, and follow the
multi-stage / non-root / healthcheck invariants from
PUKU_BACKEND_AGENT.md §2 (Container: multi-stage Docker,
non-root runtime) and ARCHITECTURE.md §3 (deployment topology).

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 1.9)
Refs: ARCHITECTURE.md §3.1, §3.2
"""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = REPO_ROOT / "backend"


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------


def test_dockerfile_exists() -> None:
    assert (BACKEND_ROOT / "Dockerfile").is_file()


def test_dockerignore_exists() -> None:
    assert (BACKEND_ROOT / ".dockerignore").is_file()


def test_root_docker_compose_exists() -> None:
    assert (REPO_ROOT / "docker-compose.yml").is_file()


def test_local_db_compose_exists() -> None:
    assert (REPO_ROOT / "docker-compose.local-db.yml").is_file()


def test_initdb_sql_exists() -> None:
    assert (BACKEND_ROOT / "docker" / "initdb" / "01-extensions.sql").is_file()


# ---------------------------------------------------------------------------
# Dockerfile content checks
# ---------------------------------------------------------------------------


def _read_dockerfile() -> str:
    return (BACKEND_ROOT / "Dockerfile").read_text()


def test_dockerfile_is_multi_stage() -> None:
    """Must use builder + runtime stages so production images don't
    ship build tools (PUKU_BACKEND_AGENT §2)."""
    text = _read_dockerfile()
    assert "AS builder" in text
    assert "AS runtime" in text


def test_dockerfile_uses_python_3_12() -> None:
    text = _read_dockerfile()
    assert "python:3.12" in text


def test_dockerfile_runs_as_non_root() -> None:
    """Security: process must not run as root (PUKU_BACKEND §2,
    AlgoVision_BACKEND §3.4)."""
    text = _read_dockerfile()
    assert "useradd" in text
    assert "USER algovision" in text


def test_dockerfile_exposes_8000() -> None:
    text = _read_dockerfile()
    assert "EXPOSE 8000" in text


def test_dockerfile_has_healthcheck() -> None:
    """The image must self-probe so orchestrators know when it's ready."""
    text = _read_dockerfile()
    assert "HEALTHCHECK" in text
    assert "/health" in text


def test_dockerfile_uses_uvicorn() -> None:
    text = _read_dockerfile()
    assert "uvicorn" in text
    assert "src.main:app" in text


def test_dockerfile_sets_unbuffered_python() -> None:
    """Log lines should flush immediately — required for container
    log aggregators to capture them in real time."""
    text = _read_dockerfile()
    assert "PYTHONUNBUFFERED=1" in text


def test_dockerfile_does_not_copy_secrets() -> None:
    """.env must NOT be in the build context. .dockerignore covers it."""
    text = (BACKEND_ROOT / ".dockerignore").read_text()
    assert ".env" in text


# ---------------------------------------------------------------------------
# docker-compose content checks
# ---------------------------------------------------------------------------


def _load_main_compose() -> dict:
    return yaml.safe_load((REPO_ROOT / "docker-compose.yml").read_text())


def _load_local_compose() -> dict:
    return yaml.safe_load((REPO_ROOT / "docker-compose.local-db.yml").read_text())


def test_main_compose_defines_api_service() -> None:
    compose = _load_main_compose()
    assert "api" in compose["services"]


def test_main_compose_api_uses_dockerfile() -> None:
    compose = _load_main_compose()
    api = compose["services"]["api"]
    assert "build" in api
    assert api["build"]["dockerfile"] == "Dockerfile"


def test_main_compose_api_uses_env_file() -> None:
    """Secrets come from .env (gitignored) — never hardcoded."""
    compose = _load_main_compose()
    api = compose["services"]["api"]
    assert "env_file" in api
    assert "./backend/.env" in api["env_file"]


def test_main_compose_api_has_healthcheck() -> None:
    compose = _load_main_compose()
    api = compose["services"]["api"]
    assert "healthcheck" in api
    assert "/health" in api["healthcheck"]["test"][-1] or "/health" in str(
        api["healthcheck"]
    )


def test_main_compose_exposes_8000() -> None:
    compose = _load_main_compose()
    api = compose["services"]["api"]
    assert "8000:8000" in api["ports"]


def test_main_compose_does_not_run_local_db() -> None:
    """Per B1.9 plan: Supabase is the DB. Local-db is opt-in via the
    local-db.yml variant."""
    compose = _load_main_compose()
    assert "db" not in compose["services"]


def test_local_db_compose_has_db_and_api() -> None:
    compose = _load_local_compose()
    services = compose["services"]
    assert "db" in services
    assert "api" in services


def test_local_db_compose_db_uses_postgres_16() -> None:
    compose = _load_local_compose()
    db = compose["services"]["db"]
    assert "postgres:16" in db["image"]


def test_local_db_compose_db_mounts_initdb() -> None:
    """Init script installs pgcrypto + citext on first run."""
    compose = _load_local_compose()
    db = compose["services"]["db"]
    initdb_mount = db["volumes"]
    assert any("initdb" in v for v in initdb_mount)


def test_local_db_compose_api_depends_on_db_health() -> None:
    """API must wait for db to be healthy, not just started."""
    compose = _load_local_compose()
    api = compose["services"]["api"]
    assert api["depends_on"]["db"]["condition"] == "service_healthy"


def test_local_db_compose_api_points_to_local_db() -> None:
    compose = _load_local_compose()
    env = compose["services"]["api"]["environment"]
    assert env["DATABASE_URL"].endswith("@db:5432/algovision")


def test_local_db_compose_keeps_volume_for_persistence() -> None:
    """DB data must persist across `docker compose down`."""
    compose = _load_local_compose()
    assert "volumes" in compose
    assert "algovision-db-data" in compose["volumes"]


# ---------------------------------------------------------------------------
# .dockerignore coverage
# ---------------------------------------------------------------------------


def test_dockerignore_excludes_pycache() -> None:
    text = (BACKEND_ROOT / ".dockerignore").read_text()
    assert "__pycache__" in text


def test_dockerignore_excludes_env() -> None:
    text = (BACKEND_ROOT / ".dockerignore").read_text()
    # .env listed but .env.example explicitly preserved with !
    assert ".env" in text
    assert "!.env.example" in text


def test_dockerignore_excludes_git() -> None:
    text = (BACKEND_ROOT / ".dockerignore").read_text()
    assert ".git/" in text
