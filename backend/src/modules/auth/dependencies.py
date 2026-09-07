"""FastAPI dependencies for the auth module.

Centralizes the wiring between the HTTP layer and the service layer:

- ``get_auth_service``: builds an AuthService from the request-scoped
  AsyncSession + the per-request repositories.
- ``get_current_user``: pulls the access token off the request
  (HTTP-only cookie first, then Authorization Bearer header),
  validates it via the service, and returns the User.

Why a separate module
---------------------
The router file stays focused on HTTP-shape concerns; the dependency
injection lives here so it's testable and reusable. Other modules
(problems, progress) will import ``get_current_user`` once we wire
them up — that's the dependency-inversion pattern in practice.

Token transport
---------------
Two ways to present an access token, both supported:
1. ``Authorization: Bearer <token>`` header — used by API clients
   (mobile, third-party integrations).
2. ``access_token`` HTTP-only cookie — the default for the browser
   frontend.

The browser cookie is checked first because that's the common case
for our own frontend; the Bearer header is the fallback for clients
that can't use cookies.

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 2 — B2.7)
Refs: AlgoVision_BACKEND.md §8 (Authentication)
Refs: PUKU_BACKEND_AGENT.md §7 (Router Conventions)
"""

from __future__ import annotations

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_session
from src.core.errors import TokenInvalid
from src.core.request_id import bind_user_id
from src.core.settings import Settings, get_settings
from src.modules.auth.repository import RefreshTokensRepository
from src.modules.auth.service import AuthService
from src.modules.users.models import User
from src.modules.users.repository import UsersRepository

# ``auto_error=False`` so we can fall back to the cookie when the
# Authorization header is absent. The default of HTTPBearer raises
# 403 immediately, which would defeat the cookie path.
_bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service(
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> AuthService:
    """Build an AuthService bound to the request-scoped session.

    Both repositories share the same session so the service can
    commit them together at the end of each public method.
    """
    return AuthService(
        session=session,
        users_repo=UsersRepository(session),
        refresh_tokens_repo=RefreshTokensRepository(session),
        settings=settings,
    )


async def _extract_access_token(request: Request) -> str | None:
    """Read the access token from the request.

    Order:
    1. ``access_token`` HTTP-only cookie — the default for the
       browser frontend.
    2. ``Authorization: Bearer <token>`` header — used by API
       clients (mobile, third-party integrations).

    Returns None if neither is present. ``get_current_user`` raises
    ``TokenInvalid`` so the response is a clean 401.
    """
    cookie = request.cookies.get("access_token")
    if cookie:
        return cookie

    # HTTPBearer is async in modern Starlette — awaiting it parses
    # the Authorization header.
    creds: HTTPAuthorizationCredentials | None = await _bearer_scheme(request)
    if creds is not None:
        return creds.credentials

    return None


async def get_current_user(
    request: Request,
    service: AuthService = Depends(get_auth_service),
) -> User:
    """FastAPI dependency: return the authenticated user.

    Raises 401 (via the AppError handler) if no token is present,
    the token is invalid/expired, or the user is inactive.
    """
    token = await _extract_access_token(request)
    if token is None:
        raise TokenInvalid("Access token is missing.")
    user = await service.get_current_user(token)
    bind_user_id(user.id)
    return user
