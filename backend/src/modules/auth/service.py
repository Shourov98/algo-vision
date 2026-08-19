"""Auth service: orchestrates registration, login, logout, refresh.

Single-responsibility rule (PUKU_BACKEND_AGENT §3.1)
----------------------------------------------------
- Services do not import HTTP. Routers do.
- Services do not import SQL. Repositories do.
- Services depend on repository PROTOCOLS so tests can swap fakes.

What this class owns
--------------------
- Email normalization (lowercase + strip) before persistence.
- Password hashing + verification (delegated to ``core.security``).
- Access token issuance + verification (delegated to ``core.tokens``).
- Refresh-token rotation: mark old used, insert new pair.
- Account status enforcement (deactivated users can't log in).
- Audit-friendly transaction boundaries: every public method commits
  via the injected session so routers don't manage the unit-of-work.

What this class does NOT own
----------------------------
- Rate limiting (B2.8 — slowapi decorator on the router).
- HTTP cookie setting (B2.6 router).
- Family revocation on refresh-token replay (B2.9 — only B2.5's job
  here is to reject the replay; full family revocation comes later).

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 2 — B2.5)
Refs: AlgoVision_BACKEND.md §8 (Authentication)
Refs: PUKU_BACKEND_AGENT.md §6, §10 (Service Conventions)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import (
    InvalidCredentials,
    Unauthorized,
    UserAlreadyExists,
    UserNotFound,
)
from src.core.security import hash_password, verify_password
from src.core.settings import Settings
from src.core.tokens import (
    issue_access_token,
    issue_refresh_token,
    verify_access_token,
)
from src.modules.auth.exceptions import (
    AccountInactive,
    RefreshTokenAlreadyUsed,
    RefreshTokenExpired,
    RefreshTokenRevoked,
)
from src.modules.auth.repository import (
    RefreshTokensRepositoryProtocol,
)
from src.modules.auth.schemas import (
    AuthResponse,
    TokenPair,
    UserResponse,
)
from src.modules.users.models import User
from src.modules.users.repository import (
    UsersRepositoryProtocol,
)

# ---------------------------------------------------------------------------
# Service protocol — lets routers (and tests) depend on the abstraction
# ---------------------------------------------------------------------------


class AuthServiceProtocol(Protocol):
    """Interface the auth router depends on.

    Adding a method here is a deliberate breaking change for any
    caller — keep this protocol minimal and stable.
    """

    async def register(
        self,
        email: str,
        password: str,
        display_name: str,
    ) -> AuthResponse: ...

    async def login(self, email: str, password: str) -> AuthResponse: ...

    async def refresh(self, refresh_token: str) -> TokenPair: ...

    async def logout(
        self,
        user_id: UUID,
        refresh_token: str | None,
    ) -> None: ...

    async def get_current_user(self, access_token: str) -> User: ...


# ---------------------------------------------------------------------------
# Concrete service
# ---------------------------------------------------------------------------


class AuthService:
    """Concrete auth orchestration.

    Composition is done via constructor injection: the service is
    given an ``AsyncSession`` and the two repositories. Tests pass
    fakes implementing the protocols; production code passes
    ``UsersRepository(session)`` and ``RefreshTokensRepository(session)``.
    """

    def __init__(
        self,
        session: AsyncSession,
        users_repo: UsersRepositoryProtocol,
        refresh_tokens_repo: RefreshTokensRepositoryProtocol,
        settings: Settings,
    ) -> None:
        self._session = session
        self._users = users_repo
        self._refresh_tokens = refresh_tokens_repo
        self._settings = settings

    # ------------------------------------------------------------------
    # register
    # ------------------------------------------------------------------

    async def register(
        self,
        email: str,
        password: str,
        display_name: str,
    ) -> AuthResponse:
        """Create a new user and return an AuthResponse.

        Order of operations:
        1. Normalize email (lowercase + strip). EmailStr in the schema
           already lowercased the domain; we lowercase the whole
           address defensively because the schema may evolve.
        2. Check uniqueness — explicit, because we'd rather raise a
           friendly ``UserAlreadyExists`` than let the DB raise an
           IntegrityError on insert.
        3. Hash the password (Argon2id, parameters from settings).
        4. Persist user via the repository.
        5. Issue access + refresh tokens, persist the refresh hash.
        6. Commit the session.

        Raises:
            UserAlreadyExists: email is already registered.
        """
        normalized_email = self._normalize_email(email)
        existing = await self._users.get_by_email(normalized_email)
        if existing is not None:
            # We do NOT disclose whether the email is registered vs
            # not — but the API contract here is explicit, so we
            # raise the friendly conflict. Callers can use a generic
            # 409 envelope if they prefer.
            raise UserAlreadyExists(
                "An account with that email already exists.",
                details={"field": "email"},
            )

        password_hash = hash_password(password, self._settings)
        user = await self._users.create(
            email=normalized_email,
            password_hash=password_hash,
            display_name=display_name,
        )
        tokens = await self._issue_token_pair(user.id)
        # Single unit of work: user row + refresh-token row committed
        # together. If the second insert fails, the user row is
        # rolled back too.
        await self._session.commit()
        return AuthResponse(
            user=_user_to_response(user),
            tokens=tokens,
        )

    # ------------------------------------------------------------------
    # login
    # ------------------------------------------------------------------

    async def login(self, email: str, password: str) -> AuthResponse:
        """Authenticate by email + password and return an AuthResponse.

        Order of operations:
        1. Normalize email.
        2. Look up user by email. If absent, raise ``InvalidCredentials``
           (NOT ``UserNotFound`` — we never disclose whether an email
           is registered).
        3. Verify password (constant-time Argon2id verify).
        4. Reject inactive accounts with ``AccountInactive`` so the
           frontend can show a specific message.
        5. Issue + persist tokens, commit, return.

        Raises:
            InvalidCredentials: email not found OR password mismatch.
            AccountInactive: the user exists but is deactivated.
        """
        normalized_email = self._normalize_email(email)
        user = await self._users.get_by_email(normalized_email)
        if user is None:
            # Defeat account enumeration: same error path / status
            # code as a wrong password.
            raise InvalidCredentials("Invalid email or password.")

        if not verify_password(password, user.password_hash, self._settings):
            raise InvalidCredentials("Invalid email or password.")

        if not user.is_active:
            # Distinct code so the frontend can render a clear message
            # ("please contact support") rather than "wrong password".
            raise AccountInactive(
                "This account has been deactivated. Please contact support.",
            )

        tokens = await self._issue_token_pair(user.id)
        await self._session.commit()
        return AuthResponse(
            user=_user_to_response(user),
            tokens=tokens,
        )

    # ------------------------------------------------------------------
    # refresh
    # ------------------------------------------------------------------

    async def refresh(self, refresh_token: str) -> TokenPair:
        """Rotate a single-use refresh token and return a new pair.

        Order of operations:
        1. Look up the refresh row by token hash.
        2. Reject if revoked -> ``RefreshTokenRevoked``.
        3. Reject if used   -> ``RefreshTokenAlreadyUsed``. (Full
           family revocation lands in B2.9; for now we just reject.)
        4. Reject if expired -> ``RefreshTokenExpired``.
        5. Mark old row ``used_at``.
        6. Issue new pair, persist new refresh hash.
        7. Commit.

        Raises:
            RefreshTokenRevoked: explicit logout / admin revocation.
            RefreshTokenAlreadyUsed: replay attempt (or a bug).
            RefreshTokenExpired: ``expires_at`` in the past.
            Unauthorized: token not found in DB.
        """
        record = await self._refresh_tokens.get_by_token(refresh_token)
        if record is None:
            # Don't disclose whether the token exists at all.
            raise Unauthorized("Refresh token is invalid.")

        # Order matters: ``revoked`` must precede ``used`` because an
        # admin-revoked token should never reanimate.
        if record.revoked_at is not None:
            raise RefreshTokenRevoked(
                "Refresh token has been revoked. Please sign in again.",
            )
        if record.used_at is not None:
            raise RefreshTokenAlreadyUsed(
                "Refresh token has already been used. Please sign in again.",
            )
        # Compare against UTC ``now``; ``expires_at`` carries tzinfo
        # because the column is TIMESTAMPTZ.
        if record.expires_at <= datetime.now(UTC):
            raise RefreshTokenExpired(
                "Refresh token has expired. Please sign in again.",
            )

        await self._refresh_tokens.mark_used(record.id)
        tokens = await self._issue_token_pair(record.user_id)
        await self._session.commit()
        return tokens

    # ------------------------------------------------------------------
    # logout
    # ------------------------------------------------------------------

    async def logout(
        self,
        user_id: UUID,
        refresh_token: str | None,
    ) -> None:
        """Revoke refresh tokens for the current user.

        Two modes:
        - ``refresh_token`` provided: revoke only that row.
        - ``refresh_token`` is None: revoke every non-revoked refresh
          token belonging to ``user_id`` (logout-all-sessions).

        The caller is responsible for clearing any cookies on the
        response (this service does not touch HTTP).

        Raises:
            UserNotFound: the user_id does not exist. We check this
                so we don't silently accept a logout for an invalid
                user — the router will turn it into a 404.
        """
        # Confirm the user exists. We deliberately don't raise if the
        # user is inactive — logout should always succeed for
        # authenticated callers, even deactivating admins can still
        # sign themselves out.
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise UserNotFound("User does not exist.")

        if refresh_token is None:
            await self._refresh_tokens.revoke_all_for_user(user_id)
        else:
            record = await self._refresh_tokens.get_by_token(refresh_token)
            if record is not None and record.user_id == user_id:
                await self._refresh_tokens.revoke(record.id)
            # If the token doesn't exist or belongs to someone else,
            # we silently do nothing — don't disclose token ownership
            # state to a potential attacker.
        await self._session.commit()

    # ------------------------------------------------------------------
    # get_current_user (used by the FastAPI dependency in B2.6)
    # ------------------------------------------------------------------

    async def get_current_user(self, access_token: str) -> User:
        """Verify an access token and return the corresponding user.

        Order of operations:
        1. Verify the access token signature + expiry.
        2. Look up the user by id from the token's ``sub``.
        3. Reject if the user is inactive (403).
        4. Reject if the user has been deleted (404).

        Raises:
            TokenExpired: the access token has expired.
            TokenInvalid: signature / payload is bad.
            UserNotFound: the user behind the token no longer exists.
            AccountInactive: the user is deactivated.
        """
        user_id = verify_access_token(access_token, self._settings)
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise UserNotFound("User does not exist.")
        if not user.is_active:
            raise AccountInactive(
                "This account has been deactivated. Please contact support.",
            )
        return user

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _issue_token_pair(self, user_id: UUID) -> TokenPair:
        """Issue an access+refresh pair and persist the refresh hash.

        Split out so register, login, and refresh all build the same
        pair shape. Does NOT commit — the caller does.
        """
        access_token, _ = issue_access_token(user_id, self._settings)
        refresh_plaintext, refresh_expires_at = issue_refresh_token(
            self._settings,
        )
        await self._refresh_tokens.insert(
            user_id=user_id,
            plaintext_token=refresh_plaintext,
            expires_at=refresh_expires_at,
        )
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_plaintext,
            token_type="bearer",
            expires_in=self._settings.access_token_ttl_seconds,
        )

    @staticmethod
    def _normalize_email(email: str) -> str:
        """Lowercase + strip the email.

        The DB column is CITEXT (case-insensitive) so the index would
        match either way, but lowercasing in Python guarantees a
        stable representation in queries / logs / comparisons.
        """
        return email.strip().lower()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _user_to_response(user: User) -> UserResponse:
    """Convert a User ORM row to a public-safe UserResponse.

    Keeping this in service.py (not routers) means the rule
    "ORM models never escape the service layer" is enforced here
    even if a future router is added in a hurry.
    """
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        created_at=user.created_at,
    )


__all__ = [
    "AuthService",
    "AuthServiceProtocol",
]
