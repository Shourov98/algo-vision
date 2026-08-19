"""Smoke tests for the FastAPI app factory.

Confirms:
- create_app() with default settings returns a FastAPI instance
- The / endpoint reflects the supplied settings.app_env
- create_app(settings=...) accepts an override

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 1.2)
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.settings import Settings, get_settings
from src.main import create_app


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