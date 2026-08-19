"""HTTP endpoints for /api/v1/auth.

Endpoints (see ALGOVISION_BACKEND_PLAN.md §7):
- POST /api/v1/auth/register  -> register a new user
- POST /api/v1/auth/login     -> exchange credentials for tokens
- POST /api/v1/auth/refresh   -> rotate a refresh token
- POST /api/v1/auth/logout    -> revoke refresh tokens
- GET  /api/v1/auth/me        -> return the current user

Conventions (PUKU_BACKEND_AGENT §7, AlgoVision_BACKEND §3)
----------------------------------------------------------
- No business logic in handlers. All work happens in AuthService.
- No SQL in handlers.
- HTTP-only cookie transport for the browser frontend; the response
  body still carries the tokens for clients that prefer explicit
  bearer transport (mobile, server-to-server).
- All AppError subclasses map to their declared status codes via
  the global handler registered in main.py (B1.4).

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 2 — B2.6)
Refs: AlgoVision_BACKEND.md §8 (Authentication)
Refs: PUKU_BACKEND_AGENT.md §7 (Router Conventions)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from pydantic import ValidationError

from src.core.errors import Unauthorized
from src.core.settings import Settings, get_settings
from src.modules.auth.dependencies import (
    get_auth_service,
    get_current_user,
)
from src.modules.auth.schemas import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)
from src.modules.auth.service import AuthService
from src.modules.users.models import User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Cookie helpers
# ---------------------------------------------------------------------------


def _set_auth_cookies(
    response: Response,
    settings: Settings,
    access: str,
    refresh: str,
) -> None:
    """Attach the access + refresh tokens as HTTP-only cookies.

    Called by register / login / refresh so the browser frontend
    gets them automatically without parsing the body. The body
    still carries the tokens so non-browser clients can use them
    as explicit bearer values.

    Cookie attributes:
    - HttpOnly: JS can't read the token (XSS hardening).
    - Secure:   only over HTTPS in production.
    - SameSite: ``settings.cookie_samesite`` (default ``lax``).
    - Domain:   ``settings.cookie_domain`` (empty = current host).
    - Path:     ``/`` so every endpoint can read them.
    """
    response.set_cookie(
        key="access_token",
        value=access,
        max_age=settings.access_token_ttl_seconds,
        path="/",
        domain=settings.cookie_domain or None,
        secure=settings.cookie_secure,
        httponly=True,
        samesite=settings.cookie_samesite,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh,
        max_age=settings.refresh_token_ttl_seconds,
        path="/",
        domain=settings.cookie_domain or None,
        secure=settings.cookie_secure,
        httponly=True,
        samesite=settings.cookie_samesite,
    )


def _clear_auth_cookies(response: Response, settings: Settings) -> None:
    """Expire the auth cookies. Used by /auth/logout."""
    response.delete_cookie(
        key="access_token",
        path="/",
        domain=settings.cookie_domain or None,
        secure=settings.cookie_secure,
        httponly=True,
        samesite=settings.cookie_samesite,
    )
    response.delete_cookie(
        key="refresh_token",
        path="/",
        domain=settings.cookie_domain or None,
        secure=settings.cookie_secure,
        httponly=True,
        samesite=settings.cookie_samesite,
    )


async def _read_refresh_token(request: Request) -> str:
    """Pull the refresh token from the request.

    Order:
    1. ``refresh_token`` HTTP-only cookie (browser path).
    2. JSON body ``{"refresh_token": "..."}`` (non-browser path).

    Raises Unauthorized (401) if neither is present.
    """
    cookie = request.cookies.get("refresh_token")
    if cookie:
        return cookie
    try:
        raw = await request.json()
        if isinstance(raw, dict):
            token = raw.get("refresh_token")
            if isinstance(token, str) and token:
                return token
    except (ValidationError, ValueError):
        # Body is not JSON / is malformed — fall through.
        pass
    raise Unauthorized("Refresh token is missing.")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=201,
    summary="Register a new user",
)
async def register(
    payload: RegisterRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> AuthResponse:
    """Create a new user account and return tokens."""
    auth = await service.register(
        email=payload.email,
        password=payload.password,
        display_name=payload.display_name,
    )
    _set_auth_cookies(
        response,
        settings,
        auth.tokens.access_token,
        auth.tokens.refresh_token,
    )
    return auth


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Exchange credentials for tokens",
)
async def login(
    payload: LoginRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> AuthResponse:
    """Authenticate by email + password and return tokens."""
    auth = await service.login(
        email=payload.email,
        password=payload.password,
    )
    _set_auth_cookies(
        response,
        settings,
        auth.tokens.access_token,
        auth.tokens.refresh_token,
    )
    return auth


@router.post(
    "/refresh",
    response_model=AuthResponse,
    summary="Rotate a refresh token",
)
async def refresh(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> AuthResponse:
    """Exchange a refresh token for a new access + refresh pair.

    Accepts the refresh token via the HTTP-only cookie OR the JSON
    body. Both are parsed to support browser and non-browser clients.

    The endpoint returns an AuthResponse (user + tokens) so the
    frontend can replace its stored profile in one round-trip. The
    user is loaded from the new access token via the service's
    ``get_current_user`` path — slightly wasteful but reuses the
    verified-token contract.
    """
    token = await _read_refresh_token(request)
    new_tokens = await service.refresh(token)
    user = await service.get_current_user(new_tokens.access_token)
    _set_auth_cookies(
        response,
        settings,
        new_tokens.access_token,
        new_tokens.refresh_token,
    )
    return AuthResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            created_at=user.created_at,
        ),
        tokens=new_tokens,
    )


@router.post(
    "/logout",
    status_code=204,
    summary="Revoke refresh tokens",
)
async def logout(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Sign out the current user.

    Two modes:
    - Body contains ``refresh_token`` -> revoke that token only.
    - Body empty / absent -> revoke all sessions for the user.

    The endpoint requires a valid access token via the standard
    dependency. We always clear the cookies on the way out.
    """
    refresh_token: str | None = None
    # Body is optional: clients can call POST /auth/logout with no
    # body to revoke all sessions. We parse it manually so a missing
    # body doesn't trigger a 422 from Pydantic.
    try:
        raw = await request.json()
    except (ValueError):
        raw = None
    if isinstance(raw, dict):
        token = raw.get("refresh_token")
        if isinstance(token, str):
            refresh_token = token or None

    await service.logout(
        user_id=current_user.id,
        refresh_token=refresh_token,
    )
    _clear_auth_cookies(response, settings)
    response.status_code = 204
    return response


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Return the current user",
)
async def me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Return the authenticated user's public profile."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
        created_at=current_user.created_at,
    )
