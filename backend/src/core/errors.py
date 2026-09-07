"""Domain exception hierarchy and HTTP mapping.

A single exception base (``AppError``) carries an HTTP status, an
error code, an optional user message, and optional details. Services
raise ``AppError`` subclasses; routers never translate exceptions
manually. The exception handler in ``main.py`` (B1.4 wiring commit)
turns these into uniform JSON responses.

Why a hierarchy instead of bare HTTPException
--------------------------------------------
- HTTPException is a FastAPI/Starlette concept. Services must not
  depend on HTTP — that would couple domain code to a web framework.
- The ``code`` field is a stable machine-readable identifier that
  the frontend can switch on (``"user.not_found"`` etc.). HTTP
  status alone is ambiguous across error categories.
- The ``details`` field carries structured info (validation errors,
  conflict reasons) without bloating the user-facing message.

Refs: PUKU_BACKEND_AGENT.md §3.1 (Services must not import HTTP)
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 1.4)
Refs: AlgoVision_BACKEND.md §3 (Hard Rules)
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class ErrorPayload(BaseModel):
    """JSON body returned for every AppError.

    Stable schema — frontend code may parse it directly.

    Fields
    ------
    code:
        Stable machine identifier (e.g. ``"validation.failed"``).
        Lowercase, dot-separated namespace.
    message:
        Human-readable description. Safe to show to end users.
    details:
        Optional structured info (validation errors, conflict reasons).
        Never contains secrets or PII.
    request_id:
        Filled by middleware (added in B6.3). Optional here so the
        schema is stable before the middleware exists.
    """

    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    details: dict[str, Any] | None = None
    request_id: str | None = None


class AppError(Exception):
    """Base exception for all expected domain errors.

    Subclasses set class-level defaults for ``status_code`` and
    ``code`` so callers can simply raise without specifying them.

    Unexpected exceptions (bugs) propagate to FastAPI's default
    500 handler and are NOT mapped to AppError. We do NOT want to
    hide bugs behind a friendly error envelope.
    """

    status_code: int = 500
    code: str = "internal.error"

    def __init__(
        self,
        message: str | None = None,
        *,
        details: dict[str, Any] | None = None,
        code: str | None = None,
        status_code: int | None = None,
    ) -> None:
        self.message = message or self.__class__.__name__
        self.details = details
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.message)

    def to_payload(self, request_id: str | None = None) -> ErrorPayload:
        return ErrorPayload(
            code=self.code,
            message=self.message,
            details=self.details,
            request_id=request_id,
        )


# ---------------------------------------------------------------------------
# Generic categories
# ---------------------------------------------------------------------------


class ValidationFailed(AppError):
    status_code = 422
    code = "validation.failed"


class NotFound(AppError):
    status_code = 404
    code = "not_found"


class Conflict(AppError):
    status_code = 409
    code = "conflict"


class Unauthorized(AppError):
    status_code = 401
    code = "unauthorized"


class Forbidden(AppError):
    status_code = 403
    code = "forbidden"


class RateLimited(AppError):
    status_code = 429
    code = "rate_limited"


class BadRequest(AppError):
    status_code = 400
    code = "bad_request"


# ---------------------------------------------------------------------------
# Domain-specific (added as features land; one per file later)
# ---------------------------------------------------------------------------


class UserNotFound(NotFound):
    code = "user.not_found"


class UserAlreadyExists(Conflict):
    code = "user.already_exists"


class InvalidCredentials(Unauthorized):
    code = "auth.invalid_credentials"


class TokenExpired(Unauthorized):
    code = "auth.token_expired"


class TokenInvalid(Unauthorized):
    code = "auth.token_invalid"