"""``user_recent_items`` — last-viewed items per user, capped at 50.

Records every "view" event a user emits on a catalog entity
(algorithm, data structure, problem). The dashboard's
"recently viewed" sidebar reads the latest 50 from this
table.

Schema overview
---------------
- id           : UUID PK, server-generated.
- user_id      : UUID NOT NULL, FK → users.id
                 ON DELETE CASCADE.
- item_type    : VARCHAR(32) NOT NULL, CHECK
                 ('algorithm' | 'data_structure' | 'problem').
- item_id      : UUID NOT NULL. No FK — the referenced row
                 could be in any of three tables; the CHECK
                 constraint on ``item_type`` is the only
                 referential guarantee. (Adding three FKs
                 on a single column is impossible.)
- viewed_at    : TIMESTAMPTZ NOT NULL DEFAULT now().

Why a surrogate id PK (not composite)
-------------------------------------
This row is event-shaped: a single (user_id, item_id,
viewed_at) tuple is not a "natural key" because the same
user can view the same item many times across sessions.
A surrogate id makes the row uniquely addressable for
the cap-to-50 window function (B5.5 repository).

Why no FK on item_id
--------------------
``item_id`` is a polymorphic reference — it points at
``algorithms.id``, ``data_structures.id``, OR
``problems.id`` depending on ``item_type``. A single
column can have only one FK. Postgres has no native
polymorphic association, so the ``item_type`` CHECK
plus application-level invariant is the only option.
We accept the trade-off because this table is a
denormalised append log, not the source of truth for
any catalog entity.

Why 50-row cap is enforced in the repository, not here
------------------------------------------------------
DATABASE_DESIGN §1 caps at 50 rows per user; the §4
constraint section doesn't add a DB-level trigger for
that. A trigger would be powerful but expensive to test
across upgrades; a window function in the repository
(B5.5) gives the same guarantee with explicit, easy-to-
test code.

Refs: DATABASE_DESIGN.md §1 (ERD: user_recent_items),
       §4 (constraints), §5 (indexes), §6 (0016)
Refs: ALGOVISION_BACKEND_PLAN.md §5 (Phase 5 — B5.3)
Refs: ALGOVISION_BACKEND_PLAN.md §6.7 (ItemViewedEvent
       handler appends to this table)
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID as _UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, text
from sqlalchemy import String as SA_String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base

# Mirrors the CHECK constraint on user_recent_items.item_type.
# Single source of truth for the polymorphic reference target.
ITEM_TYPE_VALUES: tuple[str, ...] = (
    "algorithm",
    "data_structure",
    "problem",
)


class UserRecentItem(Base):
    """One row per (user, item, viewed_at) event.

    Persistence-only — never returned from a router. The
    progress service converts to a ``RecentItem`` (B5.9)
    before handing to the dashboard router.
    """

    __tablename__ = "user_recent_items"

    # ----- Surrogate PK ---------------------------------------------------
    id: Mapped[_UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # ----- FK + polymorphic reference ------------------------------------
    user_id: Mapped[_UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    item_type: Mapped[str] = mapped_column(
        SA_String(32),
        nullable=False,
    )
    item_id: Mapped[_UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
    )

    # ----- Timestamp ------------------------------------------------------
    viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    # ----- Table-level CHECKs --------------------------------------------
    __table_args__ = (
        CheckConstraint(
            "item_type IN ('algorithm', 'data_structure', 'problem')",
            name="ck_user_recent_items_type",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<UserRecentItem id={self.id} user_id={self.user_id} "
            f"item_type={self.item_type!r}>"
        )

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)


__all__ = ["ITEM_TYPE_VALUES", "UserRecentItem"]
