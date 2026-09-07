"""``problem_companies`` M:N table — companies asking problems.

Many-to-many between ``problems`` and ``companies``. A problem
can be asked by multiple companies (e.g. "Two Sum" is in both
the Google and Meta question banks), and a company asks many
problems (e.g. Amazon has ~500 catalogued).

Schema overview
---------------
- problem_id : UUID NOT NULL, FK → problems.id, part of
               composite PK.
- company_id : UUID NOT NULL, FK → companies.id, part of
               composite PK.

Composite PK enforcement is the only constraint beyond the
FKs — there is no separate UNIQUE because the PK already
guarantees uniqueness (§4.2 of DATABASE_DESIGN).

Mirrors ``problem_topics`` (B4.3 first slice) and
``algorithm_topics`` (B3.5) semantics. The FK targets are the
only difference. Why CASCADE on both is documented in the
migration.

Refs: DATABASE_DESIGN.md §1 (ERD: problem_companies), §4
       (constraints), §6 (0013)
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 4 — Problems, B4.3)
"""

from __future__ import annotations

from uuid import UUID as _UUID

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class ProblemCompany(Base):
    """M:N row associating a problem with a company."""

    __tablename__ = "problem_companies"

    # ----- FK columns (also form the composite PK) -------------------------
    problem_id: Mapped[_UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("problems.id", ondelete="CASCADE"),
        primary_key=True,
    )
    company_id: Mapped[_UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        primary_key=True,
    )

    def __repr__(self) -> str:
        """Identity-only repr — PK pair is the only diagnostic worth showing."""
        return (
            f"<ProblemCompany problem_id={self.problem_id} "
            f"company_id={self.company_id}>"
        )

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)


__all__ = ["ProblemCompany"]
