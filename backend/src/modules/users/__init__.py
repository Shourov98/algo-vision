"""Users module.

Owns the ``User`` SQLAlchemy model and any related persistence
concerns. The auth module (B2.5) consumes this model via the
UsersRepository; routers never import the model directly.

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 2 — Auth & Users)
Refs: AlgoVision_BACKEND.md §9 (users table), §14 (module owns)
"""

from src.modules.users.models import User

__all__ = ["User"]
