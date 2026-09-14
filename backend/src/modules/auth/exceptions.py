"""Auth-specific domain exceptions.

These extend the generic categories in ``src.core.errors`` with
auth-stable codes that the frontend can switch on.

Conventions
-----------
- ``code`` is dot-namespaced: ``auth.*`` for auth, ``user.*`` for
  user-related errors.
- All subclasses set HTTP ``status_code`` and a stable ``code``.
- No exception carries a password, hash, or token in its message.

Refs: ALGOVISION_BACKEND_PLAN.md §6 (Error Handling)
Refs: PUKU_BACKEND_AGENT.md §7.4 (Error Handling)
"""

from __future__ import annotations

from src.core.errors import (
    Forbidden,
    Unauthorized,
)


class AccountInactive(Forbidden):
    """The user's account is marked inactive (deactivated by admin).

    403 — the credentials are valid but the account is not allowed
    to authenticate. Distinct from InvalidCredentials so the
    frontend can show "please contact support" rather than
    "wrong password".
    """

    code = "auth.account_inactive"


class RefreshTokenRevoked(Unauthorized):
    """The refresh token has been explicitly revoked (logout).

    Either the user logged out, an admin revoked all sessions,
    or the token family was revoked because a stolen token was
    detected (out of scope for B2.5; covered in B2.9).
    """

    code = "auth.refresh_revoked"


class RefreshTokenAlreadyUsed(Unauthorized):
    """Single-use rotation violation.

    The presented refresh token was already exchanged for a new
    pair. This indicates either a bug or an attacker replaying
    a stolen token. The service should revoke the entire token
    family (handled in B2.9; for now we just reject).
    """

    code = "auth.refresh_used"


class RefreshTokenExpired(Unauthorized):
    """The refresh token's ``expires_at`` is in the past.

    Mirrors ``TokenExpired`` for access tokens, but a distinct
    code so the frontend can react differently (e.g. force a
    full re-login rather than auto-refresh).
    """

    code = "auth.refresh_expired"
