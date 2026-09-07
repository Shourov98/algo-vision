"""``data_structures`` table — catalog of data structures.

Sibling of ``Algorithm`` — same metadata shape (slug, name,
description, difficulty, visualization_type) but no algorithmic
complexity columns. Complexity for data structures lives on
``data_structure_operations`` (per-operation rows) in a later
phase.

Why a separate table, not a column on Algorithm
-----------------------------------------------
Per DATABASE_DESIGN §1: algorithms and data structures are
distinct catalog kinds with different metadata. Treating them
as one polymorphic table would force a nullable column for
every metadata field that's unique to the other kind.

Why no FK parent and no updated_at
----------------------------------
- No hierarchical parent: data structures are a flat catalog;
  no category grouping needed for the current UX.
- No ``updated_at``: the table is small (<50 rows per
  DATABASE_DESIGN §2) and infrequently edited. ETag support is
  planned for /algorithms in B3.9 only; /data-structures reads
  are cache-friendly without per-row write tracking.

Refs: DATABASE_DESIGN.md §1 (ERD: data_structures), §4
       (constraints), §5 (indexes), §6 (0008)
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class DataStructure(Base):
    """Catalog data structure (linked list, hash map, tree, ...)."""

    __tablename__ = "data_structures"

    # ----- Identity ---------------------------------------------------------
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # ----- Display ----------------------------------------------------------
    slug: Mapped[str] = mapped_column(
        String(96),
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

    # ----- Difficulty (CHECK-constrained in migration) ----------------------
    difficulty: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )

    # ----- Visualization ----------------------------------------------------
    visualization_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    # ----- Timestamps -------------------------------------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    def __repr__(self) -> str:
        return f"<DataStructure id={self.id}>"

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)
