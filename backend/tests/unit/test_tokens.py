"""Unit tests for src.core.tokens (access + refresh token issuance).

These tests cover the cryptographic primitives only. The DB round-trip
for refresh-token storage is exercised in B2.9's integration tests.

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 2 — B2.4)
Refs: AlgoVision_BACKEND.md §29 (Authentication)
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from itsdangerous import BadSignature
from src.core.errors import TokenExpired, TokenInvalid
from src.core.settings import Settings, get_settings
from src.core.tokens import (
    ACCESS_TOKEN_SALT,
    REFRESH_TOKEN_SALT,
    hash_refresh_token,
    issue_access_token,
    issue_refresh_token,
    verify_access_token,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "app_env": "test",
        "database_url": "postgresql+asyncpg://x:x@x/x",
        "database_url_sync": "postgresql+psycopg2://x:x@x/x",
        "secret_key": "x" * 64,
    }
    base.update(overrides)
    return Settings.model_validate(base)


@pytest.fixture(autouse=True)
def _clear_cache() -> Iterator[None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def settings() -> Settings:
    return _make_settings()


# ---------------------------------------------------------------------------
# Access tokens
# ---------------------------------------------------------------------------


class TestAccessToken:
    def test_issue_returns_token_and_expiry(self, settings: Settings) -> None:
        uid = uuid4()
        token, expires_at = issue_access_token(uid, settings)
        assert isinstance(token, str)
        assert token
        assert isinstance(expires_at, datetime)
        assert expires_at.tzinfo is not None

    def test_expiry_matches_ttl(self, settings: Settings) -> None:
        """expires_at must equal now + access_token_ttl_seconds."""
        before = datetime.now(UTC)
        _, expires_at = issue_access_token(uuid4(), settings)
        after = datetime.now(UTC)
        expected_low = before + timedelta(seconds=settings.access_token_ttl_seconds)
        expected_high = after + timedelta(seconds=settings.access_token_ttl_seconds)
        assert expected_low <= expires_at <= expected_high

    def test_verify_returns_user_id(self, settings: Settings) -> None:
        uid = uuid4()
        token, _ = issue_access_token(uid, settings)
        assert verify_access_token(token, settings) == uid

    def test_issued_token_is_url_safe(self, settings: Settings) -> None:
        """itsdangerous URLSafeTimedSerializer uses base64-url
        characters so the token can travel in a cookie or query."""
        token, _ = issue_access_token(uuid4(), settings)
        # No spaces, no '+' or '/' (url-safe base64 alphabet).
        assert " " not in token
        assert "+" not in token
        assert "/" not in token

    def test_tampered_signature_raises_invalid(self, settings: Settings) -> None:
        token, _ = issue_access_token(uuid4(), settings)
        # Flip the last character.
        tampered = token[:-1] + ("a" if token[-1] != "a" else "b")
        with pytest.raises(TokenInvalid):
            verify_access_token(tampered, settings)

    def test_garbage_token_raises_invalid(self, settings: Settings) -> None:
        with pytest.raises(TokenInvalid):
            verify_access_token("not-a-token", settings)

    def test_empty_token_raises_invalid(self, settings: Settings) -> None:
        with pytest.raises(TokenInvalid):
            verify_access_token("", settings)

    def test_access_token_does_not_verify_under_refresh_salt(
        self,
        settings: Settings,
    ) -> None:
        """Defensive: a token issued under the access salt must NOT
        deserialize under the refresh salt (different salting keys).
        We verify this by attempting to unsign the access token
        with the refresh salt — it must fail."""
        from itsdangerous import URLSafeTimedSerializer

        uid = uuid4()
        access_token, _ = issue_access_token(uid, settings)
        wrong_serializer = URLSafeTimedSerializer(
            settings.secret_key.get_secret_value(),
            salt=REFRESH_TOKEN_SALT,
        )
        with pytest.raises(BadSignature):
            wrong_serializer.loads(access_token)

    def test_short_ttl_token_expires(self, settings: Settings) -> None:
        """Verify our wrapper maps itsdangerous' ``SignatureExpired``
        to our domain ``TokenExpired``.

        We don't rely on a real sleep — itsdangerous' ``max_age``
        check has a granularity of ~1 second and the settings floor
        for access-token TTL is 60 seconds, so a real-time test
        would be slow and flaky. Instead we patch the private
        serializer factory so verify_access_token sees a stub
        whose ``loads`` raises ``SignatureExpired``.
        """
        from unittest.mock import MagicMock, patch

        from itsdangerous import SignatureExpired

        token, _ = issue_access_token(uuid4(), settings)

        # Stub the serializer: dumps works (already issued), loads
        # raises SignatureExpired so our wrapper hits the except
        # branch.
        stub = MagicMock()
        stub.loads.side_effect = SignatureExpired("stale")

        with patch(
            "src.core.tokens._access_serializer",
            return_value=stub,
        ), pytest.raises(TokenExpired):
            verify_access_token(token, settings)


class TestAccessTokenSalts:
    """Salts are constants — verify the constants don't accidentally
    collide or change silently."""

    def test_salts_are_distinct(self) -> None:
        assert ACCESS_TOKEN_SALT != REFRESH_TOKEN_SALT


# ---------------------------------------------------------------------------
# Refresh tokens
# ---------------------------------------------------------------------------


class TestRefreshToken:
    def test_issue_returns_token_and_expiry(self, settings: Settings) -> None:
        plaintext, expires_at = issue_refresh_token(settings)
        assert isinstance(plaintext, str)
        assert plaintext
        assert isinstance(expires_at, datetime)
        assert expires_at.tzinfo is not None

    def test_expiry_matches_ttl(self, settings: Settings) -> None:
        before = datetime.now(UTC)
        _, expires_at = issue_refresh_token(settings)
        after = datetime.now(UTC)
        expected_low = before + timedelta(seconds=settings.refresh_token_ttl_seconds)
        expected_high = after + timedelta(seconds=settings.refresh_token_ttl_seconds)
        assert expected_low <= expires_at <= expected_high

    def test_each_issue_produces_unique_token(self, settings: Settings) -> None:
        """Refresh tokens must be unique — collision would let an
        attacker reuse a token issued to a different user."""
        a, _ = issue_refresh_token(settings)
        b, _ = issue_refresh_token(settings)
        assert a != b

    def test_issued_token_is_url_safe(self, settings: Settings) -> None:
        plaintext, _ = issue_refresh_token(settings)
        # token_urlsafe uses base64-url alphabet, no padding.
        assert " " not in plaintext
        assert "+" not in plaintext
        assert "/" not in plaintext

    def test_issued_token_has_high_entropy(self, settings: Settings) -> None:
        """token_urlsafe(32) -> 32 bytes = 256 bits. The encoded
        length depends on alphabet density; assert >= 43 chars
        (base64 of 32 bytes = 44 chars, sometimes 43 without pad)."""
        plaintext, _ = issue_refresh_token(settings)
        assert len(plaintext) >= 43


# ---------------------------------------------------------------------------
# hash_refresh_token
# ---------------------------------------------------------------------------


class TestHashRefreshToken:
    def test_returns_hex_sha256(self) -> None:
        h = hash_refresh_token("anything")
        # SHA-256 hex digest is exactly 64 lowercase hex chars.
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_is_deterministic(self) -> None:
        """Same input -> same hash (so DB lookups work)."""
        assert hash_refresh_token("x") == hash_refresh_token("x")

    def test_different_inputs_produce_different_hashes(self) -> None:
        assert hash_refresh_token("a") != hash_refresh_token("b")

    def test_empty_input_rejected(self) -> None:
        """An empty token would always hash to a known value
        (sha256('')) which is a footgun."""
        with pytest.raises(ValueError, match="refresh token must not be empty"):
            hash_refresh_token("")


# ---------------------------------------------------------------------------
# Cross-cutting
# ---------------------------------------------------------------------------


class TestAccessTokenUUIDParsing:
    def test_sub_must_be_uuid(self, settings: Settings) -> None:
        """If a token somehow has a non-UUID sub (e.g. from an
        old deployment with a different encoding), reject it
        rather than treating the user id as opaque garbage."""
        from itsdangerous import URLSafeTimedSerializer

        serializer = URLSafeTimedSerializer(
            settings.secret_key.get_secret_value(),
            salt=ACCESS_TOKEN_SALT,
        )
        # Forge a payload with a non-UUID sub.
        bad_token = serializer.dumps({"sub": "not-a-uuid", "exp": 9999999999})
        with pytest.raises(TokenInvalid, match="not a valid UUID"):
            verify_access_token(bad_token, settings)

    def test_missing_sub_rejected(self, settings: Settings) -> None:
        from itsdangerous import URLSafeTimedSerializer

        serializer = URLSafeTimedSerializer(
            settings.secret_key.get_secret_value(),
            salt=ACCESS_TOKEN_SALT,
        )
        bad_token = serializer.dumps({"exp": 9999999999})
        with pytest.raises(TokenInvalid, match="missing 'sub'"):
            verify_access_token(bad_token, settings)


# ---------------------------------------------------------------------------
# Type sanity
# ---------------------------------------------------------------------------


def test_user_id_roundtrip_preserves_uuid_type(settings: Settings) -> None:
    """The verified token returns a UUID instance, not a string."""
    uid = uuid4()
    token, _ = issue_access_token(uid, settings)
    out = verify_access_token(token, settings)
    assert isinstance(out, UUID)
    assert out == uid
