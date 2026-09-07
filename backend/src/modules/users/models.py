"""SQLAlchemy 2.x mapped class for ``users``.

This model is the single source of truth for how Python represents a
user row. It mirrors the schema declared in migration
``20260819_1226_create_users.py`` (B1.7) and is the only place a
schema change should be reflected first — the Alembic migration is
generated from this model (see B2.10).

Why Mapped[] + mapped_column
----------------------------
SQLAlchemy 2.x typed style gives us static type info (column types
visible to mypy and IDEs) without runtime cost. ``init=False`` on
``id`` lets callers construct a User with no args and have the DB
default populate it on flush — but in practice services always
explicitly create new users via the repository.

Email storage
-------------
Email is stored as PostgreSQL ``CITEXT`` (case-insensitive text).
The functional index ``ix_users_email_lower`` is created in the
migration; we additionally lowercase in Python before insert as
defense-in-depth (matches what the index already enforces).

Why we DO NOT add columns here without a migration
--------------------------------------------------
Phase 2 is intentionally narrow: just the columns the schema
already has. New columns (avatar_url, last_login_at, etc.) belong
in their own migration + ticket per PUKU_BACKEND_AGENT.md §3.3.

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 2 — B2.1)
Refs: AlgoVision_BACKEND.md §9 (users table)
Refs: DATABASE_DESIGN.md §3 (users), §5 (index plan)
Refs: PUKU_BACKEND_AGENT.md §3.3 (no schema changes without migration)
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Text, text
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class User(Base):
    """Application user.

    Persistence-only — never returned from a router (per
    PUKU_BACKEND_AGENT.md §3.1: API responses use Pydantic schemas).
    The auth service converts to ``UserResponse`` before handing to
    the router.
    """

    __tablename__ = "users"

    # ----- Identity ---------------------------------------------------------
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    email: Mapped[str] = mapped_column(
        CITEXT(),
        nullable=False,
        unique=True,
    )

    # ----- Credentials ------------------------------------------------------
    # Argon2id hash from src/core/security.py (B2.3). Never plaintext.
    password_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # ----- Profile ----------------------------------------------------------
    display_name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # ----- Status -----------------------------------------------------------
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("TRUE"),
    )

    # ----- Timestamps -------------------------------------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    # ----- Presentation -----------------------------------------------------

    def __repr__(self) -> str:
        """Safe repr that does NOT leak the email or password hash.

        PUKU_BACKEND_AGENT.md §3.4 forbids logging credentials. A
        stray ``repr(user)`` in a traceback would be just as bad —
        so we expose only the id, which is non-sensitive.
        """
        return f"<User id={self.id}>"

    def __eq__(self, other: object) -> bool:
        # Identity-only equality. Two users are equal only if they
        # are the same Python object — comparing by id would mask
        # detached/loaded state differences during a session.
        return self is other

    def __hash__(self) -> int:
        return id(self)
