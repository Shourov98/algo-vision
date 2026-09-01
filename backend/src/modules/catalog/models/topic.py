"""``topics`` table — reusable tags.

A topic is a standalone vocabulary entry. It is shared between
algorithms (Phase 3's ``algorithm_topics`` M:N table, B3.4) and
problems (Phase 4's ``problem_topics``). Keeping topics as a
standalone table — rather than a column on algorithms or a
free-text field — avoids the vocabulary-drift problem where the
same concept ("dynamic programming") ends up tagged multiple
ways.

Why no description / created_at
-------------------------------
Topics are short labels; longer context lives on the
algorithm/problem itself. Topics are static catalog content
seeded once; no creation API in v1.

Refs: DATABASE_DESIGN.md §1 (ERD: topics), §4 (constraints),
       §5 (indexes), §6 (0003)
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class Topic(Base):
    """Reusable tag."""

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
