"""``problems`` table — curated interview problems.

A problem is the question a candidate is asked, distinct from
the algorithms (algorithm) they could use to solve it (one
problem can have several algorithm tags; one algorithm can
solve many problems). The catalog (Phase 3) is the conceptual
reference; this table is the interview-preparation surface
(Phase 4 — see ``AlgoVision — Interview Preparation.svg``).

Schema overview
---------------
- Identity: id (UUID PK), slug (UK, URL key)
- Display: title, description
- Difficulty: free-text string with CHECK constraint per
  DATABASE_DESIGN §4.3 (same vocabulary as ``algorithms``).
- Editorial: solution_explanation (TEXT, nullable — only
  filled when an editorial exists)
- Cross-references: external_reference (TEXT, nullable —
  link to LeetCode / HackerRank / etc.)
- Toggles: visualization_available (BOOLEAN) — when true
  the frontend routes the problem to the visualization flow
  instead of the text-only editor flow.
- Timestamps: created_at, updated_at

Why difficulty is a free-text string (not an Enum)
--------------------------------------------------
Mirrors the ``algorithms`` decision (see
``models/algorithm.py``): the CHECK constraint lives in the
migration; future vocabulary additions ("introductory",
"advanced") need only a migration. DIFFICULTY_VALUES is the
Python-side mirror consumed by seeds + tests.

Why ``external_reference`` is free-text
--------------------------------------
We deliberately do not validate that the string is a URL.
Some references are short tags ("LC-1", "HR-warmup"), some
are URLs, some are book chapters. A TEXT column accepts all
three without premature commitment to URL validation.

Why no FK to ``algorithms`` (yet)
---------------------------------
A problem may map to multiple algorithms (e.g. "LRU Cache"
maps to Hash Map + Doubly Linked List). The mapping belongs
on the algorithm/problem edge, not as a single FK here.
Phase 6 may introduce a ``problem_algorithms`` M:N if the
frontend needs that resolution; absent a concrete feature
need, we don't create the table.

Why no ``is_published`` column
------------------------------
The catalog uses ``is_published`` (drafts are admin-only).
Problems follow the same convention — but unlike algorithms
(where the public catalog only ever shows published rows),
the problems API is staff-only in v1 (no public read
endpoint per ALGOVISION_BACKEND_PLAN §4). Draft visibility
is a separate concern; we add the column when the public
endpoint lands. Until then, all seeded rows are visible to
authenticated callers.

Refs: DATABASE_DESIGN.md §1 (ERD: problems), §4 (constraints),
       §5 (indexes), §6 (0010)
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 4 — Problems)
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID as _UUID

from sqlalchemy import Boolean, DateTime, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base

# Difficulty is a closed vocabulary on problems. The CHECK
# constraint lives in the migration; this constant is the
# Python-side mirror (same vocabulary as ``algorithms``).
DIFFICULTY_VALUES: tuple[str, ...] = ("easy", "medium", "hard")


class Problem(Base):
    """Catalog interview problem with editorial metadata."""

    __tablename__ = "problems"

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
    title: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ----- Difficulty (CHECK-constrained in migration) ---------------------
    difficulty: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )

    # ----- Editorial + cross-references -------------------------------------
    # solution_explanation is the long-form write-up the
    # frontend renders on the problem detail page. Nullable
    # because the seed ships with empty bodies for problems
    # that haven't been written up yet.
    solution_explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    # external_reference is a free-text tag or URL pointing
    # at the canonical source (LeetCode / HackerRank / book
    # chapter). See module docstring for why we don't
    # validate it as a URL.
    external_reference: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ----- Visualization flag ----------------------------------------------
    # When True, the frontend routes the problem to the
    # visualization flow; otherwise to the editor flow. Lets
    # the same catalog carry both visualizable + non-
    # visualizable problems without splitting the table.
    visualization_available: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("FALSE"),
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
        """Identity-only repr — no slug/title leak."""
        return f"<Problem id={self.id}>"

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)


__all__ = ["DIFFICULTY_VALUES", "Problem"]
