"""SQLAlchemy 2.x mapped classes for the catalog domain.

Three tables land in B3.1:

- ``algorithm_categories`` — top-level groupings (Sorting, Graph, DP, ...).
  Parent of ``algorithms``.
- ``topics`` — reusable tags ("hash-map", "recursion", "two-pointers",
  ...) shared between algorithms and problems (Phase 4).
- ``algorithms`` — the catalog of algorithms with complexity metadata,
  difficulty, visualization_type, and an ``is_published`` gate for
  admin-only draft content.

Why these three land together
-----------------------------
They form a tight cluster with strict FK dependencies:

    algorithm_categories ── algorithms
    topics (standalone here; M:N table comes in B3.4)

The database-design plan calls them out as 0003-0005 in order
(DATABASE_DESIGN.md §6). Lumping them into one ticket keeps the
shared M:N table (B3.4) on a known-good foundation.

Style
-----
- Mapped[] + mapped_column for full static type info (mypy, IDEs).
- init=False is NOT used; services always pass explicit values, so
  default population at flush is fine and explicit.
- Every repr is identity-only (id + tablename) — no field data.
  Catalog rows are public-facing content, but a defensive repr is
  cheap and matches the convention set by the User model (B2.1).

Refs: DATABASE_DESIGN.md §1 (ERD), §4 (constraints), §5 (indexes)
Refs: ALGOVISION_BACKEND_PLAN.md §5 (Phase 3 — Catalog)
Refs: PUKU_BACKEND_AGENT.md §3.3 (no schema change without migration)
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base

# Difficulty is a closed vocabulary on algorithms. We use a plain str
# at the model level (no SQLAlchemy Enum) so the CHECK constraint
# lives in the migration as documented in DATABASE_DESIGN.md §4.3,
# and so future additions don't require a model-side change.
DIFFICULTY_VALUES: tuple[str, ...] = ("easy", "medium", "hard")


class Category(Base):
    """Top-level algorithm grouping.

    Examples: "Sorting", "Graph", "Dynamic Programming",
    "Greedy", "Divide & Conquer", "Searching".

    Public-facing content — slug is the URL key. ``sort_order``
    controls display order in the category sidebar.
    """

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


class Topic(Base):
    """Reusable tag (algorithm <-> topic, problem <-> topic).

    A topic is a standalone vocabulary entry. It is shared with the
    problems module (Phase 4) via the ``problem_topics`` M:N table.
    For B3.1 the M:N from algorithms is created in B3.4.
    """

    __tablename__ = "topics"

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

    def __repr__(self) -> str:
        return f"<Topic id={self.id}>"

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)


class Algorithm(Base):
    """Catalog algorithm with complexity metadata.

    ``visualization_type`` is a frontend-facing discriminator
    (e.g. "bar-chart", "graph-traversal") that drives which SVG
    renderer the client picks. We don't constrain it here because
    the frontend owns the vocabulary; the column is just a string.

    ``is_published`` gates the public catalog. Draft algorithms are
    only visible to admins (admin role lands in a future phase).
    """

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
    # Free-text strings so we can store "O(n log n)", "O(n)", "O(n^2)"
    # exactly as documented. Numeric parsing is out of scope — the
    # frontend renders the strings verbatim.
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


__all__ = [
    "DIFFICULTY_VALUES",
    "Algorithm",
    "Category",
    "Topic",
]
