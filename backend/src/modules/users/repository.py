"""Persistence layer for users.

Single-responsibility: SQL only. No business rules, no HTTP, no
logging of secrets. The auth service (B2.5) consumes this
repository through a protocol so a fake implementation can stand
in for unit tests.

Query patterns
--------------
- ``get_by_email`` : login path. Indexed by ``ix_users_email_lower``
                    (B1.7). Email comparison is case-insensitive
                    because the column is CITEXT.
- ``get_by_id``    : /auth/me path. PK lookup, fast.
- ``create``       : register path. Service validates uniqueness
                    before calling, so the repo doesn't need a
                    catch-and-raise pattern for IntegrityError.

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 2 — B2.5)
Refs: AlgoVision_BACKEND.md §6 (Repository Layer)
Refs: PUKU_BACKEND_AGENT.md §9 (Repository Conventions)
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.users.models import User


class UsersRepositoryProtocol(Protocol):
    """Interface the auth service depends on.

    Liskov substitution: any class implementing this contract
    can stand in for the real repository in tests.
    """

    async def get_by_email(self, email: str) -> User | None: ...
    async def get_by_id(self, user_id: UUID) -> User | None: ...
    async def list_by_ids(self, ids: Sequence[UUID]) -> list[User]: ...
    async def create(
        self,
        email: str,
        password_hash: str,
        display_name: str,
    ) -> User: ...
    async def update_password_hash(
        self,
        user_id: UUID,
        new_password_hash: str,
    ) -> User | None: ...


class UsersRepository:
    """Async SQL implementation of UsersRepositoryProtocol."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        """Case-insensitive lookup (email column is CITEXT)."""
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_ids(self, ids: Sequence[UUID]) -> list[User]:
        if not ids:
            return []
        stmt = select(User).where(User.id.in_(ids))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        email: str,
        password_hash: str,
        display_name: str,
    ) -> User:
        """Persist a new user.

        Does NOT commit — that's the service layer's responsibility
        (see PUKU_BACKEND_AGENT §10 and AlgoVision_BACKEND §31).
        """
        user = User(
            email=email,
            password_hash=password_hash,
            display_name=display_name,
        )
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def update_password_hash(
        self,
        user_id: UUID,
        new_password_hash: str,
    ) -> User | None:
        """Update the password hash for an existing user.

        Returns the updated user, or None if the user does not
        exist. Used by the password-change flow (out of scope for
        B2.5 but the repo method is here so it's covered when that
        ticket lands).
        """
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        user.password_hash = new_password_hash
        await self._session.flush()
        await self._session.refresh(user)
        return user
