"""Unit tests for the User SQLAlchemy model.

These tests exercise the model class directly without needing a live
database. We verify:

- Table name + columns are declared (so ``Base.metadata`` knows about
  ``users``).
- Default values for server-side columns are declared on the model.
- ``__repr__`` does NOT leak email or password hash.
- The model can be imported via the public ``src.modules.users`` path.

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 2 — B2.1)
Refs: PUKU_BACKEND_AGENT.md §3.4 (no secrets in logs / repr)
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.core.db import Base
from src.modules.users.models import User


def test_user_table_name() -> None:
    assert User.__tablename__ == "users"


def test_user_is_registered_with_metadata() -> None:
    """Alembic and migrations rely on ``Base.metadata.tables`` to find models."""
    assert "users" in Base.metadata.tables


def test_user_columns_are_declared() -> None:
    expected = {
        "id",
        "email",
        "password_hash",
        "display_name",
        "is_active",
        "created_at",
        "updated_at",
    }
    assert set(User.__table__.columns.keys()) == expected


def test_user_id_is_uuid_pk() -> None:
    col = User.__table__.columns["id"]
    assert col.primary_key is True
    # Server default populates UUID via gen_random_uuid() — verify the
    # SQL fragment is wired up.
    assert col.server_default is not None
    assert "gen_random_uuid" in str(col.server_default.arg)


def test_user_email_is_unique_and_not_null() -> None:
    col = User.__table__.columns["email"]
    assert col.nullable is False
    assert col.unique is True


def test_user_password_hash_is_not_nullable() -> None:
    col = User.__table__.columns["password_hash"]
    assert col.nullable is False


def test_user_is_active_defaults_to_true() -> None:
    """Matches the schema in 20260819_1226_create_users.py:
    is_active BOOLEAN NOT NULL DEFAULT TRUE."""
    col = User.__table__.columns["is_active"]
    assert col.nullable is False
    assert col.server_default is not None
    assert "TRUE" in str(col.server_default.arg).upper()


def test_user_timestamps_default_to_now() -> None:
    for name in ("created_at", "updated_at"):
        col = User.__table__.columns[name]
        assert col.nullable is False
        assert col.server_default is not None
        assert "now()" in str(col.server_default.arg)


def test_user_repr_does_not_leak_secrets() -> None:
    """repr() must never include the email or password hash. A
    traceback that prints ``repr(user)`` would otherwise write them
    into logs (PUKU_BACKEND_AGENT §3.4)."""
    user = User(
        id=UUID("11111111-1111-1111-1111-111111111111"),
        email="alice@example.com",
        password_hash="argon2id$very$secret$hash",
        display_name="Alice",
    )
    text = repr(user)
    assert "alice@example.com" not in text
    assert "argon2id" not in text
    assert "secret" not in text
    assert "hash" not in text.lower()
    # The id is safe to expose (UUID, not a secret).
    assert "11111111-1111-1111-1111-111111111111" in text


def test_user_repr_handles_unset_id() -> None:
    """A freshly-constructed user has no id assigned yet (DB default
    will populate on flush). repr() must still not crash."""
    user = User(
        email="bob@example.com",
        password_hash="x",
        display_name="Bob",
    )
    text = repr(user)
    assert text.startswith("<User id=")


def test_user_equality_is_identity_only() -> None:
    """Two users with identical columns are NOT equal unless they
    are the same Python object. This protects against accidentally
    comparing detached ORM instances by attribute."""
    uid = uuid4()
    a = User(id=uid, email="x@x.com", password_hash="h", display_name="X")
    b = User(id=uid, email="x@x.com", password_hash="h", display_name="X")
    # Identity-only equality: separate instances are NEVER equal.
    assert a is not b
    assert a != b
    # But the same instance is equal to itself.
    assert a == a
    assert a is a


def test_user_can_construct_with_timestamps() -> None:
    """Application code may set timestamps explicitly when seeding."""
    now = datetime.now(tz=UTC)
    user = User(
        id=uuid4(),
        email="c@c.com",
        password_hash="h",
        display_name="C",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    assert user.created_at == now
    assert user.updated_at == now


def test_user_importable_via_public_path() -> None:
    """Sanity: the package's __init__ re-exports the model."""
    from src.modules.users import User as ReExported

    assert ReExported is User
