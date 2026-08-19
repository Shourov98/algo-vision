"""Unit tests for src.core.settings.

Covers:
- Happy path with all required env vars
- Defaults when optional env vars are absent
- CORS comma-split parsing
- Hard rule: CORS_ALLOWED_ORIGINS='*' is rejected
- SecretStr masking (the value never leaks into repr/str)
- get_settings() is process-cached
- app_env coercion (uppercase / mixed case rejected)

Refs: AlgoVision_BACKEND.md §3.4 (Security — secrets from env, no '*' CORS)
Refs: PUKU_BACKEND_AGENT.md §3.4
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from pydantic import SecretStr, ValidationError

from src.core.settings import Settings, get_settings


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def base_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Provide a valid base env so Settings() can construct without errors.

    Individual tests override the variables they care about.
    """
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:pw@db.ref.supabase.co:5432/postgres",
    )
    monkeypatch.setenv(
        "DATABASE_URL_SYNC",
        "postgresql+psycopg2://postgres:pw@db.ref.supabase.co:5432/postgres",
    )
    monkeypatch.setenv("SECRET_KEY", "x" * 64)
    yield


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_settings_constructs_with_required_vars(base_env: None) -> None:
    settings = Settings()
    assert settings.app_env == "development"
    assert settings.database_url.startswith("postgresql+asyncpg://")
    assert isinstance(settings.secret_key, SecretStr)
    # SecretStr masks by default.
    assert "x" * 64 not in repr(settings.secret_key)


def test_settings_applies_defaults_when_optional_vars_missing(
    base_env: None,
) -> None:
    settings = Settings()
    assert settings.db_pool_size == 5
    assert settings.db_max_overflow == 10
    assert settings.cookie_secure is False
    assert settings.cookie_samesite == "lax"
    assert settings.log_level == "INFO"
    assert settings.rate_limit_default == "100/minute"


# ---------------------------------------------------------------------------
# CORS parsing
# ---------------------------------------------------------------------------


def test_cors_origins_parsed_from_comma_separated_env(
    monkeypatch: pytest.MonkeyPatch,
    base_env: None,
) -> None:
    monkeypatch.setenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000, https://app.example.com ,http://127.0.0.1:8080",
    )
    settings = Settings()
    assert settings.cors_allowed_origins == [
        "http://localhost:3000",
        "https://app.example.com",
        "http://127.0.0.1:8080",
    ]


def test_cors_wildcard_rejected(monkeypatch: pytest.MonkeyPatch, base_env: None) -> None:
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "*")
    with pytest.raises(ValidationError) as excinfo:
        Settings()
    assert "CORS_ALLOWED_ORIGINS must not contain" in str(excinfo.value)


def test_cors_empty_env_yields_empty_list(
    monkeypatch: pytest.MonkeyPatch,
    base_env: None,
) -> None:
    """Empty CORS_ALLOWED_ORIGINS means 'no origins', distinct from 'unset'."""
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "")
    settings = Settings()
    assert settings.cors_allowed_origins == []


def test_cors_unset_uses_defaults(base_env: None) -> None:
    """Unset CORS_ALLOWED_ORIGINS uses the dev default list."""
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    settings = Settings()
    assert settings.cors_allowed_origins == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    monkeypatch.undo()


# ---------------------------------------------------------------------------
# Secret handling
# ---------------------------------------------------------------------------


def test_secret_key_min_length_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://postgres:pw@db:5432/x")
    monkeypatch.setenv("DATABASE_URL_SYNC", "postgresql+psycopg2://postgres:pw@db:5432/x")
    monkeypatch.setenv("SECRET_KEY", "too-short")
    with pytest.raises(ValidationError):
        Settings()


def test_secret_key_value_not_leaked_in_repr(base_env: None) -> None:
    settings = Settings()
    # SecretStr returns '**********' for str() and hides value in repr.
    assert str(settings.secret_key).startswith("*")
    assert settings.secret_key.get_secret_value() == "x" * 64


# ---------------------------------------------------------------------------
# app_env coercion
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_value", ["prod", "PRODUCTION", "live", "staging"])
def test_app_env_rejects_unknown_values(
    monkeypatch: pytest.MonkeyPatch,
    base_env: None,
    bad_value: str,
) -> None:
    monkeypatch.setenv("APP_ENV", bad_value)
    with pytest.raises(ValidationError):
        Settings()


def test_app_env_accepts_all_three_valid_values(
    monkeypatch: pytest.MonkeyPatch,
    base_env: None,
) -> None:
    for env in ("development", "test", "production"):
        monkeypatch.setenv("APP_ENV", env)
        settings = Settings()
        assert settings.app_env == env
        assert settings.is_development is (env == "development")
        assert settings.is_production is (env == "production")
        assert settings.is_test is (env == "test")


# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------


def test_get_settings_is_cached(base_env: None) -> None:
    get_settings.cache_clear()
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
    get_settings.cache_clear()
    s3 = get_settings()
    assert s3 is not s1


# ---------------------------------------------------------------------------
# Cookie configuration tied to environment
# ---------------------------------------------------------------------------


def test_cookie_secure_true_in_production(
    monkeypatch: pytest.MonkeyPatch,
    base_env: None,
) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("COOKIE_SECURE", "true")
    settings = Settings()
    assert settings.cookie_secure is True
    assert settings.is_production is True


def test_cookie_samesite_choices_enforced(
    monkeypatch: pytest.MonkeyPatch,
    base_env: None,
) -> None:
    monkeypatch.setenv("COOKIE_SAMESITE", "none")
    settings = Settings()
    assert settings.cookie_samesite == "none"
    monkeypatch.setenv("COOKIE_SAMESITE", "invalid")
    with pytest.raises(ValidationError):
        Settings()


# ---------------------------------------------------------------------------
# Sanity: test environment does not depend on a real .env file
# ---------------------------------------------------------------------------


def test_settings_does_not_require_env_file(base_env: None, tmp_path) -> None:
    """Run from a directory with no .env file — Settings must still load."""
    cwd = os.getcwd()
    try:
        os.chdir(tmp_path)  # empty dir
        settings = Settings()
        assert settings.database_url.startswith("postgresql+asyncpg://")
    finally:
        os.chdir(cwd)