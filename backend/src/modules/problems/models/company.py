"""``companies`` table — companies that ask interview problems.

A company is the organization associated with a problem via
the ``problem_companies`` M:N table (B4.3). One company can
ask many problems; one problem can be asked by many companies.

Schema overview
---------------
- Identity: id (UUID PK), slug (UK, URL key)
- Display: name

Why a separate ``companies`` table (not an enum on problems)
-----------------------------------------------------------
"Asked by Google, Meta, Amazon" reads naturally as a tagged
list — the frontend renders a problem detail page with a row
of company pills. That requires M:N semantics that an enum
on the problem can't express (a problem can be asked by N
companies). The reverse direction ("show me every problem
Google has asked") is the dominant read pattern (filter
listings by company), so the entity deserves its own table
even when the cardinality is small.

Why no ``logo_url`` / ``website`` columns
-----------------------------------------
Out of v1 scope. The interview-preparation surface is text-
first; visual assets land when the frontend asks for them.

Why no FK to ``problems``
-------------------------
Companies and problems are joined exclusively through the
``problem_companies`` junction table (B4.3). There is no
direct FK on either side — that's the whole point of an M:N.

Refs: DATABASE_DESIGN.md §1 (ERD: companies), §4
       (constraints), §6 (0010)
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 4 — Problems, B4.2)
"""

from __future__ import annotations

from uuid import UUID as _UUID

from sqlalchemy import String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class Company(Base):
    """A company that asks one or more interview problems."""

    __tablename__ = "companies"

    # ----- Identity ---------------------------------------------------------
    id: Mapped[_UUID] = mapped_column(
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

    def __repr__(self) -> str:
        """Identity-only repr — no slug/name leak."""
        return f"<Company id={self.id}>"

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)


__all__ = ["Company"]
