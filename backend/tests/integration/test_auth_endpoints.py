"""End-to-end integration tests for /api/v1/auth.

These tests exercise the full HTTP stack against a real
PostgreSQL test database. The HTTP client is httpx AsyncClient
wired to the FastAPI app via ASGITransport; the auth service
dependency is overridden so each request gets a fresh DB
session.

Coverage targets (per PUKU_BACKEND_AGENT §13.4):

- Happy paths for register, login, refresh, logout, /me.
- Cross-cutting concerns: cookies, account enumeration defense,
  refresh-token rotation semantics, replay protection,
  cascade delete behavior.

What's NOT covered here
-----------------------
- Argon2 hashing details — those live in test_security.py.
- JWT/signed-token signing — those live in test_tokens.py.
- Per-route rate limiting — those live in test_auth_router.py
  (HTTP layer) and would need explicit clock manipulation
  for end-to-end coverage. Rate limits are enforced in
  production via slowapi and exercised in unit tests with a
  custom limiter.

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 2 - B2.9)
Refs: PUKU_BACKEND_AGENT.md §13 (Test Conventions)
"""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.auth.repository import RefreshToken
from src.modules.users.models import User

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _register(
    client: AsyncClient,
    email: str,
    password: str = "correct-horse-battery-staple",
    display_name: str = "Alice",
) -> dict[str, object]:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "display_name": display_name,
        },
    )
    return {"status_code": response.status_code, "body": response.json()}


async def _login(
    client: AsyncClient,
    email: str,
    password: str = "correct-horse-battery-staple",
) -> dict[str, object]:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return {"status_code": response.status_code, "body": response.json()}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestRegister:
    async def test_happy_path_creates_user_and_returns_tokens(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        result = await _register(client, "alice@example.com")
        assert result["status_code"] == 201
        body = result["body"]  # type: ignore[assignment]
        assert body["user"]["email"] == "alice@example.com"  # type: ignore[index]
        assert "access_token" in body["tokens"]  # type: ignore[index]
        assert "refresh_token" in body["tokens"]  # type: ignore[index]

        # User is persisted.
        result_db = await db_session.execute(
            select(func.count()).select_from(User).where(
                User.email == "alice@example.com"
            )
        )
        assert result_db.scalar_one() == 1

    async def test_duplicate_email_returns_409(
        self,
        client: AsyncClient,
    ) -> None:
        await _register(client, "alice@example.com")
        result = await _register(client, "alice@example.com")
        assert result["status_code"] == 409
        body = result["body"]  # type: ignore[assignment]
        assert body["code"] == "user.already_exists"  # type: ignore[index]

    async def test_email_is_lowercased(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        await _register(client, "ALICE@Example.COM")
        result = await db_session.execute(
            select(User).where(User.email == "alice@example.com")
        )
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.email == "alice@example.com"

    async def test_weak_password_rejected_with_422(
        self,
        client: AsyncClient,
    ) -> None:
        result = await _register(
            client, "weak@example.com", password="short"
        )
        assert result["status_code"] == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


class TestLogin:
    async def test_happy_path_returns_tokens(
        self,
        client: AsyncClient,
    ) -> None:
        await _register(client, "alice@example.com")
        result = await _login(client, "alice@example.com")
        assert result["status_code"] == 200
        body = result["body"]  # type: ignore[assignment]
        assert "access_token" in body["tokens"]  # type: ignore[index]

    async def test_wrong_password_returns_401(
        self,
        client: AsyncClient,
    ) -> None:
        await _register(client, "alice@example.com")
        result = await _login(client, "alice@example.com", password="wrong")
        assert result["status_code"] == 401
        body = result["body"]  # type: ignore[assignment]
        assert body["code"] == "auth.invalid_credentials"  # type: ignore[index]

    async def test_unknown_email_returns_401(
        self,
        client: AsyncClient,
    ) -> None:
        result = await _login(client, "ghost@example.com")
        assert result["status_code"] == 401
        body = result["body"]  # type: ignore[assignment]
        # Same envelope as wrong-password so we don't leak
        # which emails are registered.
        assert body["code"] == "auth.invalid_credentials"  # type: ignore[index]


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------


class TestRefresh:
    async def test_happy_path_rotates_refresh_token(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        register = await _register(client, "alice@example.com")
        old_refresh = register["body"]["tokens"]["refresh_token"]  # type: ignore[index]

        refresh_resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert refresh_resp.status_code == 200
        body = refresh_resp.json()
        assert body["tokens"]["refresh_token"] != old_refresh  # type: ignore[index]

        # Old refresh row is marked used_at.
        result = await db_session.execute(
            select(func.count()).select_from(RefreshToken).where(
                RefreshToken.used_at.is_not(None)
            )
        )
        assert result.scalar_one() >= 1

    async def test_replay_of_used_refresh_revokes_family(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        register = await _register(client, "alice@example.com")
        refresh = register["body"]["tokens"]["refresh_token"]  # type: ignore[index]

        # First refresh: OK.
        await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh},
        )
        # Replay the same refresh: must fail and revoke the family.
        replay = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh},
        )
        assert replay.status_code == 401
        assert replay.json()["code"] == "auth.refresh_revoked"


# ---------------------------------------------------------------------------
# /auth/me
# ---------------------------------------------------------------------------


class TestMe:
    async def test_returns_current_user(
        self,
        client: AsyncClient,
    ) -> None:
        register = await _register(client, "alice@example.com")
        access = register["body"]["tokens"]["access_token"]  # type: ignore[index]

        me = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert me.status_code == 200
        assert me.json()["email"] == "alice@example.com"

    async def test_missing_token_returns_401(
        self,
        client: AsyncClient,
    ) -> None:
        me = await client.get("/api/v1/auth/me")
        assert me.status_code == 401
        assert me.json()["code"] == "auth.token_invalid"


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


class TestLogout:
    async def test_logout_revokes_refresh_token(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        register = await _register(client, "alice@example.com")
        access = register["body"]["tokens"]["access_token"]  # type: ignore[index]
        refresh = register["body"]["tokens"]["refresh_token"]  # type: ignore[index]

        logout = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh},
            headers={"Authorization": f"Bearer {access}"},
        )
        assert logout.status_code == 204

        # Refresh after logout must fail.
        replay = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh},
        )
        assert replay.status_code == 401

    async def test_logout_without_body_revokes_all_sessions(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        # Register twice to create two sessions.
        r1 = await _register(client, "alice@example.com")
        # Force a new session by clearing cookies.
        client.cookies.clear()
        r2 = await _register(client, "alice@example.com")
        # The two responses share the same email but different tokens.
        assert r1["body"]["tokens"]["refresh_token"] != r2["body"]["tokens"]["refresh_token"]  # type: ignore[index]

        # Use r2's access to log out (no body).
        access = r2["body"]["tokens"]["access_token"]  # type: ignore[index]
        await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access}"},
        )

        # Both refresh tokens must now fail.
        for rt in (r1["body"]["tokens"]["refresh_token"], r2["body"]["tokens"]["refresh_token"]):  # type: ignore[index]
            resp = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": rt},
            )
            assert resp.status_code == 401
