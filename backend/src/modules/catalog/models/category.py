"""``algorithm_categories`` table — top-level algorithm groupings.

Examples: "Sorting", "Graph", "Dynamic Programming", "Greedy",
"Divide & Conquer", "Searching".

Public-facing content. ``slug`` is the URL key. ``sort_order``
controls display order in the category sidebar.

Refs: DATABASE_DESIGN.md §1 (ERD: algorithm_categories), §4
       (constraints), §5 (indexes), §6 (0004)
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class Category(Base):
    """Top-level algorithm grouping."""

    __tablename__ = "algorithm_categories"

    # ----- Identity ---------------------------------------------------------
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # ----- Display ----------------------------------------------------------
    slug: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
    )
    name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ----- Ordering ---------------------------------------------------------
    # Display order in the category sidebar / browse page. Small int
    # is sufficient; explicit defaults to 0 so INSERTs without an
    # explicit value still get a deterministic order.
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    # ----- Timestamps -------------------------------------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    def __repr__(self) -> str:
        """Identity-only repr — no slug/name leak."""
        return f"<Category id={self.id}>"

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)
