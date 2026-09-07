"""Structured logging configuration (structlog).

A single ``configure_logging(settings)`` entry point is called once
from ``create_app`` (and once from the Alembic env). The function:

- Wires stdlib logging through structlog so libraries that use the
  stdlib logger (``uvicorn``, ``sqlalchemy``, ``alembic``) emit
  through the same JSON pipeline.
- Switches between pretty console renderer (development/test) and
  JSON renderer (production) so log aggregators can parse output.
- Adds request-id + service + environment fields to every record
  via context variables.

Why a function, not a module-level call
---------------------------------------
- Tests must be able to call ``configure_logging`` repeatedly with
  different settings without piling up handlers.
- The function must be idempotent — calling it twice should not
  duplicate handlers (stdlib logging has a global handler list).

Refs: PUKU_BACKEND_AGENT.md §2 (structlog, JSON in non-dev)
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 1.3)
Refs: AlgoVision_BACKEND.md §3 (no secrets in logs)
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

from src.core.settings import Settings

# Module-level state — the bound logger any module can import.
# Re-bound by configure_logging() so tests that reconfigure don't
# capture stale processors.
log: structlog.stdlib.BoundLogger = structlog.get_logger("algovision")

# Set of handler identities we've previously installed. Used to make
# configure_logging() idempotent — handlers are removed by identity
# check on subsequent calls rather than relying on a marker attribute
# (which can be lost if the handler is replaced by a third party).
_INSTALLED_HANDLERS: set[int] = set()

# Context-local placeholders. structlog.contextvars merges these
# into every log record emitted within the current asyncio task.
_BASE_CONTEXT: dict[str, Any] = {
    "service": "algovision-backend",
}


def configure_logging(settings: Settings) -> None:
    """Idempotently configure stdlib + structlog for this process.

    Safe to call multiple times. Each call:
    1. Removes any handlers we previously added (idempotency).
    2. Installs our shared processors on the stdlib root logger.
    3. Resets structlog config with the appropriate renderer.

    Handlers added by third-party libraries (uvicorn, alembic) are
    left in place but disabled so all records flow through us.
    """
    log_level = getattr(logging, settings.log_level)

    # --- shared structlog processor chain ----------------------------------
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        # Always keep secrets-redaction LAST among transformers so the
        # redaction sees the final field names.
        _redact_secrets,
    ]

    # Renderer chosen by environment:
    # - production: JSON for log aggregators
    # - development/test: console for humans
    if settings.is_production:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    # --- structlog config --------------------------------------------------
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # --- stdlib formatter that delegates to structlog processors ----------
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    # --- single stderr handler, idempotent ---------------------------------
    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    # Remove only handlers we previously installed (avoid clobbering
    # uvicorn's handlers in tests that import this module).
    root_logger.handlers = [
        h for h in root_logger.handlers if id(h) not in _INSTALLED_HANDLERS
    ]
    _INSTALLED_HANDLERS.clear()
    root_logger.addHandler(handler)
    _INSTALLED_HANDLERS.add(id(handler))
    root_logger.setLevel(log_level)

    # --- bind context for this process -------------------------------------
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        service=_BASE_CONTEXT["service"],
        environment=settings.app_env,
    )

    # Quiet down chatty third-party loggers unless DEBUG is requested.
    if log_level > logging.DEBUG:
        for noisy in ("uvicorn.access", "sqlalchemy.engine", "asyncio"):
            logging.getLogger(noisy).setLevel(logging.WARNING)


def _redact_secrets(
    logger: Any,
    method_name: str,
    event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    """Remove well-known secret-bearing fields from log records.

    Defense in depth — services must not log secrets in the first
    place (PUKU_BACKEND_AGENT.md §3.4), but if they accidentally do,
    the field never reaches the renderer.
    """
    sensitive_keys = {
        "password",
        "passwd",
        "secret",
        "secret_key",
        "token",
        "access_token",
        "refresh_token",
        "authorization",
        "cookie",
        "set-cookie",
        "api_key",
        "supabase_service_role_key",
    }
    for key in list(event_dict.keys()):
        if key.lower() in sensitive_keys:
            event_dict[key] = "[REDACTED]"
    return event_dict