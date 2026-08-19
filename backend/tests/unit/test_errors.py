"""Unit tests for src.core.errors.

Covers:
- AppError payload schema is stable (extra fields forbidden)
- to_payload() returns ErrorPayload with correct code/message/details
- Each subclass uses its declared status_code + code
- Subclass overrides via constructor kwargs work
- ErrorPayload is JSON-serializable for HTTP responses

Refs: AlgoVision_BACKEND.md §3 (Hard Rules — uniform error envelope)
Refs: PUKU_BACKEND_AGENT.md §3.1 (Services don't import HTTP)
"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from src.core.errors import (
    AppError,
    BadRequest,
    Conflict,
    ErrorPayload,
    Forbidden,
    InvalidCredentials,
    NotFound,
    RateLimited,
    TokenExpired,
    TokenInvalid,
    Unauthorized,
    UserAlreadyExists,
    UserNotFound,
    ValidationFailed,
)


# ---------------------------------------------------------------------------
# ErrorPayload schema
# ---------------------------------------------------------------------------


def test_error_payload_round_trips_to_json() -> None:
    payload = ErrorPayload(
        code="test.code", message="hello", details={"x": 1}, request_id="r-1"
    )
    raw = payload.model_dump_json()
    parsed = json.loads(raw)
    assert parsed["code"] == "test.code"
    assert parsed["message"] == "hello"
    assert parsed["details"] == {"x": 1}
    assert parsed["request_id"] == "r-1"


def test_error_payload_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        ErrorPayload(code="x", message="y", unknown_field="z")


def test_error_payload_details_optional() -> None:
    payload = ErrorPayload(code="x", message="y")
    assert payload.details is None
    assert payload.request_id is None


# ---------------------------------------------------------------------------
# AppError basics
# ---------------------------------------------------------------------------


def test_app_error_uses_class_defaults() -> None:
    e = AppError("boom")
    assert e.message == "boom"
    assert e.code == "internal.error"
    assert e.status_code == 500


def test_app_error_constructor_overrides() -> None:
    e = AppError(
        "boom",
        code="custom.code",
        status_code=418,
        details={"reason": "i am a teapot"},
    )
    assert e.code == "custom.code"
    assert e.status_code == 418
    assert e.details == {"reason": "i am a teapot"}


def test_app_error_default_message_is_class_name() -> None:
    e = AppError()
    assert e.message == "AppError"


def test_app_error_to_payload_includes_request_id() -> None:
    e = AppError("x", code="y.code", details={"k": "v"})
    payload = e.to_payload(request_id="r-42")
    assert isinstance(payload, ErrorPayload)
    assert payload.code == "y.code"
    assert payload.message == "x"
    assert payload.details == {"k": "v"}
    assert payload.request_id == "r-42"


# ---------------------------------------------------------------------------
# Generic categories
# ---------------------------------------------------------------------------


def test_validation_failed_is_422() -> None:
    e = ValidationFailed("bad input")
    assert e.status_code == 422
    assert e.code == "validation.failed"


def test_not_found_is_404() -> None:
    e = NotFound("missing")
    assert e.status_code == 404
    assert e.code == "not_found"


def test_conflict_is_409() -> None:
    e = Conflict("dup")
    assert e.status_code == 409
    assert e.code == "conflict"


def test_unauthorized_is_401() -> None:
    e = Unauthorized("no")
    assert e.status_code == 401
    assert e.code == "unauthorized"


def test_forbidden_is_403() -> None:
    e = Forbidden("denied")
    assert e.status_code == 403
    assert e.code == "forbidden"


def test_rate_limited_is_429() -> None:
    e = RateLimited("slow down")
    assert e.status_code == 429
    assert e.code == "rate_limited"


def test_bad_request_is_400() -> None:
    e = BadRequest("malformed")
    assert e.status_code == 400
    assert e.code == "bad_request"


# ---------------------------------------------------------------------------
# Domain subclasses preserve parent status
# ---------------------------------------------------------------------------


def test_user_not_found_inherits_404() -> None:
    e = UserNotFound("u-1")
    assert e.status_code == 404
    assert e.code == "user.not_found"
    assert isinstance(e, NotFound)


def test_user_already_exists_inherits_409() -> None:
    e = UserAlreadyExists("dup email")
    assert e.status_code == 409
    assert e.code == "user.already_exists"
    assert isinstance(e, Conflict)


@pytest.mark.parametrize(
    "exc_cls",
    [InvalidCredentials, TokenExpired, TokenInvalid],
)
def test_auth_subclasses_inherit_401(exc_cls: type[AppError]) -> None:
    e = exc_cls("nope")
    assert e.status_code == 401
    assert e.code.startswith("auth.")
    assert isinstance(e, Unauthorized)


# ---------------------------------------------------------------------------
# Subclass can override default code via constructor
# ---------------------------------------------------------------------------


def test_subclass_can_override_code_per_instance() -> None:
    e = NotFound("custom", code="specific.not_found")
    assert e.code == "specific.not_found"
    assert e.status_code == 404


# ---------------------------------------------------------------------------
# Round-trip via to_payload + model_dump_json
# ---------------------------------------------------------------------------


def test_full_round_trip_through_http_shape() -> None:
    e = UserNotFound("u-42")
    payload = e.to_payload(request_id="req-1")
    wire = json.loads(payload.model_dump_json())
    assert wire == {
        "code": "user.not_found",
        "message": "u-42",
        "details": None,
        "request_id": "req-1",
    }