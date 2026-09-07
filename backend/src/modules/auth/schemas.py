"""Pydantic schemas for the auth API.

Pure I/O models. They validate the wire format and serialize the
response; they do NOT carry domain logic. Services and routers
use these to communicate; the User SQLAlchemy model never escapes
the repository layer (PUKU_BACKEND_AGENT §3.1).

Naming follows the convention in PUKU_BACKEND_AGENT §8:
- *Request    : incoming request body
- *Response   : outgoing response body
- *Filters    : query-string filter object (none for auth)

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 2 — B2.2)
Refs: AlgoVision_BACKEND.md §8 (Authentication), §26 (Response Models)
Refs: PUKU_BACKEND_AGENT.md §8 (Pydantic Schema Conventions)
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# Minimum password length. Argon2id tolerates arbitrary lengths, but
# NIST SP 800-63B recommends a minimum of 8 chars and modern guidance
# is at least 12 for human-chosen passwords. We enforce 12 — anything
# shorter is almost certainly a guessable credential.
MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 128  # bounded to prevent abuse via huge payloads
MAX_DISPLAY_NAME_LENGTH = 100
MAX_EMAIL_LENGTH = 320  # RFC 5321 max


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    """Body of POST /auth/register.

    Email is normalized server-side (lowercased + stripped) before
    persistence; this schema only validates format and length.
    """

    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(
        ...,
        max_length=MAX_EMAIL_LENGTH,
        description="User email. Must be a syntactically valid address.",
    )
    password: str = Field(
        ...,
        min_length=MIN_PASSWORD_LENGTH,
        max_length=MAX_PASSWORD_LENGTH,
        description="Plaintext password (12-128 chars). Hashed via Argon2id before storage.",
    )
    display_name: str = Field(
        ...,
        min_length=1,
        max_length=MAX_DISPLAY_NAME_LENGTH,
        description="Public-facing display name shown in the UI.",
    )


class LoginRequest(BaseModel):
    """Body of POST /auth/login."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(
        ...,
        max_length=MAX_EMAIL_LENGTH,
        description="User email.",
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=MAX_PASSWORD_LENGTH,
        description="Plaintext password.",
    )


class RefreshRequest(BaseModel):
    """Body of POST /auth/refresh.

    The refresh token may also be presented via the
    ``refresh_token`` HTTP-only cookie. The body form is supported
    for clients that prefer explicit token transport (mobile apps,
    server-to-server flows). Both are accepted by the endpoint;
    either one is sufficient.
    """

    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(
        ...,
        min_length=1,
        description="Refresh token issued by /auth/login or /auth/register.",
    )


class LogoutRequest(BaseModel):
    """Body of POST /auth/logout.

    Optional: if the body is empty, the endpoint revokes all
    refresh tokens for the current user. If the body carries a
    ``refresh_token``, only that token is revoked (single-session
    sign-out).
    """

    model_config = ConfigDict(extra="forbid")

    refresh_token: str | None = Field(
        default=None,
        description="Optional. If present, only this refresh token is revoked.",
    )


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class UserResponse(BaseModel):
    """Public-safe user representation.

    Routers return this from /auth/register, /auth/login, /auth/me.
    It deliberately omits ``password_hash`` and any internal flags
    (is_active is not surfaced to end users; deactivation is an
    admin-side concern not part of the public API yet).
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str = Field(
        ...,
        description="Lowercased email address. The DB stores CITEXT but we always return lowercase.",
    )
    display_name: str
    created_at: datetime


class TokenPair(BaseModel):
    """Access + refresh token pair returned by login/register/refresh.

    The same body shape is used whether tokens travel in cookies or
    JSON, so the frontend can decide which to consume. In our default
    cookie flow, the router ALSO sets the tokens as HTTP-only cookies
    on the response; the body is included for clients that prefer
    explicit bearer tokens (mobile, third-party integrations).
    """

    access_token: str = Field(
        ...,
        description="Short-lived access token (15 min by default).",
    )
    refresh_token: str = Field(
        ...,
        description="Single-use refresh token (7 days by default). Rotate on use.",
    )
    token_type: str = Field(
        default="bearer",
        description="Always 'bearer'. Future-proofs for other schemes.",
    )
    expires_in: int = Field(
        ...,
        gt=0,
        description="Access-token lifetime in seconds. Must be positive.",
    )


class AuthResponse(BaseModel):
    """Combined response from /auth/register and /auth/login.

    The frontend typically only needs the user info and the token
    pair; bundling them in one envelope avoids two round-trips.
    """

    user: UserResponse
    tokens: TokenPair
