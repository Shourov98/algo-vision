"""Auth feature module.

Handles registration, login, logout, refresh-token rotation, and the
``get_current_user`` FastAPI dependency. Emits no domain events.

Canonical layered structure (one file per concern):

    models.py       SQLAlchemy ORM (User)
    schemas.py      Pydantic I/O (Register, Login, User)
    repository.py   RefreshTokensRepository protocol + impl
    service.py      AuthService: register, login, logout, refresh
    router.py       /auth/* endpoints (added in B2.6)
    exceptions.py   Auth-specific domain errors
    tests/          unit + integration tests (next to code)

Refs: PUKU_BACKEND_AGENT.md §3.1, §3.4
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 2)
Refs: DATABASE_DESIGN.md §3 (users table)
"""

from src.modules.auth.exceptions import (
    AccountInactive,
    RefreshTokenAlreadyUsed,
    RefreshTokenExpired,
    RefreshTokenRevoked,
)
from src.modules.auth.repository import (
    RefreshToken,
    RefreshTokensRepository,
    RefreshTokensRepositoryProtocol,
)
from src.modules.auth.schemas import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserResponse,
)
from src.modules.auth.service import (
    AuthService,
    AuthServiceProtocol,
)

__all__ = [
    "AccountInactive",
    "AuthResponse",
    "AuthService",
    "AuthServiceProtocol",
    "LoginRequest",
    "LogoutRequest",
    "RefreshRequest",
    "RefreshToken",
    "RefreshTokenAlreadyUsed",
    "RefreshTokenExpired",
    "RefreshTokenRevoked",
    "RefreshTokensRepository",
    "RefreshTokensRepositoryProtocol",
    "RegisterRequest",
    "TokenPair",
    "UserResponse",
]
