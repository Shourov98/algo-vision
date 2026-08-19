"""Users module.

Owns the ``User`` SQLAlchemy model and the persistence layer that
talks to it. The auth module (B2.5) consumes this repository via
its protocol; routers never import the model directly.

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 2 — Auth & Users)
Refs: AlgoVision_BACKEND.md §9 (users table), §14 (module owns)
"""

from src.modules.users.models import User
from src.modules.users.repository import (
    UsersRepository,
    UsersRepositoryProtocol,
)

__all__ = [
    "User",
    "UsersRepository",
    "UsersRepositoryProtocol",
]
