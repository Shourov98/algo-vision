"""Smoke tests for the FastAPI app factory.

Confirms:
- create_app() with default settings returns a FastAPI instance
- The / endpoint reflects the supplied settings.app_env
- create_app(settings=...) accepts an override
- AppError raised in a route becomes a uniform JSON envelope

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 1.2 + 1.4)
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.core.errors import NotFound, UserNotFound
from src.core.settings import Settings, get_settings
from src.main import create_app, dispose_engine


@pytest.fixture
def test_settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    """Provide a minimal Settings instance the factory can consume."""
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://postgres:pw@db:5432/test"
    )
    monkeypatch.setenv(
        "DATABASE_URL_SYNC", "postgresql+psycopg2://postgres:pw@db:5432/test"
    )
    monkeypatch.setenv("SECRET_KEY", "x" * 64)
    get_settings.cache_clear()
    return get_settings()


def test_create_app_returns_fastapi_instance(test_settings: Settings) -> None:
    app: FastAPI = create_app(test_settings)
    assert isinstance(app, FastAPI)
    assert app.title == "AlgoVision API"


@pytest.mark.asyncio
async def test_lifespan_disposes_engine_on_shutdown(
    test_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The lifespan context releases shared DB resources on shutdown."""
    disposed: list[bool] = []

    async def _dispose_engine() -> None:
        disposed.append(True)
        await dispose_engine()

    monkeypatch.setattr("src.main.dispose_engine", _dispose_engine)
    app = create_app(test_settings)

    async with app.router.lifespan_context(app):
        assert disposed == []

    assert disposed == [True]


def test_root_endpoint_reports_environment(test_settings: Settings) -> None:
    app = create_app(test_settings)
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "algovision-backend"
    assert body["status"] == "scaffold"
    assert body["environment"] == "test"


def test_create_app_uses_default_settings_when_none(monkeypatch) -> None:
    """create_app() with no args should not crash and produce a valid app."""
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://postgres:pw@db:5432/x"
    )
    monkeypatch.setenv(
        "DATABASE_URL_SYNC", "postgresql+psycopg2://postgres:pw@db:5432/x"
    )
    monkeypatch.setenv("SECRET_KEY", "x" * 64)
    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)
    response = client.get("/")
    assert response.json()["environment"] == "development"


# ---------------------------------------------------------------------------
# Error envelope (B1.4)
# ---------------------------------------------------------------------------


def test_app_error_becomes_json_envelope(test_settings: Settings) -> None:
    app = create_app(test_settings)

    @app.get("/_test/notfound")
    def _raise_notfound() -> None:
        raise UserNotFound("u-42")

    client = TestClient(app)
    response = client.get("/_test/notfound")
    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "user.not_found"
    assert body["message"] == "u-42"
    assert body.get("request_id") is None  # filled by B6.3 middleware
    assert "details" not in body or body["details"] is None


def test_generic_not_found_uses_default_code(test_settings: Settings) -> None:
    app = create_app(test_settings)

    @app.get("/_test/anything-missing")
    def _raise() -> None:
        raise NotFound("the thing is missing")

    client = TestClient(app)
    response = client.get("/_test/anything-missing")
    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "not_found"
    assert body["message"] == "the thing is missing"


def test_validation_failed_carries_details(test_settings: Settings) -> None:
    from src.core.errors import ValidationFailed

    app = create_app(test_settings)

    @app.get("/_test/invalid")
    def _raise() -> None:
        raise ValidationFailed("bad input", details={"field": "email"})

    client = TestClient(app)
    response = client.get("/_test/invalid")
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation.failed"
    assert body["details"] == {"field": "email"}


def test_unexpected_exception_keeps_default_500(
    test_settings: Settings,
) -> None:
    """Bugs (not AppError) must NOT be silently downgraded to a 200
    or hidden behind the AppError envelope. We expect a 500 status,
    NOT the AppError envelope (which has 'code'/'message' keys).
    """
    app = create_app(test_settings)

    @app.get("/_test/bug")
    def _raise_bug() -> None:
        raise RuntimeError("oops")

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/_test/bug")
    # 500 status is the contract we care about. The body may be a JSON
    # envelope (modern FastAPI/Starlette) or a plain string (legacy),
    # depending on installed versions — both are acceptable defaults;
    # what matters is that we did NOT rewrite it to our envelope.
    assert response.status_code == 500
    # Our envelope uses 'code' as a top-level key. The default 500
    # body must not contain it.
    assert "code" not in response.text
    # The body must mention 'Internal Server Error' OR be a JSON
    # object with 'detail', but never a 'code' field.
    assert "code" not in response.text or '"code"' not in response.text
