"""``algorithms`` table — catalog of algorithms.

``visualization_type`` is a frontend-facing discriminator
(e.g. "bar-chart", "graph-traversal") that drives which SVG
renderer the client picks. We don't constrain it here because
the frontend owns the vocabulary; the column is just a string.

``is_published`` gates the public catalog. Draft algorithms are
only visible to admins (admin role lands in a future phase).

Why difficulty is a string (not an Enum)
----------------------------------------
The CHECK constraint lives in the migration as documented in
DATABASE_DESIGN.md §4.3. A SQLAlchemy Enum would add runtime
caching and complicate autogenerate. Future additions to the
vocabulary ("advanced", "introductory") need only a migration.

Why complexity columns are free-text strings
--------------------------------------------
We deliberately do not parse "O(n log n)" into a structured
form. The catalog renders these as text; structured complexity
is a future feature (DATABASE_DESIGN §10). Storing free text
avoids premature commitment to a numeric representation that
would be hard to evolve.

Refs: DATABASE_DESIGN.md §1 (ERD: algorithms), §4 (constraints),
       §5 (indexes), §6 (0005)
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base

# Difficulty is a closed vocabulary on algorithms. The CHECK
# constraint lives in the migration; this constant is the
# Python-side mirror and is asserted by tests.
DIFFICULTY_VALUES: tuple[str, ...] = ("easy", "medium", "hard")


class Algorithm(Base):
    """Catalog algorithm with complexity metadata."""

    __tablename__ = "algorithms"

    # ----- Identity ---------------------------------------------------------
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # ----- Categorization ---------------------------------------------------
    # FK to algorithm_categories. ondelete=RESTRICT per
    # DATABASE_DESIGN §4.2 — a category with published algorithms
    # cannot be silently deleted.
    category_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
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

    # ----- Complexity metadata ----------------------------------------------
    # Free-text strings so we can store "O(n log n)", "O(n)",
    # "O(n^2)" exactly as documented.
    best_time: Mapped[str | None] = mapped_column(String(32), nullable=True)
    average_time: Mapped[str | None] = mapped_column(String(32), nullable=True)
    worst_time: Mapped[str | None] = mapped_column(String(32), nullable=True)
    space_complexity: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # ----- Publishing -------------------------------------------------------
    is_published: Mapped[bool] = mapped_column(
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

    def __repr__(self) -> str:
        return f"<Algorithm id={self.id}>"

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)
