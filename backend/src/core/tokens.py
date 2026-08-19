"""Token issuance and verification.

Two token flavors, distinct purposes:

- **Access token** — short-lived (default 15 min), stateless, signed
  with itsdangerous. Carries the user id (``sub``) and expiry. Used
  by ``get_current_user`` on every authenticated request.

- **Refresh token** — long-lived (default 7 days), opaque random
  string. Stored hashed in the ``refresh_tokens`` table so we can
  revoke / rotate it. Single-use: each refresh issues a new pair
  and marks the old refresh as ``used_at``.

Why two flavors
---------------
The classic JWT-vs-session split. Stateless access tokens keep the
hot path cheap (no DB hit per request); stateful refresh tokens
let us revoke sessions when needed (logout, password change,
suspicious activity).

Why itsdangerous, not PyJWT
---------------------------
itsdangerous gives us URL-safe signed tokens with a single
dependency (already pinned in pyproject). JWT would also work but
adds an extra library and forces an encoding choice (HS256 vs
RS256) we don't yet need — a single signing secret is fine for
a single-service deployment. We can swap to JWT later without
changing the API surface; this module is the only place that
knows.

Why access tokens are signed (not encrypted)
--------------------------------------------
The access token payload is only ``sub`` (user id) and ``exp``.
No PII, no roles — nothing that would need encryption. itsdangerous
URLSafeTimedSerializer provides HMAC-SHA256 signatures by default,
which is sufficient for tamper-detection.

Cookies vs body
---------------
Tokens can travel either in HTTP-only cookies (default, set by
the router) or in the response body (for clients that prefer
explicit bearer tokens). This module does not decide which —
it just signs / verifies the strings. Cookie handling lives in
the router (B2.6).

Refs: ALGOVISION_BACKEND_PLAN.md §8 (Auth architecture)
Refs: AlgoVision_BACKEND.md §29 (Authentication)
Refs: PUKU_BACKEND_AGENT.md §3.4 (never log secrets)
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from src.core.settings import Settings

# Distinct salts per token type. itsdangerous salts are HMAC
# domain separators — they don't have to be secret, but they MUST
# differ across token types so a refresh token can't be presented
# as an access token (or vice versa).
ACCESS_TOKEN_SALT = "algovision-access-token-v1"
REFRESH_TOKEN_SALT = "algovision-refresh-token-cookie-v1"


def _access_serializer(settings: Settings) -> URLSafeTimedSerializer:
    """Build a serializer for access tokens.

    The signing key is the project's SECRET_KEY. We strip the
    SecretStr wrapper so itsdangerous sees the raw string.
    """
    return URLSafeTimedSerializer(
        settings.secret_key.get_secret_value(),
        salt=ACCESS_TOKEN_SALT,
    )


def issue_access_token(user_id: UUID, settings: Settings) -> tuple[str, datetime]:
    """Create a signed access token for the given user.

    Returns the encoded token string and its absolute expiry
    timestamp. The expiry is computed from ``settings.access_token_ttl_seconds``
    and stamped both inside the signed payload (so the client
    knows) and returned separately (so callers can populate
    ``expires_in`` in the response).
    """
    now = datetime.now(UTC)
    expires_at = now + timedelta(seconds=settings.access_token_ttl_seconds)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = _access_serializer(settings).dumps(payload)
    return token, expires_at


def verify_access_token(token: str, settings: Settings) -> UUID:
    """Verify a signed access token and return the user id.

    Raises:
        TokenExpired: the token's ``exp`` is in the past.
        TokenInvalid: the signature is wrong, the payload is
            malformed, or the token has been tampered with.
    """
    # Import here to avoid a circular dependency between core.tokens
    # and core.errors at module-load time.
    from src.core.errors import TokenExpired, TokenInvalid

    serializer = _access_serializer(settings)
    max_age = settings.access_token_ttl_seconds
    try:
        payload = serializer.loads(token, max_age=max_age)
    except SignatureExpired as exc:
        raise TokenExpired("Access token has expired.") from exc
    except BadSignature as exc:
        raise TokenInvalid("Access token signature is invalid.") from exc

    sub = payload.get("sub")
    if not isinstance(sub, str):
        raise TokenInvalid("Access token payload is missing 'sub'.")
    try:
        return UUID(sub)
    except ValueError as exc:
        raise TokenInvalid("Access token 'sub' is not a valid UUID.") from exc


# ---------------------------------------------------------------------------
# Refresh tokens (opaque, stored hashed)
# ---------------------------------------------------------------------------


def issue_refresh_token(settings: Settings) -> tuple[str, datetime]:
    """Create a new opaque refresh token.

    Returns the plaintext token (the only time it's visible —
    must be returned to the client immediately) and its absolute
    expiry. The DB stores the SHA-256 hash, not the plaintext, so
    a database leak cannot let an attacker reuse refresh tokens.

    Why SHA-256, not bcrypt
    -----------------------
    Refresh tokens are high-entropy random strings (256 bits from
    ``secrets.token_urlsafe``). Brute-forcing a SHA-256 of such a
    value is computationally infeasible (2^256 operations), so a
    slow hash like bcrypt is unnecessary. SHA-256 also gives us
    fixed-length, indexable hashes for the DB lookup index.
    """
    now = datetime.now(UTC)
    expires_at = now + timedelta(seconds=settings.refresh_token_ttl_seconds)
    # 32 bytes -> 256 bits of entropy.
    plaintext = secrets.token_urlsafe(32)
    return plaintext, expires_at


def hash_refresh_token(plaintext: str) -> str:
    """Hash a refresh token for DB storage.

    Returns lowercase hex SHA-256 (64 chars). Using SHA-256
    directly is safe here because the input has 256 bits of
    cryptographic randomness — there's no need to slow it down.

    Empty input is rejected: an empty token would always verify
    against the empty hash, which is a footgun.
    """
    if not plaintext:
        raise ValueError("refresh token must not be empty")
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()
