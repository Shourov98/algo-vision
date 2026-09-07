"""Persistence layer for refresh tokens.

Stores opaque refresh-token records so the auth service can:
- look up by token_hash on /auth/refresh,
- mark a row ``used_at`` after rotation,
- revoke a single row or every row for a user on logout.

Schema reminder
---------------
- id            : UUID PK
- user_id       : UUID FK -> users(id) ON DELETE CASCADE
- token_hash    : TEXT UNIQUE (sha256 hex of plaintext token)
- expires_at    : TIMESTAMPTZ NOT NULL
- used_at       : TIMESTAMPTZ NULL  (single-use marker)
- revoked_at    : TIMESTAMPTZ NULL  (explicit logout)
- created_at    : TIMESTAMPTZ NOT NULL DEFAULT now()

The UNIQUE index on ``token_hash`` is the lookup path for the
refresh hot path; ``ix_refresh_tokens_user_id`` covers the
logout-all-sessions path.

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 2 — B2.5)
Refs: DATABASE_DESIGN.md §21 (pattern)
Refs: PUKU_BACKEND_AGENT.md §9 (Repository Conventions)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.tokens import hash_refresh_token


class RefreshToken:
    """Plain Python domain object for a refresh-token row.

    Kept here rather than in models.py because it's an internal
    data carrier for the auth flow; routers never see it. The
    underlying SQLAlchemy model lives in this same module so we
    don't pollute the shared models namespace.
    """

    __slots__ = (
        "created_at",
        "expires_at",
        "id",
        "revoked_at",
        "token_hash",
        "used_at",
        "user_id",
    )

    def __init__(
        self,
        id: UUID,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
        used_at: datetime | None = None,
        revoked_at: datetime | None = None,
        created_at: datetime | None = None,
    ) -> None:
        self.id = id
        self.user_id = user_id
        self.token_hash = token_hash
        self.expires_at = expires_at
        self.used_at = used_at
        self.revoked_at = revoked_at
        self.created_at = created_at


class RefreshTokensRepositoryProtocol(Protocol):
    async def insert(
        self,
        user_id: UUID,
        plaintext_token: str,
        expires_at: datetime,
    ) -> RefreshToken: ...
    async def get_by_token(self, plaintext_token: str) -> RefreshToken | None: ...
    async def mark_used(self, token_id: UUID) -> None: ...
    async def revoke(self, token_id: UUID) -> None: ...
    async def revoke_all_for_user(self, user_id: UUID) -> int: ...


class _RefreshTokenModel:
    """Internal SQLAlchemy representation.

    We declare the table inline rather than in a models module
    because refresh tokens are an auth-internal concern. SQLAlchemy
    will register the table on ``Base.metadata`` via the
    ``__tablename__`` attribute, which is enough for our
    queries and tests (we never autogenerate migrations from
    this — refresh_tokens has its own hand-written migration).
    """


def _table(base):
    """Build a Table object on the given Base.

    Defined as a function so we can attach the table to whatever
    declarative base is in use at runtime (Base from src.core.db).
    """
    import sqlalchemy as sa
    from sqlalchemy import Column, Table

    # Explicitly import the postgresql dialect so its UUID type
    # is available. SQLAlchemy 2.x lazy-loads dialects and
    # ``sqlalchemy.dialects.postgresql`` is not guaranteed to be
    # importable until the dialect module has been touched at
    # least once in the process.
    from sqlalchemy.dialects import postgresql

    return Table(
        "refresh_tokens",
        base.metadata,
        Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        Column("token_hash", sa.Text(), nullable=False, unique=True),
        Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        Column("used_at", sa.DateTime(timezone=True), nullable=True),
        Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )


# Bind the table to the project's Base once, at import time.
# Idempotent: if env.py already imported it via a model module,
# ``metadata.tables`` already has ``refresh_tokens`` and the second
# ``_table`` call returns the same Table (SQLAlchemy dedupes by
# name + key).
from src.core.db import Base as _Base  # noqa: E402

REFRESH_TOKENS_TABLE = _table(_Base)


class RefreshTokensRepository:
    """Async SQL implementation of RefreshTokensRepositoryProtocol.

    All methods take/return domain objects, never raw rows. This
    keeps the service layer free of SQLAlchemy-specific concerns.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def insert(
        self,
        user_id: UUID,
        plaintext_token: str,
        expires_at: datetime,
    ) -> RefreshToken:
        """Persist a brand-new refresh token.

        Hashes the plaintext before storage (defense in depth: a
        DB leak cannot let an attacker reuse tokens).
        """
        token_hash = hash_refresh_token(plaintext_token)
        stmt = REFRESH_TOKENS_TABLE.insert().values(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        # Insert first, then re-query for the full row including
        # server defaults. ``execute(insert)`` returns the result
        # object whose ``inserted_primary_key`` carries the new id
        # on asyncpg; we don't need it here because the token_hash
        # we already have is unique and indexes the row.
        await self._session.execute(stmt)
        select_stmt = select(REFRESH_TOKENS_TABLE).where(
            REFRESH_TOKENS_TABLE.c.token_hash == token_hash,
        )
        row = (await self._session.execute(select_stmt)).one()
        return _row_to_token(row)

    async def get_by_token(self, plaintext_token: str) -> RefreshToken | None:
        token_hash = hash_refresh_token(plaintext_token)
        stmt = select(REFRESH_TOKENS_TABLE).where(
            REFRESH_TOKENS_TABLE.c.token_hash == token_hash,
        )
        result = await self._session.execute(stmt)
        row = result.one_or_none()
        return _row_to_token(row) if row is not None else None

    async def mark_used(self, token_id: UUID) -> None:
        stmt = (
            update(REFRESH_TOKENS_TABLE)
            .where(REFRESH_TOKENS_TABLE.c.id == token_id)
            .values(used_at=datetime.now(UTC))
        )
        await self._session.execute(stmt)

    async def revoke(self, token_id: UUID) -> None:
        stmt = (
            update(REFRESH_TOKENS_TABLE)
            .where(REFRESH_TOKENS_TABLE.c.id == token_id)
            .values(revoked_at=datetime.now(UTC))
        )
        await self._session.execute(stmt)

    async def revoke_all_for_user(self, user_id: UUID) -> int:
        """Revoke every non-revoked refresh token for a user.

        Returns the number of rows affected. Used by logout-all-
        sessions and by family-revocation after a refresh-replay
        attempt (the latter is B2.9 territory).
        """
        now = datetime.now(UTC)
        stmt = (
            update(REFRESH_TOKENS_TABLE)
            .where(REFRESH_TOKENS_TABLE.c.user_id == user_id)
            .where(REFRESH_TOKENS_TABLE.c.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        result = await self._session.execute(stmt)
        # SQLAlchemy's typed stubs model ``execute(update(...))`` as
        # ``Result[Any]`` (because the statement may return rows or
        # not, depending on RETURNING). At runtime, ``rowcount`` is
        # always populated for an UPDATE without RETURNING.
        return int(result.rowcount or 0)  # type: ignore[attr-defined]


def _row_to_token(row) -> RefreshToken:
    """Map a SQLAlchemy Row to a RefreshToken domain object."""
    return RefreshToken(
        id=row.id,
        user_id=row.user_id,
        token_hash=row.token_hash,
        expires_at=row.expires_at,
        used_at=row.used_at,
        revoked_at=row.revoked_at,
        created_at=row.created_at,
    )
