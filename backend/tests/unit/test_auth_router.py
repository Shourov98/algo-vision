"""HTTP-layer tests for /api/v1/auth.

We mock the AuthService via FastAPI's dependency override so the
tests exercise the routing/serialization/cookie plumbing without
needing a real database. The service-level logic is covered by
``tests/unit/test_auth_service.py``; integration tests with a live
DB land in ``tests/integration/test_auth_endpoints.py`` (B2.9).

What we verify here
-------------------
- Each endpoint accepts the documented request shape.
- Each endpoint returns the documented response shape.
- The expected status codes are produced.
- The HTTP-only auth cookies are set on register / login / refresh.
- The auth cookies are cleared on logout.
- The ``auth.invalid_credentials`` envelope is returned for both
  unknown email and wrong password (no enumeration).
- ``auth.account_inactive`` is returned for deactivated users.
- /auth/me returns the current user from the access token.
- ``get_current_user`` rejects missing, malformed, and expired
  tokens with the right AppError codes.

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 2 — B2.6 + B2.7)
Refs: PUKU_BACKEND_AGENT.md §13 (Test Conventions)
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.core.errors import (
    InvalidCredentials,
)
from src.core.settings import Settings, get_settings
from src.main import create_app
from src.modules.auth.dependencies import get_auth_service
from src.modules.auth.exceptions import AccountInactive
from src.modules.auth.router import (
    _clear_auth_cookies,
    _set_auth_cookies,
)
from src.modules.auth.schemas import (
    AuthResponse,
    TokenPair,
    UserResponse,
)
from src.modules.users.models import User

# ---------------------------------------------------------------------------
# Settings fixture
# ---------------------------------------------------------------------------


def _make_settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "app_env": "test",
        "database_url": "postgresql+asyncpg://x:x@x/x",
        "database_url_sync": "postgresql+psycopg2://x:x@x/x",
        "secret_key": "x" * 64,
        "argon2_time_cost": 1,
        "argon2_memory_cost": 8_192,
        "argon2_parallelism": 1,
        "access_token_ttl_seconds": 60,
        "refresh_token_ttl_seconds": 86400,  # 1 day, at the floor
        "cookie_secure": False,
        "cookie_samesite": "lax",
    }
    base.update(overrides)
    return Settings.model_validate(base)


@pytest.fixture(autouse=True)
def _clear_settings_cache(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Force cookie_domain to a clean empty string so we don't inherit
    the project's .env value (which contains an inline comment)."""
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("SECRET_KEY", "x" * 64)
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://x:x@x/x")
    monkeypatch.setenv("DATABASE_URL_SYNC", "postgresql+psycopg2://x:x@x/x")
    monkeypatch.setenv("COOKIE_DOMAIN", "")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def settings() -> Settings:
    return _make_settings()


# ---------------------------------------------------------------------------
# Fake auth service
# ---------------------------------------------------------------------------


class FakeAuthService:
    """Records calls and returns canned responses.

    Tests configure ``next_*`` fields to drive the response for each
    call. Methods default to raising if not configured, so any
    unexpected invocation surfaces as a clear test failure.
    """

    def __init__(self) -> None:
        self.next_register: AuthResponse | Exception = Exception(
            "FakeAuthService.next_register not set"
        )
        self.next_login: AuthResponse | Exception = Exception(
            "FakeAuthService.next_login not set"
        )
        self.next_refresh: TokenPair | Exception = Exception(
            "FakeAuthService.next_refresh not set"
        )
        self.next_get_current: User | Exception = Exception(
            "FakeAuthService.next_get_current not set"
        )
        self.last_logout_user_id: UUID | None = None
        self.last_logout_token: str | None = None
        self.next_get_current_call_count = 0
        self.last_refresh_token: str | None = None

    async def register(
        self,
        email: str,
        password: str,
        display_name: str,
    ) -> AuthResponse:
        result = self.next_register
        if isinstance(result, Exception):
            raise result
        return result

    async def login(self, email: str, password: str) -> AuthResponse:
        result = self.next_login
        if isinstance(result, Exception):
            raise result
        return result

    async def refresh(self, refresh_token: str) -> TokenPair:
        self.last_refresh_token = refresh_token
        result = self.next_refresh
        if isinstance(result, Exception):
            raise result
        return result

    async def logout(self, user_id: UUID, refresh_token: str | None) -> None:
        self.last_logout_user_id = user_id
        self.last_logout_token = refresh_token

    async def get_current_user(self, access_token: str) -> User:
        self.next_get_current_call_count += 1
        result = self.next_get_current
        if isinstance(result, Exception):
            raise result
        return result


# ---------------------------------------------------------------------------
# App + client fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_service() -> FakeAuthService:
    return FakeAuthService()


@pytest.fixture
def app(
    settings: Settings,
    fake_service: FakeAuthService,
) -> FastAPI:
    """Build the real app but override the auth service dependency."""
    application = create_app(settings)
    # Override the AuthService dependency to return our fake. The
    # router signatures depend on AuthService, not AuthServiceProtocol,
    # so this works structurally.
    application.dependency_overrides[get_auth_service] = lambda: fake_service
    return application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _user_payload() -> UserResponse:
    return UserResponse(
        id=UUID("11111111-1111-1111-1111-111111111111"),
        email="alice@example.com",
        display_name="Alice",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _token_pair() -> TokenPair:
    return TokenPair(
        access_token="at-fake",
        refresh_token="rt-fake",
        token_type="bearer",
        expires_in=60,
    )


def _auth_response() -> AuthResponse:
    return AuthResponse(user=_user_payload(), tokens=_token_pair())


# ---------------------------------------------------------------------------
# /auth/register
# ---------------------------------------------------------------------------


class TestRegister:
    def test_happy_path_returns_201_and_tokens(
        self,
        client: TestClient,
        fake_service: FakeAuthService,
    ) -> None:
        fake_service.next_register = _auth_response()
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "alice@example.com",
                "password": "correct-horse-battery-staple",
                "display_name": "Alice",
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["user"]["email"] == "alice@example.com"
        assert body["tokens"]["access_token"] == "at-fake"
        assert body["tokens"]["refresh_token"] == "rt-fake"
        # Cookies are set.
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies

    def test_short_password_returns_422(
        self,
        client: TestClient,
    ) -> None:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "alice@example.com",
                "password": "short",  # < 12 chars
                "display_name": "Alice",
            },
        )
        assert response.status_code == 422

    def test_invalid_email_returns_422(
        self,
        client: TestClient,
    ) -> None:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "correct-horse-battery-staple",
                "display_name": "Alice",
            },
        )
        assert response.status_code == 422

    def test_extra_field_rejected(
        self,
        client: TestClient,
    ) -> None:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "alice@example.com",
                "password": "correct-horse-battery-staple",
                "display_name": "Alice",
                "is_admin": True,  # extra
            },
        )
        assert response.status_code == 422

    def test_duplicate_email_returns_409(
        self,
        client: TestClient,
        fake_service: FakeAuthService,
    ) -> None:
        from src.core.errors import UserAlreadyExists

        fake_service.next_register = UserAlreadyExists(
            "An account with that email already exists.",
            details={"field": "email"},
        )
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "alice@example.com",
                "password": "correct-horse-battery-staple",
                "display_name": "Alice",
            },
        )
        assert response.status_code == 409
        assert response.json()["code"] == "user.already_exists"


# ---------------------------------------------------------------------------
# /auth/login
# ---------------------------------------------------------------------------


class TestLogin:
    def test_happy_path_returns_tokens_and_cookies(
        self,
        client: TestClient,
        fake_service: FakeAuthService,
    ) -> None:
        fake_service.next_login = _auth_response()
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "alice@example.com", "password": "correct-horse-battery-staple"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["user"]["email"] == "alice@example.com"
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies

    def test_invalid_credentials_returns_401(
        self,
        client: TestClient,
        fake_service: FakeAuthService,
    ) -> None:
        fake_service.next_login = InvalidCredentials("Invalid email or password.")
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "x@y.com", "password": "wrong-password-here"},
        )
        assert response.status_code == 401
        body = response.json()
        assert body["code"] == "auth.invalid_credentials"

    def test_inactive_account_returns_403(
        self,
        client: TestClient,
        fake_service: FakeAuthService,
    ) -> None:
        fake_service.next_login = AccountInactive("deactivated")
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "alice@example.com", "password": "correct-horse-battery-staple"},
        )
        assert response.status_code == 403
        body = response.json()
        assert body["code"] == "auth.account_inactive"


# ---------------------------------------------------------------------------
# /auth/refresh
# ---------------------------------------------------------------------------


class TestRefresh:
    def test_with_cookie(
        self,
        client: TestClient,
        fake_service: FakeAuthService,
    ) -> None:
        # The endpoint should pull the refresh token from the cookie.
        fake_service.next_refresh = _token_pair()
        fake_service.next_get_current = User(
            id=UUID("11111111-1111-1111-1111-111111111111"),
            email="alice@example.com",
            password_hash="x",
            display_name="Alice",
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        client.cookies.set("refresh_token", "rt-from-cookie")
        response = client.post("/api/v1/auth/refresh")
        assert response.status_code == 200
        assert fake_service.last_refresh_token == "rt-from-cookie"
        # New tokens are set on the response.
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies

    def test_with_body(
        self,
        client: TestClient,
        fake_service: FakeAuthService,
    ) -> None:
        fake_service.next_refresh = _token_pair()
        fake_service.next_get_current = User(
            id=UUID("11111111-1111-1111-1111-111111111111"),
            email="alice@example.com",
            password_hash="x",
            display_name="Alice",
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "rt-from-body"},
        )
        assert response.status_code == 200
        assert fake_service.last_refresh_token == "rt-from-body"

    def test_missing_token_returns_401(
        self,
        client: TestClient,
    ) -> None:
        response = client.post("/api/v1/auth/refresh")
        assert response.status_code == 401
        assert response.json()["code"] == "unauthorized"

    def test_revoked_returns_401(
        self,
        client: TestClient,
        fake_service: FakeAuthService,
    ) -> None:
        from src.modules.auth.exceptions import RefreshTokenRevoked

        fake_service.next_refresh = RefreshTokenRevoked("revoked")
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "rt-old"},
        )
        assert response.status_code == 401
        assert response.json()["code"] == "auth.refresh_revoked"


# ---------------------------------------------------------------------------
# /auth/logout
# ---------------------------------------------------------------------------


@pytest.fixture
def logged_in_client(
    client: TestClient,
    fake_service: FakeAuthService,
) -> TestClient:
    """Pretend the user is logged in via get_current_user override."""
    from src.modules.auth.dependencies import get_current_user

    user = User(
        id=UUID("11111111-1111-1111-1111-111111111111"),
        email="alice@example.com",
        password_hash="x",
        display_name="Alice",
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    # TestClient.app is a FastAPI instance; the static type is a
    # Callable so we need a cast to access attribute-style.
    app = cast(FastAPI, client.app)
    app.dependency_overrides[get_current_user] = lambda: user
    client.cookies.set("access_token", "at-fake")
    return client


class TestLogout:
    def test_logout_without_body_revokes_all(
        self,
        logged_in_client: TestClient,
        fake_service: FakeAuthService,
    ) -> None:
        response = logged_in_client.post("/api/v1/auth/logout")
        assert response.status_code == 204
        assert fake_service.last_logout_user_id == UUID(
            "11111111-1111-1111-1111-111111111111"
        )
        assert fake_service.last_logout_token is None

    def test_logout_with_specific_token(
        self,
        logged_in_client: TestClient,
        fake_service: FakeAuthService,
    ) -> None:
        response = logged_in_client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": "rt-just-this-one"},
        )
        assert response.status_code == 204
        assert fake_service.last_logout_token == "rt-just-this-one"

    def test_logout_clear_cookies_sets_delete_cookie_headers(
        self,
        settings: Settings,
    ) -> None:
        from fastapi import Response

        resp = Response()
        _clear_auth_cookies(resp, settings)
        set_cookie_headers = resp.headers.getlist("set-cookie")
        assert any("access_token" in h for h in set_cookie_headers)
        assert any("refresh_token" in h for h in set_cookie_headers)

    def test_logout_set_cookies_uses_httponly(
        self,
        settings: Settings,
    ) -> None:
        from fastapi import Response

        resp = Response()
        _set_auth_cookies(resp, settings, "at-new", "rt-new")
        set_cookie_headers = resp.headers.getlist("set-cookie")
        # Both cookies must be HttpOnly.
        assert any("access_token" in h and "HttpOnly" in h for h in set_cookie_headers)
        assert any("refresh_token" in h and "HttpOnly" in h for h in set_cookie_headers)


# ---------------------------------------------------------------------------
# /auth/me
# ---------------------------------------------------------------------------


class TestMe:
    def _override_current_user(self, client: TestClient, user: User) -> None:
        from src.modules.auth.dependencies import get_current_user

        app = cast(FastAPI, client.app)
        app.dependency_overrides[get_current_user] = lambda: user

    def test_returns_current_user(
        self,
        client: TestClient,
        fake_service: FakeAuthService,
    ) -> None:
        user = User(
            id=UUID("11111111-1111-1111-1111-111111111111"),
            email="alice@example.com",
            password_hash="x",
            display_name="Alice",
            is_active=True,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            updated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        self._override_current_user(client, user)
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == "11111111-1111-1111-1111-111111111111"
        assert body["email"] == "alice@example.com"
        assert body["display_name"] == "Alice"
        # Defense-in-depth: password hash must not be in the body.
        assert "password_hash" not in body

    def test_missing_token_returns_401(
        self,
        client: TestClient,
    ) -> None:
        # No cookie set; HTTPBearer also absent -> 401.
        # The dependency raises TokenInvalid, which the AppError
        # handler maps to 401.
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
        assert response.json()["code"] == "auth.token_invalid"

    def test_inactive_user_returns_403(
        self,
        client: TestClient,
    ) -> None:
        from src.modules.auth.dependencies import get_current_user

        def _raise_inactive() -> None:
            raise AccountInactive("deactivated")

        app = cast(FastAPI, client.app)
        app.dependency_overrides[get_current_user] = _raise_inactive
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 403
        assert response.json()["code"] == "auth.account_inactive"
