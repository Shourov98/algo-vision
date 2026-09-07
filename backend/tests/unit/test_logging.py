"""Unit tests for src.core.logging.

These tests validate the public API of the logging module:
- configure_logging(settings) is idempotent
- Production settings -> JSON renderer
- Development settings -> console renderer
- Secret redaction happens before rendering
- contextvars bind service + environment
- Log level comes from settings

The tests use a fresh StreamHandler + StringIO so they don't depend
on pytest's logging capture (which can shadow our handlers).

Refs: AlgoVision_BACKEND.md §3.4 (no secrets in logs)
Refs: PUKU_BACKEND_AGENT.md §3.4
"""

from __future__ import annotations

import io
import json
import logging

import pytest
import structlog
from src.core.logging import configure_logging, log
from src.core.settings import Settings, get_settings

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_settings(env: str) -> Settings:
    import os
    os.environ["APP_ENV"] = env
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:pw@db:5432/x"
    os.environ["DATABASE_URL_SYNC"] = "postgresql+psycopg2://postgres:pw@db:5432/x"
    os.environ["SECRET_KEY"] = "x" * 64
    get_settings.cache_clear()
    return get_settings()


@pytest.fixture
def captured(monkeypatch: pytest.MonkeyPatch):
    """Yield a (configure, capture_and_call) helper pair.

    capture_and_call() returns the raw bytes written to our StringIO
    so individual tests can parse what they need (JSON, console, etc.)
    """
    captured_buf = io.StringIO()

    def capture_and_call(settings: Settings, level: str, **fields) -> str:
        # Ensure structlog is configured fresh for THIS settings.
        structlog.reset_defaults()
        configure_logging(settings)
        # Replace the stderr stream on the installed handler with
        # our buffer.
        handler = logging.getLogger().handlers[-1]
        handler.stream = captured_buf
        # Clear the buffer from any earlier flushes.
        captured_buf.seek(0)
        captured_buf.truncate()
        getattr(log, level)("test_event", **fields)
        handler.flush()
        return captured_buf.getvalue()

    return capture_and_call


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


def test_configure_logging_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    """Calling configure_logging twice must not add a second
    AlgoVision-owned handler. (Other libraries' handlers are kept.)"""
    s = _make_settings("development")
    # Count our handlers by formatter type — every AlgoVision-owned
    # handler uses ProcessorFormatter.
    def _ours(h: logging.Handler) -> bool:
        from structlog.stdlib import ProcessorFormatter
        return isinstance(h.formatter, ProcessorFormatter)

    configure_logging(s)
    ours_first = sum(1 for h in logging.getLogger().handlers if _ours(h))
    configure_logging(s)
    ours_second = sum(1 for h in logging.getLogger().handlers if _ours(h))
    assert ours_first == 1
    assert ours_second == 1


def test_configure_logging_does_not_remove_foreign_handlers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    s = _make_settings("development")
    root = logging.getLogger()

    class ForeignHandler(logging.Handler):
        pass

    foreign = ForeignHandler()
    root.addHandler(foreign)
    try:
        configure_logging(s)
        assert foreign in root.handlers
        # Foreign handler was not removed; AlgoVision handler was added.
        assert root.handlers.count(foreign) == 1
    finally:
        root.removeHandler(foreign)


# ---------------------------------------------------------------------------
# Renderer selection
# ---------------------------------------------------------------------------


def test_production_emits_json(captured) -> None:
    s = _make_settings("production")
    output = captured(s, "info", x=1)
    line = output.strip().splitlines()[-1]
    parsed = json.loads(line)
    assert parsed["event"] == "test_event"
    assert parsed["x"] == 1
    assert parsed["environment"] == "production"
    assert parsed["service"] == "algovision-backend"


def test_development_emits_console(captured) -> None:
    s = _make_settings("development")
    output = captured(s, "info", x=1)
    # ConsoleRenderer output contains the event name and the extra field.
    assert "test_event" in output
    assert "x" in output
    # NOT valid JSON (console renderer).
    line = output.strip().splitlines()[-1]
    with pytest.raises(json.JSONDecodeError):
        json.loads(line)


# ---------------------------------------------------------------------------
# Secret redaction
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "sensitive_key",
    [
        "password",
        "Password",
        "PASSWORD",
        "secret_key",
        "access_token",
        "Authorization",
        "supabase_service_role_key",
        "cookie",
        "api_key",
    ],
)
def test_sensitive_keys_redacted(captured, sensitive_key: str) -> None:
    s = _make_settings("production")
    output = captured(s, "info", **{sensitive_key: "supersecretvalue"})
    parsed = json.loads(output.strip().splitlines()[-1])
    assert parsed[sensitive_key] == "[REDACTED]"
    assert "supersecretvalue" not in output


def test_non_sensitive_keys_pass_through(captured) -> None:
    s = _make_settings("production")
    output = captured(s, "info", user_id=42, name="alice")
    parsed = json.loads(output.strip().splitlines()[-1])
    assert parsed["user_id"] == 42
    assert parsed["name"] == "alice"


# ---------------------------------------------------------------------------
# Context binding
# ---------------------------------------------------------------------------


def test_service_and_environment_bound(captured) -> None:
    s = _make_settings("production")
    output = captured(s, "info", marker="x")
    parsed = json.loads(output.strip().splitlines()[-1])
    assert parsed["service"] == "algovision-backend"
    assert parsed["environment"] == "production"


# ---------------------------------------------------------------------------
# Log level from settings
# ---------------------------------------------------------------------------


def test_log_level_respects_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    import os
    os.environ["APP_ENV"] = "development"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://x"
    os.environ["DATABASE_URL_SYNC"] = "postgresql+psycopg2://x"
    os.environ["SECRET_KEY"] = "x" * 64
    get_settings.cache_clear()
    s = get_settings()
    structlog.reset_defaults()
    configure_logging(s)
    assert logging.getLogger().level == logging.DEBUG


def test_uvicorn_access_quieted_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import os
    os.environ["APP_ENV"] = "production"
    os.environ["LOG_LEVEL"] = "INFO"
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://x"
    os.environ["DATABASE_URL_SYNC"] = "postgresql+psycopg2://x"
    os.environ["SECRET_KEY"] = "x" * 64
    get_settings.cache_clear()
    s = get_settings()
    structlog.reset_defaults()
    configure_logging(s)
    assert logging.getLogger("uvicorn.access").level == logging.WARNING


# ---------------------------------------------------------------------------
# Logger export
# ---------------------------------------------------------------------------


def test_module_level_log_is_bound_logger() -> None:
    assert hasattr(log, "info")
    assert hasattr(log, "warning")
    assert hasattr(log, "error")
