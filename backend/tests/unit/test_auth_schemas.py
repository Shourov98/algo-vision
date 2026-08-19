"""Unit tests for auth Pydantic schemas.

We don't need a DB or live app — these tests exercise the
validation/serialization rules in pure isolation. Per
PUKU_BACKEND_AGENT §13 (Test Conventions), schema tests live at the
unit tier because they have no I/O.

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 2 — B2.2)
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError
from src.modules.auth.schemas import (
    MAX_PASSWORD_LENGTH,
    MIN_PASSWORD_LENGTH,
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserResponse,
)

# ---------------------------------------------------------------------------
# RegisterRequest
# ---------------------------------------------------------------------------


class TestRegisterRequest:
    def test_valid_payload_parses(self) -> None:
        req = RegisterRequest(
            email="Alice@Example.COM",
            password="correct-horse-battery-staple",
            display_name="Alice",
        )
        # email-validator normalizes the domain per RFC 5321
        # (Example.COM -> Example.com). The local part (Alice) is
        # preserved. Service-layer lowercasing happens in
        # AuthService.register before persistence.
        assert req.email == "Alice@example.com"
        assert req.display_name == "Alice"

    def test_short_password_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc:
            RegisterRequest(
                email="a@b.com",
                password="short",  # < MIN_PASSWORD_LENGTH
                display_name="A",
            )
        assert "password" in str(exc.value)

    def test_long_password_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="a@b.com",
                password="x" * (MAX_PASSWORD_LENGTH + 1),
                display_name="A",
            )

    def test_invalid_email_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="not-an-email",
                password="correct-horse-battery-staple",
                display_name="A",
            )

    def test_empty_display_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="a@b.com",
                password="correct-horse-battery-staple",
                display_name="",
            )

    def test_extra_fields_forbidden(self) -> None:
        """extra='forbid' prevents clients from sneaking in
        extra keys that the service layer would silently ignore."""
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="a@b.com",
                password="correct-horse-battery-staple",
                display_name="A",
                is_admin=True,
            )

    def test_min_password_length_is_twelve(self) -> None:
        """Documented baseline: 12-char minimum (NIST + modern guidance)."""
        assert MIN_PASSWORD_LENGTH == 12


# ---------------------------------------------------------------------------
# LoginRequest
# ---------------------------------------------------------------------------


class TestLoginRequest:
    def test_valid_payload(self) -> None:
        req = LoginRequest(email="x@y.com", password="hunter2hunter2")
        assert req.email == "x@y.com"

    def test_short_password_still_allowed_at_login(self) -> None:
        """Login accepts whatever the user typed at signup time.
        We do NOT impose a min length here — the user might have
        registered before a stricter policy. The check happens at
        registration, not at login."""
        req = LoginRequest(email="x@y.com", password="x")
        assert req.password == "x"

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            LoginRequest(email="x@y.com", password="x", csrf="forged")


# ---------------------------------------------------------------------------
# RefreshRequest / LogoutRequest
# ---------------------------------------------------------------------------


class TestRefreshRequest:
    def test_minimum_required(self) -> None:
        req = RefreshRequest(refresh_token="opaque-token-string")
        assert req.refresh_token == "opaque-token-string"

    def test_empty_token_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RefreshRequest(refresh_token="")


class TestLogoutRequest:
    def test_default_body_is_empty(self) -> None:
        """An empty body revokes all sessions — the common case."""
        req = LogoutRequest.model_validate({})
        assert req.refresh_token is None

    def test_with_specific_token(self) -> None:
        req = LogoutRequest(refresh_token="abc")
        assert req.refresh_token == "abc"


# ---------------------------------------------------------------------------
# UserResponse
# ---------------------------------------------------------------------------


class TestUserResponse:
    def test_serializes_required_fields(self) -> None:
        uid = uuid4()
        now = datetime(2026, 1, 1, tzinfo=UTC)
        resp = UserResponse(
            id=uid,
            email="a@b.com",
            display_name="Alice",
            created_at=now,
        )
        assert resp.id == uid
        assert resp.email == "a@b.com"
        assert resp.created_at == now

    def test_password_hash_is_not_a_field(self) -> None:
        """Defense-in-depth: ensure the response model has no slot
        for password_hash even if a service accidentally tries to
        pass it."""
        fields = set(UserResponse.model_fields.keys())
        assert "password_hash" not in fields
        assert "hashed_password" not in fields


# ---------------------------------------------------------------------------
# TokenPair + AuthResponse
# ---------------------------------------------------------------------------


class TestTokenPair:
    def test_token_type_defaults_to_bearer(self) -> None:
        pair = TokenPair(
            access_token="at",
            refresh_token="rt",
            expires_in=900,
        )
        assert pair.token_type == "bearer"

    def test_explicit_token_type_preserved(self) -> None:
        pair = TokenPair(
            access_token="at",
            refresh_token="rt",
            token_type="mac",
            expires_in=900,
        )
        assert pair.token_type == "mac"

    def test_expires_in_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            TokenPair(access_token="a", refresh_token="r", expires_in=0)


class TestAuthResponse:
    def test_envelope_contains_user_and_tokens(self) -> None:
        resp = AuthResponse(
            user=UserResponse(
                id=uuid4(),
                email="x@y.com",
                display_name="X",
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
            ),
            tokens=TokenPair(
                access_token="at",
                refresh_token="rt",
                expires_in=900,
            ),
        )
        dumped = resp.model_dump()
        assert "user" in dumped
        assert "tokens" in dumped
        assert dumped["tokens"]["token_type"] == "bearer"
